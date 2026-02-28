"""
Personas Module
Centralized persona initialization and management.
All 6 personas: Juma, Amani, Baraka, Zawadi, Zuri, John, Karen.
"""

from .base import (
    JumaPersona, AmaniPersona, BarakaPersona,
    ZawadiPersona, ZuriPersona, JohnPersona, KarenPersona
)


def get_personas():
    """
    Get initialized persona instances.

    Returns:
        tuple: (JumaPersona, AmaniPersona, BarakaPersona, ZawadiPersona, ZuriPersona, JohnPersona, KarenPersona)
    """
    _defaults = dict(name="", handle="", description="", personality_traits=[],
                     topics=[], signature_phrases=[], proverb_style="")

    juma = JumaPersona(tone="sarcastic", persona_type="edgy", **_defaults)
    amani = AmaniPersona(tone="wise", persona_type="nurturing", **_defaults)
    baraka = BarakaPersona(tone="dry", persona_type="modern", **_defaults)
    zawadi = ZawadiPersona(tone="wise", persona_type="matriarch", **_defaults)
    zuri = ZuriPersona(tone="passionate", persona_type="activist", **_defaults)
    john = JohnPersona(tone="reflective", persona_type="diaspora", **_defaults)
    karen = KarenPersona(tone="energetic", persona_type="diaspora", **_defaults)

    return juma, amani, baraka, zawadi, zuri, john, karen
