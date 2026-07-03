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

The Reviewer scores code 0-100. If score < 65, it rejects with specific feedback and sends back to Coder. This loop continues until approved — autonomous decision making.

---

## 🚀 Run Locally

```bash
git clone https://github.com/BargaviS/codecrew-ai.git
cd codecrew-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY
PYTHONPATH=. uvicorn app.main:app --reload
```

Get free Groq key at: https://console.groq.com

---

## ⚙️ Tech Stack

FastAPI · Groq LLaMA 3.3 70B · Pydantic v2 · SSE Streaming · Custom ReAct Agent Loop

---

## 👩‍💻 Built By

**Bargavi S** — Aspiring GenAI Engineer
