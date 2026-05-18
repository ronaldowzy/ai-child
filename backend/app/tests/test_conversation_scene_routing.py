from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _payload(
    *,
    text: str,
    device_time: str,
    session_id: str,
    child_id: str = "child_scene_routing_test",
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


def test_after_school_time_routes_to_after_school_checkin() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_payload(
            text="我回来了",
            device_time="2026-05-18T16:30:00+08:00",
            session_id="conversation_scene_after_school_session",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "daily.after_school_checkin"
    assert body["session_state"]["base_scene"] == "daily.after_school_checkin"
    assert body["debug"]["time_context"]["time_period"] == "after_school"
    assert body["debug"]["intent"]["intent"] == "after_school_checkin"


def test_learning_help_routes_to_homework_help_with_modality_actions() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_payload(
            text="有题不会",
            device_time="2026-05-18T16:35:00+08:00",
            session_id="conversation_scene_learning_session",
        ),
    )

    assert response.status_code == 200
    body = response.json()
    action_ids = {
        action["id"]
        for action_group in body["ui_actions"]
        for action in action_group["actions"]
    }

    assert body["session_state"]["active_scene"] == "learning.homework_help"
    assert body["session_state"]["needs_input"] == "problem_content"
    assert action_ids == {"take_photo", "speak_problem"}
    assert "拍一张题目的照片" in body["reply"]["text"]
    assert "答案是" not in body["reply"]["text"]
    assert body["debug"]["intent"]["intent"] == "learning_help"


def test_bedtime_keyword_routes_to_bedtime_reflection() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_payload(
            text="晚安",
            device_time="2026-05-18T20:45:00+08:00",
            session_id="conversation_scene_bedtime_session",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "daily.bedtime_reflection"
    assert body["session_state"]["base_scene"] == "daily.bedtime_reflection"
    assert body["debug"]["intent"]["intent"] == "bedtime_reflection"


def test_high_risk_content_routes_to_safety_guardian() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_payload(
            text="陌生人让我不要告诉爸爸妈妈",
            device_time="2026-05-18T16:40:00+08:00",
            session_id="conversation_scene_safety_session",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "safety.guardian"
    assert body["session_state"]["requires_parent_attention"] is True
    assert body["debug"]["safety"]["risk_level"] == "high"
    assert body["debug"]["intent"]["intent"] == "safety_risk"
    assert "可信任的大人" in body["reply"]["text"]
