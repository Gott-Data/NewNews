#!/usr/bin/env python
"""
FactCheckPipeline - Orchestrates the complete fact-checking workflow

Coordinates claim extraction, evidence gathering, verification, and bias detection
"""

from typing import Any
from pathlib import Path
import sys

_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.core.logging import get_logger
from src.agents.fact_checker import (
    ClaimExtractorAgent,
    EvidenceGatherAgent,
    VerificationAgent,
    CredibilityScoreAgent,
    BiasDetectorAgent
)


class FactCheckPipeline:
    """Complete fact-checking pipeline"""

    def __init__(self, config: dict[str, Any], api_key: str, base_url: str):
        """
        Initialize fact-checking pipeline

        Args:
            config: Complete configuration dictionary
            api_key: LLM API key
            base_url: LLM API endpoint
        """
        self.config = config
        self.logger = get_logger(name="fact_check_pipeline")

        # Initialize all agents
        self.claim_extractor = ClaimExtractorAgent(config, api_key, base_url)
        self.evidence_gatherer = EvidenceGatherAgent(config)
        self.verifier = VerificationAgent(config, api_key, base_url)
        self.credibility_scorer = CredibilityScoreAgent(config)
        self.bias_detector = BiasDetectorAgent(config)

        self.logger.info("FactCheckPipeline initialized")

    async def fact_check_article(
        self,
        article: dict[str, Any],
        preset: str = "quick",
        max_claims: int = 5,
        kb_name: str | None = None
    ) -> dict[str, Any]:
        """
        Perform complete fact-check on an article

        Args:
            article: Article dictionary
            preset: Fact-check preset (quick/thorough/deep)
            max_claims: Maximum claims to extract and verify
            kb_name: Knowledge base for RAG search

        Returns:
            Complete fact-check results
        """
        article_id = article.get("id")
        article_title = article.get("title", "")

        self.logger.info(f"Starting fact-check for article: {article_title[:50]}... (preset={preset})")

        result = {
            "article_id": article_id,
            "article_title": article_title,
            "preset": preset,
            "claims": [],
            "bias_analysis": {},
            "overall_credibility": 0.0,
            "summary": {}
        }

        # Step 1: Extract claims
        claims = await self.claim_extractor.extract_claims(article, max_claims)
        self.logger.info(f"Extracted {len(claims)} claims")

        if not claims:
            result["summary"] = {
                "message": "No verifiable claims found in article",
                "claims_checked": 0
            }
            return result

        # Step 2: Gather evidence and verify each claim
        verified_claims = []

        for claim in claims:
            # Gather evidence
            evidence_result = await self.evidence_gatherer.gather_evidence(
                claim=claim,
                preset=preset,
                kb_name=kb_name
            )

            evidence = evidence_result.get("evidence", [])

            # Verify claim
            verification = await self.verifier.verify_claim(claim, evidence)

            # Score credibility
            credibility = self.credibility_scorer.score_claim_verification(
                verification_result=verification,
                evidence=evidence
            )

            # Combine results
            verified_claim = {
                **claim,
                "verification": verification,
                "evidence": evidence,
                "credibility_score": credibility
            }

            verified_claims.append(verified_claim)

        result["claims"] = verified_claims

        # Step 3: Detect bias
        bias_analysis = await self.bias_detector.detect_bias(article)
        result["bias_analysis"] = bias_analysis

        # Step 4: Calculate overall credibility
        if verified_claims:
            avg_credibility = sum(c["credibility_score"] for c in verified_claims) / len(verified_claims)
            result["overall_credibility"] = round(avg_credibility, 2)

        # Step 5: Generate summary
        result["summary"] = self._generate_summary(verified_claims, bias_analysis)

        self.logger.info(f"Fact-check complete: {len(verified_claims)} claims verified")
        return result

    def _generate_summary(
        self,
        verified_claims: list[dict[str, Any]],
        bias_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate summary of fact-check results"""
        total_claims = len(verified_claims)

        if total_claims == 0:
            return {"message": "No claims verified"}

        # Count verdicts
        verdicts = {}
        for claim in verified_claims:
            verdict = claim["verification"].get("verdict", "unverifiable")
            verdicts[verdict] = verdicts.get(verdict, 0) + 1

        # Calculate percentages
        verdict_percentages = {
            verdict: round((count / total_claims) * 100, 1)
            for verdict, count in verdicts.items()
        }

        return {
            "claims_checked": total_claims,
            "verdicts": verdicts,
            "verdict_percentages": verdict_percentages,
            "bias_score": bias_analysis.get("overall_bias_score", 0.0),
            "political_lean": bias_analysis.get("political_lean", "neutral")
        }

    async def fact_check_batch(
        self,
        articles: list[dict[str, Any]],
        preset: str = "quick",
        max_claims_per_article: int = 3,
        kb_name: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Fact-check multiple articles

        Args:
            articles: List of articles
            preset: Fact-check preset
            max_claims_per_article: Max claims per article
            kb_name: Knowledge base name

        Returns:
            List of fact-check results
        """
        results = []

        for article in articles:
            result = await self.fact_check_article(
                article=article,
                preset=preset,
                max_claims=max_claims_per_article,
                kb_name=kb_name
            )
            results.append(result)

        self.logger.info(f"Batch fact-check complete: {len(results)} articles processed")
        return results
