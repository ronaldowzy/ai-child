import logging
import time

from app.core.logging import hash_identifier
from app.domain.agent_runtime import AgentRuntimeRequest, AgentRuntimeResult
from app.domain.enums import IntentType, RiskLevel
from app.domain.schemas.conversation import (
    ConversationDebug,
    ConversationMessageRequest,
    ConversationMessageResponse,
    HealthyEngagementDebug,
    IntentDebug,
    ParentPolicyDebug,
    QuickAction,
    Reply,
    SafetyDebug,
    SessionState,
    UiAction,
)
from app.domain.scene import SceneId, SceneRouteDecision, SceneRouteRequest
from app.domain.time import TimeContext
from app.middleware.request_id import get_request_id
from app.services.attachment_service import (
    AttachmentService,
    get_attachment_service,
)
from app.services.child_agent_runtime import (
    ChildAgentRuntime,
    get_child_agent_runtime,
)
from app.services.conversation_memory_hooks import (
    ConversationMemoryHooks,
    get_conversation_memory_hooks,
)
from app.services.conversation_history_service import (
    ConversationHistoryService,
    get_conversation_history_service,
)
from app.services.conversation_persistence_service import (
    ConversationPersistenceService,
    get_conversation_persistence_service,
)
from app.services.intent_classifier import (
    IntentClassification,
    IntentClassifier,
    get_intent_classifier,
)
from app.services.parent_policy_service import (
    ParentPolicyService,
    get_parent_policy_service,
)
from app.services.quick_action_service import (
    QuickActionService,
    get_quick_action_service,
)
from app.services.safety_engine import (
    SafetyClassification,
    SafetyEngine,
    get_safety_engine,
)
from app.services.scene_orchestrator import (
    SceneOrchestrator,
    get_scene_orchestrator,
)
from app.services.time_context_service import (
    TimeContextService,
    get_time_context_service,
)
from app.services.tts_service import TtsService, get_tts_service


logger = logging.getLogger("app.conversation")
healthy_engagement_logger = logging.getLogger("app.healthy_engagement")


