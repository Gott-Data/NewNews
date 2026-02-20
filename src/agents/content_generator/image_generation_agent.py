#!/usr/bin/env python
"""
ImageGenerationAgent - Generates images for news articles using Stability AI

Creates relevant, photorealistic images based on article content
"""

from pathlib import Path
from typing import Any
import hashlib
import os
import sys

_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.core.logging import get_logger


class ImageGenerationAgent:
    """Agent for generating images using Stability AI"""

    def __init__(self, config: dict[str, Any]):
        """Initialize image generation agent"""
        self.config = config
        self.image_config = config.get("content_generation", {}).get("images", {})
        self.logger = get_logger(name="image_generation_agent")

        self.provider = self.image_config.get("provider", "stability_ai")
        self.model = self.image_config.get("model", "stable-diffusion-xl-1024-v1-0")
        self.width = self.image_config.get("width", 1024)
        self.height = self.image_config.get("height", 1024)
        self.cache_enabled = self.image_config.get("cache_enabled", True)

        # Storage path
        news_storage = config.get("news", {}).get("storage", {})
        self.images_dir = Path(news_storage.get("images_dir", "./data/news/generated_images"))
        self.images_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"ImageGenerationAgent initialized (provider={self.provider})")

    async def generate_image(
        self,
        article: dict[str, Any],
        prompt_override: str | None = None
    ) -> dict[str, Any]:
        """
        Generate an image for a news article

        Args:
            article: Article dictionary
            prompt_override: Optional custom prompt (overrides auto-generated)

        Returns:
            Image generation result with file path
        """
        # Generate prompt from article if not provided
        if prompt_override:
            prompt = prompt_override
        else:
            prompt = self._generate_prompt(article)

        self.logger.info(f"Generating image: {prompt[:50]}...")

        # Check cache
        if self.cache_enabled:
            cached = self._check_cache(prompt)
            if cached:
                self.logger.info(f"Using cached image: {cached}")
                return {
                    "success": True,
                    "image_path": cached,
                    "prompt": prompt,
                    "cached": True
                }

        # Generate new image
        try:
            if self.provider == "stability_ai":
                result = await self._generate_with_stability(prompt)
            else:
                raise ValueError(f"Unknown image provider: {self.provider}")

            # Cache result
            if self.cache_enabled and result.get("image_path"):
                self._save_to_cache(prompt, result["image_path"])

            return {
                "success": True,
                **result,
                "cached": False
            }

        except Exception as e:
            self.logger.error(f"Image generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }

    def _generate_prompt(self, article: dict[str, Any]) -> str:
        """
        Generate image prompt from article content

        Args:
            article: Article dictionary

        Returns:
            Image generation prompt
        """
        title = article.get("title", "")
        description = article.get("description", "")
        category = article.get("category", "general")

        # Build prompt based on category
        style_prefix = self._get_style_prefix(category)

        # Create focused prompt (under 1000 chars for Stability AI)
        if description:
            subject = description[:200]  # First 200 chars
        else:
            subject = title

        prompt = f"{style_prefix}, {subject}, high quality, professional news photography"

        return prompt[:1000]  # Stability AI limit

    def _get_style_prefix(self, category: str) -> str:
        """Get style prefix based on article category"""
        style_map = {
            "technology": "modern tech scene, futuristic",
            "science": "scientific illustration, educational",
            "health": "medical setting, clean and professional",
            "business": "corporate environment, business meeting",
            "politics": "government building, political scene",
            "sports": "athletic action, sports venue",
            "entertainment": "entertainment venue, vibrant",
            "environment": "nature scene, environmental",
        }

        return style_map.get(category, "photorealistic news image")

    async def _generate_with_stability(self, prompt: str) -> dict[str, Any]:
        """
        Generate image using Stability AI API

        Args:
            prompt: Image generation prompt

        Returns:
            Generation result
        """
        try:
            import requests
            import base64
            from datetime import datetime

            api_key = os.getenv("STABILITY_API_KEY")
            if not api_key:
                raise ValueError("STABILITY_API_KEY not set in environment")

            # Stability AI API endpoint
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            body = {
                "text_prompts": [
                    {
                        "text": prompt,
                        "weight": 1
                    },
                    {
                        "text": "blurry, bad quality, distorted, text, watermark",
                        "weight": -1
                    }
                ],
                "cfg_scale": self.image_config.get("cfg_scale", 7),
                "height": self.height,
                "width": self.width,
                "samples": 1,
                "steps": self.image_config.get("steps", 30),
            }

            response = requests.post(url, headers=headers, json=body, timeout=60)

            if response.status_code != 200:
                raise ValueError(f"Stability API error: {response.status_code} - {response.text}")

            data = response.json()

            # Save image
            if "artifacts" in data and len(data["artifacts"]) > 0:
                image_data = data["artifacts"][0]["base64"]
                image_bytes = base64.b64decode(image_data)

                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
                filename = f"image_{timestamp}_{prompt_hash}.png"
                filepath = self.images_dir / filename

                # Save to file
                with open(filepath, "wb") as f:
                    f.write(image_bytes)

                self.logger.info(f"Image saved: {filepath}")

                return {
                    "image_path": str(filepath),
                    "filename": filename,
                    "prompt": prompt,
                    "model": self.model
                }
            else:
                raise ValueError("No image generated in response")

        except ImportError:
            raise ValueError("requests library required for Stability AI. Run: pip install requests")

        except Exception as e:
            self.logger.error(f"Stability AI generation failed: {e}")
            raise

    def _check_cache(self, prompt: str) -> str | None:
        """
        Check if image for this prompt exists in cache

        Args:
            prompt: Image generation prompt

        Returns:
            Cached image path or None
        """
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]

        # Look for files with this hash
        for filepath in self.images_dir.glob(f"*_{prompt_hash}.png"):
            return str(filepath)

        return None

    def _save_to_cache(self, prompt: str, image_path: str) -> None:
        """Save prompt -> image mapping to cache metadata"""
        # Cache is implicit through filename hash
        # Could extend with JSON metadata file if needed
        pass

    async def batch_generate(
        self,
        articles: list[dict[str, Any]],
        max_images: int = 10
    ) -> list[dict[str, Any]]:
        """
        Generate images for multiple articles

        Args:
            articles: List of articles
            max_images: Maximum images to generate

        Returns:
            List of generation results
        """
        results = []

        for i, article in enumerate(articles[:max_images]):
            self.logger.info(f"Generating image {i+1}/{min(len(articles), max_images)}")
            result = await self.generate_image(article)
            results.append({
                "article_id": article.get("id"),
                "article_title": article.get("title"),
                **result
            })

        return results

    def get_image_url(self, image_path: str, base_url: str = "") -> str:
        """
        Convert local image path to URL

        Args:
            image_path: Local file path
            base_url: Base URL for API

        Returns:
            Image URL
        """
        # Convert absolute path to relative API path
        filepath = Path(image_path)
        filename = filepath.name

        return f"{base_url}/api/outputs/news/generated_images/{filename}"
