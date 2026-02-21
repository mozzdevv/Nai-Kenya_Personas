"""
Grok API Client
Uses OpenAI-compatible API with xAI base URL.
Supports Grok 4 family models (grok-4-fast, grok-4, grok-4.1, grok-4-heavy).
"""

from openai import OpenAI
from typing import Optional, List, Dict
import logging
import os

logger = logging.getLogger(__name__)

# Available Grok 4 models (in order of speed/cost efficiency)
# - grok-4-fast: Fastest, optimized for agentic tasks (RECOMMENDED for bots)
# - grok-4.1-fast: Ultra fast with 2M token context
# - grok-4: Advanced reasoning, 256K context
# - grok-4.1: Improved conversational quality
# - grok-4-heavy: Premium, highest reliability
GROK_MODEL_DEFAULT = "grok-4-fast"


class GrokClient:
    """Client for Grok API using OpenAI SDK."""
    
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )
        # Allow model override via env var or constructor
        self.model = model or os.getenv("GROK_MODEL", GROK_MODEL_DEFAULT)
    
    def generate(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.8,
        max_tokens: int = 280,
    ) -> str:
        """
        Generate text using Grok.
        
        Args:
            prompt: User prompt with context and examples
            system_prompt: System prompt with persona description
            temperature: Creativity (0.8 is good for street energy)
            max_tokens: Max response length (280 for tweets)
            
        Returns:
            Generated text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Grok generation error: {e}")
            raise
    
    def generate_with_examples(
        self,
        topic: str,
        persona_description: str,
        rag_examples: List[str],
        task: str = "original_post",
    ) -> str:
        """
        Generate content with RAG examples for authentic style.
        
        Args:
            topic: Topic to post about
            persona_description: Full persona description
            rag_examples: 3-8 example posts for style reference
            task: Type of content (original_post, quote_comment, reply)
            
        Returns:
            Generated tweet content
        """
        examples_text = "\n".join([f"- {ex}" for ex in rag_examples])
        
        system_prompt = f"""You are {persona_description}

Use the provided examples for natural Kiswahili/Sheng style. 
Generate content in your authentic voice - colloquial, street-smart, humorous.
NEVER use formal language. NEVER sound robotic.
CRITICAL FORMATTING: Never use em-dashes (—). Never end with an emoji. Emoji mid-sentence or skip entirely. Keep it raw and fragmented like real Nairobi Twitter.
Keep responses under 280 characters for Twitter."""
        
        if task == "original_post":
            user_prompt = f"""Topic: {topic}

Style examples from similar posts:
{examples_text}

Generate ONE original tweet about this topic in your authentic voice. Be natural, witty, relatable."""
        
        elif task == "quote_comment":
            user_prompt = f"""Original tweet to comment on:
{topic}

Style examples:
{examples_text}

Generate a SHORT (1-2 sentences) quote-tweet commentary in your voice. Be funny, empathetic, or use a proverb twist."""
        
        elif task == "reply":
            user_prompt = f"""Reply to this interaction:
{topic}

Style examples:
{examples_text}

Generate a friendly, engaging reply in your authentic voice."""
        
        else:
            user_prompt = f"""Task: {task}
Topic: {topic}

Style examples:
{examples_text}

Generate content in your voice."""
        
        return self.generate(user_prompt, system_prompt)
