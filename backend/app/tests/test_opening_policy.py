from datetime import datetime, timezone

from app.domain.memory import (
    MemoryCreateRequest,
    MemoryEvidence,
    MemorySensitivity,
    MemoryType,
)
from app.domain.schemas.parent_policy import ParentPolicy, ParentSchedule
from app.domain.time import TimeContext, TimePeriod
from app.repositories.memory_repository import InMemoryMemoryRepository
from app.services.memory_service import MemoryService
from app.services.opening_policy import OpeningMode, OpeningPolicyBuilder


def _now() -> datetime:
    return datetime(2026, 5, 23, 10, 0, tzinfo=timezone.utc)


def _parent_policy(
    *,
    child_id: str = "child_opening_policy",
    goals: list[str] | None = None,
    parent_message_raw: str | None = None,
    preferences: dict[str, object] | None = None,
) -> ParentPolicy:
    return ParentPolicy(
        child_id=child_id,
        parent_message_raw=parent_message_raw,
        goals=goals or [],
        communication_preferences=preferences or {},
        safety_rules={},
        schedule=ParentSchedule(),
        created_at=_now(),
        updated_at=_now(),
    )


def _time_context(period: TimePeriod = TimePeriod.AFTER_SCHOOL) -> TimeContext:
    return TimeContext(
        now=datetime(2026, 5, 23, 16, 30, tzinfo=timezone.utc),
        timezone="Asia/Shanghai",
        time_period=period,
        weekday=True,
        schedule_goal="情绪缓冲、学校表达、作业衔接",
        preferred_interactions=["状态选择", "学校小事", "兴趣切入"],
        avoid=["立刻连续追问"],
    )


def _memory_service() -> MemoryService:
    return MemoryService(repository=InMemoryMemoryRepository(), now_provider=_now)


def _create_interest_seed(
    service: MemoryService,
    *,
    child_id: str = "child_opening_policy",
    topic: str = "跑步比赛",
    sensitivity: MemorySensitivity = MemorySensitivity.LOW,
) -> None:
    service.create(
        MemoryCreateRequest(
            child_id=child_id,
            memory_type=MemoryType.INTEREST,
            content=f"孩子近期自然聊到{topic}，可作为低压力回访的兴趣种子。",
            tags=["relationship_memory", "interest_seed", topic],
            evidence=[
                MemoryEvidence(
                    source="conversation_summary",
                    session_id="session_opening_policy_seed",
                    quote_summary=f"孩子自然提到{topic}相关内容，适合短期轻回访。",
                    metadata={
                        "relationship_memory_type": "interest_seed",
                        "topic": topic,
                        "next_hook": "下次只轻问一个具体细节。",
                    },
                )
            ],
            sensitivity=sensitivity,
            confidence=0.8,
            importance=0.6,
        )
    )


def _create_boundary(
    service: MemoryService,
    *,
    child_id: str = "child_opening_policy",
    kind: str = "topic_change",
    topic: str = "换话题边界",
) -> None:
    service.create(
        MemoryCreateRequest(
            child_id=child_id,
            memory_type=MemoryType.STRATEGY,
            content="孩子明确表达想换话题，后续应尊重转场，不继续追问旧话题。",
            tags=["relationship_memory", "topic_boundary", "尊重边界"],
            evidence=[
                MemoryEvidence(
                    source="conversation_summary",
                    session_id="session_opening_policy_boundary",
                    quote_summary="孩子表达想换个话题或不继续当前话题。",
                    metadata={
                        "relationship_memory_type": "topic_boundary",
                        "topic": topic,
                        "boundary_kind": kind,
                        "next_hook": "下次给两个轻松方向。",
                    },
                )
            ],
            sensitivity=MemorySensitivity.LOW,
            confidence=0.84,
            importance=0.62,
        )
    )


def _create_low_expression_state(
    service: MemoryService,
    *,
    child_id: str = "child_opening_policy",
) -> None:
    service.create(
        MemoryCreateRequest(
            child_id=child_id,
            memory_type=MemoryType.EXPRESSION_PATTERN,
            content="孩子近期表达偏短句和低能量，开场应降低表达压力。",
            tags=["低能量", "短句", "低压力"],
            evidence=[
                MemoryEvidence(
                    source="conversation_summary",
                    session_id="session_opening_policy_expression",
                    quote_summary="孩子最近多用短句回应，适合给更小的表达入口。",
                    metadata={"source": "conversation_summary"},
                )
            ],
            sensitivity=MemorySensitivity.LOW,
            confidence=0.74,
            importance=0.55,
        )
    )


