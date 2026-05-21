import base64
import io
import logging
import socket
from urllib.error import HTTPError

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.asr import router as asr_router
from app.core.config import get_settings
from app.middleware.request_id import RequestIdMiddleware


@pytest.fixture(autouse=True)
def reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)
    app.include_router(asr_router, prefix="/api/v1")
    return TestClient(app)


def _audio_data_uri(raw: bytes = b"RIFF-fake-wav", audio_format: str = "wav") -> str:
    return (
        f"data:audio/{audio_format};base64,"
        + base64.b64encode(raw).decode("ascii")
    )


def _request_payload() -> dict[str, object]:
    return {
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
    }


def _enable_mimo_asr_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHILD_AI_ASR_PROVIDER", "mimo")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_ENABLED", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_API_KEY", "test-api-key")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED", "true")
    get_settings.cache_clear()


def test_asr_api_mimo_policy_blocked_by_default(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    monkeypatch.setenv("CHILD_AI_ASR_PROVIDER", "mimo")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_ENABLED", "false")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_API_KEY", "")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO", "false")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED", "false")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED", "false")
    get_settings.cache_clear()

    response = client.post("/api/v1/asr/transcribe", json=_request_payload())

    assert response.status_code == 403
    assert "mimo_asr_disabled" in response.json()["detail"]
    assert "missing_mimo_asr_api_key" in response.json()["detail"]
    assert "child_audio_not_allowed" in response.json()["detail"]


def test_asr_api_timeout_maps_to_stable_504(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    _enable_mimo_asr_policy(monkeypatch)

    def fake_urlopen(_request: object, timeout: float) -> object:
        raise socket.timeout("timed out with test-api-key")

    monkeypatch.setattr("app.providers.asr.mimo_asr_provider.urlopen", fake_urlopen)

    response = client.post("/api/v1/asr/transcribe", json=_request_payload())

    assert response.status_code == 504
    assert response.json()["detail"] == "provider_timeout"
    assert "test-api-key" not in response.text
    assert "data:audio/wav;base64" not in response.text


def test_asr_api_http_error_maps_to_stable_502_without_raw_body(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    _enable_mimo_asr_policy(monkeypatch)
    raw_body = (
        b'{"error":"test-api-key data:audio/wav;base64,UklGRg== '
        b'private transcript"}'
    )

    def fake_urlopen(request: object, timeout: float) -> object:
        raise HTTPError(
            request.full_url,
            500,
            "Server Error",
            hdrs={},
            fp=io.BytesIO(raw_body),
        )

    monkeypatch.setattr("app.providers.asr.mimo_asr_provider.urlopen", fake_urlopen)

    response = client.post("/api/v1/asr/transcribe", json=_request_payload())

    assert response.status_code == 502
    assert response.json()["detail"] == "provider_http_error"
    assert "test-api-key" not in response.text
    assert "data:audio/wav;base64" not in response.text
    assert "private transcript" not in response.text


def test_asr_api_accepts_m4a_smoke_input(client: TestClient) -> None:
    payload = _request_payload()
    payload["audio"] = {
        "data": _audio_data_uri(b"fake-m4a-smoke-audio", audio_format="m4a"),
        "format": "m4a",
        "durationMs": 1200,
    }

    response = client.post("/api/v1/asr/transcribe", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["provider"] == "mock"
    assert body["requiresConfirmation"] is True


def test_asr_call_finished_log_does_not_include_audio_or_transcript(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    client: TestClient,
) -> None:
    secret_key = "test-secret-mimo-asr-key"
    secret_transcript = "这段识别文字不应该进入 ASR timing 日志。"
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_API_KEY", secret_key)
    get_settings.cache_clear()
    caplog.set_level(logging.INFO, logger="app.asr_timing")
    payload = _request_payload()
    payload["metadata"] = {"mock_transcript": secret_transcript}

    response = client.post(
        "/api/v1/asr/transcribe",
        json=payload,
        headers={"X-Request-ID": "asr-log-request-001"},
    )

    assert response.status_code == 200
    assert secret_transcript in response.text
    assert secret_key not in caplog.text
    assert secret_transcript not in caplog.text
    assert "data:audio/wav;base64" not in caplog.text
    assert "UklGRi1mYWtlLXdhdg" not in caplog.text
    records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "asr_call_finished"
    ]
    assert records
    assert records[-1].request_id == "asr-log-request-001"
    assert records[-1].provider == "mock"
    assert records[-1].model == "mock-asr-v0"
    assert records[-1].duration_ms == 1200
    assert records[-1].audio_bytes == len(b"RIFF-fake-wav")
    assert records[-1].status == "ok"
    assert records[-1].error_type is None
