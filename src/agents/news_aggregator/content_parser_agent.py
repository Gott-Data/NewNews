#!/usr/bin/env python
"""
ContentParserAgent - Cleans and structures raw news articles

Extracts metadata, cleans HTML, detects language, and formats articles
"""

import re
from datetime import datetime
from typing import Any
from pathlib import Path

from src.core.logging import get_logger


class ContentParserAgent:
    """Agent for parsing and cleaning news content"""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize content parser agent

        Args:
            config: Complete configuration dictionary
        """
        self.config = config
        self.news_config = config.get("news", {})
        self.logger = get_logger(name="content_parser_agent")

        # Processing config
        self.processing_config = self.news_config.get("processing", {})
        self.extract_entities = self.processing_config.get("extract_entities", True)
        self.extract_keywords = self.processing_config.get("extract_keywords", True)
        self.generate_summary = self.processing_config.get("generate_summary", True)
        self.detect_language = self.processing_config.get("detect_language", True)

        self.logger.info("ContentParserAgent initialized")

    async def parse_article(self, raw_article: dict[str, Any]) -> dict[str, Any]:
        """
        Parse and clean a single article

        Args:
            raw_article: Raw article dictionary

        Returns:
            Cleaned and structured article
        """
        try:
            # Clean the content
            cleaned_content = self._clean_html(raw_article.get("content", ""))
            cleaned_description = self._clean_html(raw_article.get("description", ""))

            # Detect language if enabled
            detected_lang = raw_article.get("language", "en")
            if self.detect_language and cleaned_content:
                detected_lang = await self._detect_language(cleaned_content)

            # Build parsed article
            parsed = {
                "id": raw_article.get("id"),
                "source": raw_article.get("source"),
                "source_name": raw_article.get("source_name"),
                "title": self._clean_text(raw_article.get("title", "")),
                "description": cleaned_description,
                "content": cleaned_content,
                "url": raw_article.get("url"),
                "image_url": raw_article.get("image_url"),
                "published_at": self._parse_datetime(raw_article.get("published_at")),
                "author": raw_article.get("author"),
                "category": raw_article.get("category", "general"),
                "country": raw_article.get("country"),
                "language": detected_lang,
                "credibility_score": raw_article.get("credibility_score", 0.85),
                "fetched_at": raw_article.get("fetched_at"),
                "processed_at": datetime.now().isoformat(),
                "word_count": len(cleaned_content.split()) if cleaned_content else 0,
            }

            # Extract metadata if enabled
            if self.extract_keywords and cleaned_content:
                parsed["keywords"] = await self._extract_keywords(cleaned_content)

            if self.extract_entities and cleaned_content:
                parsed["entities"] = await self._extract_entities(cleaned_content)

            if self.generate_summary and cleaned_content:
                parsed["summary"] = await self._generate_summary(cleaned_content)

            return parsed

        except Exception as e:
            self.logger.error(f"Error parsing article {raw_article.get('id')}: {e}")
            return raw_article  # Return original if parsing fails

    async def parse_batch(self, raw_articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Parse multiple articles

        Args:
            raw_articles: List of raw article dictionaries

        Returns:
            List of parsed articles
        """
        self.logger.info(f"Parsing {len(raw_articles)} articles...")

        parsed_articles = []
        for article in raw_articles:
            parsed = await self.parse_article(article)
            if parsed:
                parsed_articles.append(parsed)

        self.logger.info(f"Successfully parsed {len(parsed_articles)} articles")
        return parsed_articles

    def _clean_html(self, text: str) -> str:
        """
        Remove HTML tags and clean text

        Args:
            text: Raw HTML text

        Returns:
            Clean text
        """
        if not text:
            return ""

        try:
            from bs4 import BeautifulSoup

            # Parse HTML
            soup = BeautifulSoup(text, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            return text

        except ImportError:
            # Fallback: simple regex-based HTML removal
            text = re.sub(r"<[^>]+>", "", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text

        Args:
            text: Input text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Remove common noise patterns
        text = re.sub(r"\[.*?\]", "", text)  # Remove [brackets]
        text = re.sub(r"\(.*?\)", "", text)  # Remove (parentheses)

        return text

    def _parse_datetime(self, dt_str: str) -> str:
        """
        Parse and normalize datetime string

        Args:
            dt_str: Datetime string in various formats

        Returns:
            ISO format datetime string
        """
        if not dt_str:
            return datetime.now().isoformat()

        try:
            # Try parsing ISO format
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.isoformat()
        except Exception:
            # Return as-is if parsing fails
            return dt_str

    async def _detect_language(self, text: str) -> str:
        """
        Detect language of text

        Args:
            text: Input text

        Returns:
            ISO language code (e.g., 'en', 'es', 'fr')
        """
        try:
            from langdetect import detect

            # Use first 500 characters for detection
            sample = text[:500] if len(text) > 500 else text
            lang = detect(sample)
            return lang

        except ImportError:
            self.logger.debug("langdetect not installed, defaulting to 'en'")
            return "en"
        except Exception as e:
            self.logger.debug(f"Language detection failed: {e}, defaulting to 'en'")
            return "en"

    async def _extract_keywords(self, text: str, max_keywords: int = 10) -> list[str]:
        """
        Extract keywords from text using TF-IDF

        Args:
            text: Input text
            max_keywords: Maximum number of keywords to extract

        Returns:
            List of keywords
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            import numpy as np

            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=max_keywords,
                stop_words="english",
                ngram_range=(1, 2)
            )

            # Fit and transform
            tfidf_matrix = vectorizer.fit_transform([text])

            # Get feature names and scores
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]

            # Sort by score
            keyword_indices = np.argsort(scores)[::-1][:max_keywords]
            keywords = [feature_names[i] for i in keyword_indices if scores[i] > 0]

            return keywords

        except ImportError:
            # Fallback: simple word frequency
            words = text.lower().split()
            word_freq = {}
            for word in words:
                if len(word) > 4:  # Only words longer than 4 chars
                    word_freq[word] = word_freq.get(word, 0) + 1

            # Sort by frequency
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, _ in sorted_words[:max_keywords]]

        except Exception as e:
            self.logger.debug(f"Keyword extraction failed: {e}")
            return []

    async def _extract_entities(self, text: str) -> dict[str, list[str]]:
        """
        Extract named entities from text

        Args:
            text: Input text

        Returns:
            Dictionary of entity types and their values
        """
        # Simple regex-based entity extraction (fallback)
        entities = {
            "organizations": [],
            "locations": [],
            "people": []
        }

        try:
            # Look for capitalized phrases (potential proper nouns)
            capitalized_phrases = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)

            # Simple heuristics
            for phrase in capitalized_phrases[:20]:  # Limit to 20
                words = phrase.split()
                if len(words) >= 2:
                    # Multi-word capitalized = likely organization or person
                    if any(word in phrase for word in ["Inc", "Corp", "Ltd", "LLC", "University", "Institute"]):
                        if phrase not in entities["organizations"]:
                            entities["organizations"].append(phrase)
                    else:
                        if phrase not in entities["people"]:
                            entities["people"].append(phrase)

            return entities

        except Exception as e:
            self.logger.debug(f"Entity extraction failed: {e}")
            return entities

    async def _generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """
        Generate summary of text

        Args:
            text: Input text
            max_sentences: Maximum number of sentences in summary

        Returns:
            Summary text
        """
        try:
            # Simple extractive summary: first N sentences
            sentences = re.split(r"[.!?]+", text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

            # Take first max_sentences
            summary_sentences = sentences[:max_sentences]
            summary = ". ".join(summary_sentences)

            if summary and not summary.endswith("."):
                summary += "."

            return summary

        except Exception as e:
            self.logger.debug(f"Summary generation failed: {e}")
            # Return first 200 characters as fallback
            return text[:200] + "..." if len(text) > 200 else text
