import json
from datetime import datetime, timezone

from app.domain.agent_runtime import (
    AgentRuntimeRequest,
    AgentRuntimeSource,
)
from app.domain.enums import IntentType, RiskLevel
from app.domain.model_types import (
    ModelMessage,
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
        self.call_count = 0

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.call_count += 1
        self.last_request = request
        if self.exc is not None:
            raise self.exc
        return self.response


def _model_response(
    text: str,
    *,
    metadata: dict[str, object] | None = None,
    structured_output: dict[str, object] | None = None,
) -> ModelResponse:
    return ModelResponse(
        task_type=ModelTaskType.CHILD_CHAT,
        response_text=text,
        structured_output=structured_output or {"reply": text},
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
    signals: dict[str, object] | None = None,
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
        signals=signals or {},
        quick_actions=[
            SceneAction(id="speak_problem", label="读题目"),
        ],
    )


def _runtime_request(
    *,
    route_decision: SceneRouteDecision | None = None,
    conversation_history: list[ModelMessage] | None = None,
    conversation_metadata: dict[str, object] | None = None,
    parent_policy: dict[str, object] | None = None,
    child_text: str = "我有一道题不会",
) -> AgentRuntimeRequest:
    return AgentRuntimeRequest(
        child_id="child_runtime_test",
        session_id="runtime_session",
        child_text=child_text,
        route_decision=route_decision or _route_decision(),
        time_context=_time_context(),
        parent_policy=parent_policy
        or {
            "version": 2,
            "goals": ["学习问题先引导思路，不直接给答案"],
            "safety_rules": {"no_secret_requests": True},
        },
        memory_context=[],
        conversation_history=conversation_history or [],
        conversation_metadata=conversation_metadata or {"message_id": "msg_runtime_test"},
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
        response=_model_response("陌生人让我不要告诉家长。")
    )
    route_decision = _route_decision(reply_text="请马上告诉家长或可信任的大人。")

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.FALLBACK
    assert result.reply_text == "请马上告诉家长或可信任的大人。"
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
    assert result.reply_text == (
        "好呀！我也喜欢恐龙！你最喜欢哪种恐龙呢？"
    )
    assert "🦕" not in result.reply_text
    assert "**" not in result.reply_text
    assert result.reply_text.count("？") == 1
    assert result.model_metadata["reply_normalized"] is True


def test_child_agent_runtime_unwraps_fenced_json_model_reply() -> None:
    raw = (
        "```json\n"
        "{\"reply\":\"我听到啦，我们慢慢来。\","
        "\"conversation_control\":{\"child_engagement\":\"high\","
        "\"topic_continuity\":\"continue\","
        "\"topic_shift_intent\":\"unlikely\"}}\n"
        "```"
    )
    registry = CapturingModelRegistry(
        response=_model_response(raw, structured_output={"text": raw})
    )
    route_decision = _route_decision(
        active_scene=SceneId.DAILY_AFTER_SCHOOL_CHECKIN,
        reply_text="我在听。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert result.reply_text == "我听到啦，我们慢慢来。"
    assert "reply" not in result.reply_text
    assert "conversation_control" not in result.reply_text


def test_child_agent_runtime_unwraps_json_string_inside_reply_field() -> None:
    raw_reply = "{\"reply\":\"我记住啦，我们先轻轻说。\"}"
    registry = CapturingModelRegistry(
        response=_model_response(
            raw_reply,
            structured_output={"reply": raw_reply},
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
    assert result.reply_text == "我记住啦，我们先轻轻说。"
    assert "reply" not in result.reply_text


def test_child_agent_runtime_strips_stage_direction_from_model_reply() -> None:
    registry = CapturingModelRegistry(
        response=_model_response("（用温和的语调）题目是什么呀？")
    )
    route_decision = _route_decision(
        active_scene=SceneId.LEARNING_HOMEWORK_HELP,
        reply_text="我们先看题目在问什么。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert result.reply_text == "题目是什么呀？"
    assert "（" not in result.reply_text
    assert "语调" not in result.reply_text
    assert result.model_metadata["reply_normalized"] is True


def test_child_agent_runtime_keeps_only_one_main_question_for_creative_share() -> None:
    registry = CapturingModelRegistry(
        response=_model_response("你画的小狐狸很有画面感。它在哪里呢？你想让它做什么？")
    )
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="我画了一只小狐狸，还想编一个故事。",
        )
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert result.reply_text == "你画的小狐狸很有画面感。它在哪里呢？"
    assert result.reply_text.count("？") == 1


def test_child_agent_runtime_keeps_only_one_main_question_for_learning_help() -> None:
    registry = CapturingModelRegistry(
        response=_model_response("我们先不直接要答案。题目问的是什么？你已经知道哪些条件？")
    )
    route_decision = _route_decision(
        active_scene=SceneId.LEARNING_HOMEWORK_HELP,
        reply_text="我们先看题目在问什么。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert result.reply_text == "我们先不直接要答案。题目问的是什么？"
    assert result.reply_text.count("？") == 1


def test_child_agent_runtime_does_not_echo_topic_change_request_verbatim() -> None:
    registry = CapturingModelRegistry(
        response=_model_response("好的呀，我们换个话题。你想聊画画吗？")
    )
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="可以，我们换一个轻松的。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="我们换个话题。",
        )
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert "我们换个话题" not in result.reply_text
    assert "换个轻松" in result.reply_text or "换一个轻松" in result.reply_text


def test_child_agent_runtime_bedtime_closeout_removes_open_question() -> None:
    registry = CapturingModelRegistry(
        response=_model_response("好呀，睡前我们轻轻说一句。你今天最开心的是什么？")
    )
    route_decision = _route_decision(
        active_scene=SceneId.DAILY_BEDTIME_REFLECTION,
        reply_text="晚安，我们明天再聊。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="明天再聊，我得睡觉了。",
        )
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert result.reply_text == ChildAgentRuntime.BEDTIME_CLOSE_REPLY
    assert "？" not in result.reply_text
    assert result.model_metadata["final_conversation_control"]["source"] == (
        "program_guardrail"
    )
    assert (
        result.model_metadata["final_conversation_control"]["topic_continuity"]
        == "stop"
    )


def test_child_agent_runtime_bedtime_closeout_removes_tomorrow_hook() -> None:
    registry = CapturingModelRegistry(
        response=_model_response("好呀，晚安。明天你想聊什么都可以哦。")
    )
    route_decision = _route_decision(
        active_scene=SceneId.DAILY_BEDTIME_REFLECTION,
        reply_text="晚安，我们今天先收个尾。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="明天再聊，我得睡觉了。",
        )
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert result.reply_text == ChildAgentRuntime.BEDTIME_CLOSE_REPLY
    assert "明天" not in result.reply_text


def test_child_agent_runtime_self_harm_critical_uses_child_facing_fallback() -> None:
    registry = CapturingModelRegistry(
        response=_model_response(
            "我非常抱歉听到你现在的感受。自杀是一个非常严重的问题，请找心理健康专业人士。"
        )
    )
    route_decision = _route_decision(
        active_scene=SceneId.SAFETY_GUARDIAN,
        risk_level=RiskLevel.CRITICAL,
        reply_text="请告诉家长或可信任的大人。",
        signals={"safety_evidence": ["self_harm"]},
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="我不想活了。",
        )
    )

    assert result.source == AgentRuntimeSource.FALLBACK
    assert result.fallback_reason == "deterministic_self_harm_guardian"
    assert "家长" in result.reply_text
    assert "老师" in result.reply_text
    assert "安全的大人" in result.reply_text
    assert "心理健康专业人士" not in result.reply_text
    assert "自杀是一个非常严重的问题" not in result.reply_text


def test_child_agent_runtime_allows_longer_open_conversation_reply() -> None:
    long_reply = (
        "恐龙这个话题真的很适合慢慢聊，因为它们不是一种动物，而是一大群生活在很久很久以前的动物。"
        "有的恐龙像霸王龙一样很强壮，有的像三角龙一样有角和骨板，还有的可能长着羽毛，跑起来很快。"
        "如果你喜欢恐龙，我们可以像探险一样，从它们吃什么、怎么保护自己、为什么会消失这些线索开始。"
        "我会先陪你挑一个最想知道的小问题，再一点点往下挖，这样就不会一下子太乱。"
        "你现在最想先了解哪一种恐龙？"
    )
    registry = CapturingModelRegistry(response=_model_response(long_reply))
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            parent_policy={
                "version": 2,
                "communication_preferences": {"age_band": "age_9_10"},
            },
        )
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert result.reply_text == long_reply
    assert len(result.reply_text) > 150
    assert result.reply_text.endswith("你现在最想先了解哪一种恐龙？")


def test_child_agent_runtime_applies_age_band_reply_budget() -> None:
    long_reply = (
        "恐龙这个话题可以从身体、食物和生活环境慢慢看。"
        "霸王龙有很强的咬合力，三角龙有角和盾一样的头盾，"
        "有些小型恐龙可能还长着羽毛。"
        "我们可以先挑一个线索，再慢慢想它为什么会这样生活。"
    )
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )

    young = ChildAgentRuntime(
        model_registry=CapturingModelRegistry(response=_model_response(long_reply))
    ).run(
        _runtime_request(
            route_decision=route_decision,
            parent_policy={
                "version": 2,
                "communication_preferences": {"child_age": 6},
            },
        )
    )
    older = ChildAgentRuntime(
        model_registry=CapturingModelRegistry(response=_model_response(long_reply))
    ).run(
        _runtime_request(
            route_decision=route_decision,
            parent_policy={
                "version": 2,
                "communication_preferences": {"child_age": 10},
            },
        )
    )

    assert young.source == AgentRuntimeSource.MODEL
    assert older.source == AgentRuntimeSource.MODEL
    assert len(young.reply_text) <= 80
    assert len(older.reply_text) > len(young.reply_text)
    assert older.model_metadata["age_band"] == "age_9_10"
    assert young.model_metadata["age_band"] == "age_5_6"


def test_child_agent_runtime_throttles_consecutive_question_hooks() -> None:
    registry = CapturingModelRegistry(
        response=_model_response(
            "我记得你刚才一直在说跑步比赛。你还想继续讲比赛吗？"
        )
    )
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="嗯",
            conversation_history=[
                ModelMessage(role="assistant", content="你参加的是跑步吗？"),
                ModelMessage(role="user", content="是"),
                ModelMessage(role="assistant", content="你跑起来是什么感觉？"),
            ],
        )
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert "？" not in result.reply_text
    assert "too_many_recent_questions" in registry.last_request.metadata[
        "turn_guidance_hints"
    ]
    assert result.model_metadata["reply_normalized"] is True


