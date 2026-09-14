"""Summarisation (owner: Lahari). Week 1 stub so the pipeline runs end to end."""

from dataclasses import dataclass, field

from app.services.segment import Segment

SECTIONS = ("decisions", "actions", "problems")


@dataclass
class SummaryResult:
    summary: str
    minutes: dict[str, list[str]] = field(default_factory=lambda: {s: [] for s in SECTIONS})


def summarize(segments: list[Segment]) -> SummaryResult:
    """Generic summary plus minute sentences per section."""
    # TODO(Lahari): load the fine-tuned Flan-T5 checkpoint from MODEL_DIR at startup and
    # generate the summary (PROJECT_PLAN.md §5 Lahari task 7). Stub: the first 3 segments.
    summary = " ".join(f"{seg.speaker}: {seg.text}" for seg in segments[:3])
    return SummaryResult(summary=summary)
