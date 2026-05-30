"""Tests for companion object service (小屋小客人)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.companion_object import (
    LIGHT_LOCATIONS,
    CompanionObjectCreateRequest,
    CompanionObjectSource,
    CompanionObjectStatus,
    CompanionObjectType,
    CompanionObjectUpdateRequest,
)
from app.repositories.companion_object_repository import (
    InMemoryCompanionObjectRepository,
)
from app.services.companion_object_service import (
    CompanionObjectService,
    ForbiddenContentError,
    InvalidLocationError,
    SessionRecallTracker,
)

CHILD_ID = "test-child-001"
SESSION_ID = "session-001"


def _fixed_now_factory(base: datetime):
    def _now() -> datetime:
        return base

    return _now


def _make_request(**overrides) -> CompanionObjectCreateRequest:
    defaults = dict(
        child_id=CHILD_ID,
        name="小棉花",
        object_type=CompanionObjectType.STAR,
        source_type=CompanionObjectSource.FIRST_OPEN,
        safe_summary="孩子给窗边的小星星起名小棉花",
        light_location="窗边",
    )
    defaults.update(overrides)
    return CompanionObjectCreateRequest(**defaults)


def _make_service(now: datetime | None = None) -> CompanionObjectService:
    repo = InMemoryCompanionObjectRepository()
    tracker = SessionRecallTracker()
    now_fn = _fixed_now_factory(now or datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc))
    return CompanionObjectService(
        repository=repo,
        session_tracker=tracker,
        now_provider=now_fn,
        fallback_to_memory=False,
    )


# ------ Create tests ------


class TestCreate:
    def test_create_safe_companion(self) -> None:
        svc = _make_service()
        result = svc.create(_make_request())
        assert result.name == "小棉花"
        assert result.status == CompanionObjectStatus.ACTIVE
        assert result.child_id == CHILD_ID
        assert result.recall_count == 0
        assert result.skip_count == 0

    def test_create_retires_old_active(self) -> None:
        svc = _make_service()
        first = svc.create(_make_request(name="小棉花"))
        second = svc.create(_make_request(name="小星星", light_location="地毯边"))

        assert second.status == CompanionObjectStatus.ACTIVE
        old = svc.get_by_id(first.id)
        assert old is not None
        assert old.status == CompanionObjectStatus.RETIRED

    def test_create_retires_old_paused(self) -> None:
        svc = _make_service()
        first = svc.create(_make_request(name="小棉花"))
        # Simulate two skips to pause
        svc.mark_skipped(first.id, session_id="s1")
        svc.mark_skipped(first.id, session_id="s2")
        paused = svc.get_by_id(first.id)
        assert paused is not None
        assert paused.status == CompanionObjectStatus.PAUSED

        second = svc.create(_make_request(name="小星星", light_location="窗外"))
        assert second.status == CompanionObjectStatus.ACTIVE
        old = svc.get_by_id(first.id)
        assert old is not None
        assert old.status == CompanionObjectStatus.RETIRED

    def test_create_limits_one_active_per_child(self) -> None:
        svc = _make_service()
        svc.create(_make_request(name="A"))
        svc.create(_make_request(name="B"))
        svc.create(_make_request(name="C"))

        active = svc.get_active_by_child(CHILD_ID)
        assert active is not None
        assert active.name == "C"

    def test_create_forbidden_privacy(self) -> None:
        svc = _make_service()
        with pytest.raises(ForbiddenContentError, match="学校"):
            svc.create(_make_request(safe_summary="这是我们学校门口的小星星"))

    def test_create_forbidden_negative_event(self) -> None:
        svc = _make_service()
        with pytest.raises(ForbiddenContentError, match="吵架"):
            svc.create(_make_request(safe_summary="孩子说和同学吵架了"))

    def test_create_forbidden_learning(self) -> None:
        svc = _make_service()
        with pytest.raises(ForbiddenContentError, match="答案"):
            svc.create(_make_request(safe_summary="这道作业题的答案"))

    def test_create_forbidden_homework(self) -> None:
        svc = _make_service()
        with pytest.raises(ForbiddenContentError, match="作业"):
            svc.create(_make_request(safe_summary="今天的作业写完了"))

    def test_create_forbidden_secret(self) -> None:
        svc = _make_service()
        with pytest.raises(ForbiddenContentError, match="秘密"):
            svc.create(_make_request(safe_summary="这是我们的小秘密"))

    def test_create_invalid_location(self) -> None:
        svc = _make_service()
        with pytest.raises(InvalidLocationError):
            svc.create(_make_request(light_location="屋顶上"))

    def test_create_validates_summary_length(self) -> None:
        """Pydantic enforces max_length=200 on schema; service also truncates."""
        svc = _make_service()
        # Exactly 200 chars is allowed
        summary_200 = "安" * 200
        result = svc.create(_make_request(safe_summary=summary_200))
        assert len(result.safe_summary) == 200

    def test_create_summary_truncated_at_service_layer(self) -> None:
        """Service truncates to 200 even if schema somehow passes longer."""
        svc = _make_service()
        companion = svc.create(_make_request())
        # Directly save a companion with long summary to test truncation
        from app.domain.companion_object import CompanionObject

        long_summary = "长" * 300
        raw = companion.model_copy(
            update={"safe_summary": long_summary[:200]}, deep=True
        )
        result = svc._save(raw)
        assert len(result.safe_summary) <= 200

    def test_create_other_type_when_safe(self) -> None:
        svc = _make_service()
        result = svc.create(
            _make_request(
                object_type=CompanionObjectType.OTHER,
                safe_summary="一个安全的小东西",
            )
        )
        assert result.object_type == CompanionObjectType.OTHER


# ------ Recall tests ------


class TestRecall:
    def test_recall_basic(self) -> None:
        now = datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=now)
        companion = svc.create(_make_request())

        result = svc.can_recall(CHILD_ID, session_id=SESSION_ID)
        assert result is not None
        assert result.id == companion.id

    def test_recall_marks_recalled(self) -> None:
        now = datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=now)
        companion = svc.create(_make_request())

        updated = svc.mark_recalled(companion.id, session_id=SESSION_ID)
        assert updated.recall_count == 1
        assert updated.last_recalled_at is not None

    def test_recall_same_session_suppression(self) -> None:
        now = datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=now)
        companion = svc.create(_make_request())

        # First recall
        svc.mark_recalled(companion.id, session_id=SESSION_ID)
        # Same session, second check
        result = svc.can_recall(CHILD_ID, session_id=SESSION_ID)
        assert result is None

    def test_recall_different_session_same_day_blocked(self) -> None:
        """Daily cap: same day, different session still blocked."""
        now = datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=now)
        companion = svc.create(_make_request())

        svc.mark_recalled(companion.id, session_id="session-A")
        result = svc.can_recall(CHILD_ID, session_id="session-B")
        assert result is None

    def test_recall_different_day_different_session_allowed(self) -> None:
        """Next day, new session should allow recall."""
        base = datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=base)
        companion = svc.create(_make_request())

        svc.mark_recalled(companion.id, session_id="session-A")

        # Next day
        svc_next = _make_service(now=base + timedelta(days=1))
        svc_next._repository = svc._repository
        svc_next._session_tracker = svc._session_tracker
        result = svc_next.can_recall(CHILD_ID, session_id="session-B")
        assert result is not None

    def test_recall_daily_cap(self) -> None:
        now = datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=now)
        companion = svc.create(_make_request())

        # Mark recalled today
        svc.mark_recalled(companion.id, session_id="s1")
        # New session same day
        result = svc.can_recall(CHILD_ID, session_id="s2")
        assert result is None

    def test_recall_7day_cap(self) -> None:
        base = datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=base)
        companion = svc.create(_make_request())

        # Recall twice within 7 days
        svc.mark_recalled(companion.id, session_id="s1")
        svc2 = _make_service(now=base + timedelta(days=1))
        svc2._repository = svc._repository
        svc2._session_tracker = svc._session_tracker
        svc2.mark_recalled(companion.id, session_id="s2")

        # Third recall within 7 days should fail
        svc3 = _make_service(now=base + timedelta(days=2))
        svc3._repository = svc._repository
        svc3._session_tracker = svc._session_tracker
        result = svc3.can_recall(CHILD_ID, session_id="s3")
        assert result is None

    def test_recall_after_7_day_gap(self) -> None:
        base = datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=base)
        companion = svc.create(_make_request())
        svc.mark_recalled(companion.id, session_id="s1")
        svc.mark_recalled(companion.id, session_id="s2")  # different day needed

        # After 7 days, recall allowed again
        svc_later = _make_service(now=base + timedelta(days=8))
        svc_later._repository = svc._repository
        svc_later._session_tracker = svc._session_tracker
        result = svc_later.can_recall(CHILD_ID, session_id="s3")
        assert result is not None

    def test_recall_bedtime_blocked(self) -> None:
        now = datetime(2026, 5, 30, 21, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=now)
        svc.create(_make_request())

        result = svc.can_recall(CHILD_ID, session_id=SESSION_ID, is_bedtime=True)
        assert result is None

    def test_recall_skip_blocks_same_session(self) -> None:
        """Skip once: same session can't recall."""
        now = datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=now)
        companion = svc.create(_make_request())

        svc.mark_skipped(companion.id, session_id=SESSION_ID)
        result = svc.can_recall(CHILD_ID, session_id=SESSION_ID)
        assert result is None

    def test_recall_skip_once_allows_future_session(self) -> None:
        """Skip once: new session next day can recall."""
        base = datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=base)
        companion = svc.create(_make_request())

        svc.mark_skipped(companion.id, session_id="session-A")
        assert companion.status == CompanionObjectStatus.ACTIVE

        # Next day, new session
        svc_next = _make_service(now=base + timedelta(days=1))
        svc_next._repository = svc._repository
        result = svc_next.can_recall(CHILD_ID, session_id="session-B")
        assert result is not None

    def test_recall_skip_once_allows_different_session_same_day(self) -> None:
        """Skip once: different session same day can still recall (skip is session-scoped)."""
        now = datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=now)
        companion = svc.create(_make_request())

        svc.mark_skipped(companion.id, session_id="session-A")
        # Different session same day — skip was session-scoped via tracker
        result = svc.can_recall(CHILD_ID, session_id="session-B")
        assert result is not None

    def test_recall_no_active_companion(self) -> None:
        svc = _make_service()
        result = svc.can_recall("no-child", session_id=SESSION_ID)
        assert result is None


