# AI Meeting Summarizer (NLP) — Four-Week Plan, Built From Scratch

**Evidence-grounded structured minutes from meeting audio, with a small fine-tuned model that runs offline.**

Team: **Krishna · Lahari · Mounika** · Duration: **4 weeks** (Mon 14 Sep → Sun 11 Oct 2026) ·
Branch names, docs and gates follow `GIT_RULES.md`. This file supersedes the earlier three-week plan.

---

## 0. The idea in one paragraph (memorise this)

Most meeting summarisers give you a paragraph and ask you to trust it. Ours produces **structured
minutes** — *Decisions*, *Action items with owners*, *Open problems* — where **every line is linked to
the transcript turns that support it** and carries a **faithfulness score**, using a **250M-parameter
seq2seq model we fine-tuned ourselves** that runs **fully offline on a laptop CPU**. Speech-to-text and
speaker diarisation are also local; **no audio or text ever leaves the machine** and there is no cloud
service in the application path. The NLP work is in four places: (1) domain-adaptive fine-tuning
plus hierarchical chunking for long transcripts, (2) a **dialogue-act tagger** that lets us filter
backchannels and find commitments before generation, (3) **section-conditioned generation** — one
model, prompted per section, evaluated against the AMI section annotations, and (4) an
**NLI-based evidence-linking module** that grounds each generated sentence and flags unsupported ones.
Frontier LLMs appear only as an *offline baseline row* in the results table, never in the app.

**Research questions the plan is built to answer**

| RQ | Question | Answered in |
|----|----------|-------------|
| RQ1 | Does SAMSum→AMI adaptive fine-tuning + speaker-turn chunking make a small model competitive on 20–60 min transcripts? | W1–W2, `benchmarks/summarization_results.md` |
| RQ2 | Do section-conditioned generation and dialogue-act input filtering beat one generic summary for *decisions / actions / problems*? | W3, `benchmarks/structured_minutes.md`, `benchmarks/ablations.md` |
| RQ3 | Can NLI-based evidence linking flag unsupported sentences reliably (agreement with human factuality ratings)? | W3–W4, `benchmarks/factuality.md`, `benchmarks/human_eval.md` |
| RQ4 | What do LoRA and int8 quantisation cost in quality versus full fine-tuning and fp32? | W2, W4, `benchmarks/ablations.md`, `benchmarks/latency.md` |

**Ground rules**

- Everything starts from the Day-0 skeleton already on `main`. Nothing is copied from any earlier project.
- **All model training runs on Kaggle GPUs, never on laptops.** Laptops are for code, the app, and
  inference on saved checkpoints. Checkpoints travel Kaggle → private Hugging Face Hub → laptop.
  (Kaggle and the Hub are training/storage infrastructure; neither is called by the running app.)

- **No cloud service in the application path.** ASR, diarisation, summarisation, tagging, search and
  faithfulness scoring all run locally from downloaded weights. The only network call the app can make
  is the one-time weight download.

- Every number in the report comes from a script in the repo writing a file in `benchmarks/raw/`.
- Only the three members ever appear as author, committer or contributor (GIT_RULES §0).

---

## 1. Ownership

| Member | Owns | NLP contribution defended in the viva |
|--------|------|----------------------------------------|
| **Lahari** | `ml/` (data, training, evaluation), `backend/app/services/summarize.py`, `docs/results.md` | Adaptive fine-tuning SAMSum→AMI, hierarchical chunking, LoRA vs full fine-tune, section-conditioned generation, ROUGE/BERTScore, human evaluation |
| **Krishna** | `frontend/`, `backend/app/services/dialogue_acts.py`, `backend/app/services/action_items.py`, `ml/dialogue_acts/`, `ml/action_items/`, `demo/` | Dialogue-act tagger (MRDA), action-item extraction with owner resolution (rules → classifier), demo |
| **Mounika** | `backend/` (API, DB, auth, pipeline, local ASR + diarisation), `backend/app/services/search.py`, `backend/app/services/evidence.py`, docker, release | Local ASR/diarisation pipeline, hybrid BM25 + dense search, NLI evidence linking and faithfulness scoring, int8 inference |

