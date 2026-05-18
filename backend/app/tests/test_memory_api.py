from fastapi.testclient import TestClient

from app.main import app
from app.repositories.memory_repository import get_memory_repository


client = TestClient(app)


def setup_function() -> None:
    get_memory_repository().clear()


def _memory_payload(
    *,
    child_id: str = "child_memory_api_test",
    content: str = "孩子最近对恐龙话题感兴趣，可以作为表达切入点。",
    memory_type: str = "interest",
    expires_at: str | None = None,
) -> dict:
    payload = {
        "child_id": child_id,
        "memory_type": memory_type,
        "content": content,
        "tags": ["恐龙", "兴趣"],
        "evidence": [
            {
                "source": "chat_summary",
                "session_id": "session_memory_api_test",
                "quote_summary": "孩子主动聊到霸王龙。",
            }
        ],
        "confidence": 0.84,
        "importance": 0.7,
        "sensitivity": "low",
        "visible_to_parent": True,
        "visible_to_child": False,
        "requires_parent_attention": False,
    }
    if expires_at is not None:
        payload["expires_at"] = expires_at
    return payload


def test_memory_api_parent_can_create_list_update_and_delete_memory() -> None:
    create_response = client.post(
        "/api/v1/memories",
        json=_memory_payload(),
    )

    assert create_response.status_code == 201
    created = create_response.json()
    memory_id = created["id"]

    list_response = client.get("/api/v1/memories/child_memory_api_test")
    assert list_response.status_code == 200
    assert [memory["id"] for memory in list_response.json()] == [memory_id]

    update_response = client.patch(
        f"/api/v1/memories/{memory_id}",
        json={
            "content": "孩子对恐龙和化石话题都表现出兴趣。",
            "tags": ["恐龙", "化石"],
            "confidence": 0.9,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["content"] == "孩子对恐龙和化石话题都表现出兴趣。"
    assert update_response.json()["tags"] == ["恐龙", "化石"]

    delete_response = client.delete(f"/api/v1/memories/{memory_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted": True}

    empty_response = client.get("/api/v1/memories/child_memory_api_test")
    assert empty_response.status_code == 200
    assert empty_response.json() == []


def test_memory_api_filters_expired_memories_by_default() -> None:
    create_response = client.post(
        "/api/v1/memories",
        json=_memory_payload(expires_at="2000-01-01T00:00:00+00:00"),
    )

    assert create_response.status_code == 201
    memory_id = create_response.json()["id"]

    active_response = client.get("/api/v1/memories/child_memory_api_test")
    inactive_response = client.get(
        "/api/v1/memories/child_memory_api_test",
        params={"active": False},
    )

    assert active_response.status_code == 200
    assert active_response.json() == []
    assert inactive_response.status_code == 200
    assert [memory["id"] for memory in inactive_response.json()] == [memory_id]


def test_memory_api_keeps_high_risk_memory_visible_to_parent() -> None:
    response = client.post(
        "/api/v1/memories",
        json=_memory_payload(
            memory_type="safety",
            content="本次会话出现需要父亲关注的安全信号，应进一步了解情况。",
        )
        | {
            "tags": ["安全提醒"],
            "sensitivity": "critical",
            "requires_parent_attention": False,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["sensitivity"] == "critical"
    assert body["requires_parent_attention"] is True
    assert body["visible_to_parent"] is True


def test_memory_api_rejects_raw_audio_as_long_term_memory_evidence() -> None:
    payload = _memory_payload()
    payload["evidence"] = [
        {
            "source": "raw_audio",
            "session_id": "session_memory_api_test",
            "quote_summary": "原始音频内容不应长期保存。",
        }
    ]

    response = client.post("/api/v1/memories", json=payload)

    assert response.status_code == 422
