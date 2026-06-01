"""Companion object (小屋小客人) service.

Business rules:
- One child max one active companion object
- Create validates safe_summary against forbidden markers
- Recall respects: bedtime suppression, same-session suppression,
  skip-based suppression, daily cap, 7-day cap
- Skip count >= 2 moves to PAUSED
- 7 days without being mentioned (child-initiated or recall-accepted) = fade out
- New companion retires old active/paused ones
- Recall-after-accept updates existing companion, does not create new
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.domain.companion_object import (
    EXCITING_TYPES,
    FORBIDDEN_SUMMARY_MARKERS,
    LIGHT_LOCATIONS,
    SAFE_SUMMARY_MAX_LENGTH,
    CompanionObject,
    CompanionObjectCreateRequest,
    CompanionObjectSource,
    CompanionObjectStatus,
    CompanionObjectType,
    CompanionObjectUpdateRequest,
)
from app.repositories.companion_object_repository import (
    CompanionObjectRepository,
    CompanionObjectRepositoryUnavailable,
    InMemoryCompanionObjectRepository,
    get_companion_object_repository,
)

logger = logging.getLogger("app.companion_object_service")

FADE_OUT_DAYS = 7
MAX_RECALL_PER_7_DAYS = 2


class CompanionObjectServiceError(RuntimeError):
    pass


class CompanionObjectNotFoundError(CompanionObjectServiceError):
    pass


class ForbiddenContentError(CompanionObjectServiceError):
    pass


class InvalidLocationError(CompanionObjectServiceError):
    pass


class SessionRecallTracker:
    """v0.1: Process-memory session recall suppression.

    Limitation: lost on service restart. Acceptable for MVP (K05).
    """

    def __init__(self) -> None:
        self._recalled: dict[str, set[str]] = defaultdict(set)

    def mark_recalled(self, session_id: str, child_id: str) -> None:
        self._recalled[session_id].add(child_id)

    def has_recalled(self, session_id: str, child_id: str) -> bool:
        return child_id in self._recalled.get(session_id, set())

    def clear_session(self, session_id: str) -> None:
        self._recalled.pop(session_id, None)


@dataclass(frozen=True)
class PendingCompanionSeed:
    child_id: str
    object_type: CompanionObjectType
    light_location: str
    source_type: CompanionObjectSource
    requested_at: datetime


class CompanionObjectService:
    def __init__(
        self,
        *,
        repository: CompanionObjectRepository | None = None,
        fallback_repository: InMemoryCompanionObjectRepository | None = None,
        session_tracker: SessionRecallTracker | None = None,
        now_provider: Callable[[], datetime] | None = None,
        fallback_to_memory: bool = True,
    ) -> None:
        self._repository = repository or get_companion_object_repository()
        self._fallback_repository = fallback_repository or InMemoryCompanionObjectRepository()
        self._session_tracker = session_tracker or SessionRecallTracker()
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))
        self._fallback_to_memory = fallback_to_memory
        self._pending_seed_naming: dict[str, PendingCompanionSeed] = {}

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(self, request: CompanionObjectCreateRequest) -> CompanionObject:
        self._validate_safe_summary(request.safe_summary)
        self._validate_location(request.light_location)

        now = self._now()

        # Retire existing active/paused companions
        existing = self._get_active_or_paused_by_child(request.child_id)
        if existing is not None:
            retired = existing.model_copy(
                update={"status": CompanionObjectStatus.RETIRED, "updated_at": now},
                deep=True,
            )
            self._save(retired)

        companion = CompanionObject(
            id=str(uuid4()),
            child_id=request.child_id,
            name=request.name.strip(),
            object_type=request.object_type,
            source_type=request.source_type,
            safe_summary=request.safe_summary.strip()[:SAFE_SUMMARY_MAX_LENGTH],
            light_location=request.light_location,
            status=CompanionObjectStatus.ACTIVE,
            last_recalled_at=None,
            recall_count=0,
            skip_count=0,
            created_at=now,
            updated_at=now,
        )
        return self._save(companion)

    def begin_seed_naming(
        self,
        *,
        session_id: str,
        child_id: str,
        object_type: CompanionObjectType = CompanionObjectType.STAR,
        light_location: str = "窗边",
        source_type: CompanionObjectSource = CompanionObjectSource.FIRST_OPEN,
    ) -> None:
        self._validate_location(light_location)
        self._pending_seed_naming[session_id] = PendingCompanionSeed(
            child_id=child_id,
            object_type=object_type,
            light_location=light_location,
            source_type=source_type,
            requested_at=self._now(),
        )

    def get_pending_seed_naming(
        self,
        *,
        session_id: str,
        child_id: str,
    ) -> PendingCompanionSeed | None:
        pending = self._pending_seed_naming.get(session_id)
        if pending is None or pending.child_id != child_id:
            return None
        return pending

    def clear_pending_seed_naming(self, *, session_id: str) -> None:
        self._pending_seed_naming.pop(session_id, None)

    # ------------------------------------------------------------------
    # Recall
    # ------------------------------------------------------------------

    def can_recall(
        self,
        child_id: str,
        *,
        session_id: str,
        is_bedtime: bool = False,
    ) -> CompanionObject | None:
        """Return companion if recall is allowed, else None.

        v0.1: bedtime = no recall for any companion.
        """
        if is_bedtime:
            return None

        companion = self._get_active_by_child(child_id)
        if companion is None:
            return None

        # Same-session suppression (covers both recall and skip within session)
        if self._session_tracker.has_recalled(session_id, child_id):
            return None

        now = self._now()

        # Daily cap
        if companion.last_recalled_at and self._is_same_day(
            companion.last_recalled_at, now
        ):
            return None

        # 7-day cap
        if companion.recall_count >= MAX_RECALL_PER_7_DAYS:
            if companion.last_recalled_at and (now - companion.last_recalled_at) < timedelta(days=FADE_OUT_DAYS):
                return None

        return companion

    def mark_recalled(
        self, companion_id: str, *, session_id: str
    ) -> CompanionObject:
        """Record that a companion was recalled in this session."""
        companion = self._get(companion_id)
        if companion is None:
            raise CompanionObjectNotFoundError(
                f"Companion {companion_id} not found"
            )
        now = self._now()
        updated = companion.model_copy(
            update={
                "last_recalled_at": now,
                "recall_count": companion.recall_count + 1,
                "updated_at": now,
            },
            deep=True,
        )
        self._session_tracker.mark_recalled(session_id, companion.child_id)
        return self._save(updated)

    # ------------------------------------------------------------------
    # Skip
    # ------------------------------------------------------------------

    def mark_skipped(self, companion_id: str, *, session_id: str | None = None) -> CompanionObject:
        """Record a skip. If skip_count >= 2, move to PAUSED.

        If session_id is provided, marks the session as having handled this
        companion (via SessionRecallTracker) so can_recall() won't suggest
        it again this session.
        """
        companion = self._get(companion_id)
        if companion is None:
            raise CompanionObjectNotFoundError(
                f"Companion {companion_id} not found"
            )
        now = self._now()
        new_skip = companion.skip_count + 1
        new_status = (
            CompanionObjectStatus.PAUSED
            if new_skip >= 2
            else companion.status
        )
        updated = companion.model_copy(
            update={
                "skip_count": new_skip,
                "status": new_status,
                "updated_at": now,
            },
            deep=True,
        )
        if session_id is not None:
            self._session_tracker.mark_recalled(session_id, companion.child_id)
        return self._save(updated)

    # ------------------------------------------------------------------
    # Update (recall-accept continuation)
    # ------------------------------------------------------------------

    def update(
        self, companion_id: str, request: CompanionObjectUpdateRequest
    ) -> CompanionObject:
        companion = self._get(companion_id)
        if companion is None:
            raise CompanionObjectNotFoundError(
                f"Companion {companion_id} not found"
            )
        if request.safe_summary is not None:
            self._validate_safe_summary(request.safe_summary)
        if request.light_location is not None:
            self._validate_location(request.light_location)

        now = self._now()
        updates: dict[str, object] = {"updated_at": now}
        if request.safe_summary is not None:
            updates["safe_summary"] = request.safe_summary.strip()[
                :SAFE_SUMMARY_MAX_LENGTH
            ]
        if request.light_location is not None:
            updates["light_location"] = request.light_location
        updated = companion.model_copy(update=updates, deep=True)
        return self._save(updated)

    # ------------------------------------------------------------------
    # Unpause (child-initiated)
    # ------------------------------------------------------------------

    def unpause(self, companion_id: str) -> CompanionObject:
        """Move PAUSED companion back to ACTIVE (child-initiated only)."""
        companion = self._get(companion_id)
        if companion is None:
            raise CompanionObjectNotFoundError(
                f"Companion {companion_id} not found"
            )
        if companion.status != CompanionObjectStatus.PAUSED:
            return companion
        now = self._now()
        updated = companion.model_copy(
            update={
                "status": CompanionObjectStatus.ACTIVE,
                "skip_count": 0,
                "updated_at": now,
            },
            deep=True,
        )
        return self._save(updated)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_active_by_child(self, child_id: str) -> CompanionObject | None:
        return self._get_active_by_child(child_id)

    def get_by_id(self, companion_id: str) -> CompanionObject | None:
        return self._get(companion_id)

    def is_faded_out(self, companion: CompanionObject) -> bool:
        """Check if companion has faded out (7 days without mention)."""
        if companion.status == CompanionObjectStatus.ACTIVE:
            return False
        if companion.status == CompanionObjectStatus.RETIRED:
            return False
        # PAUSED: fade out after 7 days since last recall or creation
        reference = companion.last_recalled_at or companion.created_at
        return (self._now() - reference) >= timedelta(days=FADE_OUT_DAYS)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_safe_summary(self, summary: str) -> None:
        normalized = summary.replace(" ", "").replace("\n", "")
        for marker in FORBIDDEN_SUMMARY_MARKERS:
            if marker in normalized:
                raise ForbiddenContentError(
                    f"safe_summary contains forbidden marker: {marker}"
                )

    def _validate_location(self, location: str) -> None:
        if location not in LIGHT_LOCATIONS:
            raise InvalidLocationError(
                f"light_location must be one of {LIGHT_LOCATIONS}, got: {location}"
            )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _now(self) -> datetime:
        now = self._now_provider()
        if now.tzinfo is None:
            return now.replace(tzinfo=timezone.utc)
        return now

    def _is_same_day(self, dt1: datetime, dt2: datetime) -> bool:
        return dt1.date() == dt2.date()

    def _save(self, companion: CompanionObject) -> CompanionObject:
        try:
            return self._repository.save(companion)
        except (CompanionObjectRepositoryUnavailable, Exception) as exc:
            logger.warning(
                "companion_repository_fallback",
                extra={
                    "event": "companion_repository_fallback",
                    "operation": "save",
                    "error_type": exc.__class__.__name__,
                },
            )
            if not self._fallback_to_memory:
                raise
            return self._fallback_repository.save(companion)

    def _get(self, companion_id: str) -> CompanionObject | None:
        try:
            return self._repository.get(companion_id)
        except (CompanionObjectRepositoryUnavailable, Exception) as exc:
            logger.warning(
                "companion_repository_fallback",
                extra={
                    "event": "companion_repository_fallback",
                    "operation": "get",
                    "error_type": exc.__class__.__name__,
                },
            )
            if not self._fallback_to_memory:
                raise
            return self._fallback_repository.get(companion_id)

    def _get_active_by_child(self, child_id: str) -> CompanionObject | None:
        try:
            return self._repository.get_active_by_child(child_id)
        except (CompanionObjectRepositoryUnavailable, Exception) as exc:
            logger.warning(
                "companion_repository_fallback",
                extra={
                    "event": "companion_repository_fallback",
                    "operation": "get_active_by_child",
                    "error_type": exc.__class__.__name__,
                },
            )
            if not self._fallback_to_memory:
                raise
            return self._fallback_repository.get_active_by_child(child_id)

    def _get_active_or_paused_by_child(
        self, child_id: str
    ) -> CompanionObject | None:
        try:
            items = self._repository.list_by_child(child_id)
        except (CompanionObjectRepositoryUnavailable, Exception) as exc:
            logger.warning(
                "companion_repository_fallback",
                extra={
                    "event": "companion_repository_fallback",
                    "operation": "list_by_child",
                    "error_type": exc.__class__.__name__,
                },
            )
            if not self._fallback_to_memory:
                raise
            items = self._fallback_repository.list_by_child(child_id)
        for item in items:
            if item.status in (
                CompanionObjectStatus.ACTIVE,
                CompanionObjectStatus.PAUSED,
            ):
                return item
        return None


_companion_service = CompanionObjectService()


def get_companion_object_service() -> CompanionObjectService:
    return _companion_service
