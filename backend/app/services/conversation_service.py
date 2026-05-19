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
from app.domain.enums import IntentType, RiskLevel
from app.domain.agent_runtime import AgentRuntimeRequest, AgentRuntimeResult
from app.domain.scene import SceneRouteDecision, SceneRouteRequest
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
from app.services.intent_classifier import (
    IntentClassification,
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
        attachment_service: AttachmentService | None = None,
        child_agent_runtime: ChildAgentRuntime | None = None,
        memory_hooks: ConversationMemoryHooks | None = None,
        debug_enabled: bool = True,
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
        homework_context = self._attachment_service.get_ready_homework_context(
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
        runtime_result = self._child_agent_runtime.run(
            AgentRuntimeRequest(
                child_id=request.child_id,
                session_id=request.session_id,
                child_text=request.input.text,
                route_decision=route_decision,
                time_context=time_context,
                parent_policy=parent_policy,
                memory_context=memory_context,
                conversation_metadata={
                    "app_mode": request.client_context.app_mode,
                    "input_type": request.input.type,
                    "attachment_count": len(request.input.attachments),
                },
            )
        )
        response = self._response_from_route_decision(route_decision, runtime_result)

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
        self._memory_hooks.record_turn(
            child_id=request.child_id,
            session_id=request.session_id,
            safety=safety,
            intent=intent,
            route_decision=route_decision,
        )
        return response

    def _response_from_route_decision(
        self,
        decision: SceneRouteDecision,
        runtime_result: AgentRuntimeResult,
    ) -> ConversationMessageResponse:
        return ConversationMessageResponse(
            reply=Reply(
                text=runtime_result.reply_text,
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
