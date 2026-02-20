#!/usr/bin/env python
"""
HeadlineGeneratorAgent - Creates engaging, unbiased headlines

Generates attention-grabbing headlines while maintaining journalistic integrity
"""

from pathlib import Path
from typing import Any
import json
import sys

_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.core.core import get_agent_params
from src.core.logging import get_logger


class HeadlineGeneratorAgent:
    """Agent for generating news headlines"""

    def __init__(self, config: dict[str, Any], api_key: str, base_url: str):
        """Initialize headline generator agent"""
        self.config = config
        self.api_key = api_key
        self.base_url = base_url
        self.logger = get_logger(name="headline_generator_agent")
        self._agent_params = get_agent_params("content_generator")
        self.logger.info("HeadlineGeneratorAgent initialized")

    async def generate_headline(
        self,
        article: dict[str, Any],
        style: str = "balanced"
    ) -> dict[str, Any]:
        """
        Generate headline for an article

        Args:
            article: Article dictionary
            style: Headline style (balanced, engaging, factual)

        Returns:
            Generated headlines with variants
        """
        content = f"{article.get('title', '')} {article.get('description', '')}"

        if not content.strip():
            return {
                "success": False,
                "error": "No content to generate headline from"
            }

        self.logger.info(f"Generating {style} headline")

        try:
            result = await self._generate_with_llm(content, style)
            return {
                "success": True,
                **result
            }

        except Exception as e:
            self.logger.error(f"Headline generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": self._generate_simple_headline(article)
            }

    async def _generate_with_llm(self, content: str, style: str) -> dict[str, Any]:
        """Use LLM to generate headlines"""
        try:
            from lightrag.llm.openai import openai_complete_if_cache
            import os

            style_instructions = {
                "balanced": "objective, factual, and neutral",
                "engaging": "attention-grabbing while maintaining accuracy",
                "factual": "straightforward and fact-focused"
            }

            instruction = style_instructions.get(style, "balanced and professional")

            system_prompt = f"""You are a professional news headline writer.

Create {instruction} headlines that:
1. Accurately summarize the story
2. Are clear and concise (under 100 characters)
3. Avoid sensationalism and clickbait
4. Maintain journalistic integrity
5. Are free of bias

Output multiple headline variants as JSON."""

            user_prompt = f"""Create 3 headline variants for this news story:

{content[:500]}

Output format (JSON):
{{
  "primary": "Main headline recommendation",
  "variants": ["Alternative 1", "Alternative 2"],
  "character_count": number,
  "style": "{style}"
}}"""

            response = await openai_complete_if_cache(
                model=os.getenv("LLM_MODEL"),
                prompt=user_prompt,
                system_prompt=system_prompt,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=self._agent_params["temperature"],
                max_tokens=self._agent_params["max_tokens"],
                response_format={"type": "json_object"}
            )

            result = json.loads(response)
            return result

        except Exception as e:
            self.logger.error(f"LLM headline generation failed: {e}")
            raise

    def _generate_simple_headline(self, article: dict[str, Any]) -> str:
        """Fallback: extract headline from title"""
        title = article.get("title", "")

        # Clean up existing title
        title = title.strip()

        # Remove source attribution if present
        if " - " in title:
            title = title.split(" - ")[0]

        # Truncate to reasonable length
        if len(title) > 100:
            title = title[:97] + "..."

        return title

    async def batch_generate(
        self,
        articles: list[dict[str, Any]],
        style: str = "balanced"
    ) -> list[dict[str, Any]]:
        """
        Generate headlines for multiple articles

        Args:
            articles: List of articles
            style: Headline style

        Returns:
            Articles with generated headlines
        """
        results = []

        for article in articles:
            headline_result = await self.generate_headline(article, style)

            article_with_headline = article.copy()
            article_with_headline["generated_headline"] = headline_result

            results.append(article_with_headline)

        return results