Folder owner reviews any PR touching their folder.

## 2. Final repository layout

```
AI-Meeting-Summarizer-NLP/
├── README.md  GIT_RULES.md  PROJECT_PLAN.md  BLUEPRINT.md
├── .gitignore  .env.example  docker-compose.yml
├── .github/pull_request_template.md  .github/workflows/ci.yml
├── frontend/                       Next.js + TypeScript + Tailwind
│   ├── src/lib/       types.ts, api.ts, auth.tsx
│   ├── src/pages/     login, register, dashboard, summariser, meetings/[id]
│   ├── src/components/ Recorder, UploadAudio, TranscriptView, MinutesView, ActionItemList,
│   │                   EvidencePanel, SearchDrawer, ExportButton, StatusBadge
│   ├── mock/db.json   json-server data for development without the backend
│   └── .env.example   NEXT_PUBLIC_API_URL
├── backend/                        FastAPI + SQLAlchemy + SQLite
│   ├── app/main.py, config.py, db.py, models.py, schemas.py, auth.py, pipeline.py
│   ├── app/routes/    auth.py, meetings.py, search.py
│   ├── app/services/  transcribe.py (faster-whisper), diarize.py (pyannote), audio.py,
│   │                  summarize.py, dialogue_acts.py, action_items.py, evidence.py, search.py, export.py
│   ├── scripts/       seed.py, create_user.py, download_models.py
│   ├── tests/
│   └── .env.example   JWT_SECRET, DATABASE_URL, MODEL_DIR, WHISPER_SIZE, HF_TOKEN (download only)
├── ml/
│   ├── data/          prepare.py (SAMSum, DialogSum, AMI), ami_sections.py (NXT parser), qmsum.py, format.py
│   ├── train.py  evaluate.py  extractive_baseline.py  chunking.py  latency.py  search_eval.py  factuality_eval.py
│   ├── kaggle/        train_samsum.ipynb, train_ami.ipynb, train_sections.ipynb, ablations.ipynb,
│   │                  train_dialogue_acts.ipynb, train_action_items.ipynb
│   ├── dialogue_acts/ prepare_mrda.py, train.py, evaluate.py
│   ├── action_items/  label.csv, train_classifier.py, evaluate.py
│   ├── baselines/     llm_baseline.py (offline only, never imported by backend/)
│   ├── notebooks/     error_analysis.ipynb
│   ├── checkpoints/   gitignored — downloaded from HF Hub for inference
│   └── requirements.txt  README.md
├── docs/              W1..W4 per member, decisions.md, problems.md, results.md, architecture.png
├── benchmarks/        summarization_results.md, structured_minutes.md, ablations.md, dialogue_act_eval.md,
│                      action_item_eval.md, factuality.md, search_eval.md, human_eval.md, latency.md, raw/
├── demo/              demo_script.md, screenshots/, sample_audio/, sample_outputs/, video/
├── report/sections/   00_abstract … 13_limitations_future (one markdown per section)
└── data/README.md     gitignored folder; explains how to download datasets
```

## 3. API contract (frozen on Day 0; frontend and backend build in parallel)

```
POST /auth/register            {email, password, name}          -> {token}
POST /auth/login               {email, password}                -> {token}
POST /meetings/upload          multipart: file, title           -> {meeting_id, status}
GET  /meetings                                                  -> [{id, title, created_at, status, summary_snippet}]
GET  /meetings/{id}                                             -> {id, title, status, participants,
                                                                    summary,                       # generic abstract
                                                                    minutes: {decisions:[...], actions:[...], problems:[...]},
                                                                    segments:[{id, speaker, start_sec, end_sec, text, dialogue_act}],
                                                                    action_items:[{text, owner, due, source_segment_id, confidence}],
                                                                    faithfulness: {score, unsupported_count}}
GET  /meetings/{id}/evidence   ?sentence_id=                    -> [{segment_id, speaker, text, entailment}]
GET  /meetings/{id}/status                                      -> {status, stage, elapsed_sec}
GET  /search?q=&k=                                              -> [{meeting_id, title, segment_id, speaker, text, score}]
GET  /meetings/{id}/export?format=txt|docx                      -> file
```
Each item in `minutes.*` is `{id, text, evidence:[segment_id], entailment, supported:bool}`.
Status values: `uploaded | transcribing | diarizing | summarizing | tagging | linking | done | failed`.

