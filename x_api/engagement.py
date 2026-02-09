"""
Engagement Scoring
Score posts for quote-worthiness based on engagement metrics.
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


# Default engagement thresholds
DEFAULT_THRESHOLDS = {
    "min_likes": 20,
    "min_retweets": 5,
    "min_replies": 10,
}


def calculate_engagement_score(tweet: Dict) -> float:
    """
    Calculate engagement score for a tweet.
    
    Weights:
    - Likes: 1x
    - Retweets: 3x (more valuable, shows resonance)
    - Replies: 2x (shows conversation potential)
    
    Args:
        tweet: Tweet dict with likes, retweets, replies
        
    Returns:
        Engagement score (float)
    """
    likes = tweet.get("likes", 0)
    retweets = tweet.get("retweets", 0)
    replies = tweet.get("replies", 0)
    
    score = (likes * 1.0) + (retweets * 3.0) + (replies * 2.0)
    return score


def meets_engagement_threshold(
    tweet: Dict,
    min_likes: int = 20,
    min_retweets: int = 5,
    min_replies: int = 10,
) -> bool:
    """
    Check if tweet meets engagement thresholds.
    
    A tweet meets threshold if it passes ANY of the criteria.
    
    Args:
        tweet: Tweet dict with engagement metrics
        min_likes: Minimum likes threshold
        min_retweets: Minimum retweets threshold
        min_replies: Minimum replies threshold
        
    Returns:
        True if tweet meets any threshold
    """
    likes = tweet.get("likes", 0)
    retweets = tweet.get("retweets", 0)
    replies = tweet.get("replies", 0)
    
    return (
        likes >= min_likes or
        retweets >= min_retweets or
        replies >= min_replies
    )


def filter_engaging_tweets(
    tweets: List[Dict],
    thresholds: Optional[Dict] = None,
    max_results: int = 10,
) -> List[Dict]:
    """
    Filter and sort tweets by engagement.
    
    Args:
        tweets: List of tweet dicts
        thresholds: Custom thresholds dict
        max_results: Maximum results to return
        
    Returns:
        Filtered and sorted list of engaging tweets
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS
    
    # Filter by threshold
    engaging = [
        tweet for tweet in tweets
        if meets_engagement_threshold(
            tweet,
            min_likes=thresholds.get("min_likes", 20),
            min_retweets=thresholds.get("min_retweets", 5),
            min_replies=thresholds.get("min_replies", 10),
        )
    ]
    
    # Calculate scores and sort
    for tweet in engaging:
        tweet["engagement_score"] = calculate_engagement_score(tweet)
    
    engaging.sort(key=lambda x: x["engagement_score"], reverse=True)
    
    logger.info(f"Found {len(engaging)} engaging tweets out of {len(tweets)}")
    return engaging[:max_results]


def select_for_quote_tweet(
    tweets: List[Dict],
    already_quoted: List[str],
    max_daily: int = 3,
) -> List[Dict]:
    """
    Select tweets for quote-tweeting.
    
    Filters:
    - Engagement threshold
    - Not already quoted
    - Respects daily limit
    
    Args:
        tweets: Candidate tweets
        already_quoted: List of tweet IDs already quoted
        max_daily: Maximum quotes per day
        
    Returns:
        Selected tweets for quoting
    """
    # Filter engaging tweets
    engaging = filter_engaging_tweets(tweets)
    
    # Filter out already quoted
    new_candidates = [
        tweet for tweet in engaging
        if tweet.get("id") not in already_quoted
    ]
    
    # Select top candidates up to daily limit
    selected = new_candidates[:max_daily]
    
    logger.info(f"Selected {len(selected)} tweets for quote-tweeting")
    return selected
