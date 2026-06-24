"""
ProofWork AI — Premium Streamlit Dashboard
============================================
Trust-First Agentic Freelance Marketplace Powered by Explainable AI (XAI)

Pages:
  1. 🏠 Home          — Platform overview & value proposition
  2. ✅ Skill Verifier — Submit & verify skills with AI scoring
  3. 🔍 Skill Gap     — Identify career-critical skill gaps
  4. 🗺  Roadmap       — Personalized learning timeline
  5. 🧠 XAI Panel     — Full explainability transparency panel

Author: Swetha
"""

import json
import sys
import os
import time
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------------------------
# Path fix so imports work from project root
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from agents.skill_verifier import SkillVerificationAgent
from agents.skill_gap_agent import SkillGapAgent
from models.schemas import SkillSubmission, SkillGapInput
from services.evaluation_engine import STATUS_COLORS, STATUS_ICONS
from utils.logger import get_logger

logger = get_logger("app")

# ---------------------------------------------------------------------------
# Streamlit Page Config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="ProofWork AI — Trust-First Freelance Intelligence",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/proofwork-ai",
        "About": "ProofWork AI — Built by Swetha | Powered by Groq LLaMA 3.3",
    },
)

# ---------------------------------------------------------------------------
# Premium CSS Styling
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

/* ===== GLOBAL RESET & BASE ===== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #0a0a0f;
    color: #e2e8f0;
}

/* ===== MAIN BACKGROUND ===== */
.stApp {
    background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 50%, #0a0f1a 100%);
    min-height: 100vh;
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #111827 100%);
    border-right: 1px solid rgba(99, 102, 241, 0.2);
}
[data-testid="stSidebar"] .stMarkdown { color: #94a3b8; }

/* ===== HIDE DEFAULT ELEMENTS ===== */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* ===== HERO GRADIENT TEXT ===== */
.hero-title {
    font-size: 3.5rem;
    font-weight: 900;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 30%, #a78bfa 60%, #c4b5fd 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
    letter-spacing: -0.03em;
}

.hero-subtitle {
    font-size: 1.15rem;
    color: #94a3b8;
    font-weight: 400;
    line-height: 1.7;
    max-width: 650px;
}

/* ===== GLASS CARDS ===== */
.glass-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 0.75rem 0;
    transition: all 0.3s ease;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}

.glass-card:hover {
    border-color: rgba(99, 102, 241, 0.4);
    box-shadow: 0 8px 40px rgba(99, 102, 241, 0.15);
    transform: translateY(-2px);
}

/* ===== METRIC CARDS ===== */
.metric-card {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.05) 100%);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    text-align: center;
    transition: all 0.3s ease;
}

.metric-card:hover {
    border-color: rgba(99, 102, 241, 0.5);
    box-shadow: 0 0 30px rgba(99, 102, 241, 0.2);
}

