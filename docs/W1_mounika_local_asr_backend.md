# W1 — Mounika — local ASR backend

Branch `week1-mounika-local-asr-backend` · PROJECT_PLAN.md §5 tasks 1–10

## What I built

- **API** (FastAPI): `/auth/register`, `/auth/login`, `/meetings/upload`, `GET /meetings`,
  `/meetings/{id}`, `/meetings/{id}/status`, `/meetings/{id}/evidence`, `DELETE /meetings/{id}`,
  `/search`, all matching the §3 contract. Every meeting route checks the owner.
- **Database** (SQLAlchemy + SQLite): `users`, `meetings` (status enum, error, stage timings, audio
  hash, faithfulness score), `transcript_segments` (nullable `dialogue_act`), `minute_items`,
  `action_items`, `segment_embeddings`, `evidence`. Deleting a meeting removes all its rows.
- **Auth**: bcrypt password hashes, 24 h JWT, `get_current_user` dependency.
- **Pipeline** (background task): audio → transcribe → diarize → summarize → dialogue acts →
  action items → evidence → embeddings → `done`. Status is committed at each stage so the UI can
  poll it; wall time per stage goes to `meetings.stage_timings`; any exception gives `failed` with
  a readable reason such as `audio failed: audio is 61.0 min; the limit is 60 min`.
- **Audio**: ffmpeg converts any of wav/mp3/m4a/webm/ogg/flac/mp4/aac/opus to 16 kHz mono wav named
  by the file's SHA-256; ffprobe enforces the 60-minute limit.
- **ASR**: faster-whisper `small`, int8, CPU, English, VAD filter, word timestamps.
- **Diarisation**: pyannote `speaker-diarization-3.1`; labels renamed `Speaker 1..n` in order of first
  appearance. Each word goes to the turn it overlaps most; consecutive same-speaker words merge;
  turns under 0.6 s join their neighbour; optional filler removal keeps backchannels.
- **Cache**: `data/transcripts/<sha256>.json` stores words and turns, so the same file is never
  transcribed or diarised twice.
- **Offline**: all model caches live under `MODEL_DIR`; the app sets `HF_HUB_OFFLINE=1`, so it can
  only load what `scripts/download_models.py` fetched.
- **Stubs with TODOs** so the pipeline runs end to end: `summarize.py` (first 3 segments, Lahari),
  `dialogue_acts.py` and `action_items.py` (Krishna), `evidence.py` (mine, W3), substring
  `search.py` (mine, hybrid in W2).
- **Scripts**: `download_models.py`, `create_user.py`, `asr_latency.py`.
- **Tests**: 15 pytest tests (auth, alignment, full pipeline with fake models, cache, failure,
  ownership, delete).

## How to run

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

- Tests: `pytest -q` → 15 passed; `ruff check .` clean.
- ASR + diarisation CPU timing for the three sample clips: **not measured yet**. It needs the clips in
  `demo/sample_audio/` (Krishna) and the pyannote download (HF token with accepted terms). Then
  `python scripts/asr_latency.py` writes `benchmarks/raw/asr_latency.csv`.

## For the team

- Krishna: `entailment`, `supported` and `faithfulness.score` are `null` until the linking stage has
  run — `types.ts` should allow `null` for those. `GET /meetings/{id}/status` returns the failure
  reason in `stage` when `status` is `failed`. Upload returns `202`.
- Lahari: `summarize(segments: list[Segment]) -> SummaryResult(summary, minutes)` is the interface the
  pipeline calls; `Segment` is in `app/services/segment.py`.

## What's next

- Run `asr_latency.py` on the three sample clips once they and the pyannote weights are available.
- Wire Lahari's `summarize.py` v1 for Gate 1 and run the offline end-to-end check.
- Week 2: hybrid BM25 + MiniLM search, pipeline stage timeouts, 20-minute recording timings.
