"""Background processing of one meeting: audio -> ASR -> diarisation -> NLP stages -> done.

Every stage commits the meeting status so GET /meetings/{id}/status can follow progress, and
records its wall time in `stage_timings`. Any exception marks the meeting `failed` with a reason.
Service modules are looked up at call time so tests can replace the heavy models.
"""

import logging
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.models import (
    ActionItem,
    Evidence,
    Meeting,
    MeetingStatus,
    MinuteItem,
    MinuteSection,
    TranscriptSegment,
)
from app.services import (
    action_items,
    audio,
    dialogue_acts,
    diarize,
    evidence,
    search,
    summarize,
    transcribe,
)
from app.services.segment import Segment

logger = logging.getLogger(__name__)


class _Run:
    """Tracks the current stage and per-stage timings for one pipeline run."""

    def __init__(self, db: Session, meeting: Meeting) -> None:
        self.db = db
        self.meeting = meeting
        self.stage = "starting"
        self.timings: dict[str, float] = {}

    def set_status(self, status: MeetingStatus) -> None:
        self.meeting.status = status
        self.db.commit()

    @contextmanager
    def timed(self, stage: str) -> Iterator[None]:
        self.stage = stage
        start = time.perf_counter()
        yield
        self.timings[stage] = round(time.perf_counter() - start, 3)
        self.meeting.stage_timings = dict(self.timings)
        self.db.commit()


def _store_segments(db: Session, meeting: Meeting, segments: list[Segment]) -> None:
    db.execute(delete(TranscriptSegment).where(TranscriptSegment.meeting_id == meeting.id))
    rows = [
        TranscriptSegment(
            meeting_id=meeting.id,
            position=i,
            speaker=seg.speaker,
            start_sec=seg.start_sec,
            end_sec=seg.end_sec,
            text=seg.text,
        )
        for i, seg in enumerate(segments)
    ]
    db.add_all(rows)
    db.flush()
    for seg, row in zip(segments, rows, strict=True):
        seg.id = row.id
    meeting.participants = list(dict.fromkeys(seg.speaker for seg in segments))


def _store_summary(
    db: Session, meeting: Meeting, result: summarize.SummaryResult
) -> list[MinuteItem]:
    db.execute(delete(MinuteItem).where(MinuteItem.meeting_id == meeting.id))
    meeting.summary = result.summary
    items = [
        MinuteItem(meeting_id=meeting.id, section=MinuteSection(section), position=i, text=text)
        for section, sentences in result.minutes.items()
        for i, text in enumerate(sentences)
    ]
    db.add_all(items)
    db.flush()
    return items


def _store_action_items(
    db: Session, meeting: Meeting, results: list[action_items.ActionItemResult]
) -> None:
    db.execute(delete(ActionItem).where(ActionItem.meeting_id == meeting.id))
    db.add_all(ActionItem(meeting_id=meeting.id, **vars(item)) for item in results)


def _store_evidence(
    db: Session, meeting: Meeting, items: list[MinuteItem], links: list[evidence.EvidenceLink]
) -> None:
    by_item: dict[int, list[evidence.EvidenceLink]] = {}
    for link in links:
        by_item.setdefault(link.minute_item_id, []).append(link)
        db.add(Evidence(**vars(link)))

    scores = []
    for item in items:
        item_links = by_item.get(item.id)
        if item_links:
            item.entailment = max(link.entailment for link in item_links)
            item.supported = item.entailment >= evidence.SUPPORT_THRESHOLD
            scores.append(item.entailment)
    meeting.faithfulness_score = sum(scores) / len(scores) if scores else None


def _process(run: _Run) -> None:
    db, meeting, settings = run.db, run.meeting, get_settings()

    run.set_status(MeetingStatus.TRANSCRIBING)
    with run.timed("audio"):
        prepared = audio.prepare_audio(
            Path(meeting.audio_path or ""), settings.audio_dir, settings.max_audio_minutes
        )
        meeting.audio_hash = prepared.sha256
        meeting.duration_sec = prepared.duration_sec
    cached_words, cached_turns = transcribe.read_cache(prepared.sha256)
    with run.timed("transcribe"):
        words = cached_words
        if words is None:
            words = transcribe.transcribe(prepared.wav_path)
            transcribe.write_cache(prepared.sha256, words=words)

    run.set_status(MeetingStatus.DIARIZING)
    with run.timed("diarize"):
        turns = cached_turns
        if turns is None:
            turns = diarize.diarize(prepared.wav_path)
            transcribe.write_cache(prepared.sha256, turns=turns)
        segments = diarize.build_segments(words, turns, settings.filler_cleanup)
        _store_segments(db, meeting, segments)

    run.set_status(MeetingStatus.SUMMARIZING)
    with run.timed("summarize"):
        items = _store_summary(db, meeting, summarize.summarize(segments))

    run.set_status(MeetingStatus.TAGGING)
    with run.timed("dialogue_acts"):
        for seg, act in zip(segments, dialogue_acts.tag(segments), strict=True):
            seg.dialogue_act = act
            row = db.get(TranscriptSegment, seg.id)
            if row is not None:
                row.dialogue_act = act
    with run.timed("action_items"):
        _store_action_items(db, meeting, action_items.extract(segments))

    run.set_status(MeetingStatus.LINKING)
    with run.timed("evidence"):
        sentences = [evidence.MinuteSentence(id=item.id, text=item.text) for item in items]
        _store_evidence(db, meeting, items, evidence.link(sentences, segments))
    with run.timed("embeddings"):
        search.index_segments(segments)

    meeting.status = MeetingStatus.DONE
    meeting.error = None


def run_pipeline(meeting_id: int, session_factory: Callable[[], Session] = SessionLocal) -> None:
    """Process one uploaded meeting to `done`, or leave it `failed` with a readable reason."""
    with session_factory() as db:
        meeting = db.get(Meeting, meeting_id)
        if meeting is None:
            logger.warning("meeting %s vanished before processing", meeting_id)
            return
        meeting.started_at = datetime.now(UTC)
        meeting.finished_at = None
        meeting.stage_timings = {}
        run = _Run(db, meeting)
        try:
            _process(run)
        except Exception as exc:
            if isinstance(exc, audio.AudioError):
                logger.warning("meeting %s rejected: %s", meeting_id, exc)
                reason = str(exc)
            else:
                logger.exception("meeting %s failed during %s", meeting_id, run.stage)
                reason = f"{type(exc).__name__}: {exc}"
            db.rollback()
            meeting = db.get(Meeting, meeting_id)
            if meeting is None:
                return
            meeting.status = MeetingStatus.FAILED
            meeting.error = f"{run.stage} failed: {reason}"[:1000]
            meeting.stage_timings = dict(run.timings)
        meeting.finished_at = datetime.now(UTC)
        db.commit()
