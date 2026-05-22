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
