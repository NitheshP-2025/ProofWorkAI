"""
ProofWork AI - Test Suite: Skill Gap Intelligence Agent
========================================================
Comprehensive pytest test coverage for:
  - SkillGapInput validation
  - Roadmap generator logic
  - SkillGapAgent orchestration
  - Career impact calculation
  - Error handling paths

Author: Swetha
"""

import json
import pytest
from unittest.mock import MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.schemas import SkillGapInput, SkillGapItem, RoadmapWeek, SkillGapResult
from utils.roadmap_generator import (
    identify_skill_gaps,
    generate_roadmap,
    compute_opportunity_increase,
    format_roadmap_for_display,
    OPPORTUNITY_MULTIPLIER,
    OPPORTUNITY_CAP,
)
from agents.skill_gap_agent import SkillGapAgent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_MARKET_DATA = {
    "Docker": 65,
    "AWS": 58,
    "FastAPI": 62,
    "LangChain": 55,
    "LangGraph": 44,
    "Machine Learning": 70,
    "Kubernetes": 50,
    "React": 60,
    "TypeScript": 57,
    "Redis": 48,
}

SAMPLE_USER_SKILLS = ["Python", "Flask", "SQL"]


@pytest.fixture
def market_data():
    return dict(SAMPLE_MARKET_DATA)


@pytest.fixture
def user_skills():
    return list(SAMPLE_USER_SKILLS)


@pytest.fixture
def gap_input(user_skills):
    return SkillGapInput(user_skills=user_skills, user_id="test_user")


@pytest.fixture
def mock_ai_roadmap_response():
    return {
        "roadmap": [
            {
                "week_range": "Week 1-2",
                "skill": "Machine Learning",
                "focus": "Machine Learning Fundamentals",
                "resources": [
                    "Andrew Ng's ML Specialization (Coursera)",
                    "Kaggle Learn — ML track",
                    "Scikit-Learn Documentation",
                ],
                "milestone": "Can train and evaluate a supervised ML model.",
            },
            {
                "week_range": "Week 3-4",
                "skill": "Docker",
                "focus": "Docker Containerization",
                "resources": [
                    "Docker Official Docs",
                    "Play With Docker (labs.play-with-docker.com)",
                    "Dockerfile best practices guide",
                ],
                "milestone": "Can containerize and deploy a Python app.",
            },
            {
                "week_range": "Week 5-6",
                "skill": "FastAPI",
                "focus": "FastAPI REST API Development",
                "resources": [
                    "FastAPI Official Tutorial",
                    "TestDriven.io FastAPI guide",
                    "FastAPI + SQLAlchemy project",
                ],
                "milestone": "Can build a complete REST API with auth and async support.",
            },
        ],
        "career_impact_summary": (
            "Mastering Machine Learning, Docker, and FastAPI could unlock "
            "up to +105% more job opportunities."
        ),
        "ai_reasoning": [
            "Machine Learning tops market demand with a score of 70/100.",
            "Docker is required for modern deployment pipelines.",
            "FastAPI is replacing Flask as the preferred Python web framework.",
            "These three skills together cover backend, ML, and DevOps.",
            "Combined, they represent high-demand full-stack freelance capabilities.",
        ],
    }


@pytest.fixture
def mock_groq_service_gap(mock_ai_roadmap_response):
    service = MagicMock()
    service.chat_json.return_value = (mock_ai_roadmap_response, json.dumps(mock_ai_roadmap_response))
    return service


@pytest.fixture
def gap_agent(mock_groq_service_gap, tmp_path):
    """Creates a SkillGapAgent with mock Groq and a temp market_data.json."""
    market_file = tmp_path / "market_data.json"
    market_file.write_text(json.dumps(SAMPLE_MARKET_DATA))
    return SkillGapAgent(
        groq_service=mock_groq_service_gap,
        market_data_path=market_file,
    )


# ---------------------------------------------------------------------------
# Tests: SkillGapInput Validation
# ---------------------------------------------------------------------------

class TestSkillGapInputValidation:

    def test_valid_input_passes(self, gap_input):
        errors = gap_input.validate()
        assert errors == []

    def test_empty_skills_fails(self):
        gi = SkillGapInput(user_skills=[])
        errors = gi.validate()
        assert any("user_skills" in e for e in errors)

    def test_too_many_skills_fails(self):
        gi = SkillGapInput(user_skills=[f"skill_{i}" for i in range(60)])
        errors = gi.validate()
        assert any("50" in e for e in errors)

    def test_from_dict_basic(self):
        gi = SkillGapInput.from_dict({"user_skills": ["Python", "SQL"]})
        assert gi.user_skills == ["Python", "SQL"]

    def test_from_dict_with_optional_fields(self):
        gi = SkillGapInput.from_dict({
            "user_skills": ["Python"],
            "user_id": "u1",
            "target_role": "ML Engineer",
        })
        assert gi.user_id == "u1"
        assert gi.target_role == "ML Engineer"

    def test_to_dict_roundtrip(self, gap_input):
        """Roundtrip must preserve all fields including optional ones."""
        gap_input_with_opts = SkillGapInput(
            user_skills=gap_input.user_skills,
            user_id="roundtrip_user",
            target_role="ML Engineer",
        )
        d = gap_input_with_opts.to_dict()
        restored = SkillGapInput.from_dict(d)
        assert restored.user_skills == gap_input_with_opts.user_skills
        assert restored.user_id == gap_input_with_opts.user_id
        assert restored.target_role == gap_input_with_opts.target_role


