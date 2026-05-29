from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
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
from app.domain.model_types import ModelResponse, ModelTaskType
from app.domain.enums import RiskCategory, RiskLevel
from app.domain.schemas.conversation import (
    ClientContext,
    ConversationInput,
    ConversationMessageRequest,
)
from app.repositories.memory_repository import InMemoryMemoryRepository
from app.repositories.memory_sql_repository import SqlAlchemyMemoryRepository
from app.services.conversation_memory_hooks import ConversationMemoryHooks
from app.services.conversation_service import ConversationService
from app.services.memory_service import MemoryService
from app.services.parent_report_service import ParentReportService
from app.services.relationship_memory import (
    INTEREST_SEED,
    PROUD_MOMENT,
    RELATIONSHIP_MEMORY_TYPE_KEY,
    TOPIC_BOUNDARY,
    build_relationship_profile,
    memory_relationship_topic,
)
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


class EmptyConversationRepository:
    def list_report_messages(self, *, child_id, report_date):
        return []


class ReportModelRegistry:
    def generate(self, request):
        return ModelResponse(
            task_type=ModelTaskType.PARENT_REPORT,
            response_text="",
            structured_output={
                "daily_report": {
                    "summary": "模型日报：学习求助。",
                    "learning_observations": [
                        "孩子本次遇到学习求助，系统引导其先说明题目在问什么。"
                    ],
                    "expression_observations": [],
                    "emotion_observations": [],
                    "safety_alerts": [],
                    "suggested_parent_actions": [
                        "今晚可以轻轻问题目在问什么；避免直接给答案。"
                    ],
                }
            },
            provider_name="mimo",
            model_name="mimo-v2.5-pro",
            metadata={},
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
        conversation_repository=EmptyConversationRepository(),
        model_registry=ReportModelRegistry(),
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


def _sqlite_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def _db_memory_service() -> tuple[MemoryService, SqlAlchemyMemoryRepository]:
    repository = SqlAlchemyMemoryRepository(session_factory=_sqlite_session_factory())
    memory_service = MemoryService(
        repository=repository,
        now_provider=_fixed_now,
    )
    return memory_service, repository


def _conversation_stack_with_memory_service(
    memory_service: MemoryService,
    *,
    runtime: CapturingRuntime | None = None,
) -> tuple[ConversationService, CapturingRuntime]:
    runtime = runtime or CapturingRuntime()
    conversation_service = ConversationService(
        scene_orchestrator=SceneOrchestrator(),
        child_agent_runtime=runtime,
        memory_hooks=ConversationMemoryHooks(memory_service=memory_service),
        debug_enabled=True,
    )
    return conversation_service, runtime


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


def _relationship_memories(memories: list[Any], relationship_type: str) -> list[Any]:
    return [
        memory
        for memory in memories
        if any(
            evidence.metadata.get(RELATIONSHIP_MEMORY_TYPE_KEY) == relationship_type
            for evidence in memory.evidence
        )
    ]


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


def test_conversation_memory_hooks_persist_structured_memory_to_sql_repository() -> None:
    child_id = "child_auto_memory_sql_learning"
    memory_service, repository = _db_memory_service()
    conversation_service, _ = _conversation_stack_with_memory_service(memory_service)

    response = conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_auto_memory_sql_learning",
            text="我有一道题不会",
        )
    )
    memories = repository.list_by_child(child_id)
    serialized = " ".join(memory.model_dump_json() for memory in memories)

    assert response.session_state.active_scene == "learning.homework_help"
    assert any(memory.memory_type == MemoryType.LEARNING_PATTERN for memory in memories)
    assert "先说明题目在问什么" in serialized
    assert "我有一道题不会" not in serialized
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
            text="有个陌生人让我不要告诉家长",
        )
    )

    memories = _memories(memory_service, child_id)
    safety_memory = next(
        memory for memory in memories if memory.memory_type == MemoryType.SAFETY
    )
    assert response.session_state.active_scene == "safety.guardian"
    assert safety_memory.requires_parent_attention is True
    assert safety_memory.visible_to_parent is True
    assert "有个陌生人让我不要告诉家长" not in safety_memory.content
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
    assert report.learning_observations == []
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
            content="本次会话出现需要家长关注的安全信号。",
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


