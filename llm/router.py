"""
Hybrid LLM Router
Routes between Grok (default) and Claude based on content type and persona.
"""

from typing import List, Optional, Literal
from enum import Enum
import re
import logging

from .grok_client import GrokClient
from .claude_client import ClaudeClient

logger = logging.getLogger(__name__)


class RouteDecision(Enum):
    """LLM routing decision."""
    GROK = "grok"
    CLAUDE = "claude"


# Keywords that trigger Claude routing
CLAUDE_TRIGGERS = {
    # Proverbs and wisdom
    "proverbs": ["methali", "proverb", "wisdom", "hekima", "wazee", "elders", "ancestors"],

    # Cultural and heritage
    "culture": ["heritage", "urithi", "traditional", "sherehe", "ceremony", "desturi", "mila", "customs"],

    # Empathy and family
    "empathy": ["miss", "home", "family", "nyumbani", "familia", "nyumba", "homesick", "remember", "moyo"],

    # Diaspora and nostalgia
    "diaspora": ["diaspora", "abroad", "ughaibuni", "immigration", "visa", "back home", "atlanta", "hartsfield", "marta", "remittance", "mpesa home"],

    # Reflective content
    "reflective": ["reflection", "kutafakari", "life", "journey", "maisha", "safari", "lessons", "growing up"],

    # Activism and poetry (Zuri)
    "activism": ["haki", "rights", "protest", "justice", "corruption", "civic", "poetry", "mashairi", "revolution", "tunaweza"],

    # Matriarch / women empowerment (Zawadi)
    "matriarch": ["sacco", "school fees", "ada", "watoto", "women empowerment", "mama", "mwanamke", "chama", "biashara ya mama"],

    # Diaspora-Atlanta specific
    "diaspora_atlanta": ["atlanta", "buckhead", "marta", "hartsfield", "jkia", "kenya airways", "perimeter", "i-285", "eldoret abroad", "nairobi from usa"],
}


def should_route_to_claude(
    topic: str,
    task: str = "original_post",
    persona_type: str = "default",
) -> tuple:
    """
    Decide whether to use Claude or Grok.

    Routing logic:
    - Default: Grok (fast, edgy, street energy)
    - Claude: Proverbs, diaspora, empathy, cultural wisdom, activism, matriarch content

    Args:
        topic: Topic/content being generated
        task: Type of task
        persona_type: Persona characteristics

    Returns:
        Tuple of (RouteDecision, trigger_score, matched_triggers, reason)
    """
    topic_lower = topic.lower()
    matched_triggers = []

    # Task-based routing
    if task == "diaspora":
        return RouteDecision.CLAUDE, 0, ["diaspora_task"], "Diaspora content requires Claude's cultural depth"

    # Check for Claude trigger keywords
    claude_score = 0
    for category, keywords in CLAUDE_TRIGGERS.items():
        for keyword in keywords:
            if keyword.lower() in topic_lower:
                claude_score += 1
                matched_triggers.append(keyword)
                logger.debug(f"Claude trigger: '{keyword}' in category '{category}'")

    # Route to Claude if 2+ triggers found
    if claude_score >= 2:
        logger.info(f"Routing to Claude (score: {claude_score})")
        reason = f"{claude_score} cultural triggers matched ({', '.join(matched_triggers)}) → Claude for nuanced content"
        return RouteDecision.CLAUDE, claude_score, matched_triggers, reason

    # Persona-based routing
    if persona_type in ("wise", "nurturing", "matriarch"):
        persona_triggers = [w for w in ["proverb", "methali", "wisdom", "hekima", "culture", "family", "familia", "sacco", "mwanamke"] if w in topic_lower]
        if persona_triggers:
            matched_triggers.extend(persona_triggers)
            reason = f"Wise/matriarch persona + topic keywords ({', '.join(persona_triggers)}) → Claude for cultural wisdom"
            return RouteDecision.CLAUDE, claude_score, matched_triggers, reason

    if persona_type == "diaspora":
        # Diaspora personas lean Claude for emotional/reflective content
        diaspora_triggers = [w for w in ["home", "nyumbani", "miss", "family", "familia", "kenya", "remember", "nostalgia"] if w in topic_lower]
        if diaspora_triggers:
            matched_triggers.extend(diaspora_triggers)
            reason = f"Diaspora persona + nostalgic keywords → Claude for authentic code-switching"
            return RouteDecision.CLAUDE, claude_score, matched_triggers, reason

    if persona_type == "activist":
        # Zuri should use Claude for poetic/reflective content
        activist_triggers = [w for w in ["poetry", "mashairi", "reflection", "kutafakari", "haki", "rights", "justice"] if w in topic_lower]
        if activist_triggers:
            matched_triggers.extend(activist_triggers)
            reason = f"Activist persona + poetic/reflective keywords → Claude for depth"
            return RouteDecision.CLAUDE, claude_score, matched_triggers, reason

    # Default to Grok
    logger.info(f"Routing to Grok (default, score: {claude_score})")
    reason = "Default — no cultural triggers found, using Grok for street energy"
    return RouteDecision.GROK, claude_score, matched_triggers, reason


class HybridRouter:
    """
    Hybrid LLM router that switches between Grok and Claude.
    """

    def __init__(self, grok_api_key: str, claude_api_key: str):
        self.grok = GrokClient(grok_api_key)
        self.claude = ClaudeClient(claude_api_key)

    def generate(
        self,
        topic: str,
        persona_description: str,
        rag_examples: List[str],
        task: str = "original_post",
        persona_type: str = "default",
        force_model: Optional[Literal["grok", "claude"]] = None,
    ) -> tuple:
        """
        Generate content using the appropriate LLM.

        Returns:
            Tuple of (generated_content, model_used, trigger_score, matched_triggers, reason)
        """
        if force_model:
            decision = RouteDecision.CLAUDE if force_model == "claude" else RouteDecision.GROK
            trigger_score, matched_triggers, reason = 0, [], f"Model forced to {force_model}"
        else:
            decision, trigger_score, matched_triggers, reason = should_route_to_claude(topic, task, persona_type)

        if decision == RouteDecision.CLAUDE:
            content = self.claude.generate_with_examples(
                topic=topic,
                persona_description=persona_description,
                rag_examples=rag_examples,
                task=task,
            )
            return content, "claude", trigger_score, matched_triggers, reason
        else:
            content = self.grok.generate_with_examples(
                topic=topic,
                persona_description=persona_description,
                rag_examples=rag_examples,
                task=task,
            )
            return content, "grok", trigger_score, matched_triggers, reason
