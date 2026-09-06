from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_is_available():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_detection_rejects_non_audio_upload():
    response = client.post(
        "/api/detect",
        files={"file": ("not-audio.txt", b"not audio", "text/plain")},
    )
    assert response.status_code == 400


def test_decloak_requires_an_audio_extension():
    response = client.post(
        "/api/decloak",
        files={"file": ("not-audio.txt", b"not audio", "text/plain")},
    )
    assert response.status_code == 400
