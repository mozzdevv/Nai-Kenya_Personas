"""
Nairobi Swahili Bot Project - Configuration Management
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
    """X API credentials for Juma (@kamaukeeeraw)."""
    model_config = {"env_prefix": "KAMAU_", "env_file": ".env", "extra": "ignore"}


class WanjikuCredentials(XCredentials):
    """X API credentials for Amani (@wanjikusagee)."""
    model_config = {"env_prefix": "WANJIKU_", "env_file": ".env", "extra": "ignore"}


class Settings(BaseSettings):
    """Main application settings."""
    
    # LLM API Keys
    grok_api_key: str = Field(..., env="GROK_API_KEY")
    claude_api_key: str = Field(..., env="CLAUDE_API_KEY")
    
    # Pinecone
    pinecone_api_key: str = Field(..., env="PINECONE_API_KEY")
    pinecone_index_name: str = Field(default="nairobi-swahili-rag", env="PINECONE_INDEX_NAME")
    
    # Scheduler
    loop_interval_hours: float = Field(default=6.0, env="LOOP_INTERVAL_HOURS")
    dry_run: bool = Field(default=False, env="DRY_RUN")
    start_time_est: Optional[str] = Field(default=None, env="START_TIME_EST")
    
    # Persona credentials (loaded automatically if available)
    kamau: Optional[KamauCredentials] = Field(default_factory=lambda: KamauCredentials())
    wanjiku: Optional[WanjikuCredentials] = Field(default_factory=lambda: WanjikuCredentials())
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Seed accounts to monitor for content inspiration
# Focused on Swahili-speaking Nairobi voices and Kenyan culture
SEED_ACCOUNTS = [
    # Nairobi locals & street commentary
    "Ma3Route",           # Nairobi matatu & transport culture
    "_CrazyNairobian",    # Billy the Goat — witty Nairobi storytelling
    "bonifacemwangi",     # Nairobi activist, social justice commentary
    "GabrielOguda",       # Political commentary, witty Swahili-English mix
    "EricOmondi",         # Comedy, viral content, social campaigns
    "KenyanTraffic",      # Daily life in Nairobi
    "naborealkenya",      # Nairobi events & culture
    # News & culture
    "NairobiLeo",         # Nairobi news & city culture
    "KenyanHistory",      # Kenyan cultural history
    "MutahiKagwe",        # Kenyan public discourse
    "Kilonje_Africa",     # Pan-African cultural commentary
    # Community & vibes
    "OleItumbi",          # Kenyan political commentary
    "KenyanVibe",         # Pop culture & daily vibes
    "NairobiNights",      # Nairobi nightlife & social scene
    # Kenyan diaspora
    "kenyandiaspora",
    "kenya_usa",
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
        "methali ya wazee kuhusu hekima ya maisha",
        "hekima kutoka kwa wazee wetu kuhusu familia",
        "methali ya zamani kuhusu maisha na safari",
        "wazee walikuwa na hekima kubwa kuhusu desturi",
        "methali kuhusu upendo na familia ya nyumbani",
        "hekima ya bibi kuhusu maisha na mila",
        "wazee na methali zao za kale kuhusu ustawi",
        "hekima na mila za watu wetu tangu zamani",
    ],
    "diaspora_nostalgia": [
        "diaspora life abroad missing home and family",
        "kenyan abroad remembering back home vibes",
        "maisha ya ughaibuni na kukumbuka nyumbani",
        "immigration journey and visa hustle from back home",
        "diaspora abroad homesick for nyumbani na familia",
        "growing up in kenya then moving abroad — the journey",
        "diaspora maisha and lessons from abroad to back home",
        "miss home family gatherings during holidays abroad",
    ],
    "family_home": [
        "familia na mila za nyumbani wakati wa December",
        "nyumba ya bibi — the home we all miss and remember",
        "growing up in a Kenyan family na masomo ya maisha",
        "sherehe ya familia nyumbani — desturi na mila",
        "miss the warmth of home and family dinners",
        "homesick for familia and the maisha we had back home",
        "hekima from grandma at home about familia and heritage",
        "family journey from rural home to Nairobi maisha",
    ],
    "ceremonies_traditions": [
        "sherehe za jadi na desturi tunazopaswa kuhifadhi",
        "urithi wa wazee wetu — sherehe za jadi",
        "sherehe ya familia na mila za wazee wetu",
        "desturi za jadi za familia yetu na wazee",
        "wazee wakifanya sherehe kwa hekima na urithi",
        "desturi na mila za zamani zinapotea — urithi hatarini",
        "sherehe ya kumbukumbu ya wazee na familia",
        "desturi za harusi na sherehe katika urithi wetu",
    ],
    "reflection_identity": [
        "kutafakari maisha na safari ya maisha",
        "growing up Kenyan — masomo na hekima from the safari of life",
        "kutafakari juu ya familia, urithi, na asili yetu",
        "safari ya Mkenya — masomo from home to diaspora",
        "safari ya maisha — hekima kutoka wazee kuhusu kukua",
        "kutafakari juu ya wazee na urithi waliotuachia",
        "masomo ya maisha — kumbuka ulikotoka, familia kwanza",
        "safari ya kujitambua na kukumbuka mila zetu",
    ],
    # === BALANCED (has some cultural keywords but mixed) ===
    "culture": [
        "urithi wetu na utambulisho wa Kikenya",
        "muziki wa jadi wa Kenya na ngoma",
        "usiku wa burudani Nairobi",
        "mila za chakula zilizopitishwa na wazee",
        "mwezi wa urithi — kusherehekea wazee",
        "sherehe za kale — mila na desturi zetu",
    ],
}

# Create global settings instance
settings = Settings()
