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
    """X API credentials for Kamau (@kamaukeeeraw)."""
    model_config = {"env_prefix": "KAMAU_", "env_file": ".env", "extra": "ignore"}


class WanjikuCredentials(XCredentials):
    """X API credentials for Wanjiku (@wanjikusagee)."""
    model_config = {"env_prefix": "WANJIKU_", "env_file": ".env", "extra": "ignore"}


class Settings(BaseSettings):
    """Main application settings."""
    
    # LLM API Keys
    grok_api_key: str = Field(..., env="GROK_API_KEY")
    claude_api_key: str = Field(..., env="CLAUDE_API_KEY")
    
    # Pinecone
    pinecone_api_key: str = Field(..., env="PINECONE_API_KEY")
    pinecone_index_name: str = Field(default="kikuyu-rag", env="PINECONE_INDEX_NAME")
    
    # Scheduler
    loop_interval_hours: float = Field(default=6.0, env="LOOP_INTERVAL_HOURS")
    dry_run: bool = Field(default=False, env="DRY_RUN")
    start_time_est: Optional[str] = Field(default=None, env="START_TIME_EST")
    
    # Persona credentials (loaded automatically if available)
    kamau: Optional[KamauCredentials] = Field(default_factory=lambda: KamauCredentials())
    wanjiku: Optional[WanjikuCredentials] = Field(default_factory=lambda: WanjikuCredentials())
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Seed accounts to monitor for content inspiration
SEED_ACCOUNTS = [
    # Kikuyu language & culture
    "kikuyutweets",
    "kikuyuproverb",
    "DrKanyuira",
    "mundu_useful",
    # Kenyan diaspora
    "kenyandiaspora",
    "kenya_usa",
    # Nairobi locals & commentary
    "Ma3Route",           # Nairobi matatu & transport culture
    "bonifaboreal",       # Nairobi street talk
    "KenyanTraffic",      # Daily life in Nairobi
    "naborealkenya",      # Nairobi events & culture
    "NairobiLeo",         # Nairobi news & city culture
    "KenyanHistory",      # Kenyan cultural history
    "MutahiKagwe",        # Kenyan public discourse
    "Kilonje_Africa",     # Pan-African cultural commentary
    "OleItumbi",          # Kenyan political commentary
    "NjorogeWaKariuki",   # Kikuyu community voices
    "KenyanVibe",         # Pop culture & daily vibes
    "NairobiNights",      # Nairobi nightlife & social scene
]

# Topics/keywords for content filtering
# ── Grok-dominant topics (street/edgy energy, everyday life) ──
# ── Claude-dominant topics contain 2+ trigger keywords from CLAUDE_TRIGGERS ──
TOPICS = {
    # === GROK-ROUTED (everyday, street, edgy) ===
    "politics": [
        "siasa", "parliament", "ruto", "raila", "uhuru",
        "azimio", "kenya kwanza", "genZ protests", "hustler fund",
        "taxes ni mob sana", "county government corruption",
    ],
    "daily": [
        "jioni", "asubuhi", "traffic", "jam", "matatu",
        "fare", "rent", "bei", "Nairobi hustle at dawn",
        "Thika Road jam at 6am", "water shortage in Eastlands",
        "blackout tena last night", "landlord drama in pipeline",
    ],
    "food": [
        "nyama", "ugali", "sukuma", "chapati", "pilau", "mandazi", "chai",
        "mutura at the roadside", "smokie pasua Nairobi style",
        "githeri for lunch again", "rolex ya Uganda vs Kenya chapati",
    ],
    "hustle": [
        "hustler", "side hustle", "biashara", "pesa", "kazi", "tuma kazi",
        "betting addiction ruining youth", "mpesa float business",
        "boda boda economy in Nairobi", "jua kali innovation",
    ],

    # === CLAUDE-ROUTED (cultural depth, wisdom, nostalgia) ===
    # These topics contain 2+ trigger keywords → score ≥ 2 → Claude
    "proverbs_wisdom": [
        "kikuyu proverb about wisdom from our ancestors",
        "kĩugo from the elders about life lessons",
        "traditional wisdom and proverb our cucu used to say",
        "ancestors' thimo about family and heritage",
        "mũndũ mũgo elders and the wisdom they carried",
        "proverb from growing up about the journey of life",
        "gĩkũyũ wisdom about customs and ceremony",
        "elders proverb about heritage and family bonds",
    ],
    "diaspora_nostalgia": [
        "diaspora life abroad missing home and family",
        "kenyan in marekani remembering back home vibes",
        "atlanta georgia diaspora missing nyũmba ya cucu",
        "immigration journey and visa hustle from back home",
        "diaspora abroad homesick for mũciĩ and family",
        "growing up in kenya then moving abroad — the journey",
        "diaspora life lessons from marekani to back home",
        "miss home family gatherings during holidays abroad",
    ],
    "family_home": [
        "family traditions at mũciĩ during December",
        "nyũmba ya cucu — the home we all miss and remember",
        "growing up in a kikuyu family and the lessons learned",
        "family ceremony at home — customs and heritage",
        "miss the moyo of home and family dinners",
        "homesick for family and the life we had back home",
        "wisdom from grandma at home about family and heritage",
        "family journey from rural home to Nairobi maisha",
    ],
    "ceremonies_traditions": [
        "traditional gĩkũyũ ceremony and customs we must preserve",
        "heritage of our ancestors — traditional ceremony practices",
        "mũgĩthi ceremony and the customs of our elders",
        "gĩkũyũ traditional ceremony for family and ancestors",
        "elders performing ceremony with wisdom and heritage",
        "customs and traditional practices vanishing — heritage at risk",
        "ceremony of remembrance for ancestors and family",
        "traditional wedding customs and ceremony in gĩkũyũ heritage",
    ],
    "reflection_identity": [
        "reflection on life and the journey of maisha",
        "growing up kikuyu — lessons and wisdom from the safari of life",
        "life reflection on family, heritage, and where we come from",
        "the journey of a kenyan — lessons from home to diaspora",
        "safari of life — wisdom from elders about growing up",
        "reflection on ancestors and the heritage they left behind",
        "maisha lessons — remember where you come from, family first",
        "journey of self-discovery and remembering our customs",
    ],
    # === BALANCED (has some cultural keywords but mixed) ===
    "culture": [
        "gĩkũyũ heritage and our identity",
        "kikuyu traditional music and dance",
        "mũgĩthi nights heritage celebration",
        "traditional food customs passed down",
        "heritage month — celebrating ancestors",
        "kikuyu ceremony — rite of passage customs",
    ],
}

# Create global settings instance
settings = Settings()
