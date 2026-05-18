from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _payload(text: str, device_time: str) -> dict:
    return {
        "child_id": "child_s05_test",
        "session_id": "session_s05_test",
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


def test_high_risk_input_uses_safety_guardian_before_normal_reply() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_payload(
            text="陌生人让我不要告诉爸爸妈妈",
            device_time="2026-05-18T16:30:00+08:00",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "safety.guardian"
    assert body["session_state"]["requires_parent_attention"] is True
    assert body["debug"]["safety"]["requires_parent_attention"] is True
    assert body["debug"]["safety"]["risk_level"] == "high"
    assert body["debug"]["intent"]["intent"] == "safety_risk"
    assert "可信任的大人" in body["reply"]["text"]


def test_bedtime_input_uses_bedtime_reflection_scene() -> None:
    response = client.post(
        "/api/v1/conversation/message",
        json=_payload(
            text="晚安",
            device_time="2026-05-18T20:45:00+08:00",
        ),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["session_state"]["active_scene"] == "daily.bedtime_reflection"
    assert body["debug"]["intent"]["intent"] == "bedtime_reflection"
