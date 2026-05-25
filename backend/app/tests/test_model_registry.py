import json

import pytest

from app.domain.model_types import (
    ModelDataPolicy,
    ModelProfile,
    ModelProviderType,
    ModelRequest,
    ModelResponse,
    ModelTaskType,
)
from app.providers.model.base import BaseModelProvider, ModelProviderError
from app.providers.model.mock_provider import MockModelProvider
from app.providers.model.openai_compatible_provider import OpenAICompatibleProvider
from app.services.model_registry import ModelRegistry, ModelRegistryError


class FakeHttpResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


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
    data_policy: ModelDataPolicy | None = None,
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
        data_policy=data_policy or ModelDataPolicy(),
    )


def _fake_mimo_response() -> dict[str, object]:
    return {
        "id": "chatcmpl_registry_test",
        "choices": [
            {
                "message": {"role": "assistant", "content": "fake mimo response"},
                "finish_reason": "stop",
            }
        ],
    }


def _enable_mimo_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHILD_AI_MODEL_PROVIDER", "mimo")
    monkeypatch.setenv("CHILD_AI_MIMO_ENABLED", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_MODEL", "mimo-v2.5-pro")
    monkeypatch.setenv("CHILD_AI_MIMO_API_KEY", "test-api-key")
    monkeypatch.setenv("CHILD_AI_MIMO_TIMEOUT_MS", "5000")


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
    monkeypatch.setenv("CHILD_AI_MIMO_MODEL", "mimo-v2.5-pro")
    monkeypatch.delenv("CHILD_AI_MIMO_API_KEY", raising=False)

    registry = ModelRegistry()
    profile = registry.select_profile(ModelTaskType.CHILD_CHAT)
    response = registry.generate(ModelRequest(task_type=ModelTaskType.CHILD_CHAT))

    assert profile.profile_name == "mimo_child_chat"
    assert profile.model_name == "mimo-v2.5-pro"
    assert profile.fallback_profile_name is None
    assert response.provider_name == "mock"
    assert response.metadata["fallback_used"] is True
    assert response.metadata["failure_type"] == "ModelProviderConfigurationError"


def test_model_registry_blocks_mimo_child_data_without_allow_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_mimo_env(monkeypatch)
    monkeypatch.setenv("CHILD_AI_MIMO_ALLOW_CHILD_DATA", "false")
    monkeypatch.setenv("CHILD_AI_MIMO_RETENTION_POLICY_CHECKED", "true")

    def fail_if_called(_request: object, timeout: float) -> FakeHttpResponse:
        raise AssertionError(f"urlopen should not be called, timeout={timeout}")

    monkeypatch.setattr(
        "app.providers.model.openai_compatible_provider.urlopen",
        fail_if_called,
    )

    response = ModelRegistry().generate(
        ModelRequest(
            task_type=ModelTaskType.CHILD_CHAT,
            input_text="fictional child-facing message",
            metadata={"contains_child_data": True},
        )
    )

    assert response.provider_name == "mock"
    assert response.metadata["fallback_used"] is True
    assert response.metadata["policy_blocked"] is True
    assert response.metadata["failed_provider"] == "mimo"
    assert response.metadata["failed_profile"] == "mimo_child_chat"
    assert response.metadata["failure_type"] == "ModelDataPolicyBlockedError"


def test_model_registry_blocks_mimo_child_data_without_retention_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_mimo_env(monkeypatch)
    monkeypatch.setenv("CHILD_AI_MIMO_ALLOW_CHILD_DATA", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_RETENTION_POLICY_CHECKED", "false")

    def fail_if_called(_request: object, timeout: float) -> FakeHttpResponse:
        raise AssertionError(f"urlopen should not be called, timeout={timeout}")

    monkeypatch.setattr(
        "app.providers.model.openai_compatible_provider.urlopen",
        fail_if_called,
    )

    response = ModelRegistry().generate(
        ModelRequest(
            task_type=ModelTaskType.CHILD_CHAT,
            input_text="fictional child-facing message",
            metadata={"contains_child_data": True},
        )
    )

    assert response.provider_name == "mock"
    assert response.metadata["policy_blocked"] is True
    assert response.metadata["failure_type"] == "ModelDataPolicyBlockedError"


def test_model_registry_allows_mimo_child_data_when_policy_is_complete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    _enable_mimo_env(monkeypatch)
    monkeypatch.setenv("CHILD_AI_MIMO_ALLOW_CHILD_DATA", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_RETENTION_POLICY_CHECKED", "true")

    def fake_urlopen(request: object, timeout: float) -> FakeHttpResponse:
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeHttpResponse(_fake_mimo_response())

    monkeypatch.setattr(
        "app.providers.model.openai_compatible_provider.urlopen",
        fake_urlopen,
    )

    response = ModelRegistry().generate(
        ModelRequest(
            task_type=ModelTaskType.CHILD_CHAT,
            input_text="fictional child-facing message",
            metadata={"contains_child_data": True},
        )
    )

    assert captured["url"] == (
        "https://token-plan-cn.xiaomimimo.com/v1/chat/completions"
    )
    assert captured["timeout"] == 5.0
    assert captured["body"]["model"] == "mimo-v2.5-pro"
    assert captured["body"]["max_completion_tokens"] == 800
    assert "max_tokens" not in captured["body"]
    assert response.provider_name == "mimo"
    assert response.response_text == "fake mimo response"
    assert "policy_blocked" not in response.metadata


@pytest.mark.parametrize(
    ("metadata_key", "allow_env"),
    [
        ("contains_image", "CHILD_AI_MIMO_ALLOW_IMAGE"),
        ("contains_audio", "CHILD_AI_MIMO_ALLOW_AUDIO"),
    ],
)
def test_model_registry_blocks_mimo_image_and_audio_without_explicit_policy(
    monkeypatch: pytest.MonkeyPatch,
    metadata_key: str,
    allow_env: str,
) -> None:
    _enable_mimo_env(monkeypatch)
    monkeypatch.setenv("CHILD_AI_MIMO_ALLOW_CHILD_DATA", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_RETENTION_POLICY_CHECKED", "true")
    monkeypatch.setenv(allow_env, "false")

    def fail_if_called(_request: object, timeout: float) -> FakeHttpResponse:
        raise AssertionError(f"urlopen should not be called, timeout={timeout}")

    monkeypatch.setattr(
        "app.providers.model.openai_compatible_provider.urlopen",
        fail_if_called,
    )

    response = ModelRegistry().generate(
        ModelRequest(
            task_type=ModelTaskType.CHILD_CHAT,
            input_text="fictional multimodal message",
            metadata={metadata_key: True},
        )
    )

    assert response.provider_name == "mock"
    assert response.metadata["policy_blocked"] is True
    assert response.metadata["failure_type"] == "ModelDataPolicyBlockedError"


def test_model_registry_can_route_vision_to_mimo_with_multimodal_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    _enable_mimo_env(monkeypatch)
    monkeypatch.setenv("CHILD_AI_VISION_PROVIDER", "mimo")
    monkeypatch.setenv("CHILD_AI_MIMO_ALLOW_IMAGE", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_RETENTION_POLICY_CHECKED", "true")

    def fake_urlopen(request: object, timeout: float) -> FakeHttpResponse:
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeHttpResponse(_fake_mimo_response())

    monkeypatch.setattr(
        "app.providers.model.openai_compatible_provider.urlopen",
        fake_urlopen,
    )

    response = ModelRegistry().generate(
        ModelRequest(
            task_type=ModelTaskType.VISION,
            input_text="请描述图片。",
            metadata={
                "contains_image": True,
                "image_data_uri": "data:image/png;base64,ZmFrZQ==",
            },
        )
    )

    content = captured["body"]["messages"][0]["content"]
    assert isinstance(content, list)
    assert captured["body"]["model"] == "mimo-v2.5"
    assert captured["body"]["max_completion_tokens"] == 800
    assert content[0]["type"] == "image_url"
    assert content[1]["type"] == "text"
    assert response.provider_name == "mimo"


def test_model_registry_can_route_parent_report_to_mimo_without_changing_child_chat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_mimo_env(monkeypatch)
    monkeypatch.setenv("CHILD_AI_MODEL_PROVIDER", "mock")
    monkeypatch.setenv("CHILD_AI_PARENT_REPORT_PROVIDER", "mimo")
    monkeypatch.setenv("CHILD_AI_MIMO_ALLOW_CHILD_DATA", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_RETENTION_POLICY_CHECKED", "true")

    registry = ModelRegistry()

    child_profile = registry.select_profile(ModelTaskType.CHILD_CHAT)
    parent_report_profile = registry.select_profile(ModelTaskType.PARENT_REPORT)
    vision_profile = registry.select_profile(ModelTaskType.VISION)

    assert child_profile.profile_name == "child_chat_primary"
    assert parent_report_profile.profile_name == "mimo_parent_report"
    assert parent_report_profile.model_name == "mimo-v2.5-pro"
    assert parent_report_profile.default_params.max_tokens == 6000
    assert parent_report_profile.default_params.timeout_ms == 90000
    assert vision_profile.profile_name == "vision_mock"


def test_model_registry_blocks_mimo_vision_without_retention_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_mimo_env(monkeypatch)
    monkeypatch.setenv("CHILD_AI_VISION_PROVIDER", "mimo")
    monkeypatch.setenv("CHILD_AI_MIMO_ALLOW_IMAGE", "true")
    monkeypatch.setenv("CHILD_AI_MIMO_RETENTION_POLICY_CHECKED", "false")

    def fail_if_called(_request: object, timeout: float) -> FakeHttpResponse:
        raise AssertionError(f"urlopen should not be called, timeout={timeout}")

    monkeypatch.setattr(
        "app.providers.model.openai_compatible_provider.urlopen",
        fail_if_called,
    )

    response = ModelRegistry().generate(
        ModelRequest(
            task_type=ModelTaskType.VISION,
            input_text="请描述图片。",
            metadata={
                "contains_image": True,
                "image_data_uri": "data:image/png;base64,ZmFrZQ==",
            },
        )
    )

    assert response.provider_name == "mock"
    assert response.metadata["policy_blocked"] is True
    assert response.metadata["failed_profile"] == "mimo_vision"
    assert response.metadata["failure_type"] == "ModelDataPolicyBlockedError"


def test_model_registry_mock_provider_is_not_blocked_by_data_policy() -> None:
    registry = ModelRegistry(
        providers={"mock": MockModelProvider(provider_name="mock")},
        profiles={
            "mock_child_chat": _profile(
                profile_name="mock_child_chat",
                provider_name="mock",
                provider_type=ModelProviderType.MOCK,
                data_policy=ModelDataPolicy(
                    external_transmission=True,
                    allow_child_data=False,
                    allow_image=False,
                    allow_audio=False,
                    retention_policy_checked=False,
                ),
            )
        },
        task_profile_map={ModelTaskType.CHILD_CHAT: "mock_child_chat"},
    )

    response = registry.generate(
        ModelRequest(
            task_type=ModelTaskType.CHILD_CHAT,
            input_text="fictional mock-only message",
            metadata={
                "contains_child_data": True,
                "contains_image": True,
                "contains_audio": True,
            },
        )
    )

    assert response.provider_name == "mock"
    assert "policy_blocked" not in response.metadata


def test_model_registry_raises_when_policy_block_has_no_mock_fallback() -> None:
    registry = ModelRegistry(
        providers={"fixed": FixedModelProvider(provider_name="fixed")},
        profiles={
            "external_child_chat": _profile(
                profile_name="external_child_chat",
                provider_name="fixed",
                provider_type=ModelProviderType.OPENAI_COMPATIBLE,
                data_policy=ModelDataPolicy(
                    external_transmission=True,
                    allow_child_data=False,
                    retention_policy_checked=True,
                ),
            )
        },
        task_profile_map={ModelTaskType.CHILD_CHAT: "external_child_chat"},
    )

    with pytest.raises(ModelRegistryError, match="without an enabled mock fallback"):
        registry.generate(
            ModelRequest(
                task_type=ModelTaskType.CHILD_CHAT,
                input_text="fictional child-facing message",
                metadata={"contains_child_data": True},
            )
        )
