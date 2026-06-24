"""
ProofWork AI - Skill Verification Agent
=========================================
Agent 1: Verifies whether a freelancer actually possesses a claimed skill
by analyzing their challenge submission using AI and explainable scoring.

Architecture:
  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
  │SkillSubmission│────▶│  GroqService │────▶│ EvaluationEngine │
  └──────────────┘     └──────────────┘     └──────────────────┘
                                                     │
                                                     ▼
                                          VerificationResult (XAI)

Design Principles:
  - Single Responsibility: This agent orchestrates only.
  - Dependency Injection: Services passed at construction.
  - Full error propagation with structured logging.
  - Timing instrumentation for production observability.

Author: Swetha
Module: agents/skill_verifier.py
"""

import time
from typing import Optional

from models.schemas import SkillSubmission, VerificationResult, APIResponse
from services.groq_service import GroqService
from services.evaluation_engine import EvaluationEngine
from utils.prompts import get_skill_verifier_prompts
from utils.logger import get_logger

logger = get_logger(__name__)


class SkillVerificationAgent:
    """
    Agent 1 — Skill Verification Agent for ProofWork AI.

    Orchestrates the full skill verification pipeline:
    1. Validates submission input.
    2. Builds AI prompts.
    3. Calls Groq API via GroqService.
    4. Converts AI response to VerificationResult via EvaluationEngine.
    5. Returns typed result with full XAI explanation.

    Example:
        agent = SkillVerificationAgent(
            groq_service=GroqService(),
            evaluation_engine=EvaluationEngine(),
        )
        result = agent.verify(submission)
    """

    def __init__(
        self,
        groq_service: Optional[GroqService] = None,
        evaluation_engine: Optional[EvaluationEngine] = None,
    ) -> None:
        """
        Initializes the Skill Verification Agent.

        Args:
            groq_service: Configured GroqService instance.
                          If None, creates one with default settings.
            evaluation_engine: EvaluationEngine instance.
                               If None, creates one with defaults.
        """
        self._groq = groq_service or GroqService()
        self._engine = evaluation_engine or EvaluationEngine()
        logger.info("SkillVerificationAgent initialized.")

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def verify(self, submission: SkillSubmission) -> APIResponse:
        """
        Verifies a skill submission and returns a structured APIResponse.

        Args:
            submission: A fully populated SkillSubmission object.

        Returns:
            APIResponse with:
              - success=True  → data contains VerificationResult dict
              - success=False → error contains description
        """
        agent_name = "SkillVerificationAgent"
        start_ms = time.monotonic() * 1000

        logger.info(
            f"[{agent_name}] Starting verification | "
            f"user_id={submission.user_id} | skill={submission.skill}"
        )

        # Step 1: Input Validation
        validation_errors = submission.validate()
        if validation_errors:
            error_msg = "; ".join(validation_errors)
            logger.warning(f"[{agent_name}] Validation failed: {error_msg}")
            return APIResponse(
                success=False,
                error=f"Input validation failed: {error_msg}",
                agent=agent_name,
                duration_ms=time.monotonic() * 1000 - start_ms,
            )

        # Step 2: Build prompts
        try:
            system_prompt, user_prompt = get_skill_verifier_prompts(
                skill=submission.skill,
                challenge_title=submission.challenge_title,
                submission_text=submission.submission_text,
                submission_time=submission.submission_time,
            )
            logger.debug(f"[{agent_name}] Prompts built successfully.")
        except Exception as exc:
            logger.exception(f"[{agent_name}] Prompt construction failed: {exc}")
            return APIResponse(
                success=False,
                error=f"Prompt construction error: {exc}",
                agent=agent_name,
                duration_ms=time.monotonic() * 1000 - start_ms,
            )

        # Step 3: Call Groq API
        try:
            ai_response_dict, raw_text = self._groq.chat_json(system_prompt, user_prompt)
            logger.info(f"[{agent_name}] AI response received successfully.")
        except (ValueError, RuntimeError, EnvironmentError) as exc:
            logger.error(f"[{agent_name}] Groq API call failed: {exc}")
            return APIResponse(
                success=False,
                error=f"AI service error: {exc}",
                agent=agent_name,
                duration_ms=time.monotonic() * 1000 - start_ms,
            )
        except Exception as exc:
            logger.exception(f"[{agent_name}] Unexpected error during AI call: {exc}")
            return APIResponse(
                success=False,
                error=f"Unexpected error: {exc}",
                agent=agent_name,
                duration_ms=time.monotonic() * 1000 - start_ms,
            )

        # Step 4: Evaluate
        try:
            result: VerificationResult = self._engine.evaluate(
                user_id=submission.user_id,
                skill=submission.skill,
                ai_response=ai_response_dict,
                raw_ai_text=raw_text,
            )
        except Exception as exc:
            logger.exception(f"[{agent_name}] Evaluation engine failed: {exc}")
            return APIResponse(
                success=False,
                error=f"Evaluation error: {exc}",
                agent=agent_name,
                duration_ms=time.monotonic() * 1000 - start_ms,
            )

        duration = time.monotonic() * 1000 - start_ms
        logger.info(
            f"[{agent_name}] Verification complete | "
            f"status={result.status} | score={result.overall_score} | "
            f"duration={duration:.0f}ms"
        )

        return APIResponse(
            success=True,
            data=result.to_dict(),
            agent=agent_name,
            duration_ms=duration,
        )

    def verify_from_dict(self, data: dict) -> APIResponse:
        """
        Convenience method — accepts a raw dict and validates into SkillSubmission.

        Args:
            data: Dictionary with submission fields.

        Returns:
            APIResponse (same as verify()).
        """
        try:
            submission = SkillSubmission.from_dict(data)
        except (KeyError, TypeError) as exc:
            logger.error(f"SkillVerificationAgent: Failed to parse input dict: {exc}")
            return APIResponse(
                success=False,
                error=f"Invalid submission format: {exc}",
                agent="SkillVerificationAgent",
            )
        return self.verify(submission)
