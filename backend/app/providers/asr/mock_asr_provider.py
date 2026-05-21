from app.domain.schemas.asr import AsrProviderName
from app.providers.asr.base import (
    AsrProviderDisabledError,
    AsrProviderRequest,
    AsrProviderResult,
    BaseAsrProvider,
)


class MockAsrProvider(BaseAsrProvider):
    """ASR placeholder that never calls an external provider."""

    _DEFAULT_TRANSCRIPT = "未听清"

    def __init__(self, *, enabled: bool = True) -> None:
        super().__init__(provider_name=AsrProviderName.MOCK, enabled=enabled)

    def transcribe(self, request: AsrProviderRequest) -> AsrProviderResult:
        if not self.enabled:
            raise AsrProviderDisabledError("Mock ASR provider is disabled")

        requested_transcript = request.metadata.get("mock_transcript")
        transcript = (
            requested_transcript.strip()
            if isinstance(requested_transcript, str)
            and requested_transcript.strip()
            else self._DEFAULT_TRANSCRIPT
        )
        return AsrProviderResult(
            transcript=transcript,
            provider=AsrProviderName.MOCK,
            model="mock-asr-v0",
            confidence=None,
            duration_ms=request.duration_ms,
            metadata={"mock": True},
        )