# ---------------------------------------------------------------------------
# Tests: Opportunity Increase Calculator
# ---------------------------------------------------------------------------

class TestOpportunityIncrease:

    def test_basic_calculation(self):
        result = compute_opportunity_increase(70)
        expected = min(70 * OPPORTUNITY_MULTIPLIER, OPPORTUNITY_CAP)
        assert abs(result - expected) < 0.01

    def test_zero_demand(self):
        result = compute_opportunity_increase(0)
        assert result == 0.0

    def test_high_demand_capped_at_200(self):
        result = compute_opportunity_increase(200)
        assert result == OPPORTUNITY_CAP

    def test_demand_100_produces_150(self):
        result = compute_opportunity_increase(100)
        assert result == min(100 * OPPORTUNITY_MULTIPLIER, OPPORTUNITY_CAP)

    def test_demand_50_produces_75(self):
        result = compute_opportunity_increase(50)
        assert abs(result - 75.0) < 0.1


# ---------------------------------------------------------------------------
# Tests: Skill Gap Identifier
# ---------------------------------------------------------------------------

class TestIdentifySkillGaps:

    def test_basic_gaps_detected(self, market_data, user_skills):
        gaps = identify_skill_gaps(user_skills, market_data, top_n=3)
        gap_names = [g.skill for g in gaps]
        # Python, Flask, SQL are in user_skills (not in market_data), so all market skills are gaps
        assert len(gaps) == 3

    def test_gaps_ranked_by_demand(self, market_data, user_skills):
        gaps = identify_skill_gaps(user_skills, market_data, top_n=5)
        demands = [g.market_demand_score for g in gaps]
        assert demands == sorted(demands, reverse=True)

    def test_no_gaps_if_user_has_all_skills(self, market_data):
        user_skills = list(market_data.keys())
        gaps = identify_skill_gaps(user_skills, market_data)
        assert gaps == []

    def test_case_insensitive_matching(self, market_data):
        # User has "docker" (lowercase) — should match "Docker" in market
        gaps = identify_skill_gaps(["docker", "aws", "fastapi"], market_data, top_n=10)
        gap_names_lower = [g.skill.lower() for g in gaps]
        assert "docker" not in gap_names_lower
        assert "aws" not in gap_names_lower

    def test_priority_rank_correct(self, market_data, user_skills):
        gaps = identify_skill_gaps(user_skills, market_data, top_n=3)
        for i, gap in enumerate(gaps):
            assert gap.priority_rank == i + 1

    def test_opportunity_increase_computed(self, market_data, user_skills):
        gaps = identify_skill_gaps(user_skills, market_data, top_n=3)
        for gap in gaps:
            expected = compute_opportunity_increase(gap.market_demand_score)
            assert abs(gap.opportunity_increase_pct - expected) < 0.01

    def test_top_n_respected(self, market_data, user_skills):
        gaps = identify_skill_gaps(user_skills, market_data, top_n=2)
        assert len(gaps) <= 2

    def test_xai_reason_populated(self, market_data, user_skills):
        gaps = identify_skill_gaps(user_skills, market_data, top_n=1)
        assert len(gaps[0].xai_reason) > 0

    def test_skill_gap_item_to_dict(self, market_data, user_skills):
        gaps = identify_skill_gaps(user_skills, market_data, top_n=1)
        d = gaps[0].to_dict()
        assert "skill" in d
        assert "market_demand_score" in d
        assert "opportunity_increase_pct" in d
        assert "priority_rank" in d


# ---------------------------------------------------------------------------
# Tests: Roadmap Generator
# ---------------------------------------------------------------------------

