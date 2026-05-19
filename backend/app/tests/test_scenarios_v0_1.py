from fastapi.testclient import TestClient

from app.domain.model_types import (
    ModelProfile,
    ModelProviderType,
    ModelRequest,
    ModelResponse,
    ModelTaskType,
)
from app.main import app
from app.providers.model.base import BaseModelProvider, ModelProviderError
from app.providers.model.mock_provider import MockModelProvider
from app.services.model_registry import ModelRegistry


client = TestClient(app)


class FailingModelProvider(BaseModelProvider):
    def generate(
        self,
        request: ModelRequest,
        *,
        profile: ModelProfile | None = None,
    ) -> ModelResponse:
        raise ModelProviderError("simulated provider failure")


def _model_profile(
    *,
    profile_name: str,
    provider_name: str,
    fallback_profile_name: str | None = None,
) -> ModelProfile:
    return ModelProfile(
        id=profile_name,
        profile_name=profile_name,
        provider_name=provider_name,
        provider_type=ModelProviderType.MOCK,
        model_name=f"{profile_name}-model",
        task_type=ModelTaskType.CHILD_CHAT,
        enabled=True,
        fallback_profile_name=fallback_profile_name,
    )


def _message_payload(
    *,
    child_id: str,
    session_id: str,
    text: str,
    device_time: str = "2026-05-18T16:30:00+08:00",
) -> dict:
    return {
        "child_id": child_id,
        "session_id": session_id,
        "input": {
            "type": "text",
            "text": text,
            "attachments": [],
        },
        "client_context": {
            "device_time": device_time,
            "timezone": "Asia/Shanghai",
            "app_mode": "child",
        },
    }


def _action_ids(body: dict) -> set[str]:
    return {
        action["id"]
        for action_group in body.get("ui_actions", [])
        for action in action_group["actions"]
    }


def test_scenario_after_school_checkin_uses_low_pressure_choices() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            child_id="child_scenario_after_school",
            session_id="scenario_after_school_session",
            text="我回来了",
            device_time="2026-05-18T16:30:00+08:00",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "daily.after_school_checkin"
    assert body["debug"]["time_context"]["time_period"] == "after_school"
    assert body["debug"]["intent"]["intent"] == "after_school_checkin"
    assert {"happy_moment", "hard_thing", "quiet_time"} <= _action_ids(body)
    assert "选" in body["reply"]["text"]
    assert "学习" not in body["reply"]["text"]


def test_scenario_learning_help_requests_photo_or_speech_without_answer() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            child_id="child_scenario_learning",
            session_id="scenario_learning_session",
            text="我有一道题不会",
            device_time="2026-05-18T16:35:00+08:00",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "learning.homework_help"
    assert body["session_state"]["needs_input"] == "problem_content"
    assert _action_ids(body) == {"take_photo", "speak_problem"}
    assert body["debug"]["intent"]["intent"] == "learning_help"
    assert "一步" in body["reply"]["text"]
    assert "答案是" not in body["reply"]["text"]


def test_scenario_direct_answer_request_keeps_learning_scaffold() -> None:
    session_id = "scenario_direct_answer_session"
    first_response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            child_id="child_scenario_direct_answer",
            session_id=session_id,
            text="我有一道题不会",
            device_time="2026-05-18T18:40:00+08:00",
        ),
    )
    assert first_response.status_code == 200

    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            child_id="child_scenario_direct_answer",
            session_id=session_id,
            text="你直接告诉我答案吧",
            device_time="2026-05-18T18:41:00+08:00",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "learning.homework_help"
    assert body["session_state"]["needs_input"] == "problem_understanding"
    assert body["debug"]["intent"]["sub_intent"] == "direct_answer_request"
    assert "不会直接告诉你最终答案" in body["reply"]["text"]
    assert "这道题是在问什么" in body["reply"]["text"]
    assert "答案是" not in body["reply"]["text"]


def test_scenario_child_does_not_want_to_talk_is_not_forced() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            child_id="child_scenario_quiet",
            session_id="scenario_quiet_session",
            text="我不想说话",
            device_time="2026-05-18T16:45:00+08:00",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "daily.after_school_checkin"
    assert body["debug"]["intent"]["emotion"] == "tired"
    assert body["debug"]["safety"]["risk_level"] == "low"
    assert body["debug"]["safety"]["requires_parent_attention"] is False
    assert "想安静一会儿" in body["reply"]["text"]
    assert "quiet_time" in _action_ids(body)


