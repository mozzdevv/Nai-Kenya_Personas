"""
Claude API Client
For nuanced content: proverbs, diaspora, empathy, cultural wisdom.
"""

import anthropic
from typing import List
import logging

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Client for Claude API using Anthropic SDK."""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def generate(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 280,
    ) -> str:
        """
        Generate text using Claude.
        
        Args:
            prompt: User prompt with context and examples
            system_prompt: System prompt with persona description
            temperature: Creativity (0.7 for nuanced content)
            max_tokens: Max response length
            
        Returns:
            Generated text
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Claude generation error: {e}")
            raise
    
    def generate_with_examples(
        self,
        topic: str,
        persona_description: str,
        rag_examples: List[str],
        task: str = "original_post",
    ) -> str:
        """
        Generate nuanced content with RAG examples.
        
        Best for:
        - Deep proverbs and cultural wisdom
        - Family/empathy/diaspora nostalgia
        - Reflective comparisons
        - High idiomatic precision
        
        Args:
            topic: Topic to post about
            persona_description: Full persona description
            rag_examples: 3-8 example posts for style reference
            task: Type of content
            
        Returns:
            Generated tweet content
        """
        examples_text = "\n".join([f"- {ex}" for ex in rag_examples])
        
        system_prompt = f"""You are {persona_description}

You are creating authentic Kikuyu/Kiswahili/Sheng content. 
Use the provided examples to capture the natural rhythm and idioms.
Focus on cultural depth, proverbs, empathy, and relatable wisdom.
Keep responses under 280 characters for Twitter.
Be warm, wise, and genuine - never formal or robotic."""
        
        if task == "original_post":
            user_prompt = f"""Topic: {topic}

Style examples from similar posts:
{examples_text}

Generate ONE original tweet about this topic. Weave in cultural wisdom, proverbs, or heartfelt observation. Be authentic and relatable."""
        
        elif task == "quote_comment":
            user_prompt = f"""Original tweet to comment on:
{topic}

Style examples:
{examples_text}

Generate a SHORT quote-tweet commentary. Use a proverb, empathetic observation, or cultural wisdom. Be warm and wise."""
        
        elif task == "reply":
            user_prompt = f"""Reply to this interaction:
{topic}

Style examples:
{examples_text}

Generate a warm, wise reply that shows cultural depth and empathy."""
        
        elif task == "diaspora":
            user_prompt = f"""Topic (diaspora perspective): {topic}

Style examples:
{examples_text}

Generate content reflecting on the topic from a diaspora perspective. Express nostalgia, reflection, or comparison between home and abroad."""
        
        else:
            user_prompt = f"""Task: {task}
Topic: {topic}

Style examples:
{examples_text}

Generate culturally rich content in your voice."""
        
        return self.generate(user_prompt, system_prompt)
