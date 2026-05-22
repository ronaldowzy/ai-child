from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Child, MemoryItemRecord
from app.db.session import SessionLocal
from app.domain.memory import (
    MemoryEvidence,
    MemoryItem,
    MemorySensitivity,
    MemoryType,
)
from app.repositories.memory_repository import MemoryRepositoryUnavailable


class SqlAlchemyMemoryRepository:
    """SQLAlchemy-backed repository for DB1-B4 memory_items persistence."""

    def __init__(
        self,
        *,
        session_factory: Callable[[], Session] = SessionLocal,
    ) -> None:
        self._session_factory = session_factory

    def ensure_available(self) -> None:
        try:
            with self._session_factory() as session:
                session.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise MemoryRepositoryUnavailable(str(exc)) from exc

    def save(self, memory: MemoryItem) -> MemoryItem:
        try:
            with self._session_factory() as session:
                self._ensure_child(session, memory.child_id)
                record = session.get(MemoryItemRecord, memory.id)
                if record is None:
                    record = MemoryItemRecord(id=memory.id, child_id=memory.child_id)
                    session.add(record)
                self._apply_memory(record, memory)
                session.commit()
                session.refresh(record)
                return self._to_domain(record)
        except SQLAlchemyError as exc:
            raise MemoryRepositoryUnavailable(str(exc)) from exc

    def get(self, memory_id: str) -> MemoryItem | None:
        try:
            with self._session_factory() as session:
                record = session.get(MemoryItemRecord, memory_id)
                if record is None:
                    return None
                return self._to_domain(record)
        except SQLAlchemyError as exc:
            raise MemoryRepositoryUnavailable(str(exc)) from exc

    def list_by_child(self, child_id: str) -> list[MemoryItem]:
        try:
            with self._session_factory() as session:
                records = (
                    session.execute(
                        select(MemoryItemRecord)
                        .where(MemoryItemRecord.child_id == child_id)
                        .order_by(MemoryItemRecord.created_at.desc())
                    )
                    .scalars()
                    .all()
                )
                return [self._to_domain(record) for record in records]
        except SQLAlchemyError as exc:
            raise MemoryRepositoryUnavailable(str(exc)) from exc

    def delete(self, memory_id: str) -> bool:
        try:
            with self._session_factory() as session:
                record = session.get(MemoryItemRecord, memory_id)
                if record is None:
                    return False
                session.delete(record)
                session.commit()
                return True
        except SQLAlchemyError as exc:
            raise MemoryRepositoryUnavailable(str(exc)) from exc

    def clear(self) -> None:
        try:
            with self._session_factory() as session:
                session.execute(sqlalchemy_delete(MemoryItemRecord))
                session.commit()
        except SQLAlchemyError as exc:
            raise MemoryRepositoryUnavailable(str(exc)) from exc

    def _ensure_child(self, session: Session, child_id: str) -> None:
        child = session.get(Child, child_id)
        if child is not None:
            return
        session.add(
            Child(
                id=child_id,
                nickname=child_id,
                timezone="Asia/Shanghai",
                profile={},
            )
        )

    def _apply_memory(
        self,
        record: MemoryItemRecord,
        memory: MemoryItem,
    ) -> None:
        record.child_id = memory.child_id
        record.memory_type = memory.memory_type.value
        record.content = memory.content
        record.tags = list(memory.tags)
        record.evidence = [
            evidence.model_dump(mode="json") for evidence in memory.evidence
        ]
        record.confidence = memory.confidence
        record.importance = memory.importance
        record.sensitivity = memory.sensitivity.value
        record.visible_to_parent = memory.visible_to_parent
        record.visible_to_child = memory.visible_to_child
        record.requires_parent_attention = memory.requires_parent_attention
        record.embedding_id = memory.embedding_id
        record.expires_at = memory.expires_at
        record.created_at = memory.created_at
        record.updated_at = memory.updated_at

    def _to_domain(self, record: MemoryItemRecord) -> MemoryItem:
        return MemoryItem(
            id=record.id,
            child_id=record.child_id,
            memory_type=MemoryType(record.memory_type),
            content=record.content,
            tags=list(record.tags or []),
            evidence=[
                MemoryEvidence.model_validate(evidence)
                for evidence in record.evidence
            ],
            confidence=record.confidence,
            importance=record.importance,
            sensitivity=MemorySensitivity(record.sensitivity),
            visible_to_parent=record.visible_to_parent,
            visible_to_child=record.visible_to_child,
            requires_parent_attention=record.requires_parent_attention,
            expires_at=self._aware_datetime(record.expires_at),
            embedding_id=record.embedding_id,
            created_at=self._aware_datetime(record.created_at),
            updated_at=self._aware_datetime(record.updated_at),
        )

    def _aware_datetime(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
