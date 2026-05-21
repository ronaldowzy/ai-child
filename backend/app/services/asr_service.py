import base64
import binascii

from app.core.config import Settings, get_settings
from app.domain.schemas.asr import (
    AsrAudioFormat,
    AsrProviderName,
    AsrTranscriptStatus,
    AsrTranscriptionRequest,
    AsrTranscriptionResponse,
)
from app.providers.asr.base import (
    AsrProviderRequest,
    BaseAsrProvider,
)
from app.providers.asr.mimo_asr_provider import MimoAsrProvider
from app.providers.asr.mock_asr_provider import MockAsrProvider
from app.services.asr_data_policy_guard import (
    AsrDataPolicyGuard,
    AsrDataPolicySettings,
)


class AsrServiceError(RuntimeError):
    pass


class AsrRequestValidationError(AsrServiceError):
    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


TRANSCRIBE_ONLY_PROMPT = (
    "请把音频中的中文内容转写为文字。只返回转写结果；"
    "不要解释、总结或添加音频里没有的内容。听不清时返回：未听清。"
)


class AsrService:
    MAX_DURATION_MS = 30_000
    MAX_DECODED_AUDIO_BYTES = 10 * 1024 * 1024
    _UNCLEAR_MARKERS = {"未听清", "没听清", "听不清", "听不清楚", "无法听清"}

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        provider: BaseAsrProvider | None = None,
        policy_guard: AsrDataPolicyGuard | None = None,
        policy_settings: AsrDataPolicySettings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._provider = provider or self._build_provider()
        self._policy_guard = policy_guard or AsrDataPolicyGuard()
        self._policy_settings = policy_settings or self._build_policy_settings()

    def transcribe(
        self,
        request: AsrTranscriptionRequest,
    ) -> AsrTranscriptionResponse:
        decoded_size = self._validate_audio(request)
        self._policy_guard.validate(self._policy_settings)

        result = self._provider.transcribe(
            AsrProviderRequest(
                audio_data_uri=request.audio.data,
                audio_format=request.audio.format,
                language=request.language,
                duration_ms=request.audio.duration_ms,
                prompt=TRANSCRIBE_ONLY_PROMPT,
                metadata={
                    "decoded_audio_bytes": decoded_size,
                    "mock_transcript": request.metadata.get("mock_transcript"),
                },
            )
        )
        transcript = result.transcript.strip()
        if not transcript or self._is_unclear_marker(transcript):
            return AsrTranscriptionResponse(
                status=AsrTranscriptStatus.NEEDS_RETRY,
                transcript=None,
                requiresConfirmation=True,
                provider=result.provider,
                model=result.model,
                language=request.language,
                durationMs=result.duration_ms,
                confidence=result.confidence,
                errorCode="empty_transcript",
                fallbackAction="retry_or_type",
            )
        if len(transcript) > 2000:
            raise AsrRequestValidationError(
                "transcript_too_long",
                "ASR transcript is too long for confirmation UI",
            )

        return AsrTranscriptionResponse(
            status=AsrTranscriptStatus.OK,
            transcript=transcript,
            requiresConfirmation=True,
            provider=result.provider,
            model=result.model,
            language=request.language,
            durationMs=result.duration_ms,
            confidence=result.confidence,
        )

    def _validate_audio(self, request: AsrTranscriptionRequest) -> int:
        audio = request.audio
        if audio.format != AsrAudioFormat.WAV:
            raise AsrRequestValidationError(
                "unsupported_audio_format",
                "Only wav ASR input is enabled in the backend skeleton",
            )
        if audio.duration_ms and audio.duration_ms > self.MAX_DURATION_MS:
            raise AsrRequestValidationError(
                "audio_too_long",
                f"Audio duration exceeds {self.MAX_DURATION_MS}ms",
            )
        encoded = self._extract_base64(audio.data, audio_format=audio.format)
        try:
            decoded = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise AsrRequestValidationError(
                "invalid_audio_data",
                "ASR audio data must be valid base64",
            ) from exc
        if len(decoded) > self.MAX_DECODED_AUDIO_BYTES:
            raise AsrRequestValidationError(
                "audio_too_large",
                "ASR audio data exceeds the backend skeleton limit",
            )
        return len(decoded)

    def _extract_base64(self, data: str, *, audio_format: AsrAudioFormat) -> str:
        prefix = f"data:audio/{audio_format.value};base64,"
        if not data.startswith(prefix):
            raise AsrRequestValidationError(
                "invalid_audio_data",
                f"ASR audio data must start with {prefix}",
            )
        encoded = data[len(prefix) :]
        if not encoded:
            raise AsrRequestValidationError(
                "invalid_audio_data",
                "ASR audio data is empty",
            )
        return encoded

    def _is_unclear_marker(self, transcript: str) -> bool:
        normalized = transcript.strip().strip("。.!！?？[]【】()（） ")
        return normalized.lower() in self._UNCLEAR_MARKERS or normalized.lower() in {
            "unclear",
            "unable_to_hear",
        }

    def _build_provider(self) -> BaseAsrProvider:
        if self._settings.asr_provider == AsrProviderName.MIMO.value:
            return MimoAsrProvider(
                base_url=self._settings.mimo_asr_base_url,
                api_key=self._settings.mimo_asr_api_key,
                model=self._settings.mimo_asr_model,
                timeout_ms=self._settings.mimo_asr_timeout_ms,
                enabled=self._settings.mimo_asr_enabled,
            )
        return MockAsrProvider()

    def _build_policy_settings(self) -> AsrDataPolicySettings:
        return AsrDataPolicySettings(
            provider=self._provider.provider_name,
            provider_enabled=self._provider.enabled,
            api_key_present=bool(self._settings.mimo_asr_api_key),
            allow_child_audio=self._settings.mimo_asr_allow_child_audio,
            retention_policy_checked=(
                self._settings.mimo_asr_retention_policy_checked
            ),
            no_training_confirmed=self._settings.mimo_asr_no_training_confirmed,
        )
