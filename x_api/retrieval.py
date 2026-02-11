"""
X API Retrieval
Fetch posts from seed accounts for RAG ingestion.
"""

import tweepy
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SeedRetriever:
    """Retrieve posts from seed accounts for RAG."""
    
    def __init__(self, bearer_token: str):
        """
        Initialize retriever with bearer token.
        
        Args:
            bearer_token: X API bearer token for app-only auth
        """
        self.client = tweepy.Client(
            bearer_token=bearer_token,
            wait_on_rate_limit=True,
        )
    
    def get_user_id(self, username: str) -> Optional[str]:
        """Get user ID from username."""
        try:
            user = self.client.get_user(username=username)
            if user.data:
                return str(user.data.id)
        except Exception as e:
            logger.error(f"Failed to get user ID for @{username}: {e}")
        return None
    
    def fetch_user_tweets(
        self,
        username: str,
        max_results: int = 20,
        exclude_replies: bool = True,
        exclude_retweets: bool = True,
    ) -> List[Dict]:
        """
        Fetch recent tweets from a user.
        
        Args:
            username: Twitter handle (without @)
            max_results: Maximum tweets to fetch (10-100)
            exclude_replies: Exclude reply tweets
            exclude_retweets: Exclude retweets
            
        Returns:
            List of tweet dicts with text, id, metrics
        """
        user_id = self.get_user_id(username)
        if not user_id:
            return []
        
        exclude = []
        if exclude_replies:
            exclude.append("replies")
        if exclude_retweets:
            exclude.append("retweets")
        
        try:
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=min(max_results, 100),
                exclude=exclude if exclude else None,
                tweet_fields=["created_at", "public_metrics", "text"],
            )
            
            if not tweets.data:
                logger.info(f"No tweets found for @{username}")
                return []
            
            results = []
            for tweet in tweets.data:
                metrics = tweet.public_metrics or {}
                results.append({
                    "id": str(tweet.id),
                    "text": tweet.text,
                    "created_at": str(tweet.created_at),
                    "likes": metrics.get("like_count", 0),
                    "retweets": metrics.get("retweet_count", 0),
                    "replies": metrics.get("reply_count", 0),
                    "source": username,
                })
            
            logger.info(f"Fetched {len(results)} tweets from @{username}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to fetch tweets from @{username}: {e}")
            return []
    
    def fetch_from_seed_accounts(
        self,
        seed_accounts: List[str],
        max_per_account: int = 20,
    ) -> List[Dict]:
        """
        Fetch tweets from multiple seed accounts.
        
        Args:
            seed_accounts: List of usernames to fetch from
            max_per_account: Max tweets per account
            
        Returns:
            Combined list of tweets from all accounts
        """
        all_tweets = []
        
        for username in seed_accounts:
            tweets = self.fetch_user_tweets(
                username=username,
                max_results=max_per_account,
            )
            all_tweets.extend(tweets)
        
        logger.info(f"Total fetched: {len(all_tweets)} tweets from {len(seed_accounts)} accounts")
        return all_tweets
    
    def search_recent_tweets(
        self,
        query: str,
        max_results: int = 20,
    ) -> List[Dict]:
        """
        Search for recent tweets matching a query.
        
        Args:
            query: Search query (supports X search operators)
            max_results: Maximum results (10-100)
            
        Returns:
            List of matching tweet dicts
        """
        try:
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),
                tweet_fields=["created_at", "public_metrics", "author_id"],
            )
            
            if not tweets.data:
                return []
            
            results = []
            for tweet in tweets.data:
                metrics = tweet.public_metrics or {}
                results.append({
                    "id": str(tweet.id),
                    "text": tweet.text,
                    "author_id": str(tweet.author_id),
                    "likes": metrics.get("like_count", 0),
                    "retweets": metrics.get("retweet_count", 0),
                    "replies": metrics.get("reply_count", 0),
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []
