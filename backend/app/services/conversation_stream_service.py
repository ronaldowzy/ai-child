from collections.abc import Iterator
from datetime import datetime, timezone
import hashlib
import logging
import time
from uuid import uuid4

from app.core.logging import hash_identifier
from app.core.config import Settings, get_settings
from app.domain.schemas.conversation import ConversationMessageResponse
from app.domain.schemas.conversation_stream import (
    ConversationStreamEvent,
    ConversationStreamRequest,
)
from app.middleware.request_id import get_request_id
from app.services.conversation_service import ConversationService
from app.services.text_segmenter import TextSegment, TextSegmenter
from app.services.tts_service import TtsService, get_tts_service


class _NoopConversationTtsService:
    def generate_for_conversation(self, *, text: str, emotion: str) -> str | None:
        return None


class _StreamEventBuilder:
    def __init__(self, *, turn_id: str, request_id: str | None) -> None:
        self._turn_id = turn_id
        self._request_id = request_id
        self._seq = 0

    def event(self, event_type: str, payload: dict[str, object]) -> ConversationStreamEvent:
        self._seq += 1
        return ConversationStreamEvent(
            event_id=f"{self._turn_id}:{self._seq:04d}",
            turn_id=self._turn_id,
            seq=self._seq,
            type=event_type,
            created_at=datetime.now(timezone.utc),
            request_id=self._request_id,
            payload=payload,
        )


