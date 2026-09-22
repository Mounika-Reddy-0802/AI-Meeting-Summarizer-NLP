# AI Meeting Summarizer (NLP)

[![CI](https://github.com/Mounika-Reddy-0802/AI-Meeting-Summarizer-NLP/actions/workflows/ci.yml/badge.svg)](https://github.com/Mounika-Reddy-0802/AI-Meeting-Summarizer-NLP/actions/workflows/ci.yml)

**Evidence-grounded structured minutes from meeting audio, with a small fine-tuned model that runs offline.**

> NLP · Speech · Abstractive summarisation · Dialogue acts · Factuality
> 4-week team project · Krishna (Frontend, Dialogue acts & Action items) · Lahari (Model training & Evaluation) · Mounika (Backend, ASR, Search & Evidence)

---

## The contribution in one sentence

A **250M-parameter Flan-T5 we fine-tune ourselves** turns a meeting recording into structured minutes —
*Decisions · Action items with owners · Open problems* — where **every sentence is linked to the
transcript turns that support it and scored for faithfulness**, with speech-to-text, diarisation and
summarisation all running **offline on a laptop**, so no audio or text ever leaves the machine.

> **Not claimed:** "beats a frontier LLM". A frontier model appears only as an offline baseline row
> in the results tables. The claim is the privacy / cost / latency trade-off, measured, and a
> grounding layer that flags the model's own unsupported sentences.

## Project status and where everything is

| | |
|---|---|
| **Current week** | Week 1 — code complete on all three branches, **Gate 1 not yet met** (see [Weekly gates](#weekly-gates)) |
| **Run the backend** | `cd backend` → `uvicorn app.main:app --port 8000` — [backend/README.md](backend/README.md) |
| **Run the frontend** | `cd frontend` → `npm run dev` — [frontend/README.md](frontend/README.md) |
| **Frontend without a backend** | `npm run mock` (json-server on :4000) |
| **Train the summariser** | Kaggle only — [ml/README.md](ml/README.md) → "Kaggle run" |
| **Numbers so far** | [benchmarks/summarization_results.md](benchmarks/summarization_results.md), generated from [benchmarks/raw/results.csv](benchmarks/raw/results.csv) |
| **Weekly write-ups** | [docs/](docs/) — one per member per week, listed [below](#weekly-docs) |
| **What went wrong** | [docs/problems.md](docs/problems.md) |
| **Design and viva prep** | [BLUEPRINT.md](BLUEPRINT.md) · plan: [PROJECT_PLAN.md](PROJECT_PLAN.md) · workflow: [GIT_RULES.md](GIT_RULES.md) |
| **Still open for Week 1** | Kaggle fine-tuning run · three sample recordings · pyannote download · weekly PRs to `dev` · cleaned `main` pushed |

---

## Architecture

```
 ┌───────────────────────────────── browser ──────────────────────────────────┐
 │ Next.js + TypeScript  (Krishna)                                            │
 │ record / upload · live stage progress · minutes tabs · evidence panel      │
 │ · speaker-grouped transcript · search · export                             │
 └──────────────────────────────────────▲─────────────────────────────────────┘
                                        │  HTTP + JWT
 ┌──────────────────────────────────────┴─────────────────────────────────────┐
 │ FastAPI + SQLite  (Mounika) — background pipeline, status per stage        │
 │                                                                            │
 │ audio.py        ffmpeg → 16 kHz mono wav, 60-min limit        (Mounika)    │
 │ transcribe.py   faster-whisper small, int8, word timestamps   (Mounika)    │
 │ diarize.py      pyannote 3.1 → speaker turns → segments       (Mounika)    │
 │ summarize.py    our fine-tuned Flan-T5-base                   (Lahari)     │
 │ dialogue_acts   DistilRoBERTa on MRDA                         (Krishna, W2)│
 │ action_items    rules + classifier + owner resolution       (Krishna, W2-3)│
 │ evidence.py     BM25 + MiniLM retrieval → NLI entailment      (Mounika, W3)│
 │ search.py       BM25 + MiniLM, reciprocal-rank fusion         (Mounika, W2)│
 └──────────────────────────────────────▲─────────────────────────────────────┘
                                        │  weights, downloaded once into MODEL_DIR
 ┌──────────────────────────────────────┴─────────────────────────────────────┐
 │ Kaggle GPUs → private Hugging Face Hub  (training and storage only)        │
 │ never called by the running app — it starts with HF_HUB_OFFLINE=1          │
 └────────────────────────────────────────────────────────────────────────────┘
```

**The NLP work is ours, in four places** (BLUEPRINT.md §4): domain-adaptive fine-tuning SAMSum → AMI
with speaker-turn chunking (Lahari) · a dialogue-act tagger that filters backchannels before
generation (Krishna) · section-conditioned generation, one model prompted per section (Lahari) · NLI
evidence linking that flags unsupported sentences (Mounika). Speech-to-text and diarisation are
inputs, not contributions — they are local so that the privacy claim is true.

---

## Quickstart

### 0. Prerequisites

| Requirement | Why | Check |
|---|---|---|
| Python 3.11 | backend and `ml/` | `py -3.11 --version` |
| Node.js 20+ | frontend | `node -v` |
| ffmpeg on `PATH` | audio conversion | `ffmpeg -version` |
| Hugging Face account that accepted the pyannote terms | one-time diarisation download | [speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1), [segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0) |
| Kaggle account with phone verification | training runs on Kaggle GPUs only | kaggle.com → Settings |

> **This repo lives in a OneDrive folder on the shared laptop.** Pause OneDrive before bulk git
> operations, and put the `ml/` virtualenv on a **short path** outside the project
> (`C:\Users\<you>\.mlvenv`) — torch's deepest files cross Windows' 260-character limit inside long
> folders ([problems.md](docs/problems.md)).

### 1. Backend

```powershell
cd backend
py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env            # JWT_SECRET (32+ chars), HF_TOKEN for the one download
python scripts/download_models.py      # once, with network: whisper, pyannote, MiniLM, NLI
uvicorn app.main:app --port 8000       # then works offline — http://localhost:8000/docs
```

### 2. The summariser checkpoint

Trained on Kaggle (`ml/kaggle/train_samsum.ipynb`), stored in a private Hub repo, then:

```powershell
huggingface-cli download <hf-user>/flan-t5-base-samsum --local-dir models/summarizer
```

Without it the backend still runs and uses the first three segments as the summary.

### 3. Frontend

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local      # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                            # http://localhost:3000 — the backend's CORS origin
```

No backend yet? `npm run mock` serves the whole API contract on :4000 — set
`NEXT_PUBLIC_API_URL=http://localhost:4000`.

### 4. `ml/` (data, baselines, evaluation)

```powershell
py -3.11 -m venv C:\Users\<you>\.mlvenv; C:\Users\<you>\.mlvenv\Scripts\Activate.ps1
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r ml/requirements.txt
pytest ml/tests
python ml/data/prepare.py --dataset samsum
python ml/evaluate.py --system extractive       # writes benchmarks/raw/results.csv
```

### 5. Checks CI runs on every PR

```powershell
cd backend;     ruff check .; pytest -q
cd ../frontend; npx tsc --noEmit; npm run build
```

---

## Repository map

| Path | Owner | Contents |
|---|---|---|
| `backend/app/` | Mounika | FastAPI app, SQLite models, JWT auth, background pipeline |
| `backend/app/services/transcribe.py`, `diarize.py`, `audio.py` | Mounika | local ASR and diarisation |
| `backend/app/services/summarize.py` | Lahari | loads our checkpoint; chunking (W2) and sections (W3) |
| `backend/app/services/dialogue_acts.py`, `action_items.py` | Krishna | tagger and action items (W2–W3) |
| `backend/app/services/search.py`, `evidence.py` | Mounika | hybrid search (W2), evidence linking (W3) |
| `backend/scripts/` | Mounika | `download_models.py`, `create_user.py`, `asr_latency.py` |
| `frontend/` | Krishna | Next.js app, typed API client, json-server mock |
| `ml/` | Lahari | data loaders, `train.py`, `evaluate.py`, TextRank baseline, Kaggle notebooks |
| `ml/dialogue_acts/`, `ml/action_items/` | Krishna | tagger and classifier training (W2–W3) |
| `docs/` | all | one weekly write-up per member + `problems.md` |
| `benchmarks/` | all | every reported number traces to a file in `benchmarks/raw/` |
| `demo/` | Krishna | sample audio, screenshots, demo script, video |
| `data/`, `models/` | — | **gitignored** — datasets and downloaded weights |

---

## Weekly gates

| Week | Gate | Status |
|---|---|---|
| 1 | One real audio file goes upload → local ASR + diarisation → our SAMSum checkpoint → summary on screen, network disabled | **not met** — code is done on all three branches; waiting on the Kaggle run, the sample recordings and the pyannote download |
| 2 | 20-minute recording → chunked summary, dialogue-act-tagged transcript, rule-based action items linked to lines, hybrid search; ≥ 5 rows in `summarization_results.md` | not started |
| 3 | Decisions / Actions / Problems with per-sentence evidence and faithfulness flags, action items with owners, docx export | not started |
| 4 | All benchmark tables and human evaluation, seed data, demo video, `docker compose up` on a clean machine | not started |

Each gate ends with a `dev → main` merge and a `week<N>-complete` tag; the final one is `v1.0`.

---

## Weekly docs

One write-up per member per week — what was built, how to run it, the numbers, and what is verified
versus still open. A week's doc is written when that week's work is finished, never ahead of it.

| Week | Krishna | Lahari | Mounika |
|---|---|---|---|
| 1 | [Frontend](docs/W1_krishna_frontend.md) | [Dataset check, SAMSum fine-tune setup, baselines](docs/W1_lahari_samsum_finetune.md) | [FastAPI backend with local ASR and diarisation](docs/W1_mounika_local_asr_backend.md) |
| 2 | — | — | — |
| 3 | — | — | — |
| 4 | — | — | — |

---

## Results

*Filled in as gates pass. Every number links to the file that produced it; numbers typed by hand are
not accepted.*

| Result | Value | Source |
|---|---|---|
| TextRank extractive baseline, SAMSum test (819 dialogues) | ROUGE-1 0.2903 · ROUGE-2 0.0830 · ROUGE-L 0.2313 · BERTScore F1 0.8628 | [`benchmarks/raw/results.csv`](benchmarks/raw/results.csv) |
| Zero-shot Flan-T5-base, SAMSum test | _pending — Kaggle run_ | `benchmarks/raw/results.csv` |
| Fine-tuned Flan-T5-base (SAMSum), SAMSum test | _pending — Kaggle run_ | `benchmarks/raw/results.csv` |
| ASR + diarisation CPU time, 3 sample clips | _pending — clips and pyannote_ | `benchmarks/raw/asr_latency.csv` |
| AMI fine-tune, chunking, ablations | _pending W2_ | `benchmarks/summarization_results.md`, `benchmarks/ablations.md` |
| Dialogue-act tagger macro-F1 on MRDA | _pending W2_ | `benchmarks/dialogue_act_eval.md` |
| Hybrid search hits@5 / MRR | _pending W2_ | `benchmarks/search_eval.md` |
| Section-conditioned minutes S-A / S-B / S-C | _pending W3_ | `benchmarks/structured_minutes.md` |
| Faithfulness per system, flag precision | _pending W3_ | `benchmarks/factuality.md` |
| Action-item F1 and owner accuracy | _pending W3_ | `benchmarks/action_item_eval.md` |
| Human evaluation and ρ with faithfulness | _pending W4_ | `benchmarks/human_eval.md` |
| fp32 vs int8 latency per 20-minute meeting | _pending W4_ | `benchmarks/latency.md` |

---

## Honest scope

**What runs offline, and what does not.** The running app makes no network call: it starts with
`HF_HUB_OFFLINE=1` and can only load what `download_models.py` fetched. Training is the exception by
design — it happens on Kaggle GPUs and checkpoints travel through a private Hugging Face repo — and
neither is ever called by the app.

**The laptop claim is not yet earned.** A timing check put zero-shot Flan-T5-base at roughly 20 s per
short SAMSum dialogue on this laptop's CPU with beam search. Week 4's int8 quantisation and latency
table exist to measure whether a 20-minute meeting is practical; until then "runs on a laptop" means
"runs", not "runs fast".

**Datasets.** SAMSum and DialogSum are licensed non-commercial — fine for coursework and the report,
and the published model card will say so. AMI is CC BY 4.0. Sources, sizes and licences are in
[`data/README.md`](data/README.md).

**The demo audio will be our own.** The sample meetings are to be recorded by the team, with consent
noted in `docs/decisions.md`; no third-party recordings are committed. They are not recorded yet.

---

## Contributing

Read [`GIT_RULES.md`](GIT_RULES.md) before your first commit. In short: branch
`week<N>-<name>-<topic>` off `dev`; commit a short lowercase imperative with no bracketed prefix;
push the same day; write your weekly doc and add to `docs/problems.md` whatever cost you time; then
open a PR to **`dev`**. Nobody commits to `main`, and only the three of us ever appear in the history.

---

## License

Academic coursework. Datasets are used under their original licences (see `data/README.md`).
