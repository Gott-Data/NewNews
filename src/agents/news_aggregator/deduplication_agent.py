#!/usr/bin/env python
"""
DeduplicationAgent - Identifies and removes duplicate news articles

Uses fuzzy matching and content similarity to detect duplicates across sources
"""

from typing import Any
from difflib import SequenceMatcher

from src.core.logging import get_logger


class DeduplicationAgent:
    """Agent for detecting and removing duplicate articles"""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize deduplication agent

        Args:
            config: Complete configuration dictionary
        """
        self.config = config
        self.news_config = config.get("news", {})
        self.logger = get_logger(name="deduplication_agent")

        # Deduplication config
        self.dedup_config = self.news_config.get("deduplication", {})
        self.enabled = self.dedup_config.get("enabled", True)
        self.similarity_threshold = self.dedup_config.get("similarity_threshold", 0.85)
        self.method = self.dedup_config.get("method", "fuzzy")

        self.logger.info(f"DeduplicationAgent initialized (threshold={self.similarity_threshold})")

    async def deduplicate(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Remove duplicate articles from list

        Args:
            articles: List of article dictionaries

        Returns:
            List of unique articles
        """
        if not self.enabled or not articles:
            return articles

        self.logger.info(f"Deduplicating {len(articles)} articles...")

        if self.method == "fuzzy":
            unique_articles = await self._deduplicate_fuzzy(articles)
        elif self.method == "embedding":
            unique_articles = await self._deduplicate_embedding(articles)
        else:  # both
            # First pass with fuzzy, then embedding
            fuzzy_unique = await self._deduplicate_fuzzy(articles)
            unique_articles = await self._deduplicate_embedding(fuzzy_unique)

        removed_count = len(articles) - len(unique_articles)
        self.logger.info(f"Removed {removed_count} duplicates, {len(unique_articles)} unique articles remain")

        return unique_articles

    async def _deduplicate_fuzzy(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Deduplicate using fuzzy string matching

        Args:
            articles: List of articles

        Returns:
            List of unique articles
        """
        unique_articles = []
        seen_titles = []

        for article in articles:
            title = article.get("title", "").lower().strip()

            if not title:
                unique_articles.append(article)
                continue

            # Check similarity against all seen titles
            is_duplicate = False
            for seen_title in seen_titles:
                similarity = self._calculate_similarity(title, seen_title)

                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    self.logger.debug(f"Duplicate detected: '{title[:50]}...' ~= '{seen_title[:50]}...' ({similarity:.2f})")
                    break

            if not is_duplicate:
                unique_articles.append(article)
                seen_titles.append(title)

        return unique_articles

    async def _deduplicate_embedding(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Deduplicate using content embeddings (more accurate but slower)

        Args:
            articles: List of articles

        Returns:
            List of unique articles
        """
        try:
            # This would use sentence transformers or OpenAI embeddings
            # For now, fallback to fuzzy matching
            self.logger.warning("Embedding-based deduplication not yet implemented, using fuzzy matching")
            return await self._deduplicate_fuzzy(articles)

        except Exception as e:
            self.logger.error(f"Embedding deduplication failed: {e}, falling back to fuzzy")
            return await self._deduplicate_fuzzy(articles)

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, str1, str2).ratio()

    async def find_duplicates(self, articles: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """
        Find all duplicate groups (without removing them)

        Args:
            articles: List of articles

        Returns:
            Dictionary mapping original article to its duplicates
        """
        duplicates = {}

        for i, article1 in enumerate(articles):
            title1 = article1.get("title", "").lower().strip()

            if not title1 or article1.get("id") in duplicates:
                continue

            duplicates[article1.get("id")] = []

            for j, article2 in enumerate(articles):
                if i >= j:  # Skip self and already compared pairs
                    continue

                title2 = article2.get("title", "").lower().strip()

                if not title2:
                    continue

                similarity = self._calculate_similarity(title1, title2)

                if similarity >= self.similarity_threshold:
                    duplicates[article1.get("id")].append({
                        "article": article2,
                        "similarity": similarity
                    })

        # Filter out articles with no duplicates
        duplicates = {k: v for k, v in duplicates.items() if v}

        self.logger.info(f"Found {len(duplicates)} articles with duplicates")
        return duplicates

    async def merge_duplicates(
        self,
        articles: list[dict[str, Any]],
        merge_strategy: str = "prefer_credible"
    ) -> list[dict[str, Any]]:
        """
        Merge duplicate articles using specified strategy

        Args:
            articles: List of articles
            merge_strategy: Strategy for merging ('prefer_credible', 'prefer_complete', 'combine')

        Returns:
            List of merged articles
        """
        duplicate_groups = await self.find_duplicates(articles)

        # Build a set of IDs to skip (duplicates)
        skip_ids = set()
        for duplicates in duplicate_groups.values():
            for dup in duplicates:
                skip_ids.add(dup["article"].get("id"))

        merged_articles = []

        for article in articles:
            article_id = article.get("id")

            # Skip if this is a duplicate
            if article_id in skip_ids:
                continue

            # Check if this article has duplicates
            if article_id in duplicate_groups:
                # Merge this article with its duplicates
                duplicates = duplicate_groups[article_id]
                merged = await self._merge_article_group(article, duplicates, merge_strategy)
                merged_articles.append(merged)
            else:
                # No duplicates, add as-is
                merged_articles.append(article)

        self.logger.info(f"Merged {len(articles)} articles into {len(merged_articles)}")
        return merged_articles

    async def _merge_article_group(
        self,
        primary: dict[str, Any],
        duplicates: list[dict[str, Any]],
        strategy: str
    ) -> dict[str, Any]:
        """
        Merge a group of duplicate articles

        Args:
            primary: Primary article
            duplicates: List of duplicate article dicts with similarity scores
            strategy: Merging strategy

        Returns:
            Merged article
        """
        if strategy == "prefer_credible":
            # Choose article from most credible source
            all_articles = [primary] + [d["article"] for d in duplicates]
            best_article = max(all_articles, key=lambda x: x.get("credibility_score", 0.5))
            return best_article

        elif strategy == "prefer_complete":
            # Choose article with most content
            all_articles = [primary] + [d["article"] for d in duplicates]
            best_article = max(all_articles, key=lambda x: len(x.get("content", "")))
            return best_article

        elif strategy == "combine":
            # Combine information from all articles
            merged = primary.copy()

            # Collect all sources
            all_sources = [primary.get("source_name")]
            for dup in duplicates:
                source = dup["article"].get("source_name")
                if source and source not in all_sources:
                    all_sources.append(source)

            merged["sources"] = all_sources
            merged["duplicate_count"] = len(duplicates)

            # Use longest content
            all_articles = [primary] + [d["article"] for d in duplicates]
            longest_content = max(all_articles, key=lambda x: len(x.get("content", "")))
            merged["content"] = longest_content.get("content")

            return merged

        else:
            # Default: return primary
            return primary
