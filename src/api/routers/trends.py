#!/usr/bin/env python
"""
Trends API Router

Handles trend detection, sentiment tracking, and novelty evaluation
"""

from pathlib import Path
from typing import Optional
import traceback

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.agents.trend_analyzer import (
    TrendDetectorAgent,
    SentimentTrackerAgent,
    NoveltyEvaluatorAgent
)
from src.agents.news_aggregator.news_storage import NewsStorage
from src.core.core import load_config_with_main
from src.core.logging import get_logger

router = APIRouter()


# Helper to load config
def load_config():
    project_root = Path(__file__).parent.parent.parent.parent
    return load_config_with_main("news.yaml", project_root)


# Initialize logger
logger = get_logger("TrendsAPI")


class TopicSentimentRequest(BaseModel):
    """Request for topic sentiment analysis"""
    topic: str
    days: int = 30


@router.get("/trending")
async def get_trending_topics(
    time_window: int = Query(7, description="Time window in days"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, description="Maximum trends to return")
):
    """
    Get currently trending topics

    Args:
        time_window: Time window for trend analysis (days)
        category: Optional category filter
        limit: Maximum trends to return

    Returns:
        List of trending topics with metrics
    """
    try:
        config = load_config()
        logger.info(f"Getting trending topics (window={time_window} days, category={category})")

        # Load recent articles
        storage = NewsStorage(config)
        articles = await storage.load_articles(
            processed=True,
            limit=1000,
            category=category
        )

        if not articles:
            return {
                "success": True,
                "trends": [],
                "message": "No articles found"
            }

        # Detect trends
        detector = TrendDetectorAgent(config)
        trends = await detector.detect_trends(articles, time_window)

        return {
            "success": True,
            "time_window_days": time_window,
            "total_trends": len(trends),
            "trends": trends[:limit]
        }

    except Exception as e:
        logger.error(f"Error getting trending topics: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline/{topic}")
async def get_topic_timeline(
    topic: str,
    days: int = Query(30, description="Number of days to analyze")
):
    """
    Get timeline of mentions for a specific topic

    Args:
        topic: Topic to track
        days: Number of days

    Returns:
        Timeline data with daily counts
    """
    try:
        config = load_config()
        logger.info(f"Getting timeline for topic: {topic} ({days} days)")

        # Load articles
        storage = NewsStorage(config)
        articles = await storage.load_articles(processed=True, limit=5000)

        if not articles:
            return {
                "success": True,
                "topic": topic,
                "timeline": [],
                "message": "No articles found"
            }

        # Get timeline
        detector = TrendDetectorAgent(config)
        timeline_data = await detector.get_topic_timeline(topic, articles, days)

        return {
            "success": True,
            **timeline_data
        }

    except Exception as e:
        logger.error(f"Error getting topic timeline: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sentiment/topic")
async def analyze_topic_sentiment(request: TopicSentimentRequest):
    """
    Analyze sentiment evolution for a topic

    Args:
        request: Topic and time window

    Returns:
        Sentiment timeline and statistics
    """
    try:
        config = load_config()
        logger.info(f"Analyzing sentiment for topic: {request.topic} ({request.days} days)")

        # Load articles
        storage = NewsStorage(config)
        articles = await storage.load_articles(processed=True, limit=5000)

        if not articles:
            return {
                "success": True,
                "message": "No articles found"
            }

        # Track sentiment
        tracker = SentimentTrackerAgent(config)
        sentiment_data = await tracker.track_topic_sentiment(
            request.topic,
            articles,
            request.days
        )

        return {
            "success": True,
            **sentiment_data
        }

    except Exception as e:
        logger.error(f"Error analyzing topic sentiment: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/articles")
