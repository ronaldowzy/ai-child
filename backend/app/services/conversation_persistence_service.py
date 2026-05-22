import logging
from typing import Any
from uuid import uuid4

from app.core.logging import hash_identifier
from app.domain.schemas.conversation import (
    ConversationMessageRequest,
    ConversationMessageResponse,
)
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

    def _log_failure(
        self,
        *,
        request: ConversationMessageRequest,
        error_type: str,
    ) -> None:
        logger.warning(
            "conversation_persistence_failed",
            extra={
                "event": "conversation_persistence_failed",
                "request_id": get_request_id(),
                "child_id_hash": hash_identifier(request.child_id),
                "session_id_hash": hash_identifier(request.session_id),
                "error_type": error_type,
            },
        )


_conversation_persistence_service = ConversationPersistenceService()


def get_conversation_persistence_service() -> ConversationPersistenceService:
    return _conversation_persistence_service
