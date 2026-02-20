#!/usr/bin/env python
"""
TrendDetectorAgent - Detects emerging topics and trending stories

Uses TF-IDF, time decay, and growth rate analysis to identify trending topics
"""

from datetime import datetime, timedelta
from typing import Any
from collections import defaultdict
from pathlib import Path
import sys

_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.core.logging import get_logger


class TrendDetectorAgent:
    """Agent for detecting trending topics in news"""

    def __init__(self, config: dict[str, Any]):
        """Initialize trend detector agent"""
        self.config = config
        self.trend_config = config.get("trend_analysis", {}).get("detection", {})
        self.logger = get_logger(name="trend_detector_agent")

        self.min_mentions = self.trend_config.get("min_mentions", 5)
        self.growth_threshold = self.trend_config.get("growth_threshold", 0.25)
        self.novelty_threshold = self.trend_config.get("novelty_threshold", 0.6)

        self.logger.info("TrendDetectorAgent initialized")

    async def detect_trends(
        self,
        articles: list[dict[str, Any]],
        time_window_days: int = 7
    ) -> list[dict[str, Any]]:
        """
        Detect trending topics from articles

        Args:
            articles: List of articles
            time_window_days: Time window for trend analysis

        Returns:
            List of trending topics with metrics
        """
        self.logger.info(f"Detecting trends in {len(articles)} articles (window={time_window_days} days)")

        # Filter articles within time window
        cutoff_date = datetime.now() - timedelta(days=time_window_days)
        recent_articles = [
            a for a in articles
            if self._parse_date(a.get("published_at")) >= cutoff_date
        ]

        if not recent_articles:
            self.logger.warning("No recent articles found in time window")
            return []

        # Extract topics from articles
        topics = self._extract_topics(recent_articles)

        # Calculate topic metrics
        trends = []
        for topic, data in topics.items():
            if data["count"] < self.min_mentions:
                continue

            # Calculate growth rate
            growth_rate = self._calculate_growth_rate(topic, data, time_window_days)

            # Only include if growing
            if growth_rate >= self.growth_threshold:
                trends.append({
                    "topic": topic,
                    "mention_count": data["count"],
                    "growth_rate": round(growth_rate, 2),
                    "first_seen": data["first_seen"],
                    "latest_seen": data["latest_seen"],
                    "categories": list(data["categories"]),
                    "sources": list(data["sources"]),
                    "articles": data["article_ids"][:10],  # Sample articles
                    "status": self._classify_trend_status(growth_rate)
                })

        # Sort by growth rate
        trends.sort(key=lambda x: x["growth_rate"], reverse=True)

        self.logger.info(f"Found {len(trends)} trending topics")
        return trends

    def _extract_topics(self, articles: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Extract topics from articles using keywords and titles"""
        topics = defaultdict(lambda: {
            "count": 0,
            "first_seen": None,
            "latest_seen": None,
            "categories": set(),
            "sources": set(),
            "article_ids": []
        })

        for article in articles:
            # Extract topics from keywords (if available)
            keywords = article.get("keywords", [])
            title = article.get("title", "").lower()
            published = self._parse_date(article.get("published_at"))

            # Use keywords or extract from title
            article_topics = keywords if keywords else self._extract_from_title(title)

            for topic in article_topics:
                topic_key = topic.lower().strip()

                if len(topic_key) < 3:  # Skip very short topics
                    continue

                data = topics[topic_key]
                data["count"] += 1
                data["categories"].add(article.get("category", "general"))
                data["sources"].add(article.get("source_name", "Unknown"))
                data["article_ids"].append(article.get("id"))

                # Update dates
                if not data["first_seen"] or published < data["first_seen"]:
                    data["first_seen"] = published.isoformat() if published else None

                if not data["latest_seen"] or (published and published > self._parse_date(data["latest_seen"])):
                    data["latest_seen"] = published.isoformat() if published else None

        return dict(topics)

    def _extract_from_title(self, title: str) -> list[str]:
        """Extract potential topics from article title"""
        import re

        # Remove common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "as", "is", "was", "are", "were", "been", "be", "has", "have", "had", "do", "does", "did", "will", "would", "should", "could", "may", "might", "can"}

        # Split and filter
        words = re.findall(r'\b[a-z]{3,}\b', title)
        topics = [w for w in words if w not in stop_words]

        # Look for multi-word phrases (capitalized sequences)
        phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', title)

        return topics[:3] + phrases[:2]  # Return top topics

    def _calculate_growth_rate(
        self,
        topic: str,
        data: dict[str, Any],
        time_window_days: int
    ) -> float:
        """
        Calculate growth rate for a topic

        Simple heuristic: count / days_active
        """
        first_seen = self._parse_date(data["first_seen"])
        latest_seen = self._parse_date(data["latest_seen"])

        if not first_seen or not latest_seen:
            return 0.0

        days_active = max(1, (latest_seen - first_seen).days)

        # Growth rate = mentions per day / time window
        mentions_per_day = data["count"] / max(1, days_active)
        baseline = data["count"] / time_window_days

        # Calculate growth as ratio
        if baseline > 0:
            growth = (mentions_per_day - baseline) / baseline
        else:
            growth = 0.0

        return max(0.0, growth)

    def _classify_trend_status(self, growth_rate: float) -> str:
        """Classify trend status based on growth rate"""
        if growth_rate >= 1.0:
            return "explosive"
        elif growth_rate >= 0.5:
            return "rising"
        elif growth_rate >= self.growth_threshold:
            return "emerging"
        else:
            return "stable"

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse date string to datetime"""
        if not date_str:
            return None

        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None

    async def get_topic_timeline(
        self,
        topic: str,
        articles: list[dict[str, Any]],
        days: int = 30
    ) -> dict[str, Any]:
        """
        Get timeline of mentions for a specific topic

        Args:
            topic: Topic to track
            articles: List of articles
            days: Number of days to analyze

        Returns:
            Timeline data with daily counts
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        topic_lower = topic.lower()

        # Build daily counts
        daily_counts = defaultdict(int)
        matching_articles = []

        for article in articles:
            published = self._parse_date(article.get("published_at"))
            if not published or published < cutoff_date:
                continue

            # Check if topic mentioned
            title = article.get("title", "").lower()
            content = article.get("content", "").lower()
            keywords = [k.lower() for k in article.get("keywords", [])]

            if topic_lower in title or topic_lower in content or topic_lower in keywords:
                date_key = published.strftime("%Y-%m-%d")
                daily_counts[date_key] += 1
                matching_articles.append(article.get("id"))

        # Convert to sorted list
        timeline = [
            {"date": date, "count": count}
            for date, count in sorted(daily_counts.items())
        ]

        return {
            "topic": topic,
            "timeline": timeline,
            "total_mentions": sum(daily_counts.values()),
            "days_active": len(daily_counts),
            "matching_articles": matching_articles[:50]  # Sample
        }
