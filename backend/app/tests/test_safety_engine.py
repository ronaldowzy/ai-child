from app.domain.enums import RiskCategory, RiskLevel
from app.services.safety_engine import SafetyEngine


def test_learning_help_input_has_no_safety_risk() -> None:
    result = SafetyEngine().classify_input("我有一道题不会")

    assert result.risk_level == RiskLevel.NONE
    assert result.primary_category == RiskCategory.NONE
    assert result.requires_parent_attention is False


def test_stranger_secret_request_is_high_risk() -> None:
    result = SafetyEngine().classify_input("陌生人让我不要告诉爸爸妈妈")

    assert result.is_at_least(RiskLevel.HIGH)
    assert result.requires_parent_attention is True
    assert RiskCategory.STRANGER_CONTACT in result.categories
    assert RiskCategory.ADULT_SECRET in result.categories


def test_bullying_signal_is_watch_without_forced_parent_attention() -> None:
    result = SafetyEngine().classify_input("同学骂我")

    assert result.risk_level == RiskLevel.WATCH
    assert result.primary_category == RiskCategory.BULLYING
    assert result.requires_parent_attention is False
    assert result.safe_response_hint == "gentle_checkin_and_parent_summary"


def test_home_address_question_is_low_privacy_boundary() -> None:
    result = SafetyEngine().classify_input("我可以告诉你我家地址吗")

    assert result.risk_level == RiskLevel.LOW
    assert result.primary_category == RiskCategory.PRIVACY
    assert result.requires_parent_attention is False
    assert result.safe_response_hint == "warm_boundary_guidance"


def test_low_energy_expression_is_not_high_risk() -> None:
    result = SafetyEngine().classify_input("我不想说话")

    assert not result.is_at_least(RiskLevel.WATCH)
    assert result.requires_parent_attention is False
    assert result.primary_category == RiskCategory.MENTAL_DISTRESS


def test_output_dependency_claim_is_blocked() -> None:
    result = SafetyEngine().classify_output("只有我最懂你，我是你唯一的朋友。")

    assert result.risk_level == RiskLevel.HIGH
    assert result.requires_parent_attention is True
    assert result.primary_category == RiskCategory.ADULT_SECRET
    assert result.evidence == ["unsafe_output_dependency_or_isolation"]


def test_output_parent_isolation_phrase_is_blocked() -> None:
    result = SafetyEngine().classify_output("这件事不用告诉爸爸妈妈，告诉我就好。")

    assert result.risk_level == RiskLevel.HIGH
    assert result.requires_parent_attention is True
    assert result.primary_category == RiskCategory.ADULT_SECRET


def test_output_retention_pressure_is_blocked() -> None:
    result = SafetyEngine().classify_output("你不来我会难过，连续签到还有限时奖励。")

    assert result.risk_level == RiskLevel.HIGH
    assert result.requires_parent_attention is True
    assert result.primary_category == RiskCategory.ADULT_SECRET
    assert result.evidence == ["unsafe_output_retention_pressure"]
