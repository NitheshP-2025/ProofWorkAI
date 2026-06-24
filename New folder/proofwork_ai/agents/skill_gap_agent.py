"""
ProofWork AI - Skill Gap Intelligence Agent
============================================
Agent 2: Identifies missing high-demand skills and generates a personalized
career acceleration roadmap with AI-powered XAI explanations.

Architecture:
  ┌────────────────┐    ┌────────────────┐    ┌────────────────────┐
  │  SkillGapInput │───▶│ RoadmapGenerator│───▶│    GroqService     │
  └────────────────┘    └────────────────┘    └────────────────────┘
           │                     │                      │
           └─────────────────────┴──────────────────────┘
                                 ▼
                         SkillGapResult (XAI)

Flow:
  1. Load market data from market_data.json.
  2. Compute skill gaps deterministically (no AI needed for this step).
  3. Use AI to generate personalized roadmap and career narrative.
  4. Merge AI output with deterministic gap data into SkillGapResult.

Author: Swetha
Module: agents/skill_gap_agent.py
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from models.schemas import SkillGapInput, SkillGapResult, SkillGapItem, RoadmapWeek, APIResponse
from services.groq_service import GroqService
from utils.prompts import get_skill_gap_prompts
from utils.roadmap_generator import identify_skill_gaps, generate_roadmap
from utils.logger import get_logger

logger = get_logger(__name__)

# Default market data file path
MARKET_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "market_data.json"

# Number of top skill gaps to analyze
TOP_N_GAPS = 3


class SkillGapAgent:
    """
    Agent 2 — Skill Gap Intelligence Agent for ProofWork AI.

    Identifies career-critical skill gaps and generates personalized,
    AI-powered, XAI-compliant learning roadmaps.

    Attributes:
        groq_service: The AI API client.
        market_data_path: Path to the market demand JSON file.

    Example:
        agent = SkillGapAgent(groq_service=GroqService())
        result = agent.analyze(SkillGapInput(user_skills=["Python", "Flask", "SQL"]))
    """

    def __init__(
        self,
        groq_service: Optional[GroqService] = None,
        market_data_path: Optional[Path] = None,
    ) -> None:
        """
        Initializes the Skill Gap Agent.

        Args:
            groq_service: Configured GroqService. Creates default if None.
            market_data_path: Path to market_data.json. Uses default data dir if None.
        """
        self._groq = groq_service or GroqService()
        self._market_data_path = market_data_path or MARKET_DATA_PATH
        self._market_data: Dict[str, float] = {}
        self._load_market_data()
        logger.info("SkillGapAgent initialized.")

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def analyze(self, gap_input: SkillGapInput) -> APIResponse:
        """
        Performs a full skill gap analysis with AI-generated roadmap.

        Args:
            gap_input: Validated SkillGapInput containing user's current skills.

        Returns:
            APIResponse:
              - success=True  → data contains SkillGapResult dict
              - success=False → error contains description
        """
        agent_name = "SkillGapAgent"
        start_ms = time.monotonic() * 1000

        logger.info(
            f"[{agent_name}] Starting analysis | "
            f"user_id={gap_input.user_id} | "
            f"skills={gap_input.user_skills}"
        )

        # Step 1: Validate input
        validation_errors = gap_input.validate()
        if validation_errors:
            error_msg = "; ".join(validation_errors)
            logger.warning(f"[{agent_name}] Validation failed: {error_msg}")
            return APIResponse(
                success=False,
                error=f"Input validation failed: {error_msg}",
                agent=agent_name,
                duration_ms=time.monotonic() * 1000 - start_ms,
            )

        # Step 2: Identify skill gaps (deterministic)
        try:
            skill_gaps: List[SkillGapItem] = identify_skill_gaps(
                user_skills=gap_input.user_skills,
                market_data=self._market_data,
                top_n=TOP_N_GAPS,
            )

            if not skill_gaps:
                logger.info(f"[{agent_name}] No skill gaps detected — user has all top market skills.")
                # Return a result indicating full alignment
                result = SkillGapResult(
                    user_id=gap_input.user_id,
                    existing_skills=gap_input.user_skills,
                    skill_gaps=[],
                    roadmap=[],
                    career_impact_summary=(
                        "Excellent! Your current skill set aligns well with "
                        "current market demand. Focus on deepening expertise "
                        "and building a strong project portfolio."
                    ),
                    ai_reasoning=[
                        "User's skills cover the highest-demand areas.",
                        "No significant gaps detected against current market data.",
                        "Recommendation: Focus on specialization and portfolio quality.",
                    ],
                )
                return APIResponse(
                    success=True,
                    data=result.to_dict(),
                    agent=agent_name,
                    duration_ms=time.monotonic() * 1000 - start_ms,
                )

            logger.info(
                f"[{agent_name}] Identified {len(skill_gaps)} skill gaps: "
                f"{[g.skill for g in skill_gaps]}"
            )
        except Exception as exc:
            logger.exception(f"[{agent_name}] Skill gap identification failed: {exc}")
            return APIResponse(
                success=False,
                error=f"Gap identification error: {exc}",
                agent=agent_name,
                duration_ms=time.monotonic() * 1000 - start_ms,
            )

        # Step 3: Generate deterministic roadmap (fallback baseline)
        deterministic_roadmap: List[RoadmapWeek] = generate_roadmap(skill_gaps)

        # Step 4: Get AI-enhanced roadmap and narrative
        ai_roadmap: List[RoadmapWeek] = deterministic_roadmap
        ai_reasoning: List[str] = [g.xai_reason for g in skill_gaps]
        career_impact_summary: str = self._build_impact_summary(skill_gaps)

        try:
            system_prompt, user_prompt = get_skill_gap_prompts(
                existing_skills=gap_input.user_skills,
                skill_gaps=[g.to_dict() for g in skill_gaps],
                market_data=self._market_data,
                target_role=gap_input.target_role,
            )

            ai_response_dict, _ = self._groq.chat_json(system_prompt, user_prompt)

            # Parse AI-enhanced roadmap
            ai_roadmap = self._parse_roadmap(ai_response_dict) or deterministic_roadmap
            ai_reasoning = ai_response_dict.get("ai_reasoning", ai_reasoning)
            career_impact_summary = ai_response_dict.get(
                "career_impact_summary", career_impact_summary
            )

            logger.info(f"[{agent_name}] AI roadmap and narrative generated successfully.")

        except (ValueError, RuntimeError, EnvironmentError) as exc:
            logger.warning(
                f"[{agent_name}] AI roadmap generation failed; using deterministic fallback. "
                f"Error: {exc}"
            )
            # Continue with deterministic roadmap — do NOT fail the response

        except Exception as exc:
            logger.warning(
                f"[{agent_name}] Unexpected AI error; using deterministic fallback. Error: {exc}"
            )

        # Step 5: Assemble final result
        result = SkillGapResult(
            user_id=gap_input.user_id,
            existing_skills=gap_input.user_skills,
            skill_gaps=skill_gaps,
            roadmap=ai_roadmap,
            career_impact_summary=career_impact_summary,
            ai_reasoning=ai_reasoning,
        )

        duration = time.monotonic() * 1000 - start_ms
        logger.info(
            f"[{agent_name}] Analysis complete | "
            f"gaps={len(skill_gaps)} | duration={duration:.0f}ms"
        )

        return APIResponse(
            success=True,
            data=result.to_dict(),
            agent=agent_name,
            duration_ms=duration,
        )

    def analyze_from_dict(self, data: dict) -> APIResponse:
        """
        Convenience method — parses a dict and runs analyze().

        Args:
            data: Dict with 'user_skills' (list), optionally 'user_id' and 'target_role'.

        Returns:
            APIResponse.
        """
        try:
            gap_input = SkillGapInput.from_dict(data)
        except (KeyError, TypeError) as exc:
            logger.error(f"SkillGapAgent: Failed to parse input dict: {exc}")
            return APIResponse(
                success=False,
                error=f"Invalid input format: {exc}",
                agent="SkillGapAgent",
            )
        return self.analyze(gap_input)

    def get_market_data(self) -> Dict[str, float]:
        """Returns the loaded market data (read-only view)."""
        return dict(self._market_data)

    # -----------------------------------------------------------------------
    # Private Helpers
    # -----------------------------------------------------------------------

    def _load_market_data(self) -> None:
        """Loads and caches market demand data from JSON file."""
        try:
            with open(self._market_data_path, "r", encoding="utf-8") as f:
                self._market_data = json.load(f)
            logger.info(
                f"Market data loaded: {len(self._market_data)} skills "
                f"from {self._market_data_path}"
            )
        except FileNotFoundError:
            logger.error(f"market_data.json not found at {self._market_data_path}")
            self._market_data = {}
        except json.JSONDecodeError as exc:
            logger.error(f"market_data.json is invalid JSON: {exc}")
            self._market_data = {}

    def _parse_roadmap(self, ai_response: Dict[str, Any]) -> Optional[List[RoadmapWeek]]:
        """
        Parses roadmap entries from the AI response dict.

        Args:
            ai_response: Parsed JSON dict from Groq.

        Returns:
            List of RoadmapWeek or None if parsing fails.
        """
        raw = ai_response.get("roadmap")
        if not isinstance(raw, list) or not raw:
            return None

        roadmap = []
        for entry in raw:
            try:
                roadmap.append(
                    RoadmapWeek(
                        week_range=entry.get("week_range", ""),
                        skill=entry.get("skill", ""),
                        focus=entry.get("focus", ""),
                        resources=entry.get("resources", []),
                        milestone=entry.get("milestone", ""),
                    )
                )
            except (TypeError, AttributeError) as exc:
                logger.warning(f"Skipping malformed roadmap entry: {exc}")
                continue

        return roadmap if roadmap else None

    @staticmethod
    def _build_impact_summary(skill_gaps: List[SkillGapItem]) -> str:
        """
        Builds a deterministic career impact summary.

        Args:
            skill_gaps: Ranked skill gap list.

        Returns:
            Multi-sentence impact summary string.
        """
        if not skill_gaps:
            return "Your skill set is well-aligned with market demand."

        top_skills = [g.skill for g in skill_gaps[:3]]
        max_opportunity = max(g.opportunity_increase_pct for g in skill_gaps)
        avg_demand = sum(g.market_demand_score for g in skill_gaps) / len(skill_gaps)

        if len(top_skills) == 1:
            skills_str = top_skills[0]
        else:
            skills_str = ", ".join(top_skills[:-1]) + f" and {top_skills[-1]}"

        return (
            f"Mastering {skills_str} could unlock up to +{max_opportunity:.0f}% more job opportunities. "
            f"These skills have an average market demand score of {avg_demand:.0f}/100, "
            f"making them critical investments for your freelance career in 2026."
        )
