from datetime import datetime

from fastapi.testclient import TestClient

from app.domain.model_types import ModelRequest, ModelResponse, ModelTaskType
from app.domain.schemas.parent_policy import ParentPolicyUpdateRequest
from app.main import app
from app.services.opening_service import OpeningService
from app.services.parent_policy_service import get_parent_policy_service


client = TestClient(app)


def _opening_payload(
    *,
    child_id: str,
    session_id: str = "opening-session",
    device_time: str = "2026-05-21T16:30:00+08:00",
) -> dict[str, object]:
    return {
        "child_id": child_id,
        "session_id": session_id,
        "client_context": {
            "device_time": device_time,
            "timezone": "Asia/Shanghai",
            "app_mode": "child",
        },
    }


def _update_policy(child_id: str, **kwargs: object) -> None:
    get_parent_policy_service().update_policy(
        ParentPolicyUpdateRequest(child_id=child_id, **kwargs)
    )


def test_opening_uses_child_nickname() -> None:
    child_id = "opening_nickname_child"
    _update_policy(child_id, child_nickname="豆豆", child_display_name="王小明")

    response = client.post(
        "/api/v1/conversation/opening",
        json=_opening_payload(child_id=child_id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"]["text"].startswith("豆豆，")
    assert body["session_state"]["active_scene"] == "conversation.open"


def test_opening_uses_display_name_when_nickname_missing() -> None:
    child_id = "opening_display_name_child"
    _update_policy(child_id, child_display_name="王小明")

    response = client.post(
        "/api/v1/conversation/opening",
        json=_opening_payload(child_id=child_id),
    )

    assert response.status_code == 200
    assert response.json()["reply"]["text"].startswith("王小明，")


def test_opening_without_name_does_not_force_call_name() -> None:
    response = client.post(
        "/api/v1/conversation/opening",
        json=_opening_payload(child_id="opening_no_name_child"),
    )

    assert response.status_code == 200
    text = response.json()["reply"]["text"]
    assert "child" not in text
    assert "大名" not in text


def test_after_school_opening_is_light_and_not_forced_school_checkin() -> None:
    response = client.post(
        "/api/v1/conversation/opening",
        json=_opening_payload(child_id="opening_after_school_child"),
    )

    text = response.json()["reply"]["text"]
    assert "回来啦" in text
    assert "今天在学校怎么样" not in text
    assert "学校" not in text


def test_bedtime_opening_is_low_stimulation() -> None:
    child_id = "opening_bedtime_child"
    _update_policy(child_id, child_nickname="豆豆")

    response = client.post(
        "/api/v1/conversation/opening",
        json=_opening_payload(
            child_id=child_id,
            device_time="2026-05-21T20:40:00+08:00",
        ),
    )

    body = response.json()
    assert "轻轻" in body["reply"]["text"]
    assert body["reply"]["emotion"] == "sleepy"


def test_parent_message_can_block_school_checkin() -> None:
    child_id = "opening_parent_message_no_school"
    _update_policy(child_id, parent_message_raw="不要查岗学校，不要追问。")

    response = client.post(
        "/api/v1/conversation/opening",
        json=_opening_payload(child_id=child_id),
    )

    text = response.json()["reply"]["text"]
    assert "学校" not in text
    assert "今天在学校怎么样" not in text


def test_opening_can_use_model_generated_text() -> None:
    class FakeOpeningModelRegistry:
        requests: list[ModelRequest]

        def __init__(self) -> None:
            self.requests = []

        def generate(self, request: ModelRequest) -> ModelResponse:
            self.requests.append(request)
            return ModelResponse(
                task_type=ModelTaskType.CHILD_CHAT,
                response_text="豆豆，晚上好，我们轻轻聊一句你想说的小事。",
                structured_output={"text": "豆豆，晚上好，我们轻轻聊一句你想说的小事。"},
                provider_name="fake",
                model_name="fake-opening",
            )

    child_id = "opening_model_child"
    _update_policy(child_id, child_nickname="豆豆", parent_message_raw="晚上要低刺激。")
    model_registry = FakeOpeningModelRegistry()
    service = OpeningService(model_registry=model_registry)
    request = _request_model(
        child_id=child_id,
        session_id="opening-model-session",
    )

    response = service.create_opening(request)

    assert response.reply.text == "豆豆，晚上好，我们轻轻聊一句你想说的小事。"
    assert model_registry.requests
    prompt = model_registry.requests[0].messages[0].content
    assert isinstance(prompt, str)
    assert "晚上要低刺激" in prompt
    assert "当前时间段" in prompt


def test_opening_tts_failure_still_returns_text() -> None:
    class FailingTts:
        def generate_for_conversation(self, *, text: str, emotion: str) -> str | None:
            raise RuntimeError("tts failed")

    service = OpeningService(tts_service=FailingTts())
    request = _request_model(
        child_id="opening_tts_failure_child",
        session_id="opening-tts-failure",
    )

    response = service.create_opening(request)

    assert response.reply.text
    assert response.reply.audio_url is None


def test_same_session_returns_cached_opening_without_regenerating_tts() -> None:
    class CountingTts:
        calls = 0

        def generate_for_conversation(self, *, text: str, emotion: str) -> str | None:
            self.calls += 1
            return "/media/tts/opening.wav"

    tts = CountingTts()
    service = OpeningService(tts_service=tts)
    request = _request_model(
        child_id="opening_cached_child",
        session_id="opening-cached-session",
    )

    first = service.create_opening(request)
    second = service.create_opening(request)

    assert first.reply.text == second.reply.text
    assert first.reply.audio_url == "/media/tts/opening.wav"
    assert second.reply.audio_url == "/media/tts/opening.wav"
    assert tts.calls == 1


def _request_model(*, child_id: str, session_id: str):
    from app.domain.schemas.conversation import (
        ClientContext,
        ConversationOpeningRequest,
    )

    return ConversationOpeningRequest(
        child_id=child_id,
        session_id=session_id,
        client_context=ClientContext(
            device_time=datetime.fromisoformat("2026-05-21T16:30:00+08:00"),
            timezone="Asia/Shanghai",
            app_mode="child",
        ),
    )
