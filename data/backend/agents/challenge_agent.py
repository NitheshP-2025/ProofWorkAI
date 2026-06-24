import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHALLENGE_FILE = os.path.join(BASE_DIR, "data", "challenges.json")

with open(CHALLENGE_FILE, "r") as file:
    challenges = json.load(file)


def discover_challenges(verified_skills):
    recommendations = []

    for challenge in challenges:
        required_skills = challenge["required_skills"]

        matched = len(set(verified_skills) & set(required_skills))
        match_score = (matched / len(required_skills)) * 100

        # Confidence calculation
        if match_score >= 80:
            confidence = "Very High"
        elif match_score >= 60:
            confidence = "High"
        elif match_score >= 40:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Explainability
        matched_skills = list(set(verified_skills) & set(required_skills))
        missing_skills = list(set(required_skills) - set(verified_skills))

        recommendations.append({
            "title": challenge["title"],
            "difficulty": challenge["difficulty"],
            "reward": challenge["reward"],
            "duration": challenge["duration"],
            "match_score": round(match_score, 2),
            "confidence": confidence,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "reason": f"{len(matched_skills)} out of {len(required_skills)} required skills are already verified."
        })

    recommendations.sort(
        key=lambda x: x["match_score"],
        reverse=True
    )

    return {
        "agent": "Challenge Discovery Agent",
        "status": "completed",
        "thinking": [
            f"Loaded {len(challenges)} challenges from knowledge base",
            f"Verified freelancer possesses {len(verified_skills)} skills",
            "Compared required skills with verified skills",
            "Calculated compatibility and confidence scores",
            "Generated explainable recommendations"
        ],
        "recommended_challenges": recommendations[:3]
    }