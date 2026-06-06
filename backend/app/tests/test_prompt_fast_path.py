from datetime import datetime, timezone

from app.domain.agent_runtime import (
    AgentRuntimeRequest,
)
from app.domain.enums import IntentType, RiskLevel
from app.domain.model_types import (
    ModelRequest,
    ModelResponse,
    ModelTaskType,
)
from app.domain.scene import (
    SceneAction,
    SceneId,
    SceneRouteDecision,
    SceneTransitionType,
)
from app.domain.time import TimeContext, TimePeriod
from app.services.child_agent_runtime import ChildAgentRuntime


class CapturingModelRegistry:
    def __init__(self, response_text: str = "好的，去跑步开心！") -> None:
        self.response = ModelResponse(
            task_type=ModelTaskType.CHILD_CHAT,
            response_text=response_text,
            structured_output={"reply": response_text},
            provider_name="fixed",
            model_name="fixed-child-chat",
            metadata={},
        )
        self.last_request: ModelRequest | None = None

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.last_request = request
        return self.response


def _time_context() -> TimeContext:
    return TimeContext(
        now=datetime(2026, 5, 28, 16, 30, tzinfo=timezone.utc),
        timezone="Asia/Shanghai",
        time_period=TimePeriod.AFTER_SCHOOL,
        weekday=True,
        schedule_goal="自由聊天",
        preferred_interactions=[],
        avoid=[],
    )


def _open_route(
    *,
    risk_level: RiskLevel = RiskLevel.NONE,
) -> SceneRouteDecision:
    return SceneRouteDecision(
        session_id="fast_path_session",
        primary_intent=IntentType.CASUAL_CHAT,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.OPEN_CONVERSATION,
        transition=SceneTransitionType.REPLACE,
        scene_stack=[SceneId.OPEN_CONVERSATION],
        risk_level=risk_level,
        confidence=0.9,
        reason="test_route",
        reply_text="好呀。",
        signals={},
        quick_actions=[],
    )


def _learning_route() -> SceneRouteDecision:
    return SceneRouteDecision(
        session_id="fast_path_session",
        primary_intent=IntentType.LEARNING_HELP,
        base_scene=SceneId.DAILY_AFTER_SCHOOL_CHECKIN,
        active_scene=SceneId.LEARNING_HOMEWORK_HELP,
        transition=SceneTransitionType.PUSH,
        scene_stack=[SceneId.DAILY_AFTER_SCHOOL_CHECKIN, SceneId.LEARNING_HOMEWORK_HELP],
        risk_level=RiskLevel.NONE,
        confidence=0.9,
        reason="learning_route",
        reply_text="我们先看看题目在问什么。",
        signals={},
        quick_actions=[SceneAction(id="speak_problem", label="读题目")],
    )


def _safety_route() -> SceneRouteDecision:
    return SceneRouteDecision(
        session_id="fast_path_session",
        primary_intent=IntentType.SAFETY_RISK,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.SAFETY_GUARDIAN,
        transition=SceneTransitionType.REPLACE,
        scene_stack=[SceneId.SAFETY_GUARDIAN],
        risk_level=RiskLevel.HIGH,
        confidence=0.95,
        reason="safety_route",
        reply_text="先去找家长或老师。",
        signals={"safety_evidence": ["adult_secret"]},
        quick_actions=[],
    )


def _privacy_route() -> SceneRouteDecision:
    return SceneRouteDecision(
        session_id="fast_path_session",
        primary_intent=IntentType.PRIVACY_QUESTION,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.PRIVACY_BOUNDARY,
        transition=SceneTransitionType.REPLACE,
        scene_stack=[SceneId.PRIVACY_BOUNDARY],
        risk_level=RiskLevel.LOW,
        confidence=0.9,
        reason="privacy_route",
        reply_text="家庭地址不要告诉别人。",
        signals={},
        quick_actions=[],
    )


def _bedtime_route() -> SceneRouteDecision:
    return SceneRouteDecision(
        session_id="fast_path_session",
        primary_intent=IntentType.BEDTIME_REFLECTION,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.DAILY_BEDTIME_REFLECTION,
        transition=SceneTransitionType.REPLACE,
        scene_stack=[SceneId.DAILY_BEDTIME_REFLECTION],
        risk_level=RiskLevel.NONE,
        confidence=0.9,
        reason="bedtime_route",
        reply_text="晚安，睡个好觉。",
        signals={},
        quick_actions=[],
    )


