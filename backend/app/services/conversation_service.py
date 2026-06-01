import logging
import re
import time

from app.core.logging import hash_identifier
from app.domain.companion_object import (
    CompanionObjectCreateRequest,
    CompanionObjectSource,
    CompanionObjectType,
    resolve_object_type_from_image,
)
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
from app.domain.scene import SceneId, SceneRouteDecision, SceneRouteRequest, SceneTransitionType
from app.domain.time import TimeContext
from app.middleware.request_id import get_request_id
from app.services.attachment_service import (
    AttachmentService,
    HomeworkAttachmentContext,
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
from app.services.light_co_creation_service import (
    CoCreationType,
    LightCoCreationService,
    get_light_co_creation_service,
)
from app.services.companion_object_service import (
    CompanionObjectService,
    get_companion_object_service,
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
        light_co_creation_service: LightCoCreationService | None = None,
        companion_object_service: CompanionObjectService | None = None,
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
        self._light_co_creation_service = (
            light_co_creation_service or get_light_co_creation_service()
        )
        self._companion_object_service = (
            companion_object_service
            if companion_object_service is not None
            else get_companion_object_service()
        )
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
        if (
            homework_context is None
            and not request.input.attachments
            and self._is_homework_followup_text(request.input.text)
        ):
            homework_context = self._attachment_service.get_latest_ready_homework_context(
                child_id=request.child_id,
                session_id=request.session_id,
            )
        if homework_context is not None and safety.risk_level == RiskLevel.NONE:
            guard_reply = self._homework_followup_guard_reply(
                child_text=request.input.text,
                homework_context=homework_context,
            )
            if guard_reply:
                response = ConversationMessageResponse(
                    reply=Reply(text=guard_reply, emotion="warm"),
                    ui_actions=[],
                    session_state=SessionState(
                        base_scene="conversation.open",
                        active_scene="learning.homework_help",
                        needs_input="problem_statement_confirm",
                    ),
                )
                self._persist_turn_if_enabled(
                    request=request,
                    response=response,
                    safety=safety,
                    intent=IntentClassification(
                        intent=IntentType.LEARNING_HELP,
                        sub_intent="homework_followup_guard",
                        risk_level=safety.risk_level,
                        needs_modality=False,
                        suggested_modalities=[],
                        confidence=0.95,
                        evidence=["deterministic_guard_reply"],
                    ),
                    route_decision=SceneRouteDecision(
                        message_id="",
                        session_id=request.session_id,
                        primary_intent=IntentType.LEARNING_HELP,
                        base_scene=SceneId.OPEN_CONVERSATION,
                        active_scene=SceneId.LEARNING_HOMEWORK_HELP,
                        transition=SceneTransitionType.REPLACE,
                        scene_stack=[SceneId.OPEN_CONVERSATION],
                        risk_level=RiskLevel.NONE,
                        confidence=0.95,
                        reason="homework_followup_guard",
                        reply_text=guard_reply,
                        reply_emotion="warm",
                    ),
                    time_context=self._time_context_service.build_context(
                        device_time=request.client_context.device_time,
                        timezone=request.client_context.timezone,
                    ),
                )
                return response
        image_context = self._attachment_service.get_image_context(
            request.input.attachments,
            child_id=request.child_id,
            session_id=request.session_id,
        )
        created_companion_action = self._check_pending_companion_seed_creation(
            child_id=request.child_id,
            session_id=request.session_id,
            child_text=request.input.text,
            quick_action_id=request.input.quick_action_id,
            image_context=image_context,
        )
        # E5: check companion extension before intent/routing
        extension_result = self._check_pending_companion_extension(
            child_id=request.child_id,
            session_id=request.session_id,
            child_text=request.input.text,
            quick_action_id=request.input.quick_action_id,
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
        # Companion object: check for skip/continue after recall
        companion_action_result = (
            created_companion_action
            or extension_result
            or self._check_companion_action(
                child_id=request.child_id,
                session_id=request.session_id,
                child_text=request.input.text,
                quick_action_id=request.input.quick_action_id,
                scene_id=route_decision.active_scene,
            )
        )
        # Lightweight pre-check for memory recall suppression.
        # Full turn_guidance is built inside ChildAgentRuntime after memory retrieval,
        # so we do a minimal boundary/engagement check here.
        bedtime = str(time_context.time_period) == "bedtime"
        child_engagement = self._pre_check_child_engagement(request.input.text)
        memory_context = self._memory_hooks.retrieve_context(
            child_id=request.child_id,
            current_text=request.input.text,
            limit=5,
            session_id=request.session_id,
            bedtime=bedtime,
            child_engagement=child_engagement,
            active_scene=route_decision.active_scene.value,
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
                intent=intent.intent.value if hasattr(intent.intent, "value") else str(intent.intent),
                sub_intent=intent.sub_intent,
            )
        )
        model_ms = self._elapsed_ms(model_started_at)

        # Update light co-creation state based on model response
        co_creation_type = runtime_result.model_metadata.get("co_creation_type", "none")
        if co_creation_type != "none":
            co_creation_enum = CoCreationType(co_creation_type)
            self._light_co_creation_service.record_co_creation_initiated(
                session_id=request.session_id,
                co_creation_type=co_creation_enum,
            )
            # Check if child rejected the co-creation
            child_engagement = runtime_result.model_metadata.get(
                "final_conversation_control", {}
            ).get("child_engagement", "neutral")
            if child_engagement in ("low", "short_or_flat"):
                self._light_co_creation_service.record_child_response(
                    session_id=request.session_id,
                    is_rejection=True,
                    is_low_interest=True,
                )
        response = self._response_from_route_decision(
            route_decision,
            runtime_result,
            child_text=request.input.text,
            parent_policy=parent_policy,
            companion_action=companion_action_result,
            image_context=image_context,
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

    _TOPIC_CHANGE_MARKERS = (
        "换个话题", "聊点别的", "别聊这个", "不说了", "算了", "今天不聊了",
        "不聊了", "不想聊了", "不要聊了",
    )
    _REFUSAL_MARKERS = (
        "不想聊了", "别问了", "你别说这个", "不要问了", "别再说了",
        "你别说了", "我不想说", "不告诉你", "就不说",
    )
    _BEDTIME_CLOSE_MARKERS = (
        "明天再聊", "我要睡觉", "我得睡觉", "晚安", "困了",
    )
    _SHORT_FLAT_REPLIES = (
        "嗯", "哦", "好吧", "不知道", "还行", "随便", "没有", "没了", "算了", "都行",
    )

    def _pre_check_child_engagement(self, child_text: str) -> str:
        """Lightweight engagement check before full turn_guidance is built."""
        normalized = child_text.strip().lower().replace(" ", "")
        # Explicit refusal: permanently block recalled topics this session.
        if any(m in normalized for m in self._REFUSAL_MARKERS):
            return "refused"
        if any(m in normalized for m in self._TOPIC_CHANGE_MARKERS):
            return "boundary"
        if any(m in normalized for m in self._BEDTIME_CLOSE_MARKERS):
            return "boundary"
        if normalized in self._SHORT_FLAT_REPLIES or len(normalized) <= 4:
            return "short_or_flat"
        return "neutral"

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

    # --- Companion object lightweight action detection ---

    _SKIP_SIGNALS = (
        "先聊别的", "先聊新的", "不想", "不要", "不知道",
        "换个话题", "聊别的", "说别的",
    )
    _COMPANION_NAME_PATTERNS = (
        r"(?:这颗星星|小星星|它|名字)?(?:就)?叫(?P<name>[^，。！？!?、\\s]{1,12})",
        r"名字(?:就)?叫(?P<name>[^，。！？!?、\\s]{1,12})",
        r"给它起名(?:叫)?(?P<name>[^，。！？!?、\\s]{1,12})",
    )

    def _extract_pending_companion_name(self, child_text: str) -> str | None:
        text = child_text.strip()
        if not text:
            return None
        compact = re.sub(r"\s+", "", text)
        if compact in {"起个名字", "起名字", "给它起个名字", "我想起个名字"}:
            return None
        for pattern in self._COMPANION_NAME_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group("name").strip("，。！？!?、,. ")
        plain = compact.strip("，。！？!?、,. ")
        if 1 <= len(plain) <= 8 and not any(marker in plain for marker in self._SKIP_SIGNALS):
            return plain
        return None

    def _check_pending_companion_seed_creation(
        self,
        *,
        child_id: str,
        session_id: str,
        child_text: str,
        quick_action_id: str | None,
        image_context: object | None = None,
    ) -> dict | None:
        svc = self._companion_object_service
        if svc is None:
            return None

        if quick_action_id == "companion_name":
            # E5: if pending extension exists, skip seed creation — let extension handle it
            if svc.get_pending_extension(session_id=session_id, child_id=child_id):
                return None
            # 图片分享场景：从当前 image_context 或最近附件获取 recognized_type
            recognized_type = None
            source_type = CompanionObjectSource.FIRST_OPEN
            if image_context is not None:
                recognized_type = getattr(image_context, "recognized_type", None)
                source_type = CompanionObjectSource.IMAGE_SHARE
            else:
                # 快速动作消息无附件，从最近图片附件查询
                recognized_type = self._attachment_service.get_latest_image_recognized_type(
                    child_id=child_id, session_id=session_id,
                )
                if recognized_type:
                    source_type = CompanionObjectSource.IMAGE_SHARE

            object_type_str = resolve_object_type_from_image(recognized_type)
            object_type = CompanionObjectType(object_type_str)

            svc.begin_seed_naming(
                session_id=session_id,
                child_id=child_id,
                object_type=object_type,
                light_location="窗边",
                source_type=source_type,
                recognized_image_type=recognized_type,
            )
            return None

        if quick_action_id == "companion_skip":
            svc.clear_pending_seed_naming(session_id=session_id)
            return None

        pending = svc.get_pending_seed_naming(session_id=session_id, child_id=child_id)
        if pending is None:
            return None

        companion_name = self._extract_pending_companion_name(child_text)
        if not companion_name:
            return None

        # 根据 pending 中的 recognized_image_type 推导 object_type
        object_type_str = resolve_object_type_from_image(pending.recognized_image_type)
        object_type = CompanionObjectType(object_type_str)

        # 构建 safe_summary：不保存图片细节
        if pending.source_type == CompanionObjectSource.IMAGE_SHARE:
            safe_summary = f"孩子给图片里的小东西起名为{companion_name}"
        else:
            safe_summary = f"这颗星星叫{companion_name}"

        try:
            companion = svc.create(
                CompanionObjectCreateRequest(
                    child_id=child_id,
                    name=companion_name,
                    object_type=object_type,
                    source_type=pending.source_type,
                    safe_summary=safe_summary,
                    light_location=pending.light_location,
                )
            )
        except Exception:
            return None

        svc.clear_pending_seed_naming(session_id=session_id)
        return {"action": "co_create", "companion": companion}

    def _check_pending_companion_extension(
        self,
        *,
        child_id: str,
        session_id: str,
        child_text: str,
        quick_action_id: str | None,
    ) -> dict | None:
        """E5: Check if child is in 'add a friend' extension flow.

        Returns a dict with extension result if consumed, None otherwise.
        """
        svc = self._companion_object_service
        if svc is None:
            return None

        # Handle extension quick actions
        if quick_action_id == "companion_skip":
            svc.clear_pending_extension(session_id=session_id)
            return {"action": "skip"}

        if quick_action_id in ("companion_friend_name", "companion_friend_image"):
            # Just acknowledge — child needs to provide name or image next
            return None

        pending = svc.get_pending_extension(session_id=session_id, child_id=child_id)
        if pending is None:
            return None

        # Skip signals during extension
        text = child_text.strip()
        if any(signal in text for signal in self._SKIP_SIGNALS):
            svc.clear_pending_extension(session_id=session_id)
            return {"action": "skip"}

        companion_name = self._extract_pending_companion_name(child_text)
        if not companion_name:
            return None

        # Update existing companion's safe_summary
        append_text = f"孩子给小屋小客人加了一个小伙伴：{companion_name}"
        updated = svc.update_safe_summary_append(pending.companion_id, append_text)
        if updated is None:
            svc.clear_pending_extension(session_id=session_id)
            return None

        svc.clear_pending_extension(session_id=session_id)
        return {
            "action": "extension_done",
            "companion": updated,
            "friend_name": companion_name,
        }

    def _check_companion_action(
        self,
        *,
        child_id: str,
        session_id: str,
        child_text: str,
        quick_action_id: str | None,
        scene_id: object,
    ) -> dict | None:
        """Check if child is responding to a companion recall.

        Returns a dict with companion info if action was taken, None otherwise.
        """
        from app.domain.scene import SceneId as _SceneId

        # Only process companion actions in safe scenes
        if scene_id in (
            _SceneId.SAFETY_GUARDIAN,
            _SceneId.SAFETY_GENTLE_CHECKIN,
            _SceneId.PRIVACY_BOUNDARY,
            _SceneId.LEARNING_HOMEWORK_HELP,
            _SceneId.DAILY_BEDTIME_REFLECTION,
        ):
            return None

        svc = self._companion_object_service
        if svc is None:
            return None

        companion = svc.get_active_by_child(child_id)
        if companion is None:
            return None

        # E5: if extension is pending, let extension handler deal with name input
        if svc.get_pending_extension(session_id=session_id, child_id=child_id):
            return None

        text = child_text.strip()

        if quick_action_id == "companion_skip":
            svc.mark_skipped(companion.id, session_id=session_id)
            return {"action": "skip", "companion": companion}

        if quick_action_id == "companion_continue":
            # E5: enter "add a friend" extension flow instead of direct co_create
            svc.begin_extension(
                session_id=session_id,
                child_id=child_id,
                companion_id=companion.id,
                companion_name=companion.name,
            )
            return {
                "action": "co_create_guidance",
                "companion": companion,
            }

        # Skip detection
        if any(signal in text for signal in self._SKIP_SIGNALS):
            svc.mark_skipped(companion.id, session_id=session_id)
            return {"action": "skip", "companion": companion}

        # Continue detection: child mentions the companion name
        if companion.name and companion.name in text:
            # Child is engaging with the companion
            return {"action": "co_create", "companion": companion}

        return None

    def _response_from_route_decision(
        self,
        decision: SceneRouteDecision,
        runtime_result: AgentRuntimeResult,
        *,
        child_text: str,
        parent_policy: object | None,
        companion_action: dict | None = None,
        image_context: object | None = None,
    ) -> ConversationMessageResponse:
        # Build companion metadata if companion is active
        companion_meta = None
        is_new_companion = False
        is_extension_done = False
        if companion_action is not None:
            companion = companion_action.get("companion")
            action = companion_action.get("action", "none")
            if companion is not None:
                from app.domain.companion_object import resolve_visual_kind
                from app.domain.schemas.conversation import CompanionObjectMeta
                companion_meta = CompanionObjectMeta(
                    id=str(companion.id),
                    name=companion.name,
                    object_type=companion.object_type,
                    light_location=companion.light_location,
                    state=companion.status,
                    action=action if action in ("recall", "co_create") else "none",
                    visual_kind=getattr(companion, "visual_kind", None)
                        or resolve_visual_kind(companion.object_type),
                )
                if action == "co_create":
                    is_new_companion = True
                elif action == "extension_done":
                    is_extension_done = True

        # E5: "add a friend" guidance — show guidance text + quick_actions
        is_co_create_guidance = (
            companion_action is not None
            and companion_action.get("action") == "co_create_guidance"
        )
        if is_co_create_guidance and companion_meta is not None:
            reply_text = "那我们给它找一个小伙伴\n你可以说一个名字，也可以给我看看"
            reply_emotion = "warm"
            quick_actions = [
                QuickAction(id="companion_friend_name", label="说个名字"),
                QuickAction(id="companion_friend_image", label="给小白狐看看"),
                QuickAction(id="companion_skip", label="先聊别的"),
            ]
            companion_meta = companion_meta.model_copy(
                update={"action": "co_create"},
            )
        # 新建 companion（起名成功）：使用确定性模板，不返回 quick_actions
        elif is_new_companion and companion_meta is not None:
            name = companion_meta.name
            location = companion_meta.light_location or "窗边"
            reply_text = f"{name}，软软的名字\n它轻轻落到{location}啦"
            reply_emotion = "warm"
            quick_actions: list = []
        # E5: extension done — companion updated, show completion feedback
        elif is_extension_done and companion_meta is not None:
            # name in meta is the ORIGINAL companion name; use extension friend name
            friend_name = (companion_action or {}).get("friend_name", companion_meta.name)
            reply_text = f"{friend_name}，也来小屋里待一会儿啦"
            reply_emotion = "warm"
            quick_actions = []
            companion_meta = companion_meta.model_copy(
                update={"action": "co_create"},
            )
        else:
            reply_text = runtime_result.reply_text
            reply_emotion = decision.reply_emotion
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
                text=reply_text,
                emotion=reply_emotion,
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
                companion_object=companion_meta,
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

    _HOMEWORK_FOLLOWUP_KEYWORDS = (
        "第", "题", "这道", "那道", "题目", "怎么做", "不会",
        "三位数", "两位数", "开头", "刚才", "那题",
    )

    def _is_homework_followup_text(self, text: str) -> bool:
        normalized = text.strip()
        if not normalized:
            return False
        return any(kw in normalized for kw in self._HOMEWORK_FOLLOWUP_KEYWORDS)

    _PROBLEM_NUMBER_EXTRACT = re.compile(r"第\s*([一二三四五六七八九十\d]+)\s*题")
    _NUMBER_MAP = {
        "一": "1", "二": "2", "三": "3", "四": "4", "五": "5",
        "六": "6", "七": "7", "八": "8", "九": "9", "十": "10",
    }
    _CONFLICT_NUMBER_PATTERN = re.compile(
        r"(?:和是|和为|等于)\s*(\d{5,})"
    )

    def _homework_followup_guard_reply(
        self,
        *,
        child_text: str,
        homework_context: HomeworkAttachmentContext,
    ) -> str | None:
        text = child_text.strip()
        hw_text = homework_context.recognized_content.text or ""

        match = self._PROBLEM_NUMBER_EXTRACT.search(text)
        if match:
            num_str = match.group(1)
            if num_str in self._NUMBER_MAP:
                num_str = self._NUMBER_MAP[num_str]
            problem_section = self._extract_problem_section(hw_text, num_str)
            if problem_section:
                summary = problem_section[:40].strip("，,、；;：:")
                if len(problem_section) > 40:
                    summary += "……"
                return (
                    f"我先对一下，是第{num_str}题这个“{summary}”吗？"
                    "如果是，我们先看它问的是什么。"
                )
            return (
                f"我怕看串题了。你再读一下第{num_str}题开头几个字，我先把题目对准。"
            )

        if "这道题" in text or "那道题" in text:
            problem_count = self._count_problems(hw_text)
            if problem_count >= 2:
                return (
                    "我怕看串题了。你告诉我题号，或者读一下题目开头几个字，我先把题目对准。"
                )

        conflict_match = self._CONFLICT_NUMBER_PATTERN.search(text)
        if conflict_match:
            spoken_number = conflict_match.group(1)
            correct_number = self._find_likely_correct_number(hw_text, spoken_number)
            if correct_number:
                return (
                    f"我看图片里这一题像是 {correct_number}，不是你刚才读的那个数。"
                    f"我们先按图片里的 {correct_number} 来看，好吗？"
                )

        return None

    @staticmethod
    def _extract_problem_section(hw_text: str, num: str) -> str | None:
        patterns = [
            rf"第\s*{num}\s*题\s*[：:]\s*",
            rf"{num}\s*[\.、]\s*",
            rf"[（(]\s*{num}\s*[)）]\s*",
        ]
        for pattern in patterns:
            match = re.search(pattern, hw_text)
            if match:
                start = match.end()
                remainder = hw_text[start:]
                next_problem = re.search(
                    r"(?:第\s*[\d一二三四五六七八九十]+\s*题|[\d]+\s*[\.、]|[（(]\s*[\d]+\s*[)）])",
                    remainder,
                )
                if next_problem:
                    return remainder[: next_problem.start()].strip()
                return remainder.strip()
        return None

    @staticmethod
    def _count_problems(hw_text: str) -> int:
        return len(re.findall(
            r"(?:第\s*[\d一二三四五六七八九十]+\s*题|[\d]+\s*[\.、]|[（(]\s*[\d]+\s*[)）])",
            hw_text,
        ))

    @staticmethod
    def _find_likely_correct_number(hw_text: str, spoken_number: str) -> str | None:
        four_digit = re.findall(r"\d{4}", hw_text)
        for num in four_digit:
            if num in spoken_number and num != spoken_number:
                return num
        return None

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
