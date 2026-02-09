"""
MVP Loop Scheduler
APScheduler-based loop that runs every 4-12 hours.
"""

import logging
import random
from datetime import datetime
from typing import List, Dict, Optional
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import settings, SEED_ACCOUNTS, TOPICS
from llm.router import HybridRouter
from rag.pinecone_store import PineconeStore
from x_api.client import XClient
from x_api.retrieval import SeedRetriever
from x_api.engagement import filter_engaging_tweets, select_for_quote_tweet
from personas.base import KamauPersona, WanjikuPersona, Persona

logger = logging.getLogger(__name__)


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
    
    def generate_original_post(self, topic: str) -> str:
        """Generate an original post on a topic."""
        # Get RAG examples
        examples = self.rag.retrieve_similar(topic, top_k=5)
        
        # Generate using hybrid router
        content, model_used = self.router.generate(
            topic=topic,
            persona_description=self.persona.get_system_prompt(),
            rag_examples=examples,
            task="original_post",
            persona_type=self.persona.persona_type,
        )
        
        logger.info(f"[{self.persona.handle}] Generated post using {model_used}: {content[:50]}...")
        return content
    
    def generate_quote_comment(self, original_tweet: Dict) -> str:
        """Generate a quote-tweet comment."""
        examples = self.rag.retrieve_similar(original_tweet["text"], top_k=3)
        
        content, model_used = self.router.generate(
            topic=original_tweet["text"],
            persona_description=self.persona.get_system_prompt(),
            rag_examples=examples,
            task="quote_comment",
            persona_type=self.persona.persona_type,
        )
        
        logger.info(f"[{self.persona.handle}] Generated quote using {model_used}")
        return content
    
    def run_posting_cycle(self, topic: Optional[str] = None):
        """Run a single posting cycle: 1-2 original posts."""
        if topic is None:
            # Pick random topic category
            category = random.choice(list(TOPICS.keys()))
            topic = random.choice(TOPICS[category])
        
        # Generate and post
        content = self.generate_original_post(topic)
        result = self.x_client.post_tweet(content, dry_run=self.dry_run)
        
        if result:
            logger.info(f"[{self.persona.handle}] Posted: {result}")
        
        return result
    
    def run_quote_cycle(self, engaging_tweets: List[Dict]):
        """Run quote-tweet cycle on engaging content."""
        # Select tweets to quote
        to_quote = select_for_quote_tweet(
            engaging_tweets,
            already_quoted=self.quoted_tweet_ids,
            max_daily=2,
        )
        
        for tweet in to_quote:
            comment = self.generate_quote_comment(tweet)
            result = self.x_client.quote_tweet(
                quote_tweet_id=tweet["id"],
                comment=comment,
                dry_run=self.dry_run,
            )
            
            if result:
                self.quoted_tweet_ids.append(tweet["id"])
                logger.info(f"[{self.persona.handle}] Quoted tweet: {tweet['id']}")
    
    def run_reply_cycle(self):
        """Check and reply to mentions."""
        mentions = self.x_client.get_my_mentions(max_results=5)
        
        for mention in mentions:
            # Generate reply
            examples = self.rag.retrieve_similar(mention["text"], top_k=3)
            
            reply, _ = self.router.generate(
                topic=mention["text"],
                persona_description=self.persona.get_system_prompt(),
                rag_examples=examples,
                task="reply",
                persona_type=self.persona.persona_type,
            )
            
            self.x_client.reply_to_tweet(
                tweet_id=mention["id"],
                reply_text=reply,
                dry_run=self.dry_run,
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
            # Add topic tags
            for tweet in tweets:
                tweet["topics"] = self._tag_topics(tweet["text"])
            
            stored = self.rag_store.store_tweets(
                tweets=tweets,
                source_account="seed_mix",
            )
            logger.info(f"Stored {stored} tweets in RAG")
        
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
    
    def start(self, interval_hours: int = 6):
        """Start the scheduler."""
        scheduler = BlockingScheduler()
        
        # Add job with interval trigger
        scheduler.add_job(
            self.run_cycle,
            IntervalTrigger(hours=interval_hours),
            id="mvp_loop",
            name="MVP Loop",
            replace_existing=True,
        )
        
        # Run immediately on start
        logger.info("Running initial cycle...")
        self.run_cycle()
        
        # Start scheduler
        logger.info(f"Scheduler started. Running every {interval_hours} hours.")
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")
