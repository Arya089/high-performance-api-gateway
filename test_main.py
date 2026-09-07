from fastapi.testclient import TestClient
from main import app, API_KEY

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_missing_api_key_returns_401():
    response = client.get("/users/1")
    assert response.status_code == 401


def test_unknown_service_returns_404():
    response = client.get(
        "/unknown-service/some-path",
        headers={"x-api-key": API_KEY},
    )
    assert response.status_code == 404
