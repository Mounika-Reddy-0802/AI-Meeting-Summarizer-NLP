"""Summarisation (owner: Lahari). v1: single-pass summary from our fine-tuned Flan-T5.

The checkpoint is loaded from MODEL_DIR/summarizer (a plain seq2seq folder: config, weights,
tokenizer), for example:

    huggingface-cli download <user>/flan-t5-base-samsum --local-dir models/summarizer

Until that folder exists the summary falls back to the first three segments, so the pipeline and
its tests still run end to end. Minutes stay empty until section-conditioned generation (Week 3).
"""

import logging
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from app.services.segment import Segment

log = logging.getLogger(__name__)

SECTIONS = ("decisions", "actions", "problems")
MODEL_SUBDIR = "summarizer"
# Must match ml/data/format.py, which the checkpoint was trained with
PREFIX = "summarize:"
MAX_INPUT_TOKENS = 1024
MAX_SUMMARY_TOKENS = 128
NUM_BEAMS = 4
FALLBACK_SEGMENTS = 3


@dataclass
class SummaryResult:
    summary: str
    minutes: dict[str, list[str]] = field(default_factory=lambda: {s: [] for s in SECTIONS})


def model_path() -> Path:
    return get_settings().model_dir / MODEL_SUBDIR


def format_transcript(segments: list[Segment]) -> str:
    """`summarize:` then one `Speaker: text` line per segment, as in training."""
    lines = (f"{seg.speaker}: {seg.text.strip()}" for seg in segments if seg.text.strip())
    return PREFIX + "\n" + "\n".join(lines)


@lru_cache(maxsize=1)
def load():
    """Load tokenizer and model once; returns None when no checkpoint has been downloaded.

    Call at startup to pay the load time before the first meeting instead of during it.
    """
    path = model_path()
    if not (path / "config.json").exists():
        log.warning(
            "no summariser checkpoint in %s; using the first %d segments",
            path,
            FALLBACK_SEGMENTS,
        )
        return None

    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(path)
    model = AutoModelForSeq2SeqLM.from_pretrained(path).eval()
    log.info("loaded summariser from %s", path)
    return tokenizer, model


def summarize(segments: list[Segment]) -> SummaryResult:
    """Generic summary plus minute sentences per section."""
    if not segments:
        return SummaryResult(summary="")

    loaded = load()
    if loaded is None:
        summary = " ".join(f"{seg.speaker}: {seg.text}" for seg in segments[:FALLBACK_SEGMENTS])
        return SummaryResult(summary=summary)

    tokenizer, model = loaded
    # TODO(Lahari, W2): transcripts longer than 1024 tokens are truncated here; hierarchical
    # chunking on speaker turns replaces this single pass.
    inputs = tokenizer(
        format_transcript(segments),
        max_length=MAX_INPUT_TOKENS,
        truncation=True,
        return_tensors="pt",
    )
    import torch

    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=MAX_SUMMARY_TOKENS, num_beams=NUM_BEAMS)
    summary = tokenizer.decode(output[0], skip_special_tokens=True).strip()
    # TODO(Lahari, W3): fill minutes from `summarize decisions:` / `actions:` / `problems:`
    return SummaryResult(summary=summary)
