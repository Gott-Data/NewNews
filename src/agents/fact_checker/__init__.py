"""
Fact Checker Module

Multi-source claim verification and bias detection agents for news articles.
"""

from .claim_extractor_agent import ClaimExtractorAgent
from .evidence_gather_agent import EvidenceGatherAgent
from .verification_agent import VerificationAgent
from .credibility_score_agent import CredibilityScoreAgent
from .bias_detector_agent import BiasDetectorAgent

__all__ = [
    "ClaimExtractorAgent",
    "EvidenceGatherAgent",
    "VerificationAgent",
    "CredibilityScoreAgent",
    "BiasDetectorAgent",
]
