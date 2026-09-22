# backend/

Mounika - FastAPI + SQLAlchemy + SQLite API with a fully local pipeline:
ffmpeg -> faster-whisper (ASR) -> pyannote (diarisation) -> summarisation -> dialogue acts ->
action items -> evidence linking -> search embeddings. After the one-time model download the
backend makes no network calls.

## Requirements

- Python 3.11 - `winget install Python.Python.3.11`
- ffmpeg on PATH - `winget install Gyan.FFmpeg`, then open a new terminal and check `ffmpeg -version`
- A Hugging Face account that has accepted the terms of `pyannote/speaker-diarization-3.1` and
  `pyannote/segmentation-3.0` (needed once, for the download only)

## Setup (PowerShell, from `backend/`)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env   # then fill in the values in .env
```

| Variable | Meaning | Example |
|----------|---------|---------|
| `JWT_SECRET` | signs login tokens | output of `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `DATABASE_URL` | SQLite database, outside git | `sqlite:///../data/app.db` |
| `MODEL_DIR` | every downloaded model lives here | `../models` |
| `WHISPER_SIZE` | faster-whisper size | `small` |
| `HF_TOKEN` | read token for the pyannote download only | from huggingface.co/settings/tokens |

`.env`, the database, `data/` and `models/` are gitignored and must never be committed.

## Run

```powershell
python scripts/download_models.py          # once, with network
uvicorn app.main:app --reload --port 8000  # then works offline
python scripts/create_user.py --email you@example.com --name "You"   # optional, or use /auth/register
```

API docs at http://localhost:8000/docs. Upload a file on `POST /meetings/upload`, then poll
`GET /meetings/{id}/status` until `done` (or `failed`, with the reason in `stage`).

## Measure

```powershell
python scripts/asr_latency.py   # ASR + diarisation CPU time for demo/sample_audio/* -> benchmarks/raw/asr_latency.csv
```

## Test

```powershell
pip install pytest ruff
ruff check .
pytest -q
```

Tests use an in-memory database and replace ffmpeg, whisper and pyannote, so they need no models.

## Layout

```
app/main.py  config.py  db.py  models.py  schemas.py  auth.py  pipeline.py
app/routes/    auth.py  meetings.py  search.py
app/services/  audio.py  transcribe.py  diarize.py  segment.py  search.py  evidence.py
               summarize.py (Lahari)  dialogue_acts.py  action_items.py (Krishna)
scripts/       download_models.py  create_user.py  asr_latency.py
tests/         test_auth.py  test_pipeline.py
```
