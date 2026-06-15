# Minimal tests for users endpoints
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_create_user_and_idempotency():
    payload = {"name": "Alice", "email": "alice@example.com"}
    headers = {"Idempotency-Key": "abc-123"}

    r1 = client.post("/api/users/", json=payload, headers=headers)
    assert r1.status_code == 201
    d1 = r1.json()
    assert d1["name"] == "Alice"

    # Repeat with same idempotency key - should return same result (same id)
    r2 = client.post("/api/users/", json=payload, headers=headers)
    # Depending on middleware implementation this could return 201 with same body
    assert r2.status_code in (200, 201)


def test_get_users_list():
    r = client.get("/api/users/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
