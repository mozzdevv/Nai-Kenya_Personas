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
    "proverbs": ["kĩugo", "proverb", "wisdom", "elders", "ancestors", "mũndũ mũgo", "thimo"],
    
    # Cultural and heritage
    "culture": ["heritage", "traditional", "ceremony", "mũgĩthi", "gĩkũyũ", "ancestors", "customs"],
    
    # Empathy and family
    "empathy": ["miss", "home", "family", "mũciĩ", "nyũmba", "homesick", "remember", "moyo"],
    
    # Diaspora and nostalgia
    "diaspora": ["diaspora", "abroad", "marekani", "atlanta", "georgia", "immigration", "visa", "back home"],
    
    # Reflective content
    "reflective": ["reflection", "life", "journey", "maisha", "safari", "lessons", "growing up"],
}


def should_route_to_claude(
    topic: str,
    task: str = "original_post",
    persona_type: str = "default",
) -> RouteDecision:
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
        RouteDecision.GROK or RouteDecision.CLAUDE
    """
    topic_lower = topic.lower()
    
    # Task-based routing
    if task == "diaspora":
        return RouteDecision.CLAUDE
    
    # Check for Claude trigger keywords
    claude_score = 0
    for category, keywords in CLAUDE_TRIGGERS.items():
        for keyword in keywords:
            if keyword.lower() in topic_lower:
                claude_score += 1
                logger.debug(f"Claude trigger: '{keyword}' in category '{category}'")
    
    # Route to Claude if 2+ triggers found
    if claude_score >= 2:
        logger.info(f"Routing to Claude (score: {claude_score})")
        return RouteDecision.CLAUDE
    
    # Persona-based routing
    if persona_type == "wise" or persona_type == "nurturing":
        # Wanjiku-type personas benefit from Claude for wisdom
        if any(word in topic_lower for word in ["proverb", "wisdom", "culture", "family"]):
            return RouteDecision.CLAUDE
    
    # Default to Grok
    logger.info(f"Routing to Grok (default, score: {claude_score})")
    return RouteDecision.GROK


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
    ) -> tuple[str, str]:
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
            Tuple of (generated_content, model_used)
        """
        # Determine which model to use
        if force_model:
            decision = RouteDecision.CLAUDE if force_model == "claude" else RouteDecision.GROK
        else:
            decision = should_route_to_claude(topic, task, persona_type)
        
        # Generate with appropriate client
        if decision == RouteDecision.CLAUDE:
            content = self.claude.generate_with_examples(
                topic=topic,
                persona_description=persona_description,
                rag_examples=rag_examples,
                task=task,
            )
            return content, "claude"
        else:
            content = self.grok.generate_with_examples(
                topic=topic,
                persona_description=persona_description,
                rag_examples=rag_examples,
                task=task,
            )
            return content, "grok"
