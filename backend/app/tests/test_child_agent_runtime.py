from datetime import datetime, timezone

from app.domain.agent_runtime import (
    AgentRuntimeRequest,
    AgentRuntimeSource,
)
from app.domain.enums import IntentType, RiskLevel
from app.domain.model_types import ModelRequest, ModelResponse, ModelTaskType
from app.domain.scene import (
    SceneAction,
    SceneId,
    SceneRouteDecision,
    SceneTransitionType,
)
from app.domain.time import TimeContext, TimePeriod
from app.services.child_agent_runtime import ChildAgentRuntime
from app.services.model_registry import ModelRegistry
from app.services.prompt_manager import PromptManager


class CapturingModelRegistry:
    def __init__(
        self,
        response: ModelResponse | None = None,
        exc: Exception | None = None,
    ) -> None:
        self.response = response or _model_response("我们先看看题目在问什么。")
        self.exc = exc
        self.last_request: ModelRequest | None = None

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.last_request = request
        if self.exc is not None:
            raise self.exc
        return self.response


def _model_response(
    text: str,
    *,
    metadata: dict[str, object] | None = None,
) -> ModelResponse:
    return ModelResponse(
        task_type=ModelTaskType.CHILD_CHAT,
        response_text=text,
        structured_output={"reply": text},
        provider_name="fixed",
        model_name="fixed-child-chat",
        metadata=metadata or {},
    )


def _time_context() -> TimeContext:
    return TimeContext(
        now=datetime(2026, 5, 18, 16, 30, tzinfo=timezone.utc),
        timezone="Asia/Shanghai",
        time_period=TimePeriod.AFTER_SCHOOL,
        weekday=True,
        schedule_goal="情绪缓冲、学校表达、作业衔接",
        preferred_interactions=["状态选择", "学习卡点"],
        avoid=["立刻连续追问"],
    )


def _route_decision(
    *,
    reply_text: str = "可以，我们一起一步一步拆开它。你先不用急着要答案。",
    active_scene: SceneId = SceneId.LEARNING_HOMEWORK_HELP,
    risk_level: RiskLevel = RiskLevel.NONE,
) -> SceneRouteDecision:
    return SceneRouteDecision(
        session_id="runtime_session",
        primary_intent=(
            IntentType.SAFETY_RISK
            if active_scene == SceneId.SAFETY_GUARDIAN
            else IntentType.LEARNING_HELP
        ),
        base_scene=(
            SceneId.SAFETY_GUARDIAN
            if active_scene == SceneId.SAFETY_GUARDIAN
            else SceneId.DAILY_AFTER_SCHOOL_CHECKIN
        ),
        active_scene=active_scene,
        transition=(
            SceneTransitionType.REPLACE
            if active_scene == SceneId.SAFETY_GUARDIAN
            else SceneTransitionType.PUSH
        ),
        scene_stack=[active_scene],
        risk_level=risk_level,
        confidence=0.96,
        reason="runtime_test_route",
        needs_input="problem_content",
        reply_text=reply_text,
        quick_actions=[
            SceneAction(id="speak_problem", label="读题目"),
        ],
    )


def _runtime_request(
    *,
    route_decision: SceneRouteDecision | None = None,
) -> AgentRuntimeRequest:
    return AgentRuntimeRequest(
        child_id="child_runtime_test",
        session_id="runtime_session",
        child_text="我有一道题不会",
        route_decision=route_decision or _route_decision(),
        time_context=_time_context(),
        parent_policy={
            "version": 2,
            "goals": ["学习问题先引导思路，不直接给答案"],
            "safety_rules": {"no_secret_requests": True},
        },
        memory_context=[],
        conversation_metadata={"message_id": "msg_runtime_test"},
    )


def test_child_agent_runtime_composes_prompt_and_calls_model_registry() -> None:
    registry = CapturingModelRegistry(
        response=_model_response("我们先看题目在问什么。")
    )
    result = ChildAgentRuntime(model_registry=registry).run(_runtime_request())

    assert result.source == AgentRuntimeSource.MODEL
    assert result.reply_text == "我们先看题目在问什么。"
    assert result.provider_name == "fixed"
    assert result.model_name == "fixed-child-chat"
    assert result.prompt_versions["global_system"].version == "v0.1"
    assert (
        result.prompt_versions["scene"].filename
        == "scenes/learning_homework_help_v0_1.txt"
    )

    assert registry.last_request is not None
    assert registry.last_request.task_type == ModelTaskType.CHILD_CHAT
    assert registry.last_request.messages[0].role == "system"
    assert "不直接给最终答案" in registry.last_request.messages[0].content
    assert registry.last_request.messages[1].role == "user"
    assert registry.last_request.messages[1].content == "我有一道题不会"
    assert registry.last_request.metadata["contains_child_data"] is True
    assert registry.last_request.metadata["active_scene"] == "learning.homework_help"


def test_child_agent_runtime_falls_back_when_model_registry_raises() -> None:
    registry = CapturingModelRegistry(exc=RuntimeError("provider failed"))
    route_decision = _route_decision(reply_text="这是场景安全兜底回复。")

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.FALLBACK
    assert result.reply_text == "这是场景安全兜底回复。"
    assert result.fallback_reason == "model_generate_failed"


