"""
Hybrid LLM Router
Routes between Grok (default) and Claude based on content type.
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
    "diaspora": ["diaspora", "abroad", "ughaibuni", "immigration", "visa", "back home"],
    
    # Reflective content
    "reflective": ["reflection", "kutafakari", "life", "journey", "maisha", "safari", "lessons", "growing up"],
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
    - Claude: Proverbs, diaspora, empathy, cultural wisdom, high idiomatic precision
    
    Args:
        topic: Topic/content being generated
        task: Type of task (original_post, quote_comment, reply, diaspora)
        persona_type: Persona characteristics (e.g., "wise", "sarcastic")
        
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
    if persona_type == "wise" or persona_type == "nurturing":
        persona_triggers = [w for w in ["proverb", "methali", "wisdom", "hekima", "culture", "family", "familia"] if w in topic_lower]
        if persona_triggers:
            matched_triggers.extend(persona_triggers)
            reason = f"Wise persona + topic keywords ({', '.join(persona_triggers)}) → Claude for cultural wisdom"
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
        
        Args:
            topic: Topic to generate about
            persona_description: Full persona description
            rag_examples: RAG examples for style reference
            task: Type of content
            persona_type: Persona characteristics for routing
            force_model: Override routing decision
            
        Returns:
            Tuple of (generated_content, model_used, trigger_score, matched_triggers, reason)
        """
        # Determine which model to use
        if force_model:
            decision = RouteDecision.CLAUDE if force_model == "claude" else RouteDecision.GROK
            trigger_score, matched_triggers, reason = 0, [], f"Model forced to {force_model}"
        else:
            decision, trigger_score, matched_triggers, reason = should_route_to_claude(topic, task, persona_type)
        
        # Generate with appropriate client
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
