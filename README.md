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

```
1. User submits a requirement (e.g. "build a rate limiter")
                    │
                    ▼
        ┌───────────────────────┐
        │   Planner Agent       │  Breaks requirement into a
        │                       │  clear technical plan
        └───────────┬───────────┘
                     │
                     ▼
        ┌───────────────────────┐
        │   Coder Agent         │◄────────────┐
        │                       │              │
        │  Writes code from     │              │ rejected +
        │  the plan             │              │ specific issues
        └───────────┬───────────┘              │
                     │                          │
                     ▼                          │
        ┌───────────────────────┐              │
        │   Reviewer Agent      │──────────────┘
        │                       │
        │  Scores code (0-100)  │
        │  approved? ──── No ───┘ (loop, up to
        │      │                   MAX_REVIEW_ITERATIONS times)
        │     Yes
        └───────────┬───────────┘
                     │
                     ▼
        ┌───────────────────────┐
        │   Tester Agent        │  Writes unit tests for the
        │                       │  approved code
        └───────────┬───────────┘
                     │
                     ▼
        ┌───────────────────────┐
        │   Documenter Agent    │  Writes README + API docs
        │                       │  for the finished feature
        └───────────┬───────────┘
                     │
                     ▼
         Final session result — streamed live to the
         browser via Server-Sent Events (SSE) as each
         agent completes its step
```

**Key implementation details:**
- All 5 agents share **one `LLMClient` instance** (Groq) — specialization comes from different system prompts per agent, not different models
- Every agent is a subclass of an abstract `BaseAgent` (template method pattern) — same `run()` contract, different prompt/behavior
- The Orchestrator is **stateless** — all session state lives in `SessionManager`, so a server restart doesn't lose an in-progress session's history (though the *current* run itself won't resume mid-way)
- LLM calls happen inside `asyncio.to_thread(...)` — this hands the blocking Groq API call to a background thread, so the FastAPI event loop isn't frozen while waiting on the LLM, and SSE events for other requests can still stream
- LLM JSON output is enforced with up to 3 retry attempts, then validated against Pydantic schemas — if the model returns malformed or wrongly-typed output, it's caught immediately rather than silently breaking a later agent

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

**Why `asyncio.to_thread` around LLM calls?**
> The Groq SDK call is synchronous/blocking. Running it directly inside an `async def` would freeze the whole FastAPI event loop for every other request while waiting on the LLM. Wrapping it in `asyncio.to_thread` offloads the blocking call to a worker thread, keeping the server responsive to other sessions while one is mid-generation.

---

## 📁 Project Structure

```
codecrew-ai/
├── app/
│   ├── main.py                       # FastAPI app entrypoint
│   ├── core/
│   │   ├── config.py                 # Environment-based settings
│   │   └── logger.py                 # Structured logging
│   ├── agents/
│   │   ├── base_agent.py             # Abstract base — shared run() contract
│   │   ├── planner_agent.py          # Requirement → technical plan
│   │   ├── coder_agent.py            # Plan → code
│   │   ├── reviewer_agent.py         # Code → score + approve/reject
│   │   ├── tester_agent.py           # Approved code → unit tests
│   │   ├── documenter_agent.py       # Finished feature → docs
│   │   └── orchestrator.py           # Coordinates all 5 agents, yields SSE events
│   ├── services/
│   │   ├── llm_client.py             # Groq wrapper — retry + JSON validation
│   │   └── session_manager.py        # Session persistence (JSON files)
│   ├── api/
│   │   └── routes/
│   │       └── main.py               # /session, /session/{id}/stream, /health
│   ├── schemas/
│   │   └── models.py                 # Pydantic contracts between agents
│   └── static/
│       └── index.html                # Live-updating frontend (SSE consumer)
├── requirements.txt
├── Dockerfile                        # HF Spaces-compatible (port 7860)
├── .env.example
└── README.md
```

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

- **Code execution** — run generated code in sandbox and fix errors automatically. Currently the Reviewer critiques code by reading it, but never actually runs it — a bug that "looks fine" but crashes at runtime could slip through.
- **Parallel agents** — Tester and Documenter don't depend on each other's output and currently run sequentially; they could run concurrently to cut total pipeline time.
- **RAG over codebase** — agents learn your existing code style
- **GitHub integration** — auto-create PR with generated code
- **Agent memory** — learn from past sessions to improve over time

---

## 👩‍💻 Built By

**Bargavi S** — Aspiring GenAI Engineer

> *"I built this to understand how AI agents can coordinate on real engineering work — planning, coding, reviewing, testing, and documenting — with each agent accountable for its part and able to send work back for revision."*
---

## 📄 License

MIT License
