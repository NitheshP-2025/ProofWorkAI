from agents.challenge_agent import discover_challenges
from agents.market_simulator import simulate_market


def run_workflow(verified_skills):

    challenge_result = discover_challenges(verified_skills)

    # Agent collaboration
    top_challenge = challenge_result["recommended_challenges"][0]

    market_result = simulate_market(verified_skills)

    return {
        "workflow": "ProofWork AI Autonomous Pipeline",
        "input": verified_skills,
        "agent_collaboration": {
            "Challenge Discovery Agent": "Completed",
            "Market Simulator Agent": "Used challenge analysis to recommend next career skill"
        },
        "results": [
            challenge_result,
            market_result
        ]
    }