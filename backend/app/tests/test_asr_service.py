import base64

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.asr import router as asr_router
from app.core.config import get_settings
from app.domain.schemas.asr import AsrTranscriptStatus, AsrTranscriptionRequest
from app.services.asr_data_policy_guard import AsrDataPolicyBlockedError
from app.services.asr_service import AsrRequestValidationError, AsrService


@pytest.fixture(autouse=True)
def reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _audio_data_uri(raw: bytes = b"RIFF-fake-wav") -> str:
    return "data:audio/wav;base64," + base64.b64encode(raw).decode("ascii")


def _request_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "childId": "asr_child_demo",
        "sessionId": "asr_session_demo",
        "audio": {
            "data": _audio_data_uri(),
            "format": "wav",
            "sampleRateHz": 16000,
            "channelCount": 1,
            "durationMs": 1200,
        },
        "language": "zh-CN",
        "mode": "confirm_before_send",
        "metadata": {"mock_transcript": "我想聊恐龙"},
    }
    payload.update(overrides)
    return payload


def test_mock_asr_returns_pending_transcript_for_confirmation() -> None:
    response = AsrService().transcribe(
        AsrTranscriptionRequest.model_validate(_request_payload())
    )

    assert response.status == AsrTranscriptStatus.OK
    assert response.transcript == "我想聊恐龙"
    assert response.requires_confirmation is True
    assert response.provider == "mock"
    assert response.model == "mock-asr-v0"


def test_asr_rejects_unsupported_format() -> None:
    payload = _request_payload()
    payload["audio"]["format"] = "m4a"
    payload["audio"]["data"] = "data:audio/m4a;base64," + base64.b64encode(
        b"fake-m4a"
    ).decode("ascii")

    with pytest.raises(AsrRequestValidationError) as exc_info:
        AsrService().transcribe(AsrTranscriptionRequest.model_validate(payload))

    assert exc_info.value.error_code == "unsupported_audio_format"


def test_mimo_asr_is_policy_blocked_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHILD_AI_ASR_PROVIDER", "mimo")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_ENABLED", "false")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_API_KEY", "")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO", "false")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED", "false")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED", "false")
    get_settings.cache_clear()

    with pytest.raises(AsrDataPolicyBlockedError) as exc_info:
        AsrService().transcribe(
            AsrTranscriptionRequest.model_validate(_request_payload())
        )

    assert "mimo_asr_disabled" in str(exc_info.value)
    assert "child_audio_not_allowed" in str(exc_info.value)


def test_asr_router_mock_smoke() -> None:
    app = FastAPI()
    app.include_router(asr_router, prefix="/api/v1")
    client = TestClient(app)

    response = client.post("/api/v1/asr/transcribe", json=_request_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["transcript"] == "我想聊恐龙"
    assert body["requiresConfirmation"] is True
