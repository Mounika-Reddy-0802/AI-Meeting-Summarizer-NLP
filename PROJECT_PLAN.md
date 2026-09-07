# AI Meeting Summarizer (NLP) — Complete Plan, Built From Scratch

Team: **Krishna · Lahari · Mounika** · Duration: 3 weeks · Branch names, docs and gates follow `GIT_RULES.md`.

**What we are building.** A web app where a user uploads or records a meeting, **Deepgram** converts
speech to text (with speaker labels), and **our own fine-tuned NLP model** produces the summary.
We also write our own **action-item extraction** and **semantic search**. Backend is FastAPI +
SQLite, frontend is Next.js. No LLM API (Gemini, GPT etc.) is used anywhere in the app — they appear
only as an offline baseline in the results table.

**Ground rules**
- Everything starts from an **empty folder**. Nothing is copied, cloned or reused from any earlier project.
- **All model training runs on Kaggle GPUs, never on laptops.** Laptops are for code, the app, and
  inference on the saved checkpoint. Checkpoints go Kaggle → private Hugging Face Hub → laptop.
- Every number in the report must come from a script in the repo writing a file in `benchmarks/raw/`.

---

## 1. Ownership

| Member | Owns | NLP contribution (what they defend in the viva) |
|--------|------|------------------------------------------------|
| **Lahari** | `ml/` (data, training, evaluation), `backend/app/services/summarize.py`, `docs/results.md` | Fine-tuned summarization model, hierarchical chunking, ablations, all evaluation |
| **Krishna** | `frontend/`, `backend/app/services/action_items.py`, `ml/action_items/`, `demo/` | Action-item extraction (rules + classifier), export, demo |
| **Mounika** | `backend/` (API, DB, auth, Deepgram pipeline), `backend/app/services/search.py`, docker, release | Semantic search with Sentence-BERT, transcript preprocessing, infrastructure |

## 2. Final repository layout

```
ai-meeting-summarizer-nlp/
├── README.md  GIT_RULES.md  PROJECT_PLAN.md
├── .gitignore  .env.example  docker-compose.yml
├── .github/pull_request_template.md
├── frontend/                       Next.js + TypeScript + Tailwind
│   ├── src/lib/       types.ts, api.ts, auth.tsx
│   ├── src/pages/     login, register, dashboard, summariser, meetings/[id]
│   ├── src/components/ Recorder, UploadAudio, TranscriptView, ActionItemList, SummaryCard, SearchDrawer, ExportButton
│   ├── mock/db.json   json-server data for development without the backend
│   └── .env.example   NEXT_PUBLIC_API_URL
├── backend/                        FastAPI + SQLAlchemy + SQLite
│   ├── app/main.py, config.py, db.py, models.py, schemas.py, auth.py, pipeline.py
│   ├── app/routes/    auth.py, meetings.py
│   ├── app/services/  transcribe.py, audio.py, summarize.py, action_items.py, search.py, export.py
│   ├── scripts/       seed.py, create_user.py
│   ├── tests/
│   └── .env.example   DEEPGRAM_API_KEY, JWT_SECRET, MODEL_PATH, DATABASE_URL
├── ml/
│   ├── data/          prepare.py (SAMSum, DialogSum, AMI), format.py
│   ├── train.py  evaluate.py  extractive_baseline.py  chunking.py  latency.py  search_eval.py
│   ├── kaggle/        train_samsum.ipynb, train_ami.ipynb, ablations.ipynb, train_action_items.ipynb
│   ├── action_items/  label.csv, train_classifier.py, evaluate.py
│   ├── baselines/     gemini_baseline.py (offline only)
│   ├── notebooks/     error_analysis.ipynb
│   ├── checkpoints/   gitignored — downloaded from HF Hub for inference
│   └── requirements.txt  README.md
├── docs/              W1..W3 per member, decisions.md, problems.md, results.md, architecture.png
├── benchmarks/        summarization_results.md, ablations.md, action_item_eval.md, search_eval.md, human_eval.md, latency.md, raw/
├── demo/              demo_script.md, screenshots/, sample_audio/, sample_outputs/, video/
├── report/sections/   00_abstract … 12_limitations_future (one markdown per section)
└── data/README.md     gitignored folder; explains how to download datasets
```

## 3. API contract (frozen on Day 0 so frontend and backend are built in parallel)

