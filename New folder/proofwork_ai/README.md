# 🔐 ProofWork AI

**Trust-First Agentic Freelance Marketplace Powered by Explainable AI (XAI)**

> *"Don't tell us what you can do. Prove it."*

---

## 🧠 What Is ProofWork AI?

ProofWork AI replaces the broken trust model of freelance marketplaces.

Instead of relying on **ratings**, **reviews**, and **self-reported skills** — all of which can be faked — ProofWork AI uses:

- ✅ **AI-Generated Challenges** — Real tasks, not self-assessments
- 🤖 **LLM-Powered Evaluation** — Analyzed by LLaMA 3.3-70B via Groq
- 🧠 **Explainable AI (XAI)** — Every score comes with full reasoning
- 📈 **Career Intelligence** — Gap analysis and personalized roadmaps

---

## 🏗️ Architecture

```
proofwork_ai/
├── app.py                      ← Streamlit dashboard (5 pages)
│
├── agents/
│   ├── skill_verifier.py       ← Agent 1: Skill Verification
│   └── skill_gap_agent.py      ← Agent 2: Skill Gap Intelligence
│
├── services/
│   ├── groq_service.py         ← Groq API client (retry + JSON parsing)
│   └── evaluation_engine.py    ← Score computation + status thresholds
│
├── utils/
│   ├── prompts.py              ← All LLM prompt templates
│   ├── roadmap_generator.py    ← Deterministic roadmap & gap logic
│   └── logger.py               ← Centralized rotating file logger
│
├── models/
│   └── schemas.py              ← All dataclass models (typed, serializable)
│
├── data/
│   ├── market_data.json        ← Market demand scores for 30+ skills
│   └── sample_submission.json  ← Demo submission for testing
│
├── tests/
│   ├── test_skill_verifier.py  ← 20+ tests for Agent 1
│   └── test_skill_gap.py       ← 25+ tests for Agent 2
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🤖 Agent 1 — Skill Verification Agent

**Purpose:** Verify whether a freelancer actually possesses a claimed skill.

### Input
```json
{
  "user_id": "101",
  "skill": "Python Automation",
  "challenge_title": "Build a File Organizer",
  "submission_text": "import os\nimport shutil\n...",
  "submission_time": "2026-06-24T10:30:00"
}
```

### AI Evaluation Dimensions
| Dimension | Weight | Description |
|-----------|--------|-------------|
| Code Quality | 30% | Structure, readability, naming conventions |
| Documentation | 20% | Docstrings, comments, clarity |
| Security | 20% | Input validation, error handling, safe patterns |
| Problem Solving | 30% | Correctness, efficiency, completeness |

### Scoring & Status
| Score Range | Status |
|-------------|--------|
| 80–100 | ✅ VERIFIED |
| 60–79 | ⚠️ PARTIALLY VERIFIED |
| 0–59 | ❌ NOT VERIFIED |

### XAI Output
```json
{
  "overall_score": 91.0,
  "status": "VERIFIED",
  "component_scores": {
    "code_quality": 88,
    "documentation": 75,
    "security": 82,
    "problem_solving": 90
  },
  "reasoning": [
    "Weighted score: CQ(88×0.30) + Doc(75×0.20) + Sec(82×0.20) + PS(90×0.30) = 85.9",
    "Clean modular structure with function decomposition.",
    "Docstring present in main function.",
    "Input validation via Path.exists() before processing."
  ],
  "strengths": ["Cross-platform pathlib usage", "Error handling for missing dirs"],
  "improvements": ["No logging module", "Missing unit tests", "No CLI interface"]
}
```

---

## 🔍 Agent 2 — Skill Gap Intelligence Agent

**Purpose:** Identify missing high-demand skills and generate a personalized career roadmap.

### Input
```json
{
  "user_skills": ["Python", "Flask", "SQL"]
}
```

### Market Data
Stored in `data/market_data.json`. Contains demand scores (0–100) for 30+ skills including Docker, AWS, FastAPI, Machine Learning, Kubernetes, and more.

### Logic
```
gap_skills = market_skills - user_skills (case-insensitive)
ranked_gaps = sort(gap_skills, by=market_demand, descending)
top_gaps = ranked_gaps[:3]
opportunity_increase = min(demand_score × 1.5, 200%)
```

### Output
```json
{
  "skill_gaps": [
    {"skill": "Machine Learning", "market_demand_score": 70, "opportunity_increase_pct": 105.0},
    {"skill": "Docker", "market_demand_score": 65, "opportunity_increase_pct": 97.5},
    {"skill": "FastAPI", "market_demand_score": 62, "opportunity_increase_pct": 93.0}
  ],
  "roadmap": [
    {"week_range": "Week 1-2", "skill": "Machine Learning", "focus": "ML Fundamentals", ...},
    {"week_range": "Week 3-4", "skill": "Docker", "focus": "Containerization", ...},
    {"week_range": "Week 5-6", "skill": "FastAPI", "focus": "REST API Development", ...}
  ],
  "career_impact_summary": "Mastering ML, Docker, and FastAPI could unlock +105% more opportunities.",
  "ai_reasoning": ["Machine Learning tops market demand at 70/100...", ...]
}
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Frontend | Streamlit |
| AI | Groq API — LLaMA 3.3-70B-Versatile |
| Visualization | Plotly |
| Data | JSON |
| Testing | pytest + pytest-cov |
| Architecture | OOP, SOLID, Modular |

