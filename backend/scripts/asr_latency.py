"""Measure local ASR + diarisation wall time on CPU for each sample clip.

    python scripts/asr_latency.py                     # every clip in demo/sample_audio/
    python scripts/asr_latency.py clip.wav --out x.csv

Default output: benchmarks/raw/asr_latency.csv.

The transcript cache is bypassed so every stage really runs. Models load once before timing.
"""

import argparse
import csv
import os
import platform
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import REPO_DIR, apply_model_env, get_settings  # noqa: E402

FIELDS = [
    "file",
    "audio_sec",
    "convert_sec",
    "asr_sec",
    "diarize_sec",
    "total_sec",
    "real_time_factor",
    "words",
    "speakers",
    "whisper_size",
    "cpu",
    "threads",
    "measured_at",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--out", type=Path, default=REPO_DIR / "benchmarks/raw/asr_latency.csv")
    args = parser.parse_args()

    settings = get_settings()
    apply_model_env(settings, offline=True)
    from app.services import diarize, transcribe
    from app.services.audio import SUPPORTED_EXTENSIONS, prepare_audio

    files = args.files or sorted(
        p
        for p in (REPO_DIR / "demo/sample_audio").iterdir()
        if p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not files:
        print("No audio found in demo/sample_audio/ - pass files explicitly.")
        return 1

    print("loading models ...")
    transcribe._load_model(settings.whisper_size)
    diarize._load_pipeline()

    rows = []
    work_dir = Path(tempfile.mkdtemp(prefix="asr-latency-"))
    for path in files:
        start = time.perf_counter()
        prepared = prepare_audio(path, work_dir, settings.max_audio_minutes)
        converted = time.perf_counter()
        words = transcribe.transcribe(prepared.wav_path)
        transcribed = time.perf_counter()
        turns = diarize.diarize(prepared.wav_path)
        diarized = time.perf_counter()

        total = diarized - start
        row = {
            "file": path.name,
            "audio_sec": round(prepared.duration_sec, 2),
            "convert_sec": round(converted - start, 2),
            "asr_sec": round(transcribed - converted, 2),
            "diarize_sec": round(diarized - transcribed, 2),
            "total_sec": round(total, 2),
            "real_time_factor": round(total / prepared.duration_sec, 3),
            "words": len(words),
            "speakers": len({t.speaker for t in turns}),
            "whisper_size": settings.whisper_size,
            "cpu": platform.processor() or platform.machine(),
            "threads": os.cpu_count(),
            "measured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        rows.append(row)
        print(row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
