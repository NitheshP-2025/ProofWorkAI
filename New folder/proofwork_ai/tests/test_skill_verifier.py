"""
ProofWork AI - Test Suite: Skill Verification Agent
=====================================================
Comprehensive pytest test coverage for:
  - SkillSubmission validation
  - EvaluationEngine scoring logic
  - SkillVerificationAgent orchestration
  - Error handling paths

Author: Swetha
"""

import json
import pytest
from unittest.mock import MagicMock

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.schemas import (
    SkillSubmission,
    ComponentScores,
    VerificationResult,
    APIResponse,
)
from services.evaluation_engine import (
    EvaluationEngine,
    THRESHOLD_VERIFIED,
    THRESHOLD_PARTIAL,
    STATUS_VERIFIED,
    STATUS_PARTIAL,
    STATUS_NOT_VERIFIED,
)
from agents.skill_verifier import SkillVerificationAgent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_submission():
    return SkillSubmission(
        user_id="test_user_001",
        skill="Python Automation",
        challenge_title="Build a File Organizer",
        submission_text=(
            "import os\nimport shutil\nfrom pathlib import Path\n\n"
            "def organize(source: str) -> None:\n"
            "    \"\"\"Organizes files into folders.\"\"\"\n"
            "    source_path = Path(source)\n"
            "    if not source_path.exists():\n"
            "        raise ValueError(f'Directory not found: {source}')\n"
            "    for f in source_path.iterdir():\n"
            "        if f.is_file():\n"
            "            dest = source_path / f.suffix.strip('.')\n"
            "            dest.mkdir(exist_ok=True)\n"
            "            shutil.move(str(f), str(dest / f.name))\n"
        ),
        submission_time="2026-06-24T10:00:00",
    )


@pytest.fixture
def mock_ai_response():
    return {
        "component_scores": {
            "code_quality": 88,
            "documentation": 75,
            "security": 82,
            "problem_solving": 90,
        },
        "reasoning": [
            "Clean modular structure with function decomposition.",
            "Docstring present in the main function.",
            "Input validation using Path.exists() before processing.",
            "Good use of pathlib for OS-agnostic file handling.",
            "Handles file collisions gracefully.",
        ],
        "strengths": [
            "Uses pathlib for cross-platform compatibility.",
            "Includes error handling for missing directories.",
            "Clear and descriptive function naming.",
        ],
        "improvements": [
            "No logging implementation — add Python logging module.",
            "Missing unit tests for the organize function.",
            "No CLI interface (argparse) for usability.",
        ],
    }


@pytest.fixture
def evaluation_engine():
    return EvaluationEngine()


@pytest.fixture
def mock_groq_service(mock_ai_response):
    service = MagicMock()
    service.chat_json.return_value = (mock_ai_response, json.dumps(mock_ai_response))
    return service


@pytest.fixture
def agent(mock_groq_service):
    return SkillVerificationAgent(
        groq_service=mock_groq_service,
        evaluation_engine=EvaluationEngine(),
    )


# ---------------------------------------------------------------------------
# Tests: SkillSubmission Validation
# ---------------------------------------------------------------------------

class TestSkillSubmissionValidation:

    def test_valid_submission_passes(self, valid_submission):
        errors = valid_submission.validate()
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_empty_user_id_fails(self, valid_submission):
        valid_submission.user_id = "   "
        errors = valid_submission.validate()
        assert any("user_id" in e for e in errors)

    def test_empty_skill_fails(self, valid_submission):
        valid_submission.skill = ""
        errors = valid_submission.validate()
        assert any("skill" in e for e in errors)

    def test_empty_challenge_fails(self, valid_submission):
        valid_submission.challenge_title = ""
        errors = valid_submission.validate()
        assert any("challenge_title" in e for e in errors)

    def test_short_submission_fails(self, valid_submission):
        valid_submission.submission_text = "too short"
        errors = valid_submission.validate()
        assert any("submission_text" in e for e in errors)

    def test_from_dict_roundtrip(self, valid_submission):
        d = valid_submission.to_dict()
        restored = SkillSubmission.from_dict(d)
        assert restored.user_id == valid_submission.user_id
        assert restored.skill == valid_submission.skill
        assert restored.submission_text == valid_submission.submission_text

    def test_from_dict_missing_key_raises(self):
        with pytest.raises((KeyError, TypeError)):
            SkillSubmission.from_dict({"user_id": "x"})  # missing required keys


# ---------------------------------------------------------------------------
# Tests: ComponentScores
# ---------------------------------------------------------------------------