```
POST /auth/register            {email, password, name}          -> {token}
POST /auth/login               {email, password}                -> {token}
POST /meetings/upload          multipart: file, title           -> {meeting_id, status}
GET  /meetings                                                  -> [{id, title, created_at, status, summary_snippet}]
GET  /meetings/{id}                                             -> {id, title, status, summary, participants,
                                                                    segments:[{speaker,start_sec,end_sec,text}],
                                                                    action_items:[{text,owner,source_segment_id}]}
GET  /meetings/{id}/status                                      -> {status}
GET  /search?q=                                                 -> [{meeting_id, title, speaker, text, score}]
GET  /meetings/{id}/export?format=txt|docx                      -> file
```
Status values: `uploaded | transcribing | summarizing | done | failed`.

---

## 4. Day 0 — setup (one afternoon, all three)

### Mounika — create the repository
```bash
mkdir ai-meeting-summarizer-nlp && cd ai-meeting-summarizer-nlp
git init -b main
git config user.name "Mounika" && git config user.email "<github-email>"
```
Create root files, one commit each: `README.md` (title + one-paragraph scope), `GIT_RULES.md`,
`PROJECT_PLAN.md` (this file), `.gitignore`, `.env.example`, placeholder `docker-compose.yml`,
`.github/pull_request_template.md`. Then the folder skeleton from §2 with a one-line `README.md`
in each empty folder (one commit: `add repository skeleton with folder readmes`).

`.gitignore` minimum:
```
.env
.env.*
!.env.example
__pycache__/
*.pyc
.venv/
node_modules/
.next/
data/
!data/README.md
ml/checkpoints/
*.db
*.wav
*.mp3
*.m4a
*.webm
!demo/sample_audio/*
.ipynb_checkpoints/
```

`.github/pull_request_template.md`:
```
## What changed
## Verify step (exact commands)
## Numbers produced (and the benchmarks/raw/ file)
## Weekly doc: docs/W<N>_<name>_<topic>.md
```

Then publish:
```bash
# GitHub -> New repository "ai-meeting-summarizer-nlp", private, no README/.gitignore/license
git remote add origin https://github.com/<org>/ai-meeting-summarizer-nlp.git
git push -u origin main
git tag -a repo-init -m "Empty skeleton, rules, plan" && git push --tags
git checkout -b dev && git push -u origin dev
```
Protect `main` (PR required). Add Krishna and Lahari as collaborators.
Add `.github/workflows/ci.yml`: ruff + pytest on `backend/`, `tsc --noEmit` + `next build` on
`frontend/`, on every PR. Put the status badge in `README.md`.

### Everyone
- Krishna & Lahari: `git clone` the new repo, `git checkout dev`, set `git config user.name/email`, `nbstripout --install`
- All three: Kaggle account with phone verification, GPU enabled in a test notebook (three accounts = 90 GPU h/week and a fallback)
- Lahari: private Hugging Face Hub repo for checkpoints; `HF_TOKEN` stored as a Kaggle secret
- Mounika: Deepgram account, API key in local `backend/.env` only
- Krishna: record 3 sample meetings (3–5 min, 2–3 speakers, ≤ 10 MB) → `demo/sample_audio/` via a small PR to `dev`
- 30-min sync: confirm §3 contract, write first entry in `docs/decisions.md`

---

## 5. Week 1 — Gate 1: audio → Deepgram → our model → summary on screen

### Mounika — `week1-mounika-fastapi-backend`
1. `backend/requirements.txt` (fastapi, uvicorn, sqlalchemy, pydantic-settings, python-jose, passlib[bcrypt], python-multipart, httpx, transformers, torch, sentence-transformers, spacy, numpy, python-docx), `backend/.env.example`, `backend/README.md`
2. `app/config.py`, `app/db.py`, `app/models.py` (User, Meeting with status enum, TranscriptSegment, ActionItem, SegmentEmbedding), `app/schemas.py`, `app/main.py` (CORS, routers, create tables)
3. `app/auth.py` (bcrypt, JWT, `get_current_user`), `app/routes/auth.py`
4. `app/routes/meetings.py` (upload → saves to `data/audio/`, list, get, status, delete), `app/pipeline.py` (BackgroundTask: transcribe → summarize → action_items → embeddings → done; failed + error message on exception)
5. `app/services/transcribe.py`: Deepgram prerecorded `?model=nova-2&diarize=true&punctuate=true&utterances=true&smart_format=true`; parse `utterances[]` into segments; merge consecutive same-speaker turns; configurable filler-word cleanup
6. Stubs with TODOs so the pipeline runs end to end: `summarize.py` (returns first 3 segments), `action_items.py` (returns `[]`), `search.py` (substring)
7. `tests/test_auth.py`, `tests/test_pipeline.py` (mocked Deepgram), `scripts/create_user.py`
8. `docs/W1_mounika_fastapi_backend.md`

