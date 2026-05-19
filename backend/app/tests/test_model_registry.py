import pytest

from app.domain.model_types import (
    ModelProfile,
    ModelProviderType,
    ModelRequest,
    ModelResponse,
    ModelTaskType,
)
from app.providers.model.base import BaseModelProvider, ModelProviderError
from app.providers.model.mock_provider import MockModelProvider
from app.providers.model.openai_compatible_provider import OpenAICompatibleProvider
from app.services.model_registry import ModelRegistry


class FixedModelProvider(BaseModelProvider):
    def generate(
        self,
        request: ModelRequest,
        *,
        profile: ModelProfile | None = None,
    ) -> ModelResponse:
        return ModelResponse(
            task_type=request.task_type,
            response_text="fixed provider response",
            structured_output={"source": "fixed"},
            provider_name=self.provider_name,
            model_name=profile.model_name if profile else "fixed-model",
        )


class FailingModelProvider(BaseModelProvider):
    def generate(
        self,
        request: ModelRequest,
        *,
        profile: ModelProfile | None = None,
    ) -> ModelResponse:
        raise ModelProviderError("simulated provider failure")


def _profile(
    *,
    profile_name: str,
    provider_name: str,
    task_type: ModelTaskType = ModelTaskType.CHILD_CHAT,
    provider_type: ModelProviderType = ModelProviderType.MOCK,
    fallback_profile_name: str | None = None,
    enabled: bool = True,
) -> ModelProfile:
    return ModelProfile(
        id=profile_name,
        profile_name=profile_name,
        provider_name=provider_name,
        provider_type=provider_type,
        model_name=f"{profile_name}-model",
        task_type=task_type,
        enabled=enabled,
        fallback_profile_name=fallback_profile_name,
    )


def test_model_registry_select_returns_default_mock_provider_for_child_chat() -> None:
    registry = ModelRegistry()

    provider = registry.select(ModelTaskType.CHILD_CHAT)
    response = registry.generate(
        ModelRequest(
            task_type=ModelTaskType.CHILD_CHAT,
            input_text="我回来了",
        )
    )

    assert isinstance(provider, MockModelProvider)
    assert response.provider_name == "mock"
    assert response.model_name == "mock-child-chat-v0"


def test_model_registry_can_switch_child_chat_profile_by_configuration() -> None:
    registry = ModelRegistry(
        providers={
            "fixed": FixedModelProvider(provider_name="fixed"),
        },
        profiles={
            "custom_child_chat": _profile(
                profile_name="custom_child_chat",
                provider_name="fixed",
            )
        },
        task_profile_map={ModelTaskType.CHILD_CHAT: "custom_child_chat"},
    )

    provider = registry.select(ModelTaskType.CHILD_CHAT)
    response = registry.generate(ModelRequest(task_type=ModelTaskType.CHILD_CHAT))

    assert isinstance(provider, FixedModelProvider)
    assert response.provider_name == "fixed"
    assert response.model_name == "custom_child_chat-model"
    assert response.structured_output == {"source": "fixed"}


def test_model_registry_falls_back_when_provider_raises_error() -> None:
    registry = ModelRegistry(
        providers={
            "broken": FailingModelProvider(provider_name="broken"),
            "mock": MockModelProvider(provider_name="mock"),
        },
        profiles={
            "broken_child_chat": _profile(
                profile_name="broken_child_chat",
                provider_name="broken",
                fallback_profile_name="child_chat_primary",
            ),
            "child_chat_primary": _profile(
                profile_name="child_chat_primary",
                provider_name="mock",
            ),
        },
        task_profile_map={ModelTaskType.CHILD_CHAT: "broken_child_chat"},
    )

    response = registry.generate(
        ModelRequest(task_type=ModelTaskType.CHILD_CHAT, input_text="你好")
    )

    assert response.provider_name == "mock"
    assert response.model_name == "child_chat_primary-model"
    assert response.metadata["fallback_used"] is True
    assert response.metadata["failed_provider"] == "broken"


def test_model_registry_uses_fallback_when_primary_provider_is_disabled() -> None:
    registry = ModelRegistry(
        providers={
            "openai_disabled": OpenAICompatibleProvider(
                provider_name="openai_disabled"
            ),
            "mock": MockModelProvider(provider_name="mock"),
        },
        profiles={
            "openai_child_chat": _profile(
                profile_name="openai_child_chat",
                provider_name="openai_disabled",
                provider_type=ModelProviderType.OPENAI_COMPATIBLE,
                fallback_profile_name="child_chat_primary",
            ),
            "child_chat_primary": _profile(
                profile_name="child_chat_primary",
                provider_name="mock",
            ),
        },
        task_profile_map={ModelTaskType.CHILD_CHAT: "openai_child_chat"},
    )

    provider = registry.select(ModelTaskType.CHILD_CHAT)
    response = registry.generate(ModelRequest(task_type=ModelTaskType.CHILD_CHAT))

    assert isinstance(provider, MockModelProvider)
    assert response.provider_name == "mock"
    assert response.metadata["fallback_used"] is True
    assert response.metadata["failed_provider"] == "openai_disabled"


def test_model_registry_keeps_mimo_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CHILD_AI_MODEL_PROVIDER", "mimo")
    monkeypatch.delenv("CHILD_AI_MIMO_ENABLED", raising=False)

    registry = ModelRegistry()
    provider = registry.select(ModelTaskType.CHILD_CHAT)
    response = registry.generate(ModelRequest(task_type=ModelTaskType.CHILD_CHAT))

    assert isinstance(provider, MockModelProvider)
    assert response.provider_name == "mock"
    assert response.metadata["fallback_used"] is True
    assert response.metadata["failed_provider"] == "mimo"


def test_model_registry_can_register_enabled_mimo_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CHILD_AI_MODEL_PROVIDER", "mimo")
    monkeypatch.setenv("CHILD_AI_MIMO_ENABLED", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_MODEL", "mimo-v2.5pro")
    monkeypatch.delenv("CHILD_AI_MIMO_API_KEY", raising=False)

    registry = ModelRegistry()
    profile = registry.select_profile(ModelTaskType.CHILD_CHAT)
    response = registry.generate(ModelRequest(task_type=ModelTaskType.CHILD_CHAT))

    assert profile.profile_name == "mimo_child_chat"
    assert profile.model_name == "mimo-v2.5pro"
    assert profile.fallback_profile_name == "child_chat_primary"
    assert response.provider_name == "mock"
    assert response.metadata["fallback_used"] is True
    assert response.metadata["failure_type"] == "ModelProviderConfigurationError"