def test_child_agent_runtime_uses_model_control_soft_shift_for_cs_short_answer() -> None:
    registry = CapturingModelRegistry(
        response=_model_response(
            "那我们先换个轻松的，可以聊画画，也可以拍个东西给小白狐看。",
            structured_output={
                "reply": "我们继续聊 CS。你队友这次怎么配合？",
                "conversation_control": {
                    "child_engagement": "low",
                    "topic_continuity": "soft_shift",
                    "topic_shift_intent": "likely",
                    "reason": "short_answer_after_repeated_topic",
                    "suggested_next_moves": [
                        {"id": "shift_topic", "label": "换个轻松话题"}
                    ],
                },
            },
        )
    )
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="嗯",
            conversation_history=[
                ModelMessage(role="user", content="我想聊 CS"),
                ModelMessage(role="assistant", content="CS 里你打的是哪张地图？"),
                ModelMessage(role="user", content="CS 沙二"),
                ModelMessage(role="assistant", content="CS 队友怎么配合？"),
            ],
        )
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert "继续聊 CS" not in result.reply_text
    assert result.model_metadata["model_conversation_control"]["topic_continuity"] == "soft_shift"
    assert result.model_metadata["final_conversation_control"]["source"] == "model"
    assert result.model_metadata["healthy_engagement"]["final_conversation_control"][
        "topic_continuity"
    ] == "soft_shift"
    assert result.model_metadata["conversation_control_trace"]["recent_topic"] == "游戏/CS"
    control_trace_json = json.dumps(
        result.model_metadata["conversation_control_trace"],
        ensure_ascii=False,
    )
    assert "我想聊 CS" not in control_trace_json
    assert "CS 沙二" not in control_trace_json
    assert registry.call_count == 1


