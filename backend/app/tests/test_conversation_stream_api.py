import json
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import conversation_stream as conversation_stream_api
from app.api.v1.conversation_stream import router as conversation_stream_router
from app.domain.schemas.conversation_stream import ConversationStreamRequest
from app.middleware.request_id import RequestIdMiddleware
from app.services.conversation_service import ConversationService
from app.services.conversation_stream_service import ConversationStreamService


class NoopTtsService:
    def generate_for_conversation(self, *, text: str, emotion: str) -> str | None:
        return None


class UrlTtsService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def generate_for_conversation(self, *, text: str, emotion: str) -> str | None:
        self.calls.append((text, emotion))
        return f"/media/tts/xiaobaohu_v01/segment_{len(self.calls)}.wav"


class FailingTtsService:
    def generate_for_conversation(self, *, text: str, emotion: str) -> str | None:
        raise RuntimeError("provider timeout with child text hidden")


def _client() -> TestClient:
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)
    app.include_router(conversation_stream_router, prefix="/api/v1")
    return TestClient(app)


def _payload(
    text: str = "我想聊恐龙",
    *,
    include_tts: bool = False,
    session_id: str = "stream_session",
) -> dict:
    return {
        "child_id": "stream_child",
        "session_id": session_id,
        "input": {
            "type": "text",
            "text": text,
            "attachments": [],
        },
        "client_context": {
            "device_time": "2026-05-21T16:35:00+08:00",
            "timezone": "Asia/Shanghai",
            "app_mode": "child",
        },
        "stream_options": {
            "protocol_version": "stream.v0.1",
            "text_granularity": "sentence",
            "include_tts": include_tts,
            "audio_delivery": "url",
            "client_turn_id": "client_turn_001",
        },
    }


def _events_from_response(response) -> list[dict]:
    return [
        json.loads(line)
        for line in response.text.splitlines()
        if line.strip()
    ]


def _events_from_service(
    service: ConversationStreamService,
    payload: dict,
) -> list[dict]:
    request = ConversationStreamRequest.model_validate(payload)
    return [
        event.model_dump(mode="json", exclude_none=True)
        for event in service.stream_events(request)
    ]


def _text_from_deltas(events: list[dict]) -> str:
    return "".join(
        event["payload"]["delta"]
        for event in events
        if event["type"] == "text_delta"
    )


