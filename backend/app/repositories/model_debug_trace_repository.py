from collections.abc import Callable

from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import ModelDebugTraceRecord
from app.db.session import SessionLocal
from app.domain.model_debug_trace import ModelDebugTrace, ModelDebugTraceCreate


class ModelDebugTraceRepositoryUnavailable(RuntimeError):
    pass


class ModelDebugTraceRepository:
    """SQLAlchemy repository for opt-in local model prompt traces."""

    def __init__(
        self,
        *,
        session_factory: Callable[[], Session] = SessionLocal,
    ) -> None:
        self._session_factory = session_factory

    def save(self, trace: ModelDebugTraceCreate) -> ModelDebugTrace:
        try:
            with self._session_factory() as session:
                record = self._to_record(trace)
                session.add(record)
                session.commit()
                session.refresh(record)
                return self._to_domain(record)
        except SQLAlchemyError as exc:
            raise ModelDebugTraceRepositoryUnavailable(str(exc)) from exc

    def list_recent(self, *, limit: int = 20) -> list[ModelDebugTrace]:
        try:
            with self._session_factory() as session:
                records = (
                    session.execute(
                        select(ModelDebugTraceRecord)
                        .order_by(ModelDebugTraceRecord.created_at.desc())
                        .limit(max(limit, 0))
                    )
                    .scalars()
                    .all()
                )
                return [self._to_domain(record) for record in records]
        except SQLAlchemyError as exc:
            raise ModelDebugTraceRepositoryUnavailable(str(exc)) from exc

    def clear(self) -> int:
        try:
            with self._session_factory() as session:
                result = session.execute(sqlalchemy_delete(ModelDebugTraceRecord))
                session.commit()
                return int(result.rowcount or 0)
        except SQLAlchemyError as exc:
            raise ModelDebugTraceRepositoryUnavailable(str(exc)) from exc

    def _to_record(self, trace: ModelDebugTraceCreate) -> ModelDebugTraceRecord:
        return ModelDebugTraceRecord(
            id=trace.id,
            created_at=trace.created_at,
            request_id=trace.request_id,
            task_type=trace.task_type,
            profile_name=trace.profile_name,
            provider_name=trace.provider_name,
            model_name=trace.model_name,
            child_id=trace.child_id,
            session_id=trace.session_id,
            child_id_hash=trace.child_id_hash,
            session_id_hash=trace.session_id_hash,
            request_messages_json=trace.request_messages_json,
            request_input_text=trace.request_input_text,
            request_context_json=trace.request_context_json,
            request_metadata_json=trace.request_metadata_json,
            request_params_json=trace.request_params_json,
            response_text=trace.response_text,
            response_structured_output_json=trace.response_structured_output_json,
            response_metadata_json=trace.response_metadata_json,
            fallback_used=trace.fallback_used,
            policy_blocked=trace.policy_blocked,
            error_type=trace.error_type,
            error_detail=trace.error_detail,
            elapsed_ms=trace.elapsed_ms,
            trace_source=trace.trace_source,
            environment=trace.environment,
        )

    def _to_domain(self, record: ModelDebugTraceRecord) -> ModelDebugTrace:
        return ModelDebugTrace(
            id=record.id,
            created_at=record.created_at,
            request_id=record.request_id,
            task_type=record.task_type,
            profile_name=record.profile_name,
            provider_name=record.provider_name,
            model_name=record.model_name,
            child_id=record.child_id,
            session_id=record.session_id,
            child_id_hash=record.child_id_hash,
            session_id_hash=record.session_id_hash,
            request_messages_json=record.request_messages_json,
            request_input_text=record.request_input_text,
            request_context_json=record.request_context_json,
            request_metadata_json=record.request_metadata_json,
            request_params_json=record.request_params_json,
            response_text=record.response_text,
            response_structured_output_json=record.response_structured_output_json,
            response_metadata_json=record.response_metadata_json,
            fallback_used=record.fallback_used,
            policy_blocked=record.policy_blocked,
            error_type=record.error_type,
            error_detail=record.error_detail,
            elapsed_ms=record.elapsed_ms,
            trace_source=record.trace_source,
            environment=record.environment,
        )