---

## ⚡ Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/proofwork-ai.git
cd proofwork-ai/proofwork_ai
```

### 2. Create a Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your Groq API key
# Get your free key at: https://console.groq.com
GROQ_API_KEY=your_groq_api_key_here
```

### 5. Run the Application
```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_skill_verifier.py -v
pytest tests/test_skill_gap.py -v
```

---

## 🖥️ Dashboard Pages

| Page | Description |
|------|-------------|
| 🏠 Home | Platform overview, value proposition, how it works |
| ✅ Skill Verifier | Submit challenge solutions for AI verification |
| 🔍 Skill Gap Analysis | Discover high-demand missing skills |
| 🗺️ Career Roadmap | Week-by-week personalized learning plan + Gantt chart |
| 🧠 XAI Panel | Full explainability — waterfall charts, reasoning chains, formula breakdown |

---

## 🧠 Explainable AI (XAI) Features

ProofWork AI is built on the principle of **zero black boxes**:

- **Verification XAI:** Score waterfall chart showing exact contribution of each dimension
- **Threshold Logic:** Displayed visually — why 80 = VERIFIED, 60 = PARTIAL
- **Reasoning Chain:** Numbered list of specific AI observations
- **Gap Logic:** Transparent formula shown: `opportunity = demand × 1.5`
- **Roadmap XAI:** 5 AI-generated reasons WHY each skill was prioritized

---

## 📁 Data Files

### `data/market_data.json`
Contains market demand scores (0–100) for 30+ in-demand tech skills.
Update this file to reflect current market conditions.

### `data/sample_submission.json`
Pre-filled demo submission for testing the Skill Verification page.
Uses a Python File Organizer challenge as the example.

---

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ Yes | — | Your Groq API key |
| `MODEL_NAME` | No | `llama-3.3-70b-versatile` | LLM model name |
| `LOG_LEVEL` | No | `INFO` | Logging level |

---

## 📊 Logging

Logs are written to `logs/proofwork_ai.log` with rotating file handler (5MB max, 3 backups).

Console output is also enabled at INFO level.

Log format:
```
2026-06-24 10:30:00 | INFO     | proofwork_ai.agents.skill_verifier    | Verification complete | user_id=101 | score=91.0 | status=VERIFIED
```

---

## 🚀 Future Improvements

- [ ] PostgreSQL integration for persistent verification history
- [ ] Freelancer profile dashboard with trust score timeline
- [ ] Multi-skill batch verification
- [ ] Client-side hiring recommendations based on verified talent pool
- [ ] GitHub repository submission integration
- [ ] Webhook notifications for verification completion
- [ ] LangGraph multi-agent orchestration layer
- [ ] RBAC (role-based access control) for client/freelancer/admin roles
- [ ] Real-time market demand data pipeline (job board API integration)
- [ ] Mobile-responsive PWA export

---

## 👩‍💻 Author

**Swetha** — Module Owner: Skill Verification & Gap Intelligence Agents

Built for the **ProofWork AI** hackathon project — a trust-first agentic freelance marketplace.

Powered by **Groq** (LLaMA 3.3-70B-Versatile) | Built with **Streamlit** + **Plotly**

---

## 📄 License

MIT License — See LICENSE file for details.
