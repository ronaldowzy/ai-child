from datetime import date, datetime, timedelta, timezone
import json

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import (
    ConversationMessageRecord,
    ConversationSessionRecord,
    MemoryItemRecord,
    ParentPolicyRecord,
    ParentReportRecord,
    RoutingDecisionRecord,
)
from app.domain.agent_runtime import (
    AgentRuntimeRequest,
    AgentRuntimeResult,
    AgentRuntimeSource,
)
from app.domain.memory import (
    MemoryCreateRequest,
    MemoryEvidence,
    MemorySensitivity,
    MemoryType,
)
from app.domain.schemas.conversation import (
    ClientContext,
    ConversationInput,
    ConversationMessageRequest,
)
from app.domain.schemas.parent_policy import ParentPolicyUpdateRequest
from app.repositories.conversation_persistence_repository import (
    ConversationPersistenceRepository,
)
from app.repositories.memory_repository import InMemoryMemoryRepository
from app.repositories.memory_sql_repository import SqlAlchemyMemoryRepository
from app.repositories.parent_policy_repository import ParentPolicyRepository
from app.repositories.parent_report_repository import (
    ParentReportRepository,
    ParentReportRepositoryUnavailable,
)
from app.services.conversation_memory_hooks import ConversationMemoryHooks
from app.services.conversation_persistence_service import (
    ConversationPersistenceService,
)
from app.services.conversation_service import ConversationService
from app.services.memory_service import MemoryService
from app.services.parent_policy_service import ParentPolicyService
from app.services.parent_report_service import ParentReportService
from app.services.scene_orchestrator import SceneOrchestrator


def _sqlite_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


class CapturingRuntime:
    def __init__(self) -> None:
        self.requests: list[AgentRuntimeRequest] = []

    def run(self, request: AgentRuntimeRequest) -> AgentRuntimeResult:
        self.requests.append(request)
        return AgentRuntimeResult(
            reply_text=request.route_decision.reply_text,
            source=AgentRuntimeSource.FALLBACK,
            fallback_reason="test_runtime",
        )


def _message(
    *,
    child_id: str,
    session_id: str,
    text: str,
) -> ConversationMessageRequest:
    return ConversationMessageRequest(
        child_id=child_id,
        session_id=session_id,
        input=ConversationInput(type="text", text=text, attachments=[]),
        client_context=ClientContext(
            device_time=datetime.fromisoformat("2026-05-22T16:35:00+08:00"),
            timezone="Asia/Shanghai",
            app_mode="child",
        ),
    )


def test_db_persistence_e2e_parent_policy_conversation_memory_report() -> None:
    session_factory = _sqlite_session_factory()
    child_id = "child_db_persistence_e2e"
    session_id = "session_db_persistence_e2e"
    memory_now = datetime(2026, 5, 22, 8, 0, tzinfo=timezone.utc)
    report_now = [datetime(2026, 5, 22, 20, 0, tzinfo=timezone.utc)]

    parent_policy_repository = ParentPolicyRepository(
        session_factory=session_factory,
    )
    parent_policy_service = ParentPolicyService(
        repository=parent_policy_repository,
        fallback_to_memory=False,
    )
    parent_policy_service.update_policy(
        ParentPolicyUpdateRequest(
            child_id=child_id,
            child_nickname="豆豆",
            parent_message_raw="最近用轻松方式鼓励孩子先说题目在问什么。",
        )
    )

    memory_repository = SqlAlchemyMemoryRepository(
        session_factory=session_factory,
    )
    memory_service = MemoryService(
        repository=memory_repository,
        now_provider=lambda: memory_now,
        fallback_to_memory=False,
    )
    report_repository = ParentReportRepository(session_factory=session_factory)
    conversation_repository = ConversationPersistenceRepository(
        session_factory=session_factory,
    )
    report_service = ParentReportService(
        memory_service=memory_service,
        repository=report_repository,
        conversation_repository=conversation_repository,
        now_provider=lambda: report_now[0],
        fallback_to_memory=False,
    )
    conversation_service = ConversationService(
        parent_policy_service=parent_policy_service,
        scene_orchestrator=SceneOrchestrator(),
        child_agent_runtime=CapturingRuntime(),
        memory_hooks=ConversationMemoryHooks(memory_service=memory_service),
        conversation_persistence_service=ConversationPersistenceService(
            repository=ConversationPersistenceRepository(
                session_factory=session_factory,
            )
        ),
        debug_enabled=False,
    )

    response = conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id=session_id,
            text="我有一道题不会",
        )
    )
    first_report = report_service.get_daily_report(
        child_id,
        report_date=date(2026, 5, 22),
    )
    report_now[0] = report_now[0] + timedelta(hours=1)
    second_report = report_service.get_daily_report(
        child_id,
        report_date=date(2026, 5, 22),
    )

    with session_factory() as session:
        assert session.execute(select(ParentPolicyRecord)).scalar_one().child_id == child_id
        assert session.get(ConversationSessionRecord, session_id) is not None
        messages = session.execute(select(ConversationMessageRecord)).scalars().all()
        routing = session.execute(select(RoutingDecisionRecord)).scalars().all()
        memories = session.execute(select(MemoryItemRecord)).scalars().all()
        reports = session.execute(select(ParentReportRecord)).scalars().all()

    assert response.session_state.active_scene == "learning.homework_help"
    assert {message.actor for message in messages} == {"child", "agent"}
    assert len(routing) == 1
    assert any(memory.memory_type == "learning_pattern" for memory in memories)
    assert len(reports) == 1
    assert reports[0].summary == first_report.summary
    assert second_report.created_at == first_report.created_at
    assert second_report.summary == first_report.summary
    assert second_report.learning_observations == first_report.learning_observations

    serialized_report = first_report.model_dump_json()
    for forbidden in (
        "evidence",
        "quote_summary",
        "raw_audio",
        "raw_photo",
        "prompt",
        "debug",
        "provider",
    ):
        assert forbidden not in serialized_report


