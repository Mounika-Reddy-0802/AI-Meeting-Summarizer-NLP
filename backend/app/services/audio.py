"""Audio preparation: hash the upload, check its length, convert to 16 kHz mono wav with ffmpeg."""

import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac", ".mp4", ".aac", ".opus"}
SAMPLE_RATE = 16_000


class AudioError(Exception):
    """Raised with a message that can be shown to the user."""


@dataclass(frozen=True)
class PreparedAudio:
    wav_path: Path
    sha256: str
    duration_sec: float


def file_sha256(path: Path) -> str:
    """Hex SHA-256 of a file, read in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require(tool: str) -> str:
    found = shutil.which(tool)
    if found is None:
        raise AudioError(f"{tool} not found on PATH - install it with: winget install Gyan.FFmpeg")
    return found


def probe_duration(path: Path) -> float:
    """Duration in seconds as reported by ffprobe."""
    result = subprocess.run(
        [
            _require("ffprobe"),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return float(result.stdout.strip())
    except ValueError as exc:
        raise AudioError("the file could not be read as audio") from exc


def prepare_audio(source: Path, audio_dir: Path, max_minutes: int) -> PreparedAudio:
    """Convert an upload to `<audio_dir>/<sha256>.wav`, reusing an earlier conversion."""
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise AudioError(f"unsupported file type {source.suffix or '(none)'}")

    duration = probe_duration(source)
    if duration <= 0:
        raise AudioError("the audio file is empty")
    if duration > max_minutes * 60:
        raise AudioError(f"audio is {duration / 60:.1f} min; the limit is {max_minutes} min")

    sha256 = file_sha256(source)
    wav_path = audio_dir / f"{sha256}.wav"
    if not wav_path.exists():
        audio_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = wav_path.with_suffix(".tmp.wav")
        result = subprocess.run(
            [
                _require("ffmpeg"),
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-ac",
                "1",
                "-ar",
                str(SAMPLE_RATE),
                "-sample_fmt",
                "s16",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            tmp_path.unlink(missing_ok=True)
            raise AudioError(f"ffmpeg could not convert the file: {result.stderr.strip()[:300]}")
        tmp_path.replace(wav_path)

    return PreparedAudio(wav_path=wav_path, sha256=sha256, duration_sec=duration)