def test_low_interest_seed_without_boundary_uses_interest_callback() -> None:
    service = _memory_service()
    _create_interest_seed(service)
    policy = OpeningPolicyBuilder(memory_service=service).build(
        child_id="child_opening_policy",
        parent_policy=_parent_policy(),
        time_context=_time_context(),
    )

    assert policy.mode == OpeningMode.INTEREST_CALLBACK
    assert policy.seed_topic == "跑步比赛"
    assert policy.seed_recall_allowed is True


def test_no_seed_uses_default_light() -> None:
    policy = OpeningPolicyBuilder(memory_service=_memory_service()).build(
        child_id="child_opening_policy",
        parent_policy=_parent_policy(),
        time_context=_time_context(),
    )

    assert policy.mode == OpeningMode.DEFAULT_LIGHT
    assert policy.seed_topic is None


def test_profile_interest_can_seed_personalized_opening() -> None:
    policy = OpeningPolicyBuilder(memory_service=_memory_service()).build(
        child_id="child_opening_policy",
        parent_policy=_parent_policy(
            preferences={"child_interests": ["恐龙", "画画"]}
        ),
        time_context=_time_context(),
    )

    assert policy.mode == OpeningMode.INTEREST_CALLBACK
    assert policy.seed_topic == "恐龙"
    assert policy.seed_recall_allowed is True


def test_low_expression_state_uses_low_expression_support() -> None:
    service = _memory_service()
    _create_low_expression_state(service)

    policy = OpeningPolicyBuilder(memory_service=service).build(
        child_id="child_opening_policy",
        parent_policy=_parent_policy(),
        time_context=_time_context(),
    )

    assert policy.mode == OpeningMode.LOW_EXPRESSION_SUPPORT
    assert policy.seed_recall_allowed is False
    assert policy.seed_recall_reason == "low_expression_state"


def test_topic_change_boundary_blocks_interest_callback() -> None:
    service = _memory_service()
    _create_interest_seed(service)
    _create_boundary(service, kind="topic_change", topic="换话题边界")

    policy = OpeningPolicyBuilder(memory_service=service).build(
        child_id="child_opening_policy",
        parent_policy=_parent_policy(),
        time_context=_time_context(),
    )

    assert policy.mode == OpeningMode.BOUNDARY_RESPECT
    assert policy.boundary_kind == "topic_change"
    assert policy.boundary_cooldown_active is True
    assert policy.seed_recall_allowed is False


def test_bedtime_close_boundary_does_not_continue_old_topic() -> None:
    service = _memory_service()
    _create_interest_seed(service)
    _create_boundary(service, kind="bedtime_close", topic="睡前收尾")

    policy = OpeningPolicyBuilder(memory_service=service).build(
        child_id="child_opening_policy",
        parent_policy=_parent_policy(),
        time_context=_time_context(),
    )

    assert policy.mode == OpeningMode.BOUNDARY_RESPECT
    assert policy.boundary_kind == "bedtime_close"
    assert policy.seed_topic is None
    assert policy.seed_recall_allowed is False


def test_refusal_boundary_blocks_old_topic() -> None:
    service = _memory_service()
    _create_interest_seed(service)
    _create_boundary(service, kind="refusal", topic="跑步比赛")

    policy = OpeningPolicyBuilder(memory_service=service).build(
        child_id="child_opening_policy",
        parent_policy=_parent_policy(),
        time_context=_time_context(),
    )

    assert policy.mode == OpeningMode.BOUNDARY_RESPECT
    assert policy.boundary_kind == "refusal"
    assert policy.seed_recall_allowed is False


def test_bedtime_with_exciting_seed_defers_interest() -> None:
    service = _memory_service()
    _create_interest_seed(service, topic="跑步比赛")

    policy = OpeningPolicyBuilder(memory_service=service).build(
        child_id="child_opening_policy",
        parent_policy=_parent_policy(),
        time_context=_time_context(TimePeriod.BEDTIME),
    )

    assert policy.mode == OpeningMode.BEDTIME_DEFER_INTEREST
    assert policy.seed_topic == "跑步比赛"
    assert policy.exciting_topic_deferred is True
    assert policy.prefer_parent_bridge is True


def test_bedtime_without_seed_uses_bedtime_closure() -> None:
    policy = OpeningPolicyBuilder(memory_service=_memory_service()).build(
        child_id="child_opening_policy",
        parent_policy=_parent_policy(),
        time_context=_time_context(TimePeriod.BEDTIME),
    )

    assert policy.mode == OpeningMode.BEDTIME_CLOSURE
    assert policy.seed_topic is None
    assert policy.prefer_parent_bridge is True