def test_parent_report_repository_failure_does_not_block_e2e_report(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FailingReportRepository:
        def save(self, _report):
            raise ParentReportRepositoryUnavailable("孩子说了不能进入日志的原话")

        def get(self, _child_id, _report_date):
            raise ParentReportRepositoryUnavailable("孩子说了不能进入日志的原话")

        def list_by_child(self, _child_id, limit=30):
            raise ParentReportRepositoryUnavailable("孩子说了不能进入日志的原话")

        def delete(self, _child_id, _report_date):
            raise ParentReportRepositoryUnavailable("孩子说了不能进入日志的原话")

        def clear(self):
            raise ParentReportRepositoryUnavailable("孩子说了不能进入日志的原话")

    memory_service = MemoryService(
        repository=InMemoryMemoryRepository(),
        now_provider=lambda: datetime(2026, 5, 22, 8, 0, tzinfo=timezone.utc),
    )
    memory_service.create(
        MemoryCreateRequest(
            child_id="child_report_fallback_e2e",
            memory_type=MemoryType.LEARNING_PATTERN,
            content="孩子在学习求助时适合先复述题意。",
            tags=["学习求助", "题意"],
            evidence=[
                MemoryEvidence(
                    source="conversation_summary",
                    session_id="session_report_fallback_e2e",
                    quote_summary="结构化摘要来源，不包含逐字聊天记录。",
                )
            ],
            confidence=0.84,
            importance=0.7,
            sensitivity=MemorySensitivity.MEDIUM,
            visible_to_parent=True,
            visible_to_child=False,
        )
    )
    session_factory = _sqlite_session_factory()
    report_service = ParentReportService(
        memory_service=memory_service,
        repository=FailingReportRepository(),
        conversation_repository=ConversationPersistenceRepository(
            session_factory=session_factory,
        ),
        now_provider=lambda: datetime(2026, 5, 22, 20, 0, tzinfo=timezone.utc),
    )
    caplog.set_level("WARNING", logger="app.parent_report")

    report = report_service.get_daily_report(
        "child_report_fallback_e2e",
        report_date=date(2026, 5, 22),
    )
    log_json = json.dumps(
        [
            {
                "message": record.getMessage(),
                "event": getattr(record, "event", None),
                "operation": getattr(record, "operation", None),
                "error_type": getattr(record, "error_type", None),
            }
            for record in caplog.records
        ],
        ensure_ascii=False,
    )

    assert report.learning_observations == ["孩子在学习求助时适合先复述题意。"]
    assert "parent_report_repository_fallback" in log_json
    assert "孩子在学习求助时适合先复述题意" not in log_json
    assert "结构化摘要来源" not in log_json
    assert "孩子说了不能进入日志的原话" not in log_json