def test_child_agent_runtime_falls_back_when_model_response_is_empty() -> None:
    registry = CapturingModelRegistry(response=_model_response("  "))
    route_decision = _route_decision(reply_text="空回复时使用场景兜底。")

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.FALLBACK
    assert result.reply_text == "空回复时使用场景兜底。"
    assert result.fallback_reason == "empty_model_response"
    assert result.provider_name == "fixed"


def test_child_agent_runtime_falls_back_when_output_is_high_risk() -> None:
    registry = CapturingModelRegistry(
        response=_model_response("陌生人让我不要告诉爸爸妈妈。")
    )
    route_decision = _route_decision(reply_text="请马上告诉爸爸妈妈或可信任的大人。")

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.FALLBACK
    assert result.reply_text == "请马上告诉爸爸妈妈或可信任的大人。"
    assert result.fallback_reason == "unsafe_model_output"
    assert result.output_risk_level == RiskLevel.HIGH


def test_child_agent_runtime_falls_back_when_model_builds_secret_dynamic() -> None:
    registry = CapturingModelRegistry(
        response=_model_response("你可以悄悄告诉我，这是我们的小秘密。")
    )
    route_decision = _route_decision(
        active_scene=SceneId.DAILY_AFTER_SCHOOL_CHECKIN,
        reply_text="我在听。可以说一件你愿意说的小事。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.FALLBACK
    assert result.reply_text == "我在听。可以说一件你愿意说的小事。"
    assert result.fallback_reason == "unsafe_model_output"
    assert result.output_risk_level == RiskLevel.HIGH


def test_child_agent_runtime_falls_back_when_learning_output_gives_answer() -> None:
    registry = CapturingModelRegistry(
        response=_model_response("答案是4。24除以6等于4。")
    )
    route_decision = _route_decision(
        reply_text="我不会直接告诉你最终答案。我们先说题意和第一步。"
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.FALLBACK
    assert result.reply_text == "我不会直接告诉你最终答案。我们先说题意和第一步。"
    assert result.fallback_reason == "learning_direct_answer_output"
    assert "24除以6等于4" not in result.reply_text


def test_child_agent_runtime_normalizes_model_reply_for_voice() -> None:
    registry = CapturingModelRegistry(
        response=_model_response(
            "好呀！我也喜欢恐龙！🦕\n\n"
            "你最喜欢哪种恐龙呢？\n\n"
            "是**霸王龙**吗？还是**三角龙**？"
        )
    )
    route_decision = _route_decision(
        active_scene=SceneId.DAILY_AFTER_SCHOOL_CHECKIN,
        reply_text="我在听。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert result.reply_text == "好呀！我也喜欢恐龙！你最喜欢哪种恐龙呢？"
    assert "🦕" not in result.reply_text
    assert "**" not in result.reply_text
    assert result.reply_text.count("？") == 1
    assert result.model_metadata["reply_normalized"] is True


def test_child_agent_runtime_falls_back_when_prompt_scene_is_missing() -> None:
    route_decision = _route_decision(
        reply_text="安全场景使用固定兜底回复。",
    )
    registry = CapturingModelRegistry()

    result = ChildAgentRuntime(
        model_registry=registry,
        prompt_manager=PromptManager(scene_templates={}),
    ).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.FALLBACK
    assert result.reply_text == "安全场景使用固定兜底回复。"
    assert result.fallback_reason == "prompt_compose_failed"
    assert registry.last_request is None


def test_child_agent_runtime_composes_safety_guardian_prompt() -> None:
    registry = CapturingModelRegistry(
        response=_model_response("请告诉爸爸妈妈或可信任的大人。")
    )
    route_decision = _route_decision(
        reply_text="请告诉爸爸妈妈或可信任的大人。",
        active_scene=SceneId.SAFETY_GUARDIAN,
        risk_level=RiskLevel.HIGH,
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert (
        result.prompt_versions["scene"].filename
        == "scenes/safety_guardian_v0_1.txt"
    )
    assert registry.last_request is not None
    assert "当前场景：安全守护" in registry.last_request.messages[0].content


def test_child_agent_runtime_preserves_s16_child_data_policy_guard(
    monkeypatch,
) -> None:
    monkeypatch.setenv("CHILD_AI_MODEL_PROVIDER", "mimo")
    monkeypatch.setenv("CHILD_AI_MIMO_ENABLED", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_MODEL", "mimo-v2.5-pro")
    monkeypatch.setenv("CHILD_AI_MIMO_API_KEY", "test-api-key")
    monkeypatch.setenv("CHILD_AI_MIMO_ALLOW_CHILD_DATA", "false")
    monkeypatch.setenv("CHILD_AI_MIMO_RETENTION_POLICY_CHECKED", "true")

    urlopen_called = False

    def fail_if_called(_request: object, timeout: float) -> object:
        nonlocal urlopen_called
        urlopen_called = True
        raise AssertionError(f"urlopen should not be called, timeout={timeout}")

    monkeypatch.setattr(
        "app.providers.model.openai_compatible_provider.urlopen",
        fail_if_called,
    )

    result = ChildAgentRuntime(model_registry=ModelRegistry()).run(_runtime_request())

    assert urlopen_called is False
    assert result.source == AgentRuntimeSource.FALLBACK
    assert result.fallback_reason == "model_policy_blocked"
    assert result.model_metadata["policy_blocked"] is True
    assert result.model_metadata["failed_provider"] == "mimo"