def test_conversation_retrieves_db_backed_memory_context_to_runtime() -> None:
    child_id = "child_auto_memory_sql_runtime_context"
    runtime = CapturingRuntime()
    memory_service, _ = _db_memory_service()
    conversation_service, _ = _conversation_stack_with_memory_service(
        memory_service,
        runtime=runtime,
    )
    memory_service.create(
        _manual_memory_request(
            child_id=child_id,
            memory_type=MemoryType.LEARNING_PATTERN,
            content="孩子最近学习求助时适合先复述题意。",
            tags=["学习求助", "题", "题意复述"],
        )
    )

    conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_auto_memory_sql_runtime_context",
            text="我有一道题不会",
        )
    )

    memory_context = runtime.requests[0].memory_context
    assert isinstance(memory_context, list)
    assert len(memory_context) == 1
    assert memory_context[0]["memory_type"] == "learning_pattern"
    assert "题意" in memory_context[0]["content"]
    assert "evidence" not in memory_context[0]


def test_running_competition_creates_interest_seed_without_raw_text() -> None:
    child_id = "child_relationship_running_interest"
    memory_service, _, conversation_service, _ = _conversation_stack()

    conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_relationship_running_interest",
            text="我要参加运动比赛，跑步的时候喜欢快的感觉。",
        )
    )

    memories = _relationship_memories(
        _memories(memory_service, child_id),
        INTEREST_SEED,
    )
    serialized = " ".join(memory.model_dump_json() for memory in memories)
    assert len(memories) == 1
    assert memories[0].memory_type == MemoryType.INTEREST
    assert memory_relationship_topic(memories[0]) == "跑步比赛"
    assert "我要参加运动比赛" not in serialized
    assert "快的感觉" not in serialized


def test_non_sports_competition_does_not_create_running_interest_seed() -> None:
    for index, text in enumerate(("我参加英语比赛。", "我参加数学比赛。")):
        child_id = f"child_relationship_non_sports_competition_{index}"
        memory_service, _, conversation_service, _ = _conversation_stack()

        conversation_service.handle_message(
            _message(
                child_id=child_id,
                session_id=f"session_relationship_non_sports_competition_{index}",
                text=text,
            )
        )

        interests = _relationship_memories(
            _memories(memory_service, child_id),
            INTEREST_SEED,
        )
        proud = _relationship_memories(
            _memories(memory_service, child_id),
            PROUD_MOMENT,
        )
        assert all(memory_relationship_topic(memory) != "跑步比赛" for memory in interests)
        assert all(
            memory_relationship_topic(memory) != "运动比赛表达" for memory in proud
        )


def test_art_and_story_create_low_sensitive_interest_seeds() -> None:
    child_id = "child_relationship_art_story"
    memory_service, _, conversation_service, _ = _conversation_stack()

    conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_relationship_art_story",
            text="我画了一只小狐狸，还想编一个故事。",
        )
    )

    interests = _relationship_memories(
        _memories(memory_service, child_id),
        INTEREST_SEED,
    )
    assert len(interests) == 1
    assert {memory.sensitivity for memory in interests} == {MemorySensitivity.LOW}
    assert memory_relationship_topic(interests[0]) in {"画画", "故事想象"}
    assert memory_relationship_topic(interests[0]) != "动物"


def test_animal_content_without_creation_action_creates_animal_interest_seed() -> None:
    child_id = "child_relationship_animal_interest"
    memory_service, _, conversation_service, _ = _conversation_stack()

    conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_relationship_animal_interest",
            text="我喜欢狐狸。",
        )
    )

    interests = _relationship_memories(
        _memories(memory_service, child_id),
        INTEREST_SEED,
    )
    assert len(interests) == 1
    assert memory_relationship_topic(interests[0]) == "动物"


def test_interest_seed_dedupes_across_sessions_for_same_child_and_topic() -> None:
    child_id = "child_relationship_interest_cross_session_dedupe"
    memory_service, _, conversation_service, _ = _conversation_stack()

    conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_relationship_interest_first",
            text="我要参加运动比赛，跑步的时候喜欢快的感觉。",
        )
    )
    conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_relationship_interest_second",
            text="我还是想聊跑步比赛。",
        )
    )

    interests = _relationship_memories(
        _memories(memory_service, child_id),
        INTEREST_SEED,
    )
    assert len(
        [
            memory
            for memory in interests
            if memory_relationship_topic(memory) == "跑步比赛"
        ]
    ) == 1


def test_topic_boundary_and_bedtime_are_recorded_as_strategy_memory() -> None:
    child_id = "child_relationship_topic_boundary"
    memory_service, _, conversation_service, _ = _conversation_stack()

    conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_relationship_topic_boundary",
            text="行，我们聊点别的话题。",
        )
    )
    conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_relationship_bedtime_boundary",
            text="我们明天再聊，我得睡觉了。",
            device_time="2026-05-19T20:40:00+08:00",
        )
    )

    boundaries = _relationship_memories(
        _memories(memory_service, child_id),
        TOPIC_BOUNDARY,
    )
    topics = {memory_relationship_topic(memory) for memory in boundaries}
    assert "换话题边界" in topics
    assert "睡前收尾" in topics
    assert all(memory.memory_type == MemoryType.STRATEGY for memory in boundaries)


