#!/usr/bin/env python
"""
NewsScraperAgent - Multi-source news collection agent

Handles news aggregation from:
- NewsAPI.org
- The Guardian API
- RSS feeds from reputable sources
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import hashlib
import json

from src.core.logging import get_logger


class NewsScraperAgent:
    """Agent for scraping news from multiple sources"""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize news scraper agent

        Args:
            config: Complete configuration dictionary
        """
        self.config = config
        self.news_config = config.get("news", {})
        self.logger = get_logger(name="news_scraper_agent")

        # Storage paths
        self.base_dir = Path(self.news_config.get("storage", {}).get("base_dir", "./data/news"))
        self.raw_dir = self.base_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

        # Source configurations
        self.sources_config = self.news_config.get("sources", {})
        self.update_frequency = self.news_config.get("update_frequency", "daily")

        # Categories and languages
        self.categories = self.news_config.get("categories", ["general"])
        self.languages = self.news_config.get("languages", ["en"])

        self.logger.info(f"NewsScraperAgent initialized with {len(self.categories)} categories")

    async def fetch_all_sources(self) -> list[dict[str, Any]]:
        """
        Fetch news from all configured sources

        Returns:
            List of raw article dictionaries
        """
        self.logger.info("Starting news aggregation from all sources...")

        all_articles = []

        # Fetch from different sources concurrently
        tasks = []

        if self.sources_config.get("newsapi", {}).get("enabled", False):
            tasks.append(self._fetch_newsapi())

        if self.sources_config.get("guardian", {}).get("enabled", False):
            tasks.append(self._fetch_guardian())

        if self.sources_config.get("rss_feeds"):
            tasks.append(self._fetch_rss_feeds())

        # Execute all fetch tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Error fetching from source: {result}")
            elif isinstance(result, list):
                all_articles.extend(result)

        self.logger.info(f"Fetched {len(all_articles)} articles from all sources")

        # Save raw articles
        await self._save_raw_articles(all_articles)

        return all_articles

    async def _fetch_newsapi(self) -> list[dict[str, Any]]:
        """
        Fetch news from NewsAPI.org

        Returns:
            List of articles from NewsAPI
        """
        try:
            import os
            from newsapi import NewsApiClient

            api_key = os.getenv("NEWSAPI_KEY")
            if not api_key:
                self.logger.warning("NEWSAPI_KEY not set, skipping NewsAPI")
                return []

            newsapi = NewsApiClient(api_key=api_key)
            articles = []

            newsapi_config = self.sources_config.get("newsapi", {})
            countries = newsapi_config.get("countries", ["us"])
            page_size = newsapi_config.get("page_size", 100)
            max_pages = newsapi_config.get("max_pages", 5)

            self.logger.info(f"Fetching from NewsAPI: {len(countries)} countries")

            for category in self.categories:
                for country in countries:
                    try:
                        # Fetch top headlines
                        for page in range(1, max_pages + 1):
                            response = newsapi.get_top_headlines(
                                category=category,
                                country=country,
                                page_size=page_size,
                                page=page
                            )

                            if response["status"] == "ok":
                                for article in response.get("articles", []):
                                    articles.append({
                                        "id": self._generate_article_id(article),
                                        "source": "newsapi",
                                        "source_name": article.get("source", {}).get("name", "Unknown"),
                                        "title": article.get("title"),
                                        "description": article.get("description"),
                                        "content": article.get("content"),
                                        "url": article.get("url"),
                                        "image_url": article.get("urlToImage"),
                                        "published_at": article.get("publishedAt"),
                                        "author": article.get("author"),
                                        "category": category,
                                        "country": country,
                                        "language": "en",  # NewsAPI primarily English
                                        "fetched_at": datetime.now().isoformat()
                                    })

                            # Break if we got fewer articles than page size (last page)
                            if len(response.get("articles", [])) < page_size:
                                break

                    except Exception as e:
                        self.logger.error(f"Error fetching NewsAPI category {category}, country {country}: {e}")

            self.logger.info(f"Fetched {len(articles)} articles from NewsAPI")
            return articles

        except ImportError:
            self.logger.error("newsapi-python not installed. Run: pip install newsapi-python")
            return []
        except Exception as e:
            self.logger.error(f"Error in NewsAPI fetch: {e}")
            return []

    async def _fetch_guardian(self) -> list[dict[str, Any]]:
        """
        Fetch news from The Guardian API

        Returns:
            List of articles from Guardian
        """
        try:
            import os
            import aiohttp

            api_key = os.getenv("GUARDIAN_API_KEY")
            if not api_key:
                self.logger.warning("GUARDIAN_API_KEY not set, skipping Guardian API")
                return []

            articles = []
            guardian_config = self.sources_config.get("guardian", {})
            page_size = guardian_config.get("page_size", 50)
            max_pages = guardian_config.get("max_pages", 10)

            self.logger.info("Fetching from The Guardian API")

            async with aiohttp.ClientSession() as session:
                for category in self.categories:
                    for page in range(1, max_pages + 1):
                        url = "https://content.guardianapis.com/search"
                        params = {
                            "api-key": api_key,
                            "section": category,
                            "page-size": page_size,
                            "page": page,
                            "show-fields": "headline,body,thumbnail,byline",
                            "order-by": "newest"
                        }

                        try:
                            async with session.get(url, params=params) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    results = data.get("response", {}).get("results", [])

                                    for article in results:
                                        fields = article.get("fields", {})
                                        articles.append({
                                            "id": self._generate_article_id(article),
                                            "source": "guardian",
                                            "source_name": "The Guardian",
                                            "title": fields.get("headline", article.get("webTitle")),
                                            "description": fields.get("body", "")[:500],  # First 500 chars
                                            "content": fields.get("body"),
                                            "url": article.get("webUrl"),
                                            "image_url": fields.get("thumbnail"),
                                            "published_at": article.get("webPublicationDate"),
                                            "author": fields.get("byline"),
                                            "category": category,
                                            "country": "gb",
                                            "language": "en",
                                            "fetched_at": datetime.now().isoformat()
                                        })

                                    # Break if we got fewer results than page size
                                    if len(results) < page_size:
                                        break

                        except Exception as e:
                            self.logger.error(f"Error fetching Guardian page {page}: {e}")

            self.logger.info(f"Fetched {len(articles)} articles from The Guardian")
            return articles

        except ImportError:
            self.logger.error("aiohttp not installed. Run: pip install aiohttp")
            return []
        except Exception as e:
            self.logger.error(f"Error in Guardian API fetch: {e}")
            return []

    async def _fetch_rss_feeds(self) -> list[dict[str, Any]]:
        """
        Fetch news from RSS feeds

        Returns:
            List of articles from RSS feeds
        """
        try:
            import feedparser

            feeds = self.sources_config.get("rss_feeds", [])
            if not feeds:
                self.logger.info("No RSS feeds configured")
                return []

            articles = []
            self.logger.info(f"Fetching from {len(feeds)} RSS feeds")

            for feed_config in feeds:
                try:
                    url = feed_config.get("url")
                    name = feed_config.get("name", "Unknown")
                    language = feed_config.get("language", "en")
                    credibility = feed_config.get("credibility_score", 0.85)

                    feed = feedparser.parse(url)

                    for entry in feed.entries:
                        # Try to extract category from tags
                        category = "general"
                        if hasattr(entry, "tags") and entry.tags:
                            category = entry.tags[0].get("term", "general")

                        articles.append({
                            "id": self._generate_article_id(entry),
                            "source": "rss",
                            "source_name": name,
                            "title": entry.get("title"),
                            "description": entry.get("summary", ""),
                            "content": entry.get("content", [{}])[0].get("value", entry.get("summary", "")),
                            "url": entry.get("link"),
                            "image_url": entry.get("media_thumbnail", [{}])[0].get("url") if hasattr(entry, "media_thumbnail") else None,
                            "published_at": entry.get("published", entry.get("updated")),
                            "author": entry.get("author"),
                            "category": category,
                            "language": language,
                            "credibility_score": credibility,
                            "fetched_at": datetime.now().isoformat()
                        })

                    self.logger.info(f"Fetched {len(feed.entries)} articles from {name}")

                except Exception as e:
                    self.logger.error(f"Error fetching RSS feed {feed_config.get('name')}: {e}")

            self.logger.info(f"Fetched {len(articles)} articles from RSS feeds")
            return articles

        except ImportError:
            self.logger.error("feedparser not installed. Run: pip install feedparser")
            return []
        except Exception as e:
            self.logger.error(f"Error in RSS feed fetch: {e}")
            return []

    def _generate_article_id(self, article: dict) -> str:
        """
        Generate unique ID for an article based on URL or title

        Args:
            article: Article dictionary

        Returns:
            Unique article ID (SHA256 hash)
        """
        # Try URL first, fallback to title + published date
        identifier = article.get("url") or article.get("link")
        if not identifier:
            title = article.get("title", "")
            published = article.get("published_at") or article.get("published") or article.get("webPublicationDate", "")
            identifier = f"{title}_{published}"

        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    async def _save_raw_articles(self, articles: list[dict[str, Any]]) -> None:
        """
        Save raw articles to storage

        Args:
            articles: List of article dictionaries
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.raw_dir / f"articles_{timestamp}.json"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved {len(articles)} raw articles to {filename}")

        except Exception as e:
            self.logger.error(f"Error saving raw articles: {e}")

    async def fetch_by_category(self, category: str) -> list[dict[str, Any]]:
        """
        Fetch news for a specific category

        Args:
            category: News category (e.g., 'technology', 'science')

        Returns:
            List of articles in that category
        """
        # Temporarily override categories
        original_categories = self.categories
        self.categories = [category]

        articles = await self.fetch_all_sources()

        # Restore original categories
        self.categories = original_categories

        return articles

    async def fetch_recent(self, hours: int = 24) -> list[dict[str, Any]]:
        """
        Fetch recent news from the last N hours

        Args:
            hours: Number of hours to look back

        Returns:
            List of recent articles
        """
        all_articles = await self.fetch_all_sources()

        # Filter by published date
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_articles = []

        for article in all_articles:
            published_str = article.get("published_at")
            if published_str:
                try:
                    # Parse ISO format datetime
                    published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                    if published.replace(tzinfo=None) >= cutoff_time:
                        recent_articles.append(article)
                except Exception:
                    # If parsing fails, include the article anyway
                    recent_articles.append(article)

        self.logger.info(f"Found {len(recent_articles)} articles from last {hours} hours")
        return recent_articles
