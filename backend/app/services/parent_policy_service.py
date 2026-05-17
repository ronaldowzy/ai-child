from datetime import datetime, timezone

from app.domain.schemas.parent_policy import (
    ParentPolicy,
    ParentPolicyUpdateRequest,
)


class ParentPolicyService:
    def __init__(self) -> None:
        self._policies: dict[str, ParentPolicy] = {}

    def get_policy(self, child_id: str) -> ParentPolicy:
        if child_id not in self._policies:
            self._policies[child_id] = self._build_default_policy(child_id)
        return self._policies[child_id]

    def update_policy(self, request: ParentPolicyUpdateRequest) -> ParentPolicy:
        current = self.get_policy(request.child_id)
        now = datetime.now(timezone.utc)

        updated = current.model_copy(
            update={
                "goals": request.goals
                if request.goals is not None
                else current.goals,
                "communication_preferences": request.communication_preferences
                if request.communication_preferences is not None
                else current.communication_preferences,
                "safety_rules": request.safety_rules
                if request.safety_rules is not None
                else current.safety_rules,
                "schedule": request.schedule
                if request.schedule is not None
                else current.schedule,
                "version": current.version + 1,
                "updated_at": now,
            },
            deep=True,
        )
        self._policies[request.child_id] = updated
        return updated

    def _build_default_policy(self, child_id: str) -> ParentPolicy:
        now = datetime.now(timezone.utc)
        return ParentPolicy(
            child_id=child_id,
            created_at=now,
            updated_at=now,
        )


_parent_policy_service = ParentPolicyService()


def get_parent_policy_service() -> ParentPolicyService:
    return _parent_policy_service
