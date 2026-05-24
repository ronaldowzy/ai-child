import json
import logging
from datetime import datetime, timezone

from app.domain.agent_runtime import AgentRuntimeRequest
from app.domain.enums import IntentType, RiskLevel
from app.domain.model_types import ModelMessage, ModelRequest, ModelResponse, ModelTaskType
from app.domain.scene import SceneId, SceneRouteDecision, SceneTransitionType
from app.domain.schemas.conversation import (
    ClientContext,
    ConversationInput,
    ConversationMessageRequest,
)
from app.domain.time import TimeContext, TimePeriod
from app.services import conversation_service as conversation_service_module
from app.services.child_agent_runtime import ChildAgentRuntime
from app.services.conversation_service import ConversationService


class CapturingModelRegistry:
    def __init__(self, reply_text: str) -> None:
        self.reply_text = reply_text
        self.last_request: ModelRequest | None = None

    def generate(self, request: ModelRequest) -> ModelResponse:
        self.last_request = request
        return ModelResponse(
            task_type=ModelTaskType.CHILD_CHAT,
            response_text=self.reply_text,
            structured_output={"reply": self.reply_text},
            provider_name="fixed",
            model_name="fixed-child-chat",
            metadata={},
        )


def _time_context() -> TimeContext:
    return TimeContext(
        now=datetime(2026, 5, 24, 20, 30, tzinfo=timezone.utc),
        timezone="Asia/Shanghai",
        time_period=TimePeriod.OTHER,
        weekday=False,
    )


def _route_decision(
    *,
    active_scene: SceneId = SceneId.OPEN_CONVERSATION,
    reply_text: str = "我听见了。",
) -> SceneRouteDecision:
    return SceneRouteDecision(
        session_id="healthy_observability_session",
        primary_intent=IntentType.CASUAL_CHAT,
        base_scene=active_scene,
        active_scene=active_scene,
        transition=SceneTransitionType.MERGE,
        scene_stack=[active_scene],
        risk_level=RiskLevel.NONE,
        confidence=0.9,
        reason="healthy_observability_test",
        reply_text=reply_text,
    )


def _runtime_request(
    *,
    child_text: str,
    conversation_history: list[ModelMessage] | None = None,
) -> AgentRuntimeRequest:
    return AgentRuntimeRequest(
        child_id="healthy_child",
        session_id="healthy_observability_session",
        child_text=child_text,
        route_decision=_route_decision(),
        time_context=_time_context(),
        parent_policy={"version": 2, "child_age": 8},
        memory_context=[],
        conversation_history=conversation_history or [],
        conversation_metadata={},
    )


def _run_with_reply(
    *,
    child_text: str,
    reply_text: str,
    conversation_history: list[ModelMessage] | None = None,
):
    registry = CapturingModelRegistry(reply_text)
    return ChildAgentRuntime(model_registry=registry).run(
        _runtime_request(
            child_text=child_text,
            conversation_history=conversation_history,
        )
    )


def test_healthy_metrics_detect_no_chat_boundary_without_raw_text() -> None:
    child_text = "不聊了，我们换个话题吧。"
    reply_text = "好，我们换一个轻松的。"

    result = _run_with_reply(child_text=child_text, reply_text=reply_text)

    metrics = result.model_metadata["healthy_engagement"]
    assert metrics["boundary_signal"] == "no_chat"
    assert metrics["boundary_respected"] is True
    assert metrics["question_count"] == 0
    assert "child_requests_topic_change" in metrics["turn_guidance_hints"]
    serialized = json.dumps(metrics, ensure_ascii=False)
    assert child_text not in serialized
    assert reply_text not in serialized


def test_healthy_metrics_detect_bedtime_closeout() -> None:
    result = _run_with_reply(
        child_text="我要睡觉了，晚安。",
        reply_text="晚安，明天还想聊什么？",
    )

    metrics = result.model_metadata["healthy_engagement"]
    assert result.reply_text == ChildAgentRuntime.BEDTIME_CLOSE_REPLY
    assert metrics["boundary_signal"] == "bedtime"
    assert metrics["boundary_respected"] is True
    assert metrics["question_count"] == 0
    assert metrics["reply_normalized"] is True


def test_healthy_metrics_count_consecutive_recent_questions() -> None:
    result = _run_with_reply(
        child_text="嗯",
        reply_text="我听见了，我们先停一下。",
        conversation_history=[
            ModelMessage(role="assistant", content="你喜欢霸王龙吗？"),
            ModelMessage(role="user", content="喜欢"),
            ModelMessage(role="assistant", content="那你还喜欢三角龙吗？"),
        ],
    )

    metrics = result.model_metadata["healthy_engagement"]
    assert metrics["consecutive_recent_questions"] == 2
    assert "too_many_recent_questions" in metrics["turn_guidance_hints"]
    assert metrics["recent_history_turns"] == 3


def test_healthy_metrics_do_not_store_raw_child_or_reply_text() -> None:
    child_text = "这是一段不应该进入观测日志的儿童原文。"
    reply_text = "这是一段不应该进入观测日志的小白狐回复全文。"

    result = _run_with_reply(child_text=child_text, reply_text=reply_text)

    serialized = json.dumps(
        result.model_metadata["healthy_engagement"],
        ensure_ascii=False,
    )
    assert child_text not in serialized
    assert reply_text not in serialized
    assert "reply_char_count" in serialized
    assert "question_count" in serialized


def test_healthy_telemetry_failure_does_not_break_response(monkeypatch) -> None:
    def raise_on_info(*_args, **_kwargs):
        raise RuntimeError("telemetry sink unavailable")

    monkeypatch.setattr(
        conversation_service_module.healthy_engagement_logger,
        "info",
        raise_on_info,
    )
    service = ConversationService(
        debug_enabled=True,
        persistence_enabled=False,
    )

    response = service.handle_message(
        ConversationMessageRequest(
            child_id="healthy_log_failure_child",
            session_id="healthy_log_failure_session",
            input=ConversationInput(text="我们换个话题吧。"),
            client_context=ClientContext(
                deviceTime=datetime(2026, 5, 24, 20, 30, tzinfo=timezone.utc),
                timezone="Asia/Shanghai",
                appMode="child",
            ),
        )
    )

    assert response.reply.text
    assert response.debug is not None
    assert response.debug.healthy_engagement is not None


def test_healthy_engagement_log_payload_is_structured_and_non_sensitive(caplog) -> None:
    raw_child_text = "这句儿童原文不能进日志。"
    caplog.set_level(logging.INFO, logger="app.healthy_engagement")
    service = ConversationService(
        debug_enabled=True,
        persistence_enabled=False,
    )

    response = service.handle_message(
        ConversationMessageRequest(
            child_id="healthy_log_payload_child",
            session_id="healthy_log_payload_session",
            input=ConversationInput(text=raw_child_text),
            client_context=ClientContext(
                deviceTime=datetime(2026, 5, 24, 20, 30, tzinfo=timezone.utc),
                timezone="Asia/Shanghai",
                appMode="child",
            ),
        )
    )

    records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "healthy_engagement_turn"
    ]
    assert records
    record = records[-1]
    assert record.active_scene
    assert record.age_band
    assert record.reply_char_count == len(response.reply.text)
    assert record.turn_total_ms is not None
    assert record.child_id_hash
    assert record.session_id_hash
    assert raw_child_text not in caplog.text
    assert response.reply.text not in caplog.text
