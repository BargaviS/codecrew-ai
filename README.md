---
title: CodeCrew AI
emoji: 🤖
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
---

# 🤖 CodeCrew AI — Multi-Agent Software Development System

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.138-green?style=flat-square&logo=fastapi)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-purple?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

**5 specialized AI agents that collaborate to plan, write, review, test and document your software — automatically.**

🌐 **Live Demo:** https://bargavishaila-codecrew-ai.hf.space
💻 **GitHub:** https://github.com/BargaviS/codecrew-ai

---

## 🎯 Problem It Solves

Writing software takes time — requirements analysis, coding, code review, testing, documentation. CodeCrew AI automates all of it with 5 specialized agents working together.

---

## 🤖 The 5 Agents

| Agent | Role | What It Does |
|-------|------|-------------|
| 🗺️ **Planner** | Requirements Analysis | Breaks your requirement into clear technical steps |
| 💻 **Coder** | Code Generation | Writes production-grade code following the plan |
| 🔍 **Reviewer** | Code Review | Reviews code, scores quality (0-100), rejects with specific feedback |
| 🧪 **Tester** | Test Generation | Writes comprehensive unit tests with edge cases |
| 📝 **Documenter** | Documentation | Writes README, API docs and usage examples |

---

## ⚡ Key Innovation — Coder-Reviewer Loop
The Reviewer gives **specific, line-by-line feedback**. The Coder reads every issue and fixes them. This loop continues until approved — **autonomous decision making**.

---

## 🏗️ Architecture
---

## ⚙️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Agent Brain | Groq LLaMA 3.3 70B | Fastest inference, free, reliable |
| Agent Pattern | Custom ReAct loop | Built from scratch — no LangChain abstraction |
| Structured Output | Pydantic v2 | Type-safe contracts between agents |
| Streaming | Server-Sent Events (SSE) | Real-time agent updates to browser |
| Backend | FastAPI | Async, auto OpenAPI docs |
| Session Storage | JSON files | Full audit trail of every agent decision |
| Frontend | Vanilla HTML/JS | Zero dependency, fast loading |

---

## 🔑 Key Engineering Decisions

**Why build agent loop from scratch instead of LangChain?**
> LangChain abstracts away the agent loop. Building from scratch means I understand every decision the system makes and can explain it clearly in interviews.

**Why Pydantic schemas between agents?**
> Every agent returns a validated Pydantic model — not raw text. This creates strict contracts between agents. If Coder returns invalid output, it fails immediately with a clear error.

**Why SSE instead of WebSockets?**
> SSE is simpler for one-way server→client streaming. WebSockets are overkill. SSE also works through proxies and is easier to debug.

**Why JSON session storage?**
> Each session is fully self-contained and human-readable. Easy to debug. For production, swap to PostgreSQL with one interface change.

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
# Add your GROQ_API_KEY — get free at https://console.groq.com

PYTHONPATH=. uvicorn app.main:app --reload
```

Open **http://localhost:8000**

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /session | Create new coding session |
| GET | /session/{id}/stream | Stream agent output (SSE) |
| GET | /session/{id} | Get full session result |
| GET | /sessions | List all sessions |

---

## 💡 What I Would Add Next

- **Code execution** — run generated code in sandbox and fix errors automatically
- **Parallel agents** — Tester and Documenter run simultaneously
- **RAG over codebase** — agents learn your existing code style
- **GitHub integration** — auto-create PR with generated code
- **Agent memory** — learn from past sessions to improve over time

---

## 👩‍💻 Built By

**Bargavi S** — Aspiring GenAI Engineer

> *"Most people use AI tools. I built the system that coordinates AI agents to work together — each specialized, each accountable, each improving the other's output."*

---

## 📄 License

MIT License
