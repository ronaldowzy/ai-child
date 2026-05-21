from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Child, ParentPolicyRecord
from app.db.session import SessionLocal
from app.domain.schemas.parent_policy import ParentPolicy, ParentSchedule


class ParentPolicyRepositoryUnavailable(RuntimeError):
    pass


class ParentPolicyRepository:
    """PostgreSQL-backed parent policy repository for DB1-B."""

    def __init__(
        self,
        *,
        session_factory: Callable[[], Session] = SessionLocal,
    ) -> None:
        self._session_factory = session_factory

    def get(self, child_id: str) -> ParentPolicy | None:
        try:
            with self._session_factory() as session:
                record = session.execute(
                    select(ParentPolicyRecord).where(
                        ParentPolicyRecord.child_id == child_id
                    )
                ).scalar_one_or_none()
                if record is None:
                    return None
                return self._to_domain(record)
        except SQLAlchemyError as exc:
            raise ParentPolicyRepositoryUnavailable(str(exc)) from exc

    def upsert(self, policy: ParentPolicy) -> ParentPolicy:
        try:
            with self._session_factory() as session:
                self._ensure_child(session, policy.child_id)
                record = session.execute(
                    select(ParentPolicyRecord).where(
                        ParentPolicyRecord.child_id == policy.child_id
                    )
                ).scalar_one_or_none()
                if record is None:
                    record = ParentPolicyRecord(
                        id=f"policy_{policy.child_id}",
                        child_id=policy.child_id,
                        goals=[],
                        communication_preferences={},
                        safety_rules={},
                        schedule={},
                        version=1,
                    )
                    session.add(record)

                record.goals = list(policy.goals)
                record.communication_preferences = dict(
                    policy.communication_preferences
                )
                record.safety_rules = dict(policy.safety_rules)
                record.schedule = policy.schedule.model_dump(mode="json")
                record.parent_message_raw = policy.parent_message_raw
                record.parent_message_updated_at = policy.parent_message_updated_at
                record.version = policy.version
                record.updated_at = policy.updated_at

                session.commit()
                session.refresh(record)
                return self._to_domain(record)
        except SQLAlchemyError as exc:
            raise ParentPolicyRepositoryUnavailable(str(exc)) from exc

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

    def _to_domain(self, record: ParentPolicyRecord) -> ParentPolicy:
        return ParentPolicy(
            child_id=record.child_id,
            parent_message_raw=record.parent_message_raw,
            parent_message_updated_at=record.parent_message_updated_at,
            goals=list(record.goals or []),
            communication_preferences=dict(record.communication_preferences or {}),
            safety_rules=dict(record.safety_rules or {}),
            schedule=ParentSchedule.model_validate(record.schedule),
            version=record.version,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
