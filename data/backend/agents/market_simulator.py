import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKET_FILE = os.path.join(BASE_DIR, "data", "market.json")

with open(MARKET_FILE, "r") as file:
    market = json.load(file)


def simulate_market(verified_skills):

    # Current opportunity score
    current_score = sum(
        market.get(skill, 0)
        for skill in verified_skills
    )

    best_skill = None
    best_future_score = current_score
    best_growth = 0

    # Try adding every missing skill
    for skill, value in market.items():

        if skill not in verified_skills:

            future_score = current_score + value
            growth = future_score - current_score

            if growth > best_growth:
                best_growth = growth
                best_future_score = future_score
                best_skill = skill

    growth_percentage = round(
        (best_growth / current_score) * 100,
        2
    ) if current_score else 0

    return {
        "agent": "Market Simulator Agent",
        "status": "completed",
        "thinking": [
            f"Current opportunity score = {current_score}",
            "Simulated every missing skill",
            "Compared opportunity growth",
            f"Selected {best_skill} as highest ROI skill"
        ],
        "simulation": {
            "current_score": current_score,
            "recommended_skill": best_skill,
            "future_score": best_future_score,
            "growth_percentage": growth_percentage
        }
    }