def test_topic_boundary_dedupes_within_same_session() -> None:
    child_id = "child_relationship_topic_boundary_dedupe"
    memory_service, _, conversation_service, _ = _conversation_stack()

    for _ in range(2):
        conversation_service.handle_message(
            _message(
                child_id=child_id,
                session_id="session_relationship_topic_boundary_dedupe",
                text="换个话题。",
            )
        )

    boundaries = _relationship_memories(
        _memories(memory_service, child_id),
        TOPIC_BOUNDARY,
    )
    assert len(
        [
            memory
            for memory in boundaries
            if memory_relationship_topic(memory) == "换话题边界"
        ]
    ) == 1


def test_competition_project_and_feeling_create_proud_moment() -> None:
    child_id = "child_relationship_proud_moment"
    memory_service, _, conversation_service, _ = _conversation_stack()

    conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_relationship_proud_moment",
            text="我参加的是运动比赛，项目是跑步，我喜欢快的感觉。",
        )
    )

    proud = _relationship_memories(
        _memories(memory_service, child_id),
        PROUD_MOMENT,
    )
    assert len(proud) == 1
    assert proud[0].memory_type == MemoryType.EXPRESSION_PATTERN
    assert "表达" in proud[0].content


def test_operation_aside_bystander_and_asr_fragments_do_not_create_relationship_memory() -> None:
    cases = [
        "按一下，说完再按一下，取消，重说。",
        "妈妈说让我跟你说我喜欢跑步。",
        "嗯这个那个说完了。",
    ]
    for index, text in enumerate(cases):
        child_id = f"child_relationship_filtered_{index}"
        memory_service, _, conversation_service, _ = _conversation_stack()

        conversation_service.handle_message(
            _message(
                child_id=child_id,
                session_id=f"session_relationship_filtered_{index}",
                text=text,
            )
        )

        memories = _memories(memory_service, child_id)
        assert not _relationship_memories(memories, INTEREST_SEED)
        assert not _relationship_memories(memories, TOPIC_BOUNDARY)
        assert not _relationship_memories(memories, PROUD_MOMENT)


def test_privacy_and_critical_self_harm_do_not_create_relationship_memory() -> None:
    cases = [
        "我的学校名字是星星小学，我也喜欢跑步。",
        "我不想活了，但是我也喜欢恐龙。",
    ]
    for index, text in enumerate(cases):
        child_id = f"child_relationship_safety_filtered_{index}"
        memory_service, _, conversation_service, _ = _conversation_stack()

        response = conversation_service.handle_message(
            _message(
                child_id=child_id,
                session_id=f"session_relationship_safety_filtered_{index}",
                text=text,
            )
        )

        memories = _memories(memory_service, child_id)
        assert not _relationship_memories(memories, INTEREST_SEED)
        assert not _relationship_memories(memories, PROUD_MOMENT)
        if "不想活" in text:
            assert response.debug is not None
            assert response.debug.safety is not None
            assert response.debug.safety.risk_level == RiskLevel.CRITICAL
            assert response.debug.safety.primary_category == RiskCategory.SELF_HARM


def test_sports_fatigue_relationship_memory_is_not_self_harm_label() -> None:
    child_id = "child_relationship_sports_fatigue"
    memory_service, _, conversation_service, _ = _conversation_stack()

    conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_relationship_sports_fatigue",
            text="我跑步比赛跑完累死了，但是不疼。",
        )
    )

    serialized = " ".join(
        memory.model_dump_json() for memory in _memories(memory_service, child_id)
    )
    assert "self_harm" not in serialized
    assert "自伤" not in serialized
    assert "累死了" not in serialized


def test_memory_hook_failure_does_not_block_child_reply(caplog) -> None:
    class FailingMemoryHooks:
        def retrieve_context(self, **_kwargs: object) -> list[dict[str, object]]:
            return []

        def record_turn(self, **_kwargs: object) -> None:
            raise RuntimeError("contains memory content")

    child_text = "我喜欢恐龙，但是记忆失败也不能阻塞我。"
    conversation_service = ConversationService(
        scene_orchestrator=SceneOrchestrator(),
        child_agent_runtime=CapturingRuntime(),
        memory_hooks=FailingMemoryHooks(),  # type: ignore[arg-type]
        debug_enabled=True,
    )
    caplog.set_level("WARNING", logger="app.conversation")

    response = conversation_service.handle_message(
        _message(
            child_id="child_relationship_memory_hook_failure",
            session_id="session_relationship_memory_hook_failure",
            text=child_text,
        )
    )

    assert response.reply.text
    assert "conversation_memory_hook_failed" in caplog.text
    assert child_text not in caplog.text
    assert "contains memory content" not in caplog.text


