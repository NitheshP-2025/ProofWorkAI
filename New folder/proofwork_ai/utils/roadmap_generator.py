"""
ProofWork AI - Roadmap Generator
==================================
Generates deterministic, data-driven learning roadmaps from skill gap data.
This module handles roadmap creation independently of the AI model, providing
a fallback and also enriching the AI-generated roadmap with structured data.

Design:
  - Pure functions for testability.
  - Market-data-aware priority sorting.
  - Career impact scoring via opportunity increase calculation.
  - Produces RoadmapWeek and SkillGapItem models.

Author: Swetha
Module: utils/roadmap_generator.py
"""

from typing import List, Dict, Tuple
from models.schemas import SkillGapItem, RoadmapWeek
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Opportunity Increase Formula
# ---------------------------------------------------------------------------

# Multiplier used to estimate opportunity increase from market demand score.
# A skill with demand=70 => +70*1.5 = +105% opportunity boost (capped at 200%)
OPPORTUNITY_MULTIPLIER = 1.5
OPPORTUNITY_CAP = 200.0

# Fallback resource templates per skill category
RESOURCE_TEMPLATES: Dict[str, List[str]] = {
    "Docker": [
        "Docker Official Docs — Get Started tutorial",
        "Play With Docker (labs.play-with-docker.com)",
        "Dockerfile best practices guide (docs.docker.com)",
    ],
    "AWS": [
        "AWS Free Tier — Hands-on labs",
        "AWS Skill Builder (skillbuilder.aws)",
        "Stephane Maarek AWS courses (Udemy)",
    ],
    "FastAPI": [
        "FastAPI Official Tutorial (fastapi.tiangolo.com)",
        "Build REST APIs with FastAPI — TestDriven.io",
        "FastAPI + SQLAlchemy full project on GitHub",
    ],
    "LangChain": [
        "LangChain Python Docs (python.langchain.com)",
        "Build LLM Apps with LangChain — DeepLearning.AI",
        "LangChain Cookbook GitHub examples",
    ],
    "LangGraph": [
        "LangGraph Docs (langchain-ai.github.io/langgraph)",
        "LangGraph multi-agent tutorial",
        "Build agentic workflows with LangGraph — blog series",
    ],
    "Machine Learning": [
        "Andrew Ng's Machine Learning Specialization (Coursera)",
        "Kaggle Learn — ML track (free)",
        "Hands-On Machine Learning with Scikit-Learn (book)",
    ],
    "Kubernetes": [
        "Kubernetes.io interactive tutorial",
        "Kubernetes in Action (book by Marko Luksa)",
        "KodeKloud Kubernetes for Beginners (free labs)",
    ],
    "React": [
        "React Official Docs (react.dev)",
        "Full Stack Open (fullstackopen.com) — free",
        "Scrimba React course",
    ],
    "TypeScript": [
        "TypeScript Handbook (typescriptlang.org/docs)",
        "Execute Program — TypeScript track",
        "Matt Pocock TypeScript tips (YouTube)",
    ],
    "GraphQL": [
        "How to GraphQL (howtographql.com)",
        "Apollo GraphQL tutorial",
        "GraphQL.org official learn section",
    ],
    "Redis": [
        "Redis University — free courses (university.redis.com)",
        "Redis official commands reference",
        "Redis in Action (book)",
    ],
    "PostgreSQL": [
        "PostgreSQL Tutorial (postgresqltutorial.com)",
        "Mode Analytics SQL School",
        "The Art of PostgreSQL (book)",
    ],
}

_DEFAULT_RESOURCES = [
    "Official documentation for the skill",
    "Udemy / Coursera top-rated course",
    "Build a real project and publish to GitHub",
]

_DEFAULT_MILESTONES: Dict[str, str] = {
    "Docker": "Can containerize a Python or Node.js app and push to Docker Hub.",
    "AWS": "Can deploy a simple web app to EC2 or Lambda using AWS Console and CLI.",
    "FastAPI": "Can build a fully functional REST API with auth, validation, and async endpoints.",
    "LangChain": "Can build a RAG-powered Q&A chatbot over custom documents.",
    "LangGraph": "Can design and run a multi-agent workflow using LangGraph nodes and edges.",
    "Machine Learning": "Can train, evaluate, and deploy a supervised ML model end-to-end.",
    "Kubernetes": "Can deploy, scale, and manage a multi-container app on a local k8s cluster.",
    "React": "Can build a full-featured SPA with hooks, context, and API integration.",
    "TypeScript": "Can migrate a JS project to TypeScript and configure strict mode.",
    "GraphQL": "Can design a GraphQL schema and implement resolvers for a REST-equivalent API.",
    "Redis": "Can implement caching, pub/sub, and session management using Redis.",
    "PostgreSQL": "Can design normalized schemas, write complex queries, and use indexing.",
}


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def compute_opportunity_increase(demand_score: float) -> float:
    """
    Computes estimated opportunity increase percentage from a demand score.

    Formula: demand_score * OPPORTUNITY_MULTIPLIER, capped at OPPORTUNITY_CAP.

    Args:
        demand_score: Raw market demand score (0–100).

    Returns:
        Estimated opportunity increase as a percentage.
    """
    raw = demand_score * OPPORTUNITY_MULTIPLIER
    return round(min(raw, OPPORTUNITY_CAP), 1)


