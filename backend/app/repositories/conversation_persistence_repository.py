from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import (
    Child,
    ConversationMessageRecord,
    ConversationSessionRecord,
    RoutingDecisionRecord,
)
from app.db.session import SessionLocal


class ConversationPersistenceRepositoryUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class ConversationSessionWrite:
    id: str
    child_id: str
    base_scene: str
    active_scene: str
    session_summary: str | None = None


@dataclass(frozen=True)
class ConversationMessageWrite:
    id: str
    session_id: str
    child_id: str
    actor: str
    message_type: str
    normalized_text: str | None = None
    input_items: list[dict[str, Any]] | None = None
    attachments: list[dict[str, Any]] | None = None
    audio_url: str | None = None
    emotion: str | None = None
    agent_motion: str | None = None
    time_context: dict[str, Any] | None = None


@dataclass(frozen=True)
class RoutingDecisionWrite:
    id: str
    message_id: str | None
    session_id: str
    primary_intent: str
    active_scene: str
    sub_scene: str | None
    risk_level: str
    decision: dict[str, Any]
    signals: dict[str, Any] | None
    confidence: float | None


@dataclass(frozen=True)
class ConversationReportMessage:
    id: str
    session_id: str
    actor: str
    message_type: str
    normalized_text: str | None
    active_scene: str | None
    risk_level: str | None
    attachments_count: int
    created_at: datetime


@dataclass(frozen=True)
class ConversationTurnWrite:
    session: ConversationSessionWrite
    child_message: ConversationMessageWrite
    agent_message: ConversationMessageWrite
    routing_decision: RoutingDecisionWrite


class ConversationPersistenceRepository:
    """PostgreSQL-backed repository for minimal conversation turn persistence."""

    def __init__(
        self,
        *,
        session_factory: Callable[[], Session] = SessionLocal,
    ) -> None:
        self._session_factory = session_factory

    def upsert_session(
        self,
        session_write: ConversationSessionWrite,
    ) -> ConversationSessionRecord:
        try:
            with self._session_factory() as session:
                self._ensure_child(session, session_write.child_id)
                record = self._upsert_session_record(session, session_write)
                session.commit()
                session.refresh(record)
                return record
        except SQLAlchemyError as exc:
            raise ConversationPersistenceRepositoryUnavailable(str(exc)) from exc

    def save_message(
        self,
        message_write: ConversationMessageWrite,
    ) -> ConversationMessageRecord:
        try:
            with self._session_factory() as session:
                record = self._message_record(message_write)
                session.add(record)
                session.commit()
                session.refresh(record)
                return record
        except SQLAlchemyError as exc:
            raise ConversationPersistenceRepositoryUnavailable(str(exc)) from exc

    def save_routing_decision(
        self,
        decision_write: RoutingDecisionWrite,
    ) -> RoutingDecisionRecord:
        try:
            with self._session_factory() as session:
                record = self._routing_decision_record(decision_write)
                session.add(record)
                session.commit()
                session.refresh(record)
                return record
        except SQLAlchemyError as exc:
            raise ConversationPersistenceRepositoryUnavailable(str(exc)) from exc

    def save_turn(self, turn_write: ConversationTurnWrite) -> None:
        try:
            with self._session_factory() as session:
                self._ensure_child(session, turn_write.session.child_id)
                self._upsert_session_record(session, turn_write.session)
                session.flush()
                session.add_all(
                    [
                        self._message_record(turn_write.child_message),
                        self._message_record(turn_write.agent_message),
                    ]
                )
                session.flush()
                session.add(self._routing_decision_record(turn_write.routing_decision))
                session.commit()
        except SQLAlchemyError as exc:
            raise ConversationPersistenceRepositoryUnavailable(str(exc)) from exc

    def list_report_messages(
        self,
        *,
        child_id: str,
        report_date: date,
    ) -> list[ConversationReportMessage]:
        start = datetime.combine(report_date, time.min, tzinfo=timezone.utc)
        end = datetime.combine(report_date, time.max, tzinfo=timezone.utc)
        try:
            with self._session_factory() as session:
                rows = (
                    session.execute(
                        select(ConversationMessageRecord, RoutingDecisionRecord)
                        .outerjoin(
                            RoutingDecisionRecord,
                            RoutingDecisionRecord.message_id
                            == ConversationMessageRecord.id,
                        )
                        .where(ConversationMessageRecord.child_id == child_id)
                        .where(ConversationMessageRecord.created_at >= start)
                        .where(ConversationMessageRecord.created_at <= end)
                        .order_by(ConversationMessageRecord.created_at.asc())
                    )
                    .all()
                )
                return [
                    self._report_message(message, route)
                    for message, route in rows
                ]
        except SQLAlchemyError as exc:
            raise ConversationPersistenceRepositoryUnavailable(str(exc)) from exc

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

    def _upsert_session_record(
        self,
        session: Session,
        session_write: ConversationSessionWrite,
    ) -> ConversationSessionRecord:
        record = session.execute(
            select(ConversationSessionRecord).where(
                ConversationSessionRecord.id == session_write.id
            )
        ).scalar_one_or_none()
        if record is None:
            record = ConversationSessionRecord(
                id=session_write.id,
                child_id=session_write.child_id,
                base_scene=session_write.base_scene,
                active_scene=session_write.active_scene,
                session_summary=session_write.session_summary,
            )
            session.add(record)
            return record

        record.child_id = session_write.child_id
        record.base_scene = session_write.base_scene
        record.active_scene = session_write.active_scene
        record.session_summary = session_write.session_summary
        return record

    def _message_record(
        self,
        message_write: ConversationMessageWrite,
    ) -> ConversationMessageRecord:
        return ConversationMessageRecord(
            id=message_write.id,
            session_id=message_write.session_id,
            child_id=message_write.child_id,
            actor=message_write.actor,
            message_type=message_write.message_type,
            normalized_text=message_write.normalized_text,
            input_items=message_write.input_items,
            attachments=message_write.attachments,
            audio_url=message_write.audio_url,
            emotion=message_write.emotion,
            agent_motion=message_write.agent_motion,
            time_context=message_write.time_context,
        )

    def _routing_decision_record(
        self,
        decision_write: RoutingDecisionWrite,
    ) -> RoutingDecisionRecord:
        return RoutingDecisionRecord(
            id=decision_write.id,
            message_id=decision_write.message_id,
            session_id=decision_write.session_id,
            primary_intent=decision_write.primary_intent,
            active_scene=decision_write.active_scene,
            sub_scene=decision_write.sub_scene,
            risk_level=decision_write.risk_level,
            decision=decision_write.decision,
            signals=decision_write.signals,
            confidence=decision_write.confidence,
        )

    def _report_message(
        self,
        message: ConversationMessageRecord,
        route: RoutingDecisionRecord | None,
    ) -> ConversationReportMessage:
        return ConversationReportMessage(
            id=message.id,
            session_id=message.session_id,
            actor=message.actor,
            message_type=message.message_type,
            normalized_text=message.normalized_text,
            active_scene=route.active_scene if route else None,
            risk_level=route.risk_level if route else None,
            attachments_count=len(message.attachments or []),
            created_at=self._aware_datetime(message.created_at),
        )

    def _aware_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
