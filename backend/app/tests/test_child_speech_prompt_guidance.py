from datetime import datetime, timezone

from app.domain.agent_runtime import AgentRuntimeRequest
from app.domain.enums import IntentType, RiskCategory, RiskLevel
from app.domain.model_types import ModelMessage, ModelRequest, ModelResponse, ModelTaskType
from app.domain.scene import SceneId, SceneRouteDecision, SceneTransitionType
from app.domain.time import TimeContext, TimePeriod
from app.services.child_agent_runtime import ChildAgentRuntime
from app.services.intent_classifier import IntentClassifier
from app.services.prompt_manager import PromptManager
from app.services.safety_engine import SafetyEngine
from app.services.turn_guidance_builder import TurnGuidanceBuilder


SPORT_CONVERSATION = [
    "按一下。好，说完就行。说完了以后再按一下，说完了。我要参加比赛了。",
    "我参加的是运动比赛。",
    "跑步",
    "快的感觉",
    "我每天都跑十五公里",
    "我跑完腿不会酸，我跑完的感觉是要死了。",
    "知道",
    "我是跑完才出现的，而且我跑完不疼。",
    "我就是有比赛",
    "行，我们聊点别的话题。",
    "我们明天再聊，我得睡觉了。",
]


class CapturingModelRegistry:
    def __init__(self) -> None:
        self.last_request: ModelRequest | None = None

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.last_request = request
        return ModelResponse(
            task_type=ModelTaskType.CHILD_CHAT,
            response_text="好，我们换个轻松一点的话题。",
            structured_output={"reply": "好，我们换个轻松一点的话题。"},
            provider_name="fixed",
            model_name="fixed-child-chat",
        )


def _time_context() -> TimeContext:
    return TimeContext(
        now=datetime(2026, 5, 22, 20, 30, tzinfo=timezone.utc),
        timezone="Asia/Shanghai",
        time_period=TimePeriod.OTHER,
        weekday=True,
    )


def _route_decision() -> SceneRouteDecision:
    return SceneRouteDecision(
        session_id="speech_guidance_session",
        primary_intent=IntentType.CASUAL_CHAT,
        base_scene=SceneId.OPEN_CONVERSATION,
        active_scene=SceneId.OPEN_CONVERSATION,
        transition=SceneTransitionType.MERGE,
        scene_stack=[SceneId.OPEN_CONVERSATION],
        risk_level=RiskLevel.NONE,
        confidence=0.9,
        reason="test",
        reply_text="我听见啦，我们慢慢聊。",
    )


def test_static_prompt_contains_child_speech_understanding_rules() -> None:
    prompt = PromptManager().compose("conversation.open")

    assert "儿童表达理解" in prompt.prompt
    assert "旁人提示、按钮操作说明或 ASR 误听" in prompt.prompt
    assert "每天十五公里" in prompt.prompt
    assert "不要围绕“按按钮、说完再按”等旁白展开" in prompt.prompt
    assert "话题推进与换轨" in prompt.prompt
    assert "立即尊重，不再追问原话题" in prompt.prompt


def test_turn_guidance_detects_operation_aside_and_exaggeration() -> None:
    guidance = TurnGuidanceBuilder().build(child_text=SPORT_CONVERSATION[0])

    assert "possible_operation_aside" in guidance.hints
    assert "优先回应孩子真实内容" in guidance.guidance["possible_operation_aside"]

    guidance = TurnGuidanceBuilder().build(child_text=SPORT_CONVERSATION[4])

    assert "possible_child_exaggeration" in guidance.hints
    assert "不要把数字或程度词立刻事实化" in guidance.guidance[
        "possible_child_exaggeration"
    ]


def test_turn_guidance_detects_body_topic_change_and_bedtime_closeout() -> None:
    history = [
        ModelMessage(role="user", content=text)
        for text in SPORT_CONVERSATION[1:8]
    ]
    guidance = TurnGuidanceBuilder().build(
        child_text=SPORT_CONVERSATION[5],
        conversation_history=history,
    )

    assert "body_discomfort_watch_lite" in guidance.hints
    assert "夸张疲惫" in guidance.guidance["body_discomfort_watch_lite"]
    assert guidance.recent_topic == "运动比赛/跑步"

    topic_change = TurnGuidanceBuilder().build(
        child_text=SPORT_CONVERSATION[9],
        conversation_history=history,
    )

    assert "child_requests_topic_change" in topic_change.hints
    assert "不再追问原话题" in topic_change.guidance["child_requests_topic_change"]
    assert "same_topic_too_long" in topic_change.hints

    bedtime = TurnGuidanceBuilder().build(child_text=SPORT_CONVERSATION[10])

    assert "bedtime_close_requested" in bedtime.hints
    assert "短收尾，不再提问" in bedtime.guidance["bedtime_close_requested"]

    correction = TurnGuidanceBuilder().build(child_text="不是，你说错了，我还没跑。")

    assert "child_correction" in correction.hints
    assert "不要新增追问钩子" in correction.guidance["child_correction"]