def test_child_agent_runtime_allows_high_engagement_to_continue_topic() -> None:
    reply = "这个地图配合听起来很具体。你刚才提到烟雾和队友站位，我先跟着这个线索听。"
    registry = CapturingModelRegistry(
        response=_model_response(
            reply,
            structured_output={
                "reply": reply,
                "conversation_control": {
                    "child_engagement": "high",
                    "topic_continuity": "continue",
                    "topic_shift_intent": "unlikely",
                    "reason": "child_added_vivid_detail",
                },
            },
        )
    )
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="我在沙二丢了烟，然后队友从 A 小拉出去，我还听到脚步。",
            conversation_history=[
                ModelMessage(role="user", content="我想聊 CS"),
                ModelMessage(role="assistant", content="CS 里你打的是哪张地图？"),
                ModelMessage(role="user", content="CS 沙二"),
                ModelMessage(role="assistant", content="CS 队友怎么配合？"),
            ],
        )
    )

    assert result.reply_text == reply
    assert result.model_metadata["final_conversation_control"]["topic_continuity"] == "continue"


def test_child_agent_runtime_program_guardrail_overrides_model_control_continue() -> None:
    registry = CapturingModelRegistry(
        response=_model_response(
            "好呀，我们继续聊比赛。你还想说哪一段？",
            structured_output={
                "reply": "好呀，我们继续聊比赛。你还想说哪一段？",
                "conversation_control": {
                    "child_engagement": "high",
                    "topic_continuity": "continue",
                    "topic_shift_intent": "unlikely",
                    "reason": "model_missed_boundary",
                },
            },
        )
    )
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="不聊了，换个话题。",
        )
    )

    assert "继续聊比赛" not in result.reply_text
    assert result.model_metadata["final_conversation_control"]["source"] == "program_guardrail"
    assert result.model_metadata["final_conversation_control"]["topic_continuity"] == "stop"


