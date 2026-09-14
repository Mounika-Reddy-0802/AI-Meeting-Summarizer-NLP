import uuid

from fastapi.testclient import TestClient

from app.services.diarize import build_segments
from app.services.segment import SpeakerTurn, Word
from tests.conftest import TURNS, WORDS, FakeModels, register

STAGES = {
    "audio",
    "transcribe",
    "diarize",
    "summarize",
    "dialogue_acts",
    "action_items",
    "evidence",
    "embeddings",
}


def upload(client: TestClient, headers: dict[str, str], content: bytes | None = None) -> int:
    body = content if content is not None else uuid.uuid4().bytes
    response = client.post(
        "/meetings/upload",
        files={"file": ("meeting.m4a", body, "audio/mp4")},
        data={"title": "Launch sync"},
        headers=headers,
    )
    assert response.status_code == 202, response.text
    assert response.json()["status"] == "uploaded"
    return response.json()["meeting_id"]


# --- alignment ---


def test_words_are_assigned_to_overlapping_speaker_turns() -> None:
    segments = build_segments(WORDS, TURNS)
    assert [s.speaker for s in segments] == ["Speaker 1", "Speaker 2", "Speaker 1"]
    assert segments[0].text == "Let's ship on Friday."
    assert segments[1].text == "Um, Priya will test it."


def test_turn_shorter_than_threshold_is_absorbed_by_neighbour() -> None:
    words = [Word(0, 1, "one"), Word(1, 2, "two"), Word(2.0, 2.3, "yes"), Word(2.4, 3.5, "three")]
    turns = [
        SpeakerTurn(0, 2, "Speaker 1"),
        SpeakerTurn(2, 2.3, "Speaker 2"),
        SpeakerTurn(2.3, 4, "Speaker 1"),
    ]
    segments = build_segments(words, turns)
    assert len(segments) == 1
    assert segments[0].text == "one two yes three"


def test_filler_cleanup_removes_fillers_but_keeps_backchannels() -> None:
    words = [Word(0, 1, "Um,"), Word(1, 2, "uh-huh"), Word(2, 3, "okay"), Word(3, 4, "uh")]
    assert build_segments(words, [], remove_fillers=True)[0].text == "uh-huh okay"
    assert build_segments(words, [], remove_fillers=False)[0].text == "Um, uh-huh okay uh"


# --- pipeline through the API ---


def test_upload_runs_every_stage_to_done(
    client: TestClient, auth_headers: dict[str, str], fake_models: FakeModels
) -> None:
    meeting_id = upload(client, auth_headers)

    status = client.get(f"/meetings/{meeting_id}/status", headers=auth_headers).json()
    assert status["status"] == "done"
    assert status["elapsed_sec"] >= 0

    meeting = client.get(f"/meetings/{meeting_id}", headers=auth_headers).json()
    assert meeting["participants"] == ["Speaker 1", "Speaker 2"]
    assert [s["speaker"] for s in meeting["segments"]] == ["Speaker 1", "Speaker 2", "Speaker 1"]
    assert meeting["summary"].startswith("Speaker 1: Let's ship on Friday.")
    assert meeting["minutes"] == {"decisions": [], "actions": [], "problems": []}
    assert meeting["faithfulness"] == {"score": None, "unsupported_count": 0}

    listed = client.get("/meetings", headers=auth_headers).json()
    assert listed[0]["id"] == meeting_id and listed[0]["summary_snippet"]

    hits = client.get("/search", params={"q": "priya"}, headers=auth_headers).json()
    assert [h["speaker"] for h in hits] == ["Speaker 2"]


def test_stage_timings_are_recorded(
    client: TestClient, auth_headers: dict[str, str], fake_models: FakeModels
) -> None:
    from app.db import SessionLocal
    from app.models import Meeting

    meeting_id = upload(client, auth_headers)
    with SessionLocal() as db:
        timings = db.get(Meeting, meeting_id).stage_timings
    assert set(timings) == STAGES
    assert all(seconds >= 0 for seconds in timings.values())


def test_same_file_is_never_transcribed_twice(
    client: TestClient, auth_headers: dict[str, str], fake_models: FakeModels
) -> None:
    content = uuid.uuid4().bytes
    first = upload(client, auth_headers, content)
    second = upload(client, auth_headers, content)
    assert fake_models.transcribe_calls == 1
    assert fake_models.diarize_calls == 1
    for meeting_id in (first, second):
        meeting = client.get(f"/meetings/{meeting_id}", headers=auth_headers).json()
        assert meeting["status"] == "done"


def test_exception_marks_meeting_failed_with_reason(
    client: TestClient, auth_headers: dict[str, str], fake_models: FakeModels
) -> None:
    fake_models.transcribe_error = RuntimeError("model missing")
    meeting_id = upload(client, auth_headers)
    status = client.get(f"/meetings/{meeting_id}/status", headers=auth_headers).json()
    assert status["status"] == "failed"
    assert status["stage"] == "transcribe failed: RuntimeError: model missing"


def test_unsupported_and_empty_uploads_are_rejected(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    text_file = client.post(
        "/meetings/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        data={"title": "x"},
        headers=auth_headers,
    )
    empty = client.post(
        "/meetings/upload",
        files={"file": ("empty.wav", b"", "audio/wav")},
        data={"title": "x"},
        headers=auth_headers,
    )
    assert text_file.status_code == 415
    assert empty.status_code == 422


def test_other_users_cannot_see_or_delete_a_meeting(
    client: TestClient, auth_headers: dict[str, str], fake_models: FakeModels
) -> None:
    meeting_id = upload(client, auth_headers)
    other = register(client, "other@example.com")
    assert client.get(f"/meetings/{meeting_id}", headers=other).status_code == 404
    assert client.delete(f"/meetings/{meeting_id}", headers=other).status_code == 404
    assert client.get("/search", params={"q": "priya"}, headers=other).json() == []


def test_delete_removes_the_meeting(
    client: TestClient, auth_headers: dict[str, str], fake_models: FakeModels
) -> None:
    meeting_id = upload(client, auth_headers)
    assert client.delete(f"/meetings/{meeting_id}", headers=auth_headers).status_code == 204
    assert client.get(f"/meetings/{meeting_id}", headers=auth_headers).status_code == 404
    assert client.get("/meetings", headers=auth_headers).json() == []
