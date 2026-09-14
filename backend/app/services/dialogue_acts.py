"""Dialogue-act tagging (owner: Krishna). Week 1 stub so the pipeline runs end to end."""

from app.services.segment import Segment


def tag(segments: list[Segment]) -> list[str | None]:
    """One label per segment: statement, question, backchannel, floor-grabber or disruption."""
    # TODO(Krishna): batched DistilRoBERTa MRDA tagger (PROJECT_PLAN.md §6). Stub: no labels.
    return [None for _ in segments]
