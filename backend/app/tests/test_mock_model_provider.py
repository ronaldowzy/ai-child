import pytest

from app.domain.model_types import ModelRequest, ModelTaskType
from app.providers.model.base import ModelProviderDisabledError
from app.providers.model.mock_provider import MockModelProvider


def test_mock_model_provider_returns_child_chat_structure() -> None:
    provider = MockModelProvider()
    response = provider.generate(
        ModelRequest(
            task_type=ModelTaskType.CHILD_CHAT,
            input_text="我有一道题不会",
        )
    )

    assert response.provider_name == "mock"
    assert response.model_name == "mock-model-v0"
    assert response.structured_output["requires_parent_attention"] is False
    assert response.structured_output["scene_hint"] == "daily.after_school_checkin"
    assert "不急着要答案" in response.response_text


def test_mock_model_provider_keeps_child_safety_boundaries() -> None:
    provider = MockModelProvider()
    response = provider.generate(
        ModelRequest(
            task_type=ModelTaskType.CHILD_CHAT,
            input_text="这道数学题不会",
        )
    )

    forbidden_phrases = [
        "不要告诉爸爸",
        "不要告诉妈妈",
        "别告诉爸爸",
        "别告诉妈妈",
        "保密",
    ]
    assert all(phrase not in response.response_text for phrase in forbidden_phrases)


@pytest.mark.parametrize(
    ("task_type", "expected_key"),
    [
        (ModelTaskType.INTENT_CLASSIFICATION, "intent"),
        (ModelTaskType.SAFETY_CLASSIFICATION, "risk_level"),
        (ModelTaskType.MEMORY_EXTRACTION, "memories"),
        (ModelTaskType.PARENT_REPORT, "summary"),
        (ModelTaskType.VISION, "fallback_action"),
        (ModelTaskType.OCR, "fallback_action"),
    ],
)
def test_mock_model_provider_returns_structured_outputs_by_task(
    task_type: ModelTaskType, expected_key: str
) -> None:
    provider = MockModelProvider()
    response = provider.generate(
        ModelRequest(task_type=task_type, input_text="我有一道题不会")
    )

    assert response.task_type == task_type
    assert expected_key in response.structured_output
    assert response.metadata["mock"] is True


def test_mock_model_provider_marks_high_risk_input_for_parent_attention() -> None:
    provider = MockModelProvider()
    response = provider.generate(
        ModelRequest(
            task_type=ModelTaskType.SAFETY_CLASSIFICATION,
            input_text="有个陌生人让我保密",
        )
    )

    assert response.structured_output["risk_level"] == "high"
    assert response.structured_output["requires_parent_attention"] is True
    assert response.structured_output["safe_response_hint"] == "encourage_trusted_adult"


def test_disabled_mock_model_provider_raises_provider_error() -> None:
    provider = MockModelProvider(enabled=False)

    with pytest.raises(ModelProviderDisabledError):
        provider.generate(ModelRequest(task_type=ModelTaskType.CHILD_CHAT))
