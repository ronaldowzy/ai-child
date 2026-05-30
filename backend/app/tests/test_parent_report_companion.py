"""Tests for parent report companion_summary integration."""

from datetime import date, datetime, timezone

from app.domain.companion_object import (
    CompanionObject,
    CompanionObjectSource,
    CompanionObjectStatus,
    CompanionObjectType,
)
from app.domain.memory import (
    MemoryCreateRequest,
    MemoryEvidence,
    MemorySensitivity,
    MemoryType,
)
from app.domain.model_types import ModelResponse, ModelTaskType
from app.domain.parent_report import ParentReportGenerationStatus
from app.repositories.conversation_persistence_repository import ConversationReportMessage
from app.repositories.memory_repository import InMemoryMemoryRepository
from app.services.memory_service import MemoryService
from app.services.parent_report_language_v4 import companion_deterministic_summary
from app.services.parent_report_service import ParentReportService


def _fixed_now() -> datetime:
    return datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc)


def _today() -> date:
    return date(2026, 5, 18)


class FakeCompanionObjectService:
    def __init__(self, companion: CompanionObject | None = None) -> None:
        self._companion = companion

    def get_active_by_child(self, child_id: str) -> CompanionObject | None:
        return self._companion


class FakeConversationRepository:
    def __init__(
        self,
        messages: list[ConversationReportMessage] | None = None,
    ) -> None:
        self.messages = messages or []

    def list_report_messages(
        self,
        *,
        child_id: str,
        report_date: date,
    ) -> list[ConversationReportMessage]:
        return [
            message
            for message in self.messages
            if message.created_at.date() == report_date
        ]


class DeterministicModelRegistry:
    """Returns a model response that triggers deterministic fallback."""

    def generate(self, request):
        return ModelResponse(
            task_type=ModelTaskType.PARENT_REPORT,
            response_text="",
            structured_output={},
            provider_name="mock",
            model_name="mock",
            metadata={"mock": True},
        )