def test_stream_endpoint_returns_ndjson_events(monkeypatch) -> None:
    service = ConversationStreamService(
        conversation_service=ConversationService(
            tts_service=NoopTtsService(),
            debug_enabled=True,
        ),
        tts_service=NoopTtsService(),
        tts_enabled=False,
    )
    monkeypatch.setattr(
        conversation_stream_api,
        "conversation_stream_service",
        service,
    )

    response = _client().post(
        "/api/v1/conversation/stream",
        json=_payload(include_tts=False),
        headers={"X-Request-ID": "stream-test-request-001"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert response.headers["X-Request-ID"] == "stream-test-request-001"
    events = _events_from_response(response)
    event_types = [event["type"] for event in events]

    assert event_types[0] == "session_started"
    assert "route_decision" in event_types
    assert "text_delta" in event_types
    assert "sentence_ready" in event_types
    assert "text_final" in event_types
    assert event_types[-1] == "done"
    assert {event["seq"] for event in events} == set(range(1, len(events) + 1))

    final_event = next(event for event in events if event["type"] == "text_final")
    assert final_event["payload"]["text"] == _text_from_deltas(events)
    assert final_event["payload"]["final_text_hash"].startswith("sha256:")
    assert events[-1]["payload"]["status"] == "completed"
    route_event = next(event for event in events if event["type"] == "route_decision")
    assert route_event["payload"]["active_scene"] == "conversation.open"


def test_stream_service_emits_audio_ready_for_sentence_tts_segments() -> None:
    tts_service = UrlTtsService()
    service = ConversationStreamService(
        conversation_service=ConversationService(
            tts_service=NoopTtsService(),
            debug_enabled=True,
        ),
        tts_service=tts_service,
        tts_enabled=True,
    )

    events = _events_from_service(
        service,
        _payload(text="我想聊恐龙。再聊三角龙！", include_tts=True),
    )

    tts_started = [event for event in events if event["type"] == "tts_started"]
    audio_ready = [event for event in events if event["type"] == "audio_ready"]

    assert tts_started
    assert len(audio_ready) == len(tts_started)
    assert len(tts_service.calls) == len(tts_started)
    assert audio_ready[0]["payload"]["audio_url"].startswith(
        "/media/tts/xiaobaohu_v01/"
    )
    assert events[-1]["payload"]["audio_segment_count"] == len(audio_ready)


def test_tts_failure_emits_error_but_preserves_text_final_and_done() -> None:
    service = ConversationStreamService(
        conversation_service=ConversationService(
            tts_service=NoopTtsService(),
            debug_enabled=True,
        ),
        tts_service=FailingTtsService(),
        tts_enabled=True,
    )

    events = _events_from_service(
        service,
        _payload(text="我想聊恐龙。再聊翼龙！", include_tts=True),
    )
    event_types = [event["type"] for event in events]

    assert "text_final" in event_types
    assert event_types[-1] == "done"
    assert events[-1]["payload"]["status"] == "completed"
    assert events[-1]["payload"]["tts_error_count"] >= 1

    error_events = [event for event in events if event["type"] == "error"]
    assert error_events
    assert all(event["payload"]["stage"] == "tts" for event in error_events)
    assert all(event["payload"]["recoverable"] is True for event in error_events)
    assert "provider timeout" not in json.dumps(error_events, ensure_ascii=False)


def test_learning_stream_keeps_no_direct_answer_policy() -> None:
    service = ConversationStreamService(
        conversation_service=ConversationService(
            tts_service=NoopTtsService(),
            debug_enabled=True,
        ),
        tts_service=NoopTtsService(),
        tts_enabled=False,
    )

    events = _events_from_service(
        service,
        _payload(
            text="我有一道题不会",
            include_tts=False,
            session_id="stream_learning_session",
        ),
    )

    route_event = next(event for event in events if event["type"] == "route_decision")
    final_event = next(event for event in events if event["type"] == "text_final")

    assert route_event["payload"]["active_scene"] == "learning.homework_help"
    assert "答案是" not in final_event["payload"]["text"]
    assert "一步" in final_event["payload"]["text"]


def test_privacy_stream_keeps_boundary_routing() -> None:
    service = ConversationStreamService(
        conversation_service=ConversationService(
            tts_service=NoopTtsService(),
            debug_enabled=True,
        ),
        tts_service=NoopTtsService(),
        tts_enabled=False,
    )

    events = _events_from_service(
        service,
        _payload(
            text="我可以告诉你我家地址吗",
            include_tts=False,
            session_id="stream_privacy_session",
        ),
    )

    route_event = next(event for event in events if event["type"] == "route_decision")
    final_event = next(event for event in events if event["type"] == "text_final")

    assert route_event["payload"]["active_scene"] == "privacy.boundary"
    assert "地址" in final_event["payload"]["text"]
    assert "爸爸妈妈" in final_event["payload"]["text"]


def test_stream_timing_log_contains_request_id_and_latency(
    caplog,
    monkeypatch,
) -> None:
    caplog.set_level(logging.INFO, logger="app.stream_timing")
    service = ConversationStreamService(
        conversation_service=ConversationService(
            tts_service=NoopTtsService(),
            debug_enabled=True,
        ),
        tts_service=UrlTtsService(),
        tts_enabled=True,
    )
    monkeypatch.setattr(
        conversation_stream_api,
        "conversation_stream_service",
        service,
    )

    response = _client().post(
        "/api/v1/conversation/stream",
        json=_payload(text="我想聊恐龙。再聊三角龙！", include_tts=True),
        headers={"X-Request-ID": "stream-log-request-001"},
    )
    assert response.status_code == 200

    records = [
        record for record in caplog.records
        if getattr(record, "event", None) == "conversation_stream_finished"
    ]
    assert records
    record = records[-1]
    assert record.request_id == "stream-log-request-001"
    assert record.active_scene == "conversation.open"
    assert record.session_id_hash
    assert record.first_text_ms is not None
    assert record.first_audio_ms is not None
    assert record.stream_total_ms >= record.first_text_ms
    assert record.tts_segment_count >= 1
    assert "我想聊恐龙。再聊三角龙！" not in caplog.text
