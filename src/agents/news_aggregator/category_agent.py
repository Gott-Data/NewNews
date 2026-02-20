#!/usr/bin/env python
"""
CategoryAgent - Auto-categorizes news articles

Uses keywords, content analysis, and ML classification to assign categories
"""

from typing import Any
import re

from src.core.logging import get_logger


class CategoryAgent:
    """Agent for categorizing news articles"""

    # Category keywords for rule-based classification
    CATEGORY_KEYWORDS = {
        "technology": [
            "ai", "artificial intelligence", "tech", "software", "hardware", "smartphone",
            "computer", "internet", "cyber", "digital", "app", "algorithm", "data", "cloud",
            "startup", "innovation", "gadget", "programming", "blockchain", "cryptocurrency"
        ],
        "science": [
            "research", "study", "scientist", "discovery", "experiment", "university",
            "laboratory", "physics", "biology", "chemistry", "astronomy", "climate",
            "vaccine", "medical", "health research", "genetics", "nasa", "space"
        ],
        "health": [
            "health", "medical", "doctor", "hospital", "disease", "treatment", "patient",
            "medicine", "therapy", "diagnosis", "covid", "pandemic", "virus", "vaccine",
            "nutrition", "mental health", "wellness", "fitness"
        ],
        "business": [
            "business", "company", "economy", "market", "stock", "finance", "investment",
            "ceo", "revenue", "profit", "merger", "acquisition", "startup", "venture capital",
            "trade", "commerce", "industry", "corporate", "earnings"
        ],
        "politics": [
            "government", "president", "minister", "parliament", "congress", "election",
            "vote", "political", "policy", "legislation", "democracy", "republican",
            "democrat", "party", "senate", "law", "regulation", "diplomat"
        ],
        "sports": [
            "sport", "game", "team", "player", "coach", "championship", "tournament",
            "league", "football", "soccer", "basketball", "baseball", "tennis", "olympic",
            "athlete", "match", "score", "win", "defeat"
        ],
        "entertainment": [
            "movie", "film", "actor", "actress", "music", "singer", "album", "concert",
            "celebrity", "hollywood", "streaming", "netflix", "tv show", "series",
            "award", "oscar", "grammy", "entertainment", "premiere"
        ],
        "environment": [
            "climate", "environment", "pollution", "sustainability", "renewable", "carbon",
            "greenhouse", "warming", "ecology", "conservation", "wildlife", "forest",
            "ocean", "emissions", "green energy", "recycling"
        ],
    }

    def __init__(self, config: dict[str, Any]):
        """
        Initialize category agent

        Args:
            config: Complete configuration dictionary
        """
        self.config = config
        self.news_config = config.get("news", {})
        self.logger = get_logger(name="category_agent")

        # Available categories
        self.categories = self.news_config.get("categories", list(self.CATEGORY_KEYWORDS.keys()))

        self.logger.info(f"CategoryAgent initialized with {len(self.categories)} categories")

    async def categorize_article(self, article: dict[str, Any]) -> str:
        """
        Categorize a single article

        Args:
            article: Article dictionary

        Returns:
            Category name
        """
        # If article already has a valid category, keep it
        existing_category = article.get("category", "general")
        if existing_category in self.categories and existing_category != "general":
            return existing_category

        # Build text for analysis
        text_parts = [
            article.get("title", ""),
            article.get("description", ""),
            article.get("content", "")[:500],  # First 500 chars of content
        ]
        text = " ".join(filter(None, text_parts)).lower()

        if not text:
            return "general"

        # Score each category
        category_scores = {}

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if category not in self.categories:
                continue

            score = 0
            for keyword in keywords:
                # Count keyword occurrences (with word boundaries)
                pattern = r"\b" + re.escape(keyword) + r"\b"
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches

            category_scores[category] = score

        # Find best matching category
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])

            if best_category[1] > 0:  # At least one keyword match
                self.logger.debug(f"Article '{article.get('title', '')[:50]}' -> {best_category[0]} (score: {best_category[1]})")
                return best_category[0]

        # Default to general if no match
        return "general"

    async def categorize_batch(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Categorize multiple articles

        Args:
            articles: List of article dictionaries

        Returns:
            List of articles with updated categories
        """
        self.logger.info(f"Categorizing {len(articles)} articles...")

        categorized = []
        category_counts = {}

        for article in articles:
            category = await self.categorize_article(article)
            article["category"] = category

            # Track category distribution
            category_counts[category] = category_counts.get(category, 0) + 1

            categorized.append(article)

        # Log category distribution
        self.logger.info(f"Category distribution: {category_counts}")

        return categorized

    async def recategorize_by_content(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Force recategorization based on content analysis (ignore existing categories)

        Args:
            articles: List of articles

        Returns:
            List of articles with updated categories
        """
        self.logger.info("Forcing recategorization of all articles...")

        recategorized = []

        for article in articles:
            # Temporarily remove category to force re-analysis
            original_category = article.get("category")
            article["category"] = "general"

            new_category = await self.categorize_article(article)
            article["category"] = new_category

            if new_category != original_category:
                self.logger.debug(
                    f"Article '{article.get('title', '')[:50]}' recategorized: "
                    f"{original_category} -> {new_category}"
                )

            recategorized.append(article)

        return recategorized

    async def get_category_stats(self, articles: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Get statistics about article categories

        Args:
            articles: List of articles

        Returns:
            Category statistics
        """
        stats = {
            "total_articles": len(articles),
            "categories": {},
            "uncategorized": 0
        }

        for article in articles:
            category = article.get("category", "general")

            if category == "general":
                stats["uncategorized"] += 1

            if category not in stats["categories"]:
                stats["categories"][category] = {
                    "count": 0,
                    "sources": set(),
                    "languages": set()
                }

            stats["categories"][category]["count"] += 1
            stats["categories"][category]["sources"].add(article.get("source_name", "Unknown"))
            stats["categories"][category]["languages"].add(article.get("language", "en"))

        # Convert sets to lists for JSON serialization
        for category_info in stats["categories"].values():
            category_info["sources"] = list(category_info["sources"])
            category_info["languages"] = list(category_info["languages"])

        return stats

    def add_custom_keywords(self, category: str, keywords: list[str]) -> None:
        """
        Add custom keywords for a category

        Args:
            category: Category name
            keywords: List of keywords to add
        """
        if category not in self.CATEGORY_KEYWORDS:
            self.CATEGORY_KEYWORDS[category] = []

        self.CATEGORY_KEYWORDS[category].extend(keywords)
        self.logger.info(f"Added {len(keywords)} custom keywords to category '{category}'")