def _make_companion(
    *,
    source_type: CompanionObjectSource = CompanionObjectSource.FIRST_OPEN,
    status: CompanionObjectStatus = CompanionObjectStatus.ACTIVE,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> CompanionObject:
    now = created_at or datetime(2026, 5, 18, 9, 0, tzinfo=timezone.utc)
    return CompanionObject(
        id="comp_test_001",
        child_id="child_companion_test",
        name="小棉花",
        object_type=CompanionObjectType.STAR,
        source_type=source_type,
        safe_summary="一颗小星星",
        light_location="窗边",
        status=status,
        recall_count=0,
        skip_count=0,
        last_recalled_at=None,
        created_at=now,
        updated_at=updated_at or now,
    )


def _make_memory_service_with_child_message() -> MemoryService:
    repo = InMemoryMemoryRepository()
    service = MemoryService(repository=repo, now_provider=_fixed_now)
    service.create(
        MemoryCreateRequest(
            child_id="child_companion_test",
            memory_type=MemoryType.INTEREST,
            content="孩子今天聊了小星星",
            tags=["星星"],
            evidence=[
                MemoryEvidence(
                    source="chat_summary",
                    session_id="session_test",
                    quote_summary="结构化摘要",
                )
            ],
            confidence=0.8,
            importance=0.5,
            sensitivity=MemorySensitivity.LOW,
            visible_to_parent=True,
            visible_to_child=False,
        )
    )
    return service


def _build_service(
    companion: CompanionObject | None = None,
    messages: list[ConversationReportMessage] | None = None,
) -> ParentReportService:
    memory_service = _make_memory_service_with_child_message()
    companion_service = FakeCompanionObjectService(companion)
    return ParentReportService(
        memory_service=memory_service,
        conversation_repository=FakeConversationRepository(messages),
        model_registry=DeterministicModelRegistry(),
        companion_object_service=companion_service,
        now_provider=_fixed_now,
    )


# --- companion_deterministic_summary unit tests ---


def test_deterministic_summary_first_open():
    result = companion_deterministic_summary(
        has_companion=True, source_type="first_open"
    )
    assert result == "今天孩子和小白狐有一次轻松共创。"


def test_deterministic_summary_star_seed():
    result = companion_deterministic_summary(
        has_companion=True, source_type="star_seed"
    )
    assert result == "今天孩子和小白狐有一次轻松共创。"


def test_deterministic_summary_image_share():
    result = companion_deterministic_summary(
        has_companion=True, source_type="image_share"
    )
    assert result == "孩子主动分享了一张作品。"


def test_deterministic_summary_chat_story():
    result = companion_deterministic_summary(
        has_companion=True, source_type="chat_story"
    )
    assert result == "今天孩子和小白狐接了一点小故事。"


def test_deterministic_summary_story_chain():
    result = companion_deterministic_summary(
        has_companion=True, source_type="story_chain"
    )
    assert result == "今天孩子和小白狐接了一点小故事。"


def test_deterministic_summary_no_companion():
    result = companion_deterministic_summary(
        has_companion=False, source_type=""
    )
    assert result is None


# --- ParentReportService integration tests ---


def test_report_with_active_companion_first_open():
    companion = _make_companion(source_type=CompanionObjectSource.FIRST_OPEN)
    service = _build_service(companion=companion)
    report = service.get_daily_report("child_companion_test", report_date=_today())
    assert report.companion_summary == "今天孩子和小白狐有一次轻松共创。"
    assert report.tonight_parent_bridge == "今晚可以轻轻问一句：你今天给小白狐看了什么呀？"


def test_report_with_active_companion_image_share():
    companion = _make_companion(source_type=CompanionObjectSource.IMAGE_SHARE)
    service = _build_service(companion=companion)
    report = service.get_daily_report("child_companion_test", report_date=_today())
    assert report.companion_summary == "孩子主动分享了一张作品。"


def test_report_with_active_companion_story_chain():
    companion = _make_companion(source_type=CompanionObjectSource.STORY_CHAIN)
    service = _build_service(companion=companion)
    report = service.get_daily_report("child_companion_test", report_date=_today())
    assert report.companion_summary == "今天孩子和小白狐接了一点小故事。"


def test_report_without_companion():
    service = _build_service(companion=None)
    report = service.get_daily_report("child_companion_test", report_date=_today())
    assert report.companion_summary is None


def test_report_with_paused_companion_not_shown():
    companion = _make_companion(status=CompanionObjectStatus.PAUSED)
    service = _build_service(companion=companion)
    report = service.get_daily_report("child_companion_test", report_date=_today())
    assert report.companion_summary is None


def test_report_with_companion_created_different_date():
    companion = _make_companion(
        created_at=datetime(2026, 5, 17, 9, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 17, 9, 0, tzinfo=timezone.utc),
    )
    service = _build_service(companion=companion)
    report = service.get_daily_report("child_companion_test", report_date=_today())
    assert report.companion_summary is None


def test_companion_summary_does_not_contain_name():
    companion = _make_companion()
    service = _build_service(companion=companion)
    report = service.get_daily_report("child_companion_test", report_date=_today())
    assert report.companion_summary is not None
    assert "小棉花" not in report.companion_summary


def test_companion_summary_does_not_contain_type():
    companion = _make_companion()
    service = _build_service(companion=companion)
    report = service.get_daily_report("child_companion_test", report_date=_today())
    assert report.companion_summary is not None
    assert "小星星" not in report.companion_summary
    assert "STAR" not in report.companion_summary


def test_companion_summary_does_not_contain_location():
    companion = _make_companion()
    service = _build_service(companion=companion)
    report = service.get_daily_report("child_companion_test", report_date=_today())
    assert report.companion_summary is not None
    assert "窗边" not in report.companion_summary


def test_companion_summary_does_not_contain_counts():
    companion = _make_companion()
    service = _build_service(companion=companion)
    report = service.get_daily_report("child_companion_test", report_date=_today())
    assert report.companion_summary is not None
    assert "召回" not in report.companion_summary
    assert "跳过" not in report.companion_summary


def test_companion_signal_in_model_payload():
    """Verify companion_hints appears in model payload when companion exists."""
    companion = _make_companion(source_type=CompanionObjectSource.IMAGE_SHARE)

    class CapturingModelRegistry:
        def __init__(self):
            self.payload = None

        def generate(self, request):
            content = request.messages[-1].content
            import json
            self.payload = json.loads(content)
            return ModelResponse(
                task_type=ModelTaskType.PARENT_REPORT,
                response_text="",
                structured_output={},
                provider_name="mock",
                model_name="mock",
                metadata={"mock": True},
            )

    memory_service = _make_memory_service_with_child_message()
    companion_service = FakeCompanionObjectService(companion)
    model_registry = CapturingModelRegistry()
    service = ParentReportService(
        memory_service=memory_service,
        conversation_repository=FakeConversationRepository(),
        model_registry=model_registry,
        companion_object_service=companion_service,
        now_provider=_fixed_now,
    )
    service.get_daily_report("child_companion_test", report_date=_today())
    assert model_registry.payload is not None
    hints = model_registry.payload.get("companion_hints")
    assert hints is not None
    assert hints["had_light_cocreation"] is True
    assert hints["cocreation_kind"] == "image_share"


def test_no_companion_signal_in_model_payload_when_absent():
    """Verify no companion_hints when no companion exists."""

    class CapturingModelRegistry:
        def __init__(self):
            self.payload = None

        def generate(self, request):
            content = request.messages[-1].content
            import json
            self.payload = json.loads(content)
            return ModelResponse(
                task_type=ModelTaskType.PARENT_REPORT,
                response_text="",
                structured_output={},
                provider_name="mock",
                model_name="mock",
                metadata={"mock": True},
            )

    memory_service = _make_memory_service_with_child_message()
    model_registry = CapturingModelRegistry()
    service = ParentReportService(
        memory_service=memory_service,
        conversation_repository=FakeConversationRepository(),
        model_registry=model_registry,
        companion_object_service=FakeCompanionObjectService(None),
        now_provider=_fixed_now,
    )
    service.get_daily_report("child_companion_test", report_date=_today())
    assert model_registry.payload is not None
    assert "companion_hints" not in model_registry.payload


def test_companion_in_fingerprint_changes_staleness():
    """Verify companion signal affects material fingerprint."""
    from hashlib import sha256
    import json as json_mod

    companion = _make_companion()
    service_with = _build_service(companion=companion)
    service_without = _build_service(companion=None)

    fp_with = service_with._material_fingerprint(memories=[], conversation_messages=[], companion_signal={"has_companion": True, "source_type": "first_open"})
    fp_without = service_without._material_fingerprint(memories=[], conversation_messages=[], companion_signal={"has_companion": False, "source_type": ""})
    assert fp_with != fp_without
