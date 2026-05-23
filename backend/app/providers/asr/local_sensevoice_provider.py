import base64
import binascii
import io
import wave
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.domain.schemas.asr import AsrAudioFormat, AsrProviderName
from app.providers.asr.base import (
    AsrProviderConfigurationError,
    AsrProviderError,
    AsrProviderRequest,
    AsrProviderResult,
    BaseAsrProvider,
)


class LocalSenseVoiceAsrProvider(BaseAsrProvider):
    """Local sherpa-onnx SenseVoice-Small adapter for short WAV ASR."""

    def __init__(
        self,
        *,
        model_path: Path,
        tokens_path: Path,
        num_threads: int = 4,
        use_itn: bool = True,
        language: str = "zh",
        enabled: bool = False,
    ) -> None:
        super().__init__(
            provider_name=AsrProviderName.LOCAL_SENSEVOICE,
            enabled=enabled,
        )
        self.model_path = model_path
        self.tokens_path = tokens_path
        self.num_threads = num_threads
        self.use_itn = use_itn
        self.language = language

    def transcribe(self, request: AsrProviderRequest) -> AsrProviderResult:
        if not self.enabled:
            raise AsrProviderConfigurationError(
                "local_sensevoice_asr_disabled"
            )
        if request.audio_format != AsrAudioFormat.WAV:
            raise AsrProviderConfigurationError(
                "local_sensevoice_supports_wav_only"
            )

        audio_bytes = self._audio_bytes(request)
        samples, sample_rate = self._decode_wav(audio_bytes)
        recognizer = _load_sensevoice_recognizer(
            model_path=str(self.model_path),
            tokens_path=str(self.tokens_path),
            num_threads=self.num_threads,
            use_itn=self.use_itn,
            language=self.language,
        )

        try:
            stream = recognizer.create_stream()
            stream.accept_waveform(sample_rate, samples)
            recognizer.decode_stream(stream)
            result = stream.result
        except Exception as exc:
            raise AsrProviderError("local_sensevoice_decode_failed") from exc

        transcript = getattr(result, "text", "")
        if not isinstance(transcript, str):
            transcript = ""
        return AsrProviderResult(
            transcript=transcript.strip(),
            provider=AsrProviderName.LOCAL_SENSEVOICE,
            model=Path(self.model_path).name,
            duration_ms=request.duration_ms,
            metadata={
                "runtime": "sherpa-onnx",
                "model_family": "sensevoice-small-int8",
                "sample_rate_hz": sample_rate,
            },
        )

    def _audio_bytes(self, request: AsrProviderRequest) -> bytes:
        decoded_audio = request.metadata.get("decoded_audio")
        if isinstance(decoded_audio, bytes):
            return decoded_audio

        prefix = f"data:audio/{request.audio_format.value};base64,"
        if not request.audio_data_uri.startswith(prefix):
            raise AsrProviderConfigurationError("invalid_audio_data_uri")
        encoded = request.audio_data_uri[len(prefix) :]
        try:
            return base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise AsrProviderConfigurationError("invalid_audio_base64") from exc

    def _decode_wav(self, audio_bytes: bytes) -> tuple[Any, int]:
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
                channels = wav.getnchannels()
                sample_width = wav.getsampwidth()
                sample_rate = wav.getframerate()
                frame_count = wav.getnframes()
                pcm = wav.readframes(frame_count)
        except wave.Error as exc:
            raise AsrProviderConfigurationError("invalid_wav_audio") from exc

        if channels < 1:
            raise AsrProviderConfigurationError("invalid_wav_channels")
        try:
            import numpy as np
        except ImportError as exc:
            raise AsrProviderConfigurationError("missing_numpy_dependency") from exc

        if sample_width == 2:
            samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
        elif sample_width == 4:
            samples = (
                np.frombuffer(pcm, dtype="<i4").astype(np.float32)
                / 2147483648.0
            )
        else:
            raise AsrProviderConfigurationError("unsupported_wav_sample_width")

        if channels > 1:
            try:
                samples = samples.reshape(-1, channels).mean(axis=1)
            except ValueError as exc:
                raise AsrProviderConfigurationError("invalid_wav_frames") from exc
        return samples, sample_rate


@lru_cache(maxsize=4)
def _load_sensevoice_recognizer(
    *,
    model_path: str,
    tokens_path: str,
    num_threads: int,
    use_itn: bool,
    language: str,
) -> Any:
    model = Path(model_path)
    tokens = Path(tokens_path)
    if not model.is_file():
        raise AsrProviderConfigurationError("missing_local_sensevoice_model")
    if not tokens.is_file():
        raise AsrProviderConfigurationError("missing_local_sensevoice_tokens")
    if num_threads < 1:
        raise AsrProviderConfigurationError("invalid_local_sensevoice_threads")

    try:
        import sherpa_onnx
    except ImportError as exc:
        raise AsrProviderConfigurationError("missing_sherpa_onnx_dependency") from exc

    try:
        return sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=str(model),
            tokens=str(tokens),
            language=language,
            use_itn=use_itn,
            num_threads=num_threads,
        )
    except Exception as exc:
        raise AsrProviderConfigurationError(
            "local_sensevoice_model_load_failed"
        ) from exc
