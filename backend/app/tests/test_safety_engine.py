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


def test_low_energy_expression_is_not_high_risk() -> None:
    result = SafetyEngine().classify_input("我不想说话")

    assert not result.is_at_least(RiskLevel.WATCH)
    assert result.requires_parent_attention is False
    assert result.primary_category == RiskCategory.MENTAL_DISTRESS