async def get_articles_with_sentiment(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, description="Number of articles")
):
    """
    Get articles with sentiment analysis

    Args:
        category: Optional category filter
        limit: Number of articles

    Returns:
        Articles with sentiment scores
    """
    try:
        config = load_config()

        # Load articles
        storage = NewsStorage(config)
        articles = await storage.load_articles(
            processed=True,
            limit=limit,
            category=category
        )

        if not articles:
            return {
                "success": True,
                "articles": [],
                "message": "No articles found"
            }

        # Analyze sentiment
        tracker = SentimentTrackerAgent(config)
        articles_with_sentiment = await tracker.batch_analyze(articles)

        return {
            "success": True,
            "count": len(articles_with_sentiment),
            "articles": articles_with_sentiment
        }

    except Exception as e:
        logger.error(f"Error getting articles with sentiment: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/novelty/evaluate")
async def evaluate_article_novelty(
    article_id: str = Query(..., description="Article ID to evaluate"),
    lookback_days: int = Query(7, description="Days to look back")
):
    """
    Evaluate novelty of an article

    Args:
        article_id: Article ID
        lookback_days: Lookback window

    Returns:
        Novelty evaluation
    """
    try:
        config = load_config()

        # Load article
        storage = NewsStorage(config)
        article = await storage.get_article_by_id(article_id)

        if not article:
            raise HTTPException(status_code=404, detail=f"Article {article_id} not found")

        # Load historical articles
        historical = await storage.load_articles(processed=True, limit=1000)

        # Evaluate novelty
        evaluator = NoveltyEvaluatorAgent(config)
        novelty = await evaluator.evaluate_novelty(article, historical, lookback_days)

        return {
            "success": True,
            "article_id": article_id,
            "article_title": article.get("title"),
            **novelty
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating novelty: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/novelty/novel-articles")
async def get_novel_articles(
    min_novelty: float = Query(0.6, description="Minimum novelty score"),
    lookback_days: int = Query(7, description="Lookback window"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, description="Maximum articles")
):
    """
    Get articles with high novelty scores

    Args:
        min_novelty: Minimum novelty threshold
        lookback_days: Lookback window
        category: Optional category filter
        limit: Maximum articles

    Returns:
        Novel articles
    """
    try:
        config = load_config()

        # Load articles
        storage = NewsStorage(config)
        articles = await storage.load_articles(
            processed=True,
            limit=500,
            category=category
        )

        if not articles:
            return {
                "success": True,
                "articles": [],
                "message": "No articles found"
            }

        # Find novel articles
        evaluator = NoveltyEvaluatorAgent(config)
        novel_articles = await evaluator.find_novel_articles(
            articles,
            min_novelty,
            lookback_days
        )

        return {
            "success": True,
            "total_novel": len(novel_articles),
            "min_novelty": min_novelty,
            "articles": novel_articles[:limit]
        }

    except Exception as e:
        logger.error(f"Error getting novel articles: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_trend_stats(days: int = Query(7, description="Time window in days")):
    """
    Get overall trend statistics

    Args:
        days: Time window

    Returns:
        Aggregate trend statistics
    """
    try:
        config = load_config()

        # Load articles
        storage = NewsStorage(config)
        articles = await storage.load_articles(processed=True, limit=2000)

        if not articles:
            return {
                "success": True,
                "message": "No articles found"
            }

        # Get trends
        detector = TrendDetectorAgent(config)
        trends = await detector.detect_trends(articles, days)

        # Get average sentiment
        tracker = SentimentTrackerAgent(config)
        articles_with_sentiment = await tracker.batch_analyze(articles[:100])  # Sample

        avg_sentiment = {
            "positive": 0.0,
            "negative": 0.0,
            "neutral": 0.0
        }

        if articles_with_sentiment:
            for article in articles_with_sentiment:
                sent = article.get("sentiment", {})
                avg_sentiment["positive"] += sent.get("positive", 0)
                avg_sentiment["negative"] += sent.get("negative", 0)
                avg_sentiment["neutral"] += sent.get("neutral", 0)

            count = len(articles_with_sentiment)
            avg_sentiment = {k: round(v/count, 2) for k, v in avg_sentiment.items()}

        return {
            "success": True,
            "time_window_days": days,
            "total_articles": len(articles),
            "trending_topics": len(trends),
            "top_trends": trends[:5],
            "average_sentiment": avg_sentiment
        }

    except Exception as e:
        logger.error(f"Error getting trend stats: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
