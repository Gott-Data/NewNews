#!/usr/bin/env python
"""
EvidenceGatherAgent - Gathers evidence from multiple sources to verify claims

Uses RAG, web search, and paper search to find supporting/contradicting evidence
"""

from pathlib import Path
from typing import Any
import sys

# Add project root to path for core imports
_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.core.logging import get_logger
from src.tools.rag_tool import RAGTool
from src.tools.web_search import WebSearchTool
from src.tools.paper_search_tool import PaperSearchTool


class EvidenceGatherAgent:
    """Agent for gathering evidence from multiple sources"""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize evidence gather agent

        Args:
            config: Complete configuration dictionary
        """
        self.config = config
        self.fact_check_config = config.get("fact_check", {})
        self.logger = get_logger(name="evidence_gather_agent")

        # Initialize search tools
        try:
            self.rag_tool = RAGTool(config)
            self.logger.info("RAG tool initialized")
        except Exception as e:
            self.logger.warning(f"RAG tool initialization failed: {e}")
            self.rag_tool = None

        try:
            self.web_search_tool = WebSearchTool(config)
            self.logger.info("Web search tool initialized")
        except Exception as e:
            self.logger.warning(f"Web search tool initialization failed: {e}")
            self.web_search_tool = None

        try:
            self.paper_search_tool = PaperSearchTool(config)
            self.logger.info("Paper search tool initialized")
        except Exception as e:
            self.logger.warning(f"Paper search tool initialization failed: {e}")
            self.paper_search_tool = None

        self.logger.info("EvidenceGatherAgent initialized")

    async def gather_evidence(
        self,
        claim: dict[str, Any],
        preset: str = "quick",
        kb_name: str | None = None
    ) -> dict[str, Any]:
        """
        Gather evidence for a claim using multiple sources

        Args:
            claim: Claim dictionary with 'claim' text
            preset: Verification preset (quick, thorough, deep)
            kb_name: Knowledge base name for RAG search

        Returns:
            Evidence dictionary with sources
        """
        claim_text = claim.get("claim", "")

        if not claim_text:
            return {"evidence": [], "error": "No claim text provided"}

        # Get preset configuration
        preset_config = self.fact_check_config.get("presets", {}).get(preset, {})
        max_sources = preset_config.get("max_sources", 5)
        enable_rag = preset_config.get("enable_rag_search", True)
        enable_web = preset_config.get("enable_web_search", True)
        enable_paper = preset_config.get("enable_paper_search", False)

        self.logger.info(f"Gathering evidence for claim: '{claim_text[:50]}...' (preset={preset})")

        evidence_list = []

        # 1. RAG search (if enabled and tool available)
        if enable_rag and self.rag_tool and kb_name:
            rag_evidence = await self._search_rag(claim_text, kb_name, max_sources)
            evidence_list.extend(rag_evidence)

        # 2. Web search (if enabled and tool available)
        if enable_web and self.web_search_tool:
            web_evidence = await self._search_web(claim_text, max_sources)
            evidence_list.extend(web_evidence)

        # 3. Paper search (if enabled and tool available)
        if enable_paper and self.paper_search_tool:
            claim_type = claim.get("type", "")
            if claim_type in ["scientific", "statistical"]:  # Only search papers for scientific claims
                paper_evidence = await self._search_papers(claim_text, max_sources)
                evidence_list.extend(paper_evidence)

        # Sort by relevance and limit
        evidence_list.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        evidence_list = evidence_list[:max_sources]

        self.logger.info(f"Gathered {len(evidence_list)} evidence items for claim")

        return {
            "claim": claim_text,
            "evidence": evidence_list,
            "total_sources": len(evidence_list),
            "preset": preset
        }

    async def _search_rag(self, claim: str, kb_name: str, max_results: int) -> list[dict[str, Any]]:
        """
        Search knowledge base using RAG

        Args:
            claim: Claim text
            kb_name: Knowledge base name
            max_results: Maximum results

        Returns:
            List of evidence items
        """
        try:
            # Use RAG tool to search
            results = await self.rag_tool.search(
                query=claim,
                kb_name=kb_name,
                mode="hybrid",
                top_k=max_results
            )

            evidence = []
            for result in results:
                evidence.append({
                    "source": "rag",
                    "source_name": f"Knowledge Base: {kb_name}",
                    "content": result.get("content", ""),
                    "relevance": result.get("score", 0.5),
                    "metadata": result.get("metadata", {})
                })

            self.logger.info(f"RAG search found {len(evidence)} results")
            return evidence

        except Exception as e:
            self.logger.error(f"RAG search failed: {e}")
            return []

    async def _search_web(self, claim: str, max_results: int) -> list[dict[str, Any]]:
        """
        Search the web for information about the claim

        Args:
            claim: Claim text
            max_results: Maximum results

        Returns:
            List of evidence items
        """
        try:
            # Use web search tool
            result = await self.web_search_tool.search(claim)

            if not result or "error" in result:
                self.logger.warning(f"Web search returned no results: {result}")
                return []

            # Extract evidence from web search results
            evidence = []

            # Parse citations from web search
            content = result.get("content", "")
            citations = result.get("citations", [])

            for i, citation in enumerate(citations[:max_results]):
                evidence.append({
                    "source": "web",
                    "source_name": citation,
                    "content": content[i*200:(i+1)*200] if len(content) > i*200 else content[-200:],  # Extract relevant snippet
                    "url": citation,
                    "relevance": 0.8 - (i * 0.1),  # Decrease relevance with position
                    "metadata": {"position": i + 1}
                })

            self.logger.info(f"Web search found {len(evidence)} results")
            return evidence

        except Exception as e:
            self.logger.error(f"Web search failed: {e}")
            return []

    async def _search_papers(self, claim: str, max_results: int) -> list[dict[str, Any]]:
        """
        Search academic papers for scientific claims

        Args:
            claim: Claim text
            max_results: Maximum results

        Returns:
            List of evidence items
        """
        try:
            # Use paper search tool
            papers = await self.paper_search_tool.search(
                query=claim,
                max_results=max_results
            )

            evidence = []
            for paper in papers:
                evidence.append({
                    "source": "paper",
                    "source_name": f"ArXiv: {paper.get('title', 'Unknown')}",
                    "content": paper.get("abstract", ""),
                    "url": paper.get("url", ""),
                    "relevance": paper.get("relevance", 0.7),
                    "metadata": {
                        "authors": paper.get("authors", []),
                        "published": paper.get("published", ""),
                        "categories": paper.get("categories", [])
                    }
                })

            self.logger.info(f"Paper search found {len(evidence)} results")
            return evidence

        except Exception as e:
            self.logger.error(f"Paper search failed: {e}")
            return []

    async def gather_batch(
        self,
        claims: list[dict[str, Any]],
        preset: str = "quick",
        kb_name: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Gather evidence for multiple claims

        Args:
            claims: List of claim dictionaries
            preset: Verification preset
            kb_name: Knowledge base name

        Returns:
            List of evidence results
        """
        results = []

        for claim in claims:
            evidence = await self.gather_evidence(claim, preset, kb_name)
            results.append(evidence)

        self.logger.info(f"Gathered evidence for {len(results)} claims")
        return results

    def is_available(self) -> dict[str, bool]:
        """
        Check which search tools are available

        Returns:
            Dictionary of tool availability
        """
        return {
            "rag": self.rag_tool is not None,
            "web": self.web_search_tool is not None,
            "paper": self.paper_search_tool is not None
        }