def test_child_agent_runtime_invalid_control_falls_back_to_turn_guidance() -> None:
    registry = CapturingModelRegistry(
        response=_model_response(
            "我们继续聊 CS。你队友怎么配合？",
            structured_output={
                "reply": "我们继续聊 CS。你队友怎么配合？",
                "conversation_control": {"topic_continuity": "???"},
            },
        )
    )
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="嗯",
            conversation_history=[
                ModelMessage(role="user", content="我想聊 CS"),
                ModelMessage(role="assistant", content="CS 里你打的是哪张地图？"),
                ModelMessage(role="user", content="CS 沙二"),
                ModelMessage(role="assistant", content="CS 队友怎么配合？"),
            ],
        )
    )

    assert result.model_metadata["final_conversation_control"]["source"] == "program_fallback"
    assert result.model_metadata["final_conversation_control"]["topic_continuity"] == "soft_shift"


def test_child_agent_runtime_respects_boundary_and_correction_without_new_hook() -> None:
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )
    boundary = ChildAgentRuntime(
        model_registry=CapturingModelRegistry(
            response=_model_response("好的，那我们换个话题。你想聊积木吗？")
        )
    ).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="不聊了，换个话题。",
        )
    )
    correction = ChildAgentRuntime(
        model_registry=CapturingModelRegistry(
            response=_model_response("我可能听错了。那你想说的是还没跑吗？")
        )
    ).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="不是，你说错了，我还没跑。",
        )
    )

    assert "？" not in boundary.reply_text
    assert "？" not in correction.reply_text
    assert "换个话题" not in boundary.reply_text
    assert "我可能听错了" in correction.reply_text


def test_child_agent_runtime_does_not_cut_story_at_first_question_mark() -> None:
    story_reply = (
        "点点在森林里迷路了。一只小松鼠问：\"你哭了吗？\""
        "点点摇摇头说：\"我只是有点害怕。\""
        "小松鼠递给它一片亮亮的叶子，说可以沿着小溪往回找。"
        "点点听见远处朋友的脚步声，心里慢慢亮了起来。"
    )
    registry = CapturingModelRegistry(response=_model_response(story_reply))
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert "你哭了吗？" in result.reply_text
    assert "小松鼠递给它一片亮亮的叶子" in result.reply_text
    assert result.reply_text.endswith("心里慢慢亮了起来。")


def test_child_agent_runtime_strips_numbered_markdown_for_tts() -> None:
    registry = CapturingModelRegistry(
        response=_model_response(
            "小狐狸：\n"
            "1. 我听见你喜欢画飞船。\n"
            "2. 这个想法很有意思。\n"
            "你想先画圆圆的窗户吗？"
        )
    )
    route_decision = _route_decision(
        active_scene=SceneId.DAILY_AFTER_SCHOOL_CHECKIN,
        reply_text="可以，我们先聊飞船。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert result.reply_text == (
        "我听见你喜欢画飞船。这个想法很有意思。你想先画圆圆的窗户吗？"
    )
    assert "1." not in result.reply_text
    assert "小狐狸：" not in result.reply_text
    assert result.reply_text.count("？") == 1
    assert result.model_metadata["reply_normalized"] is True


