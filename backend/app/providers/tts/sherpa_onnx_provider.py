"""sherpa-onnx ZipVoice zero-shot TTS provider.

Uses a reference audio sample to clone a voice and generate speech.
Model: sherpa-onnx-zipvoice-distill-int8-zh-en-emilia
Vocoder: vocos_24khz
"""

from __future__ import annotations

import io
import logging
import threading
from pathlib import Path
from typing import Any

from app.domain.tts import (
    TtsProviderName,
    TtsProviderRequest,
    TtsProviderResult,
)
from app.providers.tts.base import (
    BaseTtsProvider,
    TtsProviderConfigurationError,
    TtsProviderError,
)

logger = logging.getLogger(__name__)


class SherpaOnnxTtsProvider(BaseTtsProvider):
    """sherpa-onnx ZipVoice zero-shot TTS provider."""

    def __init__(
        self,
        *,
        model_dir: str,
        vocoder_path: str,
        voice_sample_path: str,
        voice_reference_text: str,
        num_threads: int = 2,
        num_steps: int = 4,
        enabled: bool = True,
    ) -> None:
        super().__init__(provider_name="sherpa_onnx", enabled=enabled)
        self._model_dir = Path(model_dir)
        self._vocoder_path = Path(vocoder_path)
        self._voice_sample_path = Path(voice_sample_path)
        self._voice_reference_text = voice_reference_text
        self._num_threads = num_threads
        self._num_steps = num_steps
        self._tts = None
        self._reference_audio: Any | None = None
        self._reference_sample_rate: int | None = None
        self._lock = threading.Lock()

    def _ensure_loaded(self) -> None:
        if self._tts is not None:
            return
        with self._lock:
            if self._tts is not None:
                return
            if not self.enabled:
                raise TtsProviderConfigurationError(
                    "sherpa-onnx TTS provider is disabled"
                )

        import sherpa_onnx

        model_dir = self._model_dir
        vocoder = self._vocoder_path

        missing = []
        for name in ("tokens.txt", "encoder.int8.onnx", "decoder.int8.onnx", "lexicon.txt"):
            if not (model_dir / name).exists():
                missing.append(str(model_dir / name))
        if not vocoder.exists():
            missing.append(str(vocoder))
        if not (model_dir / "espeak-ng-data").is_dir():
            missing.append(str(model_dir / "espeak-ng-data"))
        if missing:
            raise TtsProviderConfigurationError(
                f"sherpa-onnx TTS model files missing: {missing}"
            )

        config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                zipvoice=sherpa_onnx.OfflineTtsZipvoiceModelConfig(
                    tokens=str(model_dir / "tokens.txt"),
                    encoder=str(model_dir / "encoder.int8.onnx"),
                    decoder=str(model_dir / "decoder.int8.onnx"),
                    data_dir=str(model_dir / "espeak-ng-data"),
                    lexicon=str(model_dir / "lexicon.txt"),
                    vocoder=str(vocoder),
                ),
                debug=False,
                num_threads=self._num_threads,
                provider="cpu",
            )
        )
        if not config.validate():
            raise TtsProviderConfigurationError(
                "sherpa-onnx TTS config validation failed; check model files"
            )

        self._tts = sherpa_onnx.OfflineTts(config)
        logger.info(
            "sherpa-onnx TTS model loaded: model_dir=%s vocoder=%s",
            model_dir,
            vocoder,
        )

        self._load_reference_audio()

    def _load_reference_audio(self) -> None:
        try:
            import librosa
        except ModuleNotFoundError as exc:
            raise TtsProviderConfigurationError(
                "librosa is required for sherpa-onnx TTS; install backend[tts-local]"
            ) from exc

        sample_path = self._voice_sample_path
        if not sample_path.exists():
            raise TtsProviderConfigurationError(
                f"Voice sample not found: {sample_path}"
            )
        audio, sr = librosa.load(str(sample_path), sr=None)
        self._reference_audio = audio
        self._reference_sample_rate = sr
        logger.info(
            "Reference audio loaded: %s (sr=%d, duration=%.2fs)",
            sample_path,
            sr,
            len(audio) / sr,
        )

    def generate(self, request: TtsProviderRequest) -> TtsProviderResult:
        self._ensure_loaded()

        if not self._voice_reference_text:
            raise TtsProviderConfigurationError(
                "sherpa_onnx_tts_voice_reference_text is empty; "
                "set CHILD_AI_SHERPA_ONNX_TTS_VOICE_REFERENCE_TEXT in .env"
            )

        import sherpa_onnx

        gen_config = sherpa_onnx.GenerationConfig()
        gen_config.reference_audio = self._reference_audio
        gen_config.reference_sample_rate = self._reference_sample_rate
        gen_config.reference_text = self._voice_reference_text
        gen_config.num_steps = self._num_steps
        gen_config.extra["min_char_in_sentence"] = "30"

        try:
            result = self._tts.generate(request.text, gen_config)
        except Exception as exc:
            raise TtsProviderError(
                f"sherpa-onnx TTS generation failed: {exc}"
            ) from exc

        if len(result.samples) == 0:
            raise TtsProviderError(
                "sherpa-onnx TTS returned empty audio; check input text"
            )

        audio_bytes = self._samples_to_wav_bytes(
            result.samples, result.sample_rate
        )
        duration = len(result.samples) / result.sample_rate

        return TtsProviderResult(
            audio_bytes=audio_bytes,
            audio_format="wav",
            content_type="audio/wav",
            duration=duration,
            provider=TtsProviderName.SHERPA_ONNX,
            model="zipvoice-distill-int8-zh-en-emilia",
            metadata={
                "num_steps": self._num_steps,
                "sample_rate": result.sample_rate,
            },
        )

    @staticmethod
    def _samples_to_wav_bytes(
        samples: Any, sample_rate: int
    ) -> bytes:
        try:
            import soundfile as sf
        except ModuleNotFoundError as exc:
            raise TtsProviderConfigurationError(
                "soundfile is required for sherpa-onnx TTS; install backend[tts-local]"
            ) from exc

        buf = io.BytesIO()
        sf.write(buf, samples, samplerate=sample_rate, format="WAV", subtype="PCM_16")
        buf.seek(0)
        return buf.read()