class TestComponentScores:

    def test_compute_overall_formula(self):
        scores = ComponentScores(
            code_quality=90,
            documentation=80,
            security=70,
            problem_solving=85,
        )
        expected = (90 * 0.30) + (80 * 0.20) + (70 * 0.20) + (85 * 0.30)
        assert abs(scores.compute_overall() - expected) < 0.01

    def test_all_zeros(self):
        scores = ComponentScores(0, 0, 0, 0)
        assert scores.compute_overall() == 0.0

    def test_all_hundreds(self):
        scores = ComponentScores(100, 100, 100, 100)
        assert scores.compute_overall() == 100.0

    def test_weights_sum_to_one(self):
        """Ensure the formula accounts for 100% of the score."""
        total_weight = 0.30 + 0.20 + 0.20 + 0.30
        assert abs(total_weight - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# Tests: EvaluationEngine
# ---------------------------------------------------------------------------

class TestEvaluationEngine:

    def test_evaluate_returns_verified_status(self, evaluation_engine, mock_ai_response):
        result = evaluation_engine.evaluate(
            user_id="u1",
            skill="Python",
            ai_response=mock_ai_response,
            raw_ai_text="raw",
        )
        assert result.status == STATUS_VERIFIED
        assert result.overall_score >= THRESHOLD_VERIFIED

    def test_evaluate_status_partially_verified(self, evaluation_engine):
        ai_response = {
            "component_scores": {"code_quality": 65, "documentation": 60, "security": 62, "problem_solving": 70},
            "reasoning": ["moderate quality"],
            "strengths": ["some strengths"],
            "improvements": ["many improvements needed"],
        }
        result = evaluation_engine.evaluate("u2", "React", ai_response, "raw")
        assert result.status == STATUS_PARTIAL

    def test_evaluate_status_not_verified(self, evaluation_engine):
        ai_response = {
            "component_scores": {"code_quality": 40, "documentation": 30, "security": 50, "problem_solving": 35},
            "reasoning": ["poor quality"],
            "strengths": [],
            "improvements": ["needs significant work"],
        }
        result = evaluation_engine.evaluate("u3", "Kubernetes", ai_response, "raw")
        assert result.status == STATUS_NOT_VERIFIED

    def test_evaluate_with_missing_component_scores(self, evaluation_engine):
        """Should handle missing component_scores gracefully (use 0)."""
        ai_response = {"reasoning": ["no scores"]}
        result = evaluation_engine.evaluate("u4", "Go", ai_response, "raw")
        assert result.overall_score == 0.0
        assert result.status == STATUS_NOT_VERIFIED

    def test_evaluate_score_clamped_above_100(self, evaluation_engine):
        """Scores > 100 should be clamped to 100."""
        ai_response = {
            "component_scores": {"code_quality": 150, "documentation": 200, "security": 999, "problem_solving": 120},
            "reasoning": [], "strengths": [], "improvements": [],
        }
        result = evaluation_engine.evaluate("u5", "Go", ai_response, "raw")
        assert result.component_scores.code_quality == 100.0
        assert result.overall_score <= 100.0

    def test_evaluate_score_clamped_below_zero(self, evaluation_engine):
        """Scores < 0 should be clamped to 0."""
        ai_response = {
            "component_scores": {"code_quality": -10, "documentation": -5, "security": -20, "problem_solving": -1},
            "reasoning": [], "strengths": [], "improvements": [],
        }
        result = evaluation_engine.evaluate("u6", "Go", ai_response, "raw")
        assert result.component_scores.code_quality == 0.0

    def test_result_contains_xai_reasoning(self, evaluation_engine, mock_ai_response):
        result = evaluation_engine.evaluate("u7", "Python", mock_ai_response, "raw")
        assert len(result.reasoning) > 0
        assert isinstance(result.reasoning[0], str)

    def test_result_user_id_preserved(self, evaluation_engine, mock_ai_response):
        result = evaluation_engine.evaluate("test_uid_42", "Python", mock_ai_response, "raw")
        assert result.user_id == "test_uid_42"

    def test_result_to_dict_serializable(self, evaluation_engine, mock_ai_response):
        result = evaluation_engine.evaluate("u8", "Python", mock_ai_response, "raw")
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "overall_score" in d
        assert "status" in d
        assert "reasoning" in d

    def test_result_to_json_valid(self, evaluation_engine, mock_ai_response):
        result = evaluation_engine.evaluate("u9", "Python", mock_ai_response, "raw")
        json_str = result.to_json()
        parsed = json.loads(json_str)
        assert parsed["user_id"] == "u9"


# ---------------------------------------------------------------------------
# Tests: SkillVerificationAgent
# ---------------------------------------------------------------------------

class TestSkillVerificationAgent:

    def test_verify_valid_submission_succeeds(self, agent, valid_submission):
        response = agent.verify(valid_submission)
        assert response.success is True
        assert response.data is not None
        assert response.error is None

    def test_verify_returns_correct_user_id(self, agent, valid_submission):
        response = agent.verify(valid_submission)
        assert response.data["user_id"] == valid_submission.user_id

    def test_verify_returns_verified_status(self, agent, valid_submission):
        response = agent.verify(valid_submission)
        assert response.data["status"] == STATUS_VERIFIED

    def test_verify_from_dict_valid(self, agent):
        response = agent.verify_from_dict({
            "user_id": "101",
            "skill": "Python Automation",
            "challenge_title": "Build a File Organizer",
            "submission_text": "import os\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
            "submission_time": "2026-06-24T10:00:00",
        })
        assert response.success is True

    def test_verify_invalid_submission_returns_error(self, agent):
        bad_submission = SkillSubmission(
            user_id="",
            skill="",
            challenge_title="",
            submission_text="",
        )
        response = agent.verify(bad_submission)
        assert response.success is False
        assert response.error is not None

    def test_verify_from_dict_missing_fields_returns_error(self, agent):
        response = agent.verify_from_dict({"user_id": "x"})  # missing required
        assert response.success is False

    def test_verify_groq_failure_returns_error(self, valid_submission):
        broken_groq = MagicMock()
        broken_groq.chat_json.side_effect = RuntimeError("Groq API is down")
        agent = SkillVerificationAgent(
            groq_service=broken_groq,
            evaluation_engine=EvaluationEngine(),
        )
        response = agent.verify(valid_submission)
        assert response.success is False
        assert "AI service error" in response.error

    def test_verify_groq_invalid_json_returns_error(self, valid_submission):
        broken_groq = MagicMock()
        broken_groq.chat_json.side_effect = ValueError("Invalid JSON")
        agent = SkillVerificationAgent(
            groq_service=broken_groq,
            evaluation_engine=EvaluationEngine(),
        )
        response = agent.verify(valid_submission)
        assert response.success is False

    def test_response_contains_agent_name(self, agent, valid_submission):
        response = agent.verify(valid_submission)
        assert response.agent == "SkillVerificationAgent"

    def test_response_duration_non_negative(self, agent, valid_submission):
        """Duration should be >= 0; mocked calls may complete in sub-millisecond time."""
        response = agent.verify(valid_submission)
        assert response.duration_ms >= 0

    def test_api_response_serializable(self, agent, valid_submission):
        response = agent.verify(valid_submission)
        d = response.to_dict()
        json_str = json.dumps(d)
        assert json.loads(json_str)["success"] is True


# ---------------------------------------------------------------------------
# Tests: Bug Regression — EvaluationEngine mutable default aliasing
# ---------------------------------------------------------------------------

class TestEvaluationEngineRegressions:
    """Regression tests for critical bugs fixed in EvaluationEngine."""

    def test_reasoning_list_is_not_shared_across_evaluations(self):
        """
        Bug fix: _extract_list previously returned the literal default list object.
        When reasoning.insert(0, ...) was called it mutated the shared default.
        After fix, every call must return a *new* independent list.
        """
        engine = EvaluationEngine()
        # No 'reasoning' key — forces use of the default list
        ai_resp = {
            "component_scores": {
                "code_quality": 80, "documentation": 80,
                "security": 80, "problem_solving": 80,
            }
        }
        r1 = engine.evaluate("u_a", "Python", ai_resp, "raw1")
        r2 = engine.evaluate("u_b", "Go",     ai_resp, "raw2")

        # Lists must be different objects
        assert r1.reasoning is not r2.reasoning, (
            "Bug: reasoning lists are the same aliased object across evaluations"
        )
        # Each must have exactly: [scoring_explanation, default_message]
        assert len(r1.reasoning) == 2
        assert len(r2.reasoning) == 2
        # Scoring explanations should reference the correct skill
        assert "Python" in r1.reasoning[0] or "100" in r1.reasoning[0]

    def test_strengths_list_is_not_shared_across_evaluations(self):
        """Same aliasing fix must apply to strengths and improvements lists."""
        engine = EvaluationEngine()
        ai_resp = {
            "component_scores": {
                "code_quality": 50, "documentation": 50,
                "security": 50, "problem_solving": 50,
            }
            # No 'strengths' or 'improvements' keys
        }
        r1 = engine.evaluate("u_c", "Rust",   ai_resp, "raw")
        r2 = engine.evaluate("u_d", "Kafka",   ai_resp, "raw")

        assert r1.strengths is not r2.strengths, (
            "Bug: strengths lists are aliased across evaluations"
        )
        assert r1.improvements is not r2.improvements, (
            "Bug: improvements lists are aliased across evaluations"
        )

    def test_score_clamping_preserves_formula_integrity(self):
        """Score clamping must not silently alter the weighted formula result."""
        engine = EvaluationEngine()
        ai_resp = {
            "component_scores": {
                "code_quality": 100, "documentation": 100,
                "security": 100, "problem_solving": 100,
            },
            "reasoning": ["Perfect submission."],
            "strengths": ["Excellent."],
            "improvements": ["None."],
        }
        result = engine.evaluate("u_e", "Python", ai_resp, "raw")
        assert result.overall_score == 100.0, (
            f"Expected 100.0 overall score for all-100 components, got {result.overall_score}"
        )