### Krishna — `week1-krishna-frontend`
1. `npx create-next-app@latest frontend --typescript --tailwind --eslint --src-dir` (pages router), `frontend/.env.example`, `frontend/README.md`
2. `src/lib/types.ts` (mirrors §3), `src/lib/api.ts` (fetch wrapper with JWT header, one function per endpoint), `src/lib/auth.tsx` (AuthProvider, login/register/logout)
3. `frontend/mock/db.json` + `npx json-server` so the UI works before the backend exists
4. Pages: `login`, `register`, `dashboard` (meeting list with status badges), `summariser` (record or upload), `meetings/[id]` (summary, action items, speaker-grouped transcript; polls `/status`)
5. Components: `Layout`, `Recorder` (MediaRecorder → blob → `/meetings/upload`), `UploadAudio` (type/size validation), `StatusBadge`, `TranscriptView`, `ActionItemList`, `SummaryCard`
6. TypeScript strict on; `npm run build` passes
7. `docs/W1_krishna_frontend.md`

### Lahari — `week1-lahari-samsum-finetune`
1. `ml/requirements.txt` (transformers, datasets, evaluate, rouge-score, bert-score, accelerate, sentencepiece, nltk, huggingface_hub, pandas), `ml/README.md` (exact Kaggle steps)
2. `ml/data/prepare.py` (`load_samsum()` → `"Speaker: text\n"` lines + summary; `load_dialogsum()`, `load_ami()` as TODO stubs), `ml/data/format.py` (speaker tags on/off, filler cleanup)
3. `ml/train.py` (argparse: `--model` default `google/flan-t5-base`, `--dataset`, `--max_input 1024`, `--max_target 128`, `--epochs 3`, `--push_to_hub`, `--resume_from_checkpoint`; Seq2SeqTrainer; fp16; ROUGE each epoch; save best)
4. `ml/kaggle/train_samsum.ipynb`: pull the repo's `ml/` folder (or upload it as a private Kaggle dataset) → install → `python ml/train.py --push_to_hub`
5. `ml/extractive_baseline.py` (TextRank), `ml/evaluate.py` (`--system extractive|zero-shot|finetuned`; ROUGE-1/2/L + BERTScore → `benchmarks/raw/results.csv`; prints markdown table)
6. **Run on Kaggle** (~2–3 h on T4). Checkpoint → HF Hub. Notebook link + numbers in the doc
7. `backend/app/services/summarize.py` v1: load from `MODEL_PATH` at startup; single-pass `summarize(segments)`; hand to Mounika to wire in
8. `benchmarks/summarization_results.md` (3 rows), `docs/W1_lahari_samsum_finetune.md`

**Gate 1 (all three, fresh clone):** `.env` filled → backend + frontend running → upload `demo/sample_audio/meeting1.wav` → summary from the SAMSum checkpoint appears. Mounika opens `dev → main`, tags `week1-complete`.

---

## 6. Week 2 — Gate 2: real meetings, chunking, action items, search

### Lahari — `week2-lahari-ami-chunking`
- Implement `load_dialogsum()`, `load_ami()` in `prepare.py` (DialogSum first if AMI download is slow)
- `ml/kaggle/train_ami.ipynb`: continue fine-tuning the SAMSum checkpoint on AMI; evaluate on AMI test
- `train.py --lora` (PEFT, r=16): LoRA vs full fine-tuning on the same data — trainable params, GPU hours, ROUGE; this comparison is a headline result
- Publish the best checkpoint publicly on HF Hub with a proper model card (task, data, metrics, limitations)
- `ml/chunking.py`: split on speaker turns into ~800-token windows with 100 overlap
- `summarize.py` v2: hierarchical — chunk → summarize each → summarize the concatenation; speaker-tag flag
- `ml/kaggle/ablations.ipynb` + `evaluate.py --ablation`: speaker tags on/off, filler removal on/off, chunk 512/800/1024 → `benchmarks/raw/ablations.csv`
- Stretch: `allenai/led-base-16384` long-context comparison
- `benchmarks/summarization_results.md` (≥ 4 rows), `benchmarks/ablations.md`, `docs/W2_lahari_ami_chunking.md`