---

## 4. Day 0 — already done · Day 0.5 — cleanup and accounts (Mon 14 Sep, all three)

Day 0 (repo skeleton, CI, PR template, `repo-init` tag) is on `main`. Before Week 1 branches are cut:

**Mounika — repository cleanup (`REPO_FIXES.md`, do it exactly, then delete that file)**

1. Remove the tool-configuration file and its commit from history, clean `.gitignore`, replace
   `PROJECT_PLAN.md` and `GIT_RULES.md` with these versions, add `BLUEPRINT.md`, update `README.md`
   to say four weeks, re-tag `repo-init`, reset `dev` to `main`. One force-push with `--force-with-lease`
   on `main` and `dev`, agreed by all three, logged in `docs/problems.md` as the first entry.

2. Verify: `git log --format='%an <%ae> | %cn | %s'` shows only the three members and no tool names; a
   case-insensitive grep of the tree for any tool or assistant name returns nothing.

**Everyone**

- Krishna & Lahari: fresh `git clone`, `git checkout dev`, `git config user.name/email` to their own GitHub identity, `nbstripout --install`.
- All three: Kaggle account with phone verification, GPU enabled in a test notebook (three accounts ≈ 90 GPU h/week).
- Lahari: private Hugging Face Hub repo for checkpoints; `HF_TOKEN` as a Kaggle secret. Accept the
  `pyannote/speaker-diarization-3.1` and `pyannote/segmentation-3.0` model terms on the Hub (needed once for download).

- Mounika: `backend/scripts/download_models.py` plan — Whisper `small` (int8 via faster-whisper), pyannote 3.1,
  `all-MiniLM-L6-v2`, `cross-encoder/nli-deberta-v3-base`; all cached under `MODEL_DIR`.

- Krishna: record 3 sample meetings (3–5 min, 2–3 speakers, ≤ 10 MB) → `demo/sample_audio/` via a small PR to `dev`.
- Lahari: **dataset verification (Day 1 task, half a day)** — confirm each loads: SAMSum (`Samsung/samsum`),
  DialogSum (`knkarthick/dialogsum`), AMI manual annotations v1.6.2 (NXT XML, from the AMI corpus site — the
  `abstractive/*.abssumm.xml` files hold abstract / decisions / problems / actions), QMSum (GitHub, Yale-LILY),
  MRDA via the `silicone` dataset (`mrda` config). Write findings and licences in `data/README.md`.

- 30-min sync: confirm §3 contract, record the "local ASR instead of a cloud API" decision and the dataset
  status as the first entries in `docs/decisions.md`.

---

## 5. Week 1 (14–20 Sep) — Gate 1: audio → local ASR + diarisation → our model → summary on screen

### Mounika — `week1-mounika-local-asr-backend`

1. `backend/requirements.txt` (fastapi, uvicorn, sqlalchemy, pydantic-settings, python-jose, passlib[bcrypt],
   python-multipart, faster-whisper, pyannote.audio, torch, torchaudio, transformers, sentence-transformers,
   rank-bm25, numpy, python-docx), `backend/.env.example`, `backend/README.md`

2. `app/config.py`, `app/db.py`, `app/models.py` (User, Meeting with status enum, TranscriptSegment with
   `dialogue_act` nullable, MinuteItem(section, text, entailment, supported), ActionItem, SegmentEmbedding,
   Evidence(minute_item_id, segment_id, entailment)), `app/schemas.py`, `app/main.py` (CORS, routers, create tables)

