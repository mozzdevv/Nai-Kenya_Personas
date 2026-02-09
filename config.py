"""
Kikuyu Project - Configuration Management
Pydantic settings for API credentials and app configuration.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class XCredentials(BaseSettings):
    """X API credentials for a single persona."""
    consumer_key: str
    consumer_secret: str
    access_token: str
    access_token_secret: str
    bearer_token: str


class KamauCredentials(XCredentials):
    """X API credentials for Kamau (@KamauRawKE)."""
    model_config = {"env_prefix": "KAMAU_"}


class WanjikuCredentials(XCredentials):
    """X API credentials for Wanjiku (@WanjikuSage)."""
    model_config = {"env_prefix": "WANJIKU_"}


class Settings(BaseSettings):
    """Main application settings."""
    
    # LLM API Keys
    grok_api_key: str = Field(..., env="GROK_API_KEY")
    claude_api_key: str = Field(..., env="CLAUDE_API_KEY")
    
    # Pinecone
    pinecone_api_key: str = Field(..., env="PINECONE_API_KEY")
    pinecone_index_name: str = Field(default="kikuyu-rag", env="PINECONE_INDEX_NAME")
    
    # Scheduler
    loop_interval_hours: int = Field(default=6, env="LOOP_INTERVAL_HOURS")
    dry_run: bool = Field(default=False, env="DRY_RUN")
    
    # Persona credentials (loaded separately)
    kamau: Optional[KamauCredentials] = None
    wanjiku: Optional[WanjikuCredentials] = None
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load persona credentials
        self.kamau = KamauCredentials()
        self.wanjiku = WanjikuCredentials()


# Seed accounts to monitor for content inspiration
SEED_ACCOUNTS = [
    "kikuyutweets",
    "kikuyuproverb", 
    "DrKanyuira",
    "mundu_useful",
    "kenyandiaspora",
    "kenya_usa",
]

# Topics/keywords for content filtering
TOPICS = {
    "politics": ["siasa", "parliament", "ruto", "raila", "uhuru", "azimio", "kenya kwanza"],
    "culture": ["gĩkũyũ", "kikuyu", "mũgĩthi", "traditional", "heritage", "ancestors"],
    "daily": ["jioni", "asubuhi", "traffic", "jam", "matatu", "fare", "rent", "bei"],
    "food": ["nyama", "ugali", "sukuma", "chapati", "pilau", "mandazi", "chai"],
    "hustle": ["hustler", "side hustle", "biashara", "pesa", "kazi", "tuma kazi"],
}

# Create global settings instance
settings = Settings()
