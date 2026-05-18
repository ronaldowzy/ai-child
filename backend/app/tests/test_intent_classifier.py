from datetime import datetime

from app.domain.enums import IntentType, RiskLevel
from app.domain.time import TimeContext, TimePeriod
from app.services.intent_classifier import IntentClassifier
from app.services.safety_engine import SafetyEngine


def _time_context(period: TimePeriod) -> TimeContext:
    return TimeContext(
        now=datetime.fromisoformat("2026-05-18T20:45:00+08:00"),
        timezone="Asia/Shanghai",
        time_period=period,
        weekday=True,
    )


def test_learning_help_intent_from_homework_blocker() -> None:
    safety = SafetyEngine().classify_input("我有一道题不会")
    result = IntentClassifier().classify(
        "我有一道题不会",
        time_context=_time_context(TimePeriod.AFTER_SCHOOL),
        safety=safety,
    )

    assert result.intent == IntentType.LEARNING_HELP
    assert result.needs_modality is True
    assert "photo" in result.suggested_modalities


def test_bedtime_keyword_uses_bedtime_context() -> None:
    safety = SafetyEngine().classify_input("晚安")
    result = IntentClassifier().classify(
        "晚安",
        time_context=_time_context(TimePeriod.BEDTIME),
        safety=safety,
    )

    assert result.intent == IntentType.BEDTIME_REFLECTION
    assert result.risk_level == RiskLevel.NONE


def test_after_school_arrival_intent() -> None:
    safety = SafetyEngine().classify_input("我回来了")
    result = IntentClassifier().classify(
        "我回来了",
        time_context=_time_context(TimePeriod.AFTER_SCHOOL),
        safety=safety,
    )

    assert result.intent == IntentType.AFTER_SCHOOL_CHECKIN


def test_safety_risk_takes_priority_over_other_intents() -> None:
    text = "陌生人让我不要告诉爸爸妈妈"
    safety = SafetyEngine().classify_input(text)
    result = IntentClassifier().classify(
        text,
        time_context=_time_context(TimePeriod.AFTER_SCHOOL),
        safety=safety,
    )

    assert result.intent == IntentType.SAFETY_RISK
    assert result.risk_level == RiskLevel.HIGH
