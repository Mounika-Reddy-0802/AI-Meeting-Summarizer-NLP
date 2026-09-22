"""ORM models for users, meetings and every pipeline output."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, Enum, Float, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    """Timezone-aware current time, used as a column default."""
    return datetime.now(UTC)


class MeetingStatus(StrEnum):
    """Pipeline states, in order, as frozen in PROJECT_PLAN.md §3."""

    UPLOADED = "uploaded"
    TRANSCRIBING = "transcribing"
    DIARIZING = "diarizing"
    SUMMARIZING = "summarizing"
    TAGGING = "tagging"
    LINKING = "linking"
    DONE = "done"
    FAILED = "failed"


class MinuteSection(StrEnum):
    """Sections of the structured minutes."""

    DECISIONS = "decisions"
    ACTIONS = "actions"
    PROBLEMS = "problems"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    meetings: Mapped[list["Meeting"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[MeetingStatus] = mapped_column(
        Enum(MeetingStatus, values_callable=lambda e: [m.value for m in e], native_enum=False),
        default=MeetingStatus.UPLOADED,
    )
    error: Mapped[str | None] = mapped_column(Text)

    audio_path: Mapped[str | None] = mapped_column(String(500))
    audio_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    duration_sec: Mapped[float | None] = mapped_column(Float)

    participants: Mapped[list[str]] = mapped_column(JSON, default=list)
    summary: Mapped[str | None] = mapped_column(Text)
    faithfulness_score: Mapped[float | None] = mapped_column(Float)
    stage_timings: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]

    user: Mapped[User] = relationship(back_populates="meetings")
    segments: Mapped[list["TranscriptSegment"]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="TranscriptSegment.position",
    )
    minute_items: Mapped[list["MinuteItem"]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="MinuteItem.position",
    )
    action_items: Mapped[list["ActionItem"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    speaker: Mapped[str] = mapped_column(String(50))
    start_sec: Mapped[float] = mapped_column(Float)
    end_sec: Mapped[float] = mapped_column(Float)
    text: Mapped[str] = mapped_column(Text)
    dialogue_act: Mapped[str | None] = mapped_column(String(30))

    meeting: Mapped[Meeting] = relationship(back_populates="segments")
    embedding: Mapped["SegmentEmbedding | None"] = relationship(
        back_populates="segment", cascade="all, delete-orphan"
    )


class MinuteItem(Base):
    __tablename__ = "minute_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    section: Mapped[MinuteSection] = mapped_column(
        Enum(MinuteSection, values_callable=lambda e: [m.value for m in e], native_enum=False)
    )
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    entailment: Mapped[float | None] = mapped_column(Float)
    supported: Mapped[bool | None]

    meeting: Mapped[Meeting] = relationship(back_populates="minute_items")
    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="minute_item",
        cascade="all, delete-orphan",
        order_by="Evidence.rank",
    )


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(100))
    due: Mapped[str | None] = mapped_column(String(50))
    source_segment_id: Mapped[int | None] = mapped_column(
        ForeignKey("transcript_segments.id", ondelete="SET NULL")
    )
    confidence: Mapped[float | None] = mapped_column(Float)

    meeting: Mapped[Meeting] = relationship(back_populates="action_items")


class SegmentEmbedding(Base):
    __tablename__ = "segment_embeddings"

    segment_id: Mapped[int] = mapped_column(
        ForeignKey("transcript_segments.id", ondelete="CASCADE"), primary_key=True
    )
    model_name: Mapped[str] = mapped_column(String(100))
    dim: Mapped[int] = mapped_column(Integer)
    vector: Mapped[bytes] = mapped_column(LargeBinary)  # float32 array bytes

    segment: Mapped[TranscriptSegment] = relationship(back_populates="embedding")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    minute_item_id: Mapped[int] = mapped_column(
        ForeignKey("minute_items.id", ondelete="CASCADE"), index=True
    )
    segment_id: Mapped[int] = mapped_column(
        ForeignKey("transcript_segments.id", ondelete="CASCADE")
    )
    rank: Mapped[int] = mapped_column(Integer)
    entailment: Mapped[float] = mapped_column(Float)

    minute_item: Mapped[MinuteItem] = relationship(back_populates="evidence")
    segment: Mapped[TranscriptSegment] = relationship()
