import hashlib
import logging
from pathlib import Path
import time

from app.core.config import Settings, get_settings
from app.domain.schemas.tts import XiaobaihuTtsRequest, XiaobaihuTtsResponse
from app.domain.tts import (
    TtsEmotion,
    TtsProviderName,
    TtsVoiceVersion,
    XIAOBAIHU_TTS_PROMPT_VERSION,
    TtsProviderRequest,
    xiaobaihu_style_prompt,
)
from app.middleware.request_id import get_request_id
from app.providers.tts.base import TtsProviderError
from app.providers.tts.mimo_voiceclone_provider import MimoVoiceCloneProvider
from app.providers.tts.mock_tts_provider import MockTtsProvider
from app.providers.tts.sherpa_onnx_provider import SherpaOnnxTtsProvider
from app.services.tts_cache_service import TtsCacheService
from app.services.tts_data_policy_guard import (
    TtsDataPolicyBlockedError,
    TtsDataPolicyGuard,
)


class TtsServiceError(RuntimeError):
    pass


class TtsRequestValidationError(TtsServiceError):
    pass


class TtsVoiceSampleMissingError(TtsServiceError):
    pass


class TtsService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        cache_service: TtsCacheService | None = None,
        data_policy_guard: TtsDataPolicyGuard | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._cache_dir = self._settings.resolve_repo_path(
            self._settings.tts_cache_dir
        )
        self._cache_service = cache_service or TtsCacheService(
            cache_dir=self._cache_dir
        )
        self._data_policy_guard = data_policy_guard or TtsDataPolicyGuard()
        self._sherpa_provider: SherpaOnnxTtsProvider | None = None

    def generate_xiaobaihu(
        self,
        request: XiaobaihuTtsRequest,
    ) -> XiaobaihuTtsResponse:
        started_at = time.perf_counter()
        text_chars = len(request.text.strip())
        provider: TtsProviderName | None = None
        model: str | None = None
        voice_version: TtsVoiceVersion | None = None
        emotion: TtsEmotion | None = None
        cache_key: str | None = None
        cache_hit = False
        audio_bytes: int | None = None
        try:
            normalized_text = self._validate_text(request.text)
            text_chars = len(normalized_text)
            emotion = self._validate_emotion(request.emotion)
            voice_version = self._validate_voice_version(request.voice_version)
            voice_sample_path = self._voice_sample_path(voice_version)
            provider = self._provider_name()
            model = self._model_name(provider)
            voice_sample_sha256 = self._cache_service.voice_sample_sha256(
                voice_sample_path
            )
            cache_key = self._cache_service.cache_key(
                normalized_text=normalized_text,
                emotion=emotion.value,
                voice_version=voice_version,
                provider=provider,
                model=model,
                voice_sample_sha256=voice_sample_sha256,
                prompt_version=XIAOBAIHU_TTS_PROMPT_VERSION,
            )

            if not request.force_refresh and self._cache_service.has(
                voice_version=voice_version,
                cache_key=cache_key,
            ):
                cache_hit = True
                metadata = self._cache_service.load_metadata(
                    voice_version=voice_version,
                    cache_key=cache_key,
                )
                audio_path = self._cache_service.audio_path(
                    voice_version=voice_version,
                    cache_key=cache_key,
                )
                audio_bytes = self._file_size(audio_path)
                duration = metadata.get("duration")
                response = self._response(
                    audio_url=self._public_audio_url(
                        voice_version=voice_version,
                        cache_key=cache_key,
                    ),
                    duration=duration if isinstance(duration, (int, float)) else (
                        self._cache_service.duration_seconds(audio_path)
                    ),
                    text=normalized_text,
                    emotion=emotion,
                    voice_version=voice_version,
                    provider=provider,
                    model=str(metadata.get("model") or model),
                    cache_hit=True,
                )
                self._log_tts_call_finished(
                    started_at=started_at,
                    provider=provider,
                    model=response.model,
                    voice_version=voice_version,
                    emotion=emotion,
                    cache_hit=cache_hit,
                    audio_bytes=audio_bytes,
                    text_chars=text_chars,
                    cache_key=cache_key,
                    error_type=None,
                )
                return response

            provider_result = self._generate_with_fallback(
                provider=provider,
                request=TtsProviderRequest(
                    text=normalized_text,
                    emotion=emotion,
                    voice_version=voice_version,
                    voice_sample_path=str(voice_sample_path),
                    voice_sample_sha256=voice_sample_sha256,
                    style_prompt=xiaobaihu_style_prompt(emotion),
                    prompt_version=XIAOBAIHU_TTS_PROMPT_VERSION,
                ),
            )
            if provider_result.provider != provider:
                fallback_provider = provider_result.provider
                provider = fallback_provider
                model = self._model_name(fallback_provider)
                cache_key = self._cache_service.cache_key(
                    normalized_text=normalized_text,
                    emotion=emotion.value,
                    voice_version=voice_version,
                    provider=fallback_provider,
                    model=model,
                    voice_sample_sha256=voice_sample_sha256,
                    prompt_version=XIAOBAIHU_TTS_PROMPT_VERSION,
                )
                if not request.force_refresh and self._cache_service.has(
                    voice_version=voice_version,
                    cache_key=cache_key,
                ):
                    cache_hit = True
                    metadata = self._cache_service.load_metadata(
                        voice_version=voice_version,
                        cache_key=cache_key,
                    )
                    audio_path = self._cache_service.audio_path(
                        voice_version=voice_version,
                        cache_key=cache_key,
                    )
                    audio_bytes = self._file_size(audio_path)
                    duration = metadata.get("duration")
                    response = self._response(
                        audio_url=self._public_audio_url(
                            voice_version=voice_version,
                            cache_key=cache_key,
                        ),
                        duration=duration if isinstance(duration, (int, float)) else (
                            self._cache_service.duration_seconds(audio_path)
                        ),
                        text=normalized_text,
                        emotion=emotion,
                        voice_version=voice_version,
                        provider=fallback_provider,
                        model=str(metadata.get("model") or model),
                        cache_hit=True,
                    )
                    self._log_tts_call_finished(
                        started_at=started_at,
                        provider=fallback_provider,
                        model=response.model,
                        voice_version=voice_version,
                        emotion=emotion,
                        cache_hit=cache_hit,
                        audio_bytes=audio_bytes,
                        text_chars=text_chars,
                        cache_key=cache_key,
                        error_type=None,
                    )
                    return response
            audio_bytes = len(provider_result.audio_bytes)
            text_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
            duration = provider_result.duration
            self._cache_service.save(
                voice_version=voice_version,
                cache_key=cache_key,
                audio_bytes=provider_result.audio_bytes,
                metadata={
                    "textHash": text_hash,
                    "emotion": emotion.value,
                    "voiceVersion": voice_version.value,
                    "provider": provider_result.provider.value,
                    "model": provider_result.model,
                    "voiceSampleSha256": voice_sample_sha256,
                    "promptVersion": XIAOBAIHU_TTS_PROMPT_VERSION,
                    "duration": duration,
                },
            )
            response = self._response(
                audio_url=self._public_audio_url(
                    voice_version=voice_version,
                    cache_key=cache_key,
                ),
                duration=duration,
                text=normalized_text,
                emotion=emotion,
                voice_version=voice_version,
                provider=provider_result.provider,
                model=provider_result.model,
                cache_hit=False,
            )
            self._log_tts_call_finished(
                started_at=started_at,
                provider=provider_result.provider,
                model=provider_result.model,
                voice_version=voice_version,
                emotion=emotion,
                cache_hit=False,
                audio_bytes=audio_bytes,
                text_chars=text_chars,
                cache_key=cache_key,
                error_type=None,
            )
            return response
        except Exception as exc:
            self._log_tts_call_finished(
                started_at=started_at,
                provider=provider,
                model=model,
                voice_version=voice_version,
                emotion=emotion,
                cache_hit=cache_hit,
                audio_bytes=audio_bytes,
                text_chars=text_chars,
                cache_key=cache_key,
                error_type=exc.__class__.__name__,
            )
            raise

    def generate_for_conversation(
        self,
        *,
        text: str,
        emotion: str,
    ) -> str | None:
        if not self._settings.conversation_tts_enabled:
            return None
        try:
            response = self.generate_xiaobaihu(
                XiaobaihuTtsRequest(
                    text=text,
                    emotion=self._conversation_emotion(emotion),
                    voiceVersion=TtsVoiceVersion.XIAOBAIHU_V01.value,
                    forceRefresh=False,
                )
            )
        except (TtsServiceError, TtsProviderError, TtsDataPolicyBlockedError):
            return None
        return response.audio_url

    def _validate_text(self, text: str) -> str:
        normalized = self._cache_service.normalize_text(text)
        if not normalized:
            raise TtsRequestValidationError("TTS text must not be empty")
        if len(normalized) > self._settings.tts_max_text_chars:
            raise TtsRequestValidationError(
                "TTS text is too long: "
                f"max={self._settings.tts_max_text_chars}, actual={len(normalized)}"
            )
        return normalized

    def _validate_emotion(self, raw_emotion: str) -> TtsEmotion:
        try:
            return TtsEmotion(raw_emotion)
        except ValueError as exc:
            allowed = ", ".join(emotion.value for emotion in TtsEmotion)
            raise TtsRequestValidationError(
                f"Unsupported TTS emotion={raw_emotion}; allowed={allowed}"
            ) from exc

    def _validate_voice_version(self, raw_voice_version: str) -> TtsVoiceVersion:
        try:
            return TtsVoiceVersion(raw_voice_version)
        except ValueError as exc:
            allowed = ", ".join(version.value for version in TtsVoiceVersion)
            raise TtsRequestValidationError(
                "Unsupported TTS voiceVersion="
                f"{raw_voice_version}; allowed={allowed}"
            ) from exc

    def _voice_sample_path(self, voice_version: TtsVoiceVersion) -> Path:
        if voice_version != TtsVoiceVersion.XIAOBAIHU_V01:
            raise TtsRequestValidationError(
                f"Unsupported TTS voiceVersion={voice_version.value}"
            )
        voice_sample_path = self._settings.resolve_repo_path(
            self._settings.xiaobaihu_voice_sample_path
        )
        if not voice_sample_path.exists():
            raise TtsVoiceSampleMissingError(
                f"Xiaobaihu voice sample does not exist: {voice_sample_path}"
            )
        return voice_sample_path

    def _provider_name(self) -> TtsProviderName:
        try:
            return TtsProviderName(self._settings.tts_provider)
        except ValueError as exc:
            allowed = ", ".join(provider.value for provider in TtsProviderName)
            raise TtsRequestValidationError(
                "Unsupported TTS provider="
                f"{self._settings.tts_provider}; allowed={allowed}"
            ) from exc

    def _model_name(self, provider: TtsProviderName) -> str:
        if provider == TtsProviderName.MIMO:
            return self._settings.mimo_tts_model
        if provider == TtsProviderName.SHERPA_ONNX:
            return "zipvoice-distill-int8-zh-en-emilia"
        return "mock-tts-v0"

    def _generate_with_fallback(
        self,
        *,
        provider: TtsProviderName,
        request: TtsProviderRequest,
    ):
        from app.providers.tts.base import TtsProviderConfigurationError

        local_fallback_enabled = (
            self._settings.tts_enable_local_fallback
            and self._settings.sherpa_onnx_tts_enabled
            and provider != TtsProviderName.SHERPA_ONNX
        )
        try:
            self._data_policy_guard.validate(
                provider=provider,
                settings=self._settings,
                contains_child_text=True,
            )
            return self._provider(provider).generate(request)
        except TtsProviderConfigurationError:
            raise
        except (TtsProviderError, TtsDataPolicyBlockedError) as exc:
            if not local_fallback_enabled:
                raise
            logging.getLogger("app.tts_timing").warning(
                "tts_primary_failed_fallback",
                extra={
                    "event": "tts_primary_failed_fallback",
                    "primary_provider": provider.value,
                    "fallback_provider": TtsProviderName.SHERPA_ONNX.value,
                    "error_type": exc.__class__.__name__,
                    "error_detail": str(exc)[:200],
                },
            )
            return self._provider(TtsProviderName.SHERPA_ONNX).generate(request)

    def _provider(self, provider: TtsProviderName) -> MockTtsProvider | MimoVoiceCloneProvider | SherpaOnnxTtsProvider:
        if provider == TtsProviderName.MIMO:
            return MimoVoiceCloneProvider(
                base_url=self._settings.mimo_tts_base_url,
                api_key=self._settings.mimo_tts_api_key,
                model=self._settings.mimo_tts_model,
                timeout_ms=self._settings.mimo_tts_timeout_ms,
                enabled=self._settings.mimo_tts_enabled,
            )
        if provider == TtsProviderName.SHERPA_ONNX:
            if self._sherpa_provider is None:
                self._sherpa_provider = SherpaOnnxTtsProvider(
                    model_dir=self._settings.resolve_repo_path(
                        self._settings.sherpa_onnx_tts_model_dir
                    ),
                    vocoder_path=self._settings.resolve_repo_path(
                        self._settings.sherpa_onnx_tts_vocoder_path
                    ),
                    voice_sample_path=self._settings.resolve_repo_path(
                        self._settings.xiaobaihu_voice_sample_path
                    ),
                    voice_reference_text=self._settings.sherpa_onnx_tts_voice_reference_text,
                    num_threads=self._settings.sherpa_onnx_tts_num_threads,
                    num_steps=self._settings.sherpa_onnx_tts_num_steps,
                    enabled=self._settings.sherpa_onnx_tts_enabled,
                )
            return self._sherpa_provider
        return MockTtsProvider()

    def _public_audio_url(
        self,
        *,
        voice_version: TtsVoiceVersion,
        cache_key: str,
    ) -> str:
        base_url = self._settings.tts_public_base_url.rstrip("/")
        return f"{base_url}/{voice_version.value}/{cache_key}.wav"

    def _response(
        self,
        *,
        audio_url: str,
        duration: float | int | None,
        text: str,
        emotion: TtsEmotion,
        voice_version: TtsVoiceVersion,
        provider: TtsProviderName,
        model: str,
        cache_hit: bool,
    ) -> XiaobaihuTtsResponse:
        return XiaobaihuTtsResponse(
            audioUrl=audio_url,
            duration=float(duration) if isinstance(duration, (int, float)) else None,
            text=text,
            emotion=emotion.value,
            voiceVersion=voice_version.value,
            provider=provider.value,
            model=model,
            cacheHit=cache_hit,
        )

    def _conversation_emotion(self, emotion: str) -> str:
        normalized = emotion.strip().lower()
        if normalized in {"safety", "steady", "safety_concern", "concerned"}:
            return TtsEmotion.SAFETY.value
        if normalized in {"privacy", "privacy_boundary"}:
            return TtsEmotion.PRIVACY.value
        if normalized in {"calm", "sleepy", "bedtime", "gentle"}:
            return TtsEmotion.CALM.value
        if normalized in {"thinking", "focused", "homework", "homework_focus"}:
            return TtsEmotion.HINT.value
        if normalized in {"encouraging", "happy", "proud"}:
            return TtsEmotion.HAPPY.value
        return TtsEmotion.ENCOURAGE.value

    def _file_size(self, path: Path) -> int | None:
        try:
            return path.stat().st_size
        except OSError:
            return None

    def _log_tts_call_finished(
        self,
        *,
        started_at: float,
        provider: TtsProviderName | None,
        model: str | None,
        voice_version: TtsVoiceVersion | None,
        emotion: TtsEmotion | None,
        cache_hit: bool,
        audio_bytes: int | None,
        text_chars: int,
        cache_key: str | None,
        error_type: str | None,
    ) -> None:
        logging.getLogger("app.tts_timing").info(
            "tts_call_finished",
            extra={
                "event": "tts_call_finished",
                "request_id": get_request_id(),
                "provider": provider.value if provider else None,
                "model": model,
                "voice_version": voice_version.value if voice_version else None,
                "emotion": emotion.value if emotion else None,
                "cache_hit": cache_hit,
                "elapsed_ms": round((time.perf_counter() - started_at) * 1000, 1),
                "audio_bytes": audio_bytes,
                "text_chars": text_chars,
                "cache_key_prefix": cache_key[:8] if cache_key else None,
                "error_type": error_type,
                "child_id_hash": None,
                "session_id_hash": None,
            },
        )


def get_tts_service() -> TtsService:
    return TtsService()