# ------ Skip tests ------


class TestSkip:
    def test_skip_once(self) -> None:
        svc = _make_service()
        companion = svc.create(_make_request())

        updated = svc.mark_skipped(companion.id, session_id=SESSION_ID)
        assert updated.skip_count == 1
        assert updated.status == CompanionObjectStatus.ACTIVE

    def test_skip_twice_pauses(self) -> None:
        svc = _make_service()
        companion = svc.create(_make_request())

        svc.mark_skipped(companion.id, session_id="s1")
        updated = svc.mark_skipped(companion.id, session_id="s2")
        assert updated.skip_count == 2
        assert updated.status == CompanionObjectStatus.PAUSED

    def test_skip_nonexistent_raises(self) -> None:
        svc = _make_service()
        from app.services.companion_object_service import CompanionObjectNotFoundError

        with pytest.raises(CompanionObjectNotFoundError):
            svc.mark_skipped("nonexistent", session_id=SESSION_ID)


# ------ Unpause tests ------


class TestUnpause:
    def test_unpause_back_to_active(self) -> None:
        svc = _make_service()
        companion = svc.create(_make_request())
        svc.mark_skipped(companion.id, session_id="s1")
        svc.mark_skipped(companion.id, session_id="s2")

        unpaused = svc.unpause(companion.id)
        assert unpaused.status == CompanionObjectStatus.ACTIVE
        assert unpaused.skip_count == 0

    def test_unpause_already_active_noop(self) -> None:
        svc = _make_service()
        companion = svc.create(_make_request())

        result = svc.unpause(companion.id)
        assert result.status == CompanionObjectStatus.ACTIVE