class TestGenerateRoadmap:

    def test_roadmap_has_correct_count(self, market_data, user_skills):
        gaps = identify_skill_gaps(user_skills, market_data, top_n=3)
        roadmap = generate_roadmap(gaps)
        assert len(roadmap) == len(gaps)

    def test_roadmap_week_ranges_are_sequential(self, market_data, user_skills):
        gaps = identify_skill_gaps(user_skills, market_data, top_n=3)
        roadmap = generate_roadmap(gaps)
        assert roadmap[0].week_range == "Week 1-2"
        assert roadmap[1].week_range == "Week 3-4"
        assert roadmap[2].week_range == "Week 5-6"

    def test_roadmap_skills_match_gaps(self, market_data, user_skills):
        gaps = identify_skill_gaps(user_skills, market_data, top_n=3)
        roadmap = generate_roadmap(gaps)
        gap_skills = [g.skill for g in gaps]
        roadmap_skills = [r.skill for r in roadmap]
        assert gap_skills == roadmap_skills

    def test_roadmap_has_resources(self, market_data, user_skills):
        gaps = identify_skill_gaps(user_skills, market_data, top_n=3)
        roadmap = generate_roadmap(gaps)
        for entry in roadmap:
            assert len(entry.resources) > 0

    def test_roadmap_has_milestones(self, market_data, user_skills):
        gaps = identify_skill_gaps(user_skills, market_data, top_n=3)
        roadmap = generate_roadmap(gaps)
        for entry in roadmap:
            assert entry.milestone and len(entry.milestone) > 0

    def test_empty_gaps_empty_roadmap(self):
        roadmap = generate_roadmap([])
        assert roadmap == []

    def test_format_roadmap_for_display(self, market_data, user_skills):
        gaps = identify_skill_gaps(user_skills, market_data, top_n=2)
        roadmap = generate_roadmap(gaps)
        text = format_roadmap_for_display(roadmap)
        assert "LEARNING ROADMAP" in text
        assert roadmap[0].skill in text

    def test_roadmap_entry_to_dict_serializable(self, market_data, user_skills):
        gaps = identify_skill_gaps(user_skills, market_data, top_n=1)
        roadmap = generate_roadmap(gaps)
        d = roadmap[0].to_dict()
        json.dumps(d)  # Should not raise


# ---------------------------------------------------------------------------
# Tests: SkillGapAgent
# ---------------------------------------------------------------------------

class TestSkillGapAgent:

    def test_analyze_valid_input_succeeds(self, gap_agent, gap_input):
        response = gap_agent.analyze(gap_input)
        assert response.success is True
        assert response.data is not None

    def test_analyze_returns_skill_gaps(self, gap_agent, gap_input):
        response = gap_agent.analyze(gap_input)
        assert "skill_gaps" in response.data
        assert len(response.data["skill_gaps"]) > 0

    def test_analyze_returns_roadmap(self, gap_agent, gap_input):
        response = gap_agent.analyze(gap_input)
        assert "roadmap" in response.data
        assert len(response.data["roadmap"]) > 0

    def test_analyze_returns_ai_reasoning(self, gap_agent, gap_input):
        response = gap_agent.analyze(gap_input)
        assert "ai_reasoning" in response.data
        assert len(response.data["ai_reasoning"]) > 0

    def test_analyze_from_dict_basic(self, gap_agent):
        response = gap_agent.analyze_from_dict({
            "user_skills": ["Python", "Flask"],
        })
        assert response.success is True

    def test_analyze_empty_skills_fails(self, gap_agent):
        response = gap_agent.analyze_from_dict({"user_skills": []})
        assert response.success is False
        assert "validation" in response.error.lower()

    def test_analyze_returns_correct_agent_name(self, gap_agent, gap_input):
        response = gap_agent.analyze(gap_input)
        assert response.agent == "SkillGapAgent"

    def test_analyze_duration_non_negative(self, gap_agent, gap_input):
        """Duration should be >= 0; mocked calls may complete in sub-millisecond time."""
        response = gap_agent.analyze(gap_input)
        assert response.duration_ms >= 0

    def test_analyze_existing_skills_preserved(self, gap_agent):
        skills = ["Python", "Flask", "SQL"]
        response = gap_agent.analyze_from_dict({"user_skills": skills})
        assert response.data["existing_skills"] == skills

    def test_analyze_groq_failure_uses_deterministic_fallback(self, tmp_path):
        """Agent should succeed with deterministic roadmap even if AI fails."""
        broken_groq = MagicMock()
        broken_groq.chat_json.side_effect = RuntimeError("Groq is down")
        market_file = tmp_path / "market_data.json"
        market_file.write_text(json.dumps(SAMPLE_MARKET_DATA))
        agent = SkillGapAgent(groq_service=broken_groq, market_data_path=market_file)

        response = agent.analyze_from_dict({"user_skills": ["Python", "Flask"]})
        # Should still succeed with deterministic roadmap
        assert response.success is True
        assert len(response.data["roadmap"]) > 0

    def test_analyze_missing_market_data_file(self, mock_groq_service_gap):
        """Agent should handle missing market_data.json gracefully."""
        agent = SkillGapAgent(
            groq_service=mock_groq_service_gap,
            market_data_path=Path("/nonexistent/path/market_data.json"),
        )
        response = agent.analyze_from_dict({"user_skills": ["Python"]})
        # Should return success but with empty gaps (no market data = no gaps detected)
        assert response.success is True

    def test_result_json_serializable(self, gap_agent, gap_input):
        response = gap_agent.analyze(gap_input)
        json_str = json.dumps(response.to_dict())
        assert json.loads(json_str)["success"] is True

    def test_get_market_data_returns_dict(self, gap_agent):
        md = gap_agent.get_market_data()
        assert isinstance(md, dict)
        assert len(md) > 0

    def test_user_has_all_market_skills_returns_empty_gaps(self, mock_groq_service_gap, tmp_path):
        market_file = tmp_path / "market_data.json"
        market_file.write_text(json.dumps(SAMPLE_MARKET_DATA))
        agent = SkillGapAgent(groq_service=mock_groq_service_gap, market_data_path=market_file)

        all_skills = list(SAMPLE_MARKET_DATA.keys())
        response = agent.analyze_from_dict({"user_skills": all_skills})
        assert response.success is True
        assert response.data["skill_gaps"] == []


