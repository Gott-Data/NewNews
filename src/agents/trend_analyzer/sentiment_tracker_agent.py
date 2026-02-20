#!/usr/bin/env python
"""
SentimentTrackerAgent - Tracks sentiment evolution for topics over time

Analyzes emotional tone and sentiment trends in news coverage
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


class SentimentTrackerAgent:
    """Agent for tracking sentiment in news articles"""

    def __init__(self, config: dict[str, Any]):
        """Initialize sentiment tracker agent"""
        self.config = config
        self.sentiment_config = config.get("trend_analysis", {}).get("sentiment", {})
        self.logger = get_logger(name="sentiment_tracker_agent")

        self.enabled = self.sentiment_config.get("enabled", True)
        self.models = self.sentiment_config.get("models", ["vader"])

        self.logger.info(f"SentimentTrackerAgent initialized (models={self.models})")

    async def analyze_sentiment(self, text: str) -> dict[str, Any]:
        """
        Analyze sentiment of text

        Args:
            text: Text to analyze

        Returns:
            Sentiment scores (positive, negative, neutral)
        """
        if not self.enabled or not text:
            return {"positive": 0.33, "neutral": 0.34, "negative": 0.33, "compound": 0.0}

        # Try TextBlob first (simple and fast)
        try:
            from textblob import TextBlob

            blob = TextBlob(text[:1000])  # Limit to first 1000 chars
            polarity = blob.sentiment.polarity  # -1 to 1

            # Convert polarity to positive/negative/neutral
            if polarity > 0.1:
                return {
                    "positive": min(1.0, 0.5 + polarity/2),
                    "neutral": 0.3,
                    "negative": max(0.0, 0.2 - polarity/2),
                    "compound": polarity,
                    "model": "textblob"
                }
            elif polarity < -0.1:
                return {
                    "positive": max(0.0, 0.2 + polarity/2),
                    "neutral": 0.3,
                    "negative": min(1.0, 0.5 - polarity/2),
                    "compound": polarity,
                    "model": "textblob"
                }
            else:
                return {
                    "positive": 0.25,
                    "neutral": 0.5,
                    "negative": 0.25,
                    "compound": polarity,
                    "model": "textblob"
                }

        except ImportError:
            self.logger.debug("TextBlob not available, using rule-based sentiment")

        # Fallback: rule-based sentiment
        return self._rule_based_sentiment(text)

    def _rule_based_sentiment(self, text: str) -> dict[str, Any]:
        """Simple rule-based sentiment analysis"""
        text_lower = text.lower()

        positive_words = ["good", "great", "excellent", "positive", "success", "win", "improve", "growth", "hope", "better"]
        negative_words = ["bad", "poor", "negative", "fail", "loss", "worse", "decline", "crisis", "concern", "threat"]

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        total = positive_count + negative_count

        if total == 0:
            return {"positive": 0.33, "neutral": 0.34, "negative": 0.33, "compound": 0.0, "model": "rule-based"}

        pos_ratio = positive_count / total
        neg_ratio = negative_count / total

        return {
            "positive": round(pos_ratio, 2),
            "neutral": round(1 - pos_ratio - neg_ratio, 2),
            "negative": round(neg_ratio, 2),
            "compound": round(pos_ratio - neg_ratio, 2),
            "model": "rule-based"
        }

    async def track_topic_sentiment(
        self,
        topic: str,
        articles: list[dict[str, Any]],
        days: int = 30
    ) -> dict[str, Any]:
        """
        Track sentiment evolution for a topic over time

        Args:
            topic: Topic to track
            articles: List of articles
            days: Number of days to analyze

        Returns:
            Sentiment timeline and statistics
        """
        self.logger.info(f"Tracking sentiment for topic: {topic} (days={days})")

        cutoff_date = datetime.now() - timedelta(days=days)
        topic_lower = topic.lower()

        # Collect articles mentioning topic
        daily_sentiments = defaultdict(lambda: {"positive": [], "negative": [], "neutral": []})
        total_articles = 0

        for article in articles:
            published = self._parse_date(article.get("published_at"))
            if not published or published < cutoff_date:
                continue

            # Check if topic mentioned
            title = article.get("title", "").lower()
            content = article.get("content", "").lower()

            if topic_lower not in title and topic_lower not in content:
                continue

            # Analyze sentiment
            text = f"{article.get('title', '')} {article.get('description', '')}"
            sentiment = await self.analyze_sentiment(text)

            date_key = published.strftime("%Y-%m-%d")
            daily_sentiments[date_key]["positive"].append(sentiment["positive"])
            daily_sentiments[date_key]["negative"].append(sentiment["negative"])
            daily_sentiments[date_key]["neutral"].append(sentiment["neutral"])

            total_articles += 1

        # Calculate daily averages
        timeline = []
        for date in sorted(daily_sentiments.keys()):
            sentiments = daily_sentiments[date]
            timeline.append({
                "date": date,
                "positive": round(sum(sentiments["positive"]) / len(sentiments["positive"]), 2) if sentiments["positive"] else 0,
                "negative": round(sum(sentiments["negative"]) / len(sentiments["negative"]), 2) if sentiments["negative"] else 0,
                "neutral": round(sum(sentiments["neutral"]) / len(sentiments["neutral"]), 2) if sentiments["neutral"] else 0,
                "article_count": len(sentiments["positive"])
            })

        # Calculate overall stats
        all_positive = [s for day in daily_sentiments.values() for s in day["positive"]]
        all_negative = [s for day in daily_sentiments.values() for s in day["negative"]]
        all_neutral = [s for day in daily_sentiments.values() for s in day["neutral"]]

        overall = {
            "positive": round(sum(all_positive) / len(all_positive), 2) if all_positive else 0,
            "negative": round(sum(all_negative) / len(all_negative), 2) if all_negative else 0,
            "neutral": round(sum(all_neutral) / len(all_neutral), 2) if all_neutral else 0
        }

        return {
            "topic": topic,
            "timeline": timeline,
            "overall_sentiment": overall,
            "total_articles": total_articles,
            "days_analyzed": len(daily_sentiments),
            "sentiment_trend": self._calculate_trend(timeline)
        }

    def _calculate_trend(self, timeline: list[dict[str, Any]]) -> str:
        """Calculate sentiment trend direction"""
        if len(timeline) < 2:
            return "stable"

        # Compare first half vs second half
        mid = len(timeline) // 2
        first_half = timeline[:mid]
        second_half = timeline[mid:]

        avg_first = sum(day["positive"] - day["negative"] for day in first_half) / len(first_half)
        avg_second = sum(day["positive"] - day["negative"] for day in second_half) / len(second_half)

        diff = avg_second - avg_first

        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"

    async def batch_analyze(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Analyze sentiment for multiple articles

        Args:
            articles: List of articles

        Returns:
            Articles with sentiment scores added
        """
        results = []

        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            sentiment = await self.analyze_sentiment(text)

            article_with_sentiment = article.copy()
            article_with_sentiment["sentiment"] = sentiment

            results.append(article_with_sentiment)

        return results

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse date string to datetime"""
        if not date_str:
            return None

        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None