### Krishna — `week2-krishna-action-items`
- `action_items.py` v1 (spaCy `en_core_web_sm`): candidate if root verb is imperative OR sentence has a commitment pattern (`will`, `should`, `need to`, `have to`, `going to`, `let's`); owner = PERSON entity, else the speaker when first person; store `source_segment_id`
- `ml/action_items/label.csv`: hand-label ~300 sentences from AMI transcripts (action / not-action)
- `ml/action_items/train_classifier.py` (TF-IDF + logistic regression, local); `ml/kaggle/train_action_items.ipynb` (DistilBERT, Kaggle only)
- `ml/action_items/evaluate.py`: P/R/F1 rules vs classifier → `benchmarks/raw/action_items.csv`
- Frontend: clicking an action item scrolls to and highlights its transcript line; transcript shows real diarized speakers + timestamps
- `benchmarks/action_item_eval.md`, `docs/W2_krishna_action_items.md`

### Mounika — `week2-mounika-semantic-search`
- `search.py`: `all-MiniLM-L6-v2` embeddings per segment computed in the pipeline, stored in `segment_embeddings`; `/search` returns top-k by cosine similarity across the user's meetings
- `ml/search_eval.py` + `benchmarks/raw/search_queries.csv` (20 queries): substring vs semantic hits@5 → `benchmarks/search_eval.md`
- `app/services/audio.py`: ffmpeg conversion (m4a/mp3/webm → wav), 60-minute limit
- `pipeline.py` hardening: Deepgram timeout retry, failed-state handling, per-stage timing log
- Test on a real 20-minute recording
- `frontend/src/components/SearchDrawer.tsx` (Krishna reviews), `tests/test_search.py`
- `docs/W2_mounika_semantic_search.md`

**Gate 2:** 20-min recording → coherent chunked summary, action items with owners linked to lines, semantic search working, results table ≥ 4 rows. Krishna opens `dev → main`, tags `week2-complete`.

---

## 7. Week 3 — Gate 3: evaluation, demo, report

### Lahari — `week3-lahari-evaluation-report`
- `ml/baselines/gemini_baseline.py` (offline, `GEMINI_API_KEY`) → Gemini row in the results table
- Human eval: 10 meetings × 3 raters × coherence/coverage/factuality (1–5), Google Form → `benchmarks/human_eval.md`
- `ml/notebooks/error_analysis.ipynb`: 5 worst cases, categorized (hallucinated names, missed decisions, chunk-boundary loss)
- `ml/factuality.py`: NLI-based factual-consistency score (SummaC-style, `roberta-large-mnli` entailment between summary sentences and source) for every system → `benchmarks/factuality.md`; add a factuality column to the human eval
- `demo/hf_space/app.py`: public Gradio Space — paste a transcript or upload audio, get summary + action items; link in README and on each resume
- `ml/latency.py`: laptop CPU (fp32 and int8) vs Kaggle GPU vs Gemini API → `benchmarks/latency.md`
- Freeze `docs/results.md`; write `report/sections/03_data.md, 04_model.md, 05_chunking.md, 06_evaluation.md, 07_results.md`
- `docs/W3_lahari_evaluation_report.md`

### Krishna — `week3-krishna-demo-export`
- `app/services/export.py` (txt + docx via python-docx: summary, action items, speaker-grouped transcript); `GET /meetings/{id}/export`; `ExportButton.tsx`
- UI error/loading states (failed transcription, empty audio, oversized file)
- `demo/demo_script.md` (5-min viva flow), weekly screenshots, 2–3 min screen recording → `demo/video/`
- `report/sections/01_introduction.md, 02_architecture.md, 08_action_items.md, 10_demo.md`
- `docs/W3_krishna_demo_export.md`

### Mounika — `week3-mounika-docker-release`
- `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` (frontend + backend, model volume, env passthrough), tested on a clean machine
- `backend/scripts/seed.py`: demo user + processes `demo/sample_audio/*` so the demo is never empty
- int8 CPU inference for `summarize.py` (`optimum` dynamic quantization or `bitsandbytes`); record size and seconds-per-meeting before/after in `benchmarks/latency.md` — this is the "runs offline on a laptop" claim
- `README.md`: architecture image (`docs/architecture.png`), quickstart, results table from `benchmarks/`, model card link
- Secrets audit of full git history; `problems.md` / `decisions.md` tidy
- `report/sections/00_abstract.md, 09_search.md, 11_related_work.md, 12_limitations_future.md`
- Tag `v2.0` after Gate 3 · `docs/W3_mounika_docker_release.md`

