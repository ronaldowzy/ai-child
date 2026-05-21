from typing import Any

from app.domain.schemas.asr import AsrProviderName
from app.providers.asr.base import (
    AsrProviderConfigurationError,
    AsrProviderRequest,
    AsrProviderResult,
    BaseAsrProvider,
)


class MimoAsrProvider(BaseAsrProvider):
    """Disabled MiMo ASR adapter skeleton.

    The request shape is documented, but real network calls are intentionally
    deferred until Coordinator wires shared config, tests and policy approval.
    """

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
        raise AsrProviderConfigurationError(
            "MiMo ASR external call is not wired in this skeleton"
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
