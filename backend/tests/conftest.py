"""Test setup: in-memory database, temporary data folder, and fake ASR/diarisation models."""

import hashlib
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

os.environ["JWT_SECRET"] = "test-secret-that-is-at-least-32-characters"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="meeting-tests-")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.services import audio, diarize, transcribe  # noqa: E402
from app.services.segment import SpeakerTurn, Word  # noqa: E402

WORDS = [
    Word(0.0, 0.5, "Let's"),
    Word(0.5, 1.0, "ship"),
    Word(1.0, 1.6, "on"),
    Word(1.6, 2.2, "Friday."),
    Word(2.6, 3.0, "Um,"),
    Word(3.0, 3.5, "Priya"),
    Word(3.5, 4.0, "will"),
    Word(4.0, 4.6, "test"),
    Word(4.6, 5.2, "it."),
    Word(5.6, 6.4, "Agreed."),
]
TURNS = [
    SpeakerTurn(0.0, 2.3, "Speaker 1"),
    SpeakerTurn(2.5, 5.3, "Speaker 2"),
    SpeakerTurn(5.5, 6.5, "Speaker 1"),
]


@pytest.fixture(autouse=True)
def fresh_database() -> Iterator[None]:
    from app import models  # noqa: F401

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def register(client: TestClient, email: str = "mounika@example.com") -> dict[str, str]:
    """Create a user and return its Authorization header."""
    response = client.post(
        "/auth/register", json={"email": email, "password": "password123", "name": "Test"}
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    return register(client)


class FakeModels:
    """Replaces ffmpeg, whisper and pyannote; counts how often each model ran."""

    def __init__(self) -> None:
        self.transcribe_calls = 0
        self.diarize_calls = 0
        self.transcribe_error: Exception | None = None

    def prepare_audio(self, source: Path, audio_dir: Path, max_minutes: int) -> audio.PreparedAudio:
        sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
        return audio.PreparedAudio(audio_dir / f"{sha256}.wav", sha256, 6.5)

    def transcribe(self, wav_path: Path) -> list[Word]:
        self.transcribe_calls += 1
        if self.transcribe_error is not None:
            raise self.transcribe_error
        return list(WORDS)

    def diarize(self, wav_path: Path) -> list[SpeakerTurn]:
        self.diarize_calls += 1
        return list(TURNS)


@pytest.fixture
def fake_models(monkeypatch: pytest.MonkeyPatch) -> FakeModels:
    fakes = FakeModels()
    monkeypatch.setattr(audio, "prepare_audio", fakes.prepare_audio)
    monkeypatch.setattr(transcribe, "transcribe", fakes.transcribe)
    monkeypatch.setattr(diarize, "diarize", fakes.diarize)
    return fakes
