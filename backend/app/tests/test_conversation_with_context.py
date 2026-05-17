from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _payload(child_id: str, text: str, device_time: str) -> dict:
    return {
        "child_id": child_id,
        "session_id": f"session_{child_id}",
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


def test_conversation_debug_includes_after_school_time_context() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_payload(
            child_id="child_conversation_after_school_test",
            text="我回来了",
            device_time="2026-05-18T16:30:00+08:00",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["debug"]["time_context"]["time_period"] == "after_school"


def test_conversation_debug_includes_bedtime_time_context() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_payload(
            child_id="child_conversation_bedtime_test",
            text="晚安",
            device_time="2026-05-18T20:45:00+08:00",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["debug"]["time_context"]["time_period"] == "bedtime"


def test_conversation_reads_updated_parent_goals() -> None:
    child_id = "child_conversation_parent_goal_test"
    goals = [
        "鼓励孩子说出今天遇到的一个小困难",
        "遇到作业问题时先讲思路",
    ]

    policy_response = client.post(
        "/api/v1/parent/policy",
        json={
            "child_id": child_id,
            "goals": goals,
        },
    )
    assert policy_response.status_code == 200

    conversation_response = client.post(
        "/api/v1/conversation/message",
        json=_payload(
            child_id=child_id,
            text="我有一道题不会",
            device_time="2026-05-18T16:30:00+08:00",
        ),
    )

    assert conversation_response.status_code == 200
    body = conversation_response.json()

    assert body["debug"]["parent_policy"]["goals"] == goals
    assert body["debug"]["time_context"]["time_period"] == "after_school"
