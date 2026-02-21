"""
Pinecone Vector Store for RAG.
Stores and retrieves tweet examples for authentic style generation.
"""

from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Optional
import hashlib
import logging
from datetime import datetime

from .embeddings import get_embedding_generator

logger = logging.getLogger(__name__)


class PineconeStore:
    """Pinecone vector store for tweet examples."""
    
    def __init__(
        self,
        api_key: str,
        index_name: str = "nairobi-swahili-rag",
        dimension: int = 384,  # MiniLM-L6-v2 dimension
    ):
        """
        Initialize Pinecone store.
        
        Args:
            api_key: Pinecone API key
            index_name: Name of the index
            dimension: Embedding dimension (default matches sentence-transformers)
        """
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.dimension = dimension
        self.embedder = get_embedding_generator()
        
        # Create index if it doesn't exist
        self._ensure_index()
        self.index = self.pc.Index(index_name)
    
    def _ensure_index(self):
        """Create index if it doesn't exist."""
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            logger.info(f"Creating Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            logger.info(f"Index {self.index_name} created")
        else:
            logger.info(f"Using existing index: {self.index_name}")
    
    def _generate_id(self, text: str, source: str) -> str:
        """Generate unique ID for a tweet."""
        content = f"{source}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def store_tweets(
        self,
        tweets: List[Dict],
        source_account: str,
    ) -> int:
        """
        Store tweets in Pinecone for RAG retrieval.
        
        Args:
            tweets: List of tweet dicts with 'text', 'id', optional 'topics'
            source_account: Source account handle
            
        Returns:
            Number of tweets stored
        """
        if not tweets:
            return 0
        
        # Filter valid tweets first
        valid_tweets = []
        texts_to_embed = []
        
        for tweet in tweets:
            text = tweet.get("text", "")
            if text and len(text) >= 10:
                valid_tweets.append(tweet)
                texts_to_embed.append(text)
        
        if not valid_tweets:
            return 0
            
        # Generate embeddings in batch
        logger.info(f"Generating embeddings for {len(valid_tweets)} tweets...")
        embeddings = self.embedder.embed_batch(texts_to_embed)
        
        vectors = []
        for i, tweet in enumerate(valid_tweets):
            text = texts_to_embed[i]
            embedding = embeddings[i]
            
            # Create vector with metadata
            vector_id = self._generate_id(text, source_account)
            metadata = {
                "text": text[:1000],  # Pinecone metadata limit
                "source": source_account,
                "tweet_id": str(tweet.get("id", "")),
                "topics": tweet.get("topics", []),
                "stored_at": datetime.utcnow().isoformat(),
            }
            
            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": metadata,
            })
        
        # Upsert in batches of 100
        batch_size = 100
        stored = 0
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
            stored += len(batch)
        
        logger.info(f"Stored {stored} tweets from @{source_account}")
        return stored
    
    def retrieve_similar(
        self,
        query: str,
        top_k: int = 5,
        filter_source: Optional[str] = None,
        filter_topics: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Retrieve similar tweets for RAG.
        
        Args:
            query: Query text (topic or context)
            top_k: Number of results to return (3-8 recommended)
            filter_source: Optional filter by source account
            filter_topics: Optional filter by topics
            
        Returns:
            List of dicts with 'text', 'score', 'source', 'id'
        """
        # Generate query embedding
        query_embedding = self.embedder.embed(query)
        
        # Build filter
        filter_dict = {}
        if filter_source:
            filter_dict["source"] = filter_source
        if filter_topics:
            filter_dict["topics"] = {"$in": filter_topics}
        
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict if filter_dict else None,
        )
        
        # Extract results
        items = []
        for match in results.matches:
            if match.metadata and "text" in match.metadata:
                items.append({
                    "text": match.metadata["text"],
                    "score": match.score,
                    "source": match.metadata.get("source", "unknown"),
                    "id": match.id,
                })
        
        logger.info(f"Retrieved {len(items)} similar tweets for query: {query[:50]}...")
        return items
    
    def get_stats(self) -> Dict:
        """Get index statistics."""
        stats = self.index.describe_index_stats()
        return {
            "total_vectors": stats.total_vector_count,
            "dimension": stats.dimension,
        }
