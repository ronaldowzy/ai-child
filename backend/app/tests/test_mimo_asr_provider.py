import io
import json
import socket
from urllib.error import HTTPError

import pytest

from app.domain.schemas.asr import AsrAudioFormat, AsrProviderName
from app.providers.asr.base import (
    AsrProviderHttpError,
    AsrProviderRequest,
    AsrProviderTimeoutError,
)
from app.providers.asr.mimo_asr_provider import MimoAsrProvider


class FakeHttpResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def _provider() -> MimoAsrProvider:
    return MimoAsrProvider(
        base_url="https://example.test/v1",
        api_key="test-api-key",
        model="mimo-v2.5",
        timeout_ms=30000,
        enabled=True,
    )


def _request(audio_data_uri: str = "data:audio/wav;base64,UklGRi1mYWtl") -> AsrProviderRequest:
    return AsrProviderRequest(
        audio_data_uri=audio_data_uri,
        audio_format=AsrAudioFormat.WAV,
        language="zh-CN",
        duration_ms=1200,
        prompt="只返回转写结果。听不清时返回：未听清。",
        metadata={"decoded_audio_bytes": 9},
    )


def test_mimo_asr_provider_builds_payload_without_logging_audio(caplog) -> None:
    audio_data_uri = "data:audio/wav;base64,UklGRi1zbW9rZS1hdWRpbw=="

    payload = _provider().build_payload(_request(audio_data_uri))

    assert payload == {
        "model": "mimo-v2.5",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {"data": audio_data_uri},
                    },
                    {
                        "type": "text",
                        "text": "只返回转写结果。听不清时返回：未听清。",
                    },
                ],
            }
        ],
        "max_completion_tokens": 1024,
    }
    assert "UklGRi1zbW9rZS1hdWRpbw" not in caplog.text
    assert "data:audio/wav;base64" not in caplog.text


def test_mimo_asr_provider_calls_chat_completions_and_parses_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request: object, timeout: float) -> FakeHttpResponse:
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeHttpResponse(
            {
                "id": "asr-response-id",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "我想聊恐龙。",
                        },
                        "finish_reason": "stop",
                    }
                ],
            }
        )

    monkeypatch.setattr("app.providers.asr.mimo_asr_provider.urlopen", fake_urlopen)

    result = _provider().transcribe(_request())

    assert captured["url"] == "https://example.test/v1/chat/completions"
    assert captured["authorization"] == "Bearer test-api-key"
    assert captured["timeout"] == 30.0
    assert captured["body"]["messages"][0]["content"][0]["type"] == "input_audio"
    assert captured["body"]["messages"][0]["content"][1]["type"] == "text"
    assert result.transcript == "我想聊恐龙。"
    assert result.provider == AsrProviderName.MIMO
    assert result.model == "mimo-v2.5"
    assert result.metadata["response_id"] == "asr-response-id"
    assert result.metadata["finish_reason"] == "stop"


def test_mimo_asr_provider_treats_missing_content_as_empty_transcript(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(_request: object, timeout: float) -> FakeHttpResponse:
        return FakeHttpResponse({"choices": [{"message": {"content": None}}]})

    monkeypatch.setattr("app.providers.asr.mimo_asr_provider.urlopen", fake_urlopen)

    result = _provider().transcribe(_request())

    assert result.transcript == ""


def test_mimo_asr_provider_timeout_error_is_stable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(_request: object, timeout: float) -> FakeHttpResponse:
        raise socket.timeout("timed out with test-api-key")

    monkeypatch.setattr("app.providers.asr.mimo_asr_provider.urlopen", fake_urlopen)

    with pytest.raises(AsrProviderTimeoutError) as exc_info:
        _provider().transcribe(_request())

    assert str(exc_info.value) == "provider_timeout"
    assert "test-api-key" not in str(exc_info.value)


def test_mimo_asr_provider_http_error_does_not_leak_raw_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_body = (
        b'{"error":"test-api-key data:audio/wav;base64,UklGRg== '
        b'full transcript should stay private"}'
    )

    def fake_urlopen(request: object, timeout: float) -> FakeHttpResponse:
        raise HTTPError(
            request.full_url,
            429,
            "Too Many Requests",
            hdrs={},
            fp=io.BytesIO(raw_body),
        )

    monkeypatch.setattr("app.providers.asr.mimo_asr_provider.urlopen", fake_urlopen)

    with pytest.raises(AsrProviderHttpError) as exc_info:
        _provider().transcribe(_request())

    message = str(exc_info.value)
    assert message == "provider_http_error: status=429"
    assert "test-api-key" not in message
    assert "data:audio/wav;base64" not in message
    assert "full transcript" not in message
