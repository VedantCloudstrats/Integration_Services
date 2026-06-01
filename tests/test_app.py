from fastapi.testclient import TestClient

from app.main import app

API_KEY_HEADERS = {"X-API-Key": "dev-secret-key"}


def test_health_requires_api_key():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 401


def test_root_requires_api_key():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 401


def test_health_accepts_valid_api_key():
    client = TestClient(app)

    response = client.get("/health", headers=API_KEY_HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "mode": "stateless-validation",
    }


def test_invalid_api_key_is_rejected():
    client = TestClient(app)

    response = client.get("/health", headers={"X-API-Key": "wrong-key"})

    assert response.status_code == 403


def test_get_payload_endpoint_returns_empty_stateless_response():
    client = TestClient(app)

    response = client.get("/api/cmms/dart", headers=API_KEY_HEADERS)

    assert response.status_code == 200
    assert response.json()["T_DART"] == []


def test_post_endpoint_validates_and_acknowledges_payload():
    client = TestClient(app)
    payload = {
        "routine_id": 101,
        "old_dart_number": "DART-OLD",
        "new_dart_number": "DART-NEW",
        "hours": 2,
        "minutes": 30,
    }

    response = client.post(
        "/api/cmms/routines/complete",
        json=payload,
        headers=API_KEY_HEADERS,
    )

    assert response.status_code == 201
    assert response.json() == {
        "success": True,
        "message": "Routine completion payload validated successfully.",
        "data": {"routine_id": 101},
    }
