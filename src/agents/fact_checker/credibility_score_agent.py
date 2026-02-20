#!/usr/bin/env python
"""
CredibilityScoreAgent - Rates the credibility of sources and claims

Assigns credibility scores based on source reputation and evidence quality
"""

from typing import Any
from pathlib import Path
import sys

_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.core.logging import get_logger


class CredibilityScoreAgent:
    """Agent for scoring source and claim credibility"""

    # Source credibility ratings (0.0 to 1.0)
    SOURCE_RATINGS = {
        # Tier 1: Highly credible
        "reuters": 0.96,
        "associated press": 0.96,
        "bbc": 0.95,
        "the guardian": 0.92,
        "new york times": 0.93,
        "washington post": 0.91,
        "nature": 0.97,
        "science": 0.97,
        "arxiv": 0.90,

        # Tier 2: Generally credible
        "npr": 0.89,
        "the economist": 0.88,
        "wired": 0.85,
        "the verge": 0.82,

        # Default
        "default": 0.70
    }

    def __init__(self, config: dict[str, Any]):
        """Initialize credibility score agent"""
        self.config = config
        self.logger = get_logger(name="credibility_score_agent")
        self.fact_check_config = config.get("fact_check", {}).get("credibility", {})
        self.source_weight = self.fact_check_config.get("source_weight", 0.4)
        self.evidence_weight = self.fact_check_config.get("evidence_weight", 0.6)
        self.logger.info("CredibilityScoreAgent initialized")

    def score_source(self, source_name: str) -> float:
        """
        Get credibility score for a source

        Args:
            source_name: Name of the news source

        Returns:
            Credibility score (0.0 to 1.0)
        """
        source_lower = source_name.lower()

        for known_source, rating in self.SOURCE_RATINGS.items():
            if known_source in source_lower:
                return rating

        return self.SOURCE_RATINGS["default"]

    def score_claim_verification(
        self,
        verification_result: dict[str, Any],
        evidence: list[dict[str, Any]]
    ) -> float:
        """
        Score the overall credibility of a fact-check result

        Args:
            verification_result: Result from VerificationAgent
            evidence: List of evidence items

        Returns:
            Overall credibility score (0.0 to 1.0)
        """
        # Component 1: Source credibility (average of all sources)
        source_scores = [self.score_source(ev.get("source_name", "")) for ev in evidence]
        avg_source_score = sum(source_scores) / len(source_scores) if source_scores else 0.5

        # Component 2: Evidence strength (based on verification confidence)
        evidence_score = verification_result.get("confidence", 0.5)

        # Weighted combination
        overall_score = (
            avg_source_score * self.source_weight +
            evidence_score * self.evidence_weight
        )

        return round(overall_score, 2)

    def add_custom_source(self, source_name: str, rating: float):
        """
        Add a custom source rating

        Args:
            source_name: Source name
            rating: Credibility rating (0.0 to 1.0)
        """
        self.SOURCE_RATINGS[source_name.lower()] = rating
        self.logger.info(f"Added custom source rating: {source_name} = {rating}")