class ConversationService:
    """Conversation gateway service that wires context, safety, intent, and scenes."""

    def __init__(
        self,
        *,
        time_context_service: TimeContextService | None = None,
        parent_policy_service: ParentPolicyService | None = None,
        safety_engine: SafetyEngine | None = None,
        intent_classifier: IntentClassifier | None = None,
        scene_orchestrator: SceneOrchestrator | None = None,
        attachment_service: AttachmentService | None = None,
        child_agent_runtime: ChildAgentRuntime | None = None,
        memory_hooks: ConversationMemoryHooks | None = None,
        conversation_history_service: ConversationHistoryService | None = None,
        conversation_persistence_service: ConversationPersistenceService | None = None,
        quick_action_service: QuickActionService | None = None,
        tts_service: TtsService | None = None,
        debug_enabled: bool = True,
        persistence_enabled: bool = True,
    ) -> None:
        self._time_context_service = time_context_service or get_time_context_service()
        self._parent_policy_service = (
            parent_policy_service or get_parent_policy_service()
        )
        self._safety_engine = safety_engine or get_safety_engine()
        self._intent_classifier = intent_classifier or get_intent_classifier()
        self._scene_orchestrator = scene_orchestrator or get_scene_orchestrator()
        self._attachment_service = attachment_service or get_attachment_service()
        self._child_agent_runtime = child_agent_runtime or get_child_agent_runtime()
        self._memory_hooks = memory_hooks or get_conversation_memory_hooks()
        self._conversation_history_service = (
            conversation_history_service or get_conversation_history_service()
        )
        self._conversation_persistence_service = (
            conversation_persistence_service or get_conversation_persistence_service()
        )
        self._quick_action_service = quick_action_service or get_quick_action_service()
        self._tts_service = tts_service or get_tts_service()
        self._debug_enabled = debug_enabled
        self._persistence_enabled = persistence_enabled

    def handle_message(
        self, request: ConversationMessageRequest
    ) -> ConversationMessageResponse:
        started_at = time.perf_counter()
        request_start = time.time()
        parent_policy = self._parent_policy_service.get_policy(request.child_id)
        time_context = self._time_context_service.build_context(
            device_time=request.client_context.device_time,
            timezone=request.client_context.timezone,
            schedule=parent_policy.schedule,
        )
        safety = self._safety_engine.classify_input(request.input.text)
        homework_context = self._attachment_service.get_ready_homework_context(
            request.input.attachments,
            child_id=request.child_id,
            session_id=request.session_id,
        )
        image_context = self._attachment_service.get_image_context(
            request.input.attachments,
            child_id=request.child_id,
            session_id=request.session_id,
        )
        use_homework_attachment = (
            homework_context is not None and safety.risk_level == RiskLevel.NONE
        )
        if use_homework_attachment:
            intent = IntentClassification(
                intent=IntentType.LEARNING_HELP,
                sub_intent="homework_problem_with_attachment",
                risk_level=safety.risk_level,
                needs_modality=False,
                suggested_modalities=[],
                confidence=0.96,
                evidence=["attachment_id_ready"],
            )
        elif image_context and image_context.recognized_type == "privacy_sensitive":
            intent = IntentClassification(
                intent=IntentType.PRIVACY_QUESTION,
                sub_intent="privacy_boundary",
                risk_level=RiskLevel.LOW,
                needs_modality=False,
                suggested_modalities=[],
                confidence=0.9,
                evidence=["image_privacy_context"],
            )
        else:
            intent = self._intent_classifier.classify(
                request.input.text,
                time_context=time_context,
                safety=safety,
            )
        route_decision = self._scene_orchestrator.route(
            SceneRouteRequest(
                child_id=request.child_id,
                session_id=request.session_id,
                text=request.input.text,
                time_context=time_context,
                intent=intent.intent,
                sub_intent=intent.sub_intent,
                intent_confidence=intent.confidence,
                intent_evidence=intent.evidence,
                needs_modality=intent.needs_modality,
                suggested_modalities=intent.suggested_modalities,
                risk_level=safety.risk_level,
                safety_requires_parent_attention=safety.requires_parent_attention,
                safety_evidence=safety.evidence,
                parent_goals=parent_policy.goals,
                homework_problem_text=(
                    homework_context.recognized_content.text
                    if use_homework_attachment and homework_context
                    else None
                ),
                homework_problem_confidence=(
                    homework_context.recognized_content.confidence
                    if use_homework_attachment and homework_context
                    else None
                ),
            )
        )
        memory_context = self._memory_hooks.retrieve_context(
            child_id=request.child_id,
            current_text=request.input.text,
            limit=5,
        )
        conversation_history = []
        if route_decision.active_scene == SceneId.OPEN_CONVERSATION:
            conversation_history = (
                self._conversation_history_service.get_recent_model_messages(
                    session_id=request.session_id,
                    limit=6,
                )
            )
        prompt_image_context = (
            image_context.to_prompt_context()
            if image_context is not None
            else homework_context.to_prompt_context()
            if homework_context is not None
            else None
        )
        model_started_at = time.perf_counter()
        runtime_result = self._child_agent_runtime.run(
            AgentRuntimeRequest(
                child_id=request.child_id,
                session_id=request.session_id,
                child_text=request.input.text,
                route_decision=route_decision,
                time_context=time_context,
                parent_policy=parent_policy,
                memory_context=memory_context,
                conversation_history=conversation_history,
                conversation_metadata={
                    "app_mode": request.client_context.app_mode,
                    "input_type": request.input.type,
                    "attachment_count": len(request.input.attachments),
                    "contains_image": image_context is not None
                    or homework_context is not None,
                    "image_context": prompt_image_context,
                },
            )
        )
        model_ms = self._elapsed_ms(model_started_at)
        response = self._response_from_route_decision(
            route_decision,
            runtime_result,
            child_text=request.input.text,
            parent_policy=parent_policy,
        )
        tts_ms = self._attach_audio_url_if_enabled(response)
        self._persist_turn_if_enabled(
            request=request,
            response=response,
            safety=safety,
            intent=intent,
            route_decision=route_decision,
            time_context=time_context,
        )
        self._log_non_sensitive_turn_summary(
            request=request,
            route_decision=route_decision,
            runtime_result=runtime_result,
            response=response,
        )
        healthy_engagement_debug = self._healthy_engagement_debug(
            runtime_result,
            turn_total_ms=self._elapsed_ms(started_at),
        )
        self._log_healthy_engagement_metrics(
            request=request,
            runtime_result=runtime_result,
            healthy_engagement=healthy_engagement_debug,
        )
        self._log_conversation_latency(
            request=request,
            route_decision=route_decision,
            response=response,
            request_start=request_start,
            model_ms=model_ms,
            tts_ms=tts_ms,
            turn_total_ms=self._elapsed_ms(started_at),
        )

        if self._debug_enabled:
            response.debug = ConversationDebug(
                time_context=time_context,
                parent_policy=ParentPolicyDebug(
                    goals=parent_policy.goals,
                    communication_preferences=parent_policy.communication_preferences,
                    safety_rules=parent_policy.safety_rules,
                ),
                safety=SafetyDebug(
                    risk_level=safety.risk_level,
                    primary_category=safety.primary_category,
                    categories=safety.categories,
                    requires_parent_attention=safety.requires_parent_attention,
                    evidence=safety.evidence,
                    safe_response_hint=safety.safe_response_hint,
                ),
                intent=IntentDebug(
                    intent=intent.intent,
                    sub_intent=intent.sub_intent,
                    emotion=intent.emotion,
                    risk_level=intent.risk_level,
                    needs_modality=intent.needs_modality,
                    suggested_modalities=intent.suggested_modalities,
                    confidence=intent.confidence,
                    evidence=intent.evidence,
                ),
                healthy_engagement=healthy_engagement_debug,
            )
        try:
            self._memory_hooks.record_turn(
                child_id=request.child_id,
                session_id=request.session_id,
                child_text=request.input.text,
                safety=safety,
                intent=intent,
                route_decision=route_decision,
            )
        except Exception as exc:
            logger.warning(
                "conversation_memory_hook_failed",
                extra={
                    "event": "conversation_memory_hook_failed",
                    "request_id": get_request_id(),
                    "child_id_hash": hash_identifier(request.child_id),
                    "session_id_hash": hash_identifier(request.session_id),
                    "error_type": exc.__class__.__name__,
                },
            )
        self._conversation_history_service.record_turn(
            session_id=request.session_id,
            child_text=request.input.text,
            agent_text=response.reply.text,
        )
        return response

    def _persist_turn_if_enabled(
        self,
        *,
        request: ConversationMessageRequest,
        response: ConversationMessageResponse,
        safety: SafetyClassification,
        intent: IntentClassification,
        route_decision: SceneRouteDecision,
        time_context: TimeContext,
    ) -> None:
        if not self._persistence_enabled:
            return
        try:
            self._conversation_persistence_service.record_turn(
                request=request,
                response=response,
                safety=safety,
                intent=intent,
                route_decision=route_decision,
                time_context=time_context,
            )
        except Exception as exc:
            logger.warning(
                "conversation_persistence_failed",
                extra={
                    "event": "conversation_persistence_failed",
                    "request_id": get_request_id(),
                    "child_id_hash": hash_identifier(request.child_id),
                    "session_id_hash": hash_identifier(request.session_id),
                    "error_type": exc.__class__.__name__,
                },
            )

    def _log_non_sensitive_turn_summary(
        self,
        *,
        request: ConversationMessageRequest,
        route_decision: SceneRouteDecision,
        runtime_result: AgentRuntimeResult,
        response: ConversationMessageResponse,
    ) -> None:
        logger.info(
            "conversation_turn_summary",
            extra={
                "event": "conversation_turn_summary",
                "request_id": get_request_id(),
                "child_id_hash": hash_identifier(request.child_id),
                "session_id_hash": hash_identifier(request.session_id),
                "scene": route_decision.active_scene.value,
                "runtime_source": runtime_result.source.value,
                "fallback_reason": runtime_result.fallback_reason,
                "reply_chars": len(response.reply.text),
                "reply_normalized": (
                    runtime_result.model_metadata.get("reply_normalized") is True
                ),
                "audio_url_present": response.reply.audio_url is not None,
                "quick_actions": len(response.ui_actions),
            },
        )

    def _healthy_engagement_debug(
        self,
        runtime_result: AgentRuntimeResult,
        *,
        turn_total_ms: float,
    ) -> HealthyEngagementDebug | None:
        metrics = runtime_result.model_metadata.get("healthy_engagement")
        if not isinstance(metrics, dict):
            return None
        sanitized_metrics = dict(metrics)
        sanitized_metrics["turn_total_ms"] = turn_total_ms
        try:
            return HealthyEngagementDebug.model_validate(sanitized_metrics)
        except Exception:
            return None

    def _log_healthy_engagement_metrics(
        self,
        *,
        request: ConversationMessageRequest,
        runtime_result: AgentRuntimeResult,
        healthy_engagement: HealthyEngagementDebug | None,
    ) -> None:
        if healthy_engagement is None:
            return
        payload = healthy_engagement.model_dump(mode="json")
        payload.update(
            {
                "event": "healthy_engagement_turn",
                "request_id": get_request_id(),
                "child_id_hash": hash_identifier(request.child_id),
                "session_id_hash": hash_identifier(request.session_id),
                "runtime_source": runtime_result.source.value,
                "fallback_reason": runtime_result.fallback_reason,
            }
        )
        try:
            healthy_engagement_logger.info(
                "healthy_engagement_turn",
                extra=payload,
            )
        except Exception as exc:
            logger.warning(
                "healthy_engagement_log_failed",
                extra={
                    "event": "healthy_engagement_log_failed",
                    "request_id": get_request_id(),
                    "child_id_hash": hash_identifier(request.child_id),
                    "session_id_hash": hash_identifier(request.session_id),
                    "error_type": exc.__class__.__name__,
                },
            )

    def _elapsed_ms(self, started_at: float) -> float:
        return round((time.perf_counter() - started_at) * 1000, 1)

    def _response_from_route_decision(
        self,
        decision: SceneRouteDecision,
        runtime_result: AgentRuntimeResult,
        *,
        child_text: str,
        parent_policy: object | None,
    ) -> ConversationMessageResponse:
        quick_actions = self._quick_action_service.actions_for(
            decision=decision,
            child_text=child_text,
            reply_text=runtime_result.reply_text,
            parent_policy=parent_policy,
            conversation_control=runtime_result.model_metadata.get(
                "final_conversation_control"
            ),
        )
        return ConversationMessageResponse(
            reply=Reply(
                text=runtime_result.reply_text,
                emotion=decision.reply_emotion,
                agent_motion=self._agent_motion_for(decision),
            ),
            ui_actions=[
                UiAction(
                    actions=[
                        QuickAction(id=action.id, label=action.label)
                        for action in quick_actions
                    ]
                )
            ]
            if quick_actions
            else [],
            session_state=SessionState(
                base_scene=decision.base_scene.value,
                active_scene=decision.active_scene.value,
                needs_input=decision.needs_input,
                requires_parent_attention=(
                    True if decision.requires_parent_attention else None
                ),
            ),
        )

    def _attach_audio_url_if_enabled(
        self,
        response: ConversationMessageResponse,
    ) -> float | None:
        if not response.reply.voice_enabled:
            return None
        started_at = time.perf_counter()
        try:
            audio_url = self._tts_service.generate_for_conversation(
                text=response.reply.text,
                emotion=response.reply.emotion,
            )
        except Exception:
            return self._elapsed_ms(started_at)
        if audio_url:
            response.reply.audio_url = audio_url
        return self._elapsed_ms(started_at)

    def _log_conversation_latency(
        self,
        *,
        request: ConversationMessageRequest,
        route_decision: SceneRouteDecision,
        response: ConversationMessageResponse,
        request_start: float,
        model_ms: float,
        tts_ms: float | None,
        turn_total_ms: float,
    ) -> None:
        logger.info(
            "conversation_turn_latency",
            extra={
                "event": "conversation_turn_latency",
                "request_id": get_request_id(),
                "request_start": request_start,
                "child_id_hash": hash_identifier(request.child_id),
                "session_id_hash": hash_identifier(request.session_id),
                "active_scene": route_decision.active_scene.value,
                "model_ms": model_ms,
                "tts_ms": tts_ms,
                "audio_url_present": response.reply.audio_url is not None,
                "turn_total_ms": turn_total_ms,
            },
        )

    def _agent_motion_for(self, decision: SceneRouteDecision) -> str:
        active_scene = decision.active_scene.value
        if active_scene == "learning.homework_help":
            return "thinking_nod"
        if active_scene == "daily.bedtime_reflection":
            return "sleepy_blink"
        if active_scene == "safety.guardian":
            return "concerned_still"
        if active_scene == "safety.gentle_checkin":
            return "gentle_nod"
        if active_scene == "privacy.boundary":
            return "steady_boundary"
        if decision.reply_emotion == "calm":
            return "calm_breathe"
        return "listening_tail"
