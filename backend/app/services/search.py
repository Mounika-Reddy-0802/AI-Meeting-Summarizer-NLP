"""Transcript search (owner: Mounika). Week 1: substring search; hybrid BM25 + dense in Week 2."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Meeting, TranscriptSegment
from app.schemas import SearchHit
from app.services.segment import Segment


def index_segments(segments: list[Segment]) -> None:
    """Compute and store search embeddings for a meeting's segments."""
    # TODO(Mounika, W2): all-MiniLM-L6-v2 vectors into segment_embeddings (PROJECT_PLAN.md §6).


def search(db: Session, user_id: int, query: str, k: int) -> list[SearchHit]:
    """Case-insensitive substring match over the user's transcript segments."""
    needle = query.strip().lower()
    if not needle:
        return []
    rows = db.execute(
        select(TranscriptSegment, Meeting.title)
        .join(Meeting, Meeting.id == TranscriptSegment.meeting_id)
        .where(Meeting.user_id == user_id)
        .where(func.lower(TranscriptSegment.text).contains(needle, autoescape=True))
        .order_by(Meeting.created_at.desc(), TranscriptSegment.position)
        .limit(k)
    ).all()
    return [
        SearchHit(
            meeting_id=seg.meeting_id,
            title=title,
            segment_id=seg.id,
            speaker=seg.speaker,
            text=seg.text,
            score=float(seg.text.lower().count(needle)),
        )
        for seg, title in rows
    ]
