"""Evidence linking and faithfulness (owner: Mounika). Week 1 stub; implemented in Week 3."""

from dataclasses import dataclass

from app.services.segment import Segment

SUPPORT_THRESHOLD = 0.5


@dataclass(frozen=True)
class MinuteSentence:
    id: int
    text: str


@dataclass(frozen=True)
class EvidenceLink:
    minute_item_id: int
    segment_id: int
    rank: int
    entailment: float


def link(sentences: list[MinuteSentence], segments: list[Segment]) -> list[EvidenceLink]:
    """Top supporting segments per minute sentence with their entailment probability."""
    # TODO(Mounika, W3): hybrid top-5 retrieval + nli-deberta-v3-base entailment, tau tuned
    # on the labelled dev set (PROJECT_PLAN.md §7). Stub: no links.
    return []