3. `app/auth.py` (bcrypt, JWT, `get_current_user`), `app/routes/auth.py`
4. `app/routes/meetings.py` (upload → `data/audio/`, list, get, status, delete), `app/pipeline.py`
   (BackgroundTask: transcribe → diarize → summarize → dialogue_acts → action_items → evidence → embeddings → done;
   `failed` + error message on exception; per-stage timing written to the meeting row)

5. `app/services/transcribe.py`: faster-whisper `small`, `compute_type=int8`, word timestamps, VAD filter;
   `app/services/diarize.py`: pyannote 3.1 → speaker turns; align words to turns → segments
   `{speaker, start, end, text}`; merge consecutive same-speaker turns; configurable filler-word cleanup.
   Cache transcripts as JSON in `data/transcripts/` keyed by file hash — never re-transcribe the same file

6. `app/services/audio.py`: ffmpeg conversion (m4a/mp3/webm → 16 kHz mono wav), 60-minute limit
7. Stubs with TODOs so the pipeline runs end to end: `summarize.py` (first 3 segments), `dialogue_acts.py`
   (returns `None`), `action_items.py` (`[]`), `evidence.py` (`[]`), `search.py` (substring)

8. `tests/test_auth.py`, `tests/test_pipeline.py` (ASR and diarisation mocked), `scripts/create_user.py`,
   `scripts/download_models.py`

9. Measure: ASR + diarisation wall time on a laptop CPU for the 3 sample clips → `benchmarks/raw/asr_latency.csv`
10. `docs/W1_mounika_local_asr_backend.md`

### Krishna — `week1-krishna-frontend`

1. `npx create-next-app@latest frontend --typescript --tailwind --eslint --src-dir` (pages router), `.env.example`, `README.md`
2. `src/lib/types.ts` (mirrors §3 including `minutes` and `evidence`), `src/lib/api.ts` (fetch wrapper with JWT
   header, one function per endpoint), `src/lib/auth.tsx`

3. `frontend/mock/db.json` + `npx json-server` so the UI works before the backend exists
4. Pages: `login`, `register`, `dashboard` (meeting list with status badges), `summariser` (record or upload),
   `meetings/[id]` (generic summary, minutes tabs Decisions/Actions/Problems, speaker-grouped transcript; polls `/status` and shows the current stage)

5. Components: `Layout`, `Recorder` (MediaRecorder → blob → `/meetings/upload`), `UploadAudio`, `StatusBadge`,
   `TranscriptView`, `MinutesView`, `ActionItemList`, `SummaryCard`; `EvidencePanel` as a placeholder

6. TypeScript strict on; `npm run build` passes
7. `docs/W1_krishna_frontend.md`

### Lahari — `week1-lahari-samsum-finetune`

1. `ml/requirements.txt` (transformers, datasets, evaluate, rouge-score, bert-score, accelerate, peft, sentencepiece,
   nltk, huggingface_hub, pandas, lxml), `ml/README.md` (exact Kaggle steps)

2. `ml/data/prepare.py` (`load_samsum()` → `"Speaker: text\n"` lines + summary; `load_dialogsum()`, `load_ami()`
   as stubs), `ml/data/format.py` (speaker tags on/off, filler cleanup, section prefix)

3. `ml/train.py` (argparse: `--model` default `google/flan-t5-base`, `--dataset`, `--max_input 1024`,
   `--max_target 128`, `--epochs 3`, `--lora`, `--push_to_hub`, `--resume_from_checkpoint`; Seq2SeqTrainer;
   fp16; ROUGE each epoch; save best)

4. `ml/kaggle/train_samsum.ipynb`: pull the repo's `ml/` → install → `python ml/train.py --push_to_hub`
5. `ml/extractive_baseline.py` (TextRank), `ml/evaluate.py` (`--system extractive|zero-shot|finetuned`;
   ROUGE-1/2/L + BERTScore → `benchmarks/raw/results.csv`; prints the markdown table)