def _request(
    *,
    child_text: str = "我一会要去跑步了",
    route_decision: SceneRouteDecision | None = None,
    intent: str | None = "casual_chat",
    image_context: dict | None = None,
    memory_context: list | dict | str | None = None,
    conversation_metadata: dict | None = None,
) -> AgentRuntimeRequest:
    meta = conversation_metadata or {}
    if image_context is not None:
        meta.setdefault("image_context", image_context)
        meta.setdefault("contains_image", True)
    return AgentRuntimeRequest(
        child_id="child_fast_path_test",
        session_id="fast_path_session",
        child_text=child_text,
        route_decision=route_decision or _open_route(),
        time_context=_time_context(),
        parent_policy={
            "version": 2,
            "communication_preferences": {
                "child_nickname": "小禾",
                "child_age": 8,
                "child_grade": 2,
                "child_gender": "boy",
            },
        },
        memory_context=memory_context or [],
        conversation_metadata=meta,
        intent=intent,
    )


def _run(request: AgentRuntimeRequest) -> tuple:
    registry = CapturingModelRegistry()
    runtime = ChildAgentRuntime(model_registry=registry)
    result = runtime.run(request)
    return result, registry


# --- Fast path enabled cases ---

def test_fast_path_enabled_for_running_chat() -> None:
    """普通跑步聊天应走 fast path，不被轻共创误拦截。"""
    result, _ = _run(_request(child_text="我一会要去跑步了。"))
    assert result.fast_path_used is True
    assert result.fast_path_reason == "low_risk_open_chat"
    assert result.fast_path_blocked_reason is None
    assert result.prompt_template_mode == "fast"


def test_fast_path_enabled_for_jump_rope() -> None:
    """跳绳是普通运动，不应触发轻共创，应走 fast path。"""
    result, _ = _run(_request(child_text="一块跳绳了，我们跳了很多。"))
    assert result.fast_path_used is True
    assert result.prompt_template_mode == "fast"


def test_fast_path_enabled_for_short_reply() -> None:
    result, _ = _run(_request(child_text="都行吧。"))
    assert result.fast_path_used is True
    assert result.prompt_template_mode == "fast"


def test_fast_path_enabled_for_topic_change() -> None:
    result, _ = _run(_request(child_text="换个话题。"))
    assert result.fast_path_used is True
    assert result.prompt_template_mode == "fast"


# --- Fast path prompt is shorter ---

def test_fast_path_prompt_shorter_than_full() -> None:
    fast_result, _ = _run(_request(child_text="今天天气真好。"))
    # Run a full path case for comparison (learning scene)
    full_result, _ = _run(_request(
        child_text="这道题怎么做？",
        route_decision=_learning_route(),
        intent="learning_help",
    ))
    assert fast_result.prompt_total_chars > 0
    assert full_result.prompt_total_chars > 0
    assert fast_result.prompt_total_chars < full_result.prompt_total_chars


# --- Fast path blocked cases ---

def test_fast_path_blocked_for_learning_help() -> None:
    result, _ = _run(_request(
        child_text="这道题怎么做？",
        route_decision=_learning_route(),
        intent="learning_help",
    ))
    assert result.fast_path_used is False
    # Scene check happens before intent check
    assert "scene=" in result.fast_path_blocked_reason


def test_fast_path_blocked_for_image_context() -> None:
    result, _ = _run(_request(
        child_text="看看这个",
        image_context={"recognized_text": "一张画", "recognized_type": "child_drawing"},
    ))
    assert result.fast_path_used is False
    # contains_image=True is set by the helper, so blocked_reason is has_image_or_attachment
    assert result.fast_path_blocked_reason in ("has_image_or_attachment", "has_image_context")


def test_fast_path_blocked_for_safety_scene() -> None:
    result, _ = _run(_request(
        child_text="陌生人让我保密",
        route_decision=_safety_route(),
        intent="safety_risk",
    ))
    assert result.fast_path_used is False
    # Scene check or risk_level check happens before intent
    assert result.fast_path_blocked_reason is not None


def test_fast_path_blocked_for_privacy_scene() -> None:
    result, _ = _run(_request(
        child_text="我不想告诉家长",
        route_decision=_privacy_route(),
        intent="privacy_question",
    ))
    assert result.fast_path_used is False
    assert result.fast_path_blocked_reason is not None


def test_fast_path_blocked_for_bedtime() -> None:
    result, _ = _run(_request(
        child_text="我要睡觉了",
        route_decision=_bedtime_route(),
        intent="bedtime_reflection",
    ))
    assert result.fast_path_used is False
    # bedtime scene != conversation.open, so blocked by scene
    assert result.fast_path_blocked_reason is not None


def test_fast_path_blocked_for_sensitive_keyword() -> None:
    result, _ = _run(_request(child_text="陌生人让我保密"))
    assert result.fast_path_used is False
    assert "sensitive_keyword" in (result.fast_path_blocked_reason or "")


# --- Output contract fields ---

def test_fast_path_result_has_debug_fields() -> None:
    result, _ = _run(_request(child_text="今天天气不错。"))
    assert result.prompt_total_chars > 0
    assert result.system_prompt_chars > 0
    assert "global_system" in result.section_chars_by_layer
    assert result.prompt_template_mode in ("fast", "full")


# --- Fast path output uses lightweight contract ---

