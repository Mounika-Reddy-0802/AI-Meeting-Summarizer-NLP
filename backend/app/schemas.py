"""Request and response bodies, mirroring the API contract in PROJECT_PLAN.md §3.

`entailment`, `supported` and `faithfulness.score` are null until the linking stage has run.
"""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.models import MeetingStatus

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

# SQLite returns naive datetimes; every stored time is UTC, so say so in the response
UTCDateTime = Annotated[
    datetime, AfterValidator(lambda v: v if v.tzinfo else v.replace(tzinfo=UTC))
]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- auth ---


class RegisterIn(BaseModel):
    email: str = Field(max_length=254, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)


class LoginIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class TokenOut(BaseModel):
    token: str


# --- meetings ---


class UploadOut(BaseModel):
    meeting_id: int
    status: MeetingStatus


class MeetingListItem(ORMModel):
    id: int
    title: str
    created_at: UTCDateTime
    status: MeetingStatus
    summary_snippet: str | None = None


class SegmentOut(ORMModel):
    id: int
    speaker: str
    start_sec: float
    end_sec: float
    text: str
    dialogue_act: str | None = None


class MinuteItemOut(BaseModel):
    id: int
    text: str
    evidence: list[int] = []
    entailment: float | None = None
    supported: bool | None = None


class MinutesOut(BaseModel):
    decisions: list[MinuteItemOut] = []
    actions: list[MinuteItemOut] = []
    problems: list[MinuteItemOut] = []


class ActionItemOut(ORMModel):
    text: str
    owner: str | None = None
    due: str | None = None
    source_segment_id: int | None = None
    confidence: float | None = None


class FaithfulnessOut(BaseModel):
    score: float | None = None
    unsupported_count: int = 0


class MeetingDetail(BaseModel):
    id: int
    title: str
    status: MeetingStatus
    participants: list[str] = []
    summary: str | None = None
    minutes: MinutesOut = MinutesOut()
    segments: list[SegmentOut] = []
    action_items: list[ActionItemOut] = []
    faithfulness: FaithfulnessOut = FaithfulnessOut()


class EvidenceOut(BaseModel):
    segment_id: int
    speaker: str
    text: str
    entailment: float


class StatusOut(BaseModel):
    status: MeetingStatus
    stage: str | None = None
    elapsed_sec: float


# --- search ---


class SearchHit(BaseModel):
    meeting_id: int
    title: str
    segment_id: int
    speaker: str
    text: str
    score: float
