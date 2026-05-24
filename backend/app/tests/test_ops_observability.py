import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.domain.model_types import ModelRequest, ModelTaskType
from app.domain.schemas.conversation import (
    ClientContext,
    ConversationInput,
    ConversationMessageRequest,
)
from app.domain.schemas.tts import XiaobaihuTtsRequest
from app.main import app
from app.services.conversation_service import ConversationService
from app.services.model_registry import ModelRegistry
from app.services.tts_data_policy_guard import TtsDataPolicyBlockedError
from app.services.tts_service import TtsService


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_request_id_is_generated_when_missing() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"].startswith("req_")
    assert len(response.headers["X-Request-ID"]) <= 64


def test_request_id_reuses_safe_client_header() -> None:
    response = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": "qa-request_123.abc:1"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "qa-request_123.abc:1"


@pytest.mark.parametrize(
    "raw_request_id",
    [
        "bad request id",
        "bad/request/id",
        "x" * 65,
    ],
)
def test_invalid_request_id_is_replaced(raw_request_id: str) -> None:
    response = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": raw_request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != raw_request_id
    assert response.headers["X-Request-ID"].startswith("req_")


def test_request_finished_log_contains_request_id(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app.request_timing")

    response = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": "qa-log-request-001"},
    )

    assert response.status_code == 200
    timing_records = [
        record for record in caplog.records
        if getattr(record, "event", None) == "request_finished"
    ]
    assert timing_records
    assert timing_records[-1].request_id == "qa-log-request-001"
    assert timing_records[-1].method == "GET"
    assert timing_records[-1].path == "/api/v1/health"
    assert timing_records[-1].status_code == 200


def test_model_call_finished_log_does_not_include_prompt_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    secret_prompt_text = "完整 prompt 不应该进入日志，里面有孩子说的话。"
    caplog.set_level(logging.INFO, logger="app.model_timing")

    response = ModelRegistry().generate(
        ModelRequest(
            task_type=ModelTaskType.CHILD_CHAT,
            messages=[{"role": "user", "content": secret_prompt_text}],
            input_text=secret_prompt_text,
            context={
                "conversation": {
                    "child_id": "fictional_child_for_log_test",
                    "session_id": "fictional_session_for_log_test",
                }
            },
        )
    )

    assert response.response_text
    assert secret_prompt_text not in caplog.text
    records = [
        record for record in caplog.records
        if getattr(record, "event", None) == "model_call_finished"
    ]
    assert records
    assert records[-1].provider == "mock"
    assert records[-1].model == "mock-child-chat-v0"
    assert records[-1].child_id_hash
    assert records[-1].session_id_hash


def test_conversation_latency_log_splits_model_and_tts_without_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FixedTtsService:
        def generate_for_conversation(self, *, text: str, emotion: str) -> str:
            return "/media/tts/xiaobaohu_v01/fixed.wav"

    child_text = "这句儿童输入不应该进入延迟日志。"
    caplog.set_level(logging.INFO, logger="app.conversation")
    service = ConversationService(
        tts_service=FixedTtsService(),
        debug_enabled=False,
        persistence_enabled=False,
    )

    response = service.handle_message(
        ConversationMessageRequest(
            child_id="fictional_latency_child",
            session_id="fictional_latency_session",
            input=ConversationInput(text=child_text),
            client_context=ClientContext(
                deviceTime="2026-05-24T16:30:00+08:00",
                timezone="Asia/Shanghai",
            ),
        )
    )

    assert response.reply.audio_url == "/media/tts/xiaobaohu_v01/fixed.wav"
    assert child_text not in caplog.text
    records = [
        record for record in caplog.records
        if getattr(record, "event", None) == "conversation_turn_latency"
    ]
    assert records
    record = records[-1]
    assert record.request_start is not None
    assert record.model_ms >= 0
    assert record.tts_ms >= 0
    assert record.turn_total_ms >= record.model_ms
    assert record.audio_url_present is True
    assert record.child_id_hash
    assert record.session_id_hash


def test_tts_call_finished_log_does_not_include_api_key_or_full_text(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    secret_key = "test-secret-mimo-api-key"
    full_tts_text = "这一整段小白狐朗读文本不应该完整进入日志。"
    monkeypatch.setenv("CHILD_AI_TTS_PROVIDER", "mimo")
    monkeypatch.setenv("CHILD_AI_MIMO_TTS_ENABLED", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_TTS_API_KEY", secret_key)
    monkeypatch.setenv("CHILD_AI_MIMO_TTS_ALLOW_CHILD_TEXT", "false")
    monkeypatch.setenv("CHILD_AI_MIMO_TTS_RETENTION_POLICY_CHECKED", "true")
    get_settings.cache_clear()
    caplog.set_level(logging.INFO, logger="app.tts_timing")

    with pytest.raises(TtsDataPolicyBlockedError):
        TtsService().generate_xiaobaihu(
            XiaobaihuTtsRequest(
                text=full_tts_text,
                emotion="encourage",
            )
        )

    assert secret_key not in caplog.text
    assert full_tts_text not in caplog.text
    records = [
        record for record in caplog.records
        if getattr(record, "event", None) == "tts_call_finished"
    ]
    assert records
    assert records[-1].provider == "mimo"
    assert records[-1].text_chars == len(full_tts_text)
    assert records[-1].error_type == "TtsDataPolicyBlockedError"


def test_health_detail_does_not_leak_mimo_tts_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret_key = "test-secret-mimo-tts-key"
    monkeypatch.setenv("CHILD_AI_TTS_PROVIDER", "mimo")
    monkeypatch.setenv("CHILD_AI_MIMO_TTS_ENABLED", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_TTS_API_KEY", secret_key)
    get_settings.cache_clear()

    response = client.get("/api/v1/health/detail")

    assert response.status_code == 200
    response_text = response.text
    assert secret_key not in response_text
    assert response.json()["components"]["mimo_tts_config"]["apiKeyPresent"] is True


def test_health_detail_returns_degraded_when_postgres_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_build_engine(_database_url: str):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        "app.services.health_service.build_engine",
        fail_build_engine,
    )

    response = client.get("/api/v1/health/detail")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["components"]["postgres"]["status"] == "degraded"
    assert body["components"]["postgres"]["errorType"] == "RuntimeError"


def test_health_detail_returns_degraded_when_tts_cache_unwritable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    blocked_cache_path = tmp_path / "cache-file"
    blocked_cache_path.write_text("not a directory", encoding="utf-8")
    monkeypatch.setenv("CHILD_AI_TTS_CACHE_DIR", str(blocked_cache_path))
    monkeypatch.setattr(
        "app.services.health_service.HealthService._postgres_health",
        lambda _self: {"status": "ok"},
    )
    get_settings.cache_clear()

    response = client.get("/api/v1/health/detail")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["components"]["tts_cache"]["status"] == "degraded"
    assert body["components"]["tts_cache"]["writable"] is False
