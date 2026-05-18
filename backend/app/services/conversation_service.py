from app.domain.schemas.conversation import (
    ConversationDebug,
    ConversationMessageRequest,
    ConversationMessageResponse,
    IntentDebug,
    ParentPolicyDebug,
    QuickAction,
    Reply,
    SafetyDebug,
    SessionState,
    UiAction,
)
from app.domain.scene import SceneRouteDecision, SceneRouteRequest
from app.services.intent_classifier import (
    IntentClassifier,
    get_intent_classifier,
)
from app.services.parent_policy_service import (
    ParentPolicyService,
    get_parent_policy_service,
)
from app.services.safety_engine import SafetyEngine, get_safety_engine
from app.services.scene_orchestrator import (
    SceneOrchestrator,
    get_scene_orchestrator,
)
from app.services.time_context_service import (
    TimeContextService,
    get_time_context_service,
)


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
        debug_enabled: bool = True,
    ) -> None:
        self._time_context_service = time_context_service or get_time_context_service()
        self._parent_policy_service = (
            parent_policy_service or get_parent_policy_service()
        )
        self._safety_engine = safety_engine or get_safety_engine()
        self._intent_classifier = intent_classifier or get_intent_classifier()
        self._scene_orchestrator = scene_orchestrator or get_scene_orchestrator()
        self._debug_enabled = debug_enabled

    def handle_message(
        self, request: ConversationMessageRequest
    ) -> ConversationMessageResponse:
        parent_policy = self._parent_policy_service.get_policy(request.child_id)
        time_context = self._time_context_service.build_context(
            device_time=request.client_context.device_time,
            timezone=request.client_context.timezone,
            schedule=parent_policy.schedule,
        )
        safety = self._safety_engine.classify_input(request.input.text)
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
            )
        )
        response = self._response_from_route_decision(route_decision)

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
            )
        return response

    def _response_from_route_decision(
        self, decision: SceneRouteDecision
    ) -> ConversationMessageResponse:
        return ConversationMessageResponse(
            reply=Reply(
                text=decision.reply_text,
                emotion=decision.reply_emotion,
            ),
            ui_actions=[
                UiAction(
                    actions=[
                        QuickAction(id=action.id, label=action.label)
                        for action in decision.quick_actions
                    ]
                )
            ]
            if decision.quick_actions
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