def test_relationship_memory_source_labels_conversation_summary() -> None:
    child_id = "child_relationship_source_conversation"
    memory_service, _, conversation_service, _ = _conversation_stack()

    conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_relationship_source_conversation",
            text="我喜欢恐龙。",
        )
    )

    memories = _relationship_memories(
        _memories(memory_service, child_id),
        INTEREST_SEED,
    )
    assert len(memories) == 1
    for evidence in memories[0].evidence:
        assert evidence.metadata.get("source") == "conversation_summary"


def test_build_relationship_profile_merges_parent_and_conversation_sources() -> None:
    child_id = "child_relationship_profile_merge"
    memory_service, _, conversation_service, _ = _conversation_stack()

    conversation_service.handle_message(
        _message(
            child_id=child_id,
            session_id="session_relationship_profile_merge",
            text="我喜欢恐龙。",
        )
    )

    profile = build_relationship_profile(
        memory_service,
        child_id=child_id,
        parent_profile_interests=["画画", "恐龙"],
        parent_profile_boundaries=["不要追问学校"],
    )

    assert "画画" in profile["interests"]
    assert "恐龙" in profile["interests"]
    assert "不要追问学校" in profile["topic_boundaries"]

    interest_details = profile["interest_details"]
    assert interest_details[0]["topic"] == "画画"
    assert interest_details[0]["source"] == "parent_setting"
    # 恐龙 is from both parent and conversation; parent comes first
    assert interest_details[1]["topic"] == "恐龙"
    assert interest_details[1]["source"] == "parent_setting"

    boundary_details = profile["boundary_details"]
    assert boundary_details[0]["topic"] == "不要追问学校"
    assert boundary_details[0]["source"] == "parent_setting"


def test_parent_report_support_style_offer_two_choices_tailors_actions() -> None:
    child_id = "child_report_offer_two"
    repository = InMemoryMemoryRepository()
    memory_service = MemoryService(
        repository=repository,
        now_provider=_fixed_now,
    )

    expression_memory = memory_service.create(
        MemoryCreateRequest(
            child_id=child_id,
            memory_type=MemoryType.EXPRESSION_PATTERN,
            content="孩子今天更多使用短句或指令式表达。",
            tags=["表达"],
            evidence=[MemoryEvidence(
                source="conversation_summary",
                session_id="s",
                quote_summary="短句表达",
                metadata={},
            )],
            confidence=0.8,
            importance=0.5,
        )
    )

    report_service = ParentReportService(
        memory_service=memory_service,
        conversation_repository=EmptyConversationRepository(),
        model_registry=ReportModelRegistry(),
        now_provider=_fixed_now,
    )

    report = report_service._deterministic_fallback_report(
        child_id=child_id,
        target_date=date(2026, 5, 19),
        memories=[expression_memory],
        conversation_messages=[],
        conversation=report_service._conversation_analysis([]),
        support_style=["offer_two_choices"],
    )

    actions_text = " ".join(report.suggested_parent_actions)
    assert "两个简单选择" in actions_text or "选择就好" in actions_text


def test_parent_report_support_style_ask_fewer_questions_tailors_actions() -> None:
    child_id = "child_report_ask_fewer"
    repository = InMemoryMemoryRepository()
    memory_service = MemoryService(
        repository=repository,
        now_provider=_fixed_now,
    )

    report_service = ParentReportService(
        memory_service=memory_service,
        conversation_repository=EmptyConversationRepository(),
        model_registry=ReportModelRegistry(),
        now_provider=_fixed_now,
    )

    report = report_service._deterministic_fallback_report(
        child_id=child_id,
        target_date=date(2026, 5, 19),
        memories=[],
        conversation_messages=[],
        conversation=report_service._conversation_analysis([]),
        support_style=["ask_fewer_questions"],
    )

    actions_text = " ".join(report.suggested_parent_actions)
    bridge = report.tonight_parent_bridge or ""
    # With ask_fewer_questions, the default action should emphasize not追问
    assert "不追问" in actions_text or "不追问" in bridge or "只轻轻" in actions_text
