import json
import logging
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.api.v1 import conversation_stream as conversation_stream_api
from app.api.v1.conversation_stream import router as conversation_stream_router
from app.domain.schemas.conversation import (
    ConversationMessageResponse,
    Reply,
    SessionState,
)
from app.domain.schemas.conversation_stream import ConversationStreamRequest
from app.middleware.request_id import RequestIdMiddleware
from app.repositories.conversation_persistence_repository import ConversationTurnWrite
from app.services.conversation_persistence_service import ConversationPersistenceService
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


class PartiallyFailingTtsService:
    def __init__(self, *, fail_call_indexes: set[int]) -> None:
        self._fail_call_indexes = fail_call_indexes
        self.calls: list[tuple[str, str]] = []

    def generate_for_conversation(self, *, text: str, emotion: str) -> str | None:
        call_index = len(self.calls)
        self.calls.append((text, emotion))
        if call_index in self._fail_call_indexes:
            raise RuntimeError("provider timeout with child text hidden")
        return f"/media/tts/xiaobaohu_v01/segment_{call_index}.wav"


class SlowThenFastTtsService:
    def __init__(self, *, slow_call_indexes: set[int]) -> None:
        self._slow_call_indexes = slow_call_indexes
        self.calls: list[tuple[str, str]] = []

    def generate_for_conversation(self, *, text: str, emotion: str) -> str | None:
        call_index = len(self.calls)
        self.calls.append((text, emotion))
        if call_index in self._slow_call_indexes:
            time.sleep(0.2)
        return f"/media/tts/xiaobaohu_v01/segment_{call_index}.wav"


class StaticConversationService:
    def __init__(self, *, reply_text: str, voice_enabled: bool = True) -> None:
        self._reply_text = reply_text
        self._voice_enabled = voice_enabled

    def handle_message(
        self,
        request: ConversationStreamRequest,
    ) -> ConversationMessageResponse:
        return ConversationMessageResponse(
            reply=Reply(
                text=self._reply_text,
                voice_enabled=self._voice_enabled,
                emotion="warm",
                agent_motion="listening_tail",
            ),
            ui_actions=[],
            session_state=SessionState(
                base_scene="conversation.open",
                active_scene="conversation.open",
            ),
        )


class CapturingStreamPersistenceService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def record_stream_turn(self, **kwargs: object) -> None:
        self.calls.append(kwargs)


class FailingStreamPersistenceService:
    def record_stream_turn(self, **_kwargs: object) -> None:
        raise RuntimeError("simulated stream persistence failure")


class CapturingTurnRepository:
    def __init__(self) -> None:
        self.turn: ConversationTurnWrite | None = None

    def save_turn(self, turn_write: ConversationTurnWrite) -> None:
        self.turn = turn_write


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


def _event_types(events: list[dict]) -> list[str]:
    return [event["type"] for event in events]


