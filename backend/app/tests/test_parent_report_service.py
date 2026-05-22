from datetime import date, datetime, timezone

from app.domain.memory import (
    MemoryCreateRequest,
    MemoryEvidence,
    MemorySensitivity,
    MemoryType,
)
from app.repositories.memory_repository import InMemoryMemoryRepository
from app.repositories.conversation_persistence_repository import ConversationReportMessage
from app.repositories.parent_report_repository import (
    InMemoryParentReportRepository,
    ParentReportRepositoryUnavailable,
)
from app.services.memory_service import MemoryService
from app.services.parent_report_service import ParentReportService


def _fixed_now() -> datetime:
    return datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc)


def _memory_request(
    *,
    child_id: str = "child_parent_report_service_test",
    memory_type: MemoryType,
    content: str,
    tags: list[str],
    sensitivity: MemorySensitivity = MemorySensitivity.LOW,
    requires_parent_attention: bool = False,
) -> MemoryCreateRequest:
    return MemoryCreateRequest(
        child_id=child_id,
        memory_type=memory_type,
        content=content,
        tags=tags,
        evidence=[
            MemoryEvidence(
                source="chat_summary",
                session_id="session_parent_report_service_test",
                quote_summary="这里是结构化摘要来源，不应在父亲日报中逐字返回。",
            )
        ],
        confidence=0.82,
        importance=0.7,
        sensitivity=sensitivity,
        visible_to_parent=True,
        visible_to_child=False,
        requires_parent_attention=requires_parent_attention,
    )


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


def _services() -> tuple[
    InMemoryMemoryRepository,
    MemoryService,
    ParentReportService,
]:
    repository = InMemoryMemoryRepository()
    memory_service = MemoryService(
        repository=repository,
        now_provider=_fixed_now,
    )
    report_service = ParentReportService(
        memory_service=memory_service,
        conversation_repository=FakeConversationRepository(),
        now_provider=_fixed_now,
    )
    return repository, memory_service, report_service


def _services_with_report_repository() -> tuple[
    MemoryService,
    InMemoryParentReportRepository,
    ParentReportService,
]:
    memory_repository = InMemoryMemoryRepository()
    report_repository = InMemoryParentReportRepository()
    memory_service = MemoryService(
        repository=memory_repository,
        now_provider=_fixed_now,
    )
    report_service = ParentReportService(
        memory_service=memory_service,
        repository=report_repository,
        conversation_repository=FakeConversationRepository(),
        now_provider=_fixed_now,
    )
    return memory_service, report_repository, report_service


def _conversation_message(
    *,
    message_id: str,
    actor: str = "child",
    text: str | None,
    active_scene: str | None = "conversation.open",
    risk_level: str | None = "none",
    attachments_count: int = 0,
    created_at: datetime = datetime(2026, 5, 18, 10, 30, tzinfo=timezone.utc),
) -> ConversationReportMessage:
    return ConversationReportMessage(
        id=message_id,
        session_id="session_parent_report_service_test",
        actor=actor,
        message_type="text",
        normalized_text=text,
        active_scene=active_scene,
        risk_level=risk_level,
        attachments_count=attachments_count,
        created_at=created_at,
    )


