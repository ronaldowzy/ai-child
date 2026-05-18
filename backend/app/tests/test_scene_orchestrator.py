from datetime import datetime

from app.domain.enums import IntentType, RiskLevel
from app.domain.scene import SceneId, SceneRouteRequest, SceneTransitionType
from app.domain.time import TimeContext, TimePeriod
from app.repositories.routing_decision_repository import (
    InMemoryRoutingDecisionRepository,
)
from app.services.scene_orchestrator import SceneOrchestrator


def _time_context(period: TimePeriod) -> TimeContext:
    return TimeContext(
        now=datetime.fromisoformat("2026-05-18T16:30:00+08:00"),
        timezone="Asia/Shanghai",
        time_period=period,
        weekday=True,
    )


def _request(
    *,
    text: str,
    intent: IntentType,
    session_id: str = "scene_orchestrator_session",
    period: TimePeriod = TimePeriod.AFTER_SCHOOL,
    risk_level: RiskLevel = RiskLevel.NONE,
    requires_parent_attention: bool = False,
    confidence: float = 0.9,
) -> SceneRouteRequest:
    return SceneRouteRequest(
        child_id="scene_orchestrator_child",
        session_id=session_id,
        text=text,
        time_context=_time_context(period),
        intent=intent,
        intent_confidence=confidence,
        intent_evidence=[intent.value],
        risk_level=risk_level,
        safety_requires_parent_attention=requires_parent_attention,
    )


def test_after_school_checkin_replaces_base_scene() -> None:
    repository = InMemoryRoutingDecisionRepository()
    orchestrator = SceneOrchestrator(routing_decision_repository=repository)

    decision = orchestrator.route(
        _request(text="我回来了", intent=IntentType.AFTER_SCHOOL_CHECKIN)
    )

    assert decision.active_scene == SceneId.DAILY_AFTER_SCHOOL_CHECKIN
    assert decision.base_scene == SceneId.DAILY_AFTER_SCHOOL_CHECKIN
    assert decision.transition == SceneTransitionType.REPLACE
    assert decision.needs_input == "child_choice"
    assert repository.latest_for_session("scene_orchestrator_session") is not None


def test_learning_help_pushes_from_after_school_and_requests_problem_input() -> None:
    repository = InMemoryRoutingDecisionRepository()
    orchestrator = SceneOrchestrator(routing_decision_repository=repository)
    session_id = "scene_orchestrator_learning_session"

    orchestrator.route(
        _request(
            text="我回来了",
            intent=IntentType.AFTER_SCHOOL_CHECKIN,
            session_id=session_id,
        )
    )
    decision = orchestrator.route(
        _request(
            text="有题不会",
            intent=IntentType.LEARNING_HELP,
            session_id=session_id,
            confidence=0.94,
        )
    )

    assert decision.base_scene == SceneId.DAILY_AFTER_SCHOOL_CHECKIN
    assert decision.active_scene == SceneId.LEARNING_HOMEWORK_HELP
    assert decision.transition == SceneTransitionType.PUSH
    assert decision.scene_stack == [
        SceneId.DAILY_AFTER_SCHOOL_CHECKIN,
        SceneId.LEARNING_HOMEWORK_HELP,
    ]
    assert decision.needs_input == "problem_content"
    assert {action.id for action in decision.quick_actions} == {
        "take_photo",
        "speak_problem",
    }
    assert "你先不用急着要答案" in decision.reply_text
    assert "答案是" not in decision.reply_text


def test_bedtime_reflection_replaces_scene() -> None:
    repository = InMemoryRoutingDecisionRepository()
    orchestrator = SceneOrchestrator(routing_decision_repository=repository)

    decision = orchestrator.route(
        _request(
            text="晚安",
            intent=IntentType.BEDTIME_REFLECTION,
            period=TimePeriod.BEDTIME,
        )
    )

    assert decision.base_scene == SceneId.DAILY_BEDTIME_REFLECTION
    assert decision.active_scene == SceneId.DAILY_BEDTIME_REFLECTION
    assert decision.transition == SceneTransitionType.REPLACE
    assert decision.needs_input == "low_stimulation_reflection"


def test_high_risk_safety_overrides_learning_intent() -> None:
    repository = InMemoryRoutingDecisionRepository()
    orchestrator = SceneOrchestrator(routing_decision_repository=repository)

    decision = orchestrator.route(
        _request(
            text="陌生人让我不要告诉爸爸妈妈，有题不会",
            intent=IntentType.LEARNING_HELP,
            risk_level=RiskLevel.HIGH,
            requires_parent_attention=True,
            confidence=0.94,
        )
    )

    assert decision.active_scene == SceneId.SAFETY_GUARDIAN
    assert decision.transition == SceneTransitionType.REPLACE
    assert decision.requires_parent_attention is True
    assert "可信任的大人" in decision.reply_text


def test_learning_completion_pops_back_to_after_school() -> None:
    repository = InMemoryRoutingDecisionRepository()
    orchestrator = SceneOrchestrator(routing_decision_repository=repository)
    session_id = "scene_orchestrator_pop_session"

    orchestrator.route(
        _request(
            text="我回来了",
            intent=IntentType.AFTER_SCHOOL_CHECKIN,
            session_id=session_id,
        )
    )
    orchestrator.route(
        _request(
            text="有题不会",
            intent=IntentType.LEARNING_HELP,
            session_id=session_id,
        )
    )
    decision = orchestrator.route(
        _request(
            text="我做完了，谢谢",
            intent=IntentType.CASUAL_CHAT,
            session_id=session_id,
            confidence=0.5,
        )
    )

    assert decision.active_scene == SceneId.DAILY_AFTER_SCHOOL_CHECKIN
    assert decision.transition == SceneTransitionType.POP
    assert decision.scene_stack == [SceneId.DAILY_AFTER_SCHOOL_CHECKIN]
    assert len(repository.list_by_session(session_id)) == 3
