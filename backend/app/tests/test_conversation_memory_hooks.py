from datetime import date, datetime, timedelta, timezone
from typing import Any

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
from app.repositories.memory_repository import InMemoryMemoryRepository
from app.services.conversation_memory_hooks import ConversationMemoryHooks
from app.services.conversation_service import ConversationService
from app.services.memory_service import MemoryService
from app.services.parent_report_service import ParentReportService
from app.services.scene_orchestrator import SceneOrchestrator


FORBIDDEN_EVIDENCE_SOURCES = {
    "raw_audio",
    "original_audio",
    "raw_photo",
    "original_photo",
    "raw_image",
    "original_image",
    "raw_chat",
    "full_chat",
    "chat_transcript",
    "long_chat_transcript",
}


def _fixed_now() -> datetime:
    return datetime(2026, 5, 19, 8, 0, tzinfo=timezone.utc)


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


def _conversation_stack(
    *,
    runtime: CapturingRuntime | None = None,
) -> tuple[MemoryService, ParentReportService, ConversationService, CapturingRuntime]:
    repository = InMemoryMemoryRepository()
    memory_service = MemoryService(
        repository=repository,
        now_provider=_fixed_now,
    )
    report_service = ParentReportService(
        memory_service=memory_service,
        now_provider=_fixed_now,
    )
    runtime = runtime or CapturingRuntime()
    conversation_service = ConversationService(
        scene_orchestrator=SceneOrchestrator(),
        child_agent_runtime=runtime,
        memory_hooks=ConversationMemoryHooks(memory_service=memory_service),
        debug_enabled=True,
    )
    return memory_service, report_service, conversation_service, runtime


def _message(
    *,
    child_id: str,
    session_id: str,
    text: str,
    device_time: str = "2026-05-19T16:35:00+08:00",
) -> ConversationMessageRequest:
    return ConversationMessageRequest(
        child_id=child_id,
        session_id=session_id,
        input=ConversationInput(
            type="text",
            text=text,
            attachments=[],
        ),
        client_context=ClientContext(
            device_time=datetime.fromisoformat(device_time),
            timezone="Asia/Shanghai",
            app_mode="child",
        ),
    )


def _memories(memory_service: MemoryService, child_id: str) -> list[Any]:
    return memory_service.list_memories(
        child_id,
        active_only=True,
        include_safety=True,
    )


def _assert_summary_evidence(memories: list[Any]) -> None:
    assert memories
    for memory in memories:
        for evidence in memory.evidence:
            assert evidence.source == "conversation_summary"
            assert evidence.source not in FORBIDDEN_EVIDENCE_SOURCES
            assert evidence.quote_summary


def _manual_memory_request(
    *,
    child_id: str,
    memory_type: MemoryType,
    content: str,
    tags: list[str],
    sensitivity: MemorySensitivity = MemorySensitivity.MEDIUM,
    requires_parent_attention: bool = False,
) -> MemoryCreateRequest:
    return MemoryCreateRequest(
        child_id=child_id,
        memory_type=memory_type,
        content=content,
        tags=tags,
        evidence=[
            MemoryEvidence(
                source="conversation_summary",
                session_id="manual_memory_context_session",
                quote_summary="结构化摘要来源，不包含逐字聊天记录。",
            )
        ],
        confidence=0.82,
        importance=0.7,
        sensitivity=sensitivity,
        visible_to_parent=True,
        visible_to_child=False,
        requires_parent_attention=requires_parent_attention,
    )


def test_learning_help_creates_learning_memory() -> None:
    child_id = "child_auto_memory_learning"
    memory_service, _, conversation_service, _ = _conversation_stack()

    response = conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_auto_memory_learning",
            text="我有一道题不会",
        )
    )

    memories = _memories(memory_service, child_id)
    assert response.session_state.active_scene == "learning.homework_help"
    assert any(memory.memory_type == MemoryType.LEARNING_PATTERN for memory in memories)
    assert any("先说明题目在问什么" in memory.content for memory in memories)
    _assert_summary_evidence(memories)


def test_direct_answer_request_creates_learning_pattern() -> None:
    child_id = "child_auto_memory_direct_answer"
    memory_service, _, conversation_service, _ = _conversation_stack()

    response = conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_auto_memory_direct_answer",
            text="你直接告诉我答案吧",
            device_time="2026-05-19T18:41:00+08:00",
        )
    )

    memories = _memories(memory_service, child_id)
    assert response.session_state.active_scene == "learning.homework_help"
    assert any(
        memory.memory_type == MemoryType.LEARNING_PATTERN
        and "直接要答案倾向" in memory.content
        for memory in memories
    )
    _assert_summary_evidence(memories)