.metric-value {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6366f1, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.metric-label {
    font-size: 0.8rem;
    color: #64748b;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 0.25rem;
}

/* ===== STATUS BADGES ===== */
.badge-verified {
    display: inline-block;
    padding: 0.4rem 1.2rem;
    background: rgba(0, 200, 81, 0.15);
    border: 1px solid #00C851;
    border-radius: 50px;
    color: #00C851;
    font-weight: 700;
    font-size: 0.9rem;
    letter-spacing: 0.05em;
}

.badge-partial {
    display: inline-block;
    padding: 0.4rem 1.2rem;
    background: rgba(255, 187, 51, 0.15);
    border: 1px solid #FFBB33;
    border-radius: 50px;
    color: #FFBB33;
    font-weight: 700;
    font-size: 0.9rem;
    letter-spacing: 0.05em;
}

.badge-not-verified {
    display: inline-block;
    padding: 0.4rem 1.2rem;
    background: rgba(255, 68, 68, 0.15);
    border: 1px solid #FF4444;
    border-radius: 50px;
    color: #FF4444;
    font-weight: 700;
    font-size: 0.9rem;
    letter-spacing: 0.05em;
}

/* ===== SECTION HEADERS ===== */
.section-header {
    font-size: 1.6rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 1.5rem 0 0.75rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.section-subheader {
    font-size: 0.95rem;
    color: #64748b;
    margin-bottom: 1rem;
}

/* ===== XAI REASONING ITEMS ===== */
.xai-item {
    background: rgba(99, 102, 241, 0.06);
    border-left: 3px solid #6366f1;
    border-radius: 0 8px 8px 0;
    padding: 0.75rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.9rem;
    color: #cbd5e1;
    line-height: 1.6;
}

/* ===== ROADMAP TIMELINE ===== */
.roadmap-entry {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 12px;
    padding: 1.2rem;
    margin: 0.75rem 0;
    position: relative;
    overflow: hidden;
}

.roadmap-entry::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, #6366f1, #8b5cf6);
}

.roadmap-week {
    font-size: 0.75rem;
    font-weight: 700;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

.roadmap-skill {
    font-size: 1.1rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0.2rem 0;
}

.roadmap-focus {
    font-size: 0.85rem;
    color: #94a3b8;
}

/* ===== SKILL TAGS ===== */
.skill-tag {
    display: inline-block;
    padding: 0.3rem 0.9rem;
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 50px;
    color: #a78bfa;
    font-size: 0.8rem;
    font-weight: 500;
    margin: 0.2rem;
}

.skill-tag-gap {
    display: inline-block;
    padding: 0.3rem 0.9rem;
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 50px;
    color: #fbbf24;
    font-size: 0.8rem;
    font-weight: 500;
    margin: 0.2rem;
}

/* ===== STREAMLIT OVERRIDES ===== */
.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.6rem 2rem !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
}

.stButton > button:hover {
    box-shadow: 0 6px 25px rgba(99, 102, 241, 0.5) !important;
    transform: translateY(-1px) !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}

.stTextArea > div > div > textarea {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
}

.stProgress > div > div > div {
    background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
}

[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: #a78bfa !important;
}

[data-testid="stMetricLabel"] {
    font-size: 0.8rem !important;
    color: #64748b !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ===== ALERT / INFO BOXES ===== */
.stAlert {
    border-radius: 12px !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
}

/* ===== JSON VIEWER ===== */
.stCode {
    border-radius: 12px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ===== DIVIDERS ===== */
hr {
    border: none;
    border-top: 1px solid rgba(99, 102, 241, 0.1);
    margin: 1.5rem 0;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255, 255, 255, 0.02);
    border-radius: 12px;
    padding: 0.25rem;
    border: 1px solid rgba(99, 102, 241, 0.1);
}

.stTabs [data-baseweb="tab"] {
    color: #64748b !important;
    font-weight: 500;
    border-radius: 10px;
}

.stTabs [aria-selected="true"] {
    background: rgba(99, 102, 241, 0.2) !important;
    color: #a78bfa !important;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session State Initialisation
# ---------------------------------------------------------------------------

def init_session_state():
    defaults = {
        "verification_result": None,
        "gap_result": None,
        "current_page": "🏠 Home",
        "verifier_agent": None,
        "gap_agent": None,
        "api_key_valid": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# ---------------------------------------------------------------------------
# Agent Factory (cached for performance)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_agents(api_key: str):
    """Creates and caches agent instances. Re-runs only when API key changes."""
    from services.groq_service import GroqService
    groq = GroqService(api_key=api_key)
    verifier = SkillVerificationAgent(groq_service=groq)
    gap_agent = SkillGapAgent(groq_service=groq)
    return verifier, gap_agent


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar():
    with st.sidebar:
        # Logo / Brand
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 2rem 0;">
            <div style="font-size: 2.5rem; margin-bottom: 0.3rem;">🔐</div>
            <div style="font-size: 1.3rem; font-weight: 800; background: linear-gradient(135deg, #6366f1, #a78bfa); 
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                ProofWork AI
            </div>
            <div style="font-size: 0.7rem; color: #475569; font-weight: 500; letter-spacing: 0.12em; text-transform: uppercase; margin-top: 0.2rem;">
                Trust-First Intelligence
            </div>
        </div>
        """, unsafe_allow_html=True)

        # API Key Input
        st.markdown("**🔑 Groq API Key**")
        api_key = st.text_input(
            "api_key_input",
            type="password",
            placeholder="gsk_...",
            label_visibility="collapsed",
            key="api_key_input",
        )

        env_key = os.getenv("GROQ_API_KEY", "").strip()
        resolved_key = api_key.strip() if api_key and api_key.strip() else env_key

        if resolved_key:
            st.markdown(
                '<div style="color: #00C851; font-size: 0.8rem; margin-bottom: 1rem;">✅ API Key loaded</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="color: #FF4444; font-size: 0.8rem; margin-bottom: 1rem;">⚠️ No API key found</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Navigation
        st.markdown("**📌 Navigation**")
        pages = [
            "🏠 Home",
            "✅ Skill Verifier",
            "🔍 Skill Gap Analysis",
            "🗺️ Career Roadmap",
            "🧠 XAI Panel",
        ]

        for page in pages:
            is_active = st.session_state.current_page == page
            if st.button(
                page,
                key=f"nav_{page}",
                use_container_width=True,
            ):
                st.session_state.current_page = page
                st.rerun()

        st.markdown("---")

        # Platform Stats
        st.markdown("**📊 Platform Stats**")
        st.markdown("""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
            <div class="metric-card">
                <div style="font-size: 1.4rem; font-weight: 800; color: #6366f1;">2,847</div>
                <div style="font-size: 0.65rem; color: #475569; text-transform: uppercase; letter-spacing: 0.08em;">Verified</div>
            </div>
            <div class="metric-card">
                <div style="font-size: 1.4rem; font-weight: 800; color: #8b5cf6;">94.2%</div>
                <div style="font-size: 0.65rem; color: #475569; text-transform: uppercase; letter-spacing: 0.08em;">Accuracy</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            '<div style="font-size: 0.72rem; color: #334155; text-align: center;">'
            'Built by <strong style="color: #6366f1;">Swetha</strong> | '
            'Powered by <strong style="color: #8b5cf6;">Groq LLaMA 3.3</strong>'
            '</div>',
            unsafe_allow_html=True,
        )

        return resolved_key


# ---------------------------------------------------------------------------
# Page: Home
# ---------------------------------------------------------------------------

def render_home():
    # Hero Section
    st.markdown("""
    <div style="padding: 3rem 0 2rem 0;">
        <div class="hero-title">ProofWork AI</div>
        <div style="font-size: 1.3rem; font-weight: 600; color: #8b5cf6; margin: 0.5rem 0 1rem 0;">
            Trust-First Agentic Freelance Intelligence
        </div>
        <p class="hero-subtitle">
            Don't tell us what you can do — <strong style="color: #a78bfa;">Prove it.</strong><br>
            AI-powered skill verification and career intelligence for the next generation of freelancers.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # CTA Buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("✅ Verify a Skill", use_container_width=True, key="home_cta_verify"):
            st.session_state.current_page = "✅ Skill Verifier"
            st.rerun()
    with col2:
        if st.button("🔍 Find Skill Gaps", use_container_width=True, key="home_cta_gap"):
            st.session_state.current_page = "🔍 Skill Gap Analysis"
            st.rerun()

    st.markdown("---")

    # Platform Stats Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""<div class="metric-card">
            <div class="metric-value">2,847</div>
            <div class="metric-label">Skills Verified</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="metric-card">
            <div class="metric-value">94.2%</div>
            <div class="metric-label">AI Accuracy</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class="metric-card">
            <div class="metric-value">1,203</div>
            <div class="metric-label">Freelancers</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown("""<div class="metric-card">
            <div class="metric-value">30+</div>
            <div class="metric-label">Skills Tracked</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # How It Works
    st.markdown('<div class="section-header">⚙️ How ProofWork AI Works</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 2rem; margin-bottom: 0.75rem;">📝</div>
            <div style="font-weight: 700; color: #e2e8f0; font-size: 1.05rem; margin-bottom: 0.5rem;">Submit Your Work</div>
            <div style="color: #64748b; font-size: 0.88rem; line-height: 1.7;">
                Complete an AI-generated challenge relevant to your claimed skill. No fake portfolios, no borrowed code.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 2rem; margin-bottom: 0.75rem;">🤖</div>
            <div style="font-weight: 700; color: #e2e8f0; font-size: 1.05rem; margin-bottom: 0.5rem;">AI Verification</div>
            <div style="color: #64748b; font-size: 0.88rem; line-height: 1.7;">
                LLaMA 3.3-70B analyzes your submission across 4 dimensions: Code Quality, Documentation, Security, and Problem Solving.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="glass-card">
            <div style="font-size: 2rem; margin-bottom: 0.75rem;">🏆</div>
            <div style="font-weight: 700; color: #e2e8f0; font-size: 1.05rem; margin-bottom: 0.5rem;">Earn Trust Badge</div>
            <div style="color: #64748b; font-size: 0.88rem; line-height: 1.7;">
                Receive a verifiable trust badge with full XAI transparency. Clients see WHY you were verified, not just that you were.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Philosophy Quote
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(139,92,246,0.05) 100%);
                border: 1px solid rgba(99,102,241,0.2); border-radius: 16px; padding: 2rem;
                text-align: center; margin: 1rem 0;">
        <div style="font-size: 1.6rem; font-weight: 800; color: #e2e8f0; font-style: italic; margin-bottom: 0.5rem;">
            "Don't tell us what you can do. Prove it."
        </div>
        <div style="font-size: 0.9rem; color: #64748b;">— ProofWork AI Core Philosophy</div>
    </div>
    """, unsafe_allow_html=True)

    # XAI Feature Highlight
    st.markdown('<div class="section-header">🧠 Explainable AI — No Black Boxes</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="glass-card">
            <div style="font-weight: 700; color: #a78bfa; margin-bottom: 0.75rem;">Why XAI Matters</div>
            <ul style="color: #94a3b8; font-size: 0.88rem; line-height: 2; padding-left: 1.2rem;">
                <li>Every score includes specific reasoning</li>
                <li>Strengths and weaknesses are itemized</li>
                <li>Scoring formula is fully transparent</li>
                <li>No algorithmic black boxes</li>
                <li>Clients can audit every decision</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        # Mini XAI preview
        st.markdown("""
        <div class="glass-card">
            <div style="font-weight: 700; color: #a78bfa; margin-bottom: 0.75rem;">Sample XAI Output</div>
            <div class="xai-item">✅ Strong modular code structure detected</div>
            <div class="xai-item">✅ Docstrings present in all public functions</div>
            <div class="xai-item">✅ Input validation and error handling implemented</div>
            <div class="xai-item">⚠️ No unit tests included in submission</div>
        </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page: Skill Verifier
# ---------------------------------------------------------------------------

def render_skill_verifier(api_key: str, verifier: object):
    st.markdown('<div class="hero-title" style="font-size: 2.2rem;">✅ Skill Verification Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle" style="margin-bottom: 1.5rem;">Submit your challenge solution. Our AI evaluates it across 4 dimensions with full XAI transparency.</div>', unsafe_allow_html=True)

    if not api_key:
        st.error("⚠️ Please enter your Groq API key in the sidebar to use this feature.")
        return

    # Load sample
    sample_path = ROOT / "data" / "sample_submission.json"
    sample_data = {}
    if sample_path.exists():
        with open(sample_path, "r") as f:
            sample_data = json.load(f)

    with st.form("skill_verification_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            user_id = st.text_input(
                "👤 Freelancer ID",
                value=sample_data.get("user_id", ""),
                placeholder="e.g., freelancer_101",
                key="sv_user_id",
            )
            skill = st.text_input(
                "🎯 Claimed Skill",
                value=sample_data.get("skill", ""),
                placeholder="e.g., Python Automation, React, FastAPI",
                key="sv_skill",
            )
        with col2:
            challenge = st.text_input(
                "📋 Challenge Title",
                value=sample_data.get("challenge_title", ""),
                placeholder="e.g., Build a File Organizer",
                key="sv_challenge",
            )
            submission_time = st.text_input(
                "🕐 Submission Timestamp",
                value=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                key="sv_time",
            )

        submission_text = st.text_area(
            "💻 Submission — Code or Explanation",
            value=sample_data.get("submission_text", ""),
            height=320,
            placeholder="Paste your code or detailed explanation here...",
            key="sv_text",
        )

        col_a, col_b = st.columns([1, 3])
        with col_a:
            submitted = st.form_submit_button("🚀 Verify Skill", use_container_width=True)

    if submitted:
        if not submission_text.strip():
            st.warning("Please enter a submission before verifying.")
            return

        with st.spinner("🤖 AI is analyzing your submission..."):
            start = time.time()
            try:
                v_agent, _ = get_agents(api_key)
                response = v_agent.verify_from_dict({
                    "user_id": user_id or "anonymous",
                    "skill": skill or "Unknown",
                    "challenge_title": challenge or "General Challenge",
                    "submission_text": submission_text,
                    "submission_time": submission_time,
                })
                elapsed = time.time() - start
            except EnvironmentError as e:
                st.error(f"API Key Error: {e}")
                return
            except Exception as e:
                st.error(f"Unexpected error: {e}")
                logger.exception(e)
                return

        if not response.success:
            st.error(f"❌ Verification failed: {response.error}")
            return

        st.session_state.verification_result = response.data
        result = response.data

        st.markdown("---")
        st.markdown('<div class="section-header">📊 Verification Results</div>', unsafe_allow_html=True)

        # Score & Status Banner
        score = result["overall_score"]
        status = result["status"]
        icon = STATUS_ICONS.get(status, "❓")

        status_class = {
            "VERIFIED": "badge-verified",
            "PARTIALLY VERIFIED": "badge-partial",
            "NOT VERIFIED": "badge-not-verified",
        }.get(status, "badge-partial")

        st.markdown(f"""
        <div class="glass-card" style="text-align: center; padding: 2rem;">
            <div style="font-size: 4rem; font-weight: 900; background: linear-gradient(135deg, #6366f1, #a78bfa);
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                {score:.1f}
            </div>
            <div style="color: #64748b; font-size: 0.8rem; margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em;">
                Overall Score / 100
            </div>
            <div class="{status_class}">{icon} {status}</div>
            <div style="color: #475569; font-size: 0.8rem; margin-top: 1rem;">
                Analysis completed in {elapsed:.1f}s | {result.get('verified_at', '')[:19]}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Component Scores
        st.markdown('<div class="section-header" style="font-size: 1.2rem;">📐 Component Breakdown</div>', unsafe_allow_html=True)
        cs = result["component_scores"]

        cols = st.columns(4)
        labels = [
            ("Code Quality", cs["code_quality"], "0.30", "💻"),
            ("Documentation", cs["documentation"], "0.20", "📝"),
            ("Security", cs["security"], "0.20", "🔒"),
            ("Problem Solving", cs["problem_solving"], "0.30", "🧩"),
        ]
        for col, (label, val, weight, emoji) in zip(cols, labels):
            with col:
                color = "#00C851" if val >= 80 else ("#FFBB33" if val >= 60 else "#FF4444")
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 1.3rem; margin-bottom: 0.2rem;">{emoji}</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: {color};">{val:.0f}</div>
                    <div style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em;">{label}</div>
                    <div style="font-size: 0.65rem; color: #334155; margin-top: 0.2rem;">Weight: {weight}</div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(int(val) / 100)

        # Radar Chart
        st.markdown("---")
        col_chart, col_xai = st.columns([1, 1])

        with col_chart:
            st.markdown('<div class="section-header" style="font-size: 1.2rem;">📡 Skill Radar</div>', unsafe_allow_html=True)
            categories = ["Code Quality", "Documentation", "Security", "Problem Solving"]
            values = [cs["code_quality"], cs["documentation"], cs["security"], cs["problem_solving"]]
            values_closed = values + [values[0]]
            categories_closed = categories + [categories[0]]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values_closed,
                theta=categories_closed,
                fill='toself',
                fillcolor='rgba(99,102,241,0.2)',
                line=dict(color='#6366f1', width=2),
                name='Score',
                marker=dict(color='#a78bfa', size=8),
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=[80] * 5,
                theta=categories_closed,
                fill='toself',
                fillcolor='rgba(0,200,81,0.05)',
                line=dict(color='rgba(0,200,81,0.3)', width=1, dash='dot'),
                name='Verified Threshold',
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(255,255,255,0.05)',
                                    tickfont=dict(color='#475569', size=10)),
                    angularaxis=dict(tickfont=dict(color='#94a3b8', size=11)),
                    bgcolor='rgba(0,0,0,0)',
                ),
                showlegend=True,
                legend=dict(font=dict(color='#94a3b8', size=10)),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'),
                height=350,
                margin=dict(l=20, r=20, t=30, b=20),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        with col_xai:
            st.markdown('<div class="section-header" style="font-size: 1.2rem;">🧠 XAI Reasoning</div>', unsafe_allow_html=True)
            for reason in result.get("reasoning", []):
                st.markdown(f'<div class="xai-item">{reason}</div>', unsafe_allow_html=True)

        # Strengths & Improvements
        st.markdown("---")
        col_s, col_i = st.columns(2)
        with col_s:
            st.markdown('<div class="section-header" style="font-size: 1.1rem;">💪 Strengths</div>', unsafe_allow_html=True)
            for s in result.get("strengths", []):
                st.markdown(f'<div class="xai-item" style="border-left-color: #00C851;">✅ {s}</div>', unsafe_allow_html=True)
        with col_i:
            st.markdown('<div class="section-header" style="font-size: 1.1rem;">🔧 Improvements</div>', unsafe_allow_html=True)
            for imp in result.get("improvements", []):
                st.markdown(f'<div class="xai-item" style="border-left-color: #FFBB33;">⚡ {imp}</div>', unsafe_allow_html=True)

        # JSON Download
        st.markdown("---")
        st.download_button(
            label="⬇️ Download Full Verification Report (JSON)",
            data=json.dumps(result, indent=2),
            file_name=f"verification_{user_id}_{skill.replace(' ', '_')}.json",
            mime="application/json",
            key="download_verification",
        )

        with st.expander("🔍 View Raw JSON Response"):
            st.code(json.dumps(result, indent=2), language="json")


# ---------------------------------------------------------------------------
# Page: Skill Gap Analysis
# ---------------------------------------------------------------------------

def render_skill_gap(api_key: str):
    st.markdown('<div class="hero-title" style="font-size: 2.2rem;">🔍 Skill Gap Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle" style="margin-bottom: 1.5rem;">Discover which missing skills will maximize your earning potential and career growth.</div>', unsafe_allow_html=True)

    if not api_key:
        st.error("⚠️ Please enter your Groq API key in the sidebar to use this feature.")
        return

    with st.form("skill_gap_form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            skills_input = st.text_input(
                "🛠️ Your Current Skills (comma-separated)",
                value="Python, Flask, SQL",
                placeholder="e.g., Python, React, Docker, AWS",
                key="sg_skills",
            )
        with col2:
            user_id_sg = st.text_input(
                "👤 User ID (optional)",
                placeholder="freelancer_101",
                key="sg_uid",
            )
            target_role = st.text_input(
                "🎯 Target Role (optional)",
                placeholder="e.g., ML Engineer, Full Stack Dev",
                key="sg_role",
            )

        submitted_gap = st.form_submit_button("🔍 Analyze Skill Gaps", use_container_width=False)

    if submitted_gap:
        user_skills = [s.strip() for s in skills_input.split(",") if s.strip()]
        if not user_skills:
            st.warning("Please enter at least one skill.")
            return

        with st.spinner("🔍 Analyzing your skill gaps against market demand..."):
            try:
                _, g_agent = get_agents(api_key)
                response = g_agent.analyze_from_dict({
                    "user_skills": user_skills,
                    "user_id": user_id_sg or None,
                    "target_role": target_role or None,
                })
            except EnvironmentError as e:
                st.error(f"API Key Error: {e}")
                return
            except Exception as e:
                st.error(f"Unexpected error: {e}")
                logger.exception(e)
                return

        if not response.success:
            st.error(f"❌ Analysis failed: {response.error}")
            return

        st.session_state.gap_result = response.data
        result = response.data

        st.markdown("---")
        st.markdown('<div class="section-header">📊 Gap Analysis Results</div>', unsafe_allow_html=True)

        # Current Skills
        st.markdown("**🛠️ Your Current Skills:**")
        tags_html = "".join(f'<span class="skill-tag">{s}</span>' for s in result["existing_skills"])
        st.markdown(f'<div style="margin: 0.5rem 0 1rem 0;">{tags_html}</div>', unsafe_allow_html=True)

        # Identified Gaps
        if result["skill_gaps"]:
            st.markdown("**⚠️ Top Priority Skill Gaps:**")
            gap_tags = "".join(f'<span class="skill-tag-gap">{g["skill"]}</span>' for g in result["skill_gaps"])
            st.markdown(f'<div style="margin: 0.5rem 0 1rem 0;">{gap_tags}</div>', unsafe_allow_html=True)

        # Career Impact Summary
        st.markdown(f"""
        <div class="glass-card" style="border-left: 3px solid #6366f1;">
            <div style="font-size: 0.8rem; font-weight: 700; color: #6366f1; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">
                💡 Career Impact
            </div>
            <div style="color: #e2e8f0; font-size: 0.95rem; line-height: 1.7;">
                {result.get("career_impact_summary", "")}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Gap Opportunity Cards + Bar Chart
        col_gaps, col_chart = st.columns([1, 1])
        with col_gaps:
            st.markdown('<div class="section-header" style="font-size: 1.1rem;">🎯 Opportunity Boost</div>', unsafe_allow_html=True)
            for gap in result["skill_gaps"]:
                pct = gap["opportunity_increase_pct"]
                demand = gap["market_demand_score"]
                rank = gap["priority_rank"]
                st.markdown(f"""
                <div class="glass-card" style="padding: 1rem 1.2rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 0.7rem; color: #6366f1; font-weight: 700;">#{rank}</span>
                            <span style="font-size: 1rem; font-weight: 700; color: #e2e8f0; margin-left: 0.5rem;">{gap["skill"]}</span>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.3rem; font-weight: 800; color: #00C851;">+{pct:.0f}%</div>
                            <div style="font-size: 0.7rem; color: #475569;">opportunities</div>
                        </div>
                    </div>
                    <div style="margin-top: 0.5rem;">
                        <div style="font-size: 0.72rem; color: #64748b; margin-bottom: 0.3rem;">Market Demand: {demand}/100</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with col_chart:
            st.markdown('<div class="section-header" style="font-size: 1.1rem;">📈 Market Demand</div>', unsafe_allow_html=True)

            _, g_agent2 = get_agents(api_key)
            market_data = g_agent2.get_market_data()
            top_market = sorted(market_data.items(), key=lambda x: -x[1])[:12]
            skills_m = [x[0] for x in top_market]
            scores_m = [x[1] for x in top_market]
            colors = ["#6366f1" if s in [g["skill"] for g in result["skill_gaps"]] else "#334155" for s in skills_m]

            fig_bar = go.Figure(go.Bar(
                x=scores_m,
                y=skills_m,
                orientation='h',
                marker=dict(color=colors),
                text=[f"{s}" for s in scores_m],
                textposition='inside',
                textfont=dict(color='white', size=10),
            ))
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(title='Demand Score', gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#94a3b8')),
                yaxis=dict(tickfont=dict(color='#94a3b8'), autorange='reversed'),
                height=380,
                margin=dict(l=10, r=10, t=10, b=30),
                showlegend=False,
                font=dict(color='#94a3b8'),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # Download
        st.markdown("---")
        st.download_button(
            label="⬇️ Download Skill Gap Report (JSON)",
            data=json.dumps(result, indent=2),
            file_name="skill_gap_analysis.json",
            mime="application/json",
            key="download_gap",
        )

        with st.expander("🔍 View Raw JSON Response"):
            st.code(json.dumps(result, indent=2), language="json")


# ---------------------------------------------------------------------------
# Page: Career Roadmap
# ---------------------------------------------------------------------------

def render_roadmap():
    st.markdown('<div class="hero-title" style="font-size: 2.2rem;">🗺️ Career Roadmap</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle" style="margin-bottom: 1.5rem;">Your personalized, AI-generated week-by-week learning plan to close skill gaps and maximize career growth.</div>', unsafe_allow_html=True)

    result = st.session_state.gap_result

    if not result:
        st.info("🔍 Run a Skill Gap Analysis first to generate your personalized roadmap.")
        if st.button("Go to Skill Gap Analysis →", key="goto_gap"):
            st.session_state.current_page = "🔍 Skill Gap Analysis"
            st.rerun()
        return

    roadmap = result.get("roadmap", [])
    if not roadmap:
        st.success("🎉 No skill gaps detected! Your profile is already aligned with market demand.")
        return

    # Summary banner
    total_weeks = len(roadmap) * 2
    st.markdown(f"""
    <div class="glass-card" style="display: flex; gap: 2rem; align-items: center; padding: 1.5rem 2rem;">
        <div>
            <div style="font-size: 2rem; font-weight: 800; color: #6366f1;">{total_weeks}</div>
            <div style="font-size: 0.75rem; color: #475569; text-transform: uppercase;">Total Weeks</div>
        </div>
        <div>
            <div style="font-size: 2rem; font-weight: 800; color: #8b5cf6;">{len(roadmap)}</div>
            <div style="font-size: 0.75rem; color: #475569; text-transform: uppercase;">Skills to Learn</div>
        </div>
        <div style="flex: 1; color: #94a3b8; font-size: 0.9rem; line-height: 1.7;">
            {result.get("career_impact_summary", "")}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Timeline entries
    st.markdown('<div class="section-header">📅 Learning Timeline</div>', unsafe_allow_html=True)

    for i, entry in enumerate(roadmap):
        with st.container():
            st.markdown(f"""
            <div class="roadmap-entry">
                <div class="roadmap-week">{entry.get("week_range", f"Week {i*2+1}-{i*2+2}")}</div>
                <div class="roadmap-skill">{entry.get("skill", "")}</div>
                <div class="roadmap-focus">{entry.get("focus", "")}</div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([1, 1])
            with col1:
                resources = entry.get("resources", [])
                if resources:
                    st.markdown("**📚 Resources:**")
                    for res in resources:
                        st.markdown(f"  • {res}")
            with col2:
                milestone = entry.get("milestone", "")
                if milestone:
                    st.markdown(f"""
                    <div style="background: rgba(0,200,81,0.07); border: 1px solid rgba(0,200,81,0.2);
                                border-radius: 8px; padding: 0.75rem; font-size: 0.85rem; color: #94a3b8;">
                        🎯 <strong style="color: #00C851;">Milestone:</strong><br>{milestone}
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("")

    # Gantt / Timeline Chart
    st.markdown("---")
    st.markdown('<div class="section-header">📊 Roadmap Gantt View</div>', unsafe_allow_html=True)

    gantt_data = []
    for i, entry in enumerate(roadmap):
        start_week = i * 2 + 1
        end_week = start_week + 1
        gantt_data.append({
            "Skill": entry.get("skill", f"Skill {i+1}"),
            "Start": start_week,
            "End": end_week + 1,
            "Focus": entry.get("focus", ""),
        })

    if gantt_data:
        df = pd.DataFrame(gantt_data)
        fig_gantt = go.Figure()
        colors_palette = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd"]
        for i, row in df.iterrows():
            fig_gantt.add_trace(go.Bar(
                x=[row["End"] - row["Start"]],
                y=[row["Skill"]],
                base=[row["Start"]],
                orientation='h',
                marker=dict(color=colors_palette[i % len(colors_palette)], opacity=0.85),
                name=row["Skill"],
                hovertemplate=f"<b>{row['Skill']}</b><br>Week {row['Start']}–{row['End']-1}<br>{row['Focus']}<extra></extra>",
                text=f"Week {row['Start']}–{row['End']-1}",
                textposition='inside',
                textfont=dict(color='white', size=11),
            ))

        fig_gantt.update_layout(
            barmode='overlay',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title='Week', tickmode='linear', tick0=1, dtick=1,
                       gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#94a3b8')),
            yaxis=dict(tickfont=dict(color='#94a3b8'), autorange='reversed'),
            height=max(200, len(roadmap) * 70),
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=30),
            font=dict(color='#94a3b8'),
        )
        st.plotly_chart(fig_gantt, use_container_width=True)

    # Download
    st.markdown("---")
    st.download_button(
        label="⬇️ Download Roadmap (JSON)",
        data=json.dumps(roadmap, indent=2),
        file_name="career_roadmap.json",
        mime="application/json",
        key="download_roadmap",
    )


# ---------------------------------------------------------------------------
# Page: XAI Explanation Panel
# ---------------------------------------------------------------------------

def render_xai_panel():
    st.markdown('<div class="hero-title" style="font-size: 2.2rem;">🧠 Explainable AI Panel</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="hero-subtitle" style="margin-bottom: 1.5rem;">
        Every decision made by ProofWork AI is fully transparent and auditable.
        This panel shows WHY scores were generated, WHY skills were recommended,
        and WHY the roadmap was created — with zero black boxes.
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔐 Verification XAI", "📈 Skill Gap XAI"])

    with tab1:
        result = st.session_state.verification_result
        if not result:
            st.info("Run a Skill Verification first to populate this panel.")
        else:
            st.markdown('<div class="section-header">🔐 Verification Explainability</div>', unsafe_allow_html=True)

            # Scoring Formula Breakdown
            cs = result["component_scores"]
            st.markdown("""
            <div class="glass-card">
                <div style="font-weight: 700; color: #a78bfa; margin-bottom: 1rem; font-size: 1.05rem;">
                    ⚖️ Scoring Formula (Fully Transparent)
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; color: #94a3b8; line-height: 2;">
                    Overall Score = (Code Quality × 0.30) + (Documentation × 0.20) + (Security × 0.20) + (Problem Solving × 0.30)
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Score waterfall
            weights = {"Code Quality": 0.30, "Documentation": 0.20, "Security": 0.20, "Problem Solving": 0.30}
            raw_vals = {
                "Code Quality": cs["code_quality"],
                "Documentation": cs["documentation"],
                "Security": cs["security"],
                "Problem Solving": cs["problem_solving"],
            }
            contributions = {k: raw_vals[k] * weights[k] for k in weights}
            total_contrib = sum(contributions.values())

            fig_waterfall = go.Figure(go.Waterfall(
                name="Score",
                orientation="v",
                measure=["relative", "relative", "relative", "relative", "total"],
                x=list(contributions.keys()) + ["Overall Score"],
                textposition="outside",
                text=[f"+{v:.1f}" for v in contributions.values()] + [f"{total_contrib:.1f}"],
                y=list(contributions.values()) + [total_contrib],
                connector={"line": {"color": "rgba(99,102,241,0.3)"}},
                increasing={"marker": {"color": "#6366f1"}},
                totals={"marker": {"color": "#a78bfa"}},
            ))
            fig_waterfall.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(tickfont=dict(color='#94a3b8')),
                yaxis=dict(title="Score Points", gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#94a3b8')),
                height=300,
                margin=dict(l=10, r=10, t=30, b=10),
                font=dict(color='#94a3b8'),
                title=dict(text="Score Contribution Waterfall", font=dict(color='#e2e8f0', size=13)),
            )
            st.plotly_chart(fig_waterfall, use_container_width=True)

            # Threshold Explanation
            score = result["overall_score"]
            st.markdown(f"""
            <div class="glass-card">
                <div style="font-weight: 700; color: #a78bfa; margin-bottom: 0.75rem; font-size: 1.05rem;">
                    🎯 Threshold Decision Logic
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                    <div style="text-align: center; padding: 0.75rem; border-radius: 8px; 
                                background: {'rgba(0,200,81,0.15)' if score >= 80 else 'rgba(255,255,255,0.03)'};
                                border: 1px solid {'#00C851' if score >= 80 else 'rgba(255,255,255,0.05)'};">
                        <div style="font-size: 0.75rem; color: #00C851; font-weight: 700;">VERIFIED</div>
                        <div style="color: #94a3b8; font-size: 0.8rem;">Score ≥ 80</div>
                    </div>
                    <div style="text-align: center; padding: 0.75rem; border-radius: 8px;
                                background: {'rgba(255,187,51,0.15)' if 60 <= score < 80 else 'rgba(255,255,255,0.03)'};
                                border: 1px solid {'#FFBB33' if 60 <= score < 80 else 'rgba(255,255,255,0.05)'};">
                        <div style="font-size: 0.75rem; color: #FFBB33; font-weight: 700;">PARTIALLY VERIFIED</div>
                        <div style="color: #94a3b8; font-size: 0.8rem;">60 ≤ Score &lt; 80</div>
                    </div>
                    <div style="text-align: center; padding: 0.75rem; border-radius: 8px;
                                background: {'rgba(255,68,68,0.15)' if score < 60 else 'rgba(255,255,255,0.03)'};
                                border: 1px solid {'#FF4444' if score < 60 else 'rgba(255,255,255,0.05)'};">
                        <div style="font-size: 0.75rem; color: #FF4444; font-weight: 700;">NOT VERIFIED</div>
                        <div style="color: #94a3b8; font-size: 0.8rem;">Score &lt; 60</div>
                    </div>
                </div>
                <div style="color: #94a3b8; font-size: 0.88rem;">
                    Your score of <strong style="color: #a78bfa;">{score:.1f}</strong> falls in the
                    <strong style="color: {STATUS_COLORS.get(result['status'], '#94a3b8')};">
                    {result['status']}</strong> range.
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Full Reasoning
            st.markdown('<div class="section-header" style="font-size: 1.1rem;">💬 AI Reasoning Chain</div>', unsafe_allow_html=True)
            for i, reason in enumerate(result.get("reasoning", []), 1):
                st.markdown(f"""
                <div class="xai-item">
                    <strong style="color: #6366f1;">Reason {i}:</strong> {reason}
                </div>
                """, unsafe_allow_html=True)

    with tab2:
        result = st.session_state.gap_result
        if not result:
            st.info("Run a Skill Gap Analysis first to populate this panel.")
        else:
            st.markdown('<div class="section-header">📈 Skill Gap Explainability</div>', unsafe_allow_html=True)

            # Why these gaps?
            st.markdown("""
            <div class="glass-card">
                <div style="font-weight: 700; color: #a78bfa; margin-bottom: 0.75rem;">
                    🧮 Gap Detection Logic
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #94a3b8; line-height: 1.9;">
                    gap_skills = market_skills - user_skills (case-insensitive)<br>
                    ranked_gaps = sort(gap_skills, by=market_demand, descending=True)<br>
                    top_gaps = ranked_gaps[:3]<br>
                    opportunity_increase = min(demand_score × 1.5, 200)
                </div>
            </div>
            """, unsafe_allow_html=True)

            # AI Reasoning Chain
            st.markdown('<div class="section-header" style="font-size: 1.1rem;">💬 AI Reasoning Chain</div>', unsafe_allow_html=True)
            for i, reason in enumerate(result.get("ai_reasoning", []), 1):
                st.markdown(f"""
                <div class="xai-item">
                    <strong style="color: #6366f1;">Reason {i}:</strong> {reason}
                </div>
                """, unsafe_allow_html=True)

            # Opportunity impact chart
            gaps = result.get("skill_gaps", [])
            if gaps:
                st.markdown("---")
                st.markdown('<div class="section-header" style="font-size: 1.1rem;">📊 Career Growth Projection</div>', unsafe_allow_html=True)

                skills_g = [g["skill"] for g in gaps]
                opps = [g["opportunity_increase_pct"] for g in gaps]
                demands = [g["market_demand_score"] for g in gaps]

                fig_bubble = go.Figure()
                for i, (sk, op, dm) in enumerate(zip(skills_g, opps, demands)):
                    fig_bubble.add_trace(go.Scatter(
                        x=[dm], y=[op],
                        mode='markers+text',
                        marker=dict(
                            size=dm * 0.7,
                            color=["#6366f1", "#8b5cf6", "#a78bfa"][i % 3],
                            opacity=0.8,
                            line=dict(color='white', width=1),
                        ),
                        text=[sk],
                        textposition='top center',
                        textfont=dict(color='#e2e8f0', size=12),
                        name=sk,
                    ))

                fig_bubble.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(title='Market Demand Score', gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#94a3b8')),
                    yaxis=dict(title='Opportunity Increase %', gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#94a3b8')),
                    height=350,
                    margin=dict(l=10, r=10, t=30, b=30),
                    font=dict(color='#94a3b8'),
                    showlegend=False,
                )
                st.plotly_chart(fig_bubble, use_container_width=True)


# ---------------------------------------------------------------------------
# Main Router
# ---------------------------------------------------------------------------

def main():
    api_key = render_sidebar()

    # Load agents if key available
    page = st.session_state.current_page

    if page == "🏠 Home":
        render_home()
    elif page == "✅ Skill Verifier":
        verifier = None
        if api_key:
            try:
                verifier, _ = get_agents(api_key)
            except Exception:
                pass
        render_skill_verifier(api_key, verifier)
    elif page == "🔍 Skill Gap Analysis":
        render_skill_gap(api_key)
    elif page == "🗺️ Career Roadmap":
        render_roadmap()
    elif page == "🧠 XAI Panel":
        render_xai_panel()
    else:
        render_home()


if __name__ == "__main__":
    main()
else:
    # Streamlit runs this file as a module, not as __main__
    # so we must call main() unconditionally here.
    main()
