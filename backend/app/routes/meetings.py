"""Meeting upload, listing, detail, status, evidence and delete."""

import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import get_settings
from app.db import get_db
from app.models import Evidence, Meeting, MeetingStatus, MinuteItem, User
from app.pipeline import run_pipeline
from app.schemas import (
    ActionItemOut,
    EvidenceOut,
    FaithfulnessOut,
    MeetingDetail,
    MeetingListItem,
    MinuteItemOut,
    MinutesOut,
    SegmentOut,
    StatusOut,
    UploadOut,
)
from app.services.audio import SUPPORTED_EXTENSIONS

router = APIRouter(prefix="/meetings", tags=["meetings"])

RUNNING = {
    MeetingStatus.TRANSCRIBING,
    MeetingStatus.DIARIZING,
    MeetingStatus.SUMMARIZING,
    MeetingStatus.TAGGING,
    MeetingStatus.LINKING,
}
SNIPPET_CHARS = 160


def _get_owned(db: Session, meeting_id: int, user: User) -> Meeting:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None or meeting.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting


async def _save_upload(file: UploadFile, max_bytes: int) -> Path:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Unsupported file type; use {allowed}"
        )
    uploads = get_settings().audio_dir / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    path = uploads / f"{uuid.uuid4().hex}{suffix}"
    size = 0
    with path.open("wb") as out:
        while chunk := await file.read(1 << 20):
            size += len(chunk)
            if size > max_bytes:
                out.close()
                path.unlink(missing_ok=True)
                raise HTTPException(
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File is too large"
                )
            out.write(chunk)
    if size == 0:
        path.unlink(missing_ok=True)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="The file is empty")
    return path


@router.post("/upload", response_model=UploadOut, status_code=status.HTTP_202_ACCEPTED)
async def upload(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(..., min_length=1, max_length=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadOut:
    """Store the recording and start processing it in the background."""
    path = await _save_upload(file, get_settings().max_upload_mb * 1024 * 1024)
    meeting = Meeting(user_id=user.id, title=title.strip(), audio_path=str(path))
    db.add(meeting)
    db.commit()
    background.add_task(run_pipeline, meeting.id)
    return UploadOut(meeting_id=meeting.id, status=meeting.status)


@router.get("", response_model=list[MeetingListItem])
def list_meetings(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[MeetingListItem]:
    """The user's meetings, newest first."""
    meetings = db.scalars(
        select(Meeting).where(Meeting.user_id == user.id).order_by(Meeting.created_at.desc())
    )
    return [
        MeetingListItem(
            id=m.id,
            title=m.title,
            created_at=m.created_at,
            status=m.status,
            summary_snippet=(m.summary or "")[:SNIPPET_CHARS] or None,
        )
        for m in meetings
    ]


@router.get("/{meeting_id}", response_model=MeetingDetail)
def get_meeting(
    meeting_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MeetingDetail:
    """Full meeting: summary, minutes with evidence ids, transcript and action items."""
    meeting = _get_owned(db, meeting_id, user)
    minutes = MinutesOut()
    for item in meeting.minute_items:
        getattr(minutes, item.section.value).append(
            MinuteItemOut(
                id=item.id,
                text=item.text,
                evidence=[ev.segment_id for ev in item.evidence],
                entailment=item.entailment,
                supported=item.supported,
            )
        )
    return MeetingDetail(
        id=meeting.id,
        title=meeting.title,
        status=meeting.status,
        participants=meeting.participants,
        summary=meeting.summary,
        minutes=minutes,
        segments=[SegmentOut.model_validate(seg) for seg in meeting.segments],
        action_items=[ActionItemOut.model_validate(item) for item in meeting.action_items],
        faithfulness=FaithfulnessOut(
            score=meeting.faithfulness_score,
            unsupported_count=sum(1 for item in meeting.minute_items if item.supported is False),
        ),
    )


@router.get("/{meeting_id}/status", response_model=StatusOut)
def get_status(
    meeting_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> StatusOut:
    """Current pipeline stage, error reason if failed, and seconds since processing began."""
    meeting = _get_owned(db, meeting_id, user)
    start = meeting.started_at or meeting.created_at
    end = meeting.finished_at or datetime.now(UTC)
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    if end.tzinfo is None:
        end = end.replace(tzinfo=UTC)
    if meeting.status == MeetingStatus.FAILED:
        stage = meeting.error
    else:
        stage = meeting.status.value if meeting.status in RUNNING else None
    return StatusOut(
        status=meeting.status,
        stage=stage,
        elapsed_sec=round(max((end - start).total_seconds(), 0.0), 1),
    )


@router.get("/{meeting_id}/evidence", response_model=list[EvidenceOut])
def get_evidence(
    meeting_id: int,
    sentence_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EvidenceOut]:
    """Supporting transcript segments for one minute sentence, best first."""
    meeting = _get_owned(db, meeting_id, user)
    item = db.get(MinuteItem, sentence_id)
    if item is None or item.meeting_id != meeting.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sentence not found")
    rows = db.scalars(
        select(Evidence).where(Evidence.minute_item_id == item.id).order_by(Evidence.rank)
    )
    return [
        EvidenceOut(
            segment_id=ev.segment_id,
            speaker=ev.segment.speaker,
            text=ev.segment.text,
            entailment=ev.entailment,
        )
        for ev in rows
    ]


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    """Delete the meeting and its upload; the wav and cache go when no other meeting uses them."""
    meeting = _get_owned(db, meeting_id, user)
    if meeting.status in RUNNING:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Meeting is still processing")
    settings = get_settings()
    audio_hash, audio_path = meeting.audio_hash, meeting.audio_path
    db.delete(meeting)
    db.commit()

    if audio_path:
        Path(audio_path).unlink(missing_ok=True)
    if audio_hash and not db.scalar(
        select(func.count()).select_from(Meeting).where(Meeting.audio_hash == audio_hash)
    ):
        (settings.audio_dir / f"{audio_hash}.wav").unlink(missing_ok=True)
        (settings.transcripts_dir / f"{audio_hash}.json").unlink(missing_ok=True)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