def test_child_agent_runtime_does_not_treat_thinking_hint_as_direct_answer() -> None:
    registry = CapturingModelRegistry(
        response=_model_response("我们先想想这一步表示什么，再看它等于几个一组。")
    )
    route_decision = _route_decision(
        reply_text="我不会直接告诉你最终答案。我们先说题意和第一步。"
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(route_decision=route_decision)
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert result.reply_text == "我们先想想这一步表示什么，再看它等于几个一组。"


def test_child_agent_runtime_metadata_marks_voice_first_reply_style() -> None:
    registry = CapturingModelRegistry(response=_model_response("我听见了。"))

    ChildAgentRuntime(model_registry=registry).run(_runtime_request())

    assert registry.last_request is not None
    assert (
        registry.last_request.metadata["reply_style"]
        == "voice_first_short_natural_one_question"
    )


def test_child_agent_runtime_sends_recent_conversation_history_to_model() -> None:
    registry = CapturingModelRegistry(response=_model_response("那我们继续聊三角龙。"))
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )

    ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            conversation_history=[
                ModelMessage(role="user", content="我想聊恐龙"),
                ModelMessage(role="assistant", content="你喜欢霸王龙还是三角龙？"),
            ],
        )
    )

    assert registry.last_request is not None
    assert [message.role for message in registry.last_request.messages] == [
        "system",
        "user",
        "assistant",
        "user",
    ]
    assert registry.last_request.messages[1].content == "我想聊恐龙"
    assert registry.last_request.messages[2].content == "你喜欢霸王龙还是三角龙？"
    assert registry.last_request.messages[3].content == "我有一道题不会"
    assert registry.last_request.metadata["uses_recent_conversation_history"] is True
    assert registry.last_request.metadata["active_scene"] == "conversation.open"


def test_child_agent_runtime_passes_image_context_to_prompt_and_metadata() -> None:
    registry = CapturingModelRegistry(response=_model_response("这个积木城堡看起来很有想象力。"))
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )

    ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            conversation_metadata={
                "message_id": "msg_runtime_image_context",
                "contains_image": True,
                "image_context": {
                    "attachment_id": "att_image_001",
                    "image_purpose": "share",
                    "recognized_type": "image_observation",
                    "recognized_text": "孩子搭了一个积木城堡",
                    "child_caption": "你看我搭的这个",
                },
            },
        )
    )

    assert registry.last_request is not None
    assert registry.last_request.metadata["contains_image"] is True
    assert "孩子搭了一个积木城堡" in registry.last_request.messages[0].content
    assert "不要把它强行当成作业" in registry.last_request.messages[0].content


def test_child_agent_runtime_repairs_image_refusal_when_context_exists() -> None:
    registry = CapturingModelRegistry(
        response=_model_response("小白狐看不到图片，你可以把图片里的内容说给我听。")
    )
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="你猜猜图上这是什么，它是什么颜色？",
            conversation_metadata={
                "message_id": "msg_runtime_image_context",
                "contains_image": True,
                "image_context": {
                    "attachment_id": "att_image_001",
                    "image_purpose": "share",
                    "recognized_type": "image_observation",
                    "recognized_text": "一个蓝色包装盒，上面有几行中文。",
                    "child_caption": "你看这个",
                },
            },
        )
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert "看不到图片" not in result.reply_text
    assert "蓝色包装盒" in result.reply_text
    assert result.model_metadata["image_context_reply_repaired"] is True


def test_child_agent_runtime_repairs_empty_image_reply_when_context_exists() -> None:
    registry = CapturingModelRegistry(response=_model_response(""))
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="图片都有什么？",
            conversation_metadata={
                "message_id": "msg_runtime_image_context_empty",
                "contains_image": True,
                "image_context": {
                    "attachment_id": "att_image_002",
                    "image_purpose": "share",
                    "recognized_type": "image_observation",
                    "recognized_text": "",
                    "child_caption": "我给小白狐看了一张图",
                },
            },
        )
    )

    assert result.source == AgentRuntimeSource.MODEL
    assert result.fallback_reason is None
    # E3: 确定性模板回复，detail 为空时兜底"一个小东西"
    assert "一个小东西" in result.reply_text
    assert "要不要给它起个名字" in result.reply_text
    assert result.model_metadata["image_context_reply_repaired"] is True


def test_child_agent_runtime_guides_photo_upload_without_claiming_no_image_feature() -> None:
    registry = CapturingModelRegistry(
        response=_model_response("我没有看图功能，只能听你说文字。")
    )
    route_decision = _route_decision(
        active_scene=SceneId.OPEN_CONVERSATION,
        reply_text="我在听。",
    )

    result = ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            route_decision=route_decision,
            child_text="我新买了一个东西，拍照给你看看好不好？",
            conversation_metadata={"message_id": "msg_runtime_image_request"},
        )
    )

    assert "没有看图功能" not in result.reply_text
    assert "给小白狐看看" in result.reply_text


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
        response=_model_response("请告诉家长或可信任的大人。")
    )
    route_decision = _route_decision(
        reply_text="请告诉家长或可信任的大人。",
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
