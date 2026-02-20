#!/usr/bin/env python
"""
NoveltyEvaluatorAgent - Detects genuinely new information vs recycled content

Evaluates how novel an article's information is compared to previous coverage
"""

from datetime import datetime, timedelta
from typing import Any
from difflib import SequenceMatcher
from pathlib import Path
import sys

_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.core.logging import get_logger


class NoveltyEvaluatorAgent:
    """Agent for evaluating content novelty"""

    def __init__(self, config: dict[str, Any]):
        """Initialize novelty evaluator agent"""
        self.config = config
        self.logger = get_logger(name="novelty_evaluator_agent")
        self.novelty_threshold = config.get("trend_analysis", {}).get("detection", {}).get("novelty_threshold", 0.6)
        self.logger.info("NoveltyEvaluatorAgent initialized")

    async def evaluate_novelty(
        self,
        article: dict[str, Any],
        historical_articles: list[dict[str, Any]],
        lookback_days: int = 7
    ) -> dict[str, Any]:
        """
        Evaluate how novel an article is

        Args:
            article: Article to evaluate
            historical_articles: Previous articles to compare against
            lookback_days: How many days back to compare

        Returns:
            Novelty score and analysis
        """
        article_content = f"{article.get('title', '')} {article.get('description', '')}"

        if not article_content.strip():
            return {"novelty_score": 0.0, "reason": "Empty content"}

        # Filter historical articles by date and topic
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        article_published = self._parse_date(article.get("published_at"))

        if not article_published:
            return {"novelty_score": 0.5, "reason": "No publish date"}

        relevant_articles = []
        for hist_article in historical_articles:
            hist_published = self._parse_date(hist_article.get("published_at"))

            if not hist_published or hist_published >= article_published:
                continue

            if hist_published < cutoff_date:
                continue

            # Same category increases relevance
            if article.get("category") == hist_article.get("category"):
                relevant_articles.append(hist_article)

        if not relevant_articles:
            return {
                "novelty_score": 1.0,
                "reason": "No similar recent coverage found",
                "similar_articles": []
            }

        # Calculate similarity to previous articles
        max_similarity = 0.0
        most_similar = None

        for hist_article in relevant_articles:
            hist_content = f"{hist_article.get('title', '')} {hist_article.get('description', '')}"
            similarity = self._calculate_similarity(article_content, hist_content)

            if similarity > max_similarity:
                max_similarity = similarity
                most_similar = hist_article

        # Novelty = 1 - similarity
        novelty_score = max(0.0, 1.0 - max_similarity)

        result = {
            "novelty_score": round(novelty_score, 2),
            "max_similarity": round(max_similarity, 2),
            "similar_articles": [most_similar.get("id")] if most_similar else [],
            "classification": self._classify_novelty(novelty_score),
            "reason": self._generate_reason(novelty_score, max_similarity)
        }

        return result

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _classify_novelty(self, score: float) -> str:
        """Classify novelty level"""
        if score >= 0.8:
            return "highly_novel"
        elif score >= 0.6:
            return "moderately_novel"
        elif score >= 0.4:
            return "somewhat_novel"
        else:
            return "recycled"

    def _generate_reason(self, novelty: float, similarity: float) -> str:
        """Generate human-readable reason"""
        if novelty >= 0.8:
            return "Genuinely new information not covered in recent articles"
        elif novelty >= 0.6:
            return "Adds new perspective or details to ongoing story"
        elif novelty >= 0.4:
            return "Updates existing story with some new information"
        else:
            return f"Largely similar to previous coverage ({similarity*100:.0f}% similar)"

    async def batch_evaluate(
        self,
        articles: list[dict[str, Any]],
        lookback_days: int = 7
    ) -> list[dict[str, Any]]:
        """
        Evaluate novelty for multiple articles

        Args:
            articles: List of articles (should be sorted by publish date)
            lookback_days: Lookback window

        Returns:
            Articles with novelty scores
        """
        results = []

        # Sort by publish date
        sorted_articles = sorted(
            articles,
            key=lambda a: self._parse_date(a.get("published_at")) or datetime.min
        )

        for i, article in enumerate(sorted_articles):
            # Use all previous articles as historical context
            historical = sorted_articles[:i]

            novelty = await self.evaluate_novelty(article, historical, lookback_days)

            article_with_novelty = article.copy()
            article_with_novelty["novelty"] = novelty

            results.append(article_with_novelty)

        return results

    async def find_novel_articles(
        self,
        articles: list[dict[str, Any]],
        min_novelty: float = 0.6,
        lookback_days: int = 7
    ) -> list[dict[str, Any]]:
        """
        Find articles with high novelty scores

        Args:
            articles: List of articles
            min_novelty: Minimum novelty threshold
            lookback_days: Lookback window

        Returns:
            Novel articles
        """
        evaluated = await self.batch_evaluate(articles, lookback_days)

        novel_articles = [
            article for article in evaluated
            if article.get("novelty", {}).get("novelty_score", 0) >= min_novelty
        ]

        self.logger.info(f"Found {len(novel_articles)} novel articles out of {len(articles)}")

        return novel_articles

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse date string to datetime"""
        if not date_str:
            return None

        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None
