from fastapi.testclient import TestClient

from tests.conftest import register


def test_register_returns_token(client: TestClient) -> None:
    headers = register(client)
    assert headers["Authorization"].startswith("Bearer ")


def test_duplicate_email_is_rejected_case_insensitively(client: TestClient) -> None:
    register(client, "Mounika@Example.com")
    response = client.post(
        "/auth/register",
        json={"email": "mounika@example.com", "password": "password123", "name": "Again"},
    )
    assert response.status_code == 409


def test_short_password_and_bad_email_are_rejected(client: TestClient) -> None:
    short = {"email": "a@example.com", "password": "short", "name": "A"}
    bad_email = {"email": "not-an-email", "password": "password123", "name": "A"}
    assert client.post("/auth/register", json=short).status_code == 422
    assert client.post("/auth/register", json=bad_email).status_code == 422


def test_login_with_correct_and_wrong_password(client: TestClient) -> None:
    register(client, "user@example.com")
    ok = client.post("/auth/login", json={"email": "USER@example.com", "password": "password123"})
    wrong = client.post("/auth/login", json={"email": "user@example.com", "password": "nope-nope"})
    unknown = client.post("/auth/login", json={"email": "x@example.com", "password": "password123"})
    assert ok.status_code == 200 and ok.json()["token"]
    assert wrong.status_code == 401
    assert unknown.status_code == 401


def test_protected_routes_need_a_valid_token(client: TestClient) -> None:
    assert client.get("/meetings").status_code == 401
    assert client.get("/meetings", headers={"Authorization": "Bearer garbage"}).status_code == 401
    assert client.get("/meetings", headers=register(client)).status_code == 200
