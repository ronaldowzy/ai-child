import logging
from typing import Any
from uuid import uuid4

from app.core.logging import hash_identifier
from app.domain.schemas.conversation import (
    ConversationMessageRequest,
    ConversationMessageResponse,
)
from app.domain.schemas.conversation_stream import ConversationStreamRequest
from app.domain.scene import SceneRouteDecision
from app.domain.time import TimeContext
from app.middleware.request_id import get_request_id
from app.repositories.conversation_persistence_repository import (
    ConversationMessageWrite,
    ConversationPersistenceRepository,
    ConversationPersistenceRepositoryUnavailable,
    ConversationSessionWrite,
    ConversationTurnWrite,
    RoutingDecisionWrite,
)
from app.services.intent_classifier import IntentClassification
from app.services.safety_engine import SafetyClassification


logger = logging.getLogger("app.conversation_persistence")


class ConversationPersistenceService:
    """Builds a non-sensitive turn payload and persists it best-effort."""

    def __init__(
        self,
        *,
        repository: ConversationPersistenceRepository | None = None,
    ) -> None:
        self._repository = repository or ConversationPersistenceRepository()

    def record_turn(
        self,
        *,
        request: ConversationMessageRequest,
        response: ConversationMessageResponse,
        safety: SafetyClassification,
        intent: IntentClassification,
        route_decision: SceneRouteDecision,
        time_context: TimeContext,
    ) -> None:
        try:
            self._repository.save_turn(
                self._turn_write(
                    request=request,
                    response=response,
                    safety=safety,
                    intent=intent,
                    route_decision=route_decision,
                    time_context=time_context,
                )
            )
        except ConversationPersistenceRepositoryUnavailable as exc:
            self._log_failure(
                request=request,
                error_type=exc.__class__.__name__,
            )
        except Exception as exc:
            self._log_failure(
                request=request,
                error_type=exc.__class__.__name__,
            )

    def record_stream_turn(
        self,
        *,
        request: ConversationStreamRequest,
        response: ConversationMessageResponse,
        final_text: str,
        text_segment_count: int,
        tts_segment_count: int,
        audio_segment_count: int,
        tts_error_count: int,
        first_audio_url: str | None,
    ) -> None:
        try:
            self._repository.save_turn(
                self._stream_turn_write(
                    request=request,
                    response=response,
                    final_text=final_text,
                    text_segment_count=text_segment_count,
                    tts_segment_count=tts_segment_count,
                    audio_segment_count=audio_segment_count,
                    tts_error_count=tts_error_count,
                    first_audio_url=first_audio_url,
                )
            )
        except ConversationPersistenceRepositoryUnavailable as exc:
            self._log_failure(
                request=request,
                error_type=exc.__class__.__name__,
                event="conversation_stream_persistence_failed",
            )
        except Exception as exc:
            self._log_failure(
                request=request,
                error_type=exc.__class__.__name__,
                event="conversation_stream_persistence_failed",
            )

    def _turn_write(
        self,
        *,
        request: ConversationMessageRequest,
        response: ConversationMessageResponse,
        safety: SafetyClassification,
        intent: IntentClassification,
        route_decision: SceneRouteDecision,
        time_context: TimeContext,
    ) -> ConversationTurnWrite:
        child_message_id = f"msg_child_{uuid4().hex}"
        agent_message_id = f"msg_agent_{uuid4().hex}"
        safe_time_context = self._safe_time_context(time_context)
        return ConversationTurnWrite(
            session=ConversationSessionWrite(
                id=request.session_id,
                child_id=request.child_id,
                base_scene=route_decision.base_scene.value,
                active_scene=route_decision.active_scene.value,
                session_summary=None,
            ),
            child_message=ConversationMessageWrite(
                id=child_message_id,
                session_id=request.session_id,
                child_id=request.child_id,
                actor="child",
                message_type=request.input.type or "text",
                normalized_text=request.input.text,
                input_items=[{"type": request.input.type or "text"}],
                attachments=self._safe_attachments(request.input.attachments),
                audio_url=None,
                emotion=None,
                agent_motion=None,
                time_context=safe_time_context,
            ),
            agent_message=ConversationMessageWrite(
                id=agent_message_id,
                session_id=request.session_id,
                child_id=request.child_id,
                actor="agent",
                message_type=response.reply.type,
                normalized_text=response.reply.text,
                input_items=None,
                attachments=None,
                audio_url=response.reply.audio_url,
                emotion=response.reply.emotion,
                agent_motion=response.reply.agent_motion,
                time_context=safe_time_context,
            ),
            routing_decision=RoutingDecisionWrite(
                id=f"route_{uuid4().hex}",
                message_id=child_message_id,
                session_id=request.session_id,
                primary_intent=intent.intent.value,
                active_scene=route_decision.active_scene.value,
                sub_scene=intent.sub_intent,
                risk_level=safety.risk_level.value,
                decision={
                    "base_scene": route_decision.base_scene.value,
                    "active_scene": route_decision.active_scene.value,
                    "needs_input": route_decision.needs_input,
                    "requires_parent_attention": (
                        route_decision.requires_parent_attention
                    ),
                    "reply_emotion": response.reply.emotion,
                    "agent_motion": response.reply.agent_motion,
                },
                signals={
                    "attachment_count": len(request.input.attachments),
                    "safety_requires_parent_attention": (
                        safety.requires_parent_attention
                    ),
                    "intent_confidence": intent.confidence,
                },
                confidence=intent.confidence,
            ),
        )

    def _stream_turn_write(
        self,
        *,
        request: ConversationStreamRequest,
        response: ConversationMessageResponse,
        final_text: str,
        text_segment_count: int,
        tts_segment_count: int,
        audio_segment_count: int,
        tts_error_count: int,
        first_audio_url: str | None,
    ) -> ConversationTurnWrite:
        child_message_id = f"msg_child_{uuid4().hex}"
        agent_message_id = f"msg_agent_{uuid4().hex}"
        safe_time_context = self._safe_response_time_context(
            response=response,
            request=request,
        )
        primary_intent = self._response_intent(response)
        risk_level = self._response_risk_level(response)
        intent_confidence = self._response_intent_confidence(response)
        safety_requires_parent_attention = (
            response.debug.safety.requires_parent_attention
            if response.debug and response.debug.safety
            else response.session_state.requires_parent_attention is True
        )
        has_audio = audio_segment_count > 0
        stream_audio_summary = {
            "type": "stream_audio_summary",
            "has_audio": has_audio,
            "audio_segment_count": audio_segment_count,
            "tts_segment_count": tts_segment_count,
            "tts_error_count": tts_error_count,
            "text_segment_count": text_segment_count,
        }
        return ConversationTurnWrite(
            session=ConversationSessionWrite(
                id=request.session_id,
                child_id=request.child_id,
                base_scene=response.session_state.base_scene,
                active_scene=response.session_state.active_scene,
                session_summary=None,
            ),
            child_message=ConversationMessageWrite(
                id=child_message_id,
                session_id=request.session_id,
                child_id=request.child_id,
                actor="child",
                message_type=request.input.type or "text",
                normalized_text=request.input.text,
                input_items=[
                    {
                        "type": request.input.type or "text",
                        "delivery": "stream",
                    }
                ],
                attachments=self._safe_attachments(request.input.attachments),
                audio_url=None,
                emotion=None,
                agent_motion=None,
                time_context=safe_time_context,
            ),
            agent_message=ConversationMessageWrite(
                id=agent_message_id,
                session_id=request.session_id,
                child_id=request.child_id,
                actor="agent",
                message_type=response.reply.type,
                normalized_text=final_text or response.reply.text,
                input_items=[stream_audio_summary],
                attachments=None,
                audio_url=first_audio_url if has_audio else None,
                emotion=response.reply.emotion,
                agent_motion=response.reply.agent_motion,
                time_context=safe_time_context,
            ),
            routing_decision=RoutingDecisionWrite(
                id=f"route_{uuid4().hex}",
                message_id=child_message_id,
                session_id=request.session_id,
                primary_intent=primary_intent,
                active_scene=response.session_state.active_scene,
                sub_scene=self._response_sub_intent(response),
                risk_level=risk_level,
                decision={
                    "base_scene": response.session_state.base_scene,
                    "active_scene": response.session_state.active_scene,
                    "needs_input": response.session_state.needs_input,
                    "requires_parent_attention": (
                        response.session_state.requires_parent_attention is True
                    ),
                    "reply_emotion": response.reply.emotion,
                    "agent_motion": response.reply.agent_motion,
                    "delivery": "stream",
                },
                signals={
                    "attachment_count": len(request.input.attachments),
                    "safety_requires_parent_attention": (
                        safety_requires_parent_attention
                    ),
                    "intent_confidence": intent_confidence,
                    "stream_protocol_version": (
                        request.stream_options.protocol_version
                    ),
                    "include_tts": request.stream_options.include_tts,
                    "text_segment_count": text_segment_count,
                    "tts_segment_count": tts_segment_count,
                    "audio_segment_count": audio_segment_count,
                    "tts_error_count": tts_error_count,
                    "has_audio": has_audio,
                },
                confidence=intent_confidence,
            ),
        )

    def _safe_attachments(self, attachment_ids: list[str]) -> list[dict[str, Any]] | None:
        if not attachment_ids:
            return None
        return [
            {
                "id": attachment_id,
                "type": "attachment",
            }
            for attachment_id in attachment_ids
        ]

    def _safe_time_context(self, time_context: TimeContext) -> dict[str, Any]:
        return {
            "period": time_context.time_period.value,
            "timezone": time_context.timezone,
            "device_time_iso": time_context.now.isoformat(),
        }

    def _safe_response_time_context(
        self,
        *,
        response: ConversationMessageResponse,
        request: ConversationStreamRequest,
    ) -> dict[str, Any]:
        if response.debug:
            return self._safe_time_context(response.debug.time_context)
        return {
            "period": "unknown",
            "timezone": request.client_context.timezone,
            "device_time_iso": request.client_context.device_time.isoformat(),
        }

    def _response_intent(self, response: ConversationMessageResponse) -> str:
        if response.debug and response.debug.intent:
            return self._value(response.debug.intent.intent)
        return "unknown"

    def _response_sub_intent(
        self,
        response: ConversationMessageResponse,
    ) -> str | None:
        if response.debug and response.debug.intent:
            return response.debug.intent.sub_intent
        return None

    def _response_risk_level(self, response: ConversationMessageResponse) -> str:
        if response.debug and response.debug.safety:
            return self._value(response.debug.safety.risk_level)
        return "unknown"

    def _response_intent_confidence(
        self,
        response: ConversationMessageResponse,
    ) -> float | None:
        if response.debug and response.debug.intent:
            return response.debug.intent.confidence
        return None

    def _value(self, value: Any) -> str:
        raw_value = getattr(value, "value", value)
        return str(raw_value)

    def _log_failure(
        self,
        *,
        request: ConversationMessageRequest,
        error_type: str,
        event: str = "conversation_persistence_failed",
    ) -> None:
        logger.warning(
            event,
            extra={
                "event": event,
                "request_id": get_request_id(),
                "child_id_hash": hash_identifier(request.child_id),
                "session_id_hash": hash_identifier(request.session_id),
                "error_type": error_type,
            },
        )


_conversation_persistence_service = ConversationPersistenceService()


def get_conversation_persistence_service() -> ConversationPersistenceService:
    return _conversation_persistence_service
