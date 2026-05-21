import json
import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.domain.schemas.asr import AsrProviderName
from app.providers.asr.base import (
    AsrProviderConfigurationError,
    AsrProviderError,
    AsrProviderHttpError,
    AsrProviderRequest,
    AsrProviderResult,
    AsrProviderTimeoutError,
    BaseAsrProvider,
)


class MimoAsrProvider(BaseAsrProvider):
    """MiMo OpenAI-compatible audio-input ASR adapter."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_ms: int,
        enabled: bool = False,
    ) -> None:
        super().__init__(provider_name=AsrProviderName.MIMO, enabled=enabled)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_ms = timeout_ms

    def transcribe(self, request: AsrProviderRequest) -> AsrProviderResult:
        if not self.enabled:
            raise AsrProviderConfigurationError("MiMo ASR provider is disabled")
        if not self.api_key:
            raise AsrProviderConfigurationError("Missing MiMo ASR API key")

        response_json = self._post_json(
            payload=self.build_payload(request),
            timeout_seconds=max(self.timeout_ms / 1000, 0.001),
        )
        return AsrProviderResult(
            transcript=self._extract_transcript(response_json),
            provider=AsrProviderName.MIMO,
            model=self.model,
            duration_ms=request.duration_ms,
            metadata={
                "response_id": response_json.get("id"),
                "finish_reason": self._extract_finish_reason(response_json),
            },
        )

    def build_payload(self, request: AsrProviderRequest) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {"data": request.audio_data_uri},
                        },
                        {"type": "text", "text": request.prompt},
                    ],
                }
            ],
            "max_completion_tokens": 1024,
        }

    def _post_json(
        self,
        *,
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            f"{self.base_url}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except socket.timeout as exc:
            raise AsrProviderTimeoutError("provider_timeout") from exc
        except HTTPError as exc:
            raise AsrProviderHttpError(
                f"provider_http_error: status={exc.code}"
            ) from exc
        except URLError as exc:
            if isinstance(exc.reason, socket.timeout):
                raise AsrProviderTimeoutError("provider_timeout") from exc
            raise AsrProviderError("provider_request_failed") from exc

        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise AsrProviderError("provider_invalid_json") from exc
        if not isinstance(parsed, dict):
            raise AsrProviderError("provider_unexpected_json")
        return parsed

    def _extract_transcript(self, response_json: dict[str, Any]) -> str:
        choice = self._first_choice(response_json)
        message = choice.get("message")
        if not isinstance(message, dict):
            return ""
        content = message.get("content")
        if not isinstance(content, str):
            return ""
        return content.strip()

    def _extract_finish_reason(self, response_json: dict[str, Any]) -> str | None:
        choice = self._first_choice(response_json, required=False)
        if choice is None:
            return None
        finish_reason = choice.get("finish_reason")
        return finish_reason if isinstance(finish_reason, str) else None

    def _first_choice(
        self,
        response_json: dict[str, Any],
        *,
        required: bool = True,
    ) -> dict[str, Any] | None:
        choices = response_json.get("choices")
        if not isinstance(choices, list) or not choices:
            if required:
                raise AsrProviderError("provider_response_missing_choices")
            return None
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            if required:
                raise AsrProviderError("provider_response_invalid_choice")
            return None
        return first_choice