def _event_index(
    events: list[dict],
    event_type: str,
    *,
    sentence_index: int | None = None,
) -> int:
    for index, event in enumerate(events):
        if event["type"] != event_type:
            continue
        if (
            sentence_index is not None
            and event["payload"].get("sentence_index") != sentence_index
        ):
            continue
        return index
    raise AssertionError(
        f"missing event type={event_type} sentence_index={sentence_index}"
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
    event_types = _event_types(events)

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
    session_started = events[0]["payload"]
    assert session_started["stream_mode"] == "safe_reply_pseudo"
    assert session_started["text_delta_source"] == "post_safety_full_reply"
    assert session_started["true_llm_streaming"] is False
    route_event = next(event for event in events if event["type"] == "route_decision")
    assert route_event["payload"]["active_scene"] == "conversation.open"


def test_stream_route_payload_matches_non_stream_companion_continue_actions() -> None:
    from app.domain.companion_object import (
        CompanionObjectCreateRequest,
        CompanionObjectSource,
        CompanionObjectType,
    )
    from app.repositories.companion_object_repository import InMemoryCompanionObjectRepository
    from app.services.companion_object_service import CompanionObjectService

    non_stream_companion_service = CompanionObjectService(
        repository=InMemoryCompanionObjectRepository(),
    )
    non_stream_companion_service.create(
        CompanionObjectCreateRequest(
            child_id="stream_child",
            name="小棉花",
            object_type=CompanionObjectType.STAR,
            source_type=CompanionObjectSource.FIRST_OPEN,
            safe_summary="这颗星星叫小棉花",
            light_location="窗边",
        )
    )
    stream_companion_service = CompanionObjectService(
        repository=InMemoryCompanionObjectRepository(),
    )
    stream_companion_service.create(
        CompanionObjectCreateRequest(
            child_id="stream_child",
            name="小棉花",
            object_type=CompanionObjectType.STAR,
            source_type=CompanionObjectSource.FIRST_OPEN,
            safe_summary="这颗星星叫小棉花",
            light_location="窗边",
        )
    )

    non_stream_conversation_service = ConversationService(
        companion_object_service=non_stream_companion_service,
        tts_service=NoopTtsService(),
        debug_enabled=True,
    )
    stream_conversation_service = ConversationService(
        companion_object_service=stream_companion_service,
        tts_service=NoopTtsService(),
        debug_enabled=True,
    )
    request_payload = _payload(text="加一个朋友")
    request_payload["input"]["quick_action_id"] = "companion_continue"

    non_stream_response = non_stream_conversation_service.handle_message(
        ConversationStreamRequest.model_validate(request_payload),
    )
    stream_events = _events_from_service(
        ConversationStreamService(
            conversation_service=stream_conversation_service,
            tts_service=NoopTtsService(),
            tts_enabled=False,
        ),
        request_payload,
    )
    route_event = next(event for event in stream_events if event["type"] == "route_decision")

    non_stream_action_ids = [
        action.id
        for group in non_stream_response.ui_actions
        for action in group.actions
    ]
    stream_action_ids = [
        action["id"]
        for action in route_event["payload"]["quick_actions"]
    ]

    assert non_stream_response.reply.text == "那我们给它找一个小伙伴\n你可以说一个名字，也可以给我看看"
    assert non_stream_action_ids == [
        "companion_friend_name",
        "companion_friend_image",
        "companion_skip",
    ]
    assert stream_action_ids == non_stream_action_ids


def test_include_tts_false_skips_tts_events_and_provider_calls() -> None:
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
        _payload(text="我想聊恐龙。再聊三角龙！", include_tts=False),
    )
    event_types = _event_types(events)

    assert "tts_started" not in event_types
    assert "audio_ready" not in event_types
    assert tts_service.calls == []
    assert events[0]["payload"]["include_tts"] is False
    assert events[-1]["payload"]["audio_segment_count"] == 0
    assert events[-1]["payload"]["tts_error_count"] == 0


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
    assert _event_index(events, "audio_ready") < _event_index(events, "text_final")
    assert events[-1]["type"] == "done"

    for started_event in tts_started:
        sentence_index = started_event["payload"]["sentence_index"]
        assert _event_index(events, "sentence_ready", sentence_index=sentence_index) < (
            _event_index(events, "tts_started", sentence_index=sentence_index)
        )
        assert _event_index(events, "tts_started", sentence_index=sentence_index) < (
            _event_index(events, "audio_ready", sentence_index=sentence_index)
        )

    final_event = next(event for event in events if event["type"] == "text_final")
    assert final_event["payload"]["text"] == _text_from_deltas(events)


def test_stream_service_persists_one_completed_turn_after_done() -> None:
    persistence = CapturingStreamPersistenceService()
    service = ConversationStreamService(
        conversation_service=StaticConversationService(
            reply_text="你好呀，我是小白狐。我们可以聊恐龙。"
        ),
        tts_service=NoopTtsService(),
        conversation_persistence_service=persistence,
        tts_enabled=False,
    )

    events = _events_from_service(
        service,
        _payload(text="我想聊恐龙", include_tts=False),
    )

    text_delta_count = len([event for event in events if event["type"] == "text_delta"])
    final_text = next(
        event["payload"]["text"] for event in events if event["type"] == "text_final"
    )

    assert events[-1]["type"] == "done"
    assert len(persistence.calls) == 1
    call = persistence.calls[0]
    assert call["request"].input.text == "我想聊恐龙"
    assert call["final_text"] == final_text
    assert call["response"].session_state.active_scene == "conversation.open"
    assert call["text_segment_count"] == text_delta_count
    assert call["audio_segment_count"] == 0
    assert "segments" not in call


