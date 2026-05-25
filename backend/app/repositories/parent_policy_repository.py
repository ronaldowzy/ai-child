from collections.abc import Callable
from typing import Any

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

    _CHILD_PROFILE_PREFERENCE_KEYS = {
        "child_age",
        "child_grade",
        "child_call_preference",
        "child_interests",
        "topic_boundaries",
        "child_profile_schema",
    }

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
                child = session.get(Child, child_id)
                return self._to_domain(record, child)
        except SQLAlchemyError as exc:
            raise ParentPolicyRepositoryUnavailable(str(exc)) from exc

    def upsert(self, policy: ParentPolicy) -> ParentPolicy:
        try:
            with self._session_factory() as session:
                child = self._ensure_child(session, policy.child_id)
                self._apply_child_profile(child, policy)
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
                record.communication_preferences = self._policy_preferences_only(
                    policy.communication_preferences
                )
                record.safety_rules = dict(policy.safety_rules)
                record.schedule = policy.schedule.model_dump(mode="json")
                record.child_nickname = None
                record.child_display_name = None
                record.parent_message_raw = policy.parent_message_raw
                record.parent_message_updated_at = policy.parent_message_updated_at
                record.version = policy.version
                record.updated_at = policy.updated_at

                session.commit()
                session.refresh(record)
                session.refresh(child)
                return self._to_domain(record, child)
        except SQLAlchemyError as exc:
            raise ParentPolicyRepositoryUnavailable(str(exc)) from exc

    def _ensure_child(self, session: Session, child_id: str) -> Child:
        child = session.get(Child, child_id)
        if child is not None:
            return child
        child = Child(
            id=child_id,
            nickname=child_id,
            timezone="Asia/Shanghai",
            profile={},
        )
        session.add(child)
        return child

    def _apply_child_profile(self, child: Child, policy: ParentPolicy) -> None:
        preferences = dict(policy.communication_preferences or {})
        profile = dict(child.profile or {})

        nickname = self._optional_str(policy.child_nickname)
        display_name = self._optional_str(policy.child_display_name)
        if nickname:
            child.nickname = nickname
            profile["child_nickname"] = nickname
        elif display_name:
            child.nickname = display_name
        if display_name:
            profile["child_display_name"] = display_name

        child_age = self._optional_int(preferences.get("child_age"))
        if child_age is not None:
            child.age = child_age

        child_grade = self._optional_str(preferences.get("child_grade"))
        if child_grade is not None:
            child.grade = child_grade

        call_preference = self._optional_str(
            preferences.get("child_call_preference")
        )
        if call_preference is not None:
            profile["child_call_preference"] = call_preference

        if "child_interests" in preferences:
            profile["child_interests"] = self._string_list(
                preferences.get("child_interests")
            )
        if "topic_boundaries" in preferences:
            profile["topic_boundaries"] = self._string_list(
                preferences.get("topic_boundaries")
            )
        if any(key in preferences for key in self._CHILD_PROFILE_PREFERENCE_KEYS):
            profile["child_profile_schema"] = str(
                preferences.get("child_profile_schema") or "child_profile_v0_1"
            )
        child.profile = profile

    def _policy_preferences_only(self, preferences: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in dict(preferences or {}).items()
            if key not in self._CHILD_PROFILE_PREFERENCE_KEYS
        }

    def _to_domain(
        self,
        record: ParentPolicyRecord,
        child: Child | None,
    ) -> ParentPolicy:
        preferences = dict(record.communication_preferences or {})
        profile = dict(child.profile or {}) if child is not None else {}

        profile_nickname = self._optional_str(profile.get("child_nickname"))
        legacy_nickname = self._optional_str(record.child_nickname)
        stored_nickname = self._optional_str(child.nickname if child else None)
        child_display_name = (
            self._optional_str(profile.get("child_display_name"))
            or self._optional_str(record.child_display_name)
        )
        child_nickname = profile_nickname or legacy_nickname
        if (
            child_nickname is None
            and stored_nickname
            and stored_nickname != record.child_id
            and stored_nickname != child_display_name
        ):
            child_nickname = stored_nickname

        if child is not None and child.age is not None:
            preferences["child_age"] = child.age
        if child is not None and child.grade:
            preferences["child_grade"] = child.grade
        for key in (
            "child_call_preference",
            "child_interests",
            "topic_boundaries",
            "child_profile_schema",
        ):
            if key in profile:
                preferences[key] = profile[key]

        return ParentPolicy(
            child_id=record.child_id,
            child_nickname=child_nickname,
            child_display_name=child_display_name,
            parent_message_raw=record.parent_message_raw,
            parent_message_updated_at=record.parent_message_updated_at,
            goals=list(record.goals or []),
            communication_preferences=preferences,
            safety_rules=dict(record.safety_rules or {}),
            schedule=ParentSchedule.model_validate(record.schedule),
            version=record.version,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _optional_int(self, value: object) -> int | None:
        try:
            return int(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _optional_str(self, value: object) -> str | None:
        text = str(value or "").strip()
        return text or None

    def _string_list(self, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split("，") if item.strip()]
        return []
