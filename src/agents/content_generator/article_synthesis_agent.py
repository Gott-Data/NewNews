#!/usr/bin/env python
"""
ArticleSynthesisAgent - Generates summaries from multiple news sources

Creates comprehensive summaries by combining information from multiple articles
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


class ArticleSynthesisAgent:
    """Agent for synthesizing articles from multiple sources"""

    def __init__(self, config: dict[str, Any], api_key: str, base_url: str):
        """Initialize article synthesis agent"""
        self.config = config
        self.api_key = api_key
        self.base_url = base_url
        self.logger = get_logger(name="article_synthesis_agent")

        self._agent_params = get_agent_params("content_generator")

        self.synthesis_config = config.get("content_generation", {}).get("articles", {})
        self.auto_generate = self.synthesis_config.get("auto_generate_summaries", True)
        self.min_sources = self.synthesis_config.get("min_sources_for_synthesis", 3)
        self.max_length = self.synthesis_config.get("max_summary_length", 500)

        self.logger.info("ArticleSynthesisAgent initialized")

    async def synthesize_from_sources(
        self,
        articles: list[dict[str, Any]],
        topic: str | None = None
    ) -> dict[str, Any]:
        """
        Synthesize a summary from multiple article sources

        Args:
            articles: List of source articles
            topic: Optional topic focus

        Returns:
            Synthesized article with summary
        """
        if len(articles) < self.min_sources:
            return {
                "success": False,
                "error": f"Need at least {self.min_sources} sources, got {len(articles)}"
            }

        self.logger.info(f"Synthesizing article from {len(articles)} sources")

        # Extract relevant information
        sources_info = []
        for article in articles:
            sources_info.append({
                "source": article.get("source_name", "Unknown"),
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", "")[:1000],  # Limit content length
                "published": article.get("published_at", "")
            })

        # Generate synthesis using LLM
        synthesis = await self._generate_synthesis(sources_info, topic)

        return {
            "success": True,
            "synthesis": synthesis,
            "source_count": len(articles),
            "sources": [a.get("source_name") for a in articles]
        }

    async def _generate_synthesis(
        self,
        sources: list[dict[str, Any]],
        topic: str | None
    ) -> dict[str, Any]:
        """Use LLM to generate synthesis from sources"""
        try:
            from lightrag.llm.openai import openai_complete_if_cache
            import os

            # Build sources text
            sources_text = "\n\n".join([
                f"Source {i+1}: {s['source']}\nTitle: {s['title']}\nContent: {s['description']}"
                for i, s in enumerate(sources)
            ])

            system_prompt = """You are a news synthesis expert who combines information from multiple sources into a comprehensive, balanced summary.

Your task is to:
1. Identify the core facts that multiple sources agree on
2. Note any conflicting information between sources
3. Create a balanced, objective summary
4. Attribute different perspectives to their sources
5. Maintain journalistic integrity and avoid bias

Output as JSON with the synthesized article."""

            topic_text = f" focusing on: {topic}" if topic else ""
            user_prompt = f"""Synthesize a comprehensive news summary{topic_text} from these sources:

{sources_text}

Create a balanced summary of approximately {self.max_length} words.

Output format (JSON):
{{
  "title": "Synthesized headline that captures the story",
  "summary": "Comprehensive summary combining all sources",
  "key_points": ["bullet", "point", "list"],
  "agreements": "What sources agree on",
  "conflicts": "Any conflicting information between sources",
  "word_count": number
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
            self.logger.error(f"LLM synthesis failed: {e}")
            # Fallback: simple concatenation
            return self._simple_synthesis(sources)

    def _simple_synthesis(self, sources: list[dict[str, Any]]) -> dict[str, Any]:
        """Fallback: simple rule-based synthesis"""
        # Use first source as base
        title = sources[0]["title"]

        # Combine descriptions
        descriptions = [s["description"] for s in sources if s["description"]]
        combined = " ".join(descriptions)

        # Truncate to max length
        words = combined.split()[:self.max_length]
        summary = " ".join(words)

        return {
            "title": title,
            "summary": summary,
            "key_points": [s["title"] for s in sources[:5]],
            "agreements": "Multiple sources reporting same story",
            "conflicts": "None detected",
            "word_count": len(words)
        }

    async def generate_daily_digest(
        self,
        articles: list[dict[str, Any]],
        max_stories: int = 10
    ) -> dict[str, Any]:
        """
        Generate a daily news digest

        Args:
            articles: All articles from the day
            max_stories: Maximum stories in digest

        Returns:
            Daily digest with top stories
        """
        from collections import defaultdict

        # Group articles by similarity (same topic)
        topic_groups = defaultdict(list)

        for article in articles:
            # Use category as rough topic grouping
            category = article.get("category", "general")
            topic_groups[category].append(article)

        # Synthesize top story from each category
        digest_stories = []

        for category, category_articles in list(topic_groups.items())[:max_stories]:
            if len(category_articles) >= 2:  # Need multiple sources
                synthesis = await self.synthesize_from_sources(
                    category_articles[:5],  # Top 5 articles per category
                    topic=category
                )

                if synthesis.get("success"):
                    digest_stories.append({
                        "category": category,
                        **synthesis["synthesis"]
                    })

        return {
            "success": True,
            "date": articles[0].get("published_at", "")[:10] if articles else "",
            "story_count": len(digest_stories),
            "stories": digest_stories
        }