6. **Run on Kaggle** (~2–3 h on a T4). Checkpoint → HF Hub. Notebook link + numbers in the weekly doc
7. `backend/app/services/summarize.py` v1: load from `MODEL_DIR` at startup; single-pass `summarize(segments)`; hand to Mounika to wire in
8. `benchmarks/summarization_results.md` (3 rows: extractive, zero-shot, fine-tuned on SAMSum test), `docs/W1_lahari_samsum_finetune.md`

**Gate 1 (all three, fresh clone):** `.env` filled → `download_models.py` → backend + frontend running →
upload `demo/sample_audio/meeting1.wav` → diarised transcript with real speaker labels and a summary from the
SAMSum checkpoint appear, with the network cable unplugged. Mounika opens `dev → main`, tags `week1-complete`.

---

## 6. Week 2 (21–27 Sep) — Gate 2: real meetings, chunking, dialogue acts, hybrid search

### Lahari — `week2-lahari-ami-chunking`

- Implement `load_dialogsum()`, `load_ami()` (plain AMI summaries) in `prepare.py`; `ml/data/ami_sections.py`
  parses the NXT `abssumm.xml` files into `{meeting_id, abstract, decisions, problems, actions}` and caches JSON
  (this feeds Week 3 — do it now)

- `ml/kaggle/train_ami.ipynb`: continue fine-tuning the SAMSum checkpoint on AMI; evaluate on AMI test
- `train.py --lora` (PEFT, r=16): LoRA vs full fine-tuning on identical data — trainable params, GPU hours, ROUGE
- `ml/chunking.py`: split on speaker turns into ~800-token windows with 100 overlap
- `summarize.py` v2: hierarchical — chunk → summarise each → summarise the concatenation; speaker-tag flag
- `ml/kaggle/ablations.ipynb` + `evaluate.py --ablation`: speaker tags on/off, filler removal on/off,
  chunk 512/800/1024 → `benchmarks/raw/ablations.csv`

- Publish the best checkpoint publicly on HF Hub with a model card (task, data, metrics, limitations)
- Stretch: `allenai/led-base-16384` long-context comparison
- `benchmarks/summarization_results.md` (≥ 5 rows), `benchmarks/ablations.md`, `docs/W2_lahari_ami_chunking.md`

### Krishna — `week2-krishna-dialogue-acts`

- `ml/dialogue_acts/prepare_mrda.py`: load MRDA (`silicone`, `mrda`), 5 basic labels
  (statement / question / backchannel / floor-grabber / disruption); build inputs as
  `prev_utterance [SEP] utterance` so the tagger sees one turn of context

- `ml/kaggle/train_dialogue_acts.ipynb` → fine-tune `distilroberta-base` (Kaggle only); `ml/dialogue_acts/evaluate.py`
  → macro-F1 and confusion matrix → `benchmarks/raw/dialogue_acts.csv`; compare against a TF-IDF + logistic
  regression baseline trained locally

- `backend/app/services/dialogue_acts.py`: tag every segment in the pipeline (batched CPU inference);
  stored in `TranscriptSegment.dialogue_act`

- `action_items.py` v1 (spaCy `en_core_web_sm`): candidate if segment is a *statement* AND (root verb is imperative
  OR a commitment pattern fires: `will`, `should`, `need to`, `have to`, `going to`, `let's`); store `source_segment_id`

- Frontend: transcript rows coloured by dialogue act with a legend; backchannels collapsed by default;
  clicking an action item scrolls to and highlights its transcript line; real speakers + timestamps shown

- `benchmarks/dialogue_act_eval.md`, `docs/W2_krishna_dialogue_acts.md`

### Mounika — `week2-mounika-hybrid-search`

- `search.py`: `all-MiniLM-L6-v2` embeddings per segment computed in the pipeline and stored in
  `segment_embeddings`; BM25 index (`rank_bm25`) per user; `/search` returns top-k by **reciprocal-rank fusion**
  of BM25 and cosine scores across the user's meetings

- `ml/search_eval.py` + `benchmarks/raw/search_queries.csv` (25 queries with relevant segment ids, labelled by the
  team on the 20-min recording): substring vs BM25 vs dense vs hybrid, hits@5 and MRR → `benchmarks/search_eval.md`