def test_no_school_check_uses_place_neutral_policy_rules() -> None:
    policy = OpeningPolicyBuilder(memory_service=_memory_service()).build(
        child_id="child_opening_policy",
        parent_policy=_parent_policy(parent_message_raw="不要查岗学校，不要追问。"),
        time_context=_time_context(),
    )

    assert "学校" not in " ".join(policy.prompt_rules)
    assert any("不提固定场所" in rule for rule in policy.prompt_rules)


def test_parent_learning_goal_is_translated_to_low_pressure_hint() -> None:
    service = _memory_service()
    _create_interest_seed(service)
    policy = OpeningPolicyBuilder(memory_service=service).build(
        child_id="child_opening_policy",
        parent_policy=_parent_policy(goals=["希望孩子多学习，遇到作业能拆开想。"]),
        time_context=_time_context(),
    )

    assert policy.mode == OpeningMode.INTEREST_CALLBACK
    assert policy.parent_goal_hint is not None
    assert "小问题" in policy.parent_goal_hint
    assert "今天我们来聊学习吧" not in policy.parent_goal_hint


def test_age_band_limits_for_younger_and_older_children() -> None:
    young_policy = OpeningPolicyBuilder(memory_service=_memory_service()).build(
        child_id="child_opening_policy",
        parent_policy=_parent_policy(preferences={"child_age": 6}),
        time_context=_time_context(),
    )
    older_policy = OpeningPolicyBuilder(memory_service=_memory_service()).build(
        child_id="child_opening_policy",
        parent_policy=_parent_policy(preferences={"child_age": 10}),
        time_context=_time_context(),
    )

    assert young_policy.age_band == "age_5_6"
    assert young_policy.max_chars == 36
    assert young_policy.max_spoken_options == 2
    assert older_policy.age_band == "age_9_10"
    assert older_policy.max_chars == 60
    assert older_policy.max_spoken_options == 3


def test_memory_read_failure_falls_back_without_blocking_policy() -> None:
    class FailingMemoryService:
        def list_memories(self, *_args, **_kwargs):
            raise RuntimeError("database unavailable")

    policy = OpeningPolicyBuilder(memory_service=FailingMemoryService()).build(  # type: ignore[arg-type]
        child_id="child_opening_policy",
        parent_policy=_parent_policy(),
        time_context=_time_context(),
    )

    assert policy.mode == OpeningMode.DEFAULT_LIGHT
    assert policy.seed_topic is None


def test_opening_prompt_uses_structured_profile_not_raw_preferences() -> None:
    from app.services.opening_service import OpeningService

    service = OpeningService(
        parent_policy_service=_StubParentPolicyService(),
        time_context_service=_StubTimeContextService(),
        tts_service=_StubTtsService(),
        model_registry=_StubModelRegistry(),
        memory_service=_memory_service(),
    )
    parent_policy = _parent_policy(
        preferences={
            "child_age": 8,
            "child_interests": ["恐龙", "画画"],
            "child_temperament": ["warms_up_slowly"],
            "support_style_preferences": ["offer_two_choices"],
        },
    )
    parent_policy = parent_policy.model_copy(
        update={"child_nickname": "豆豆"},
    )
    opening_policy = OpeningPolicyBuilder(
        memory_service=_memory_service(),
    ).build(
        child_id="child_opening_policy",
        parent_policy=parent_policy,
        time_context=_time_context(),
    )

    prompt = service._opening_prompt(
        parent_policy=parent_policy,
        time_context=_time_context(),
        opening_policy=opening_policy,
    )

    assert "孩子画像" in prompt
    assert "child_interests" in prompt
    assert "恐龙" in prompt
    assert "child_temperament" in prompt
    assert "不要给孩子贴标签" in prompt
    assert "support_style_preferences" in prompt
    assert "不要在开场白中提及家长设置的偏好标签" in prompt
    # Should NOT contain raw dict dump
    assert "communication_preferences" not in prompt


class _StubParentPolicyService:
    def get_policy(self, child_id):
        return _parent_policy()


class _StubTimeContextService:
    def build_context(self, **_kwargs):
        return _time_context()


class _StubTtsService:
    def generate_for_conversation(self, **_kwargs):
        return None


class _StubModelRegistry:
    def generate(self, request):
        from app.domain.model_types import ModelResponse
        return ModelResponse(
            task_type=request.task_type,
            response_text="豆豆，你好呀！",
            structured_output={},
            provider_name="mock",
            model_name="mock",
            metadata={"mock": True},
        )
