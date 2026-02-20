#!/usr/bin/env python
"""
VerificationAgent - Analyzes evidence to determine claim truthfulness

Evaluates gathered evidence and assigns verdict (true/false/misleading/unverifiable)
"""

from pathlib import Path
from typing import Any
import json
import sys

_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.core.core import get_agent_params
from src.core.logging import get_logger


class VerificationAgent:
    """Agent for verifying claims based on evidence"""

    def __init__(self, config: dict[str, Any], api_key: str, base_url: str):
        """Initialize verification agent"""
        self.config = config
        self.api_key = api_key
        self.base_url = base_url
        self.logger = get_logger(name="verification_agent")
        self._agent_params = get_agent_params("fact_checker")
        self.logger.info("VerificationAgent initialized")

    async def verify_claim(
        self,
        claim: dict[str, Any],
        evidence: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Verify a claim based on gathered evidence

        Args:
            claim: Claim dictionary
            evidence: List of evidence items

        Returns:
            Verification result with verdict and confidence
        """
        try:
            if not evidence:
                return {
                    "claim": claim.get("claim"),
                    "verdict": "unverifiable",
                    "confidence": 0.0,
                    "reasoning": "No evidence found to verify this claim",
                    "evidence_count": 0
                }

            # Use LLM to analyze evidence and determine verdict
            result = await self._verify_with_llm(claim, evidence)

            result["evidence_count"] = len(evidence)
            return result

        except Exception as e:
            self.logger.error(f"Verification failed: {e}")
            return {
                "claim": claim.get("claim"),
                "verdict": "error",
                "confidence": 0.0,
                "reasoning": f"Verification error: {str(e)}",
                "evidence_count": len(evidence)
            }

    async def _verify_with_llm(
        self,
        claim: dict[str, Any],
        evidence: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Use LLM to verify claim against evidence"""
        try:
            from lightrag.llm.openai import openai_complete_if_cache
            import os

            claim_text = claim.get("claim", "")

            # Build evidence summary
            evidence_text = "\n\n".join([
                f"Source {i+1} ({ev.get('source_name', 'Unknown')}):\n{ev.get('content', '')[:500]}"
                for i, ev in enumerate(evidence[:10])  # Limit to 10 sources
            ])

            system_prompt = """You are a fact-checking expert who analyzes evidence to verify claims.

Your task is to:
1. Analyze the provided evidence
2. Determine if the claim is TRUE, FALSE, MISLEADING, or UNVERIFIABLE
3. Provide a confidence score (0.0 to 1.0)
4. Explain your reasoning

Verdict definitions:
- TRUE: Evidence strongly supports the claim
- FALSE: Evidence contradicts the claim
- MISLEADING: Claim is partially true but missing important context
- UNVERIFIABLE: Insufficient or conflicting evidence

Output as JSON."""

            user_prompt = f"""Claim to verify:
"{claim_text}"

Evidence gathered:
{evidence_text}

Analyze the evidence and determine the verdict.

Output format (JSON):
{{
  "verdict": "true|false|misleading|unverifiable",
  "confidence": 0.0-1.0,
  "reasoning": "Detailed explanation of your verdict",
  "supporting_sources": ["list", "of", "supporting", "sources"],
  "contradicting_sources": ["list", "of", "contradicting", "sources"]
}}"""

            response = await openai_complete_if_cache(
                model=os.getenv("LLM_MODEL"),
                prompt=user_prompt,
                system_prompt=system_prompt,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=self._agent_params["temperature"],
                max_tokens=self._agent_params["max_tokens"],
                response_format={"type": "json_object"}
            )

            result = json.loads(response)
            result["claim"] = claim_text

            return result

        except Exception as e:
            self.logger.error(f"LLM verification failed: {e}")
            # Fallback to simple heuristic
            return self._verify_heuristic(claim, evidence)

    def _verify_heuristic(
        self,
        claim: dict[str, Any],
        evidence: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Fallback heuristic verification"""
        claim_text = claim.get("claim", "")

        # Simple keyword matching heuristic
        supporting = 0
        contradicting = 0

        for ev in evidence:
            content = ev.get("content", "").lower()
            if any(word in content for word in ["confirm", "support", "verify", "true", "accurate"]):
                supporting += 1
            if any(word in content for word in ["false", "incorrect", "misleading", "debunk", "deny"]):
                contradicting += 1

        total = supporting + contradicting

        if total == 0:
            verdict = "unverifiable"
            confidence = 0.0
        elif supporting > contradicting * 2:
            verdict = "true"
            confidence = min(0.9, supporting / total)
        elif contradicting > supporting * 2:
            verdict = "false"
            confidence = min(0.9, contradicting / total)
        else:
            verdict = "misleading"
            confidence = 0.5

        return {
            "claim": claim_text,
            "verdict": verdict,
            "confidence": round(confidence, 2),
            "reasoning": f"Based on {supporting} supporting and {contradicting} contradicting sources",
            "supporting_sources": [],
            "contradicting_sources": []
        }
