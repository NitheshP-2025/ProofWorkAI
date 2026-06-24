import streamlit as st
import plotly.graph_objects as go
import json
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

from agents.trust_score_agent import run_trust_agent
from agents.challenge_discovery_agent import run_challenge_agent
from agents.skill_verification_agent import run_verification_agent
from agents.proposal_agent import run_proposal_agent

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e3a8a);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #1e40af);
}

[data-testid="stSidebar"] * {
    color: white;
}

.stTextInput input,
.stTextArea textarea {
    background-color: white;
    color: black;
    border-radius: 10px;
}

.stTextInput label,
.stTextArea label,
.stSlider label {
    color: white;
}

div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.08);
    padding: 15px;
    border-radius: 15px;
}

.stButton>button {
    width: 100%;
    border-radius: 10px;
    height: 3em;
}
</style>
""", unsafe_allow_html=True)


def main():

    st.set_page_config(
        page_title="ProofWork AI",
        page_icon="🤖",
        layout="wide"
    )

    st.markdown("""
# 🤖 ProofWork AI
### Trust First Agentic Freelance Marketplace

Verify Skills • Build Trust • Grow Careers
""")


    c1,c2,c3 = st.columns(3)

    c1.metric("🤖 Active Agents", "6")
    c2.metric("🔐 Trust Model", "XAI Powered")
    c3.metric("⚡ Verification", "AI Based")


    st.info(
        "🤖 AI Agents Activated: Trust • Verification • Market • Proposal"
    )


    st.markdown("""
### 🔄 AI Workflow

Profile → Challenge → Verification → Trust Score → Opportunities → Proposal
""")


    st.divider()


    with st.sidebar:

        st.header("👤 Freelancer Profile")

        name = st.text_input("Your Name")

        skills_input = st.text_input(
            "Your Skills",
            "Python, Machine Learning, SQL"
        )

        freelancer_skills = [
            s.strip()
            for s in skills_input.split(",")
        ]


        st.subheader("📊 Performance Metrics")

        completion_rate = st.slider("Completion Rate %",0,100,90)
        quality_score = st.slider("Quality Score %",0,100,85)
        on_time = st.slider("On Time Delivery %",0,100,92)
        satisfaction = st.slider("Client Satisfaction %",0,100,88)
        repeat = st.slider("Repeat Engagements %",0,100,80)



    submission_text = st.text_area(
        "📝 Submit Challenge Work Description"
    )


    project_requirement = st.text_input(
        "🎯 Project Requirement"
    )



    if st.button("🚀 Run ProofWork AI"):


        with st.spinner("AI Agents analyzing profile..."):


            freelancer_data = {

                "completion_rate": completion_rate,
                "quality_score": quality_score,
                "on_time_delivery": on_time,
                "client_satisfaction": satisfaction,
                "repeat_engagements": repeat

            }


            trust_result = run_trust_agent(
                freelancer_data
            )


            score = trust_result["trust_score"]


            tabs = st.tabs(
                [
                    "🏆 Trust Score",
                    "✅ Skill Verification",
                    "📈 Market Growth",
                    "✍️ Proposal"
                ]
            )



            with tabs[0]:

                st.header("🏆 Trust Score")

                col1,col2 = st.columns(2)

                with col1:

                    st.metric(
                        "Trust Score",
                        f"{score}/100"
                    )

                    st.progress(score/100)

                    st.success(
                        trust_result["verdict"]
                    )


                with col2:

                    st.subheader("XAI Breakdown")

                    for key,val in trust_result["breakdown"].items():

                        st.write(
                            f"✓ {key}: {val}"
                        )


                    with st.expander("Why did AI give this score?"):

                        st.write(
                            "Score is calculated using completion rate, quality score, delivery performance, satisfaction and repeat engagements."
                        )



            with tabs[1]:

                st.header("✅ Skill Verification")


                with open("data/mock_challenges.json") as f:

                    challenges = json.load(f)


                verification_result = run_verification_agent(
                    submission_text,
                    freelancer_skills,
                    challenges
                )


                verification = verification_result["skill_verification"]


                c1,c2,c3 = st.columns(3)

                c1.metric("Code Quality", f"{verification['code_quality']}%")
                c2.metric("Documentation", f"{verification['documentation']}%")
                c3.metric("Security", f"{verification['security']}%")


                st.info(
                    verification["status"]
                )



            with tabs[2]:

                st.header("🚀 Market Opportunity Simulator")


                challenge_result = run_challenge_agent(
                    freelancer_skills
                )


                simulator = challenge_result["market_simulator"]


                labels = ["Current"] + [
                    s["learn_skill"]
                    for s in simulator["simulation"]
                ]


                values = [
                    simulator["current_opportunities"]
                ] + [
                    s["new_opportunities"]
                    for s in simulator["simulation"]
                ]


                fig = go.Figure(
                    go.Bar(
                        x=labels,
                        y=values
                    )
                )


                fig.update_layout(
                    title="Future Opportunities",
                    template="plotly_dark"
                )


                st.plotly_chart(
                    fig,
                    use_container_width=True
                )



            with tabs[3]:

                st.header("✍️ Personalized Proposal")


                if project_requirement:


                    verified = freelancer_skills


                    proposal_result = run_proposal_agent(
                        name,
                        verified,
                        project_requirement,
                        score
                    )


                    proposal = proposal_result["proposal"]


                    st.text_area(
                        "Generated Proposal",
                        proposal,
                        height=200
                    )


                    st.download_button(
                        "📥 Download Proposal",
                        proposal,
                        file_name="proposal.txt"
                    )


                else:

                    st.warning(
                        "Enter project requirement"
                    )



if __name__ == "__main__":
    main()
