#!/usr/bin/env python
"""
ClaimExtractorAgent - Identifies verifiable claims in news articles

Extracts factual claims that can be fact-checked from article content
"""

from pathlib import Path
from typing import Any
import json
import re
import sys

# Add project root to path for core imports
_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.core.core import get_agent_params
from src.core.logging import get_logger


class ClaimExtractorAgent:
    """Agent for extracting verifiable claims from news articles"""

    def __init__(self, config: dict[str, Any], api_key: str, base_url: str):
        """
        Initialize claim extractor agent

        Args:
            config: Complete configuration dictionary
            api_key: LLM API key
            base_url: LLM API endpoint
        """
        self.config = config
        self.api_key = api_key
        self.base_url = base_url
        self.logger = get_logger(name="claim_extractor_agent")

        # Load agent parameters from unified config
        self._agent_params = get_agent_params("fact_checker")

        self.logger.info("ClaimExtractorAgent initialized")

    async def extract_claims(self, article: dict[str, Any], max_claims: int = 5) -> list[dict[str, Any]]:
        """
        Extract verifiable claims from an article

        Args:
            article: Article dictionary with title and content
            max_claims: Maximum number of claims to extract

        Returns:
            List of claim dictionaries
        """
        try:
            title = article.get("title", "")
            content = article.get("content", "")

            if not content:
                self.logger.warning(f"No content in article: {title}")
                return []

            # Extract claims using LLM
            claims = await self._extract_with_llm(title, content, max_claims)

            # Add article context to each claim
            for claim in claims:
                claim["article_id"] = article.get("id")
                claim["article_title"] = title
                claim["source"] = article.get("source_name")

            self.logger.info(f"Extracted {len(claims)} claims from article: {title[:50]}...")
            return claims

        except Exception as e:
            self.logger.error(f"Error extracting claims: {e}")
            return []

    async def _extract_with_llm(self, title: str, content: str, max_claims: int) -> list[dict[str, Any]]:
        """
        Use LLM to extract verifiable claims from article

        Args:
            title: Article title
            content: Article content
            max_claims: Maximum claims to extract

        Returns:
            List of claims
        """
        try:
            from lightrag.llm.openai import openai_complete_if_cache

            # Build prompt
            system_prompt = """You are a fact-checking assistant that identifies verifiable claims in news articles.

Your task is to extract factual claims that can be verified through research. Focus on:
1. Specific factual statements (numbers, dates, events, quotes)
2. Claims that can be proven true or false
3. Statements attributed to specific sources
4. Statistical or scientific claims

Avoid:
- Opinions or subjective statements
- Predictions or speculation
- General statements without specifics
- Claims that are inherently unverifiable

For each claim, identify:
- The exact claim text
- The type of claim (statistical, event, quote, scientific)
- Who/what is making the claim
- Why it's important to verify

Output as JSON array."""

            user_prompt = f"""Article Title: {title}

Article Content:
{content[:2000]}  # Limit to first 2000 chars

Extract up to {max_claims} verifiable claims from this article.

Output format (JSON array):
[
  {{
    "claim": "The exact claim statement",
    "type": "statistical|event|quote|scientific|other",
    "subject": "Who/what the claim is about",
    "importance": "Why this claim matters",
    "context": "Surrounding context from article"
  }}
]"""

            response = await openai_complete_if_cache(
                model=self.get_model(),
                prompt=user_prompt,
                system_prompt=system_prompt,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=self._agent_params["temperature"],
                max_tokens=self._agent_params["max_tokens"],
                response_format={"type": "json_object"}
            )

            # Parse JSON response
            response_data = json.loads(response)

            # Handle both array and object with claims key
            if isinstance(response_data, list):
                claims = response_data
            elif "claims" in response_data:
                claims = response_data["claims"]
            else:
                claims = []

            return claims[:max_claims]

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Fallback to rule-based extraction
            return self._extract_with_rules(content, max_claims)

        except Exception as e:
            self.logger.error(f"LLM extraction failed: {e}")
            # Fallback to rule-based extraction
            return self._extract_with_rules(content, max_claims)

    def _extract_with_rules(self, content: str, max_claims: int) -> list[dict[str, Any]]:
        """
        Fallback: Extract claims using rule-based patterns

        Args:
            content: Article content
            max_claims: Maximum claims to extract

        Returns:
            List of claims
        """
        claims = []

        # Pattern 1: Quotes (attributed statements)
        quote_pattern = r'"([^"]+)"[,\s]+(?:said|stated|claimed|announced|reported)\s+([A-Z][^,.]+)'
        for match in re.finditer(quote_pattern, content):
            if len(claims) >= max_claims:
                break

            claims.append({
                "claim": match.group(1),
                "type": "quote",
                "subject": match.group(2).strip(),
                "importance": "Attributed statement",
                "context": content[max(0, match.start() - 100):match.end() + 100]
            })

        # Pattern 2: Statistical claims
        stat_pattern = r'(\d+(?:\.\d+)?%?)\s+(?:of|percent|million|billion|thousand)\s+([^.]+)'
        for match in re.finditer(stat_pattern, content):
            if len(claims) >= max_claims:
                break

            claims.append({
                "claim": match.group(0),
                "type": "statistical",
                "subject": match.group(2).strip(),
                "importance": "Statistical claim",
                "context": content[max(0, match.start() - 100):match.end() + 100]
            })

        # Pattern 3: Event claims (happened/occurred)
        event_pattern = r'([A-Z][^.]+(?:happened|occurred|took place|announced|launched|released)[^.]+)'
        for match in re.finditer(event_pattern, content):
            if len(claims) >= max_claims:
                break

            claims.append({
                "claim": match.group(1).strip(),
                "type": "event",
                "subject": "Event claim",
                "importance": "Factual event",
                "context": content[max(0, match.start() - 100):match.end() + 100]
            })

        self.logger.info(f"Rule-based extraction found {len(claims)} claims")
        return claims[:max_claims]

    def get_model(self) -> str:
        """Get LLM model name from environment"""
        import os
        env_model = os.getenv("LLM_MODEL")
        if not env_model:
            raise ValueError("Environment variable LLM_MODEL is not set")
        return env_model

    async def batch_extract(self, articles: list[dict[str, Any]], max_claims_per_article: int = 5) -> dict[str, list[dict[str, Any]]]:
        """
        Extract claims from multiple articles

        Args:
            articles: List of articles
            max_claims_per_article: Max claims per article

        Returns:
            Dictionary mapping article IDs to their claims
        """
        results = {}

        for article in articles:
            article_id = article.get("id")
            claims = await self.extract_claims(article, max_claims_per_article)
            results[article_id] = claims

        total_claims = sum(len(claims) for claims in results.values())
        self.logger.info(f"Extracted {total_claims} total claims from {len(articles)} articles")

        return results
