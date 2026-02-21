"""
Personas Module
Centralized persona initialization and management.
"""

from .base import JumaPersona, AmaniPersona

def get_personas():
    """
    Get initialized persona instances.
    
    Returns:
        tuple: (JumaPersona, AmaniPersona)
    """
    juma = JumaPersona(
        name="", handle="", description="", tone="sarcastic",
        personality_traits=[], topics=[], signature_phrases=[],
        proverb_style="", persona_type="edgy"
    )
    
    amani = AmaniPersona(
        name="", handle="", description="", tone="wise",
        personality_traits=[], topics=[], signature_phrases=[],
        proverb_style="", persona_type="nurturing"
    )
    
    return juma, amani
