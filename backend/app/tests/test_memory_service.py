from datetime import datetime, timedelta, timezone

import pytest

from app.domain.memory import (
    MemoryCreateRequest,
    MemoryEvidence,
    MemorySensitivity,
    MemoryType,
    MemoryUpdateRequest,
)
from app.repositories.memory_repository import InMemoryMemoryRepository
from app.services.memory_service import MemoryService, UnsafeMemoryError


def _fixed_now() -> datetime:
    return datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc)


def _request(
    *,
    child_id: str = "child_memory_service_test",
    memory_type: MemoryType = MemoryType.INTEREST,
    content: str = "孩子最近对恐龙话题感兴趣，可以作为阅读和表达切入点。",
    tags: list[str] | None = None,
    sensitivity: MemorySensitivity = MemorySensitivity.LOW,
    requires_parent_attention: bool = False,
    expires_at: datetime | None = None,
) -> MemoryCreateRequest:
    return MemoryCreateRequest(
        child_id=child_id,
        memory_type=memory_type,
        content=content,
        tags=tags or ["恐龙", "兴趣"],
        evidence=[
            MemoryEvidence(
                source="chat_summary",
                session_id="session_memory_service_test",
                quote_summary="孩子主动讲到霸王龙和三角龙。",
            )
        ],
        confidence=0.82,
        importance=0.7,
        sensitivity=sensitivity,
        requires_parent_attention=requires_parent_attention,
        expires_at=expires_at,
    )


def _service() -> MemoryService:
    return MemoryService(
        repository=InMemoryMemoryRepository(),
        now_provider=_fixed_now,
    )


def test_memory_service_creates_and_retrieves_active_memory() -> None:
    service = _service()

    created = service.create(_request())
    retrieved = service.retrieve("child_memory_service_test", query="恐龙")

    assert created.id
    assert created.created_at == _fixed_now()
    assert created.updated_at == _fixed_now()
    assert created.evidence[0].source == "chat_summary"
    assert created.confidence == 0.82
    assert created.expires_at == _fixed_now() + timedelta(days=180)
    assert [memory.id for memory in retrieved] == [created.id]


def test_memory_service_filters_expired_memories_from_retrieve() -> None:
    service = _service()
    expired = service.create(
        _request(expires_at=_fixed_now() - timedelta(minutes=1))
    )
    active = service.create(_request(content="孩子喜欢围绕恐龙继续提问。"))

    retrieved = service.retrieve("child_memory_service_test", query="恐龙")
    all_memories = service.list_memories(
        "child_memory_service_test",
        active_only=False,
    )

    assert [memory.id for memory in retrieved] == [active.id]
    assert {memory.id for memory in all_memories} == {expired.id, active.id}


def test_memory_service_marks_critical_memory_for_parent_attention() -> None:
    service = _service()

    memory = service.create(
        _request(
            memory_type=MemoryType.SAFETY,
            content="本次会话出现需要父亲关注的安全信号，应进一步了解情况。",
            tags=["安全提醒"],
            sensitivity=MemorySensitivity.CRITICAL,
            requires_parent_attention=False,
        )
    )

    assert memory.sensitivity == MemorySensitivity.CRITICAL
    assert memory.requires_parent_attention is True
    assert memory.visible_to_parent is True
    assert service.retrieve(
        "child_memory_service_test",
        include_safety=False,
    ) == []
    assert service.retrieve(
        "child_memory_service_test",
        include_safety=True,
    )[0].id == memory.id


def test_memory_service_updates_and_deletes_memory() -> None:
    service = _service()
    created = service.create(_request())

    updated = service.update(
        created.id,
        MemoryUpdateRequest(
            content="孩子对恐龙和化石话题都表现出兴趣。",
            tags=["恐龙", "化石"],
            confidence=0.88,
        ),
    )
    deleted = service.delete(created.id)

    assert updated.content == "孩子对恐龙和化石话题都表现出兴趣。"
    assert updated.tags == ["恐龙", "化石"]
    assert updated.confidence == 0.88
    assert deleted is True
    assert service.list_memories("child_memory_service_test") == []


def test_memory_service_rejects_raw_media_or_fixed_negative_labels() -> None:
    service = _service()

    with pytest.raises(UnsafeMemoryError):
        service.create(
            _request(
                content="孩子最近对植物感兴趣。",
                tags=["植物"],
                expires_at=None,
            ).model_copy(
                update={
                    "evidence": [
                        MemoryEvidence(
                            source="raw_audio",
                            session_id="session_memory_service_test",
                            quote_summary="原始音频内容不应长期保存。",
                        )
                    ]
                }
            )
        )

    with pytest.raises(UnsafeMemoryError):
        service.create(
            _request(
                content="孩子胆小、不合群。",
                tags=["表达"],
            )
        )
