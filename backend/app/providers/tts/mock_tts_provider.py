from io import BytesIO
import wave

from app.domain.tts import (
    TtsProviderName,
    TtsProviderRequest,
    TtsProviderResult,
)
from app.providers.tts.base import BaseTtsProvider


class MockTtsProvider(BaseTtsProvider):
    def __init__(self, *, provider_name: str = "mock") -> None:
        super().__init__(provider_name=provider_name, enabled=True)

    def generate(self, request: TtsProviderRequest) -> TtsProviderResult:
        duration = 0.25
        return TtsProviderResult(
            audio_bytes=self._silence_wav(duration=duration),
            audio_format="wav",
            content_type="audio/wav",
            duration=duration,
            provider=TtsProviderName.MOCK,
            model="mock-tts-v0",
            metadata={"mock": True, "emotion": request.emotion.value},
        )

    def _silence_wav(self, *, duration: float) -> bytes:
        sample_rate = 24000
        frame_count = int(sample_rate * duration)
        buffer = BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b"\x00\x00" * frame_count)
        return buffer.getvalue()
