# 🤖 CodeCrew AI — Multi-Agent Software Development System

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.138-green?style=flat-square&logo=fastapi)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-purple?style=flat-square)
![Agents](https://img.shields.io/badge/Agents-5_Specialized-orange?style=flat-square)

**5 specialized AI agents that collaborate to plan, write, review, test and document your software — automatically.**

💻 **GitHub:** https://github.com/BargaviS/codecrew-ai

---

## 🎯 What It Does

You describe what you want to build in plain English. CodeCrew AI runs 5 agents in sequence — each one specialized for a specific job. You watch them work in real time.

---

## 🤖 The 5 Agents

| Agent | Role | What It Does |
|-------|------|-------------|
| 🗺️ **Planner** | Requirements Analysis | Breaks your requirement into clear technical steps |
| 💻 **Coder** | Code Generation | Writes production-grade code following the plan |
| 🔍 **Reviewer** | Code Review | Reviews code, scores quality, rejects with specific feedback |
| 🧪 **Tester** | Test Generation | Writes comprehensive unit tests with edge cases |
| 📝 **Documenter** | Documentation | Writes README, API docs and usage examples |

---

## ⚡ Key Innovation — Coder-Reviewer Loop

This is what makes it genuinely agentic:
The Reviewer gives **specific, actionable feedback** — not generic comments. The Coder reads every issue and fixes them. This is autonomous decision-making — not just prompt chaining.

---

## 🏗️ Architecture
---

## ⚙️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Agent Brain | Groq LLaMA 3.3 70B | Fastest inference, tool-compatible, free |
| Agent Pattern | Custom ReAct loop | Built from scratch — no LangChain abstraction |
| Structured Output | Pydantic v2 | Type-safe contracts between agents |
| Streaming | Server-Sent Events (SSE) | Real-time agent updates to frontend |
| Backend | FastAPI | Async, auto OpenAPI docs |
| Session Storage | JSON files | Full audit trail of every agent decision |
| Frontend | Vanilla HTML/JS | Zero dependency, fast loading |

---

## 🔑 Key Engineering Decisions

**Why build agent loop from scratch instead of LangChain?**
LangChain abstracts away the agent loop. Building it from scratch means I understand exactly how agents think, decide and hand off work. I can explain every line in an interview.

**Why Pydantic schemas between agents?**
Every agent returns a validated Pydantic model — not raw text. This creates a strict contract between agents. If the Coder returns invalid output, it fails immediately with a clear error — not silently corrupt data downstream.

**Why SSE streaming instead of WebSockets?**
SSE is simpler for one-way streaming (server → client). WebSockets are overkill when we only need to push updates to the user. SSE is also easier to debug and works through proxies.

**Why JSON session storage instead of a database?**
Each session is fully self-contained. JSON files are human-readable, easy to debug, and don't need a database setup. For production, this would swap to PostgreSQL with one interface change.

---

## 📁 Project Structure
---

## 🚀 Run Locally

```bash
git clone https://github.com/BargaviS/codecrew-ai.git
cd codecrew-ai

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Add your GROQ_API_KEY in .env
# Get free key at: https://console.groq.com

PYTHONPATH=. uvicorn app.main:app --reload
```

Open **http://localhost:8000**

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /session | Create new session |
| GET | /session/{id}/stream | Stream agent output (SSE) |
| GET | /session/{id} | Get full session result |
| GET | /sessions | List all sessions |

---

## 💡 What I Would Add Next

- **Parallel agents** — Tester and Documenter run simultaneously
- **Code execution** — Run generated code in sandbox and fix errors
- **RAG over codebase** — Agents learn your existing code style
- **GitHub integration** — Auto-create PR with generated code
- **Agent memory** — Learn from past sessions to improve over time

---

## 👩‍💻 Built By

**Bargavi S** — Aspiring GenAI Engineer

> *"Most people use AI tools. I built the system that coordinates AI agents to work together — each specialized, each accountable, each improving the other's output."*

---

## 📄 License

MIT License
