"""
ProofWork AI - Data Schemas & Models
=====================================
Defines all core data structures used across the ProofWork AI platform.
Uses Python dataclasses for clean, typed, production-ready models.

Author: Swetha
Module: models/schemas.py
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import json


def _utcnow_iso() -> str:
    """Returns current UTC time as ISO string (timezone-aware, deprecation-safe)."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Skill Verification Models
# ---------------------------------------------------------------------------

@dataclass
class SkillSubmission:
    """
    Represents a freelancer's skill challenge submission.

    Attributes:
        user_id: Unique identifier for the freelancer.
        skill: The claimed skill being verified.
        challenge_title: The title of the challenge assigned.
        submission_text: The actual code or explanation submitted.
        submission_time: ISO timestamp of submission.
    """
    user_id: str
    skill: str
    challenge_title: str
    submission_text: str
    submission_time: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillSubmission":
        return cls(
            user_id=data["user_id"],
            skill=data["skill"],
            challenge_title=data["challenge_title"],
            submission_text=data["submission_text"],
            submission_time=data.get("submission_time", _utcnow_iso()),
        )

    def validate(self) -> List[str]:
        """Returns list of validation errors. Empty list means valid."""
        errors = []
        if not self.user_id or not self.user_id.strip():
            errors.append("user_id cannot be empty.")
        if not self.skill or not self.skill.strip():
            errors.append("skill cannot be empty.")
        if not self.challenge_title or not self.challenge_title.strip():
            errors.append("challenge_title cannot be empty.")
        if not self.submission_text or len(self.submission_text.strip()) < 10:
            errors.append("submission_text must be at least 10 characters.")
        return errors


@dataclass
class ComponentScores:
    """
    Breakdown of individual AI-evaluated score components.

    Each component is scored on a 0–100 scale by the AI model.
    """
    code_quality: float = 0.0
    documentation: float = 0.0
    security: float = 0.0
    problem_solving: float = 0.0

    def compute_overall(self) -> float:
        """
        Computes weighted overall score.
        Weights: code_quality=0.30, documentation=0.20, security=0.20, problem_solving=0.30
        """
        return round(
            (self.code_quality * 0.30)
            + (self.documentation * 0.20)
            + (self.security * 0.20)
            + (self.problem_solving * 0.30),
            2,
        )

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class VerificationResult:
    """
    Full verification result for a skill submission.

    Attributes:
        user_id: The freelancer's ID.
        skill: Skill being verified.
        overall_score: Final weighted score (0–100).
        status: VERIFIED | PARTIALLY VERIFIED | NOT VERIFIED
        component_scores: Breakdown of scores by dimension.
        reasoning: XAI reasoning list explaining each decision.
        strengths: Detected strengths in the submission.
        improvements: Suggested improvements for the freelancer.
        ai_raw_response: Raw model response for transparency.
        verified_at: Timestamp of verification.
    """
    user_id: str
    skill: str
    overall_score: float
    status: str
    component_scores: ComponentScores
    reasoning: List[str]
    strengths: List[str]
    improvements: List[str]
    ai_raw_response: str = ""
    verified_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["component_scores"] = self.component_scores.to_dict()
        return result

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# ---------------------------------------------------------------------------
# Skill Gap Models
# ---------------------------------------------------------------------------

@dataclass
class SkillGapInput:
    """
    Input model for the Skill Gap Intelligence Agent.

    Attributes:
        user_id: Optional user identifier for tracking.
        user_skills: List of skills the freelancer currently has.
        target_role: Optional target job role for focused gap analysis.
    """
    user_skills: List[str]
    user_id: Optional[str] = None
    target_role: Optional[str] = None

    def validate(self) -> List[str]:
        errors = []
        if not self.user_skills:
            errors.append("user_skills list cannot be empty.")
        if len(self.user_skills) > 50:
            errors.append("user_skills list cannot exceed 50 items.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillGapInput":
        return cls(
            user_skills=data.get("user_skills", []),
            user_id=data.get("user_id"),
            target_role=data.get("target_role"),
        )


@dataclass
class SkillGapItem:
    """
    A single identified skill gap with enriched metadata.

    Attributes:
        skill: Name of the missing skill.
        market_demand_score: Raw demand score (0–100) from market_data.json.
        opportunity_increase_pct: Estimated % increase in job opportunities.
        priority_rank: Rank among all gaps (1 = highest priority).
        xai_reason: Explainable reason for recommending this skill.
    """
    skill: str
    market_demand_score: float
    opportunity_increase_pct: float
    priority_rank: int
    xai_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RoadmapWeek:
    """Represents a two-week block in the learning roadmap."""
    week_range: str          # e.g., "Week 1-2"
    skill: str               # e.g., "Docker"
    focus: str               # e.g., "Docker Fundamentals"
    resources: List[str]     # Suggested resources / topics
    milestone: str           # What the learner should be able to do

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SkillGapResult:
    """
    Complete result from the Skill Gap Intelligence Agent.

    Attributes:
        user_id: Freelancer identifier.
        existing_skills: Skills the user already has.
        skill_gaps: Top ranked skill gap items.
        roadmap: Week-by-week learning roadmap.
        career_impact_summary: Overall narrative impact statement.
        ai_reasoning: XAI reasoning for all recommendations.
        generated_at: Timestamp.
    """
    user_id: Optional[str]
    existing_skills: List[str]
    skill_gaps: List[SkillGapItem]
    roadmap: List[RoadmapWeek]
    career_impact_summary: str
    ai_reasoning: List[str]
    generated_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "existing_skills": self.existing_skills,
            "skill_gaps": [g.to_dict() for g in self.skill_gaps],
            "roadmap": [r.to_dict() for r in self.roadmap],
            "career_impact_summary": self.career_impact_summary,
            "ai_reasoning": self.ai_reasoning,
            "generated_at": self.generated_at,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# ---------------------------------------------------------------------------
# Platform-wide Response Wrapper
# ---------------------------------------------------------------------------

@dataclass
class APIResponse:
    """
    Standardized API response wrapper for all agent outputs.

    Attributes:
        success: Whether the operation succeeded.
        data: The result payload (dict).
        error: Error message if not successful.
        agent: Which agent produced the result.
        duration_ms: Processing time in milliseconds.
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    agent: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
