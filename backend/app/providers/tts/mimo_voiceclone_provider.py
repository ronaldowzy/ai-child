import base64
import json
import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.domain.tts import (
    TtsProviderName,
    TtsProviderRequest,
    TtsProviderResult,
)
from app.providers.tts.base import (
    BaseTtsProvider,
    TtsProviderConfigurationError,
    TtsProviderError,
    TtsProviderTimeoutError,
)


class MimoVoiceCloneProvider(BaseTtsProvider):
    """MiMo VoiceClone adapter.

    The concrete request/response schema is intentionally isolated here. If MiMo
    changes fields, only this provider should need updates; Android and
    conversation services must continue to consume backend `audio_url`.
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_ms: int,
        enabled: bool,
        provider_name: str = "mimo",
    ) -> None:
        super().__init__(provider_name=provider_name, enabled=enabled)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_ms = timeout_ms

    def generate(self, request: TtsProviderRequest) -> TtsProviderResult:
        if not self.enabled:
            raise TtsProviderConfigurationError("MiMo TTS provider is disabled")
        if not self.api_key:
            raise TtsProviderConfigurationError("Missing MiMo TTS API key")

        response_json = self._post_json(
            payload=self._payload(request),
            timeout_seconds=max(self.timeout_ms / 1000, 0.001),
        )
        audio_bytes = self._extract_audio_bytes(response_json)
        return TtsProviderResult(
            audio_bytes=audio_bytes,
            audio_format="wav",
            content_type="audio/wav",
            duration=self._extract_duration(response_json),
            provider=TtsProviderName.MIMO,
            model=self.model,
            metadata={
                "response_id": response_json.get("id"),
                "raw_provider": "mimo",
            },
        )

    def _payload(self, request: TtsProviderRequest) -> dict[str, Any]:
        sample_data_uri = self._voice_sample_data_uri(request.voice_sample_path)
        return {
            "model": self.model,
            "messages": [
                {"role": "user", "content": request.style_prompt},
                {"role": "assistant", "content": request.text},
            ],
            "audio": {
                "format": "wav",
                "voice": sample_data_uri,
            },
        }

    def _voice_sample_data_uri(self, path: str) -> str:
        with open(path, "rb") as audio_file:
            encoded = base64.b64encode(audio_file.read()).decode("ascii")
        return f"data:audio/wav;base64,{encoded}"

    def _post_json(
        self,
        *,
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        endpoint = f"{self.base_url}/chat/completions"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            endpoint,
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
            raise TtsProviderTimeoutError("MiMo TTS provider timed out") from exc
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise TtsProviderError(
                f"MiMo TTS provider returned HTTP {exc.code}: {error_body[:300]}"
            ) from exc
        except URLError as exc:
            raise TtsProviderError(
                f"MiMo TTS provider request failed: {exc.reason}"
            ) from exc

        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise TtsProviderError("MiMo TTS provider returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise TtsProviderError("MiMo TTS provider returned unexpected JSON")
        return parsed

    def _extract_audio_bytes(self, response_json: dict[str, Any]) -> bytes:
        encoded = self._first_string(
            response_json,
            ("choices", 0, "message", "audio", "data"),
            ("audio", "data"),
            ("audio", "base64"),
            ("data",),
            ("audio_data",),
        )
        if encoded is None:
            raise TtsProviderError("MiMo TTS response has no supported audio field")
        if encoded.startswith("data:"):
            encoded = encoded.split(",", 1)[-1]
        try:
            return base64.b64decode(encoded)
        except ValueError as exc:
            raise TtsProviderError("MiMo TTS audio field is not valid base64") from exc

    def _extract_duration(self, response_json: dict[str, Any]) -> float | None:
        duration = response_json.get("duration")
        if isinstance(duration, (int, float)):
            return float(duration)
        audio = response_json.get("audio")
        if isinstance(audio, dict) and isinstance(audio.get("duration"), (int, float)):
            return float(audio["duration"])
        choice_audio = self._first_mapping(
            response_json,
            ("choices", 0, "message", "audio"),
        )
        if isinstance(choice_audio, dict) and isinstance(
            choice_audio.get("duration"),
            (int, float),
        ):
            return float(choice_audio["duration"])
        return None

    def _first_string(
        self,
        data: dict[str, Any],
        *paths: tuple[str | int, ...],
    ) -> str | None:
        for path in paths:
            current: Any = data
            for key in path:
                if isinstance(key, int):
                    if not isinstance(current, list) or len(current) <= key:
                        current = None
                        break
                    current = current[key]
                    continue
                if not isinstance(current, dict):
                    current = None
                    break
                current = current.get(key)
            if isinstance(current, str) and current:
                return current
        return None

    def _first_mapping(
        self,
        data: dict[str, Any],
        path: tuple[str | int, ...],
    ) -> dict[str, Any] | None:
        current: Any = data
        for key in path:
            if isinstance(key, int):
                if not isinstance(current, list) or len(current) <= key:
                    return None
                current = current[key]
                continue
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current if isinstance(current, dict) else None
