"""
MVP Loop Scheduler
APScheduler-based loop that runs every 4-12 hours.
"""

import logging
import random
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Optional
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import settings, SEED_ACCOUNTS, TOPICS
from api.database import ActivityLogger, get_db
from llm.router import HybridRouter
from rag.pinecone_store import PineconeStore
from x_api.client import XClient
from x_api.retrieval import SeedRetriever
from x_api.engagement import filter_engaging_tweets, select_for_quote_tweet
from personas.base import KamauPersona, WanjikuPersona, Persona
from validation import ContentValidator

logger = logging.getLogger(__name__)

MAX_VALIDATION_RETRIES = 2


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
        validator = ContentValidator(recent_posts=recent)
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
            # Pick random topic category
            category = random.choice(list(TOPICS.keys()))
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
        """Initialize all persona bots."""
        bots = []
        
        # Kamau bot
        kamau_persona = KamauPersona(
            name="", handle="", description="", tone="sarcastic",
            personality_traits=[], topics=[], signature_phrases=[],
            proverb_style="", persona_type="edgy"
        )
        kamau_client = XClient(
            consumer_key=settings.kamau.consumer_key,
            consumer_secret=settings.kamau.consumer_secret,
            access_token=settings.kamau.access_token,
            access_token_secret=settings.kamau.access_token_secret,
            bearer_token=settings.kamau.bearer_token,
            persona_name="Kamau",
        )
        bots.append(PersonaBot(
            persona=kamau_persona,
            x_client=kamau_client,
            llm_router=self.llm_router,
            rag_store=self.rag_store,
            dry_run=self.dry_run,
        ))
        
        # Wanjiku bot
        wanjiku_persona = WanjikuPersona(
            name="", handle="", description="", tone="wise",
            personality_traits=[], topics=[], signature_phrases=[],
            proverb_style="", persona_type="nurturing"
        )
        wanjiku_client = XClient(
            consumer_key=settings.wanjiku.consumer_key,
            consumer_secret=settings.wanjiku.consumer_secret,
            access_token=settings.wanjiku.access_token,
            access_token_secret=settings.wanjiku.access_token_secret,
            bearer_token=settings.wanjiku.bearer_token,
            persona_name="Wanjiku",
        )
        bots.append(PersonaBot(
            persona=wanjiku_persona,
            x_client=wanjiku_client,
            llm_router=self.llm_router,
            rag_store=self.rag_store,
            dry_run=self.dry_run,
        ))
        
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
            count = 0
            for tweet in tweets:
                 # Tag topics
                tweet["topics"] = self._tag_topics(tweet["text"])
                
                # Log to DB
                ActivityLogger.log_knowledge(
                    source=tweet.get("source", "seed_account"),
                    content=tweet["text"],
                    topics=tweet["topics"],
                    vector_id=tweet.get("id")
                )
                count += 1
            logger.info(f"Stored {count} tweets in Knowledge Base DB")
        
        return tweets
    
    def _tag_topics(self, text: str) -> List[str]:
        """Tag tweet with relevant topics."""
        text_lower = text.lower()
        tags = []
        
        for category, keywords in TOPICS.items():
            if any(kw in text_lower for kw in keywords):
                tags.append(category)
        
        return tags
    
    def run_cycle(self):
        """Run one complete MVP cycle."""
        logger.info(f"=== Starting MVP cycle at {datetime.now()} ===")
        
        try:
            # 1. Refresh RAG with seed content
            fresh_tweets = self.refresh_rag()
            
            # 2. Find engaging content for quotes
            engaging = filter_engaging_tweets(fresh_tweets, max_results=10)
            
            # 3. Run each bot
            for bot in self.bots:
                logger.info(f"Running cycle for {bot.persona.handle}")
                
                # Post 1-2 original tweets
                bot.run_posting_cycle()
                
                # Maybe post a second one (50% chance)
                if random.random() > 0.5:
                    bot.run_posting_cycle()
                
                # Quote/retweet engaging content
                bot.run_quote_cycle(engaging)
                
                # Reply to mentions
                bot.run_reply_cycle()
            
            logger.info(f"=== MVP cycle completed at {datetime.now()} ===")
            
        except Exception as e:
            logger.error(f"MVP cycle error: {e}", exc_info=True)
    
    def start(self, interval_hours: float = 6, start_time_est: Optional[str] = None):
        """Start the scheduler."""
        scheduler = BlockingScheduler()
        
        start_date = None
        if start_time_est:
            try:
                # Parse "HH:MM"
                hour, minute = map(int, start_time_est.split(":"))
                
                # Get current time in EST
                est = pytz.timezone("US/Eastern")
                now_est = datetime.now(est)
                
                # Create target time for today in EST
                target_est = now_est.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # If 10am has already passed today, schedule for tomorrow
                if target_est <= now_est:
                    target_est += timedelta(days=1)
                
                start_date = target_est
                logger.info(f"Scheduling first run for {start_date} (EST)")
            except Exception as e:
                logger.error(f"Failed to parse START_TIME_EST '{start_time_est}': {e}. Starting immediately.")
        
        # Add job with interval trigger
        scheduler.add_job(
            self.run_cycle,
            IntervalTrigger(hours=interval_hours, start_date=start_date),
            id="mvp_loop",
            name="MVP Loop",
            replace_existing=True,
        )
        
        if not start_date:
            # Run immediately only if no scheduled start
            logger.info("Running initial cycle...")
            self.run_cycle()
        else:
            logger.info(f"Waiting for scheduled start at {start_date}...")
        
        # Start scheduler
        logger.info(f"Scheduler started. Running every {interval_hours} hours.")
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")
