from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.memory_repository import get_memory_repository


client = TestClient(app)


def setup_function() -> None:
    get_memory_repository().clear()


def _today() -> str:
    # Use local date to match memory created_at which uses local time
    return datetime.now().date().isoformat()


def _memory_payload(
    *,
    child_id: str = "child_parent_report_api_test",
    memory_type: str = "learning_pattern",
    content: str = "孩子在学习求助时需要先确认题意，再一步一步说出已知条件。",
    tags: list[str] | None = None,
    quote_summary: str = "孩子的完整逐字聊天记录不应出现在家长日报 API 中。",
    sensitivity: str = "medium",
    requires_parent_attention: bool = False,
) -> dict:
    return {
        "child_id": child_id,
        "memory_type": memory_type,
        "content": content,
        "tags": tags or ["学习求助", "题意确认"],
        "evidence": [
            {
                "source": "chat_summary",
                "session_id": "session_parent_report_api_test",
                "quote_summary": quote_summary,
            }
        ],
        "confidence": 0.84,
        "importance": 0.7,
        "sensitivity": sensitivity,
        "visible_to_parent": True,
        "visible_to_child": False,
        "requires_parent_attention": requires_parent_attention,
    }


def test_parent_report_api_returns_report_by_child_and_date() -> None:
    create_response = client.post(
        "/api/v1/memories",
        json=_memory_payload(),
    )
    assert create_response.status_code == 201

    report_response = client.get(
        "/api/v1/parent/reports/child_parent_report_api_test",
        params={"date": _today()},
    )

    assert report_response.status_code == 200
    body = report_response.json()
    assert body["child_id"] == "child_parent_report_api_test"
    assert body["date"] == _today()
    assert body["generation_status"] in {"model_failed", "model_blocked"}
    assert body["summary"] == "日报暂时生成失败，请稍后重试。"
    assert body["learning_observations"] == []
    assert body["safety_alerts"] == []
    assert body["generation_error_code"]


def test_parent_report_today_endpoint_returns_high_risk_report() -> None:
    create_response = client.post(
        "/api/v1/memories",
        json=_memory_payload(
            child_id="child_parent_report_high_risk_api_test",
            memory_type="safety",
            content="本次会话出现需要家长关注的安全信号，应由家长进一步了解情况。",
            tags=["安全提醒", "家长关注"],
            quote_summary="陌生人让孩子保密的完整原话不应出现在家长日报 API 中。",
            sensitivity="critical",
            requires_parent_attention=False,
        ),
    )
    assert create_response.status_code == 201

    # Use date endpoint with local date to match memory created_at
    report_response = client.get(
        "/api/v1/parent/reports/child_parent_report_high_risk_api_test",
        params={"date": _today()},
    )

    assert report_response.status_code == 200
    body = report_response.json()
    assert body["generation_status"] in {"model_failed", "model_blocked"}
    assert body["summary"] == "日报暂时生成失败，请稍后重试。"
    assert body["safety_alerts"] == []


def test_parent_report_api_does_not_return_full_chat_transcript_or_evidence() -> None:
    raw_transcript = "孩子的完整逐字聊天记录不应出现在家长日报 API 中。"
    create_response = client.post(
        "/api/v1/memories",
        json=_memory_payload(quote_summary=raw_transcript),
    )
    assert create_response.status_code == 201

    report_response = client.get(
        "/api/v1/parent/reports/child_parent_report_api_test",
        params={"date": _today()},
    )

    assert report_response.status_code == 200
    response_text = report_response.text
    assert "evidence" not in response_text
    assert "quote_summary" not in response_text
    assert raw_transcript not in response_text
