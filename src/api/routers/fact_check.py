#!/usr/bin/env python
"""
Fact-Checking API Router

Handles claim verification, bias detection, and credibility scoring
"""

from pathlib import Path
from typing import Optional
import traceback

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.agents.fact_checker.fact_check_pipeline import FactCheckPipeline
from src.agents.news_aggregator.news_storage import NewsStorage
from src.core.core import get_llm_config, load_config_with_main
from src.core.logging import get_logger

router = APIRouter()


# Helper to load config
def load_config():
    project_root = Path(__file__).parent.parent.parent.parent
    return load_config_with_main("news.yaml", project_root)


# Initialize logger
logger = get_logger("FactCheckAPI")


class VerifyRequest(BaseModel):
    """Request model for fact-checking"""
    article_id: str
    preset: str = "quick"  # quick, thorough, or deep
    max_claims: int = 5
    kb_name: Optional[str] = None


class VerifyTextRequest(BaseModel):
    """Request model for fact-checking raw text"""
    title: str
    content: str
    preset: str = "quick"
    max_claims: int = 5
    kb_name: Optional[str] = None


@router.post("/verify")
async def verify_article(request: VerifyRequest):
    """
    Fact-check a news article by ID

    Args:
        request: Verification request with article ID and parameters

    Returns:
        Complete fact-check results
    """
    try:
        config = load_config()
        logger.info(f"Fact-checking article: {request.article_id} (preset={request.preset})")

        # Get LLM config
        llm_config = get_llm_config()
        api_key = llm_config["api_key"]
        base_url = llm_config["base_url"]

        # Load article
        storage = NewsStorage(config)
        article = await storage.get_article_by_id(request.article_id)

        if not article:
            raise HTTPException(status_code=404, detail=f"Article {request.article_id} not found")

        # Initialize pipeline
        pipeline = FactCheckPipeline(config, api_key, base_url)

        # Run fact-check
        result = await pipeline.fact_check_article(
            article=article,
            preset=request.preset,
            max_claims=request.max_claims,
            kb_name=request.kb_name
        )

        return {
            "success": True,
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fact-checking article: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify/text")
async def verify_text(request: VerifyTextRequest):
    """
    Fact-check raw text (not from database)

    Args:
        request: Text verification request

    Returns:
        Fact-check results
    """
    try:
        config = load_config()
        logger.info(f"Fact-checking text: {request.title[:50]}... (preset={request.preset})")

        # Get LLM config
        llm_config = get_llm_config()
        api_key = llm_config["api_key"]
        base_url = llm_config["base_url"]

        # Create article-like structure
        article = {
            "id": "temp",
            "title": request.title,
            "content": request.content
        }

        # Initialize pipeline
        pipeline = FactCheckPipeline(config, api_key, base_url)

        # Run fact-check
        result = await pipeline.fact_check_article(
            article=article,
            preset=request.preset,
            max_claims=request.max_claims,
            kb_name=request.kb_name
        )

        return {
            "success": True,
            "result": result
        }

    except Exception as e:
        logger.error(f"Error fact-checking text: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_fact_check_history(
    limit: int = Query(20, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip")
):
    """
    Get history of fact-checked articles

    Args:
        limit: Number of results
        offset: Pagination offset

    Returns:
        List of fact-check results
    """
    try:
        # TODO: Implement fact-check history storage
        # For now, return empty list
        return {
            "success": True,
            "total": 0,
            "results": []
        }

    except Exception as e:
        logger.error(f"Error getting fact-check history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/presets")
async def get_presets():
    """
    Get available fact-checking presets and their configurations

    Returns:
        Dictionary of presets
    """
    try:
        config = load_config()
        presets = config.get("fact_check", {}).get("presets", {})

        return {
            "success": True,
            "presets": presets
        }

    except Exception as e:
        logger.error(f"Error getting presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources/credibility")
async def get_source_credibility(source_name: str = Query(..., description="Source name to check")):
    """
    Get credibility score for a news source

    Args:
        source_name: Name of the source

    Returns:
        Credibility score
    """
    try:
        config = load_config()

        from src.agents.fact_checker import CredibilityScoreAgent

        scorer = CredibilityScoreAgent(config)
        score = scorer.score_source(source_name)

        return {
            "success": True,
            "source": source_name,
            "credibility_score": score
        }

    except Exception as e:
        logger.error(f"Error getting source credibility: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def verify_batch(article_ids: list[str], preset: str = "quick", kb_name: Optional[str] = None):
    """
    Fact-check multiple articles in batch

    Args:
        article_ids: List of article IDs
        preset: Fact-check preset
        kb_name: Knowledge base name

    Returns:
        List of fact-check results
    """
    try:
        config = load_config()
        logger.info(f"Batch fact-checking {len(article_ids)} articles (preset={preset})")

        # Get LLM config
        llm_config = get_llm_config()
        api_key = llm_config["api_key"]
        base_url = llm_config["base_url"]

        # Load articles
        storage = NewsStorage(config)
        articles = []

        for article_id in article_ids:
            article = await storage.get_article_by_id(article_id)
            if article:
                articles.append(article)

        if not articles:
            raise HTTPException(status_code=404, detail="No articles found")

        # Initialize pipeline
        pipeline = FactCheckPipeline(config, api_key, base_url)

        # Run batch fact-check
        results = await pipeline.fact_check_batch(
            articles=articles,
            preset=preset,
            max_claims_per_article=3,  # Limit for batch processing
            kb_name=kb_name
        )

        return {
            "success": True,
            "total": len(results),
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch fact-check: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
