import os
import json
import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.domain.model_types import ModelProfile, ModelRequest, ModelResponse
from app.providers.model.base import (
    BaseModelProvider,
    ModelProviderConfigurationError,
    ModelProviderDisabledError,
    ModelProviderError,
    ModelProviderTimeoutError,
)


class OpenAICompatibleProvider(BaseModelProvider):
    def __init__(
        self,
        *,
        provider_name: str = "openai_compatible",
        base_url_env: str | None = None,
        api_key_env: str | None = None,
        model_name_env: str | None = None,
        default_base_url: str | None = None,
        default_model_name: str | None = None,
        enabled: bool = False,
    ) -> None:
        super().__init__(provider_name=provider_name, enabled=enabled)
        self.base_url_env = base_url_env
        self.api_key_env = api_key_env
        self.model_name_env = model_name_env
        self.default_base_url = default_base_url
        self.default_model_name = default_model_name

    def generate(
        self,
        request: ModelRequest,
        *,
        profile: ModelProfile | None = None,
    ) -> ModelResponse:
        if not self.enabled:
            raise ModelProviderDisabledError(
                f"Provider {self.provider_name} is disabled"
            )

        base_url = self._resolve_base_url()
        api_key = self._resolve_api_key()
        model_name = self._resolve_model_name(profile)
        timeout_seconds = self._timeout_seconds(profile)

        payload = {
            "model": model_name,
            "messages": self._messages(request),
            "temperature": (
                profile.default_params.temperature if profile is not None else 0.0
            ),
            "max_tokens": (
                profile.default_params.max_tokens if profile is not None else 800
            ),
        }
        response_json = self._post_chat_completion(
            base_url=base_url,
            api_key=api_key,
            payload=payload,
            timeout_seconds=timeout_seconds,
        )
        response_text = self._extract_response_text(response_json)
        return ModelResponse(
            task_type=request.task_type,
            response_text=response_text,
            structured_output={"text": response_text},
            provider_name=self.provider_name,
            model_name=model_name,
            metadata={
                "openai_compatible": True,
                "response_id": response_json.get("id"),
                "finish_reason": self._first_choice(response_json).get(
                    "finish_reason"
                ),
            },
        )

    def _resolve_base_url(self) -> str:
        base_url = os.getenv(self.base_url_env or "") or self.default_base_url
        if not base_url:
            raise ModelProviderConfigurationError(
                "Missing OpenAI-compatible base URL"
            )
        return base_url.rstrip("/")

    def _resolve_api_key(self) -> str:
        api_key = os.getenv(self.api_key_env or "")
        if not api_key:
            raise ModelProviderConfigurationError(
                f"Missing required model environment variable: {self.api_key_env}"
            )
        return api_key

    def _resolve_model_name(self, profile: ModelProfile | None) -> str:
        model_name = (
            os.getenv(self.model_name_env or "")
            or (profile.model_name if profile is not None else None)
            or self.default_model_name
        )
        if not model_name:
            raise ModelProviderConfigurationError(
                "Missing OpenAI-compatible model name"
            )
        return model_name

    def _timeout_seconds(self, profile: ModelProfile | None) -> float:
        timeout_ms = profile.default_params.timeout_ms if profile is not None else 5000
        return max(timeout_ms / 1000, 0.001)

    def _messages(self, request: ModelRequest) -> list[dict[str, str]]:
        if request.messages:
            return [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ]
        return [{"role": "user", "content": request.input_text or ""}]

    def _post_chat_completion(
        self,
        *,
        base_url: str,
        api_key: str,
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        endpoint = f"{base_url}/chat/completions"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            endpoint,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except socket.timeout as exc:
            raise ModelProviderTimeoutError(
                f"Provider {self.provider_name} timed out"
            ) from exc
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise ModelProviderError(
                f"Provider {self.provider_name} returned HTTP {exc.code}: "
                f"{error_body[:300]}"
            ) from exc
        except URLError as exc:
            raise ModelProviderError(
                f"Provider {self.provider_name} request failed: {exc.reason}"
            ) from exc

        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise ModelProviderError(
                f"Provider {self.provider_name} returned invalid JSON"
            ) from exc
        if not isinstance(parsed, dict):
            raise ModelProviderError(
                f"Provider {self.provider_name} returned unexpected JSON"
            )
        return parsed

    def _extract_response_text(self, response_json: dict[str, Any]) -> str:
        choice = self._first_choice(response_json)
        message = choice.get("message")
        if not isinstance(message, dict):
            raise ModelProviderError(
                f"Provider {self.provider_name} response has no message"
            )
        content = message.get("content")
        if not isinstance(content, str):
            raise ModelProviderError(
                f"Provider {self.provider_name} response has no text content"
            )
        return content

    def _first_choice(self, response_json: dict[str, Any]) -> dict[str, Any]:
        choices = response_json.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ModelProviderError(
                f"Provider {self.provider_name} response has no choices"
            )
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ModelProviderError(
                f"Provider {self.provider_name} response choice is invalid"
            )
        return first_choice
