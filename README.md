# AI Meeting Summarizer (NLP)

A web app where a user uploads or records a meeting, **Deepgram** converts speech to text (with
speaker labels), and **our own fine-tuned NLP model** (Flan-T5, trained on Kaggle GPUs) produces the
summary. Action-item extraction and semantic search are our own code as well. The backend is
FastAPI + SQLite, the frontend is Next.js. No LLM API (Gemini, GPT etc.) is used anywhere in the
application path — they appear only as an offline baseline in the results table.

Built from scratch in three weeks by **Krishna · Lahari · Mounika**.
See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the week-by-week plan and [GIT_RULES.md](GIT_RULES.md)
for the repository workflow.

## Status

Day 0 — repository skeleton. Quickstart, architecture diagram and results table land in Week 3.
