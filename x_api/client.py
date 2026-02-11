"""
X API Client
OAuth 1.0a client for posting, quoting, retweeting, and replying.
"""

import tweepy
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class XClient:
    """X/Twitter API client for a single persona."""
    
    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        access_token: str,
        access_token_secret: str,
        bearer_token: str,
        persona_name: str = "Unknown",
    ):
        """
        Initialize X client with OAuth 1.0a credentials.
        
        Args:
            consumer_key: API Key
            consumer_secret: API Secret
            access_token: User access token
            access_token_secret: User access token secret
            bearer_token: Bearer token for read operations
            persona_name: Name for logging
        """
        self.persona_name = persona_name
        
        # OAuth 1.0a client for posting (user context)
        self.client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True,
        )
        
        # OAuth 2.0 client for reading (app context)
        self.read_client = tweepy.Client(
            bearer_token=bearer_token,
            wait_on_rate_limit=True,
        )
        
        logger.info(f"X client initialized for {persona_name}")
    
    def post_tweet(self, text: str, dry_run: bool = False) -> Optional[Dict]:
        """
        Post a tweet.
        
        Args:
            text: Tweet text (max 280 chars)
            dry_run: If True, don't actually post
            
        Returns:
            Tweet data dict or None
        """
        if len(text) > 280:
            text = text[:277] + "..."
            logger.warning(f"Tweet truncated to 280 chars")
        
        if dry_run:
            logger.info(f"[DRY RUN] Would post: {text}")
            return {"id": "dry_run", "text": text}
        
        try:
            response = self.client.create_tweet(text=text)
            tweet_id = response.data["id"]
            logger.info(f"[@{self.persona_name}] Posted tweet: {tweet_id}")
            return {"id": tweet_id, "text": text}
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            raise
    
    def quote_tweet(
        self,
        quote_tweet_id: str,
        comment: str,
        dry_run: bool = False,
    ) -> Optional[Dict]:
        """
        Quote a tweet with commentary.
        
        Args:
            quote_tweet_id: ID of tweet to quote
            comment: Commentary to add
            dry_run: If True, don't actually post
            
        Returns:
            Tweet data dict or None
        """
        if len(comment) > 250:  # Leave room for quote
            comment = comment[:247] + "..."
        
        if dry_run:
            logger.info(f"[DRY RUN] Would quote {quote_tweet_id}: {comment}")
            return {"id": "dry_run", "quote_id": quote_tweet_id, "text": comment}
        
        try:
            response = self.client.create_tweet(
                text=comment,
                quote_tweet_id=quote_tweet_id,
            )
            tweet_id = response.data["id"]
            logger.info(f"[@{self.persona_name}] Quote tweeted: {tweet_id}")
            return {"id": tweet_id, "quote_id": quote_tweet_id, "text": comment}
        except Exception as e:
            logger.error(f"Failed to quote tweet: {e}")
            raise
    
    def retweet(self, tweet_id: str, dry_run: bool = False) -> bool:
        """
        Retweet a tweet.
        
        Args:
            tweet_id: ID of tweet to retweet
            dry_run: If True, don't actually retweet
            
        Returns:
            Success boolean
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would retweet: {tweet_id}")
            return True
        
        try:
            # Get authenticated user ID first
            me = self.client.get_me()
            user_id = me.data.id
            
            self.client.retweet(tweet_id=tweet_id, user_auth=True)
            logger.info(f"[@{self.persona_name}] Retweeted: {tweet_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to retweet: {e}")
            return False
    
    def reply_to_tweet(
        self,
        tweet_id: str,
        reply_text: str,
        dry_run: bool = False,
    ) -> Optional[Dict]:
        """
        Reply to a tweet.
        
        Args:
            tweet_id: ID of tweet to reply to
            reply_text: Reply content
            dry_run: If True, don't actually reply
            
        Returns:
            Tweet data dict or None
        """
        if len(reply_text) > 280:
            reply_text = reply_text[:277] + "..."
        
        if dry_run:
            logger.info(f"[DRY RUN] Would reply to {tweet_id}: {reply_text}")
            return {"id": "dry_run", "reply_to": tweet_id, "text": reply_text}
        
        try:
            response = self.client.create_tweet(
                text=reply_text,
                in_reply_to_tweet_id=tweet_id,
            )
            new_tweet_id = response.data["id"]
            logger.info(f"[@{self.persona_name}] Replied to {tweet_id}: {new_tweet_id}")
            return {"id": new_tweet_id, "reply_to": tweet_id, "text": reply_text}
        except Exception as e:
            logger.error(f"Failed to reply: {e}")
            raise
    
    def get_my_mentions(self, max_results: int = 10) -> List[Dict]:
        """
        Get recent mentions of this account.
        
        Args:
            max_results: Maximum mentions to fetch
            
        Returns:
            List of mention tweet dicts
        """
        try:
            me = self.client.get_me()
            user_id = me.data.id
            
            mentions = self.client.get_users_mentions(
                id=user_id,
                max_results=max_results,
                tweet_fields=["created_at", "author_id", "text"],
            )
            
            if not mentions.data:
                return []
            
            return [
                {
                    "id": str(tweet.id),
                    "text": tweet.text,
                    "author_id": str(tweet.author_id),
                    "created_at": str(tweet.created_at),
                }
                for tweet in mentions.data
            ]
        except Exception as e:
            logger.error(f"Failed to get mentions: {e}")
            return []
