"""
MVP Loop Scheduler
APScheduler-based loop that runs every 4-12 hours.
"""

import logging
import random
import re
from datetime import datetime, timedelta, date
import pytz
from typing import List, Dict, Optional
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import settings, SEED_ACCOUNTS, TOPICS, PERSONA_TOPICS
from api.database import ActivityLogger, get_db
from llm.router import HybridRouter
from rag.pinecone_store import PineconeStore
from x_api.client import XClient
from x_api.retrieval import SeedRetriever
from x_api.engagement import filter_engaging_tweets, select_for_quote_tweet
from personas.base import Persona
from validation import ContentValidator

logger = logging.getLogger(__name__)

MAX_VALIDATION_RETRIES = 2

# ── Posting schedule constants ────────────────────────────────────────────────
# Weekdays (Mon–Fri): 08:23–23:40 EAT only.
# Weekend nights:
#   Saturday early morning 00:00–03:59 EAT  (Friday late night extended to 4am)
#   Sunday   early morning 00:00–01:59 EAT  (Saturday late night extended to 2am)
WEEKEND_NIGHT_POSTS_PER_PERSONA = 5  # max posts per persona per weekend-night window


class PersonaBot:
    """Bot instance for a single persona."""
    
    def __init__(
        self,
        persona: Persona,
        x_client: XClient,
        llm_router: HybridRouter,
        rag_store: PineconeStore,
        dry_run: bool = False,
    ):
        self.persona = persona
        self.x_client = x_client
        self.router = llm_router
        self.rag = rag_store
        self.dry_run = dry_run
        self.quoted_tweet_ids: List[str] = []
        self.dynamic_vocabulary: List[str] = []  # Stores injected vocabulary for the current cycle
    
    def _get_recent_posts(self, limit: int = 10) -> List[str]:
        """Fetch recent posts for this persona from the database."""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT content FROM posts WHERE persona = ? ORDER BY created_at DESC LIMIT ?",
                    (self.persona.handle, limit)
                )
                return [row["content"] for row in cursor.fetchall()]
        except Exception:
            return []
    
    def _validate_content(self, content: str, topic: str) -> 'ValidationResult':
        """Run content through the authenticity validator."""
        recent = self._get_recent_posts()
        # Pass dynamic vocabulary injected from the scheduler loop
        validator = ContentValidator(recent_posts=recent, dynamic_vocabulary=self.dynamic_vocabulary)
        return validator.validate(content, self.persona.handle, topic)
    
    def generate_original_post(self, topic: str) -> tuple:
        """Generate an original post on a topic with validation.
        
        Returns:
            Tuple of (content, model_used, validation_result)
        """
        # Get RAG examples
        examples = self.rag.retrieve_similar(topic, top_k=5)
        
        # Log RAG activity
        ActivityLogger.log_rag_activity(
            action="retrieve",
            source="pinecone",
            query=topic,
            results_count=len(examples),
            details=examples,
            persona=self.persona.handle
        )
        
        # Extract text for LLM
        example_texts = [e["text"] for e in examples]
        
        # Generate with validation retry loop
        last_validation = None
        for attempt in range(1 + MAX_VALIDATION_RETRIES):
            content, model_used, trigger_score, matched_triggers, reason = self.router.generate(
                topic=topic,
                persona_description=self.persona.get_system_prompt(),
                rag_examples=example_texts,
                task="original_post",
                persona_type=self.persona.persona_type,
            )
            
            # Validate content
            last_validation = self._validate_content(content, topic)
            
            if last_validation.passed:
                logger.info(f"[{self.persona.handle}] Content passed validation (score: {last_validation.authenticity_score}, attempt: {attempt+1})")
                break
            else:
                logger.warning(
                    f"[{self.persona.handle}] Validation FAILED (attempt {attempt+1}/{1+MAX_VALIDATION_RETRIES}): "
                    f"{last_validation.summary}"
                )
                if attempt < MAX_VALIDATION_RETRIES:
                    # Append rejection reason to examples for next attempt
                    rejection_hint = f"REJECTED (issues: {'; '.join(last_validation.issues + last_validation.warnings)}). Try again — vary your opener, keep it raw/messy, no hashtags."
                    example_texts = example_texts + [rejection_hint]
        
        logger.info(f"[{self.persona.handle}] Generated post using {model_used}: {content[:50]}...")
        
        # Log routing decision
        ActivityLogger.log_llm_routing(
            persona=self.persona.handle,
            topic=topic,
            task="original_post",
            decision=model_used,
            trigger_score=trigger_score,
            triggers_matched=matched_triggers,
            reason=reason
        )
        
        return content, model_used, last_validation
    
    def generate_quote_comment(self, original_tweet: Dict) -> tuple:
        """Generate a quote-tweet comment with validation.
        
        Returns:
            Tuple of (content, model_used, validation_result)
        """
        examples = self.rag.retrieve_similar(original_tweet["text"], top_k=3)
        example_texts = [e["text"] for e in examples]
        
        last_validation = None
        for attempt in range(1 + MAX_VALIDATION_RETRIES):
            content, model_used, trigger_score, matched_triggers, reason = self.router.generate(
                topic=original_tweet["text"],
                persona_description=self.persona.get_system_prompt(),
                rag_examples=example_texts,
                task="quote_comment",
                persona_type=self.persona.persona_type,
            )
            
            last_validation = self._validate_content(content, original_tweet["text"])
            
            if last_validation.passed:
                break
            elif attempt < MAX_VALIDATION_RETRIES:
                rejection_hint = f"REJECTED (issues: {'; '.join(last_validation.issues + last_validation.warnings)}). Try again."
                example_texts = example_texts + [rejection_hint]
        
        # Log routing decision for quote
        ActivityLogger.log_llm_routing(
            persona=self.persona.handle,
            topic=original_tweet["text"][:100],
            task="quote_comment",
            decision=model_used,
            trigger_score=trigger_score,
            triggers_matched=matched_triggers,
            reason=reason
        )
        
        logger.info(f"[{self.persona.handle}] Generated quote using {model_used}")
        return content, model_used, last_validation
    
    def run_posting_cycle(self, topic: Optional[str] = None):
        """Run a single posting cycle: 1-2 original posts."""
        if topic is None:
            # Pick from persona-specific topic pool (falls back to all topics)
            persona_topic_keys = PERSONA_TOPICS.get(
                self.persona.credentials_key, list(TOPICS.keys())
            )
            category = random.choice(persona_topic_keys)
            topic = random.choice(TOPICS[category])
        
        # Generate and post (with validation)
        content, model_used, validation = self.generate_original_post(topic)
        result = self.x_client.post_tweet(content, dry_run=self.dry_run)
        
        if result:
            logger.info(f"[{self.persona.handle}] Posted: {result}")
            ActivityLogger.log_post(
                persona=self.persona.handle,
                content=content,
                tweet_id=str(result) if result != True else "dry_run",
                post_type="original",
                llm_used=model_used,
                authenticity_score=validation.authenticity_score if validation else 0,
                validation_issues=(
                    validation.issues + validation.warnings
                ) if validation else None,
            )
        
        return result
    
    def run_quote_cycle(self, engaging_tweets: List[Dict]):
        """Run quote-tweet cycle on engaging content."""
        to_quote = select_for_quote_tweet(
            engaging_tweets,
            already_quoted=self.quoted_tweet_ids,
            max_daily=2,
        )
        
        for tweet in to_quote:
            comment, model_used, validation = self.generate_quote_comment(tweet)
            result = self.x_client.quote_tweet(
                quote_tweet_id=tweet["id"],
                comment=comment,
                dry_run=self.dry_run,
            )
            
            if result:
                self.quoted_tweet_ids.append(tweet["id"])
                logger.info(f"[{self.persona.handle}] Quoted tweet: {tweet['id']}")
                ActivityLogger.log_post(
                    persona=self.persona.handle,
                    content=str(comment),
                    tweet_id=str(result) if result != True else "dry_run",
                    post_type="quote",
                    llm_used=model_used,
                    authenticity_score=validation.authenticity_score if validation else 0,
                    validation_issues=(
                        validation.issues + validation.warnings
                    ) if validation else None,
                )
    
    def run_reply_cycle(self):
        """Check and reply to mentions (with validation)."""
        mentions = self.x_client.get_my_mentions(max_results=5)
        
        for mention in mentions:
            # Generate reply with validation
            examples = self.rag.retrieve_similar(mention["text"], top_k=3)
            example_texts = [e["text"] for e in examples]
            
            last_validation = None
            for attempt in range(1 + MAX_VALIDATION_RETRIES):
                reply, model_used, trigger_score, matched_triggers, reason = self.router.generate(
                    topic=mention["text"],
                    persona_description=self.persona.get_system_prompt(),
                    rag_examples=example_texts,
                    task="reply",
                    persona_type=self.persona.persona_type,
                )
                
                last_validation = self._validate_content(reply, mention["text"])
                
                if last_validation.passed:
                    break
                elif attempt < MAX_VALIDATION_RETRIES:
                    rejection_hint = f"REJECTED (issues: {'; '.join(last_validation.issues + last_validation.warnings)}). Try again."
                    example_texts = example_texts + [rejection_hint]
            
            # Log routing decision for reply
            ActivityLogger.log_llm_routing(
                persona=self.persona.handle,
                topic=mention["text"][:100],
                task="reply",
                decision=model_used,
                trigger_score=trigger_score,
                triggers_matched=matched_triggers,
                reason=reason
            )
            
            result = self.x_client.reply_to_tweet(
                tweet_id=mention["id"],
                reply_text=reply,
                dry_run=self.dry_run,
            )
            
            if result:
                ActivityLogger.log_post(
                    persona=self.persona.handle,
                    content=reply,
                    tweet_id=str(result) if result != True else "dry_run",
                    post_type="reply",
                    llm_used=model_used,
                    authenticity_score=last_validation.authenticity_score if last_validation else 0,
                    validation_issues=(
                        last_validation.issues + last_validation.warnings
                    ) if last_validation else None,
                )


