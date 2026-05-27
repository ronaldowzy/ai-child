import logging
from datetime import datetime, timezone

from app.domain.schemas.parent_policy import (
    ParentPolicy,
    ParentPolicyUpdateRequest,
)
from app.repositories.parent_policy_repository import (
    ParentPolicyRepository,
    ParentPolicyRepositoryUnavailable,
)

logger = logging.getLogger("app.parent_policy")


class ParentPolicyService:
    def __init__(
        self,
        *,
        repository: ParentPolicyRepository | None = None,
        fallback_to_memory: bool = True,
    ) -> None:
        self._policies: dict[str, ParentPolicy] = {}
        self._repository = repository or ParentPolicyRepository()
        self._fallback_to_memory = fallback_to_memory
        self._repository_available = True

    def get_policy(self, child_id: str) -> ParentPolicy:
        if self._repository_available:
            try:
                policy = self._repository.get(child_id)
                if policy is not None:
                    logger.info("get_policy: found for childId=%s", child_id)
                    self._policies[child_id] = policy
                    return policy
                logger.info("get_policy: creating default for childId=%s", child_id)
                policy = self._build_default_policy(child_id)
                return self._persist_or_remember(policy)
            except ParentPolicyRepositoryUnavailable:
                if not self._fallback_to_memory:
                    raise
                logger.warning("get_policy: repository unavailable, using memory fallback")
                self._repository_available = False

        return self._get_memory_policy(child_id)

    def update_policy(self, request: ParentPolicyUpdateRequest) -> ParentPolicy:
        logger.info(
            "update_policy: childId=%s, nickname=%s, age=%s, gender=%s",
            request.child_id,
            request.child_nickname,
            request.communication_preferences.get("child_age") if request.communication_preferences else None,
            request.communication_preferences.get("child_gender") if request.communication_preferences else None,
        )
        current = self.get_policy(request.child_id)
        now = datetime.now(timezone.utc)

        updated = current.model_copy(
            update={
                "parent_message_raw": request.parent_message_raw
                if request.parent_message_raw is not None
                else current.parent_message_raw,
                "child_nickname": request.child_nickname
                if request.child_nickname is not None
                else current.child_nickname,
                "child_display_name": request.child_display_name
                if request.child_display_name is not None
                else current.child_display_name,
                "parent_message_updated_at": now
                if request.parent_message_raw is not None
                else current.parent_message_updated_at,
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
        return self._persist_or_remember(updated)

    def _get_memory_policy(self, child_id: str) -> ParentPolicy:
        if child_id not in self._policies:
            self._policies[child_id] = self._build_default_policy(child_id)
        return self._policies[child_id]

    def _persist_or_remember(self, policy: ParentPolicy) -> ParentPolicy:
        if self._repository_available:
            try:
                saved = self._repository.upsert(policy)
                self._policies[policy.child_id] = saved
                return saved
            except ParentPolicyRepositoryUnavailable:
                if not self._fallback_to_memory:
                    raise
                self._repository_available = False
        self._policies[policy.child_id] = policy
        return policy

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
