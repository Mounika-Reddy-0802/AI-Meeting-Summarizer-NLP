"""Local speaker diarisation with pyannote 3.1, and alignment of words to speaker turns."""

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.services.segment import Segment, SpeakerTurn, Word

PIPELINE_ID = "pyannote/speaker-diarization-3.1"
MIN_TURN_SEC = 0.6
FILLERS = {"um", "umm", "uh", "uhh", "erm", "er", "ah", "hmm", "mm"}


@lru_cache(maxsize=1)
def _load_pipeline() -> Any:
    from pyannote.audio import Pipeline

    pipeline = Pipeline.from_pretrained(PIPELINE_ID)
    if pipeline is None:
        raise RuntimeError(f"{PIPELINE_ID} is not in MODEL_DIR - run scripts/download_models.py")
    return pipeline


def diarize(wav_path: Path) -> list[SpeakerTurn]:
    """Speaker turns, relabelled `Speaker 1`, `Speaker 2`, … in order of first appearance."""
    import soundfile
    import torch

    samples, sample_rate = soundfile.read(str(wav_path), dtype="float32", always_2d=True)
    waveform = torch.from_numpy(samples.T.copy())
    annotation = _load_pipeline()({"waveform": waveform, "sample_rate": sample_rate})

    names: dict[str, str] = {}
    turns: list[SpeakerTurn] = []
    for turn, _track, label in annotation.itertracks(yield_label=True):
        name = names.setdefault(label, f"Speaker {len(names) + 1}")
        turns.append(SpeakerTurn(start=float(turn.start), end=float(turn.end), speaker=name))
    return sorted(turns, key=lambda t: t.start)


def _speaker_for(word: Word, turns: list[SpeakerTurn]) -> str:
    """Speaker whose turn overlaps the word most; the nearest turn if none overlaps."""
    best, best_overlap = None, 0.0
    for turn in turns:
        overlap = min(word.end, turn.end) - max(word.start, turn.start)
        if overlap > best_overlap:
            best, best_overlap = turn, overlap
    if best is None:
        middle = (word.start + word.end) / 2
        best = min(turns, key=lambda t: min(abs(middle - t.start), abs(middle - t.end)))
    return best.speaker


def _merge_same_speaker(segments: list[Segment]) -> list[Segment]:
    merged: list[Segment] = []
    for seg in segments:
        if merged and merged[-1].speaker == seg.speaker:
            last = merged[-1]
            last.end_sec = seg.end_sec
            last.text = f"{last.text} {seg.text}"
        else:
            merged.append(Segment(seg.speaker, seg.start_sec, seg.end_sec, seg.text))
    return merged


def _clean_text(text: str, remove_fillers: bool) -> str:
    if remove_fillers:
        kept = [t for t in text.split() if re.sub(r"[^\w]", "", t.lower()) not in FILLERS]
        text = " ".join(kept)
    return re.sub(r"\s+", " ", text).strip()


def build_segments(
    words: list[Word], turns: list[SpeakerTurn], remove_fillers: bool = False
) -> list[Segment]:
    """Assign words to speakers, merge consecutive same-speaker words, absorb very short turns."""
    if not words:
        return []
    labelled = [
        Segment(_speaker_for(w, turns) if turns else "Speaker 1", w.start, w.end, w.text)
        for w in words
    ]
    segments = _merge_same_speaker(labelled)

    # a turn shorter than MIN_TURN_SEC between two others is attached to the previous one
    changed = True
    while changed and len(segments) > 1:
        changed = False
        for i, seg in enumerate(segments):
            if seg.end_sec - seg.start_sec < MIN_TURN_SEC:
                neighbour = segments[i - 1] if i > 0 else segments[i + 1]
                seg.speaker = neighbour.speaker
                segments = _merge_same_speaker(segments)
                changed = True
                break

    result = []
    for seg in segments:
        seg.text = _clean_text(seg.text, remove_fillers)
        if seg.text:
            result.append(seg)
    return result