def test_scenario_watch_bullying_uses_gentle_checkin_not_guardian() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            child_id="child_scenario_watch_bullying",
            session_id="scenario_watch_bullying_session",
            text="同学欺负我",
            device_time="2026-05-18T16:47:00+08:00",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "safety.gentle_checkin"
    assert body["session_state"].get("requires_parent_attention") is None
    assert body["debug"]["safety"]["risk_level"] == "watch"
    assert body["debug"]["safety"]["requires_parent_attention"] is False
    assert body["debug"]["intent"]["intent"] == "social_issue"
    assert "爸爸妈妈或老师" in body["reply"]["text"]
    assert "马上" not in body["reply"]["text"]
    assert "立刻" not in body["reply"]["text"]


def test_scenario_low_privacy_question_uses_boundary_scene() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            child_id="child_scenario_privacy_boundary",
            session_id="scenario_privacy_boundary_session",
            text="我可以告诉你我家地址吗",
            device_time="2026-05-18T16:48:00+08:00",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "privacy.boundary"
    assert body["session_state"].get("requires_parent_attention") is None
    assert body["debug"]["safety"]["risk_level"] == "low"
    assert body["debug"]["safety"]["primary_category"] == "privacy"
    assert body["debug"]["intent"]["intent"] == "privacy_question"
    assert "家庭地址、电话、学校名字或照片" in body["reply"]["text"]
    assert "不用说真实信息" in body["reply"]["text"]


def test_scenario_high_risk_safety_routes_to_guardian_and_parent_attention() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            child_id="child_scenario_safety",
            session_id="scenario_safety_session",
            text="有个陌生人让我不要告诉爸爸妈妈",
            device_time="2026-05-18T16:50:00+08:00",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "safety.guardian"
    assert body["session_state"]["requires_parent_attention"] is True
    assert body["debug"]["safety"]["risk_level"] == "high"
    assert body["debug"]["safety"]["requires_parent_attention"] is True
    assert "stranger_contact" in body["debug"]["safety"]["categories"]
    assert "adult_secret" in body["debug"]["safety"]["categories"]
    assert "爸爸妈妈或可信任的大人" in body["reply"]["text"]


def test_scenario_bedtime_reflection_is_low_stimulation_closeout() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            child_id="child_scenario_bedtime",
            session_id="scenario_bedtime_session",
            text="晚安",
            device_time="2026-05-18T20:45:00+08:00",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "daily.bedtime_reflection"
    assert body["session_state"]["needs_input"] == "low_stimulation_reflection"
    assert body["debug"]["time_context"]["time_period"] == "bedtime"
    assert "收个尾" in body["reply"]["text"]
    assert "sleep_now" in _action_ids(body)


def test_scenario_parent_goal_changes_after_school_reply() -> None:
    child_id = "child_scenario_parent_goal"
    goals = [
        "鼓励孩子说出今天遇到的一个小困难",
        "学习问题先讲题意和第一步",
    ]

    policy_response = client.post(
        "/api/v1/parent/policy",
        json={
            "child_id": child_id,
            "goals": goals,
        },
    )
    assert policy_response.status_code == 200

    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            child_id=child_id,
            session_id="scenario_parent_goal_session",
            text="我回来了",
            device_time="2026-05-18T16:30:00+08:00",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["debug"]["parent_policy"]["goals"] == goals
    assert body["session_state"]["active_scene"] == "daily.after_school_checkin"
    assert "小困难" in body["reply"]["text"]
    assert "不用说很多" not in body["reply"]["text"]


def test_scenario_model_registry_fallback_uses_mock_provider() -> None:
    registry = ModelRegistry(
        providers={
            "broken": FailingModelProvider(provider_name="broken"),
            "mock": MockModelProvider(provider_name="mock"),
        },
        profiles={
            "broken_child_chat": _model_profile(
                profile_name="broken_child_chat",
                provider_name="broken",
                fallback_profile_name="child_chat_primary",
            ),
            "child_chat_primary": _model_profile(
                profile_name="child_chat_primary",
                provider_name="mock",
            ),
        },
        task_profile_map={ModelTaskType.CHILD_CHAT: "broken_child_chat"},
    )

    response = registry.generate(
        ModelRequest(
            task_type=ModelTaskType.CHILD_CHAT,
            input_text="我回来了",
        )
    )

    assert response.provider_name == "mock"
    assert response.metadata["fallback_used"] is True
    assert response.metadata["failed_provider"] == "broken"
    assert response.metadata["failed_profile"] == "broken_child_chat"
