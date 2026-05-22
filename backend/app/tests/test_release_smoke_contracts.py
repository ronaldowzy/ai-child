from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess

import pytest

from app.core.config import Settings
from app.domain.schemas.asr import AsrTranscriptionRequest
from app.domain.schemas.conversation import ConversationMessageResponse, Reply, SessionState
from app.domain.schemas.conversation_stream import ConversationStreamRequest
from app.repositories.conversation_persistence_repository import ConversationTurnWrite
from app.services.asr_service import AsrService
from app.services.conversation_persistence_service import ConversationPersistenceService
from app.services.conversation_stream_service import ConversationStreamService


ROOT_DIR = Path(__file__).resolve().parents[3]
SMOKE_SCRIPTS = [
    "scripts/setup_local_postgres.sh",
    "scripts/smoke_backend_local.sh",
    "scripts/smoke_db_persistence.sh",
    "scripts/smoke_voice_stack.sh",
    "scripts/check_asr_real_status.sh",
    "scripts/smoke_mimo_asr_opt_in.sh",
    "scripts/smoke_vision_model_opt_in.sh",
]


class StaticConversationService:
    def handle_message(
        self,
        _request: ConversationStreamRequest,
    ) -> ConversationMessageResponse:
        return ConversationMessageResponse(
            reply=Reply(
                text="你好呀。我们可以慢慢聊恐龙。",
                voice_enabled=True,
                emotion="warm",
                agent_motion="listening_tail",
            ),
            ui_actions=[],
            session_state=SessionState(
                base_scene="conversation.open",
                active_scene="conversation.open",
            ),
        )


class UrlTtsService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def generate_for_conversation(self, *, text: str, emotion: str) -> str:
        self.calls.append((text, emotion))
        return f"/media/tts/xiaobaohu_v01/smoke_{len(self.calls)}.wav"


class CapturingTurnRepository:
    def __init__(self) -> None:
        self.turn: ConversationTurnWrite | None = None

    def save_turn(self, turn_write: ConversationTurnWrite) -> None:
        self.turn = turn_write


def _stream_payload() -> dict:
    return {
        "child_id": "child_release_smoke_stream",
        "session_id": "session_release_smoke_stream",
        "input": {
            "type": "text",
            "text": "我想聊恐龙",
            "attachments": [],
        },
        "client_context": {
            "device_time": "2026-05-22T16:35:00+08:00",
            "timezone": "Asia/Shanghai",
            "app_mode": "child",
        },
        "stream_options": {
            "protocol_version": "stream.v0.1",
            "text_granularity": "sentence",
            "include_tts": True,
            "audio_delivery": "url",
            "client_turn_id": "release_smoke_contract",
        },
    }


def test_smoke_scripts_are_executable_and_parse_as_bash() -> None:
    for relative_path in SMOKE_SCRIPTS:
        script_path = ROOT_DIR / relative_path
        assert script_path.is_file(), relative_path
        assert os.access(script_path, os.X_OK), relative_path
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            cwd=ROOT_DIR,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr


def test_mock_asr_smoke_data_uri_does_not_log_raw_audio_or_transcript(
    caplog: pytest.LogCaptureFixture,
) -> None:
    data_uri = "data:audio/wav;base64,UklGRgAAAAA="
    transcript = "你好小白狐，我们来测试语音输入。"
    request = AsrTranscriptionRequest.model_validate(
        {
            "childId": "child_asr_log_smoke",
            "sessionId": "session_asr_log_smoke",
            "audio": {
                "data": data_uri,
                "format": "wav",
                "sampleRateHz": 16000,
                "channelCount": 1,
                "durationMs": 500,
            },
            "language": "zh-CN",
            "mode": "confirm_before_send",
            "metadata": {"mock_transcript": transcript},
        }
    )
    caplog.set_level("INFO", logger="app.asr_timing")

    response = AsrService(settings=Settings(asr_provider="mock")).transcribe(request)

    assert response.status == "ok"
    assert response.transcript == transcript
    assert "asr_call_finished" in caplog.text
    assert data_uri not in caplog.text
    assert "UklGRgAAAAA=" not in caplog.text
    assert transcript not in caplog.text


def test_stream_include_tts_persistence_stores_summary_not_full_event_list() -> None:
    repository = CapturingTurnRepository()
    tts_service = UrlTtsService()
    service = ConversationStreamService(
        conversation_service=StaticConversationService(),
        tts_service=tts_service,
        conversation_persistence_service=ConversationPersistenceService(
            repository=repository
        ),
        settings=Settings(
            conversation_tts_enabled=True,
            conversation_stream_tts_soft_timeout_ms=0,
        ),
        tts_enabled=True,
    )
    request = ConversationStreamRequest.model_validate(_stream_payload())

    events = [event.model_dump(mode="json") for event in service.stream_events(request)]

    assert any(event["type"] == "audio_ready" for event in events)
    assert repository.turn is not None
    assert len(tts_service.calls) >= 1
    stream_audio_summary = repository.turn.agent_message.input_items
    assert stream_audio_summary == [
        {
            "type": "stream_audio_summary",
            "has_audio": True,
            "audio_segment_count": len(tts_service.calls),
            "tts_segment_count": len(tts_service.calls),
            "tts_error_count": 0,
            "text_segment_count": len(tts_service.calls),
        }
    ]
    persisted = json.dumps(asdict(repository.turn), ensure_ascii=False)
    assert "session_started" not in persisted
    assert "text_delta" not in persisted
    assert "sentence_ready" not in persisted
    assert "audio_ready" not in persisted
    assert "event_id" not in persisted
    assert "turn_id" not in persisted
