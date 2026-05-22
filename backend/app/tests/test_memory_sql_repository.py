from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.domain.memory import (
    MemoryEvidence,
    MemoryItem,
    MemorySensitivity,
    MemoryType,
)
from app.repositories.memory_sql_repository import SqlAlchemyMemoryRepository


def _sqlite_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def _memory(
    *,
    memory_id: str = "memory_sql_1",
    child_id: str = "child_memory_sql",
    content: str = "孩子最近对恐龙话题感兴趣，可以作为表达切入点。",
    tags: list[str] | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    expires_at: datetime | None = None,
    embedding_id: str | None = "embedding_memory_sql_1",
    visible_to_parent: bool = True,
    visible_to_child: bool = False,
    requires_parent_attention: bool = False,
) -> MemoryItem:
    now = created_at or datetime(2026, 5, 22, 8, 0, tzinfo=timezone.utc)
    return MemoryItem(
        id=memory_id,
        child_id=child_id,
        memory_type=MemoryType.INTEREST,
        content=content,
        tags=tags or ["恐龙", "兴趣"],
        evidence=[
            MemoryEvidence(
                source="conversation_summary",
                session_id="session_memory_sql",
                quote_summary="孩子主动讲到恐龙兴趣。",
                metadata={"active_scene": "conversation.open"},
            )
        ],
        confidence=0.82,
        importance=0.7,
        sensitivity=MemorySensitivity.MEDIUM,
        visible_to_parent=visible_to_parent,
        visible_to_child=visible_to_child,
        requires_parent_attention=requires_parent_attention,
        expires_at=expires_at or now + timedelta(days=30),
        embedding_id=embedding_id,
        created_at=now,
        updated_at=updated_at or now,
    )


def test_sql_memory_repository_save_get_roundtrips_all_fields() -> None:
    repository = SqlAlchemyMemoryRepository(
        session_factory=_sqlite_session_factory()
    )
    memory = _memory(
        visible_to_child=True,
        requires_parent_attention=True,
    )

    saved = repository.save(memory)
    reloaded = repository.get(memory.id)

    assert reloaded is not None
    assert saved.id == memory.id
    assert reloaded.child_id == memory.child_id
    assert reloaded.memory_type == MemoryType.INTEREST
    assert reloaded.content == memory.content
    assert reloaded.tags == ["恐龙", "兴趣"]
    assert reloaded.evidence[0].source == "conversation_summary"
    assert reloaded.evidence[0].metadata == {"active_scene": "conversation.open"}
    assert reloaded.confidence == 0.82
    assert reloaded.importance == 0.7
    assert reloaded.sensitivity == MemorySensitivity.MEDIUM
    assert reloaded.visible_to_parent is True
    assert reloaded.visible_to_child is True
    assert reloaded.requires_parent_attention is True
    assert reloaded.embedding_id == "embedding_memory_sql_1"
    assert reloaded.expires_at == memory.expires_at
    assert reloaded.created_at == memory.created_at
    assert reloaded.updated_at == memory.updated_at


def test_sql_memory_repository_save_same_id_updates_without_duplicate() -> None:
    repository = SqlAlchemyMemoryRepository(
        session_factory=_sqlite_session_factory()
    )
    original = _memory(memory_id="memory_sql_update")
    updated = original.model_copy(
        update={
            "content": "孩子最近对化石话题也表现出兴趣。",
            "tags": ["化石", "兴趣"],
            "updated_at": original.updated_at + timedelta(hours=1),
        },
        deep=True,
    )

    repository.save(original)
    repository.save(updated)
    memories = repository.list_by_child(original.child_id)

    assert len(memories) == 1
    assert memories[0].id == "memory_sql_update"
    assert memories[0].content == "孩子最近对化石话题也表现出兴趣。"
    assert memories[0].tags == ["化石", "兴趣"]


def test_sql_memory_repository_list_filters_child_and_sorts_created_desc() -> None:
    repository = SqlAlchemyMemoryRepository(
        session_factory=_sqlite_session_factory()
    )
    older = _memory(
        memory_id="memory_sql_older",
        created_at=datetime(2026, 5, 20, 8, 0, tzinfo=timezone.utc),
    )
    newer = _memory(
        memory_id="memory_sql_newer",
        created_at=datetime(2026, 5, 21, 8, 0, tzinfo=timezone.utc),
    )
    other_child = _memory(
        memory_id="memory_sql_other_child",
        child_id="child_memory_sql_other",
        created_at=datetime(2026, 5, 22, 8, 0, tzinfo=timezone.utc),
    )

    repository.save(older)
    repository.save(newer)
    repository.save(other_child)

    assert [memory.id for memory in repository.list_by_child("child_memory_sql")] == [
        "memory_sql_newer",
        "memory_sql_older",
    ]


def test_sql_memory_repository_delete_returns_bool() -> None:
    repository = SqlAlchemyMemoryRepository(
        session_factory=_sqlite_session_factory()
    )
    memory = _memory(memory_id="memory_sql_delete")
    repository.save(memory)

    assert repository.delete(memory.id) is True
    assert repository.delete(memory.id) is False
    assert repository.get(memory.id) is None


def test_sql_memory_repository_json_and_visibility_roundtrip() -> None:
    repository = SqlAlchemyMemoryRepository(
        session_factory=_sqlite_session_factory()
    )
    expires_at = datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc)
    memory = _memory(
        memory_id="memory_sql_json",
        tags=["  恐龙  ", "兴趣"],
        expires_at=expires_at,
        embedding_id="embedding_json_roundtrip",
        visible_to_parent=False,
        visible_to_child=True,
        requires_parent_attention=False,
    )

    repository.save(memory)
    reloaded = repository.get(memory.id)

    assert reloaded is not None
    assert reloaded.tags == ["恐龙", "兴趣"]
    assert reloaded.evidence[0].quote_summary == "孩子主动讲到恐龙兴趣。"
    assert reloaded.expires_at == expires_at
    assert reloaded.embedding_id == "embedding_json_roundtrip"
    assert reloaded.visible_to_parent is False
    assert reloaded.visible_to_child is True
    assert reloaded.requires_parent_attention is False
