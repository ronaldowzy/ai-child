import base64

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.asr import router as asr_router
from app.core.config import get_settings
from app.domain.schemas.asr import (
    AsrProviderName,
    AsrTranscriptStatus,
    AsrTranscriptionRequest,
)
from app.providers.asr.base import (
    AsrProviderError,
    AsrProviderRequest,
    AsrProviderResult,
    BaseAsrProvider,
)
from app.providers.asr.local_sensevoice_provider import LocalSenseVoiceAsrProvider
from app.providers.asr.mimo_asr_provider import MimoAsrProvider
from app.services.asr_data_policy_guard import (
    AsrDataPolicyBlockedError,
    AsrDataPolicyGuard,
    AsrDataPolicySettings,
)
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


class StaticAsrProvider(BaseAsrProvider):
    def __init__(self, transcript: str) -> None:
        super().__init__(provider_name=AsrProviderName.MOCK, enabled=True)
        self._transcript = transcript

    def transcribe(self, request: AsrProviderRequest) -> AsrProviderResult:
        return AsrProviderResult(
            transcript=self._transcript,
            provider=self.provider_name,
            model="static-asr-test",
            duration_ms=request.duration_ms,
        )


class FailingLocalAsrProvider(BaseAsrProvider):
    def __init__(self) -> None:
        super().__init__(
            provider_name=AsrProviderName.LOCAL_SENSEVOICE,
            enabled=True,
        )

    def transcribe(self, request: AsrProviderRequest) -> AsrProviderResult:
        raise AsrProviderError("local_sensevoice_test_failure")


class RecordingAsrProvider(BaseAsrProvider):
    def __init__(self, transcript: str) -> None:
        super().__init__(provider_name=AsrProviderName.MOCK, enabled=True)
        self._transcript = transcript
        self.last_request: AsrProviderRequest | None = None

    def transcribe(self, request: AsrProviderRequest) -> AsrProviderResult:
        self.last_request = request
        return AsrProviderResult(
            transcript=self._transcript,
            provider=self.provider_name,
            model="recording-asr-test",
            duration_ms=request.duration_ms,
        )


def test_mock_asr_returns_pending_transcript_for_confirmation() -> None:
    response = AsrService().transcribe(
        AsrTranscriptionRequest.model_validate(_request_payload())
    )

    assert response.status == AsrTranscriptStatus.OK
    assert response.transcript == "我想聊恐龙"
    assert response.requires_confirmation is True
    assert response.provider == "mock"
    assert response.model == "mock-asr-v0"


def test_asr_accepts_m4a_smoke_input() -> None:
    payload = _request_payload()
    payload["audio"]["format"] = "m4a"
    payload["audio"]["data"] = "data:audio/m4a;base64," + base64.b64encode(
        b"fake-m4a"
    ).decode("ascii")

    response = AsrService().transcribe(AsrTranscriptionRequest.model_validate(payload))

    assert response.status == AsrTranscriptStatus.OK
    assert response.provider == "mock"
    assert response.requires_confirmation is True


def test_mock_asr_without_explicit_transcript_needs_retry() -> None:
    payload = _request_payload()
    payload.pop("metadata")

    response = AsrService().transcribe(AsrTranscriptionRequest.model_validate(payload))

    assert response.status == AsrTranscriptStatus.NEEDS_RETRY
    assert response.transcript is None
    assert response.error_code == "empty_transcript"


def test_asr_rejects_unsupported_format() -> None:
    payload = _request_payload()
    payload["audio"]["format"] = "mp3"
    payload["audio"]["data"] = "data:audio/mp3;base64," + base64.b64encode(
        b"fake-mp3"
    ).decode("ascii")

    with pytest.raises(AsrRequestValidationError) as exc_info:
        AsrService().transcribe(AsrTranscriptionRequest.model_validate(payload))

    assert exc_info.value.error_code == "unsupported_audio_format"


@pytest.mark.parametrize("transcript", ["", "未听清", "未听清。"])
def test_empty_or_unclear_asr_transcript_needs_retry(transcript: str) -> None:
    response = AsrService(provider=StaticAsrProvider(transcript)).transcribe(
        AsrTranscriptionRequest.model_validate(_request_payload())
    )

    assert response.status == AsrTranscriptStatus.NEEDS_RETRY
    assert response.transcript is None
    assert response.requires_confirmation is True
    assert response.error_code == "empty_transcript"
    assert response.fallback_action == "retry_or_type"


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


def test_mimo_asr_reuses_shared_mimo_key_and_default_asr_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CHILD_AI_ASR_PROVIDER", "mimo")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_ENABLED", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_API_KEY", "")
    monkeypatch.setenv("CHILD_AI_MIMO_API_KEY", "shared-mimo-key")
    monkeypatch.setenv("CHILD_AI_MIMO_TTS_API_KEY", "tts-fallback-key")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED", "true")
    get_settings.cache_clear()

    service = AsrService()

    assert isinstance(service._provider, MimoAsrProvider)
    assert service._provider.api_key == "shared-mimo-key"
    assert service._provider.model == "mimo-v2.5"


def test_local_sensevoice_is_policy_allowed_without_cloud_flags() -> None:
    AsrDataPolicyGuard().validate(
        AsrDataPolicySettings(
            provider=AsrProviderName.LOCAL_SENSEVOICE,
            provider_enabled=True,
            api_key_present=False,
            allow_child_audio=False,
            retention_policy_checked=False,
            no_training_confirmed=False,
        )
    )


def test_local_sensevoice_provider_can_be_selected_by_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CHILD_AI_ASR_PROVIDER", "local_sensevoice")
    monkeypatch.setenv("CHILD_AI_LOCAL_SENSEVOICE_ENABLED", "true")
    monkeypatch.setenv(
        "CHILD_AI_LOCAL_SENSEVOICE_MODEL_PATH",
        "backend/models/asr/sensevoice/model.int8.onnx",
    )
    monkeypatch.setenv(
        "CHILD_AI_LOCAL_SENSEVOICE_TOKENS_PATH",
        "backend/models/asr/sensevoice/tokens.txt",
    )
    get_settings.cache_clear()

    service = AsrService()

    assert isinstance(service._provider, LocalSenseVoiceAsrProvider)
    assert service._provider.enabled is True
    assert service._provider.model_path.name == "model.int8.onnx"
    assert service._provider.tokens_path.name == "tokens.txt"
    assert service._fallback_provider is not None
    assert service._fallback_provider.provider_name == AsrProviderName.MIMO


def test_local_sensevoice_failure_falls_back_to_existing_provider() -> None:
    fallback_provider = RecordingAsrProvider("我想聊火山")

    response = AsrService(
        provider=FailingLocalAsrProvider(),
        fallback_provider=fallback_provider,
    ).transcribe(AsrTranscriptionRequest.model_validate(_request_payload()))

    assert response.status == AsrTranscriptStatus.OK
    assert response.transcript == "我想聊火山"
    assert response.provider == AsrProviderName.MOCK
    assert response.model == "recording-asr-test"
    assert fallback_provider.last_request is not None
    assert fallback_provider.last_request.metadata["decoded_audio_bytes"] == len(
        b"RIFF-fake-wav"
    )
    assert fallback_provider.last_request.metadata["decoded_audio"] == b"RIFF-fake-wav"


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
