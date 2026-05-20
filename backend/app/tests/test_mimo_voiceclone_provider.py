import base64
import json

from app.domain.tts import (
    TtsEmotion,
    TtsProviderName,
    TtsProviderRequest,
    TtsVoiceVersion,
)
from app.providers.tts.mimo_voiceclone_provider import MimoVoiceCloneProvider


class FakeResponse:
    def __init__(self, body: dict) -> None:
        self._body = body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._body).encode("utf-8")


def test_mimo_voiceclone_provider_extracts_audio_data(monkeypatch, tmp_path) -> None:
    sample_path = tmp_path / "sample.wav"
    sample_path.write_bytes(b"RIFF-sample")
    audio_bytes = b"RIFF-generated"

    def fake_urlopen(request, timeout: float) -> FakeResponse:
        assert timeout == 30.0
        assert request.full_url == "https://example.test/v1/chat/completions"
        payload = json.loads(request.data.decode("utf-8"))
        assert payload["model"] == "mimo-v2.5-tts-voiceclone"
        assert payload["messages"][0] == {
            "role": "user",
            "content": "小白狐声音",
        }
        assert payload["messages"][1] == {"role": "assistant", "content": "你好。"}
        assert payload["audio"]["format"] == "wav"
        assert payload["audio"]["voice"].startswith("data:audio/wav;base64,")
        return FakeResponse(
            {
                "id": "tts-response-id",
                "choices": [
                    {
                        "message": {
                            "audio": {
                                "data": base64.b64encode(audio_bytes).decode("ascii"),
                                "duration": 1.25,
                            }
                        }
                    }
                ],
            }
        )

    monkeypatch.setattr(
        "app.providers.tts.mimo_voiceclone_provider.urlopen",
        fake_urlopen,
    )
    provider = MimoVoiceCloneProvider(
        base_url="https://example.test/v1",
        api_key="test-key",
        model="mimo-v2.5-tts-voiceclone",
        timeout_ms=30000,
        enabled=True,
    )

    result = provider.generate(
        TtsProviderRequest(
            text="你好。",
            emotion=TtsEmotion.ENCOURAGE,
            voice_version=TtsVoiceVersion.XIAOBAIHU_V01,
            voice_sample_path=str(sample_path),
            voice_sample_sha256="sample-sha",
            style_prompt="小白狐声音",
        )
    )

    assert result.audio_bytes == audio_bytes
    assert result.provider == TtsProviderName.MIMO
    assert result.model == "mimo-v2.5-tts-voiceclone"
    assert result.duration == 1.25
