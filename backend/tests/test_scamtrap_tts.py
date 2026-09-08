"""Deterministic ScamTrap TTS tests; no test calls an external provider."""

from fastapi.testclient import TestClient

from app.main import app
from app.tts import TTSUnavailableError

client = TestClient(app)


def test_tts_is_disabled_when_config_off(monkeypatch):
    import app.tts
    class DummySettings:
        enable_cloud_tts = False
        tts_timeout_seconds = 5
    monkeypatch.setattr(app.tts, "settings", DummySettings())
    response = client.post(
        "/api/scamtrap/tts",
        json={"text": "Hello beta, who is this calling?", "persona_id": "elderly_grandma"},
    )
    assert response.status_code == 503


def test_tts_endpoint_returns_mocked_audio(monkeypatch):
    async def mock_synthesis(text, persona):
        assert persona == "elderly_grandma"
        return b"mock-mp3-audio" * 50

    monkeypatch.setattr("app.tts.synthesize_speech", mock_synthesis)
    response = client.post(
        "/api/scamtrap/tts",
        json={"text": "Hello beta, who is this calling?", "persona_id": "elderly_grandma"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert len(response.content) > 100


def test_tts_rejects_invalid_persona():
    response = client.post("/api/scamtrap/tts", json={"text": "Hello", "persona_id": "unknown"})
    assert response.status_code == 400


def test_tts_unavailable_error_is_explicit():
    assert str(TTSUnavailableError("disabled")) == "disabled"