**Gate 3:** clean machine `docker compose up` → seeded demo works; all `benchmarks/` files present; report assembled; video recorded. Lahari opens `dev → main`, tags `week3-complete` and `v2.0`.

---

## 8. Weekly sync (30 min, fixed day)
1. Each member: done / blocked / numbers so far
2. Update `docs/decisions.md`
3. Confirm gate status; assign the `dev → main` opener (W1 Mounika, W2 Krishna, W3 Lahari)

## 9. Risk register

| Risk | Owner | Mitigation |
|------|-------|-----------|
| AMI download / preprocessing slow | Lahari | Ship DialogSum checkpoint first; AMI is an upgrade, not a blocker |
| Kaggle quota runs out | Lahari | `flan-t5-base` not `-large`; 3 epochs; save every epoch; switch to Krishna's/Mounika's account |
| Kaggle session dies mid-training | Lahari | Checkpoint every epoch to HF Hub; `--resume_from_checkpoint` |
| Deepgram free credits exhausted | Mounika | Cache transcripts as JSON in `data/transcripts/`; never re-transcribe the same file |
| Frontend blocked on backend | Krishna | json-server mock from the Day 0 contract |
| Labeling 300 sentences is slow | Krishna | Label 150 first; rules-only is still a valid section |
| Model too slow on CPU for live demo | Mounika | Seed script pre-processes demo meetings; live upload uses a 3-min clip |

---

## 10. Making it resume-grade

**The pitch (use this wording everywhere — README, report, interviews):**
> A small, specialized summarization model that reaches *X %* of frontier-LLM quality on real meeting
> transcripts while running offline on a CPU at near-zero cost — so meeting audio never leaves the
> organization.

Do **not** claim to beat Gemini/GPT on ROUGE; you won't, and interviewers know it. Claim the
privacy/cost/latency trade-off with numbers, and show exactly where the small model loses (error
analysis). Honesty with numbers reads as senior; overclaiming reads as student.

**Artifacts a recruiter can click in under a minute**
1. Public HF Hub model card with metrics (Lahari)
2. Public Gradio Space demo (Lahari) — link it from README and resumes
3. README with CI badge, architecture diagram, 20-second GIF of the app, results table (Mounika)
4. 2–3 min demo video (Krishna)
5. A 600-word write-up per member (LinkedIn/Medium or `report/`) on *their* NLP piece

**Headline results the plan is designed to produce** (fill in real values)
| Claim | Source file |
|-------|-------------|
| Fine-tuned vs zero-shot: +X ROUGE-L on AMI | `benchmarks/summarization_results.md` |
| LoRA reaches Y % of full fine-tune quality with Z % of trainable params | `benchmarks/ablations.md` |
| Speaker tags in input: +A ROUGE-L | `benchmarks/ablations.md` |
| Factual consistency: our model vs Gemini vs extractive | `benchmarks/factuality.md` |
| Action items: F1 = B (classifier) vs C (rules) | `benchmarks/action_item_eval.md` |
| Semantic search hits@5 = D vs E substring | `benchmarks/search_eval.md` |
| int8 CPU inference: F s per 20-min meeting, G× smaller | `benchmarks/latency.md` |

**Resume bullet templates**
- Lahari — *Fine-tuned Flan-T5 (full + LoRA) on AMI/SAMSum for meeting summarization; +X ROUGE-L over zero-shot, Y % of Gemini quality at ~0 per-meeting cost; published model card and Gradio demo on Hugging Face.*
- Krishna — *Built speaker-linked action-item extraction (spaCy rules → DistilBERT classifier, F1 = B) and the Next.js front end for an end-to-end meeting-summarization system; produced the demo used in evaluation with N testers.*
- Mounika — *Designed the FastAPI pipeline (Deepgram diarization → summarization → Sentence-BERT semantic search, hits@5 D vs E), int8 CPU inference at F s/meeting, Dockerized with CI.*

**Deliberately out of scope** (would dilute Week 3): live streaming summarization, multi-language,
mobile app, LLM-based agents. Mention them in *Future Work*, don't build them.