def identify_skill_gaps(
    user_skills: List[str],
    market_data: Dict[str, float],
    top_n: int = 3,
) -> List[SkillGapItem]:
    """
    Identifies and ranks skill gaps by market demand.

    Args:
        user_skills: Skills the freelancer currently has.
        market_data: Mapping of skill → demand score.
        top_n: Maximum number of gaps to return.

    Returns:
        List of SkillGapItem sorted by demand (highest first), limited to top_n.
    """
    # Normalize to lowercase for comparison
    user_skills_lower = {s.strip().lower() for s in user_skills}

    gaps: List[Tuple[str, float]] = []
    for skill, demand in market_data.items():
        if skill.strip().lower() not in user_skills_lower:
            gaps.append((skill, demand))

    # Sort by demand descending
    gaps.sort(key=lambda x: x[1], reverse=True)
    gaps = gaps[:top_n]

    logger.debug(f"Identified {len(gaps)} skill gaps from {len(market_data)} market skills.")

    return [
        SkillGapItem(
            skill=skill,
            market_demand_score=demand,
            opportunity_increase_pct=compute_opportunity_increase(demand),
            priority_rank=rank + 1,
            xai_reason=(
                f"{skill} has a market demand score of {demand}/100. "
                f"Adding it to your profile is estimated to increase your "
                f"job opportunities by +{compute_opportunity_increase(demand)}%."
            ),
        )
        for rank, (skill, demand) in enumerate(gaps)
    ]


def generate_roadmap(skill_gaps: List[SkillGapItem]) -> List[RoadmapWeek]:
    """
    Generates a week-by-week learning roadmap for identified skill gaps.

    Each skill occupies a 2-week block. Skills are ordered by priority rank.

    Args:
        skill_gaps: Ranked list of SkillGapItem objects.

    Returns:
        List of RoadmapWeek objects forming the learning plan.
    """
    roadmap: List[RoadmapWeek] = []

    for i, gap in enumerate(skill_gaps):
        week_start = (i * 2) + 1
        week_end = week_start + 1
        week_range = f"Week {week_start}-{week_end}"

        # Skill-aware focus labels give more accurate descriptions than positional index
        _FOCUS_LABELS: Dict[str, str] = {
            "Docker": "Docker Containerization & DevOps",
            "AWS": "Cloud Infrastructure & Deployment",
            "FastAPI": "High-Performance REST API Development",
            "LangChain": "LLM Application Development",
            "LangGraph": "Multi-Agent Workflow Engineering",
            "Machine Learning": "ML Fundamentals & Model Training",
            "Kubernetes": "Container Orchestration & Scaling",
            "React": "Modern Frontend Development",
            "TypeScript": "Type-Safe JavaScript Engineering",
            "GraphQL": "API Query Language & Schema Design",
            "Redis": "In-Memory Caching & Data Structures",
            "PostgreSQL": "Advanced Relational Database Design",
        }
        _POSITION_LABELS = ["Fundamentals", "Deep Dive", "Projects & Deployment", "Advanced Patterns"]
        focus = _FOCUS_LABELS.get(
            gap.skill,
            f"{gap.skill} {_POSITION_LABELS[min(i, len(_POSITION_LABELS) - 1)]}",
        )

        resources = RESOURCE_TEMPLATES.get(gap.skill, _DEFAULT_RESOURCES)
        milestone = _DEFAULT_MILESTONES.get(
            gap.skill,
            f"Can demonstrate proficiency in {gap.skill} with a working project.",
        )

        roadmap.append(
            RoadmapWeek(
                week_range=week_range,
                skill=gap.skill,
                focus=focus,
                resources=list(resources),
                milestone=milestone,
            )
        )
        logger.debug(f"Roadmap entry added: {week_range} → {gap.skill}")

    return roadmap


def format_roadmap_for_display(roadmap: List[RoadmapWeek]) -> str:
    """
    Formats roadmap as a human-readable text block.

    Args:
        roadmap: List of RoadmapWeek items.

    Returns:
        Formatted multi-line string.
    """
    lines = ["📅 LEARNING ROADMAP", "=" * 40]
    for entry in roadmap:
        lines.append(f"\n{entry.week_range}: {entry.skill}")
        lines.append(f"  Focus   : {entry.focus}")
        lines.append(f"  Milestone: {entry.milestone}")
        lines.append("  Resources:")
        for res in entry.resources:
            lines.append(f"    • {res}")
    return "\n".join(lines)
