"""SQLAlchemy-backed companion object repository."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Child, CompanionObjectRecord
from app.db.session import SessionLocal
from app.domain.companion_object import (
    CompanionObject,
    CompanionObjectSource,
    CompanionObjectStatus,
    CompanionObjectType,
)
from app.repositories.companion_object_repository import (
    CompanionObjectRepositoryUnavailable,
)


class SqlAlchemyCompanionObjectRepository:
    """SQLAlchemy-backed repository for companion_objects persistence."""

    def __init__(
        self,
        *,
        session_factory: Callable[[], Session] = SessionLocal,
    ) -> None:
        self._session_factory = session_factory

    def ensure_available(self) -> None:
        from sqlalchemy import text

        try:
            with self._session_factory() as session:
                session.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise CompanionObjectRepositoryUnavailable(str(exc)) from exc

    def save(self, companion: CompanionObject) -> CompanionObject:
        try:
            with self._session_factory() as session:
                self._ensure_child(session, companion.child_id)
                record = session.get(CompanionObjectRecord, companion.id)
                if record is None:
                    record = CompanionObjectRecord(
                        id=companion.id, child_id=companion.child_id
                    )
                    session.add(record)
                self._apply(record, companion)
                session.commit()
                session.refresh(record)
                return self._to_domain(record)
        except SQLAlchemyError as exc:
            raise CompanionObjectRepositoryUnavailable(str(exc)) from exc

    def get(self, companion_id: str) -> CompanionObject | None:
        try:
            with self._session_factory() as session:
                record = session.get(CompanionObjectRecord, companion_id)
                return self._to_domain(record) if record else None
        except SQLAlchemyError as exc:
            raise CompanionObjectRepositoryUnavailable(str(exc)) from exc

    def get_active_by_child(self, child_id: str) -> CompanionObject | None:
        try:
            with self._session_factory() as session:
                record = (
                    session.execute(
                        select(CompanionObjectRecord).where(
                            CompanionObjectRecord.child_id == child_id,
                            CompanionObjectRecord.status == CompanionObjectStatus.ACTIVE,
                        )
                    )
                    .scalars()
                    .first()
                )
                return self._to_domain(record) if record else None
        except SQLAlchemyError as exc:
            raise CompanionObjectRepositoryUnavailable(str(exc)) from exc

    def list_by_child(self, child_id: str) -> list[CompanionObject]:
        try:
            with self._session_factory() as session:
                records = (
                    session.execute(
                        select(CompanionObjectRecord)
                        .where(CompanionObjectRecord.child_id == child_id)
                        .order_by(CompanionObjectRecord.created_at.desc())
                    )
                    .scalars()
                    .all()
                )
                return [self._to_domain(r) for r in records]
        except SQLAlchemyError as exc:
            raise CompanionObjectRepositoryUnavailable(str(exc)) from exc

    def delete(self, companion_id: str) -> bool:
        try:
            with self._session_factory() as session:
                record = session.get(CompanionObjectRecord, companion_id)
                if record is None:
                    return False
                session.delete(record)
                session.commit()
                return True
        except SQLAlchemyError as exc:
            raise CompanionObjectRepositoryUnavailable(str(exc)) from exc

    def clear(self) -> None:
        from sqlalchemy import delete as sqlalchemy_delete

        try:
            with self._session_factory() as session:
                session.execute(sqlalchemy_delete(CompanionObjectRecord))
                session.commit()
        except SQLAlchemyError as exc:
            raise CompanionObjectRepositoryUnavailable(str(exc)) from exc

    def _ensure_child(self, session: Session, child_id: str) -> None:
        child = session.get(Child, child_id)
        if child is None:
            raise CompanionObjectRepositoryUnavailable(
                f"child_id {child_id} does not exist in children table"
            )

    def _apply(
        self, record: CompanionObjectRecord, companion: CompanionObject
    ) -> None:
        record.child_id = companion.child_id
        record.name = companion.name
        record.object_type = companion.object_type.value
        record.source_type = companion.source_type.value
        record.safe_summary = companion.safe_summary
        record.light_location = companion.light_location
        record.status = companion.status.value
        record.visual_kind = companion.visual_kind
        record.last_recalled_at = companion.last_recalled_at
        record.recall_count = companion.recall_count
        record.skip_count = companion.skip_count
        record.created_at = companion.created_at
        record.updated_at = companion.updated_at

    def _to_domain(self, record: CompanionObjectRecord) -> CompanionObject:
        from app.domain.companion_object import resolve_visual_kind

        visual_kind = record.visual_kind
        if not visual_kind:
            visual_kind = resolve_visual_kind(record.object_type)
        return CompanionObject(
            id=record.id,
            child_id=record.child_id,
            name=record.name,
            object_type=CompanionObjectType(record.object_type),
            source_type=CompanionObjectSource(record.source_type),
            safe_summary=record.safe_summary,
            light_location=record.light_location,
            status=CompanionObjectStatus(record.status),
            visual_kind=visual_kind,
            last_recalled_at=self._aware_datetime(record.last_recalled_at),
            recall_count=record.recall_count,
            skip_count=record.skip_count,
            created_at=self._aware_datetime(record.created_at),
            updated_at=self._aware_datetime(record.updated_at),
        )

    def _aware_datetime(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
