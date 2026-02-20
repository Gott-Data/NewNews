#!/usr/bin/env python
"""
NewsStorage - File-based storage manager for news articles

Handles saving, loading, and querying news articles in JSON format
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from src.core.logging import get_logger


class NewsStorage:
    """Storage manager for news articles"""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize news storage

        Args:
            config: Complete configuration dictionary
        """
        self.config = config
        self.news_config = config.get("news", {})
        self.logger = get_logger(name="news_storage")

        # Storage paths
        storage_config = self.news_config.get("storage", {})
        self.base_dir = Path(storage_config.get("base_dir", "./data/news"))
        self.raw_dir = Path(storage_config.get("raw_articles_dir", "./data/news/raw"))
        self.processed_dir = Path(storage_config.get("processed_articles_dir", "./data/news/processed"))
        self.images_dir = Path(storage_config.get("images_dir", "./data/news/generated_images"))

        # Storage settings
        self.max_articles_per_source = storage_config.get("max_articles_per_source", 1000)
        self.cleanup_after_days = storage_config.get("cleanup_after_days", 30)

        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

        # Index file for quick lookups
        self.index_file = self.processed_dir / "articles_index.json"

        self.logger.info(f"NewsStorage initialized at {self.base_dir}")

    async def save_articles(self, articles: list[dict[str, Any]], processed: bool = False) -> None:
        """
        Save articles to storage

        Args:
            articles: List of article dictionaries
            processed: Whether these are processed articles (True) or raw (False)
        """
        if not articles:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_dir = self.processed_dir if processed else self.raw_dir
        filename = target_dir / f"articles_{timestamp}.json"

        try:
            # Save articles to file
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved {len(articles)} {'processed' if processed else 'raw'} articles to {filename}")

            # Update index if processed
            if processed:
                await self._update_index(articles)

        except Exception as e:
            self.logger.error(f"Error saving articles: {e}")

    async def load_articles(
        self,
        processed: bool = True,
        limit: Optional[int] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        after_date: Optional[datetime] = None
    ) -> list[dict[str, Any]]:
        """
        Load articles from storage with filtering

        Args:
            processed: Load processed articles (True) or raw (False)
            limit: Maximum number of articles to return
            category: Filter by category
            source: Filter by source
            after_date: Only return articles published after this date

        Returns:
            List of articles
        """
        target_dir = self.processed_dir if processed else self.raw_dir

        all_articles = []

        # Load all article files
        for article_file in sorted(target_dir.glob("articles_*.json"), reverse=True):
            try:
                with open(article_file, "r", encoding="utf-8") as f:
                    articles = json.load(f)

                # Apply filters
                filtered_articles = articles

                if category:
                    filtered_articles = [a for a in filtered_articles if a.get("category") == category]

                if source:
                    filtered_articles = [a for a in filtered_articles if a.get("source") == source]

                if after_date:
                    filtered_articles = [
                        a for a in filtered_articles
                        if self._parse_date(a.get("published_at")) >= after_date
                    ]

                all_articles.extend(filtered_articles)

                # Check if we've hit the limit
                if limit and len(all_articles) >= limit:
                    all_articles = all_articles[:limit]
                    break

            except Exception as e:
                self.logger.error(f"Error loading {article_file}: {e}")

        self.logger.info(f"Loaded {len(all_articles)} articles from storage")
        return all_articles

    async def get_article_by_id(self, article_id: str) -> Optional[dict[str, Any]]:
        """
        Get a single article by ID

        Args:
            article_id: Article ID

        Returns:
            Article dictionary or None if not found
        """
        # Check index first
        index = await self._load_index()

        if article_id in index:
            file_path = index[article_id]["file"]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    articles = json.load(f)

                for article in articles:
                    if article.get("id") == article_id:
                        return article

            except Exception as e:
                self.logger.error(f"Error loading article {article_id}: {e}")

        return None

    async def delete_old_articles(self) -> int:
        """
        Delete articles older than cleanup_after_days

        Returns:
            Number of articles deleted
        """
        cutoff_date = datetime.now() - timedelta(days=self.cleanup_after_days)
        deleted_count = 0

        for article_dir in [self.raw_dir, self.processed_dir]:
            for article_file in article_dir.glob("articles_*.json"):
                try:
                    # Parse timestamp from filename
                    timestamp_str = article_file.stem.replace("articles_", "")
                    file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                    if file_date < cutoff_date:
                        article_file.unlink()
                        deleted_count += 1
                        self.logger.info(f"Deleted old article file: {article_file.name}")

                except Exception as e:
                    self.logger.error(f"Error deleting {article_file}: {e}")

        if deleted_count > 0:
            # Rebuild index after deletion
            await self._rebuild_index()

        return deleted_count

    async def get_stats(self) -> dict[str, Any]:
        """
        Get storage statistics

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_articles": 0,
            "by_category": {},
            "by_source": {},
            "by_language": {},
            "storage_size_mb": 0,
            "oldest_article": None,
            "newest_article": None
        }

        # Load all processed articles
        articles = await self.load_articles(processed=True, limit=None)

        stats["total_articles"] = len(articles)

        # Calculate statistics
        for article in articles:
            # Category stats
            category = article.get("category", "general")
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

            # Source stats
            source = article.get("source_name", "Unknown")
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

            # Language stats
            language = article.get("language", "en")
            stats["by_language"][language] = stats["by_language"].get(language, 0) + 1

            # Date range
            published = self._parse_date(article.get("published_at"))
            if published:
                if not stats["oldest_article"] or published < self._parse_date(stats["oldest_article"]):
                    stats["oldest_article"] = article.get("published_at")

                if not stats["newest_article"] or published > self._parse_date(stats["newest_article"]):
                    stats["newest_article"] = article.get("published_at")

        # Calculate storage size
        total_size = 0
        for path in [self.raw_dir, self.processed_dir, self.images_dir]:
            for file in path.rglob("*"):
                if file.is_file():
                    total_size += file.stat().st_size

        stats["storage_size_mb"] = round(total_size / (1024 * 1024), 2)

        return stats

    async def _update_index(self, articles: list[dict[str, Any]]) -> None:
        """
        Update the articles index for faster lookups

        Args:
            articles: List of articles to index
        """
        index = await self._load_index()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.processed_dir / f"articles_{timestamp}.json"

        for article in articles:
            article_id = article.get("id")
            if article_id:
                index[article_id] = {
                    "file": str(filename),
                    "title": article.get("title"),
                    "category": article.get("category"),
                    "published_at": article.get("published_at"),
                    "indexed_at": datetime.now().isoformat()
                }

        # Save index
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error updating index: {e}")

    async def _load_index(self) -> dict[str, Any]:
        """
        Load the articles index

        Returns:
            Index dictionary
        """
        if not self.index_file.exists():
            return {}

        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading index: {e}")
            return {}

    async def _rebuild_index(self) -> None:
        """Rebuild the articles index from scratch"""
        self.logger.info("Rebuilding articles index...")

        index = {}

        for article_file in self.processed_dir.glob("articles_*.json"):
            try:
                with open(article_file, "r", encoding="utf-8") as f:
                    articles = json.load(f)

                for article in articles:
                    article_id = article.get("id")
                    if article_id:
                        index[article_id] = {
                            "file": str(article_file),
                            "title": article.get("title"),
                            "category": article.get("category"),
                            "published_at": article.get("published_at"),
                            "indexed_at": datetime.now().isoformat()
                        }

            except Exception as e:
                self.logger.error(f"Error reading {article_file} for index: {e}")

        # Save rebuilt index
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Index rebuilt with {len(index)} articles")

        except Exception as e:
            self.logger.error(f"Error saving rebuilt index: {e}")

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse date string to datetime

        Args:
            date_str: ISO format date string

        Returns:
            datetime object or None
        """
        if not date_str:
            return None

        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None
