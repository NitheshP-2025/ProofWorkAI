

import json

def calculate_trust_score(freelancer_data):
    completion_rate = freelancer_data.get("completion_rate", 0)
    quality_score = freelancer_data.get("quality_score", 0)
    on_time_delivery = freelancer_data.get("on_time_delivery", 0)
    client_satisfaction = freelancer_data.get("client_satisfaction", 0)
    repeat_engagements = freelancer_data.get("repeat_engagements", 0)

    trust_score = (
        (completion_rate * 0.30) +
        (quality_score * 0.25) +
        (on_time_delivery * 0.20) +
        (client_satisfaction * 0.15) +
        (repeat_engagements * 0.10)
    )

    return round(trust_score, 2)


def generate_xai_breakdown(freelancer_data, trust_score):

    strengths = []
    weaknesses = []
    suggestions = []

    if freelancer_data["completion_rate"] >= 90:
        strengths.append("✅ Excellent completion rate — clients can rely on you")
    else:
        weaknesses.append("❌ Low completion rate — finish more projects")
        suggestions.append("💡 Complete pending projects to boost trust")

    if freelancer_data["quality_score"] >= 85:
        strengths.append("✅ High quality work — clients are satisfied")
    else:
        weaknesses.append("❌ Quality needs improvement")
        suggestions.append("💡 Focus on delivering cleaner, well-documented work")

    if freelancer_data["on_time_delivery"] >= 90:
        strengths.append("✅ Delivers on time — very reliable")
    else:
        weaknesses.append("❌ Missing deadlines hurts your score")
        suggestions.append("💡 Set realistic deadlines and stick to them")

    if freelancer_data["client_satisfaction"] >= 85:
        strengths.append("✅ Clients are happy with your work")
    else:
        weaknesses.append("❌ Client satisfaction is low")
        suggestions.append("💡 Communicate more with clients during projects")

    if freelancer_data["repeat_engagements"] >= 80:
        strengths.append("✅ Clients keep coming back — strong loyalty")
    else:
        weaknesses.append("❌ Low repeat clients")
        suggestions.append("💡 Follow up with past clients for new projects")

    breakdown = {
        "trust_score": trust_score,
        "verdict": "High Trust ⭐" if trust_score >= 80
                   else "Medium Trust ⚠️" if trust_score >= 60
                   else "Low Trust ❌",
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions
    }
    return breakdown


def run_trust_agent(freelancer_data):
    trust_score = calculate_trust_score(freelancer_data)
    xai_breakdown = generate_xai_breakdown(freelancer_data, trust_score)
    return xai_breakdown


if __name__ == "__main__":
    print("=== ProofWork AI - Trust Score Agent ===\n")

    completion_rate = float(input("Enter Completion Rate (0-100): "))
    quality_score = float(input("Enter Quality Score (0-100): "))
    on_time_delivery = float(input("Enter On-Time Delivery (0-100): "))
    client_satisfaction = float(input("Enter Client Satisfaction (0-100): "))
    repeat_engagements = float(input("Enter Repeat Engagements (0-100): "))

    sample = {
        "completion_rate": completion_rate,
        "quality_score": quality_score,
        "on_time_delivery": on_time_delivery,
        "client_satisfaction": client_satisfaction,
        "repeat_engagements": repeat_engagements
    }

    result = run_trust_agent(sample)
    print(json.dumps(result, indent=2))
