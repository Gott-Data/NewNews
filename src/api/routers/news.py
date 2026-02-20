#!/usr/bin/env python
"""
News API Router

Handles news aggregation, retrieval, and management endpoints
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
import traceback

from fastapi import APIRouter, HTTPException, Query, WebSocket
from pydantic import BaseModel

from src.agents.news_aggregator import (
    NewsScraperAgent,
    ContentParserAgent,
    DeduplicationAgent,
    CategoryAgent
)
from src.agents.news_aggregator.news_storage import NewsStorage
from src.core.core import load_config_with_main
from src.core.logging import get_logger

router = APIRouter()


# Helper to load config (with main.yaml merge)
def load_config():
    project_root = Path(__file__).parent.parent.parent.parent
    return load_config_with_main("news.yaml", project_root)


# Initialize logger
config = load_config()
logger = get_logger("NewsAPI")


class FetchNewsRequest(BaseModel):
    """Request model for fetching news"""
    category: Optional[str] = None
    hours: Optional[int] = 24
    sources: Optional[list[str]] = None


class SearchRequest(BaseModel):
    """Request model for searching articles"""
    query: str
    category: Optional[str] = None
    source: Optional[str] = None
    limit: int = 20


@router.post("/fetch")
async def fetch_news(request: FetchNewsRequest):
    """
    Trigger news aggregation from all configured sources

    Args:
        request: Fetch news request parameters

    Returns:
        Aggregation results with article count
    """
    try:
        config = load_config()
        logger.info(f"Starting news fetch: category={request.category}, hours={request.hours}")

        # Initialize agents
        scraper = NewsScraperAgent(config)
        parser = ContentParserAgent(config)
        dedup = DeduplicationAgent(config)
        categorizer = CategoryAgent(config)
        storage = NewsStorage(config)

        # Fetch raw articles
        if request.category:
            raw_articles = await scraper.fetch_by_category(request.category)
        elif request.hours:
            raw_articles = await scraper.fetch_recent(hours=request.hours)
        else:
            raw_articles = await scraper.fetch_all_sources()

        logger.info(f"Fetched {len(raw_articles)} raw articles")

        # Parse and clean
        parsed_articles = await parser.parse_batch(raw_articles)
        logger.info(f"Parsed {len(parsed_articles)} articles")

        # Deduplicate
        unique_articles = await dedup.deduplicate(parsed_articles)
        logger.info(f"After deduplication: {len(unique_articles)} unique articles")

        # Categorize
        categorized_articles = await categorizer.categorize_batch(unique_articles)
        logger.info(f"Categorized {len(categorized_articles)} articles")

        # Save processed articles
        await storage.save_articles(categorized_articles, processed=True)

        # Get category distribution
        category_stats = await categorizer.get_category_stats(categorized_articles)

        return {
            "success": True,
            "total_fetched": len(raw_articles),
            "total_unique": len(unique_articles),
            "total_saved": len(categorized_articles),
            "categories": category_stats.get("categories", {}),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles")
async def get_articles(
    category: Optional[str] = Query(None, description="Filter by category"),
    source: Optional[str] = Query(None, description="Filter by source"),
    language: Optional[str] = Query(None, description="Filter by language"),
    limit: int = Query(20, description="Maximum number of articles to return"),
    offset: int = Query(0, description="Number of articles to skip")
):
    """
    Get list of articles with optional filtering

    Args:
        category: Filter by category
        source: Filter by source
        language: Filter by language
        limit: Maximum articles to return
        offset: Pagination offset

    Returns:
        List of articles
    """
    try:
        config = load_config()
        storage = NewsStorage(config)

        # Load articles with filters
        articles = await storage.load_articles(
            processed=True,
            limit=limit + offset,  # Load extra for offset
            category=category,
            source=source
        )

        # Filter by language if specified
        if language:
            articles = [a for a in articles if a.get("language") == language]

        # Apply pagination
        paginated_articles = articles[offset:offset + limit]

        return {
            "success": True,
            "total": len(articles),
            "count": len(paginated_articles),
            "offset": offset,
            "limit": limit,
            "articles": paginated_articles
        }

    except Exception as e:
        logger.error(f"Error getting articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/article/{article_id}")
async def get_article(article_id: str):
    """
    Get a single article by ID

    Args:
        article_id: Article ID

    Returns:
        Article details
    """
    try:
        config = load_config()
        storage = NewsStorage(config)

        article = await storage.get_article_by_id(article_id)

        if not article:
            raise HTTPException(status_code=404, detail=f"Article {article_id} not found")

        return {
            "success": True,
            "article": article
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
async def get_sources():
    """
    Get list of configured news sources

    Returns:
        List of sources with configuration
    """
    try:
        config = load_config()
        sources_config = config.get("news", {}).get("sources", {})

        sources = []

        # NewsAPI
        if sources_config.get("newsapi", {}).get("enabled"):
            sources.append({
                "name": "NewsAPI",
                "type": "api",
                "enabled": True,
                "countries": sources_config["newsapi"].get("countries", [])
            })

        # Guardian
        if sources_config.get("guardian", {}).get("enabled"):
            sources.append({
                "name": "The Guardian",
                "type": "api",
                "enabled": True
            })

        # RSS feeds
        for feed in sources_config.get("rss_feeds", []):
            sources.append({
                "name": feed.get("name"),
                "type": "rss",
                "enabled": True,
                "language": feed.get("language"),
                "credibility_score": feed.get("credibility_score")
            })

        return {
            "success": True,
            "count": len(sources),
            "sources": sources
        }

    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """
    Get storage statistics

    Returns:
        Statistics about stored articles
    """
    try:
        config = load_config()
        storage = NewsStorage(config)

        stats = await storage.get_stats()

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
async def cleanup_old_articles():
    """
    Delete articles older than the configured retention period

    Returns:
        Number of articles deleted
    """
    try:
        config = load_config()
        storage = NewsStorage(config)

        deleted_count = await storage.delete_old_articles()

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} old article files"
        }

    except Exception as e:
        logger.error(f"Error cleaning up articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recategorize")
async def recategorize_articles():
    """
    Force recategorization of all articles based on content

    Returns:
        Recategorization results
    """
    try:
        config = load_config()
        storage = NewsStorage(config)
        categorizer = CategoryAgent(config)

        # Load all articles
        articles = await storage.load_articles(processed=True, limit=None)

        # Recategorize
        recategorized = await categorizer.recategorize_by_content(articles)

        # Save updated articles
        await storage.save_articles(recategorized, processed=True)

        # Get new stats
        category_stats = await categorizer.get_category_stats(recategorized)

        return {
            "success": True,
            "total_articles": len(recategorized),
            "categories": category_stats.get("categories", {})
        }

    except Exception as e:
        logger.error(f"Error recategorizing articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/live")
async def websocket_live_news(websocket: WebSocket):
    """
    WebSocket endpoint for real-time news updates

    Sends new articles as they are aggregated
    """
    await websocket.accept()

    try:
        # Get filter preferences
        data = await websocket.receive_json()
        category_filter = data.get("category")
        source_filter = data.get("source")

        logger.info(f"WebSocket connected: category={category_filter}, source={source_filter}")

        # Send initial batch of recent articles
        config = load_config()
        storage = NewsStorage(config)

        recent_articles = await storage.load_articles(
            processed=True,
            limit=10,
            category=category_filter,
            source=source_filter
        )

        await websocket.send_json({
            "type": "initial",
            "articles": recent_articles
        })

        # Keep connection alive and send updates
        # (In production, this would monitor for new articles and push them)
        while True:
            await asyncio.sleep(60)  # Check every minute

            # For now, just send a heartbeat
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            })

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        traceback.print_exc()
    finally:
        logger.info("WebSocket disconnected")