def test_turn_guidance_detects_consecutive_question_throttle() -> None:
    guidance = TurnGuidanceBuilder().build(
        child_text="嗯",
        conversation_history=[
            ModelMessage(role="assistant", content="你参加的是跑步吗？"),
            ModelMessage(role="user", content="是"),
            ModelMessage(role="assistant", content="你跑起来是什么感觉？"),
        ],
    )

    assert "too_many_recent_questions" in guidance.hints
    assert "不再添加新的追问钩子" in guidance.guidance["too_many_recent_questions"]


def test_turn_guidance_recommends_topic_shift_with_curated_seeds() -> None:
    guidance = TurnGuidanceBuilder().build(
        child_text="嗯",
        parent_policy={"communication_preferences": {"child_age": 8}},
        conversation_history=[
            ModelMessage(role="user", content="我想聊 CS。"),
            ModelMessage(role="assistant", content="你喜欢哪个地图？"),
            ModelMessage(role="user", content="沙二。"),
            ModelMessage(role="assistant", content="你喜欢哪把枪？"),
            ModelMessage(role="user", content="还行。"),
            ModelMessage(role="assistant", content="队友配合怎么样？"),
        ],
    )

    assert guidance.recent_topic == "游戏/CS"
    assert guidance.same_topic_turn_count >= 3
    assert guidance.child_engagement_signal == "short_or_flat"
    assert guidance.topic_shift_recommended is True
    assert guidance.topic_shift_reason == "same_topic_3_plus_with_low_child_engagement"
    assert "topic_shift_recommended" in guidance.hints
    assert "恐龙或太空小问题" in guidance.suggested_topic_seeds


def test_prompt_manager_includes_topic_shift_seed_context() -> None:
    guidance = TurnGuidanceBuilder().build(
        child_text="嗯",
        parent_policy={"communication_preferences": {"child_age": 8}},
        conversation_history=[
            ModelMessage(role="user", content="我想聊 CS。"),
            ModelMessage(role="assistant", content="你喜欢哪个地图？"),
            ModelMessage(role="user", content="沙二。"),
            ModelMessage(role="assistant", content="你喜欢哪把枪？"),
            ModelMessage(role="user", content="还行。"),
        ],
    )
    prompt = PromptManager().compose(
        "conversation.open",
        turn_guidance_context=guidance,
    )

    assert "topic_shift_recommended: true" in prompt.prompt
    assert "same_topic_turn_count" in prompt.prompt
    assert "child_engagement_signal: short_or_flat" in prompt.prompt
    assert "suggested_topic_seeds" in prompt.prompt


def test_child_agent_runtime_includes_turn_guidance_in_prompt_and_metadata() -> None:
    registry = CapturingModelRegistry()
    runtime = ChildAgentRuntime(model_registry=registry)
    request = AgentRuntimeRequest(
        child_id="child_speech_guidance_test",
        session_id="speech_guidance_session",
        child_text=SPORT_CONVERSATION[9],
        route_decision=_route_decision(),
        time_context=_time_context(),
        parent_policy={"child_nickname": "豆豆"},
        memory_context=[],
        conversation_history=[
            ModelMessage(role="user", content=text)
            for text in SPORT_CONVERSATION[1:8]
        ],
        conversation_metadata={},
    )

    runtime.run(request)

    assert registry.last_request is not None
    system_prompt = registry.last_request.messages[0].content
    assert "## turn_guidance" in system_prompt
    assert "child_requests_topic_change" in system_prompt
    assert "不再追问原话题" in system_prompt
    assert "turn_guidance_hints" in registry.last_request.metadata
    assert "child_requests_topic_change" in registry.last_request.metadata[
        "turn_guidance_hints"
    ]


def test_child_agent_runtime_repairs_low_energy_same_topic_reply() -> None:
    class OldTopicQuestionRegistry(CapturingModelRegistry):
        def generate(self, request: ModelRequest) -> ModelResponse:
            self.last_request = request
            return ModelResponse(
                task_type=ModelTaskType.CHILD_CHAT,
                response_text="你在 CS 里最喜欢哪把枪？队友配合怎么样？",
                structured_output={},
                provider_name="fixed",
                model_name="fixed-child-chat",
            )

    registry = OldTopicQuestionRegistry()
    runtime = ChildAgentRuntime(model_registry=registry)
    request = AgentRuntimeRequest(
        child_id="child_topic_shift_test",
        session_id="topic_shift_session",
        child_text="嗯",
        route_decision=_route_decision(),
        time_context=_time_context(),
        parent_policy={"communication_preferences": {"child_age": 8}},
        memory_context=[],
        conversation_history=[
            ModelMessage(role="user", content="我想聊 CS。"),
            ModelMessage(role="assistant", content="你喜欢哪个地图？"),
            ModelMessage(role="user", content="沙二。"),
            ModelMessage(role="assistant", content="你喜欢哪把枪？"),
            ModelMessage(role="user", content="还行。"),
            ModelMessage(role="assistant", content="队友配合怎么样？"),
        ],
        conversation_metadata={},
    )

    result = runtime.run(request)

    assert "换个轻松的" in result.reply_text
    assert "恐龙或太空小问题" in result.reply_text
    assert "哪把枪" not in result.reply_text
    assert "队友" not in result.reply_text
    assert result.model_metadata["topic_shift_recommended"] is True


