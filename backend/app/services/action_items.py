"""Action-item extraction (owner: Krishna). Week 1 stub so the pipeline runs end to end."""

from dataclasses import dataclass

from app.services.segment import Segment


@dataclass
class ActionItemResult:
    text: str
    owner: str | None
    due: str | None
    source_segment_id: int | None
    confidence: float | None


def extract(segments: list[Segment]) -> list[ActionItemResult]:
    """Action items with owner, due date and the segment they came from."""
    # TODO(Krishna): rules on statement-tagged segments, then the classifier and owner
    # resolution (PROJECT_PLAN.md §6-§7). Stub: no items.
    return []
