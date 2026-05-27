from fastapi.testclient import TestClient

from app.main import app
from app.repositories.attachment_repository import get_attachment_repository


client = TestClient(app)

CHILD_ID = "child_homework_followup_test"

MULTI_PROBLEM_OCR = (
    "第2题：除数是9，商是103，余数是2，问被除数是多少。\n"
    "第6题：一个三位数加一个两位数的和是1065。若在两位数的末尾添一个9，"
    "则它与一个三位数相同。这两个加数分别是多少？\n"
    "第7题：一个长方形的周长是30厘米。"
)


def setup_function() -> None:
    get_attachment_repository().clear()


def _message_payload(
    *,
    text: str,
    session_id: str,
    child_id: str = CHILD_ID,
    attachments: list[str] | None = None,
) -> dict:
    return {
        "child_id": child_id,
        "session_id": session_id,
        "input": {
            "type": "text",
            "text": text,
            "attachments": attachments or [],
        },
        "client_context": {
            "device_time": "2026-05-27T18:35:00+08:00",
            "timezone": "Asia/Shanghai",
            "app_mode": "child",
        },
    }


def _upload_homework(
    session_id: str,
    mock_ocr_text: str = MULTI_PROBLEM_OCR,
    mock_confidence: float = 0.92,
) -> str:
    resp = client.post(
        "/api/v1/conversation/attachment",
        json={
            "child_id": CHILD_ID,
            "session_id": session_id,
            "attachment_type": "homework_photo",
            "file_id": "mock_homework_photo",
            "mock_ocr_text": mock_ocr_text,
            "mock_confidence": mock_confidence,
        },
    )
    return resp.json()["attachment_id"]


def test_followup_without_attachment_still_gets_homework_context() -> None:
    session_id = "followup_no_attachment_session"
    _upload_homework(session_id)

    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            text="第六题，一个三位数开头的这个题。",
            session_id=session_id,
        ),
    )

    assert response.status_code == 200
    body = response.json()
    reply = body["reply"]["text"]
    assert body["session_state"]["active_scene"] == "learning.homework_help"
    assert "第六题" in reply or "6" in reply
    assert "三位数" in reply or "1065" in reply
    assert "除数是9" not in reply
    assert "商是103" not in reply
    assert "余数是2" not in reply
    assert "答案" not in reply


def test_followup_conflict_number_guard() -> None:
    session_id = "followup_conflict_session"
    _upload_homework(session_id)

    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            text="一个三位数加一个两位数的和是1011065。",
            session_id=session_id,
        ),
    )

    assert response.status_code == 200
    body = response.json()
    reply = body["reply"]["text"]
    assert "1065" in reply
    assert "不是你刚才读的那个数" in reply
    assert "不像小学题" not in reply
    assert "答案" not in reply


def test_followup_multi_problem_no_number_specified() -> None:
    session_id = "followup_no_number_session"
    _upload_homework(session_id)

    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            text="这道题怎么做？",
            session_id=session_id,
        ),
    )

    assert response.status_code == 200
    body = response.json()
    reply = body["reply"]["text"]
    assert "我怕看串题了" in reply
    assert "题号" in reply
    assert "开头几个字" in reply


def test_current_attachment_takes_priority_over_old() -> None:
    session_id = "followup_priority_session"
    _upload_homework(session_id)

    new_attachment_id = _upload_homework(
        session_id,
        mock_ocr_text="小明有36个苹果，平均分给4个同学，每人几个？",
    )

    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            text="这道题怎么做？",
            session_id=session_id,
            attachments=[new_attachment_id],
        ),
    )

    assert response.status_code == 200
    body = response.json()
    reply = body["reply"]["text"]
    assert body["session_state"]["active_scene"] == "learning.homework_help"
    assert "答案" not in reply


def test_normal_chat_does_not_trigger_homework_followup() -> None:
    session_id = "followup_normal_chat_session"
    _upload_homework(session_id)

    response = client.post(
        "/api/v1/conversation/message",
        json=_message_payload(
            text="我们聊点别的吧",
            session_id=session_id,
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_state"]["active_scene"] == "conversation.open"
    assert "串题" not in body["reply"]["text"]
    assert "题号" not in body["reply"]["text"]
