"""
Database Module
SQLite database for activity logging and dashboard data.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from contextlib import contextmanager
import json
import logging

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "nairobi.db"


def init_db():
    """Initialize database with schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Posts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tweet_id TEXT UNIQUE,
            persona TEXT NOT NULL,
            content TEXT NOT NULL,
            post_type TEXT NOT NULL,  -- original, quote, reply
            llm_used TEXT NOT NULL,   -- grok, claude
            quoted_tweet_id TEXT,
            reply_to_id TEXT,
            likes INTEGER DEFAULT 0,
            retweets INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            authenticity_score INTEGER DEFAULT 0,
            validation_issues TEXT,  -- JSON array of issues/warnings
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            dry_run BOOLEAN DEFAULT FALSE
        )
    """)
    
    # RAG activity table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rag_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,  -- fetch, store, retrieve
            source TEXT,
            tweet_count INTEGER DEFAULT 0,
            query TEXT,
            results_count INTEGER DEFAULT 0,
            details TEXT,  -- JSON array of retrieved items
            persona TEXT,  -- which persona triggered the action
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # LLM routing decisions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS llm_routing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            task TEXT NOT NULL,
            persona TEXT NOT NULL,
            decision TEXT NOT NULL,  -- grok, claude
            trigger_score INTEGER DEFAULT 0,
            triggers_matched TEXT,  -- JSON array
            reason TEXT,  -- human-readable explanation
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Error logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,      -- error, warning
            component TEXT NOT NULL,  -- x_api, llm, rag, scheduler
            message TEXT NOT NULL,
            traceback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Engagement metrics history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS engagement_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tweet_id TEXT NOT NULL,
            likes INTEGER DEFAULT 0,
            retweets INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Knowledge Base table (RAG source items)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            content TEXT NOT NULL,
            topics TEXT,  -- JSON array
            vector_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    
    # Migrations for existing databases — add new columns safely
    migrations = [
        ("rag_activity", "persona", "TEXT"),
        ("llm_routing", "reason", "TEXT"),
        ("posts", "authenticity_score", "INTEGER DEFAULT 0"),
        ("posts", "validation_issues", "TEXT"),
    ]
    for table, column, coltype in migrations:
        try:
            cursor = conn.cursor()
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
    
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


@contextmanager
def get_db():
    """Get database connection context manager."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class ActivityLogger:
    """Log bot activity to database."""
    
    @staticmethod
    def log_post(
        tweet_id: str,
        persona: str,
        content: str,
        post_type: str,
        llm_used: str,
        quoted_tweet_id: Optional[str] = None,
        reply_to_id: Optional[str] = None,
        dry_run: bool = False,
        authenticity_score: int = 0,
        validation_issues: Optional[List[str]] = None,
    ):
        """Log a post to the database."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO posts 
                (tweet_id, persona, content, post_type, llm_used, 
                 quoted_tweet_id, reply_to_id, dry_run,
                 authenticity_score, validation_issues)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (tweet_id, persona, content, post_type, llm_used,
                  quoted_tweet_id, reply_to_id, dry_run,
                  authenticity_score,
                  json.dumps(validation_issues) if validation_issues else None))
            conn.commit()
    
    @staticmethod
    def log_knowledge_batch(items: List[Dict]):
        """
        Log multiple items to knowledge base in one transaction.
        
        Args:
            items: List of dicts containing 'source', 'content', 'topics', 'vector_id'
        """
        if not items:
            return
            
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Filter duplicates based on content
            contents = [item["content"] for item in items]
            placeholders = ",".join(["?"] * len(contents))
            
            cursor.execute(f"SELECT content FROM knowledge_base WHERE content IN ({placeholders})", contents)
            existing_contents = {row[0] for row in cursor.fetchall()}
            
            # Prepare new items
            new_items = []
            for item in items:
                if item["content"] not in existing_contents:
                    new_items.append((
                        item["source"], 
                        item["content"], 
                        json.dumps(item["topics"]), 
                        item.get("vector_id")
                    ))
            
            if new_items:
                cursor.executemany("""
                    INSERT INTO knowledge_base 
                    (source, content, topics, vector_id)
                    VALUES (?, ?, ?, ?)
                """, new_items)
                conn.commit()
                logger.info(f"Batch logged {len(new_items)} items to Knowledge Base")

    @staticmethod
    def log_rag_activity(
        action: str,
        source: Optional[str] = None,
        tweet_count: int = 0,
        query: Optional[str] = None,
        results_count: int = 0,
        details: Optional[List[Dict]] = None,
        persona: Optional[str] = None,
    ):
        """Log RAG activity."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rag_activity 
                (action, source, tweet_count, query, results_count, details, persona)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (action, source, tweet_count, query, results_count, 
                  json.dumps(details) if details else None, persona))
            conn.commit()
    
    @staticmethod
    def log_llm_routing(
        topic: str,
        task: str,
        persona: str,
        decision: str,
        trigger_score: int = 0,
        triggers_matched: Optional[List[str]] = None,
        reason: Optional[str] = None,
    ):
        """Log LLM routing decision."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO llm_routing 
                (topic, task, persona, decision, trigger_score, triggers_matched, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (topic, task, persona, decision, trigger_score,
                  json.dumps(triggers_matched or []), reason))
            conn.commit()
    
    @staticmethod
    def log_error(
        level: str,
        component: str,
        message: str,
        traceback: Optional[str] = None,
    ):
        """Log an error."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO errors (level, component, message, traceback)
                VALUES (?, ?, ?, ?)
            """, (level, component, message, traceback))
            conn.commit()
    
    @staticmethod
    def update_engagement(tweet_id: str, likes: int, retweets: int, replies: int):
        """Update engagement metrics for a post."""
        with get_db() as conn:
            cursor = conn.cursor()
            # Update posts table
            cursor.execute("""
                UPDATE posts SET likes = ?, retweets = ?, replies = ?
                WHERE tweet_id = ?
            """, (likes, retweets, replies, tweet_id))
            # Add to history
            cursor.execute("""
                INSERT INTO engagement_history 
                (tweet_id, likes, retweets, replies)
                VALUES (?, ?, ?, ?)
            """, (tweet_id, likes, retweets, replies))
            conn.commit()


class DashboardQueries:
    """Query methods for dashboard API."""
    
    @staticmethod
    def get_recent_posts(limit: int = 50) -> List[Dict]:
        """Get recent posts."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM posts 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_post_stats() -> Dict:
        """Get post statistics."""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Total posts by persona
            cursor.execute("""
                SELECT persona, COUNT(*) as count 
                FROM posts GROUP BY persona
            """)
            by_persona = {row["persona"]: row["count"] for row in cursor.fetchall()}
            
            # Total by post type
            cursor.execute("""
                SELECT post_type, COUNT(*) as count 
                FROM posts GROUP BY post_type
            """)
            by_type = {row["post_type"]: row["count"] for row in cursor.fetchall()}
            
            # Total engagement
            cursor.execute("""
                SELECT SUM(likes) as likes, SUM(retweets) as retweets, 
                       SUM(replies) as replies
                FROM posts
            """)
            row = cursor.fetchone()
            engagement = {
                "likes": row["likes"] or 0,
                "retweets": row["retweets"] or 0,
                "replies": row["replies"] or 0,
            }
            
            return {
                "by_persona": by_persona,
                "by_type": by_type,
                "engagement": engagement,
            }
    
    @staticmethod
    def get_rag_activity(limit: int = 50) -> List[Dict]:
        """Get recent RAG activity."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM rag_activity 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
            
    @staticmethod
    def get_knowledge_base(limit: int = 100) -> List[Dict]:
        """Get knowledge base items."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM knowledge_base 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            rows = []
            for row in cursor.fetchall():
                d = dict(row)
                if d["topics"]:
                    try:
                        d["topics"] = json.loads(d["topics"])
                    except:
                        d["topics"] = []
                rows.append(d)
            return rows
    
    @staticmethod
    def get_llm_routing_stats() -> Dict:
        """Get LLM routing statistics."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT decision, COUNT(*) as count 
                FROM llm_routing GROUP BY decision
            """)
            return {row["decision"]: row["count"] for row in cursor.fetchall()}
    
    @staticmethod
    def get_llm_routing_history(limit: int = 50) -> List[Dict]:
        """Get recent LLM routing decisions."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM llm_routing 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_errors(limit: int = 100, level: Optional[str] = None) -> List[Dict]:
        """Get recent errors."""
        with get_db() as conn:
            cursor = conn.cursor()
            if level:
                cursor.execute("""
                    SELECT * FROM errors 
                    WHERE level = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (level, limit))
            else:
                cursor.execute("""
                    SELECT * FROM errors 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]


# Initialize database on import
init_db()
