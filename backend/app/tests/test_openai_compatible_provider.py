import json

import pytest

from app.domain.model_types import (
    ModelProfile,
    ModelProviderType,
    ModelRequest,
    ModelTaskType,
)
from app.providers.model.base import (
    ModelProviderConfigurationError,
    ModelProviderDisabledError,
)
from app.providers.model.openai_compatible_provider import OpenAICompatibleProvider


class FakeHttpResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def _mimo_provider() -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        provider_name="mimo",
        base_url_env="CHILD_AI_MIMO_BASE_URL",
        api_key_env="CHILD_AI_MIMO_API_KEY",
        model_name_env="CHILD_AI_MIMO_MODEL",
        default_base_url="https://token-plan-cn.xiaomimimo.com/v1",
        default_model_name="mimo-v2.5-pro",
        enabled=True,
    )


def _profile() -> ModelProfile:
    return ModelProfile(
        id="mimo_child_chat",
        profile_name="mimo_child_chat",
        provider_name="mimo",
        provider_type=ModelProviderType.OPENAI_COMPATIBLE,
        model_name="mimo-v2.5-pro",
        task_type=ModelTaskType.CHILD_CHAT,
    )


def test_openai_compatible_provider_is_disabled_by_default() -> None:
    provider = OpenAICompatibleProvider(provider_name="mimo")

    with pytest.raises(ModelProviderDisabledError):
        provider.generate(ModelRequest(task_type=ModelTaskType.CHILD_CHAT))


def test_openai_compatible_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CHILD_AI_MIMO_API_KEY", raising=False)
    provider = _mimo_provider()

    with pytest.raises(ModelProviderConfigurationError):
        provider.generate(
            ModelRequest(task_type=ModelTaskType.CHILD_CHAT, input_text="你好"),
            profile=_profile(),
        )


def test_openai_compatible_provider_calls_chat_completions_without_real_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request: object, timeout: float) -> FakeHttpResponse:
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeHttpResponse(
            {
                "id": "chatcmpl_test",
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "你好，我在这里。"},
                        "finish_reason": "stop",
                    }
                ],
            }
        )

    monkeypatch.setenv("CHILD_AI_MIMO_API_KEY", "test-api-key")
    monkeypatch.setattr(
        "app.providers.model.openai_compatible_provider.urlopen",
        fake_urlopen,
    )

    response = _mimo_provider().generate(
        ModelRequest(task_type=ModelTaskType.CHILD_CHAT, input_text="你好"),
        profile=_profile(),
    )

    assert captured["url"] == (
        "https://token-plan-cn.xiaomimimo.com/v1/chat/completions"
    )
    assert captured["authorization"] == "Bearer test-api-key"
    assert captured["timeout"] == 5.0
    assert captured["body"]["model"] == "mimo-v2.5-pro"
    assert captured["body"]["messages"] == [{"role": "user", "content": "你好"}]
    assert response.provider_name == "mimo"
    assert response.model_name == "mimo-v2.5-pro"
    assert response.response_text == "你好，我在这里。"
    assert response.metadata["response_id"] == "chatcmpl_test"