class MVPLoop:
    """Main MVP loop that orchestrates all bots."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        
        # Initialize shared services
        self.llm_router = HybridRouter(
            grok_api_key=settings.grok_api_key,
            claude_api_key=settings.claude_api_key,
        )
        
        self.rag_store = PineconeStore(
            api_key=settings.pinecone_api_key,
            index_name=settings.pinecone_index_name,
        )
        
        # Use Kamau's bearer token for retrieval
        self.retriever = SeedRetriever(
            bearer_token=settings.kamau.bearer_token,
        )
        
        # Initialize persona bots
        self.bots = self._init_bots()
        
        logger.info(f"MVP Loop initialized with {len(self.bots)} bots (dry_run={dry_run})")
    
    def _init_bots(self) -> List[PersonaBot]:
        """Initialize all persona bots. Skips any persona with missing/placeholder credentials."""
        from personas import get_personas
        bots = []

        all_personas = get_personas()

        # Map each persona's credentials_key to settings attribute
        cred_map = {
            "kamau":   settings.kamau,
            "wanjiku": settings.wanjiku,
            "baraka":  settings.baraka,
            "zawadi":  settings.zawadi,
            "zuri":    settings.zuri,
            "john":    settings.john,
            "karen":   settings.karen,
        }

        for persona in all_personas:
            creds = cred_map.get(persona.credentials_key)
            if not creds:
                logger.warning(f"Skipping {persona.name} ({persona.handle}) — credentials missing or incomplete")
                continue

            client = XClient(
                consumer_key=creds.consumer_key,
                consumer_secret=creds.consumer_secret,
                access_token=creds.access_token,
                access_token_secret=creds.access_token_secret,
                bearer_token=creds.bearer_token,
                persona_name=persona.name,
            )
            bots.append(PersonaBot(
                persona=persona,
                x_client=client,
                llm_router=self.llm_router,
                rag_store=self.rag_store,
                dry_run=self.dry_run,
            ))
            logger.info(f"Loaded bot: {persona.name} ({persona.handle})")

        logger.info(f"Active bots: {len(bots)} / {len(all_personas)}")
        return bots
    
    def refresh_rag(self):
        """Fetch fresh content from seed accounts and store in RAG."""
        logger.info("Refreshing RAG from seed accounts...")
        
        tweets = self.retriever.fetch_from_seed_accounts(
            seed_accounts=SEED_ACCOUNTS,
            max_per_account=20,
        )
        
        if tweets:
            # 1. Store in Pinecone
            try:
                stored = self.rag_store.store_tweets(
                    tweets=tweets,
                    source_account="seed_mix",
                )
                logger.info(f"Stored {stored} tweets in Pinecone")
            except Exception as e:
                logger.error(f"Pinecone storage failed: {e}")
            
            # 2. Store in Local Database (for Knowledge Base tab)
            knowledge_items = []
            for tweet in tweets:
                 # Tag topics
                tweet["topics"] = self._tag_topics(tweet["text"])
                
                knowledge_items.append({
                    "source": tweet.get("source", "seed_account"),
                    "content": tweet["text"],
                    "topics": tweet["topics"],
                    "vector_id": tweet.get("id")
                })
            
            ActivityLogger.log_knowledge_batch(knowledge_items)
        
        return tweets
    
    def _tag_topics(self, text: str) -> List[str]:
        """Tag tweet with relevant topics."""
        text_lower = text.lower()
        tags = []
        
        for category, keywords in TOPICS.items():
            if any(kw in text_lower for kw in keywords):
                tags.append(category)
        
        return tags
    
    def _get_window_type(self, now_eat):
        """Classify current EAT time into a posting window.

        Returns:
            ('weekend_night', max_posts)  — Sat 00:00-03:59 or Sun 00:00-01:59 EAT
            ('daytime',       0)          — 08:23-23:40 EAT any day
            ('blocked',       0)          — outside all windows
        """
        wd = now_eat.weekday()  # 0=Mon … 6=Sun
        h, m = now_eat.hour, now_eat.minute

        # Sat 00:00-03:59 EAT  (Friday night extended to 4am Saturday)
        if wd == 5 and h < 4:
            return 'weekend_night', WEEKEND_NIGHT_POSTS_PER_PERSONA

        # Sun 00:00-01:59 EAT  (Saturday night extended to 2am Sunday)
        if wd == 6 and h < 2:
            return 'weekend_night', WEEKEND_NIGHT_POSTS_PER_PERSONA

        # Standard daytime window: 08:23-23:40 EAT  (all days)
        after_start = h > 8 or (h == 8 and m >= 23)
        before_end  = h < 23 or (h == 23 and m <= 40)
        if after_start and before_end:
            return 'daytime', 0

        return 'blocked', 0

    def _get_persona_posts_since_midnight(self, handle: str) -> int:
        """Count posts logged for this persona since midnight EAT today."""
        eat = pytz.timezone("Africa/Nairobi")
        now_eat = datetime.now(eat)
        midnight_eat = now_eat.replace(hour=0, minute=0, second=0, microsecond=0)
        midnight_utc = midnight_eat.astimezone(pytz.UTC).isoformat()

        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) as count FROM posts WHERE persona = ? AND created_at > ?",
                    (handle, midnight_utc)
                )
                return cursor.fetchone()["count"]
        except Exception:
            return 0

    def _check_time_constraints(self) -> bool:
        """Check if we are allowed to post based on EAT time and limits."""
        eat = pytz.timezone("Africa/Nairobi")
        now_eat = datetime.now(eat)
        window, max_night_posts = self._get_window_type(now_eat)

        if window == 'weekend_night':
            # Weekend night: only enforce the 2-minute system-wide gap.
            # Per-persona cap enforced in run_cycle().
            day_name = now_eat.strftime('%A')
            logger.info(f"Weekend night window ({day_name} {now_eat.strftime('%H:%M')} EAT)")
            try:
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT created_at FROM posts ORDER BY created_at DESC LIMIT 1")
                    last_post = cursor.fetchone()
                    if last_post:
                        last_time = datetime.fromisoformat(last_post["created_at"])
                        if last_time.tzinfo is None:
                            last_time = last_time.replace(tzinfo=pytz.UTC)
                        now_utc = datetime.now(pytz.UTC)
                        time_since_last = (now_utc - last_time).total_seconds() / 60.0
                        if time_since_last < 2.0:
                            logger.info(f"Weekend night: gap too short ({time_since_last:.1f}m < 2m)")
                            return False
            except Exception:
                pass
            return True

        if window == 'blocked':
            logger.info(
                f"Outside posting window (EAT: {now_eat.strftime('%A %H:%M')}). "
                f"Weekdays: 08:23-23:40 | Sat night: until 04:00 | Sun night: until 02:00"
            )
            return False

        # window == 'daytime': standard hourly-cap logic
        is_work_hours = 10 <= now_eat.hour < 15
        max_posts_per_hour = 2 if is_work_hours else 6

        try:
            with get_db() as conn:
                cursor = conn.cursor()

                # Check recent post gap (system-wide)
                cursor.execute("SELECT created_at FROM posts ORDER BY created_at DESC LIMIT 1")
                last_post = cursor.fetchone()
                if last_post:
                    last_time = datetime.fromisoformat(last_post["created_at"])
                    if last_time.tzinfo is None:
                        last_time = last_time.replace(tzinfo=pytz.UTC)
                    now_utc = datetime.now(pytz.UTC)
                    time_since_last = (now_utc - last_time).total_seconds() / 60.0
                    if time_since_last < 2.0:
                        logger.info(f"Skipping... Last post was {time_since_last:.1f} mins ago (min gap: 2 mins).")
                        return False

                # Check hourly count (system-wide)
                one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
                cursor.execute("SELECT COUNT(*) as count FROM posts WHERE created_at > ?", (one_hour_ago,))
                posts_last_hour = cursor.fetchone()["count"]
                if posts_last_hour >= max_posts_per_hour:
                    logger.info(f"Skipping... Hourly limit reached ({posts_last_hour}/{max_posts_per_hour}). Mode: {'Work' if is_work_hours else 'Normal'}")
                    return False

                logger.info(f"Scheduler Go-Ahead: {posts_last_hour}/{max_posts_per_hour} posts/hr. Gap OK.")
                return True

        except Exception as e:
            logger.error(f"Scheduler check failed: {e}")
            return False  # Fail safe

    def _extract_dynamic_vocabulary(self, tweets: List[Dict]) -> List[str]:
        """
        Extract frequent non-standard words from recent tweets to use as dynamic context.
        Simple heuristic: words >= 4 chars, occurring > 1 time, not in standard ignore list.
        """
        if not tweets:
            return []
            
        word_counts = {}
        for t in tweets:
            # Simple tokenization
            words = re.findall(r'\b\w+\b', t["text"].lower())
            for w in words:
                if len(w) > 3: # Ignore short filler words
                    word_counts[w] = word_counts.get(w, 0) + 1
        
        # Filter for words that appear more than once (trending/common)
        # In a real system, we'd check against a standard English dict to be sure,
        # but for now, just capturing frequency helps catch slang/hashtags.
        dynamic_vocab = [w for w, count in word_counts.items() if count > 1]
        
        # Also include ALL hashtags found
        for t in tweets:
            hashtags = re.findall(r'#\w+', t["text"].lower())
            dynamic_vocab.extend(hashtags)
            
        return list(set(dynamic_vocab))

    def run_cycle(self):
        """Run one Smart Scheduler cycle."""
        logger.info(f"=== Scheduler Tick at {datetime.now()} ===")

        # 1. Check constraints
        if not self._check_time_constraints():
            return

        try:
            # 2. Refresh RAG
            fresh_tweets = self.refresh_rag()
            engaging = filter_engaging_tweets(fresh_tweets, max_results=10)

            # Dynamic vocabulary injection
            dynamic_vocab = self._extract_dynamic_vocabulary(fresh_tweets)
            if dynamic_vocab:
                logger.info(f"Dynamic Vocabulary Injected: {len(dynamic_vocab)} terms (e.g. {dynamic_vocab[:5]})")

            # 3. Select bot
            eat = pytz.timezone("Africa/Nairobi")
            now_eat = datetime.now(eat)
            window, max_night_posts = self._get_window_type(now_eat)

            if window == 'weekend_night':
                # Weekend night: pick the first (shuffled) persona still under their nightly cap
                shuffled = random.sample(self.bots, len(self.bots))
                bot = None
                for candidate in shuffled:
                    count = self._get_persona_posts_since_midnight(candidate.persona.handle)
                    if count < max_night_posts:
                        bot = candidate
                        logger.info(
                            f"Weekend night: selected {candidate.persona.handle} "
                            f"({count}/{max_night_posts} posts tonight)"
                        )
                        break
                if bot is None:
                    logger.info(
                        f"Weekend night: all personas at {max_night_posts} posts — sleeping."
                    )
                    return
            else:
                # Daytime: pick randomly
                bot = random.choice(self.bots)

            # Pass dynamic vocabulary to the bot for this cycle
            bot.dynamic_vocabulary = dynamic_vocab

            # 4. Decide Action (Original Post vs Quote vs Reply)
            # Weights: 60% Original, 30% Quote, 10% Reply
            roll = random.random()

            if roll < 0.6:
                logger.info(f"Attempting ORIGINAL POST for {bot.persona.handle}")
                bot.run_posting_cycle()
            elif roll < 0.9 and engaging:
                logger.info(f"Attempting QUOTE for {bot.persona.handle}")
                bot.run_quote_cycle(engaging)
            else:
                logger.info(f"Attempting REPLY for {bot.persona.handle}")
                bot.run_reply_cycle()

            logger.info(f"=== Cycle Action Completed ===")

        except Exception as e:
            logger.error(f"Cycle error: {e}", exc_info=True)
    
    def start(self, interval_hours: float = 6, start_time_est: Optional[str] = None):
        """Start the scheduler (Interval: 5 mins)."""
        scheduler = BlockingScheduler()
        
        # Fixed 5-minute interval for granular checks
        interval_minutes = 5
        
        # Add job
        scheduler.add_job(
            self.run_cycle,
            IntervalTrigger(minutes=interval_minutes),
            id="mvp_loop",
            name="Smart Scheduler",
            replace_existing=True,
        )
        
        logger.info(f"Smart Scheduler started. Checking every {interval_minutes} minutes.")
        logger.info("Constraints: 08:23-23:40 EAT | Work: 10-3pm (2/hr) | Normal: 6/hr | Gap: 2-20m")
        
        # Initial run
        self.run_cycle()
        
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")