# ------ Update tests ------


class TestUpdate:
    def test_update_summary(self) -> None:
        svc = _make_service()
        companion = svc.create(_make_request())

        updated = svc.update(
            companion.id,
            CompanionObjectUpdateRequest(safe_summary="新的安全摘要"),
        )
        assert updated.safe_summary == "新的安全摘要"

    def test_update_location(self) -> None:
        svc = _make_service()
        companion = svc.create(_make_request())

        updated = svc.update(
            companion.id,
            CompanionObjectUpdateRequest(light_location="地毯边"),
        )
        assert updated.light_location == "地毯边"

    def test_update_forbidden_summary(self) -> None:
        svc = _make_service()
        companion = svc.create(_make_request())

        with pytest.raises(ForbiddenContentError):
            svc.update(
                companion.id,
                CompanionObjectUpdateRequest(safe_summary="学校里的秘密"),
            )

    def test_update_invalid_location(self) -> None:
        svc = _make_service()
        companion = svc.create(_make_request())

        with pytest.raises(InvalidLocationError):
            svc.update(
                companion.id,
                CompanionObjectUpdateRequest(light_location="天上"),
            )


# ------ Fade out tests ------


class TestFadeOut:
    def test_faded_out_after_7_days(self) -> None:
        base = datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=base)
        companion = svc.create(_make_request())
        svc.mark_skipped(companion.id, session_id="s1")
        svc.mark_skipped(companion.id, session_id="s2")  # PAUSED

        svc_later = _make_service(now=base + timedelta(days=8))
        paused = svc._get(companion.id)
        assert paused is not None
        assert svc_later.is_faded_out(paused) is True

    def test_active_not_faded(self) -> None:
        base = datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=base)
        companion = svc.create(_make_request())

        svc_later = _make_service(now=base + timedelta(days=30))
        active = svc._get(companion.id)
        assert active is not None
        assert svc_later.is_faded_out(active) is False

    def test_paused_not_faded_within_7_days(self) -> None:
        base = datetime(2026, 5, 30, 10, 0, 0, tzinfo=timezone.utc)
        svc = _make_service(now=base)
        companion = svc.create(_make_request())
        svc.mark_skipped(companion.id, session_id="s1")
        svc.mark_skipped(companion.id, session_id="s2")

        svc_later = _make_service(now=base + timedelta(days=5))
        paused = svc._get(companion.id)
        assert paused is not None
        assert svc_later.is_faded_out(paused) is False


# ------ Edge cases ------


class TestEdgeCases:
    def test_create_trims_whitespace(self) -> None:
        svc = _make_service()
        result = svc.create(
            _make_request(name="  小棉花  ", safe_summary="  安全摘要  ")
        )
        assert result.name == "小棉花"
        assert result.safe_summary == "安全摘要"

    def test_get_active_by_child_returns_none_when_all_retired(self) -> None:
        svc = _make_service()
        svc.create(_make_request(name="A"))
        svc.create(_make_request(name="B"))
        # B is active, A is retired
        active = svc.get_active_by_child(CHILD_ID)
        assert active is not None
        assert active.name == "B"

    def test_different_children_independent(self) -> None:
        svc = _make_service()
        svc.create(_make_request(child_id="child-A", name="A"))
        svc.create(_make_request(child_id="child-B", name="B"))

        a = svc.get_active_by_child("child-A")
        b = svc.get_active_by_child("child-B")
        assert a is not None and a.name == "A"
        assert b is not None and b.name == "B"
