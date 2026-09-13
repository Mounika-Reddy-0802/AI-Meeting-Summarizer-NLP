# AI Meeting Summarizer (NLP)

[![CI](https://github.com/Mounika-Reddy-0802/AI-Meeting-Summarizer-NLP/actions/workflows/ci.yml/badge.svg)](https://github.com/Mounika-Reddy-0802/AI-Meeting-Summarizer-NLP/actions/workflows/ci.yml)

**Evidence-grounded structured minutes from meeting audio, with a small fine-tuned model that runs offline.**

A user uploads or records a meeting. Speech-to-text and speaker diarisation run locally
(faster-whisper + pyannote). **Our own fine-tuned Flan-T5 model** (trained on Kaggle GPUs) produces
structured minutes — *Decisions · Action items with owners · Open problems* — and every generated
sentence is linked to the transcript turns that support it and scored for faithfulness with an NLI
model. A dialogue-act tagger, action-item extraction with owner resolution and hybrid BM25 + dense
search are our own code as well. Backend is FastAPI + SQLite, frontend is Next.js.

**No cloud service and no LLM API in the application path.** Nothing leaves the machine after the
one-time model download; a frontier LLM appears only as an offline baseline row in the results table.

Built from scratch in four weeks by **Krishna · Lahari · Mounika**.
See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the week-by-week plan, [BLUEPRINT.md](BLUEPRINT.md) for
the architecture and NLP design, and [GIT_RULES.md](GIT_RULES.md) for the repository workflow.

## Status

Day 0 — repository skeleton. Quickstart, architecture diagram and results table land in Week 4.