def test_parent_report_service_generates_normal_daily_report() -> None:
    _, memory_service, report_service = _services()
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.LEARNING_PATTERN,
            content="孩子在学习求助时需要先确认题意，再一步一步说出已知条件。",
            tags=["学习求助", "题意确认"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.EXPRESSION_PATTERN,
            content="孩子在开放提问下回答较短，使用选择题式引导时更容易开始表达。",
            tags=["表达", "选择题有效"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.EMOTION_OBSERVATION,
            content="孩子本次表达了低落或紧张情绪，后续适合先接住感受再进入问题解决。",
            tags=["情绪观察", "先共情"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    assert report.child_id == "child_parent_report_service_test"
    assert report.date == date(2026, 5, 18)
    assert "学习支持" in report.summary
    assert report.learning_observations == [
        "孩子在学习求助时需要先确认题意，再一步一步说出已知条件。"
    ]
    assert report.expression_observations == [
        "孩子在开放提问下回答较短，使用选择题式引导时更容易开始表达。"
    ]
    assert report.emotion_observations == [
        "孩子本次表达了低落或紧张情绪，后续适合先接住感受再进入问题解决。"
    ]
    assert report.safety_alerts == []
    assert any("不直接给最终答案" in action for action in report.suggested_parent_actions)
    assert "逐字返回" not in report.model_dump_json()


def test_parent_report_service_get_daily_report_saves_generated_report() -> None:
    memory_service, report_repository, report_service = _services_with_report_repository()
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.LEARNING_PATTERN,
            content="孩子在学习求助时需要先确认题意，再一步一步说出已知条件。",
            tags=["学习求助", "题意确认"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )

    report = report_service.get_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )
    persisted = report_repository.get(
        "child_parent_report_service_test",
        date(2026, 5, 18),
    )

    assert persisted is not None
    assert persisted.summary == report.summary
    assert persisted.learning_observations == report.learning_observations


def test_parent_report_service_uses_daily_conversation_without_raw_transcript() -> None:
    memory_service = MemoryService(
        repository=InMemoryMemoryRepository(),
        now_provider=_fixed_now,
    )
    report_service = ParentReportService(
        memory_service=memory_service,
        conversation_repository=FakeConversationRepository(
            [
                _conversation_message(
                    message_id="msg_child_photo_learning",
                    text="我发了一张家里的照片，里面有数学题不会做。",
                    active_scene="conversation.open",
                    attachments_count=1,
                ),
                _conversation_message(
                    message_id="msg_agent_photo_learning",
                    actor="agent",
                    text="我们先看看你最想问哪里。",
                ),
            ]
        ),
        now_provider=_fixed_now,
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    report_json = report.model_dump_json()
    assert "会话消息" in report.summary
    assert "图片分享" in report.summary
    assert any("复述题意" in item for item in report.learning_observations)
    assert any("图片" in item for item in report.expression_observations)
    assert "我发了一张家里的照片" not in report_json
    assert "数学题不会做" not in report_json


def test_parent_report_service_refreshes_stale_report_when_conversation_is_newer() -> None:
    memory_service, report_repository, _ = _services_with_report_repository()
    old_report_service = ParentReportService(
        memory_service=memory_service,
        repository=report_repository,
        conversation_repository=FakeConversationRepository(),
        now_provider=_fixed_now,
    )
    old_report = old_report_service.get_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )
    report_service = ParentReportService(
        memory_service=memory_service,
        repository=report_repository,
        conversation_repository=FakeConversationRepository(
            [
                _conversation_message(
                    message_id="msg_child_newer_photo",
                    text="我拍了一张图想问问这是什么。",
                    attachments_count=1,
                    created_at=datetime(2026, 5, 18, 11, 0, tzinfo=timezone.utc),
                )
            ]
        ),
        now_provider=lambda: datetime(2026, 5, 18, 11, 5, tzinfo=timezone.utc),
    )

    refreshed = report_service.get_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    assert refreshed.summary != old_report.summary
    assert "会话消息" in refreshed.summary
    assert refreshed.created_at > old_report.created_at


def test_parent_report_service_second_get_returns_persisted_report() -> None:
    memory_service, _, report_service = _services_with_report_repository()
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.LEARNING_PATTERN,
            content="孩子在学习求助时需要先确认题意，再一步一步说出已知条件。",
            tags=["学习求助", "题意确认"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )
    first = report_service.get_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.EXPRESSION_PATTERN,
            content="这条后续记忆不应改变已持久化的当日报告。",
            tags=["表达"],
        )
    )

    second = report_service.get_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    assert second.created_at == first.created_at
    assert second.learning_observations == first.learning_observations
    assert second.expression_observations == first.expression_observations


