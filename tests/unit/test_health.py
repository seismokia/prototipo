from fastapi.testclient import TestClient

from api.config import Settings, get_settings
from api.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "asistente-patrimonial"
    assert body["version"] == get_settings().version


def test_health_reports_configured_environment() -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(environment="test")
    try:
        response = client.get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.json()["environment"] == "test"