def test_low_energy_expression_creates_emotion_observation_without_parent_attention() -> None:
    child_id = "child_auto_memory_low_energy"
    memory_service, _, conversation_service, _ = _conversation_stack()

    response = conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_auto_memory_low_energy",
            text="我不想说话",
        )
    )

    memories = _memories(memory_service, child_id)
    emotion_memory = next(
        memory
        for memory in memories
        if memory.memory_type == MemoryType.EMOTION_OBSERVATION
    )
    assert response.debug is not None
    assert response.debug.safety is not None
    assert response.debug.safety.risk_level == "low"
    assert emotion_memory.requires_parent_attention is False
    assert emotion_memory.expires_at == _fixed_now() + timedelta(days=14)
    assert "低能量" in emotion_memory.content
    _assert_summary_evidence(memories)


def test_high_risk_guardian_creates_parent_attention_safety_memory() -> None:
    child_id = "child_auto_memory_high_risk"
    memory_service, _, conversation_service, _ = _conversation_stack()

    response = conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_auto_memory_high_risk",
            text="有个陌生人让我不要告诉爸爸妈妈",
        )
    )

    memories = _memories(memory_service, child_id)
    safety_memory = next(
        memory for memory in memories if memory.memory_type == MemoryType.SAFETY
    )
    assert response.session_state.active_scene == "safety.guardian"
    assert safety_memory.requires_parent_attention is True
    assert safety_memory.visible_to_parent is True
    assert "有个陌生人让我不要告诉爸爸妈妈" not in safety_memory.content
    assert memory_service.retrieve(child_id, include_safety=False) == []
    assert memory_service.retrieve(child_id, include_safety=True)[0].id == safety_memory.id
    _assert_summary_evidence(memories)


def test_watch_bullying_creates_parent_visible_observation_without_forced_attention() -> None:
    child_id = "child_auto_memory_watch"
    memory_service, _, conversation_service, _ = _conversation_stack()

    response = conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_auto_memory_watch",
            text="同学骂我",
        )
    )

    memories = _memories(memory_service, child_id)
    observation = next(
        memory
        for memory in memories
        if memory.memory_type == MemoryType.EMOTION_OBSERVATION
    )
    assert response.session_state.active_scene == "safety.gentle_checkin"
    assert observation.visible_to_parent is True
    assert observation.requires_parent_attention is False
    assert "学校同伴互动" in observation.content
    _assert_summary_evidence(memories)


def test_privacy_boundary_memory_does_not_store_specific_private_values() -> None:
    child_id = "child_auto_memory_privacy"
    memory_service, _, conversation_service, _ = _conversation_stack()

    response = conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_auto_memory_privacy",
            text="我的电话是13800000000，学校名字是星星小学，可以告诉你吗",
        )
    )

    memories = _memories(memory_service, child_id)
    privacy_memory = next(
        memory for memory in memories if memory.memory_type == MemoryType.STRATEGY
    )
    assert response.session_state.active_scene == "privacy.boundary"
    assert "家庭地址、电话、学校名字或照片" in privacy_memory.content
    assert "13800000000" not in privacy_memory.model_dump_json()
    assert "星星小学" not in privacy_memory.model_dump_json()
    _assert_summary_evidence(memories)


def test_parent_report_uses_conversation_generated_memory_summary() -> None:
    child_id = "child_auto_memory_report"
    memory_service, report_service, conversation_service, _ = _conversation_stack()

    conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_auto_memory_report",
            text="我有一道题不会",
        )
    )

    report = report_service.generate_daily_report(
        child_id,
        report_date=date(2026, 5, 19),
    )
    report_json = report.model_dump_json()
    assert memory_service.list_memories(child_id)
    assert report.learning_observations == [
        "孩子本次遇到学习求助，系统引导其先说明题目在问什么。"
    ]
    assert "evidence" not in report_json
    assert "quote_summary" not in report_json
    assert "逐字聊天记录" not in report_json


def test_conversation_passes_retrieved_non_safety_memory_context_to_runtime() -> None:
    child_id = "child_auto_memory_runtime_context"
    runtime = CapturingRuntime()
    memory_service, _, conversation_service, _ = _conversation_stack(runtime=runtime)
    memory_service.create(
        _manual_memory_request(
            child_id=child_id,
            memory_type=MemoryType.LEARNING_PATTERN,
            content="孩子最近学习求助时适合先复述题意。",
            tags=["学习求助", "题", "题意复述"],
        )
    )
    memory_service.create(
        _manual_memory_request(
            child_id=child_id,
            memory_type=MemoryType.SAFETY,
            content="本次会话出现需要父亲关注的安全信号。",
            tags=["安全提醒"],
            sensitivity=MemorySensitivity.HIGH,
            requires_parent_attention=True,
        )
    )

    conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_auto_memory_runtime_context",
            text="我有一道题不会",
        )
    )

    memory_context = runtime.requests[0].memory_context
    assert isinstance(memory_context, list)
    assert len(memory_context) == 1
    assert memory_context[0]["memory_type"] == "learning_pattern"
    assert "题意" in memory_context[0]["content"]
    assert "evidence" not in memory_context[0]
