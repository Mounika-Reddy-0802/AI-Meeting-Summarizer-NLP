# W1 · Mounika — FastAPI backend with local ASR and diarisation

Branch `week1-mounika-local-asr-backend` · PROJECT_PLAN.md §4 (Day 0.5 cleanup) and §5 Mounika tasks 1–10 · opens Gate 1 (`dev → main`)

## What I built

**API** (FastAPI) — `/auth/register`, `/auth/login`, `/meetings/upload`, `GET /meetings`,
`/meetings/{id}`, `/meetings/{id}/status`, `/meetings/{id}/evidence`, `DELETE /meetings/{id}`,
`/search`, all matching the §3 contract. Every meeting route checks the owner, so one user can never
read another's meeting by guessing an id. Upload returns `202`; `/status` returns the failure reason
in `stage` when `status` is `failed`.

**Database** (SQLAlchemy + SQLite) — `users`, `meetings` (status enum, error, stage timings, audio
hash, faithfulness score), `transcript_segments` (nullable `dialogue_act`), `minute_items`,
`action_items`, `segment_embeddings`, `evidence`. All seven tables exist from Week 1, so later weeks
fill columns rather than migrate schemas. Deleting a meeting removes all its rows.

**Auth** — bcrypt password hashes, 24 h JWT, a `get_current_user` dependency. `JWT_SECRET` must be at
least 32 characters or the app refuses to start.

**Pipeline** (background task) — audio → transcribe → diarize → summarize → dialogue acts → action
items → evidence → embeddings → `done`. Status is committed at each stage so the UI can poll it; wall
time per stage goes to `meetings.stage_timings`; any exception gives `failed` with a readable reason
such as `audio failed: audio is 61.0 min; the limit is 60 min`.

**Audio** — ffmpeg converts any of wav / mp3 / m4a / webm / ogg / flac / mp4 / aac / opus to 16 kHz
mono wav named by the file's SHA-256; ffprobe enforces the 60-minute limit.

**ASR** — faster-whisper `small`, int8, CPU, English, VAD filter, word timestamps. `small` rather than
`base` for proper nouns — names become action-item owners — and rather than `medium` for CPU time.

**Diarisation** — pyannote `speaker-diarization-3.1`; labels renamed `Speaker 1..n` in order of first
appearance. Each word goes to the turn it overlaps most; consecutive same-speaker words merge; turns
under 0.6 s join their neighbour; optional filler removal keeps backchannels (Krishna's tagger needs them).

**Cache** — `data/transcripts/<sha256>.json` stores words and turns, so the same file is never
transcribed or diarised twice.

**Offline** — every model cache lives under `MODEL_DIR`, and the app sets `HF_HUB_OFFLINE=1`, so it can
only load what `scripts/download_models.py` fetched. The privacy claim is enforced, not promised.

**Stubs with TODOs** so the pipeline runs end to end: `summarize.py` (first 3 segments — replaced by
Lahari's v1), `dialogue_acts.py` and `action_items.py` (Krishna, W2), `evidence.py` (mine, W3),
substring `search.py` (mine, hybrid in W2).

**Scripts** — `download_models.py`, `create_user.py`, `asr_latency.py`.

## How to run / verify

```powershell
cd backend
py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env          # set JWT_SECRET and HF_TOKEN
python scripts/download_models.py    # once, with network
uvicorn app.main:app --port 8000     # http://localhost:8000/docs
pip install pytest ruff; ruff check .; pytest -q
```

## Numbers

| Item | Value |
|---|---|
| Endpoints | 9, matching the §3 contract |
| Database tables | 7 |
| Tests | 15 passed (`pytest -q`); `ruff check .` clean |
| Audio formats accepted | 9, converted to 16 kHz mono wav |
| ASR + diarisation CPU time on the 3 sample clips | **not measured** — see Status |

## Status — verified by running, not by inspection

- ✅ **15 tests pass**: auth, word-to-turn alignment, the full pipeline with fake models, the transcript
  cache, failure handling, ownership, delete. They use an in-memory database and replace ffmpeg,
  Whisper and pyannote, so they need no models.
- ✅ **Contract checked from the frontend side**: Krishna's app ran against this backend (CORS, 422
  messages, register, upload, list, detail, status, the `failed` reason).
- ✅ **Tests still pass with Lahari's real `summarize.py`** in place of the stub, after resolving the
  one merge conflict at that path in her favour.
- ✅ Faster-whisper `small`, MiniLM and the NLI model are downloaded into `MODEL_DIR`.
- ⬜ **pyannote is not downloaded.** `download_models.py` needs `HF_TOKEN` in `backend/.env` from an
  account that has accepted the `speaker-diarization-3.1` and `segmentation-3.0` terms.
- ⬜ **`benchmarks/raw/asr_latency.csv` is not produced.** `asr_latency.py` is ready; it needs the three
  sample clips in `demo/sample_audio/` (Krishna) and pyannote.
- ⬜ **`main` on GitHub still has the pre-cleanup history.** `dev` and the `repo-init` tag were
  force-pushed; `main` is protected, so its push was rejected (`docs/problems.md`). Until it is
  pushed, PRs opened against `main` show false conflicts. Weekly PRs go to `dev` anyway.
- ⬜ PR to `dev` not opened yet.

## For the team

- Krishna: `entailment`, `supported` and `faithfulness.score` are `null` until the linking stage has
  run. `GET /meetings/{id}/status` returns the failure reason in `stage` when `status` is `failed`.
- Lahari: `summarize(segments: list[Segment]) -> SummaryResult(summary, minutes)` is the interface the
  pipeline calls; `Segment` lives in `app/services/segment.py`.

## Next (Week 2 — `week2-mounika-hybrid-search`)

- Push the cleaned `main` once protection is relaxed for one push (whole-team agreement, GIT_RULES §11).
- Run `asr_latency.py` once the clips and pyannote exist; merge Week 1 and tag `week1-complete`.
- Hybrid BM25 + MiniLM search, pipeline stage timeouts, 20-minute recording timings.
