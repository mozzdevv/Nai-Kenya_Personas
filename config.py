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


class BarakaCredentials(XCredentials):
    """X API credentials for Baraka (@barakaO254)."""
    model_config = {"env_prefix": "BARAKA_", "env_file": ".env", "extra": "ignore"}


class ZawadiCredentials(XCredentials):
    """X API credentials for Mama Zawadi (@zawadi_naks)."""
    model_config = {"env_prefix": "ZAWADI_", "env_file": ".env", "extra": "ignore"}


class ZuriCredentials(XCredentials):
    """X API credentials for Zuri (@zuriadhiambo_)."""
    model_config = {"env_prefix": "ZURI_", "env_file": ".env", "extra": "ignore"}


class JohnCredentials(XCredentials):
    """X API credentials for John (@njuguna_atl)."""
    model_config = {"env_prefix": "JOHN_", "env_file": ".env", "extra": "ignore"}


class KarenCredentials(XCredentials):
    """X API credentials for Karen (@karenkips_)."""
    model_config = {"env_prefix": "KAREN_", "env_file": ".env", "extra": "ignore"}


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

    # Persona credentials
    kamau: Optional[KamauCredentials] = Field(default_factory=lambda: KamauCredentials())
    wanjiku: Optional[WanjikuCredentials] = Field(default_factory=lambda: WanjikuCredentials())
    baraka: Optional[BarakaCredentials] = Field(default_factory=lambda: _safe_load(BarakaCredentials))
    zawadi: Optional[ZawadiCredentials] = Field(default_factory=lambda: _safe_load(ZawadiCredentials))
    zuri: Optional[ZuriCredentials] = Field(default_factory=lambda: _safe_load(ZuriCredentials))
    john: Optional[JohnCredentials] = Field(default_factory=lambda: _safe_load(JohnCredentials))
    karen: Optional[KarenCredentials] = Field(default_factory=lambda: _safe_load(KarenCredentials))

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def _safe_load(cls):
    """Load credentials safely — returns None if any required field is missing/placeholder."""
    try:
        creds = cls()
        # Reject placeholder values
        placeholder = "PLACEHOLDER_ADD_FROM_DEVELOPER_PORTAL"
        if creds.access_token == placeholder or creds.access_token_secret == placeholder:
            return None
        return creds
    except Exception:
        return None


# Seed accounts to monitor for content inspiration
# Covers: Nairobi street, Rift Valley/upcountry, Lake/Kisumu, tech/Silicon Savannah, diaspora
SEED_ACCOUNTS = [
    # Nairobi street & commentary
    "Ma3Route",           # Nairobi matatu & transport culture
    "_CrazyNairobian",    # Witty Nairobi storytelling
    "bonifacemwangi",     # Nairobi activist, social justice
    "GabrielOguda",       # Political commentary, Swahili-English mix
    "EricOmondi",         # Comedy, viral content, social campaigns
    "KenyanTraffic",      # Daily life in Nairobi
    "naborealkenya",      # Nairobi events & culture
    # News & national culture
    "NairobiLeo",         # Nairobi news & city culture
    "KenyanHistory",      # Kenyan cultural history
    "MutahiKagwe",        # Kenyan public discourse
    "Kilonje_Africa",     # Pan-African cultural commentary
    # Politics & commentary
    "OleItumbi",          # Kenyan political commentary
    "KenyanVibe",         # Pop culture & daily vibes
    "NairobiNights",      # Nairobi nightlife & social scene
    # Rift Valley / upcountry voices
    "nakurucity",         # Nakuru city news & life
    "RiftValleyKenya",    # Rift Valley regional news
    # Lake region / Kisumu voices
    "KisumuCity",         # Kisumu city updates
    "LakeVictoriaKE",     # Lake Victoria environment & culture
    # Tech / Silicon Savannah
    "iLabAfrica",         # Nairobi tech hub culture
    "ictauthorityke",     # Kenya ICT & digital economy
    "DisruptAfrica",      # African startup & tech news
    # Gen Z / activism
    "GenzKenya",          # Gen Z Kenya movement
    # Kenyan diaspora (US-based)
    "kenyandiaspora",
    "kenya_usa",
    "KenyansinUSA",
    "KenyanDiaspora1",  # replaced @KenyansInAtlanta (>15 chars, caused 400 errors)
]