def test_stream_persistence_records_audio_segment_summary_once() -> None:
    persistence = CapturingStreamPersistenceService()
    service = ConversationStreamService(
        conversation_service=StaticConversationService(
            reply_text=(
                "第一段声音已经准备好了。"
                "第二段声音也应该排队播放。"
                "第三段声音继续验证顺序。"
            )
        ),
        tts_service=UrlTtsService(),
        conversation_persistence_service=persistence,
        tts_enabled=True,
    )

    events = _events_from_service(
        service,
        _payload(text="请分段讲", include_tts=True),
    )
    audio_ready = [event for event in events if event["type"] == "audio_ready"]

    assert len(audio_ready) == 3
    assert len(persistence.calls) == 1
    call = persistence.calls[0]
    assert call["audio_segment_count"] == 3
    assert call["first_audio_url"] == audio_ready[0]["payload"]["audio_url"]
    assert call["tts_error_count"] == 0
    assert "segment_texts" not in call


def test_stream_persistence_records_tts_error_stats_for_partial_failures() -> None:
    persistence = CapturingStreamPersistenceService()
    service = ConversationStreamService(
        conversation_service=StaticConversationService(
            reply_text=(
                "第一段音频现在应该可以正常播放出来。"
                "第二段音频会模拟一次失败但不能影响后面。"
                "第三段音频仍然需要继续生成并播放出来。"
            )
        ),
        tts_service=PartiallyFailingTtsService(fail_call_indexes={1}),
        conversation_persistence_service=persistence,
        tts_enabled=True,
    )

    events = _events_from_service(
        service,
        _payload(text="请分三段讲", include_tts=True),
    )
    audio_ready = [event for event in events if event["type"] == "audio_ready"]
    tts_errors = [
        event for event in events
        if event["type"] == "error" and event["payload"].get("stage") == "tts"
    ]

    assert len(audio_ready) == 2
    assert len(tts_errors) == 1
    assert len(persistence.calls) == 1
    call = persistence.calls[0]
    assert call["audio_segment_count"] == 2
    assert call["tts_error_count"] == 1
    assert call["first_audio_url"] == audio_ready[0]["payload"]["audio_url"]


def test_stream_persistence_failure_does_not_block_text_final_or_done(
    caplog,
) -> None:
    caplog.set_level(logging.WARNING, logger="app.conversation_persistence")
    child_text = "这句孩子输入不应该出现在持久化失败日志"
    final_text = "这句最终回复也不应该出现在持久化失败日志。"
    service = ConversationStreamService(
        conversation_service=StaticConversationService(reply_text=final_text),
        tts_service=NoopTtsService(),
        conversation_persistence_service=FailingStreamPersistenceService(),
        tts_enabled=False,
    )

    events = _events_from_service(
        service,
        _payload(text=child_text, include_tts=False),
    )
    event_types = _event_types(events)

    assert "text_final" in event_types
    assert event_types[-1] == "done"
    assert "conversation_stream_persistence_failed" in caplog.text
    assert child_text not in caplog.text
    assert final_text not in caplog.text


def test_stream_persistence_debug_disabled_uses_unknown_intent_and_risk() -> None:
    repository = CapturingTurnRepository()
    persistence = ConversationPersistenceService(repository=repository)
    service = ConversationStreamService(
        conversation_service=StaticConversationService(
            reply_text="没有 debug 时也要能保存最终文本。"
        ),
        tts_service=UrlTtsService(),
        conversation_persistence_service=persistence,
        tts_enabled=True,
    )

    events = _events_from_service(
        service,
        _payload(text="debug 关闭测试", include_tts=True),
    )
    audio_ready = [event for event in events if event["type"] == "audio_ready"]

    assert events[-1]["type"] == "done"
    assert repository.turn is not None
    assert repository.turn.routing_decision.primary_intent == "unknown"
    assert repository.turn.routing_decision.risk_level == "unknown"
    assert repository.turn.agent_message.normalized_text == (
        "没有 debug 时也要能保存最终文本。"
    )
    assert repository.turn.agent_message.input_items == [
        {
            "type": "stream_audio_summary",
            "has_audio": True,
            "audio_segment_count": len(audio_ready),
            "tts_segment_count": len(audio_ready),
            "tts_error_count": 0,
            "text_segment_count": len(
                [event for event in events if event["type"] == "text_delta"]
            ),
        }
    ]
    assert repository.turn.agent_message.audio_url == (
        audio_ready[0]["payload"]["audio_url"]
    )