- `pipeline.py` hardening: stage timeouts, `failed` state with a readable reason, resumable from cached transcript
- Test the full pipeline on a real 20-minute recording; record per-stage CPU timings → `benchmarks/raw/pipeline_timing.csv`
- `frontend/src/components/SearchDrawer.tsx` (Krishna reviews), `tests/test_search.py`
- `docs/W2_mounika_hybrid_search.md`

**Gate 2:** 20-min recording → coherent chunked summary, transcript tagged with dialogue acts, rule-based
action items linked to lines, hybrid search working, results table ≥ 5 rows. Krishna opens `dev → main`,
tags `week2-complete`.

---

## 7. Week 3 (28 Sep–4 Oct) — Gate 3: structured minutes, evidence linking, action-item classifier

### Lahari — `week3-lahari-structured-minutes`

- Section-conditioned training set from `ami_sections.py`: one example per (meeting, section) with input
  `summarize <section>: <transcript>` and target the section text; also a `summarize abstract:` example.
  If AMI section volume is thin, augment with QMSum query/answer pairs whose queries ask for decisions/actions/problems

- `ml/kaggle/train_sections.ipynb`: continue from the AMI checkpoint; `--dataset sections`
- Three systems evaluated on AMI test per section (ROUGE-L, BERTScore):
  **S-A** generic summary split heuristically, **S-B** section-conditioned generation on the full chunked transcript,
  **S-C** section-conditioned generation on a **dialogue-act-filtered** transcript (backchannels and
  floor-grabbers removed; Krishna's tagger) → `benchmarks/raw/structured_minutes.csv`, `benchmarks/structured_minutes.md`

- `summarize.py` v3: returns `summary` + `minutes.{decisions, actions, problems}` as sentence lists
- Sentence-level `id`s so Mounika's evidence module can attach to them
- `docs/W3_lahari_structured_minutes.md`

### Mounika — `week3-mounika-evidence-linking`

- `backend/app/services/evidence.py`: for each minute sentence, retrieve top-5 transcript segments by the
  hybrid scorer from `search.py`, run `cross-encoder/nli-deberta-v3-base` (premise = segment window,
  hypothesis = sentence), keep max entailment; `supported = entailment ≥ τ`; meeting-level
  `faithfulness.score` = mean max-entailment (SummaC-ZS style); store rows in `Evidence`

- `GET /meetings/{id}/evidence`; `ml/factuality_eval.py`: faithfulness score for every system on AMI test
  (extractive, zero-shot, fine-tuned, S-B, S-C) → `benchmarks/raw/factuality.csv`, `benchmarks/factuality.md`

- Threshold τ chosen on a 60-sentence dev set labelled supported/unsupported by the team (kept in `benchmarks/raw/`)
- Frontend `EvidencePanel.tsx` (Krishna reviews): click a minute sentence → supporting turns with entailment bars;
  unsupported sentences marked with a warning badge

- `tests/test_evidence.py`; `docs/W3_mounika_evidence_linking.md`

### Krishna — `week3-krishna-action-items`

- `ml/action_items/label.csv`: hand-label ~300 statement-tagged AMI sentences (action / not-action) — label 150 first
- `ml/action_items/train_classifier.py` (TF-IDF + logistic regression, local); `ml/kaggle/train_action_items.ipynb`
  (DistilBERT, Kaggle only); `ml/action_items/evaluate.py`: P/R/F1 rules vs classifier vs rules+classifier
  → `benchmarks/raw/action_items.csv`, `benchmarks/action_item_eval.md`

- **Owner resolution**: first person → speaker; second person → the previous other speaker; PERSON entity
  wins if present; due-date from `dateparser` on the sentence; evaluate owner accuracy on the labelled set

- `app/services/export.py` (txt + docx via python-docx: minutes by section, action items with owners,
  speaker-grouped transcript); `GET /meetings/{id}/export`; `ExportButton.tsx`

- UI error/loading states (failed stage, empty audio, oversized file)
- `docs/W3_krishna_action_items.md`

**Gate 3:** 20-min recording → Decisions / Actions / Problems tabs populated, each sentence expandable to
its evidence with entailment, unsupported sentences flagged, action items with owners, docx export;
`benchmarks/` has structured_minutes, factuality and action_item_eval. Lahari opens `dev → main`, tags `week3-complete`.

---

## 8. Week 4 (5–11 Oct) — Gate 4: evaluation freeze, demo, report, viva

### Lahari — `week4-lahari-evaluation-report`

- `ml/baselines/llm_baseline.py` (offline script, key from an env var, never imported by `backend/`) → one
  frontier-LLM row per table for context; the pitch is the trade-off, not beating it

- Human eval: 10 meetings × 3 raters × {coherence, coverage, factuality} 1–5, on **S-C vs generic vs LLM**,
  blind order, Google Form export → `benchmarks/raw/human_eval.csv`, `benchmarks/human_eval.md`;
  Spearman correlation between our faithfulness score and rater factuality → the RQ3 number

- `ml/notebooks/error_analysis.ipynb`: 6 worst cases categorised (hallucinated names, missed decisions,
  chunk-boundary loss, wrong section, unsupported-but-true); a "failure exhibit" section for the viva

- Freeze `docs/results.md`; write `report/sections/03_data.md, 04_model.md, 05_chunking.md,
  06_structured_minutes.md, 08_evaluation.md, 09_results.md`

- `docs/W4_lahari_evaluation_report.md`

### Krishna — `week4-krishna-demo-export`

- `demo/demo_script.md` (5-min viva flow: upload → watch stages → minutes → click evidence → flagged sentence →
  action item owner → search → export → unplug network and repeat on a 3-min clip)

- Screenshots per week, 2–3 min screen recording with audio → `demo/video/`; 20-second GIF for the README
- Viva Q&A prep `docs/viva_qa.md` (see `BLUEPRINT.md §9`)
- `report/sections/01_introduction.md, 02_architecture.md, 07_dialogue_acts_action_items.md, 11_demo.md`
- `docs/W4_krishna_demo_export.md`

### Mounika — `week4-mounika-docker-release`

- `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` (frontend + backend, model volume,
  env passthrough), tested on a clean machine

- `backend/scripts/seed.py`: demo user + pre-processed `demo/sample_audio/*` so the demo is never empty
- int8 dynamic quantisation of the summariser for CPU; `ml/latency.py`: fp32 vs int8 seconds per 20-min meeting,
  model size, plus ASR/diarisation/tagging/linking stage times → `benchmarks/latency.md` — the "runs on a laptop" claim

- `README.md`: architecture image (`docs/architecture.png`), quickstart, results table from `benchmarks/`,
  model card link, GIF; secrets audit of full git history; `problems.md` / `decisions.md` tidy

- `report/sections/00_abstract.md, 10_search_evidence.md, 12_related_work.md, 13_limitations_future.md`
- Tag `v1.0` after Gate 4 · `docs/W4_mounika_docker_release.md`

**Gate 4:** clean machine `docker compose up` → seeded demo works offline; all `benchmarks/` files present;
report assembled; video recorded; viva Q&A rehearsed once. Mounika opens `dev → main`, tags `week4-complete` and `v1.0`.

---

## 9. Weekly sync (30 min, fixed day)

1. Each member: done / blocked / numbers so far
2. Update `docs/decisions.md`
3. Confirm gate status; `dev → main` opener rotates: W1 Mounika, W2 Krishna, W3 Lahari, W4 Mounika

## 10. Risk register

| Risk | Owner | Mitigation |
|------|-------|-----------|
| pyannote diarisation too slow on a laptop CPU | Mounika | Live demo uses a 3-min clip; longer meetings pre-processed by `seed.py`; whole pipeline can run once on a Kaggle GPU to produce cached transcripts |
| AMI NXT section annotations awkward to parse | Lahari | `ami_sections.py` built in Week 2 not Week 3; QMSum decision/action queries as the fallback training set |
| MRDA label mapping or dataset loading issues | Krishna | TF-IDF baseline first; if MRDA fails, use SwDA (`silicone`, `swda`) with the same collapsed labels |
| Kaggle quota runs out | Lahari | `flan-t5-base` not `-large`; 3 epochs; save every epoch; LoRA runs are cheap; switch accounts |
| Kaggle session dies mid-training | Lahari | Checkpoint every epoch to HF Hub; `--resume_from_checkpoint` |
| NLI flags too many true sentences | Mounika | Premise = segment ± 1 neighbour; τ tuned on the labelled dev set; report precision of flags honestly |
| Frontend blocked on backend | Krishna | json-server mock from the Day-0 contract |
| Labelling 300 sentences is slow | Krishna | 150 first; rules-only is still a valid section |
| Week 3 is the heaviest week | All | Week 2 already delivers the section parser and the DA tagger; nothing in Week 3 starts from zero |

---

## 11. Making it resume-grade

**The pitch (use this wording everywhere — README, report, interviews):**
> Structured, evidence-linked meeting minutes from a 250M-parameter model we fine-tuned ourselves: decisions,
> owned action items and open problems, each sentence grounded to the transcript turns that support it and
> scored for faithfulness — reaching *X %* of frontier-LLM quality on real meetings while running fully offline on
> a laptop CPU, so meeting audio never leaves the room.

Do **not** claim to beat a frontier LLM on ROUGE. Claim the privacy/cost/latency trade-off with numbers, show the
faithfulness flags catching real hallucinations, and show exactly where the small model loses (error analysis).
Honesty with numbers reads as senior; overclaiming reads as student.

**Artifacts a recruiter can click in under a minute**

1. Public HF Hub model card with metrics (Lahari)
2. README with CI badge, architecture diagram, 20-second GIF, results table (Mounika)
3. 2–3 min demo video (Krishna)
4. A 600-word write-up per member on *their* NLP piece (LinkedIn/Medium or `report/`)

**Headline results the plan is designed to produce** (fill in real values)

| Claim | Source file |
|-------|-------------|
| Fine-tuned vs zero-shot: +X ROUGE-L on AMI | `benchmarks/summarization_results.md` |
| LoRA reaches Y % of full fine-tune quality with Z % of trainable params | `benchmarks/ablations.md` |
| Section-conditioned + DA-filtered input: +A ROUGE-L on *decisions* over a generic summary | `benchmarks/structured_minutes.md` |
| Dialogue-act tagger: macro-F1 = B on MRDA | `benchmarks/dialogue_act_eval.md` |
| Faithfulness score correlates ρ = C with human factuality; flags catch D % of hallucinated sentences | `benchmarks/factuality.md`, `benchmarks/human_eval.md` |
| Action items: F1 = E (rules+classifier) vs F (rules); owner accuracy G % | `benchmarks/action_item_eval.md` |
| Hybrid search hits@5 = H vs I (dense) vs J (BM25) | `benchmarks/search_eval.md` |
| Whole pipeline on a laptop CPU: K min per 20-min meeting; int8 summariser L× smaller | `benchmarks/latency.md` |

**Resume bullet templates**

- Lahari — *Fine-tuned Flan-T5 (full + LoRA) on SAMSum→AMI for section-conditioned meeting minutes;
  +X ROUGE-L over zero-shot, dialogue-act-filtered input +A on decisions; published model card; ran a 3-rater human evaluation.*

- Krishna — *Built a dialogue-act tagger (MRDA, macro-F1 B) and speaker-attributed action-item extraction with
  owner resolution (F1 E), plus the Next.js front end for an end-to-end offline meeting-minutes system.*

- Mounika — *Designed a fully offline FastAPI pipeline (Whisper + pyannote diarisation → summarisation → NLI
  evidence linking, ρ = C with human factuality) with hybrid BM25 + dense search (hits@5 H), int8 CPU inference, Docker and CI.*

**Deliberately out of scope**: live streaming summarisation, multi-language, mobile app, chat-with-your-meeting.
Mention them in *Future Work*, don't build them.
