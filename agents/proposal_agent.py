# proposal_agent.py

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def run_proposal_agent(freelancer_name, verified_skills, project_requirement, trust_score):

    strengths_text = ", ".join(verified_skills)

    prompt = f"""
    Create a professional freelance proposal.

    Freelancer Name:
    {freelancer_name}

    Verified Skills:
    {strengths_text}

    Trust Score:
    {trust_score}/100

    Project Requirement:
    {project_requirement}

    Rules:
    - Maximum 5 sentences
    - Professional tone
    - Highlight verified skills
    - Use trust score as credibility
    - End with confidence and willingness to deliver
    """

    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama-3.1-8b-instant"
    )

    proposal = response.choices[0].message.content

    return {
        "proposal": proposal,
        "agent": "Proposal Assistant Agent",
        "status": "Generated Successfully"
    }
