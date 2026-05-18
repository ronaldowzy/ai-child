from fastapi.testclient import TestClient

from app.main import app
from app.repositories.attachment_repository import get_attachment_repository


client = TestClient(app)


def setup_function() -> None:
    get_attachment_repository().clear()


def _message_payload(
    *,
    text: str,
    session_id: str,
    attachments: list[str] | None = None,
) -> dict:
    return {
        "child_id": "child_learning_attachment_test",
        "session_id": session_id,
        "input": {
            "type": "text",
            "text": text,
            "attachments": attachments or [],
        },
        "client_context": {
            "device_time": "2026-05-18T18:35:00+08:00",
            "timezone": "Asia/Shanghai",
            "app_mode": "child",
        },
    }


def test_learning_help_starts_with_photo_or_speech_actions() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            text="我有一道题不会",
            session_id="learning_attachment_start_session",
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
    assert "答案是" not in body["reply"]["text"]


def test_learning_help_continues_with_attachment_id_to_problem_confirmation() -> None:
    session_id = "learning_attachment_continue_session"
    attachment_response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": "child_learning_attachment_test",
            "session_id": session_id,
            "attachment_type": "homework_photo",
            "file_id": "mock_homework_photo",
            "mock_ocr_text": "小明有24个苹果，平均分给6个同学，每人几个？",
            "mock_confidence": 0.94,
        },
    )
    attachment_id = attachment_response.json()["attachment_id"]

    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            text="这是刚才拍的题目",
            session_id=session_id,
            attachments=[attachment_id],
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "learning.homework_help"
    assert body["session_state"]["needs_input"] == "problem_understanding"
    assert body["ui_actions"] == []
    assert "这道题是在问什么" in body["reply"]["text"]
    assert "答案是" not in body["reply"]["text"]
    assert body["debug"]["intent"]["sub_intent"] == "homework_problem_with_attachment"
