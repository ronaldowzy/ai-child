from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.domain.memory import (
    MemoryCreateRequest,
    MemoryEvidence,
    MemorySensitivity,
    MemoryType,
    MemoryUpdateRequest,
)
from app.repositories.memory_repository import (
    InMemoryMemoryRepository,
    MemoryRepositoryUnavailable,
)
from app.repositories.memory_sql_repository import SqlAlchemyMemoryRepository
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


def _sqlite_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
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


def test_memory_service_create_can_read_back_from_sql_repository() -> None:
    repository = SqlAlchemyMemoryRepository(
        session_factory=_sqlite_session_factory()
    )
    service = MemoryService(repository=repository, now_provider=_fixed_now)

    created = service.create(_request())
    reloaded = repository.get(created.id)

    assert reloaded is not None
    assert reloaded.id == created.id
    assert reloaded.content == created.content
    assert reloaded.evidence[0].quote_summary == "孩子主动讲到霸王龙和三角龙。"


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


def test_memory_service_retrieve_sorts_by_query_score_importance_and_confidence() -> None:
    service = _service()
    lower_rank = service.create(
        _request(
            content="孩子也有学习求助记录。",
            tags=["学习求助"],
            memory_type=MemoryType.LEARNING_PATTERN,
        ).model_copy(update={"importance": 0.4, "confidence": 0.4})
    )
    higher_rank = service.create(
        _request(
            content="孩子最近学习求助时适合先复述题意。",
            tags=["学习求助", "题意"],
            memory_type=MemoryType.LEARNING_PATTERN,
        ).model_copy(update={"importance": 0.8, "confidence": 0.8})
    )

    retrieved = service.retrieve(
        "child_memory_service_test",
        query="学习求助 题意",
    )

    assert [memory.id for memory in retrieved] == [higher_rank.id, lower_rank.id]


def test_memory_service_marks_critical_memory_for_parent_attention() -> None:
    service = _service()

    memory = service.create(
        _request(
            memory_type=MemoryType.SAFETY,
            content="本次会话出现需要家长关注的安全信号，应进一步了解情况。",
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

    for source in ("full_transcript", "raw_transcript", "verbatim_child_text"):
        with pytest.raises(UnsafeMemoryError):
            service.create(
                _request(
                    content="孩子最近对植物感兴趣。",
                    tags=["植物"],
                ).model_copy(
                    update={
                        "evidence": [
                            MemoryEvidence(
                                source=source,
                                session_id="session_memory_service_test",
                                quote_summary="不应保存逐字转写。",
                            )
                        ]
                    },
                    deep=True,
                )
            )

    with pytest.raises(UnsafeMemoryError):
        service.create(
            _request(
                content="孩子就是不愿意表达。",
                tags=["表达"],
            )
        )


def test_memory_service_repository_failure_falls_back_without_sensitive_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FailingRepository:
        def save(self, _memory):
            raise MemoryRepositoryUnavailable("contains raw child details")

        def get(self, _memory_id):
            raise MemoryRepositoryUnavailable("contains raw child details")

        def list_by_child(self, _child_id):
            raise MemoryRepositoryUnavailable("contains raw child details")

        def delete(self, _memory_id):
            raise MemoryRepositoryUnavailable("contains raw child details")

        def clear(self):
            raise MemoryRepositoryUnavailable("contains raw child details")

    caplog.set_level("WARNING", logger="app.memory_service")
    service = MemoryService(
        repository=FailingRepository(),
        fallback_repository=InMemoryMemoryRepository(),
        now_provider=_fixed_now,
    )
    request = _request(
        content="孩子最近对植物话题感兴趣，可以作为表达切入点。"
    )

    created = service.create(request)
    retrieved = service.retrieve("child_memory_service_test", query="植物")

    assert [memory.id for memory in retrieved] == [created.id]
    assert "memory_repository_fallback" in caplog.text
    assert "孩子最近对植物话题感兴趣" not in caplog.text
    assert "孩子主动讲到霸王龙和三角龙" not in caplog.text
    assert "contains raw child details" not in caplog.text