# Topics/keywords for content generation
# ── Grok-dominant (street/edgy/everyday) ──
# ── Claude-dominant (2+ trigger keywords from CLAUDE_TRIGGERS) ──
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

    # === GROK-ROUTED: Tech & Gig Economy (Baraka) ===
    "tech_gig": [
        "silicon savannah nairobi tech scene",
        "data labeling job for AI company paying peanuts",
        "MPESA API integration fintech Kenya",
        "startup culture Westlands Nairobi",
        "WiFi imekatika during client call tena",
        "KPLC outage during deadline remote work life",
        "gig economy content moderation kenya",
        "safaricom data bundles bei kubwa sana",
        "remote work from Nairobi for foreign company",
        "AI replacing Kenyan gig workers fear",
        "Github commit at midnight Nairobi developer life",
    ],

    # === GROK-ROUTED: Upcountry Life (Zawadi / Rift Valley) ===
    "upcountry_life": [
        "maize fertilizer bei imepanda tena Nakuru",
        "SACCO loan kuanza biashara Rift Valley",
        "school fees pressure form one",
        "Nakuru town market prices vs Nairobi",
        "unga bei imepanda tena family budget",
        "landlord wa Nakuru vs Nairobi same drama",
        "Rift Valley roads barabara imeharibiwa tena",
        "Eldoret to Nakuru road trip matatu",
        "small business hustle mama mboga Nakuru",
        "women chama SACCO savings group Kenya",
        "borehole water shortage rural Rift Valley",
    ],

    # === GROK-ROUTED: WhatsApp/TikTok/Social Culture ===
    "whatsapp_social": [
        "WhatsApp group admin kuondoa watu ovyo",
        "family WhatsApp group drama at 3am",
        "TikTok Kenya trending video ya leo",
        "Facebook Marketplace scam Kenya onyo",
        "WhatsApp status yangu leo asubuhi",
        "TikTok influencer Kenya bei ya bidhaa",
        "Facebook group Kenya buy and sell",
        "Instagram ya Kenya vs ukweli wa maisha",
        "social media influencer life Kenya fake",
        "WhatsApp voice note badala ya kupiga simu",
    ],

    # === GROK-ROUTED: Gen Z Activism (Zuri / Kisumu) ===
    "gen_z_activism": [
        "GenZ Kenya standing up for haki yetu",
        "corruption Kenya bado inaendelea bila aibu",
        "Kisumu protests solidarity na wapigania haki",
        "Lake Victoria environment pollution serikali haziangalii",
        "youth unemployment Kenya serikali iko wapi",
        "GenZ finance bill protests streets nairobi kisumu",
        "Kisumu lakeside vibes usiku wa mwisho wa wiki",
        "poetry for Kenya revolution maneno ya ukweli",
        "civic education youth kenya tunaweza",
        "Kondele Kisumu life ukweli wa barabarani",
        "Maseno university student life Kisumu",
    ],

    # === CLAUDE-ROUTED: Diaspora Atlanta (John & Karen) ===
    "diaspora_atlanta": [
        "diaspora life Atlanta missing nyumbani Kenya",
        "Hartsfield airport landing Kenya Airways flight home",
        "MARTA Atlanta commute vs Nairobi matatu memories",
        "sending MPESA remittance home familia Kenya",
        "Kenyan community Atlanta diaspora meetup chapati",
        "watching Citizen TV online from Atlanta missing news",
        "property investment Kenya from diaspora abroad",
        "school fees kids in USA vs back home Kenya",
        "diaspora abroad homesick for family gatherings nyumbani",
        "immigration visa stress Kenyan in America journey",
        "Atlanta traffic Perimeter vs Thika Road memories",
        "Buckhead Atlanta Kenyan restaurant nyama choma",
        "diaspora Kenyan second generation kids culture gap",
    ],

    # === CLAUDE-ROUTED (cultural depth, wisdom, nostalgia) ===
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
    "culture": [
        "urithi wetu na utambulisho wa Kikenya",
        "muziki wa jadi wa Kenya na ngoma",
        "usiku wa burudani Nairobi",
        "mila za chakula zilizopitishwa na wazee",
        "mwezi wa urithi — kusherehekea wazee",
        "sherehe za kale — mila na desturi zetu",
    ],
}

# ── Per-persona topic pools ──────────────────────────────────────────────────
# Each key matches persona.credentials_key in personas/base.py.
# Only topics in this list will be used when generating posts for that persona.
# Falls back to ALL topics if a key is missing (shouldn't happen).
PERSONA_TOPICS = {
    # Juma — Eastlands street hustler. Politics, daily Nairobi grind, food, hustle, social media noise.
    "kamau": [
        "politics",
        "daily",
        "hustle",
        "food",
        "whatsapp_social",
    ],
    # Amani — Wise/cultural, NGO sector. Proverbs, family, traditions, culture, reflection.
    "wanjiku": [
        "proverbs_wisdom",
        "family_home",
        "ceremonies_traditions",
        "culture",
        "reflection_identity",
    ],
    # Baraka — Tech/gig worker in Westlands. Tech, Nairobi daily, hustle, social media, some politics.
    "baraka": [
        "tech_gig",
        "daily",
        "hustle",
        "whatsapp_social",
        "politics",
    ],
    # Mama Zawadi — Matriarch in Nakuru. Upcountry life, food, family, proverbs.
    "zawadi": [
        "upcountry_life",
        "food",
        "family_home",
        "proverbs_wisdom",
    ],
    # Zuri — Gen Z activist, Kisumu. Activism, reflection, culture, social media.
    "zuri": [
        "gen_z_activism",
        "reflection_identity",
        "culture",
        "whatsapp_social",
    ],
    # John — Diaspora lawyer, Atlanta. Diaspora Atlanta, nostalgia, reflection, family.
    "john": [
        "diaspora_atlanta",
        "diaspora_nostalgia",
        "reflection_identity",
        "family_home",
    ],
    # Karen — Diaspora realtor, Atlanta. Diaspora Atlanta, hustle, social media, traditions.
    "karen": [
        "diaspora_atlanta",
        "diaspora_nostalgia",
        "hustle",
        "whatsapp_social",
        "ceremonies_traditions",
    ],
}

# Create global settings instance
settings = Settings()