def test_parent_report_service_repository_failure_returns_generated_report(
    caplog,
) -> None:
    class FailingReportRepository:
        def save(self, _report):
            raise ParentReportRepositoryUnavailable("contains report summary")

        def get(self, _child_id, _report_date):
            raise ParentReportRepositoryUnavailable("contains report summary")

        def list_by_child(self, _child_id, limit=30):
            raise ParentReportRepositoryUnavailable("contains report summary")

        def delete(self, _child_id, _report_date):
            raise ParentReportRepositoryUnavailable("contains report summary")

        def clear(self):
            raise ParentReportRepositoryUnavailable("contains report summary")

    memory_service = MemoryService(
        repository=InMemoryMemoryRepository(),
        now_provider=_fixed_now,
    )
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.LEARNING_PATTERN,
            content="孩子在学习求助时需要先确认题意，再一步一步说出已知条件。",
            tags=["学习求助", "题意确认"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )
    report_service = ParentReportService(
        memory_service=memory_service,
        repository=FailingReportRepository(),
        conversation_repository=FakeConversationRepository(),
        now_provider=_fixed_now,
    )
    caplog.set_level("WARNING", logger="app.parent_report")

    report = report_service.get_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    assert report.learning_observations
    assert "parent_report_repository_fallback" in caplog.text
    assert "孩子在学习求助时需要先确认题意" not in caplog.text
    assert "contains report summary" not in caplog.text


def test_parent_report_service_only_uses_parent_visible_current_day_memory() -> None:
    repository, memory_service, report_service = _services()
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.LEARNING_PATTERN,
            content="今天可见的学习观察。",
            tags=["今天"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.LEARNING_PATTERN,
            content="今天不可见的学习观察。",
            tags=["不可见"],
            sensitivity=MemorySensitivity.MEDIUM,
        ).model_copy(update={"visible_to_parent": False}, deep=True)
    )
    yesterday = memory_service.create(
        _memory_request(
            memory_type=MemoryType.LEARNING_PATTERN,
            content="昨天的学习观察。",
            tags=["昨天"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )
    repository.save(
        yesterday.model_copy(
            update={
                "created_at": datetime(2026, 5, 17, 10, 0, tzinfo=timezone.utc),
                "updated_at": datetime(2026, 5, 17, 10, 0, tzinfo=timezone.utc),
            },
            deep=True,
        )
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    report_json = report.model_dump_json()
    assert "今天可见的学习观察" in report_json
    assert "今天不可见的学习观察" not in report_json
    assert "昨天的学习观察" not in report_json


def test_parent_report_service_generates_high_risk_report_without_raw_detail() -> None:
    _, memory_service, report_service = _services()
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.SAFETY,
            content="本次会话出现需要父亲关注的安全信号，应由父亲进一步了解情况。",
            tags=["安全提醒", "父亲关注"],
            sensitivity=MemorySensitivity.CRITICAL,
            requires_parent_attention=True,
        )
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    report_json = report.model_dump_json()
    assert "安全信号" in report.summary
    assert report.safety_alerts
    assert any("安全确认" in action for action in report.suggested_parent_actions)
    assert "逐字返回" not in report_json
    assert "胆小" not in report_json
    assert "不合群" not in report_json
    assert "懒" not in report_json
    assert "不聪明" not in report_json


def test_parent_report_service_sanitizes_fixed_negative_labels() -> None:
    repository, memory_service, report_service = _services()
    repository.save(
        memory_service.create(
            _memory_request(
                memory_type=MemoryType.EXPRESSION_PATTERN,
                content="孩子在开放提问下回答较短。",
                tags=["表达"],
            )
        ).model_copy(update={"content": "孩子胆小、不合群。"}, deep=True)
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    report_json = report.model_dump_json()
    assert "胆小" not in report_json
    assert "不合群" not in report_json
    assert "需要更多安全感" in report_json
