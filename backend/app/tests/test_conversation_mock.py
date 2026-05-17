from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _payload(text: str) -> dict:
    return {
        "child_id": "child_test",
        "session_id": "session_test",
        "input": {
            "type": "text",
            "text": text,
            "attachments": [],
        },
        "client_context": {
            "device_time": "2026-05-17T16:35:00+08:00",
            "timezone": "Asia/Shanghai",
            "app_mode": "child",
        },
    }


def test_conversation_message_returns_learning_help_mock_reply() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_payload("我有一道题不会"),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["reply"]["type"] == "agent_message"
    assert "答案" in body["reply"]["text"]
    assert "拍题目" in str(body["ui_actions"])
    assert body["session_state"] == {
        "base_scene": "daily.after_school_checkin",
        "active_scene": "learning.homework_help",
        "needs_input": "problem_content",
    }


def test_conversation_mock_reply_keeps_child_safety_boundaries() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_payload("这道数学题不会"),
    )

    assert response.status_code == 200
    reply_text = response.json()["reply"]["text"]

    forbidden_phrases = [
        "不要告诉爸爸",
        "不要告诉妈妈",
        "别告诉爸爸",
        "别告诉妈妈",
        "保密",
    ]
    assert all(phrase not in reply_text for phrase in forbidden_phrases)
    assert "你先不用急着要答案" in reply_text
