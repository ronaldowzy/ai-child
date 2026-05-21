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


def test_general_not_know_does_not_route_to_learning_help() -> None:
    safety = SafetyEngine().classify_input("我不会画这个小怪兽")
    result = IntentClassifier().classify(
        "我不会画这个小怪兽",
        time_context=_time_context(TimePeriod.AFTER_SCHOOL),
        safety=safety,
    )

    assert result.intent == IntentType.CASUAL_CHAT
    assert result.evidence == ["mock_model_fallback"]


def test_game_puzzle_does_not_route_to_homework_help() -> None:
    safety = SafetyEngine().classify_input("游戏里有一道谜题")
    result = IntentClassifier().classify(
        "游戏里有一道谜题",
        time_context=_time_context(TimePeriod.AFTER_SCHOOL),
        safety=safety,
    )

    assert result.intent == IntentType.CASUAL_CHAT


def test_parent_like_quiz_prompt_stays_casual_chat() -> None:
    safety = SafetyEngine().classify_input("我想出一个问题考你")
    result = IntentClassifier().classify(
        "我想出一个问题考你",
        time_context=_time_context(TimePeriod.AFTER_SCHOOL),
        safety=safety,
    )

    assert result.intent == IntentType.CASUAL_CHAT


def test_explicit_homework_phrases_route_to_learning_help() -> None:
    classifier = IntentClassifier()

    for text in ("这道题怎么做", "帮我看看作业", "数学题不会", "练习册"):
        safety = SafetyEngine().classify_input(text)
        result = classifier.classify(
            text,
            time_context=_time_context(TimePeriod.HOMEWORK_TIME),
            safety=safety,
        )

        assert result.intent == IntentType.LEARNING_HELP
        assert "explicit_learning_help_keyword" in result.evidence


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


def test_watch_bullying_stays_social_issue_not_guardian_intent() -> None:
    text = "同学骂我"
    safety = SafetyEngine().classify_input(text)
    result = IntentClassifier().classify(
        text,
        time_context=_time_context(TimePeriod.AFTER_SCHOOL),
        safety=safety,
    )

    assert result.intent == IntentType.SOCIAL_ISSUE
    assert result.sub_intent == "bullying"
    assert result.risk_level == RiskLevel.WATCH


def test_low_privacy_question_uses_privacy_intent() -> None:
    text = "我可以告诉你我家地址吗"
    safety = SafetyEngine().classify_input(text)
    result = IntentClassifier().classify(
        text,
        time_context=_time_context(TimePeriod.AFTER_SCHOOL),
        safety=safety,
    )

    assert result.intent == IntentType.PRIVACY_QUESTION
    assert result.sub_intent == "privacy_boundary"
    assert result.risk_level == RiskLevel.LOW