# ---------------------------------------------------------------------------
# Tests: Bug Regression — Impact Summary Single-Skill
# ---------------------------------------------------------------------------

class TestImpactSummaryRegression:
    """Regression tests for bug fixes in _build_impact_summary."""

    def test_single_gap_no_leading_and(self, tmp_path):
        """Bug fix: single skill gap must NOT produce ' and Docker' (leading space+and).
        Uses a broken Groq to force the deterministic _build_impact_summary path.
        """
        broken_groq = MagicMock()
        broken_groq.chat_json.side_effect = RuntimeError("forced failure")
        market_file = tmp_path / "market_data.json"
        market_file.write_text(json.dumps({"Docker": 65}))
        agent = SkillGapAgent(groq_service=broken_groq, market_data_path=market_file)

        response = agent.analyze_from_dict({"user_skills": ["Python"]})
        assert response.success is True
        summary = response.data["career_impact_summary"]
        # Must read 'Mastering Docker' not 'Mastering  and Docker'
        assert "Mastering Docker" in summary
        assert "Mastering  and" not in summary
        assert not summary.startswith("Mastering  ")

    def test_two_gaps_correct_conjunction(self, tmp_path):
        """Two skill gaps should format as 'A and B' (deterministic path)."""
        broken_groq = MagicMock()
        broken_groq.chat_json.side_effect = RuntimeError("forced failure")
        market_file = tmp_path / "market_data.json"
        market_file.write_text(json.dumps({"Docker": 65, "AWS": 58}))
        agent = SkillGapAgent(groq_service=broken_groq, market_data_path=market_file)

        response = agent.analyze_from_dict({"user_skills": ["Python"]})
        assert response.success is True
        summary = response.data["career_impact_summary"]
        assert "Docker and AWS" in summary

    def test_three_gaps_correct_list(self, tmp_path):
        """Three skill gaps should format as 'A, B and C' (deterministic path)."""
        broken_groq = MagicMock()
        broken_groq.chat_json.side_effect = RuntimeError("forced failure")
        market_file = tmp_path / "market_data.json"
        market_file.write_text(json.dumps({"Docker": 65, "AWS": 58, "FastAPI": 62}))
        agent = SkillGapAgent(groq_service=broken_groq, market_data_path=market_file)

        response = agent.analyze_from_dict({"user_skills": ["Python"]})
        assert response.success is True
        summary = response.data["career_impact_summary"]
        # e.g. 'Mastering Docker, FastAPI and AWS could unlock...'
        assert " and " in summary
        assert "," in summary


# ---------------------------------------------------------------------------
# Tests: Bug Regression — Mutable Default Aliasing in EvaluationEngine
# ---------------------------------------------------------------------------

class TestEvaluationEngineAliasRegression:
    """Regression tests for mutable list aliasing bug in EvaluationEngine._extract_list."""

    def test_multiple_evaluations_do_not_share_reasoning_lists(self):
        """Bug fix: two evaluations with missing reasoning must not share the same list object."""
        from services.evaluation_engine import EvaluationEngine
        engine = EvaluationEngine()

        # Response with no 'reasoning' key — will use default list
        ai_response_no_reasoning = {
            "component_scores": {
                "code_quality": 75, "documentation": 70, "security": 72, "problem_solving": 80
            }
        }

        result1 = engine.evaluate("u1", "Python", ai_response_no_reasoning, "raw")
        result2 = engine.evaluate("u2", "Docker", ai_response_no_reasoning, "raw")

        # Both should have the scoring explanation prepended, but as independent lists
        assert result1.reasoning is not result2.reasoning, (
            "reasoning lists must be independent objects, not the same aliased list"
        )
        # Each list should have exactly 2 items: the scoring explanation + the default
        assert len(result1.reasoning) == 2
        assert len(result2.reasoning) == 2