class ConversationStreamService:
    """NDJSON pseudo-streaming service for safe child-facing conversation turns."""

    def __init__(
        self,
        *,
        conversation_service: ConversationService | None = None,
        tts_service: TtsService | None = None,
        text_segmenter: TextSegmenter | None = None,
        settings: Settings | None = None,
        debug_enabled: bool = True,
        tts_enabled: bool | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._conversation_service = conversation_service or ConversationService(
            tts_service=_NoopConversationTtsService(),
            debug_enabled=debug_enabled,
        )
        self._tts_service = tts_service or get_tts_service()
        self._text_segmenter = text_segmenter or TextSegmenter(
            hard_max_chars=self._settings.tts_max_text_chars
        )
        self._tts_enabled = (
            self._settings.conversation_tts_enabled
            if tts_enabled is None
            else tts_enabled
        )

    def stream_ndjson(self, request: ConversationStreamRequest) -> Iterator[str]:
        for event in self.stream_events(request):
            yield event.model_dump_json(exclude_none=True) + "\n"

    def stream_events(
        self,
        request: ConversationStreamRequest,
    ) -> Iterator[ConversationStreamEvent]:
        started_at = time.perf_counter()
        first_text_ms: float | None = None
        first_audio_ms: float | None = None
        active_scene: str | None = None
        error_type: str | None = None
        audio_segment_count = 0
        tts_error_count = 0
        turn_id = self._turn_id(request)
        builder = _StreamEventBuilder(turn_id=turn_id, request_id=get_request_id())
        yield builder.event(
            "session_started",
            {
                "requestId": get_request_id(),
                "sessionId": request.session_id,
                "protocol_version": request.stream_options.protocol_version,
                "text_granularity": request.stream_options.text_granularity,
                "include_tts": request.stream_options.include_tts,
                "audio_delivery": request.stream_options.audio_delivery,
                "client_turn_id": request.stream_options.client_turn_id,
            },
        )

        try:
            response = self._conversation_service.handle_message(request)
        except Exception as exc:
            error_type = exc.__class__.__name__
            yield builder.event(
                "error",
                {
                    "stage": "conversation",
                    "code": "conversation_failed",
                    "recoverable": False,
                    "safe_message": "小白狐这次没有接上，我们先停一下，等会儿再试。",
                },
            )
            yield builder.event(
                "done",
                {
                    "status": "failed",
                    "reason": "conversation_failed",
                },
            )
            self._log_stream_finished(
                request=request,
                started_at=started_at,
                active_scene=active_scene,
                first_text_ms=first_text_ms,
                first_audio_ms=first_audio_ms,
                audio_segment_count=audio_segment_count,
                error_type=error_type,
            )
            return

        active_scene = response.session_state.active_scene
        yield builder.event("route_decision", self._route_payload(response))

        segments = self._text_segmenter.segment(
            response.reply.text,
            hard_max_chars=self._settings.tts_max_text_chars,
        )
        final_text = "".join(segment.text for segment in segments)
        for segment in segments:
            if first_text_ms is None:
                first_text_ms = self._elapsed_ms(started_at)
            yield builder.event("text_delta", self._text_delta_payload(segment))
            yield builder.event("sentence_ready", self._sentence_ready_payload(segment))

        final_text_hash = self._text_hash(final_text)
        yield builder.event(
            "text_final",
            {
                "text": final_text,
                "char_count": len(final_text),
                "sentence_count": len(segments),
                "final_text_hash": final_text_hash,
                "is_final": True,
            },
        )

        if self._should_generate_tts(request=request, response=response):
            for segment in segments:
                yield builder.event("tts_started", self._tts_started_payload(segment))
                try:
                    audio_url = self._tts_service.generate_for_conversation(
                        text=segment.text,
                        emotion=response.reply.emotion,
                    )
                except Exception:
                    tts_error_count += 1
                    yield builder.event(
                        "error",
                        self._tts_error_payload(segment, code="tts_failed"),
                    )
                    continue
                if not audio_url:
                    tts_error_count += 1
                    yield builder.event(
                        "error",
                        self._tts_error_payload(segment, code="tts_unavailable"),
                    )
                    continue
                audio_segment_count += 1
                if first_audio_ms is None:
                    first_audio_ms = self._elapsed_ms(started_at)
                yield builder.event(
                    "audio_ready",
                    self._audio_ready_payload(
                        segment,
                        audio_url=audio_url,
                        play_order=audio_segment_count - 1,
                    ),
                )

        yield builder.event(
            "done",
            {
                "status": "completed",
                "final_text_hash": final_text_hash,
                "text_segment_count": len(segments),
                "audio_segment_count": audio_segment_count,
                "tts_error_count": tts_error_count,
            },
        )
        self._log_stream_finished(
            request=request,
            started_at=started_at,
            active_scene=active_scene,
            first_text_ms=first_text_ms,
            first_audio_ms=first_audio_ms,
            audio_segment_count=audio_segment_count,
            error_type="tts_segment_failed" if tts_error_count else error_type,
        )

    def _turn_id(self, request: ConversationStreamRequest) -> str:
        if request.stream_options.client_turn_id:
            safe_client_id = "".join(
                char
                for char in request.stream_options.client_turn_id
                if char.isalnum() or char in {"_", "-", ".", ":"}
            )
            if safe_client_id:
                return f"turn_{safe_client_id[:48]}"
        return f"turn_{uuid4().hex}"

    def _route_payload(self, response: ConversationMessageResponse) -> dict[str, object]:
        payload: dict[str, object] = {
            "base_scene": response.session_state.base_scene,
            "baseScene": response.session_state.base_scene,
            "active_scene": response.session_state.active_scene,
            "activeScene": response.session_state.active_scene,
            "needs_input": response.session_state.needs_input,
            "needsInput": response.session_state.needs_input,
            "requires_parent_attention": (
                response.session_state.requires_parent_attention is True
            ),
            "requiresParentAttention": (
                response.session_state.requires_parent_attention is True
            ),
            "reply_type": response.reply.type,
            "voice_enabled": response.reply.voice_enabled,
            "voiceEnabled": response.reply.voice_enabled,
            "emotion": response.reply.emotion,
            "agent_motion": response.reply.agent_motion,
            "agentMotion": response.reply.agent_motion,
        }
        if response.debug and response.debug.intent:
            payload["intent"] = response.debug.intent.intent.value
            payload["intent_confidence"] = response.debug.intent.confidence
        if response.debug and response.debug.safety:
            payload["risk_level"] = response.debug.safety.risk_level.value
            payload["riskLevel"] = response.debug.safety.risk_level.value
            payload["risk_category"] = response.debug.safety.primary_category.value
            payload["riskCategory"] = response.debug.safety.primary_category.value
        return payload

    def _text_delta_payload(self, segment: TextSegment) -> dict[str, object]:
        return {
            "index": segment.index,
            "delta": segment.text,
            "text_range": {"start": segment.start, "end": segment.end},
            "sentence_index": segment.index,
            "is_sentence_end": segment.is_sentence_end,
        }

    def _sentence_ready_payload(self, segment: TextSegment) -> dict[str, object]:
        return {
            "index": segment.index,
            "segment_id": f"seg_{segment.index}",
            "sentence_index": segment.index,
            "text": segment.text,
            "text_range": {"start": segment.start, "end": segment.end},
            "char_count": len(segment.text),
            "is_sentence_end": segment.is_sentence_end,
        }

    def _tts_started_payload(self, segment: TextSegment) -> dict[str, object]:
        return {
            "index": segment.index,
            "segment_id": f"seg_{segment.index}",
            "sentence_index": segment.index,
            "text_range": {"start": segment.start, "end": segment.end},
            "play_order": segment.index,
            "audio_delivery": "url",
        }

    def _audio_ready_payload(
        self,
        segment: TextSegment,
        *,
        audio_url: str,
        play_order: int,
    ) -> dict[str, object]:
        return {
            "index": segment.index,
            "segment_id": f"seg_{segment.index}",
            "sentence_index": segment.index,
            "audioUrl": audio_url,
            "audio_url": audio_url,
            "text": segment.text,
            "content_type": "audio/wav",
            "text_range": {"start": segment.start, "end": segment.end},
            "play_order": play_order,
        }

    def _tts_error_payload(self, segment: TextSegment, *, code: str) -> dict[str, object]:
        return {
            "stage": "tts",
            "code": code,
            "recoverable": True,
            "segment_id": f"seg_{segment.index}",
            "sentence_index": segment.index,
            "text_range": {"start": segment.start, "end": segment.end},
            "fallback": "system_tts_or_text",
            "safe_message": "这段声音没有放出来，但文字还在这里。",
        }

    def _should_generate_tts(
        self,
        *,
        request: ConversationStreamRequest,
        response: ConversationMessageResponse,
    ) -> bool:
        return (
            request.stream_options.include_tts
            and request.stream_options.audio_delivery == "url"
            and response.reply.voice_enabled
            and self._tts_enabled
        )

    def _text_hash(self, text: str) -> str:
        return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"

    def _elapsed_ms(self, started_at: float) -> float:
        return round((time.perf_counter() - started_at) * 1000, 1)

    def _log_stream_finished(
        self,
        *,
        request: ConversationStreamRequest,
        started_at: float,
        active_scene: str | None,
        first_text_ms: float | None,
        first_audio_ms: float | None,
        audio_segment_count: int,
        error_type: str | None,
    ) -> None:
        logging.getLogger("app.stream_timing").info(
            "conversation_stream_finished",
            extra={
                "event": "conversation_stream_finished",
                "request_id": get_request_id(),
                "session_id_hash": hash_identifier(request.session_id),
                "active_scene": active_scene,
                "first_text_ms": first_text_ms,
                "first_audio_ms": first_audio_ms,
                "stream_total_ms": self._elapsed_ms(started_at),
                "tts_segment_count": audio_segment_count,
                "error_type": error_type,
            },
        )
