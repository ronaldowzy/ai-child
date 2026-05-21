import base64
import binascii
import logging
import time

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
from app.middleware.request_id import get_request_id
from app.providers.asr.mimo_asr_provider import MimoAsrProvider
from app.providers.asr.mock_asr_provider import MockAsrProvider
from app.services.asr_data_policy_guard import (
    AsrDataPolicyBlockedError,
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
    SUPPORTED_AUDIO_FORMATS = {AsrAudioFormat.WAV, AsrAudioFormat.M4A}
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
        started_at = time.perf_counter()
        provider: AsrProviderName | None = self._provider.provider_name
        model: str | None = self._model_name(provider)
        duration_ms = request.audio.duration_ms
        decoded_size: int | None = None
        response_status: AsrTranscriptStatus | None = None
        error_type: str | None = None
        try:
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
            provider = result.provider
            model = result.model
            duration_ms = result.duration_ms
            transcript = result.transcript.strip()
            if not transcript or self._is_unclear_marker(transcript):
                response_status = AsrTranscriptStatus.NEEDS_RETRY
                return AsrTranscriptionResponse(
                    status=response_status,
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

            response_status = AsrTranscriptStatus.OK
            return AsrTranscriptionResponse(
                status=response_status,
                transcript=transcript,
                requiresConfirmation=True,
                provider=result.provider,
                model=result.model,
                language=request.language,
                durationMs=result.duration_ms,
                confidence=result.confidence,
            )
        except AsrDataPolicyBlockedError as exc:
            response_status = AsrTranscriptStatus.BLOCKED
            error_type = exc.__class__.__name__
            raise
        except Exception as exc:
            response_status = AsrTranscriptStatus.FAILED
            error_type = exc.__class__.__name__
            raise
        finally:
            self._log_asr_call_finished(
                started_at=started_at,
                provider=provider,
                model=model,
                duration_ms=duration_ms,
                audio_bytes=decoded_size,
                status=response_status,
                error_type=error_type,
            )

    def _validate_audio(self, request: AsrTranscriptionRequest) -> int:
        audio = request.audio
        if audio.format not in self.SUPPORTED_AUDIO_FORMATS:
            raise AsrRequestValidationError(
                "unsupported_audio_format",
                "Only wav and m4a ASR input are enabled in the backend skeleton",
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

    def _log_asr_call_finished(
        self,
        *,
        started_at: float,
        provider: AsrProviderName | None,
        model: str | None,
        duration_ms: int | None,
        audio_bytes: int | None,
        status: AsrTranscriptStatus | None,
        error_type: str | None,
    ) -> None:
        logging.getLogger("app.asr_timing").info(
            "asr_call_finished",
            extra={
                "event": "asr_call_finished",
                "request_id": get_request_id(),
                "provider": provider.value if provider else None,
                "model": model,
                "duration_ms": duration_ms,
                "audio_bytes": audio_bytes,
                "elapsed_ms": round((time.perf_counter() - started_at) * 1000, 1),
                "status": status.value if status else None,
                "error_type": error_type,
            },
        )

    def _is_unclear_marker(self, transcript: str) -> bool:
        normalized = transcript.strip().strip("。.!！?？[]【】()（） ")
        return normalized.lower() in self._UNCLEAR_MARKERS or normalized.lower() in {
            "unclear",
            "unable_to_hear",
        }

    def _model_name(self, provider: AsrProviderName | None) -> str | None:
        if provider == AsrProviderName.MIMO:
            return self._settings.mimo_asr_model
        if provider == AsrProviderName.MOCK:
            return "mock-asr-v0"
        return None

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
