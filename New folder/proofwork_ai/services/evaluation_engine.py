"""
ProofWork AI - Evaluation Engine
==================================
Stateless service that processes raw AI scores into verified VerificationResult models.

Responsibilities:
  - Parse and validate component scores from AI JSON responses.
  - Compute overall weighted score using defined formula.
  - Apply verification status thresholds.
  - Combine AI reasoning with deterministic metadata.
  - Produce complete, XAI-compliant VerificationResult.

Author: Swetha
Module: services/evaluation_engine.py
"""

from typing import Any, Dict, List
from models.schemas import ComponentScores, VerificationResult
from utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Verification Thresholds
# ---------------------------------------------------------------------------

THRESHOLD_VERIFIED = 80.0
THRESHOLD_PARTIAL = 60.0

STATUS_VERIFIED = "VERIFIED"
STATUS_PARTIAL = "PARTIALLY VERIFIED"
STATUS_NOT_VERIFIED = "NOT VERIFIED"

# Status badge colors for UI (referenced in app.py)
STATUS_COLORS = {
    STATUS_VERIFIED: "#00C851",
    STATUS_PARTIAL: "#FFBB33",
    STATUS_NOT_VERIFIED: "#FF4444",
}

STATUS_ICONS = {
    STATUS_VERIFIED: "✅",
    STATUS_PARTIAL: "⚠️",
    STATUS_NOT_VERIFIED: "❌",
}

# Score floor/ceiling for safety
SCORE_MIN = 0.0
SCORE_MAX = 100.0


# ---------------------------------------------------------------------------
# EvaluationEngine
# ---------------------------------------------------------------------------

class EvaluationEngine:
    """
    Converts raw AI analysis (JSON dict) into a structured VerificationResult.

    This engine is purely deterministic and stateless — it performs no I/O.
    All scoring logic follows the documented formula:
        overall = code_quality*0.30 + documentation*0.20 + security*0.20 + problem_solving*0.30
    """

    def evaluate(
        self,
        user_id: str,
        skill: str,
        ai_response: Dict[str, Any],
        raw_ai_text: str,
    ) -> VerificationResult:
        """
        Processes an AI response dict and produces a VerificationResult.

        Args:
            user_id: The freelancer's ID.
            skill: The skill being verified.
            ai_response: Parsed JSON dict from Groq.
            raw_ai_text: The original raw model response string.

        Returns:
            A fully populated VerificationResult.

        Raises:
            ValueError: If required keys are missing from ai_response.
        """
        logger.info(f"Evaluating submission | user_id={user_id} | skill={skill}")

        component_scores = self._parse_component_scores(ai_response)
        overall_score = component_scores.compute_overall()
        status = self._determine_status(overall_score)

        reasoning = self._extract_list(ai_response, "reasoning", default=[
            "AI reasoning not available.",
        ])
        strengths = self._extract_list(ai_response, "strengths", default=[
            "Strengths not specified.",
        ])
        improvements = self._extract_list(ai_response, "improvements", default=[
            "Improvements not specified.",
        ])

        # Append deterministic scoring summary to reasoning
        scoring_explanation = self._build_scoring_explanation(component_scores, overall_score, status)
        reasoning.insert(0, scoring_explanation)

        result = VerificationResult(
            user_id=user_id,
            skill=skill,
            overall_score=overall_score,
            status=status,
            component_scores=component_scores,
            reasoning=reasoning,
            strengths=strengths,
            improvements=improvements,
            ai_raw_response=raw_ai_text,
        )

        logger.info(
            f"Evaluation complete | user_id={user_id} | "
            f"overall={overall_score:.1f} | status={status}"
        )
        return result

    # -----------------------------------------------------------------------
    # Private Helpers
    # -----------------------------------------------------------------------

    def _parse_component_scores(self, ai_response: Dict[str, Any]) -> ComponentScores:
        """
        Extracts and validates component scores from the AI response.

        Args:
            ai_response: Dict containing 'component_scores' key.

        Returns:
            ComponentScores instance with clamped values.

        Raises:
            ValueError: If 'component_scores' key is missing.
        """
        raw_scores = ai_response.get("component_scores")
        if not raw_scores or not isinstance(raw_scores, dict):
            logger.warning("'component_scores' missing or malformed in AI response. Using zeros.")
            raw_scores = {}

        return ComponentScores(
            code_quality=self._clamp_score(raw_scores.get("code_quality", 0)),
            documentation=self._clamp_score(raw_scores.get("documentation", 0)),
            security=self._clamp_score(raw_scores.get("security", 0)),
            problem_solving=self._clamp_score(raw_scores.get("problem_solving", 0)),
        )

    def _determine_status(self, overall_score: float) -> str:
        """
        Applies verification threshold rules to determine status.

        Rules:
            >= 80  → VERIFIED
            >= 60  → PARTIALLY VERIFIED
            < 60   → NOT VERIFIED

        Args:
            overall_score: Computed weighted score.

        Returns:
            Status string.
        """
        if overall_score >= THRESHOLD_VERIFIED:
            return STATUS_VERIFIED
        elif overall_score >= THRESHOLD_PARTIAL:
            return STATUS_PARTIAL
        else:
            return STATUS_NOT_VERIFIED

    def _build_scoring_explanation(
        self,
        scores: ComponentScores,
        overall: float,
        status: str,
    ) -> str:
        """
        Generates a human-readable scoring summary for XAI transparency.

        Args:
            scores: Component scores.
            overall: Weighted overall score.
            status: Verification status.

        Returns:
            Single-sentence scoring summary.
        """
        return (
            f"Weighted score calculated: Code Quality ({scores.code_quality:.0f}×0.30) + "
            f"Documentation ({scores.documentation:.0f}×0.20) + "
            f"Security ({scores.security:.0f}×0.20) + "
            f"Problem Solving ({scores.problem_solving:.0f}×0.30) = "
            f"{overall:.1f}/100 → Status: {status}"
        )

    @staticmethod
    def _clamp_score(value: Any) -> float:
        """
        Safely clamps a score value to [SCORE_MIN, SCORE_MAX].

        Args:
            value: Raw score (any type from JSON parsing).

        Returns:
            Float in range [0.0, 100.0].
        """
        try:
            num = float(value)
        except (TypeError, ValueError):
            logger.warning(f"Invalid score value '{value}' — defaulting to 0.")
            return SCORE_MIN
        return max(SCORE_MIN, min(SCORE_MAX, num))

    @staticmethod
    def _extract_list(
        data: Dict[str, Any],
        key: str,
        default: List[str],
    ) -> List[str]:
        """
        Safely extracts a list field from the AI response.

        Args:
            data: The parsed AI response dict.
            key: Key to extract.
            default: Fallback list if key is missing or malformed.

        Returns:
            List of strings.
        """
        value = data.get(key)
        if isinstance(value, list) and all(isinstance(v, str) for v in value):
            # Return a copy so callers cannot mutate the AI response list
            return list(value)
        logger.warning(f"Field '{key}' missing or non-string list in AI response. Using default.")
        # Return a copy of default to prevent mutable aliasing across calls
        return list(default)
