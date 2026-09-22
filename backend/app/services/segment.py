"""Plain data types passed between pipeline stages, independent of the database."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Word:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class SpeakerTurn:
    start: float
    end: float
    speaker: str


@dataclass
class Segment:
    """One speaker turn of the transcript. `id` is the database id once stored."""

    speaker: str
    start_sec: float
    end_sec: float
    text: str
    id: int | None = None
    dialogue_act: str | None = None