def test_one_tts_segment_failure_does_not_stop_later_segments() -> None:
    tts_service = PartiallyFailingTtsService(fail_call_indexes={1})
    service = ConversationStreamService(
        conversation_service=StaticConversationService(
            reply_text=(
                "第一段文字已经准备好了。"
                "第二段声音现在开始合成。"
                "第三段也应该继续播放。"
            ),
        ),
        tts_service=tts_service,
        tts_enabled=True,
    )

    events = _events_from_service(
        service,
        _payload(text="请分三段讲", include_tts=True),
    )

    tts_started = [event for event in events if event["type"] == "tts_started"]
    error_events = [event for event in events if event["type"] == "error"]
    audio_ready = [event for event in events if event["type"] == "audio_ready"]

    assert len(tts_started) == 3
    assert len(tts_service.calls) == 3
    assert len(error_events) == 1
    assert error_events[0]["payload"]["stage"] == "tts"
    assert error_events[0]["payload"]["sentence_index"] == 1
    assert {event["payload"]["sentence_index"] for event in audio_ready} == {0, 2}
    assert _event_index(events, "error", sentence_index=1) < _event_index(
        events,
        "audio_ready",
        sentence_index=2,
    )
    assert _event_index(events, "audio_ready", sentence_index=2) < _event_index(
        events,
        "text_final",
    )
    assert events[-1]["type"] == "done"
    assert events[-1]["payload"]["tts_segment_count"] == 3
    assert events[-1]["payload"]["audio_segment_count"] == 2
    assert events[-1]["payload"]["tts_error_count"] == 1


def test_slow_tts_segment_soft_timeout_does_not_block_later_segments() -> None:
    tts_service = SlowThenFastTtsService(slow_call_indexes={1})
    service = ConversationStreamService(
        conversation_service=StaticConversationService(
            reply_text=(
                "第一段文字已经准备好了。"
                "第二段声音可能会很慢很慢。"
                "第三段不能被慢段卡住继续播放。"
            ),
        ),
        tts_service=tts_service,
        settings=Settings(conversation_stream_tts_soft_timeout_ms=50),
        tts_enabled=True,
    )

    events = _events_from_service(
        service,
        _payload(text="请分三段讲", include_tts=True),
    )

    error_events = [event for event in events if event["type"] == "error"]
    audio_ready = [event for event in events if event["type"] == "audio_ready"]

    assert len(tts_service.calls) == 3
    assert len(error_events) == 1
    assert error_events[0]["payload"]["code"] == "tts_timeout"
    assert error_events[0]["payload"]["sentence_index"] == 1
    assert error_events[0]["payload"]["text"] == "第二段声音可能会很慢很慢。"
    assert {event["payload"]["sentence_index"] for event in audio_ready} == {0, 2}
    assert _event_index(events, "error", sentence_index=1) < _event_index(
        events,
        "audio_ready",
        sentence_index=2,
    )
    assert events[-1]["payload"]["tts_error_count"] == 1


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


def test_safety_stream_keeps_guardian_routing_and_parent_attention() -> None:
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
            text="陌生人让我不要告诉家长",
            include_tts=False,
            session_id="stream_safety_session",
        ),
    )

    route_event = next(event for event in events if event["type"] == "route_decision")
    final_event = next(event for event in events if event["type"] == "text_final")

    assert route_event["payload"]["active_scene"] == "safety.guardian"
    assert route_event["payload"]["requires_parent_attention"] is True
    assert route_event["payload"]["risk_level"] == "high"
    assert "家长" in final_event["payload"]["text"]
    assert "可信任的大人" in final_event["payload"]["text"]


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
    assert "家长" in final_event["payload"]["text"]


