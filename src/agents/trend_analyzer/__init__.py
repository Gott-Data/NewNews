"""
Trend Analyzer Module

Agents for detecting trends, tracking sentiment, and evaluating novelty in news coverage.
"""

from .trend_detector_agent import TrendDetectorAgent
from .sentiment_tracker_agent import SentimentTrackerAgent
from .novelty_evaluator_agent import NoveltyEvaluatorAgent

__all__ = [
    "TrendDetectorAgent",
    "SentimentTrackerAgent",
    "NoveltyEvaluatorAgent",
]
