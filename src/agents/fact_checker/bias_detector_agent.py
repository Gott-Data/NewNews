#!/usr/bin/env python
"""
BiasDetectorAgent - Detects political lean, emotional tone, and loaded language

Analyzes articles for bias indicators to help readers identify potential slant
"""

from typing import Any
import re
from pathlib import Path
import sys

_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.core.logging import get_logger


class BiasDetectorAgent:
    """Agent for detecting bias in news articles"""

    # Loaded language indicators
    LOADED_WORDS = {
        "positive": ["hero", "brilliant", "outstanding", "triumph", "victory", "success"],
        "negative": ["disaster", "failure", "catastrophe", "scandal", "crisis", "outrage"]
    }

    # Political lean indicators (simplified)
    POLITICAL_INDICATORS = {
        "left": ["progressive", "liberal", "socialist", "climate action", "social justice"],
        "right": ["conservative", "traditional", "free market", "law and order", "family values"]
    }

    def __init__(self, config: dict[str, Any]):
        """Initialize bias detector agent"""
        self.config = config
        self.logger = get_logger(name="bias_detector_agent")
        self.bias_config = config.get("fact_check", {}).get("bias_detection", {})
        self.enabled = self.bias_config.get("enabled", True)
        self.logger.info("BiasDetectorAgent initialized")

    async def detect_bias(self, article: dict[str, Any]) -> dict[str, Any]:
        """
        Detect bias in an article

        Args:
            article: Article dictionary with title and content

        Returns:
            Bias analysis dictionary
        """
        if not self.enabled:
            return {"bias_detection_enabled": False}

        title = article.get("title", "")
        content = article.get("content", "")
        text = f"{title} {content}".lower()

        analysis = {
            "political_lean": "neutral",
            "political_confidence": 0.0,
            "emotional_tone": "balanced",
            "loaded_language": [],
            "bias_indicators": []
        }

        # 1. Detect political lean
        if self.bias_config.get("check_political_lean", True):
            lean_analysis = self._detect_political_lean(text)
            analysis.update(lean_analysis)

        # 2. Detect emotional tone
        if self.bias_config.get("check_emotional_tone", True):
            tone_analysis = self._detect_emotional_tone(text)
            analysis["emotional_tone"] = tone_analysis

        # 3. Detect loaded language
        if self.bias_config.get("check_loaded_language", True):
            loaded = self._detect_loaded_language(text)
            analysis["loaded_language"] = loaded

        # 4. Overall bias score
        analysis["overall_bias_score"] = self._calculate_bias_score(analysis)

        return analysis

    def _detect_political_lean(self, text: str) -> dict[str, Any]:
        """Detect political lean based on keyword indicators"""
        left_score = 0
        right_score = 0

        for keyword in self.POLITICAL_INDICATORS["left"]:
            left_score += len(re.findall(r"\b" + re.escape(keyword) + r"\b", text, re.IGNORECASE))

        for keyword in self.POLITICAL_INDICATORS["right"]:
            right_score += len(re.findall(r"\b" + re.escape(keyword) + r"\b", text, re.IGNORECASE))

        total = left_score + right_score

        if total == 0:
            return {"political_lean": "neutral", "political_confidence": 0.0}

        if left_score > right_score * 1.5:
            lean = "left"
            confidence = min(0.9, left_score / total)
        elif right_score > left_score * 1.5:
            lean = "right"
            confidence = min(0.9, right_score / total)
        else:
            lean = "neutral"
            confidence = 0.5

        return {
            "political_lean": lean,
            "political_confidence": round(confidence, 2)
        }

    def _detect_emotional_tone(self, text: str) -> str:
        """Detect emotional tone (positive/negative/balanced)"""
        positive_count = 0
        negative_count = 0

        for word in self.LOADED_WORDS["positive"]:
            positive_count += len(re.findall(r"\b" + re.escape(word) + r"\b", text, re.IGNORECASE))

        for word in self.LOADED_WORDS["negative"]:
            negative_count += len(re.findall(r"\b" + re.escape(word) + r"\b", text, re.IGNORECASE))

        total = positive_count + negative_count

        if total == 0:
            return "balanced"

        ratio = positive_count / total if total > 0 else 0.5

        if ratio > 0.65:
            return "positive"
        elif ratio < 0.35:
            return "negative"
        else:
            return "balanced"

    def _detect_loaded_language(self, text: str) -> list[str]:
        """Detect instances of loaded/emotional language"""
        loaded_instances = []

        all_loaded_words = self.LOADED_WORDS["positive"] + self.LOADED_WORDS["negative"]

        for word in all_loaded_words:
            pattern = r"\b" + re.escape(word) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                loaded_instances.append(word)

        return loaded_instances[:10]  # Limit to 10 examples

    def _calculate_bias_score(self, analysis: dict[str, Any]) -> float:
        """Calculate overall bias score (0 = unbiased, 1 = heavily biased)"""
        score = 0.0

        # Political lean factor
        if analysis["political_lean"] != "neutral":
            score += analysis["political_confidence"] * 0.4

        # Emotional tone factor
        if analysis["emotional_tone"] != "balanced":
            score += 0.3

        # Loaded language factor
        loaded_count = len(analysis["loaded_language"])
        if loaded_count > 0:
            score += min(0.3, loaded_count * 0.05)

        return round(min(1.0, score), 2)

    async def batch_detect(self, articles: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """
        Detect bias in multiple articles

        Args:
            articles: List of articles

        Returns:
            Dictionary mapping article IDs to bias analysis
        """
        results = {}

        for article in articles:
            article_id = article.get("id")
            analysis = await self.detect_bias(article)
            results[article_id] = analysis

        return results