def test_fast_path_uses_fast_output_contract(registry=None) -> None:
    result, reg = _run(_request(child_text="你好呀。"))
    assert result.fast_path_used is True
    # Verify the system prompt contains fast contract markers
    system_msg = reg.last_request.messages[0].content
    assert "co_creation_type" not in system_msg  # fast contract omits co-creation
    assert "child_engagement" in system_msg  # but keeps basic control


def test_full_path_uses_full_output_contract() -> None:
    result, reg = _run(_request(
        child_text="这道题怎么做？",
        route_decision=_learning_route(),
        intent="learning_help",
    ))
    assert result.fast_path_used is False
    system_msg = reg.last_request.messages[0].content
    assert "co_creation_type" in system_msg  # full contract has co-creation


# --- Memory context blocks fast path ---

def test_fast_path_blocked_for_memory_context() -> None:
    result, _ = _run(_request(
        child_text="今天天气不错",
        memory_context=[{"type": "interest", "content": "孩子喜欢画画"}],
    ))
    assert result.fast_path_used is False
    assert result.fast_path_blocked_reason == "has_memory"


def test_fast_path_enabled_for_empty_memory() -> None:
    result, _ = _run(_request(
        child_text="今天天气不错",
        memory_context=[],
    ))
    assert result.fast_path_used is True


# --- Image / attachment stricter blocking (返修 1) ---

def test_fast_path_blocked_for_contains_image_without_context() -> None:
    """contains_image=True but no image_context → still blocked."""
    result, _ = _run(_request(
        child_text="看看这个",
        conversation_metadata={"contains_image": True},
    ))
    assert result.fast_path_used is False
    assert result.fast_path_blocked_reason == "has_image_or_attachment"


def test_fast_path_blocked_for_homework_context() -> None:
    """homework_context present → blocked."""
    result, _ = _run(_request(
        child_text="这道题怎么做",
        conversation_metadata={"homework_context": {"text": "1+1=?"}},
    ))
    assert result.fast_path_used is False
    assert result.fast_path_blocked_reason == "has_homework_context"


def test_fast_path_blocked_for_pending_image() -> None:
    """pending_image metadata → blocked."""
    result, _ = _run(_request(
        child_text="我拍了一张照片",
        conversation_metadata={"pending_image": True},
    ))
    assert result.fast_path_used is False
    assert result.fast_path_blocked_reason == "has_pending_image"


def test_fast_path_blocked_for_attachment_count() -> None:
    """attachment_count > 0 → blocked."""
    result, _ = _run(_request(
        child_text="看看这个",
        conversation_metadata={"attachment_count": 1},
    ))
    assert result.fast_path_used is False
    assert result.fast_path_blocked_reason == "has_image_or_attachment"


# --- Co-creation stricter blocking (返修 2) ---

def test_fast_path_blocked_for_co_creation_suggested() -> None:
    """Turn guidance suggests co-creation → blocked."""
    result, _ = _run(_request(child_text="我想编一个恐龙的故事"))
    assert result.fast_path_used is False
    assert result.fast_path_blocked_reason == "co_creation_suggested"


def test_fast_path_blocked_for_co_creation_type_in_metadata() -> None:
    """co_creation_active in metadata → blocked."""
    result, _ = _run(_request(
        child_text="今天天气不错",
        conversation_metadata={"co_creation_active": True},
    ))
    assert result.fast_path_used is False
    assert result.fast_path_blocked_reason == "co_creation_active"


def test_fast_path_enabled_for_playing_ball() -> None:
    """打球是普通运动，应走 fast path。"""
    result, _ = _run(_request(child_text="我一会要去打球了。"))
    assert result.fast_path_used is True
    assert result.prompt_template_mode == "fast"


def test_co_creation_triggered_for_story_with_character() -> None:
    """小兔跳到月亮上：角色+场景+运动词，可触发轻共创。"""
    from app.services.light_co_creation_service import LightCoCreationService
    svc = LightCoCreationService()
    decision = svc.should_trigger_story_chain(
        session_id="test_co_creation",
        child_text="小兔跳到月亮上。",
    )
    assert decision.should_trigger is True


def test_co_creation_not_triggered_for_running() -> None:
    """普通跑步不应触发轻共创。"""
    from app.services.light_co_creation_service import LightCoCreationService
    svc = LightCoCreationService()
    decision = svc.should_trigger_story_chain(
        session_id="test_co_creation_running",
        child_text="我一会要去跑步了。",
    )
    assert decision.should_trigger is False


def test_co_creation_not_triggered_for_jump_rope() -> None:
    """普通跳绳不应触发轻共创。"""
    from app.services.light_co_creation_service import LightCoCreationService
    svc = LightCoCreationService()
    decision = svc.should_trigger_story_chain(
        session_id="test_co_creation_jump_rope",
        child_text="一块跳绳了，我们跳了很多。",
    )
    assert decision.should_trigger is False
