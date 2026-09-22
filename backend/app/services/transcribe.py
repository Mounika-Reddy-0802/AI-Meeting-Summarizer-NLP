"""Local speech-to-text with faster-whisper, plus the per-file transcript cache."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.services.segment import SpeakerTurn, Word


@lru_cache(maxsize=1)
def _load_model(size: str) -> Any:
    from faster_whisper import WhisperModel

    return WhisperModel(size, device="cpu", compute_type="int8", local_files_only=True)


def transcribe(wav_path: Path) -> list[Word]:
    """Word-level transcript of an English recording, with VAD removing silence."""
    model = _load_model(get_settings().whisper_size)
    segments, _info = model.transcribe(
        str(wav_path),
        language="en",
        beam_size=5,
        vad_filter=True,
        word_timestamps=True,
    )
    words: list[Word] = []
    for segment in segments:
        for word in segment.words or []:
            text = word.word.strip()
            if text:
                words.append(Word(start=float(word.start), end=float(word.end), text=text))
    return words


# --- cache: data/transcripts/<sha256>.json holds raw words and speaker turns ---


def _cache_path(sha256: str) -> Path:
    return get_settings().transcripts_dir / f"{sha256}.json"


def read_cache(sha256: str) -> tuple[list[Word] | None, list[SpeakerTurn] | None]:
    """Cached words and turns for a file hash; either part is None if not cached yet."""
    path = _cache_path(sha256)
    if not path.exists():
        return None, None
    data = json.loads(path.read_text(encoding="utf-8"))
    words = [Word(**w) for w in data["words"]] if data.get("words") is not None else None
    turns = [SpeakerTurn(**t) for t in data["turns"]] if data.get("turns") is not None else None
    return words, turns


def write_cache(
    sha256: str, words: list[Word] | None = None, turns: list[SpeakerTurn] | None = None
) -> None:
    """Store words and/or turns for a file hash, keeping whatever is already cached."""
    cached_words, cached_turns = read_cache(sha256)
    words = words if words is not None else cached_words
    turns = turns if turns is not None else cached_turns
    path = _cache_path(sha256)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "sha256": sha256,
        "whisper_size": get_settings().whisper_size,
        "words": None if words is None else [w.__dict__ for w in words],
        "turns": None if turns is None else [t.__dict__ for t in turns],
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(path)
