# 📚 StudyPilot AI

**A secure, full-stack multi-agent study assistant** — paste your notes, get a quiz, get graded, and track your progress over time. Built for the **Google × Kaggle AI Agents: Intensive Vibe Coding Capstone Project** (Freestyle Track).

![Status](https://img.shields.io/badge/status-working-brightgreen)
![Mode](https://img.shields.io/badge/mode-offline%20simulation-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 🎯 What It Does

StudyPilot AI turns raw study notes into a full learning loop:

1. **Paste or upload your notes** in the Study Lab
2. An **agent pipeline** sanitizes the input, extracts key facts, and generates a quiz
3. **Take the quiz** — questions are built directly from real sentences in your notes
4. **Get graded instantly**, with explanations that quote your original notes back to you
5. **Track your progress** over time on the Dashboard, with full history of every attempt

Runs **completely offline** in high-fidelity Simulation Mode — no API key required. Optionally connect a free Gemini API key for live LLM-powered generation.

---

## 🖼️ Screenshots

> *(Add your dashboard, quiz, and feedback screenshots here)*

| Dashboard | Quiz Session | Feedback Hub |
|---|---|---|
| ![Dashboard](docs/screenshot-dashboard.png) | ![Quiz](docs/screenshot-quiz.png) | ![Feedback](docs/screenshot-feedback.png) |

---

## 🧠 Multi-Agent Architecture

StudyPilot AI is built on an **ADK-style multi-agent system**, where each agent has a single clear responsibility and hands off to the next:

```
 User Notes
     │
     ▼
┌─────────────────────┐
│  Notes Extractor     │  → validates, sanitizes, extracts key terms & facts
│  Agent               │
└─────────┬────────────┘
          ▼
┌─────────────────────┐
│  Quiz Generator      │  → builds fact-based questions from real note content
│  Agent               │
└─────────┬────────────┘
          ▼
┌─────────────────────┐
│  Grader / Feedback   │  → scores answers, explains mistakes using source text
│  Agent               │
└─────────┬────────────┘
          ▼
┌─────────────────────┐
│  Progress Tracker    │  → logs attempts, tracks trends, flags weak topics
│  Agent               │
└─────────────────────┘
```

### Key Concepts Demonstrated

| Concept | Implementation |
|---|---|
| **Multi-Agent System (ADK)** | `BaseAgent` class + 4 specialized sub-agents coordinating in a pipeline |
| **MCP Server** | `mcp_server.py` exposes agent capabilities (`extract_notes`, `generate_quiz`, `grade_answers`) as MCP tools over JSON-RPC |
| **Security Features** | `safety_filter.py` — input size validation, prompt-injection heuristics, HTML/script sanitization before any content reaches an agent |
| **Agent Skills** | Reusable skill modules (`safety_filter`, `db_store`) declared and used across agents |
| **Deployability** | Single-command local deployment via Flask, `localhost:3000` |

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, vanilla JS, Chart.js
- **Data Storage:** Lightweight JSON file store (`db.json`)
- **AI Integration:** Optional Google Gemini API (`google-genai`), with full offline simulation fallback
- **Protocol:** Model Context Protocol (MCP) server for agent tool exposure

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
git clone https://github.com/Anchal-Verma04/studypilot-ai.git
cd studypilot-ai
pip install -r requirements.txt
```

### Run the app

```bash
python src/server.py
```

Then open your browser at:

```
http://localhost:3000
```

That's it — no API key needed. The app runs fully offline in **Simulation Mode**.

### (Optional) Enable live Gemini AI

1. Get a free API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Copy `.env.example` to `.env`
3. Add your key:
   ```
   GEMINI_API_KEY=your_key_here
   ```
4. Restart the server

---

## 📂 Project Structure

```
studypilot-ai/
├── src/
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── notes_extractor_agent.py
│   │   ├── quiz_generator_agent.py
│   │   ├── grader_agent.py
│   │   └── progress_tracker_agent.py
│   ├── skills/
│   │   ├── safety_filter.py
│   │   └── db_store.py
│   ├── public/
│   │   ├── index.html
│   │   ├── styles.css
│   │   └── app.js
│   ├── mcp_server.py
│   ├── server.py
│   └── test_agents.py
├── db.json
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔒 Security Notes

- All user-submitted notes pass through **size validation** and **prompt-injection heuristics** before reaching any agent
- Content is **HTML-sanitized** to prevent script injection in the UI
- No credentials are hardcoded — API keys are loaded from a local `.env` file (never committed to version control)

---

## 🏆 About This Project

Built as the capstone project for Google & Kaggle's **5-Day AI Agents: Intensive Vibe Coding Course** (Freestyle Track), demonstrating multi-agent orchestration, MCP server design, agent skills, and security-conscious agent architecture — developed using **Antigravity IDE**.

---

## 📄 License

MIT License — free to use, modify, and learn from.