def test_text_final_payload_excludes_debug_and_session_state_internals() -> None:
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
            session_id="stream_text_final_privacy_session",
        ),
    )

    final_payload = next(
        event["payload"] for event in events if event["type"] == "text_final"
    )
    serialized = json.dumps(final_payload, ensure_ascii=False)

    assert set(final_payload) == {
        "text",
        "char_count",
        "sentence_count",
        "final_text_hash",
        "is_final",
    }
    assert "debug" not in final_payload
    assert "session_state" not in final_payload
    assert "sessionState" not in final_payload
    assert "risk_level" not in final_payload
    assert "parent_policy" not in serialized
    assert "safety_rules" not in serialized


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
    assert record.request_start is not None
    assert record.model_ms is not None
    assert record.model_ms >= 0
    assert record.first_text_ms is not None
    assert record.first_tts_start_ms is not None
    assert record.tts_started_ms == record.first_tts_start_ms
    assert record.first_audio_ms is not None
    assert record.text_to_audio_ms is not None
    assert record.text_to_audio_ms >= 0
    assert record.text_segment_count >= 1
    assert record.stream_total_ms >= record.first_text_ms
    assert record.turn_total_ms == record.stream_total_ms
    assert record.tts_segment_count >= 1
    assert record.audio_segment_count >= 1
    assert record.tts_error_count == 0
    assert "我想聊恐龙。再聊三角龙！" not in caplog.text


def test_parallel_tts_generates_all_audio_events() -> None:
    """并行 TTS 应为所有段生成音频事件，顺序与段顺序一致。"""
    tts_service = UrlTtsService()
    service = ConversationStreamService(
        conversation_service=StaticConversationService(
            reply_text=(
                "第一段并行测试文字已经准备好了。"
                "第二段并行测试文字也应该完成。"
                "第三段并行测试文字同样需要生成。"
            )
        ),
        tts_service=tts_service,
        tts_enabled=True,
    )

    events = _events_from_service(
        service,
        _payload(text="并行测试", include_tts=True),
    )

    audio_ready = [e for e in events if e["type"] == "audio_ready"]
    tts_started = [e for e in events if e["type"] == "tts_started"]

    assert len(tts_started) == 3
    assert len(audio_ready) == 3
    assert len(tts_service.calls) == 3

    # 验证音频事件按段顺序排列
    for i, event in enumerate(audio_ready):
        assert event["payload"]["sentence_index"] == i
        assert event["payload"]["play_order"] == i

    # 验证所有文字事件在音频事件之前
    last_text_delta_idx = _event_index(events, "text_delta", sentence_index=2)
    first_audio_idx = _event_index(events, "audio_ready", sentence_index=0)
    assert last_text_delta_idx < first_audio_idx


def test_parallel_tts_partial_failure_preserves_order() -> None:
    """并行 TTS 中部分失败不影响其他段的顺序。"""
    service = ConversationStreamService(
        conversation_service=StaticConversationService(
            reply_text=(
                "第一段文字应该能够成功生成音频。"
                "第二段文字会模拟失败但不影响后面。"
                "第三段文字也应该能够成功生成音频。"
            )
        ),
        tts_service=PartiallyFailingTtsService(fail_call_indexes={1}),
        tts_enabled=True,
    )

    events = _events_from_service(
        service,
        _payload(text="并行部分失败测试", include_tts=True),
    )

    audio_ready = [e for e in events if e["type"] == "audio_ready"]
    error_events = [e for e in events if e["type"] == "error" and e["payload"].get("stage") == "tts"]

    assert len(audio_ready) == 2
    assert len(error_events) == 1
    assert error_events[0]["payload"]["sentence_index"] == 1
    assert {e["payload"]["sentence_index"] for e in audio_ready} == {0, 2}
    assert events[-1]["type"] == "done"
    assert events[-1]["payload"]["tts_error_count"] == 1


def test_tts_parallel_timing_log_emitted(caplog) -> None:
    """并行 TTS 完成后应发出 tts_parallel_finished 日志。"""
    caplog.set_level(logging.INFO, logger="app.tts_timing")
    service = ConversationStreamService(
        conversation_service=StaticConversationService(
            reply_text="第一段日志测试已经完成了。第二段日志测试也要完成了。"
        ),
        tts_service=UrlTtsService(),
        tts_enabled=True,
    )

    _events_from_service(
        service,
        _payload(text="并行日志测试", include_tts=True),
    )

    parallel_records = [
        r for r in caplog.records
        if getattr(r, "event", None) == "tts_parallel_finished"
    ]
    assert len(parallel_records) == 1
    record = parallel_records[0]
    assert record.segment_count == 2
    assert record.success_count == 2
    assert record.error_count == 0
    assert record.max_segment_ms >= 0
    assert record.min_segment_ms >= 0