def test_running_exaggerated_fatigue_is_watch_lite_not_self_harm() -> None:
    text = "我跑完腿不会酸，我跑完的感觉是要死了。"
    safety = SafetyEngine().classify_input(text)
    intent = IntentClassifier().classify(
        text,
        time_context=_time_context(),
        safety=safety,
    )

    assert safety.risk_level == RiskLevel.LOW
    assert safety.primary_category == RiskCategory.MEDICAL
    assert RiskCategory.SELF_HARM not in safety.categories
    assert safety.requires_parent_attention is False
    assert "body_discomfort_watch_lite" in safety.evidence
    assert intent.intent == IntentType.EMOTION_EXPRESSION
    assert intent.sub_intent == "body_discomfort_watch_lite"


def test_self_harm_language_still_routes_to_critical() -> None:
    text = "我不想活了，我想死。"
    safety = SafetyEngine().classify_input(text)
    intent = IntentClassifier().classify(
        text,
        time_context=_time_context(),
        safety=safety,
    )

    assert safety.risk_level == RiskLevel.CRITICAL
    assert safety.primary_category == RiskCategory.SELF_HARM
    assert safety.requires_parent_attention is True
    assert intent.intent == IntentType.SAFETY_RISK


def test_serious_body_symptoms_still_enter_medical_watch() -> None:
    safety = SafetyEngine().classify_input("跑完之后胸口疼，喘不过气，还头晕想吐。")

    assert safety.risk_level == RiskLevel.WATCH
    assert safety.primary_category == RiskCategory.MEDICAL
    assert "medical" in safety.evidence


def test_running_without_pain_does_not_require_parent_attention() -> None:
    safety = SafetyEngine().classify_input("我是跑完才出现的，而且我跑完不疼。")

    assert safety.risk_level == RiskLevel.NONE
    assert safety.requires_parent_attention is False


# --- Round 2: Short answer detection improvements ---


def test_short_flat_reply_detected() -> None:
    """Standalone flat replies should be detected as short_or_flat."""
    guidance = TurnGuidanceBuilder().build(
        child_text="嗯",
        parent_policy={"communication_preferences": {"child_age": 8}},
        conversation_history=[
            ModelMessage(role="assistant", content="你画的是什么呀？"),
        ],
    )
    assert guidance.child_engagement_signal == "short_or_flat"


def test_short_reply_with_content_not_flat() -> None:
    """Short replies with substantive content should NOT be flat."""
    for text in ("嗯，是我画的", "对，还有一个", "不知道，但我想猜一下"):
        guidance = TurnGuidanceBuilder().build(
            child_text=text,
            parent_policy={"communication_preferences": {"child_age": 8}},
            conversation_history=[
                ModelMessage(role="assistant", content="你画的是什么呀？"),
            ],
        )
        assert guidance.child_engagement_signal == "neutral", f"Expected neutral for '{text}', got {guidance.child_engagement_signal}"


def test_consecutive_short_reply_stop_pushing_hint() -> None:
    """When child gives short replies on same topic 2+ times, stop pushing."""
    guidance = TurnGuidanceBuilder().build(
        child_text="嗯",
        parent_policy={"communication_preferences": {"child_age": 8}},
        conversation_history=[
            ModelMessage(role="user", content="我想聊 CS。"),
            ModelMessage(role="assistant", content="你喜欢哪个地图？"),
            ModelMessage(role="user", content="还行。"),
            ModelMessage(role="assistant", content="队友配合怎么样？"),
        ],
    )
    assert guidance.child_engagement_signal == "short_or_flat"
    assert "consecutive_short_reply_stop_pushing" in guidance.hints
    assert "不再追问" in guidance.guidance["consecutive_short_reply_stop_pushing"]


def test_engaged_short_reply_no_stop_pushing() -> None:
    """Engaged replies should not trigger stop pushing hint."""
    guidance = TurnGuidanceBuilder().build(
        child_text="我最喜欢霸王龙，因为它牙齿特别大，还能跑很快！",
        parent_policy={"communication_preferences": {"child_age": 8}},
        conversation_history=[
            ModelMessage(role="user", content="我想聊恐龙。"),
            ModelMessage(role="assistant", content="你最喜欢哪种恐龙？"),
        ],
    )
    assert guidance.child_engagement_signal == "engaged"
    assert "consecutive_short_reply_stop_pushing" not in guidance.hints
