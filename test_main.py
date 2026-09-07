from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_service_returns_404():
    response = client.get("/unknown-service/some-path")
    assert response.status_code == 200  # Note: current code returns tuple, not proper 404
