import hashlib
from pathlib import Path

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
from app.providers.tts.base import TtsProviderError
from app.providers.tts.mimo_voiceclone_provider import MimoVoiceCloneProvider
from app.providers.tts.mock_tts_provider import MockTtsProvider
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

    def generate_xiaobaihu(
        self,
        request: XiaobaihuTtsRequest,
    ) -> XiaobaihuTtsResponse:
        normalized_text = self._validate_text(request.text)
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
            metadata = self._cache_service.load_metadata(
                voice_version=voice_version,
                cache_key=cache_key,
            )
            audio_path = self._cache_service.audio_path(
                voice_version=voice_version,
                cache_key=cache_key,
            )
            duration = metadata.get("duration")
            return self._response(
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

        self._data_policy_guard.validate(
            provider=provider,
            settings=self._settings,
            contains_child_text=True,
        )
        provider_result = self._provider(provider).generate(
            TtsProviderRequest(
                text=normalized_text,
                emotion=emotion,
                voice_version=voice_version,
                voice_sample_path=str(voice_sample_path),
                voice_sample_sha256=voice_sample_sha256,
                style_prompt=xiaobaihu_style_prompt(emotion),
                prompt_version=XIAOBAIHU_TTS_PROMPT_VERSION,
            )
        )
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
        return self._response(
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
        return "mock-tts-v0"

    def _provider(self, provider: TtsProviderName) -> MockTtsProvider | MimoVoiceCloneProvider:
        if provider == TtsProviderName.MIMO:
            return MimoVoiceCloneProvider(
                base_url=self._settings.mimo_tts_base_url,
                api_key=self._settings.mimo_tts_api_key,
                model=self._settings.mimo_tts_model,
                timeout_ms=self._settings.mimo_tts_timeout_ms,
                enabled=self._settings.mimo_tts_enabled,
            )
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


def get_tts_service() -> TtsService:
    return TtsService()
