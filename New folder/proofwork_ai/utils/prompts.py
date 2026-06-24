"""
ProofWork AI - Prompt Templates
=================================
All LLM prompts are centralized here.

Design Principles:
  - Each prompt is a pure function for testability.
  - System + user prompt pairs are returned as tuples.
  - Prompts are engineered for structured JSON responses.
  - Every prompt requests XAI reasoning to maintain explainability.

Author: Swetha
Module: utils/prompts.py
"""

from typing import Tuple


# ---------------------------------------------------------------------------
# Skill Verification Prompts
# ---------------------------------------------------------------------------

SKILL_VERIFIER_SYSTEM_PROMPT = """You are an expert technical evaluator for ProofWork AI, a trust-first freelance marketplace.
Your role is to rigorously assess skill submissions from freelancers using Explainable AI (XAI) principles.

You evaluate submissions across four dimensions:
1. Code Quality (0-100): Structure, readability, naming conventions, best practices.
2. Documentation Quality (0-100): Comments, docstrings, clarity of explanation.
3. Security Awareness (0-100): Input validation, error handling, safe patterns, potential vulnerabilities.
4. Problem Solving (0-100): Approach correctness, efficiency, completeness, creativity.

CRITICAL RULES:
- Be strict but fair. Real employers will rely on your scores.
- Always explain WHY you assigned each score.
- Identify specific strengths observed in the submission.
- Identify specific improvements the freelancer can make.
- Return ONLY valid JSON. No prose before or after the JSON block.
- Use the EXACT JSON schema provided.

JSON RESPONSE SCHEMA:
{
  "component_scores": {
    "code_quality": <number 0-100>,
    "documentation": <number 0-100>,
    "security": <number 0-100>,
    "problem_solving": <number 0-100>
  },
  "reasoning": [
    "<specific observation 1>",
    "<specific observation 2>",
    "<specific observation 3>",
    "<specific observation 4>",
    "<specific observation 5>"
  ],
  "strengths": [
    "<strength 1>",
    "<strength 2>",
    "<strength 3>"
  ],
  "improvements": [
    "<improvement suggestion 1>",
    "<improvement suggestion 2>",
    "<improvement suggestion 3>"
  ]
}"""


def build_skill_verifier_user_prompt(
    skill: str,
    challenge_title: str,
    submission_text: str,
    submission_time: str,
) -> str:
    """
    Builds the user-turn prompt for skill verification.

    Args:
        skill: The claimed skill (e.g., "Python Automation").
        challenge_title: The challenge given (e.g., "Build a File Organizer").
        submission_text: The actual submission content.
        submission_time: ISO timestamp of submission.

    Returns:
        Formatted user prompt string.
    """
    return f"""SKILL VERIFICATION REQUEST
==========================

Claimed Skill: {skill}
Challenge Title: {challenge_title}
Submission Time: {submission_time}

SUBMISSION CONTENT:
-------------------
{submission_text}
-------------------

Evaluate this submission strictly and fairly across all four dimensions.
Provide detailed, specific reasoning for each score.
Identify real strengths and actionable improvement areas.
Return only the JSON object as described in the system prompt."""


def get_skill_verifier_prompts(
    skill: str,
    challenge_title: str,
    submission_text: str,
    submission_time: str,
) -> Tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) tuple for the verifier agent.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    return (
        SKILL_VERIFIER_SYSTEM_PROMPT,
        build_skill_verifier_user_prompt(
            skill, challenge_title, submission_text, submission_time
        ),
    )


# ---------------------------------------------------------------------------
# Skill Gap Intelligence Prompts
# ---------------------------------------------------------------------------

SKILL_GAP_SYSTEM_PROMPT = """You are a Senior Career Intelligence Analyst for ProofWork AI.
Your role is to analyze a freelancer's existing skills against real-world market demand and generate an actionable, explainable career acceleration plan.

You will receive:
1. The freelancer's current skills.
2. Market demand data (skill → demand score 0–100).
3. The top skill gaps (skills missing from the freelancer's profile but in high market demand).

Your task:
- Generate a detailed, personalized learning roadmap (6–12 weeks).
- Provide an overall career impact narrative.
- Explain WHY each recommended skill matters (XAI reasoning).
- Be specific, actionable, and motivating.

CRITICAL RULES:
- Return ONLY valid JSON. No prose before or after the JSON block.
- Use the EXACT JSON schema provided.
- Each roadmap entry covers a 2-week period.
- Resources must be specific and practical (not generic like "Google it").

JSON RESPONSE SCHEMA:
{
  "roadmap": [
    {
      "week_range": "Week 1-2",
      "skill": "<skill name>",
      "focus": "<specific learning focus>",
      "resources": ["<resource 1>", "<resource 2>", "<resource 3>"],
      "milestone": "<what the learner can do by end of this period>"
    }
  ],
  "career_impact_summary": "<motivating 2-3 sentence impact narrative>",
  "ai_reasoning": [
    "<XAI reason 1 for recommendations>",
    "<XAI reason 2>",
    "<XAI reason 3>",
    "<XAI reason 4>",
    "<XAI reason 5>"
  ]
}"""


def build_skill_gap_user_prompt(
    existing_skills: list,
    skill_gaps: list,
    market_data: dict,
    target_role: str = None,
) -> str:
    """
    Builds the user-turn prompt for skill gap analysis.

    Args:
        existing_skills: Freelancer's current skill list.
        skill_gaps: Top-ranked missing skills.
        market_data: Full market demand dictionary.
        target_role: Optional career target role.

    Returns:
        Formatted user prompt string.
    """
    role_line = f"Target Role: {target_role}" if target_role else "Target Role: Senior Freelance Developer (general)"

    market_snapshot = "\n".join(
        f"  - {skill}: {score}/100 demand"
        for skill, score in sorted(market_data.items(), key=lambda x: -x[1])
    )

    gaps_formatted = "\n".join(
        f"  {i+1}. {gap['skill']} (demand: {gap['market_demand_score']}/100, "
        f"opportunity boost: +{gap['opportunity_increase_pct']}%)"
        for i, gap in enumerate(skill_gaps)
    )

    existing_formatted = ", ".join(existing_skills) if existing_skills else "None listed"

    return f"""SKILL GAP ANALYSIS REQUEST
===========================

Freelancer Profile:
  Current Skills: {existing_formatted}
  {role_line}

Top Skill Gaps Identified (already ranked by priority):
{gaps_formatted}

Full Market Demand Snapshot:
{market_snapshot}

Instructions:
- Create a personalized week-by-week learning roadmap covering the top skill gaps.
- Write a motivating career impact summary.
- Provide 5 XAI reasoning points explaining WHY these skills were prioritized.
- Each roadmap entry should specify concrete resources (courses, docs, projects).
- Return only the JSON object as described in the system prompt."""


def get_skill_gap_prompts(
    existing_skills: list,
    skill_gaps: list,
    market_data: dict,
    target_role: str = None,
) -> Tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) tuple for the skill gap agent.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    return (
        SKILL_GAP_SYSTEM_PROMPT,
        build_skill_gap_user_prompt(
            existing_skills, skill_gaps, market_data, target_role
        ),
    )
