from fastapi.testclient import TestClient

from app.main import app
from app.repositories.attachment_repository import get_attachment_repository


client = TestClient(app)


def setup_function() -> None:
    get_attachment_repository().clear()


def test_conversation_attachment_accepts_high_confidence_homework_photo() -> None:
    response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": "child_attachment_api_test",
            "session_id": "attachment_api_high_session",
            "attachment_type": "image",
            "image_purpose": "learning_homework",
            "file_id": "mock_homework_photo",
            "mock_ocr_text": "小明有24个苹果，平均分给6个同学，每人几个？",
            "mock_vision_text": "小明有24个苹果，平均分给6个同学，每人几个？",
            "mock_confidence": 0.93,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["attachment_id"].startswith("att_")
    assert body["recognized_content"]["type"] == "homework_problem"
    assert body["recognized_content"]["text"] == (
        "小明有24个苹果，平均分给6个同学，每人几个？"
    )
    assert body["recognized_content"]["confidence"] == 0.93
    assert body["session_state"]["active_scene"] == "learning.homework_help"
    assert body["session_state"]["needs_input"] == "problem_understanding"
    assert "这道题是在问什么" in body["reply"]["text"]
    assert "答案是" not in body["reply"]["text"]


def test_conversation_attachment_low_confidence_requests_retry_or_speech() -> None:
    response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": "child_attachment_api_test",
            "session_id": "attachment_api_low_session",
            "attachment_type": "homework_photo",
            "file_id": "bad_photo_homework",
            "mock_confidence": 0.31,
        },
    )

    assert response.status_code == 200
    body = response.json()
    action_ids = {
        action["id"]
        for action_group in body["ui_actions"]
        for action in action_group["actions"]
    }

    assert "text" not in body["recognized_content"]
    assert body["recognized_content"]["confidence"] == 0.31
    assert body["recognized_content"]["fallback_action"] == "retake_or_speak_problem"
    assert body["session_state"]["needs_input"] == "problem_content"
    assert action_ids == {"take_photo", "speak_problem"}
    assert "没看清楚" in body["reply"]["text"]


def test_conversation_attachment_accepts_generic_image_share() -> None:
    response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": "child_attachment_api_test",
            "session_id": "attachment_api_share_session",
            "attachment_type": "image",
            "image_purpose": "share",
            "file_id": "mock_toy_photo",
            "mock_vision_text": "孩子搭了一个积木城堡",
            "child_caption": "你看我搭的这个",
            "mock_confidence": 0.9,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["recognized_content"]["type"] == "image_observation"
    assert body["recognized_content"]["image_purpose"] == "share"
    assert body["session_state"]["active_scene"] == "conversation.open"
    assert "积木城堡" in body["reply"]["text"]
    assert "这道题" not in body["reply"]["text"]


def test_generic_photo_with_homework_like_text_stays_image_context() -> None:
    response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": "child_attachment_api_test",
            "session_id": "attachment_api_share_homework_like_session",
            "attachment_type": "image",
            "image_purpose": "share",
            "file_id": "camera_photo_with_text",
            "mock_vision_text": "图片里有一张纸，上面像是数学题目和一些数字。",
            "child_caption": "我拍了一张图片给小白狐看。",
            "mock_confidence": 0.9,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["recognized_content"]["type"] == "homework_problem"
    assert body["recognized_content"]["image_purpose"] == "share"
    assert body["session_state"]["active_scene"] == "conversation.open"
    assert body["session_state"].get("needs_input") is None
    assert "这道题是在问什么" not in body["reply"]["text"]


def test_generic_image_context_can_continue_in_conversation() -> None:
    child_id = "child_attachment_context_test"
    session_id = "attachment_context_session"
    attachment_response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": child_id,
            "session_id": session_id,
            "attachment_type": "image",
            "image_purpose": "share",
            "file_id": "mock_blocks_photo",
            "mock_vision_text": "孩子搭了一个积木城堡",
            "child_caption": "你看我搭的这个",
            "mock_confidence": 0.9,
        },
    )
    attachment_id = attachment_response.json()["attachment_id"]

    response = client.post(
        "/api/v1/conversation/message",
        json={
            "child_id": child_id,
            "session_id": session_id,
            "input": {
                "type": "text",
                "text": "我们继续聊刚才那张图片",
                "attachments": [attachment_id],
            },
            "client_context": {
                "device_time": "2026-05-18T16:30:00+08:00",
                "timezone": "Asia/Shanghai",
                "app_mode": "child",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "conversation.open"
    assert "积木城堡" in body["reply"]["text"]
    assert "这道题" not in body["reply"]["text"]


def test_homework_like_share_image_context_reaches_conversation_prompt() -> None:
    child_id = "child_attachment_homework_like_context_test"
    session_id = "attachment_homework_like_context_session"
    attachment_response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": child_id,
            "session_id": session_id,
            "attachment_type": "image",
            "image_purpose": "share",
            "file_id": "camera_homework_like_photo",
            "mock_vision_text": "图片里有一张纸，上面像是数学题目和一些数字。",
            "child_caption": "我拍了一张图片给小白狐看。",
            "mock_confidence": 0.9,
        },
    )
    attachment_id = attachment_response.json()["attachment_id"]

    response = client.post(
        "/api/v1/conversation/message",
        json={
            "child_id": child_id,
            "session_id": session_id,
            "input": {
                "type": "text",
                "text": "我们继续聊刚才那张图片",
                "attachments": [attachment_id],
            },
            "client_context": {
                "device_time": "2026-05-18T16:30:00+08:00",
                "timezone": "Asia/Shanghai",
                "app_mode": "child",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "conversation.open"
    assert "数学题目" in body["reply"]["text"]


def test_conversation_attachment_privacy_image_routes_to_boundary() -> None:
    response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": "child_attachment_api_test",
            "session_id": "attachment_api_privacy_session",
            "attachment_type": "image",
            "image_purpose": "privacy_sensitive",
            "file_id": "mock_address_photo",
            "mock_vision_text": "照片里有家庭地址和电话号码",
            "mock_confidence": 0.9,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["recognized_content"]["type"] == "privacy_sensitive"
    assert body["session_state"]["active_scene"] == "privacy.boundary"
    assert "隐私信息" in body["reply"]["text"]


def test_privacy_image_context_still_routes_to_boundary_on_followup() -> None:
    child_id = "child_attachment_privacy_context_test"
    session_id = "attachment_privacy_context_session"
    attachment_response = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": child_id,
            "session_id": session_id,
            "attachment_type": "image",
            "image_purpose": "privacy_sensitive",
            "file_id": "mock_address_photo_followup",
            "mock_vision_text": "照片里有家庭地址和电话号码",
            "mock_confidence": 0.9,
        },
    )
    attachment_id = attachment_response.json()["attachment_id"]

    response = client.post(
        "/api/v1/conversation/message",
        json={
            "child_id": child_id,
            "session_id": session_id,
            "input": {
                "type": "text",
                "text": "我们继续聊刚才那张图片",
                "attachments": [attachment_id],
            },
            "client_context": {
                "device_time": "2026-05-18T16:30:00+08:00",
                "timezone": "Asia/Shanghai",
                "app_mode": "child",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "privacy.boundary"
    assert body["debug"]["intent"]["intent"] == "privacy_question"
