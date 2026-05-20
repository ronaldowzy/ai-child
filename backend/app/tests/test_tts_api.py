import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.domain.schemas.conversation import (
    ClientContext,
    ConversationInput,
    ConversationMessageRequest,
)
from app.main import app
from app.services.conversation_service import ConversationService


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_xiaobaihu_tts_endpoint_returns_mock_audio_url_by_default() -> None:
    response = client.post(
        "/api/v1/tts/xiaobaohu",
        json={
            "text": "我们先看题目在问什么。",
            "emotion": "hint",
            "voiceVersion": "xiaobaohu_v01",
            "forceRefresh": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["audioUrl"].startswith("/media/tts/xiaobaohu_v01/")
    assert body["provider"] == "mock"
    assert body["model"] == "mock-tts-v0"
    assert body["cacheHit"] is False
    assert body["text"] == "我们先看题目在问什么。"

    media_response = client.get(body["audioUrl"])
    assert media_response.status_code == 200
    assert media_response.content.startswith(b"RIFF")

    metadata_response = client.get(body["audioUrl"].replace(".wav", ".json"))
    assert metadata_response.status_code == 404


def test_xiaobaihu_tts_endpoint_uses_cache_on_second_request() -> None:
    payload = {
        "text": "缓存测试句子。",
        "emotion": "encourage",
        "voiceVersion": "xiaobaohu_v01",
        "forceRefresh": True,
    }
    first = client.post("/api/v1/tts/xiaobaohu", json=payload)
    assert first.status_code == 200

    payload["forceRefresh"] = False
    second = client.post("/api/v1/tts/xiaobaohu", json=payload)

    assert second.status_code == 200
    assert second.json()["cacheHit"] is True
    assert second.json()["audioUrl"] == first.json()["audioUrl"]


def test_xiaobaihu_tts_rejects_too_long_text() -> None:
    response = client.post(
        "/api/v1/tts/xiaobaohu",
        json={"text": "很" * 601, "emotion": "encourage"},
    )

    assert response.status_code == 400
    assert "too long" in response.json()["detail"]


def test_xiaobaihu_tts_rejects_unknown_emotion() -> None:
    response = client.post(
        "/api/v1/tts/xiaobaohu",
        json={"text": "你好。", "emotion": "shout"},
    )

    assert response.status_code == 400
    assert "Unsupported TTS emotion" in response.json()["detail"]


def test_mimo_tts_policy_blocked_before_provider_call(monkeypatch) -> None:
    monkeypatch.setenv("CHILD_AI_TTS_PROVIDER", "mimo")
    monkeypatch.setenv("CHILD_AI_MIMO_TTS_ENABLED", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_TTS_API_KEY", "test-key")
    monkeypatch.setenv("CHILD_AI_MIMO_TTS_ALLOW_CHILD_TEXT", "false")
    monkeypatch.setenv("CHILD_AI_MIMO_TTS_RETENTION_POLICY_CHECKED", "true")
    get_settings.cache_clear()

    def fail_if_called(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("MiMo TTS network call should be blocked")

    monkeypatch.setattr(
        "app.providers.tts.mimo_voiceclone_provider.urlopen",
        fail_if_called,
    )

    response = client.post(
        "/api/v1/tts/xiaobaohu",
        json={"text": "你好。", "emotion": "encourage"},
    )

    assert response.status_code == 403
    assert "child_text_not_allowed" in response.json()["detail"]


def test_missing_voice_sample_returns_clear_error(monkeypatch) -> None:
    monkeypatch.setenv(
        "CHILD_AI_XIAOBAIHU_VOICE_SAMPLE_PATH",
        "backend/assets/voices/missing_sample.wav",
    )
    get_settings.cache_clear()

    response = client.post(
        "/api/v1/tts/xiaobaohu",
        json={"text": "你好。", "emotion": "encourage"},
    )

    assert response.status_code == 503
    assert "voice sample does not exist" in response.json()["detail"]


def test_conversation_tts_failure_does_not_break_text_reply() -> None:
    class FailingTtsService:
        def generate_for_conversation(self, *, text: str, emotion: str) -> str | None:
            raise RuntimeError(f"TTS failed for {emotion}: {text}")

    service = ConversationService(
        tts_service=FailingTtsService(),
        debug_enabled=False,
    )
    response = service.handle_message(
        ConversationMessageRequest(
            child_id="child_tts_failure_test",
            session_id="conversation_tts_failure_session",
            input=ConversationInput(text="我想聊恐龙"),
            client_context=ClientContext(
                device_time="2026-05-20T16:30:00+08:00",
                timezone="Asia/Shanghai",
                app_mode="child",
            ),
        )
    )

    assert response.reply.text
    assert response.reply.audio_url is None
