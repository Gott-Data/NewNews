#!/usr/bin/env python
"""
Content Generation API Router

Handles automated content creation including image generation,
article synthesis, and headline generation
"""

from pathlib import Path
from typing import Optional
import traceback

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.agents.content_generator import (
    ImageGenerationAgent,
    ArticleSynthesisAgent,
    HeadlineGeneratorAgent
)
from src.agents.news_aggregator.news_storage import NewsStorage
from src.core.core import get_llm_config, load_config_with_main
from src.core.logging import get_logger

router = APIRouter()


# Helper to load config
def load_config():
    project_root = Path(__file__).parent.parent.parent.parent
    return load_config_with_main("news.yaml", project_root)


# Initialize logger
logger = get_logger("ContentAPI")


class GenerateImageRequest(BaseModel):
    """Request for image generation"""
    article_id: str
    prompt_override: Optional[str] = None


class SynthesizeRequest(BaseModel):
    """Request for article synthesis"""
    article_ids: list[str]
    topic: Optional[str] = None


class GenerateHeadlineRequest(BaseModel):
    """Request for headline generation"""
    article_id: str
    style: str = "balanced"  # balanced, engaging, factual


@router.post("/generate/image")
async def generate_image(request: GenerateImageRequest):
    """
    Generate an image for a news article

    Args:
        request: Image generation request

    Returns:
        Generated image path and URL
    """
    try:
        config = load_config()
        logger.info(f"Generating image for article: {request.article_id}")

        # Load article
        storage = NewsStorage(config)
        article = await storage.get_article_by_id(request.article_id)

        if not article:
            raise HTTPException(status_code=404, detail=f"Article {request.article_id} not found")

        # Generate image
        generator = ImageGenerationAgent(config)
        result = await generator.generate_image(article, request.prompt_override)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Image generation failed"))

        # Convert to URL
        image_url = generator.get_image_url(result["image_path"])

        return {
            "success": True,
            "article_id": request.article_id,
            "image_path": result["image_path"],
            "image_url": image_url,
            "prompt": result.get("prompt"),
            "cached": result.get("cached", False)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/article")
async def synthesize_article(request: SynthesizeRequest):
    """
    Synthesize an article from multiple sources

    Args:
        request: Synthesis request with article IDs

    Returns:
        Synthesized article
    """
    try:
        config = load_config()
        logger.info(f"Synthesizing article from {len(request.article_ids)} sources")

        # Get LLM config
        llm_config = get_llm_config()
        api_key = llm_config["api_key"]
        base_url = llm_config["base_url"]

        # Load articles
        storage = NewsStorage(config)
        articles = []

        for article_id in request.article_ids:
            article = await storage.get_article_by_id(article_id)
            if article:
                articles.append(article)

        if not articles:
            raise HTTPException(status_code=404, detail="No articles found")

        # Synthesize
        synthesizer = ArticleSynthesisAgent(config, api_key, base_url)
        result = await synthesizer.synthesize_from_sources(articles, request.topic)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Synthesis failed"))

        return {
            "success": True,
            **result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error synthesizing article: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/headline")
async def generate_headline(request: GenerateHeadlineRequest):
    """
    Generate headline variants for an article

    Args:
        request: Headline generation request

    Returns:
        Generated headlines
    """
    try:
        config = load_config()
        logger.info(f"Generating headline for article: {request.article_id}")

        # Get LLM config
        llm_config = get_llm_config()
        api_key = llm_config["api_key"]
        base_url = llm_config["base_url"]

        # Load article
        storage = NewsStorage(config)
        article = await storage.get_article_by_id(request.article_id)

        if not article:
            raise HTTPException(status_code=404, detail=f"Article {request.article_id} not found")

        # Generate headline
        generator = HeadlineGeneratorAgent(config, api_key, base_url)
        result = await generator.generate_headline(article, request.style)

        return {
            "success": True,
            "article_id": request.article_id,
            **result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating headline: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/digest")
async def generate_daily_digest(
    days: int = Query(1, description="Number of days to include"),
    max_stories: int = Query(10, description="Maximum stories in digest")
):
    """
    Generate a daily news digest

    Args:
        days: Number of days to include
        max_stories: Maximum stories

    Returns:
        Daily digest with synthesized stories
    """
    try:
        config = load_config()
        logger.info(f"Generating daily digest ({days} days, max {max_stories} stories)")

        # Get LLM config
        llm_config = get_llm_config()
        api_key = llm_config["api_key"]
        base_url = llm_config["base_url"]

        # Load recent articles
        storage = NewsStorage(config)
        articles = await storage.load_articles(processed=True, limit=500)

        if not articles:
            return {
                "success": True,
                "message": "No articles found",
                "stories": []
            }

        # Generate digest
        synthesizer = ArticleSynthesisAgent(config, api_key, base_url)
        digest = await synthesizer.generate_daily_digest(articles, max_stories)

        return {
            "success": True,
            **digest
        }

    except Exception as e:
        logger.error(f"Error generating digest: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/images")
async def batch_generate_images(
    article_ids: list[str],
    max_images: int = Query(10, description="Maximum images to generate")
):
    """
    Generate images for multiple articles

    Args:
        article_ids: List of article IDs
        max_images: Maximum images to generate

    Returns:
        List of generated images
    """
    try:
        config = load_config()
        logger.info(f"Batch generating {min(len(article_ids), max_images)} images")

        # Load articles
        storage = NewsStorage(config)
        articles = []

        for article_id in article_ids[:max_images]:
            article = await storage.get_article_by_id(article_id)
            if article:
                articles.append(article)

        if not articles:
            raise HTTPException(status_code=404, detail="No articles found")

        # Generate images
        generator = ImageGenerationAgent(config)
        results = await generator.batch_generate(articles, max_images)

        return {
            "success": True,
            "total": len(results),
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch image generation: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
