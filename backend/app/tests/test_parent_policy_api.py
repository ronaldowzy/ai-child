from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_parent_policy_get_returns_default_policy() -> None:
    response = client.get(
        "/api/v1/parent/policy",
        params={"child_id": "child_policy_default_test"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["child_id"] == "child_policy_default_test"
    assert "鼓励孩子每天说一件学校小事" in body["goals"]
    assert body["schedule"]["daily_schedule"]


def test_parent_policy_post_updates_goals() -> None:
    child_id = "child_policy_update_test"
    goals = [
        "鼓励孩子说出今天遇到的一个小困难",
        "数学题先复述题意",
    ]

    update_response = client.post(
        "/api/v1/parent/policy",
        json={
            "child_id": child_id,
            "goals": goals,
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["goals"] == goals

    get_response = client.get(f"/api/v1/parent/policy/{child_id}")

    assert get_response.status_code == 200
    assert get_response.json()["goals"] == goals


def test_parent_policy_post_updates_parent_message_raw() -> None:
    child_id = "child_policy_parent_message_test"
    parent_message = "小名叫豆豆，最近喜欢恐龙。不要说孩子胆小。"

    update_response = client.post(
        "/api/v1/parent/policy",
        json={
            "child_id": child_id,
            "parent_message_raw": parent_message,
        },
    )

    assert update_response.status_code == 200
    body = update_response.json()
    assert body["parent_message_raw"] == parent_message
    assert body["parent_message_updated_at"] is not None

    get_response = client.get(f"/api/v1/parent/policy/{child_id}")

    assert get_response.status_code == 200
    assert get_response.json()["parent_message_raw"] == parent_message
