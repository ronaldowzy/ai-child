from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from contextvars import copy_context
from dataclasses import dataclass
import hashlib
import logging
import time

from app.core.logging import hash_identifier
from app.core.config import get_settings
from app.domain.memory import MemorySensitivity
from app.domain.schemas.conversation import (
    CompanionObjectMeta,
    ConversationMessageResponse,
    ConversationOpeningRequest,
    QuickAction,
    Reply,
    SessionState,
    UiAction,
)
from app.domain.schemas.parent_policy import ParentPolicy
from app.domain.time import TimeContext, TimePeriod
from app.domain.model_types import ModelMessage, ModelRequest, ModelTaskType
from app.services.memory_service import MemoryService, get_memory_service
from app.services.model_registry import ModelRegistry, get_model_registry
from app.services.opening_policy import (
    OpeningMode,
    OpeningPolicy,
    OpeningPolicyBuilder,
)
from app.services.parent_policy_service import (
    ParentPolicyService,
    get_parent_policy_service,
)
from app.services.conversation_history_service import (
    ConversationHistoryService,
    get_conversation_history_service,
)
from app.services.relationship_memory import (
    latest_interest_seed,
    latest_show_and_tell_event,
    latest_unfinished_thread,
)
from app.services.time_context_service import (
    TimeContextService,
    get_time_context_service,
)
from app.services.tts_service import TtsService, get_tts_service
from app.domain.schemas.child_profile import render_child_profile_for_prompt
from app.middleware.request_id import get_request_id


logger = logging.getLogger("app.opening_timing")
DEFAULT_OPENING_TTS_SOFT_TIMEOUT_MS = 15000


@dataclass(frozen=True)
class _ModelOpeningResult:
    text: str
    model_ms: float
    fallback_used: bool
    error_type: str | None = None


@dataclass(frozen=True)
class _OpeningTtsResult:
    tts_ms: float
    audio_url_present: bool
    error_type: str | None = None


@dataclass(frozen=True)
class _OpeningCacheInfo:
    fallback_used: bool
    audio_url_present: bool


class OpeningService:
    """Builds one short child-safe opening greeting per app session."""

    def __init__(
        self,
        *,
        parent_policy_service: ParentPolicyService | None = None,
        time_context_service: TimeContextService | None = None,
        tts_service: TtsService | None = None,
        model_registry: ModelRegistry | None = None,
        memory_service: MemoryService | None = None,
        opening_policy_builder: OpeningPolicyBuilder | None = None,
        model_soft_timeout_ms: int | None = None,
        tts_soft_timeout_ms: int | None = None,
        companion_object_service: object | None = None,
        conversation_history_service: ConversationHistoryService | None = None,
    ) -> None:
        self._parent_policy_service = (
            parent_policy_service or get_parent_policy_service()
        )
        self._time_context_service = time_context_service or get_time_context_service()
        self._tts_service = tts_service or get_tts_service()
        self._model_registry = model_registry or get_model_registry()
        self._memory_service = memory_service or get_memory_service()
        self._opening_policy_builder = (
            opening_policy_builder
            or OpeningPolicyBuilder(memory_service=self._memory_service)
        )
        self._companion_object_service = companion_object_service
        self._conversation_history_service = (
            conversation_history_service or get_conversation_history_service()
        )
        self._model_soft_timeout_ms = (
            model_soft_timeout_ms
            if model_soft_timeout_ms is not None
            else get_settings().opening_model_soft_timeout_ms
        )
        self._tts_soft_timeout_ms = (
            tts_soft_timeout_ms
            if tts_soft_timeout_ms is not None
            else get_settings().opening_tts_soft_timeout_ms
        )
        self._session_cache: dict[tuple[str, str], ConversationMessageResponse] = {}
        self._session_cache_info: dict[tuple[str, str], _OpeningCacheInfo] = {}

    def _check_companion_recall(
        self,
        *,
        child_id: str,
        session_id: str,
        bedtime: bool,
        current_mode: OpeningMode,
    ) -> object | None:
        """Check if a companion object should be recalled at opening.

        Returns the companion object if recall is appropriate, None otherwise.
        Recall is blocked when:
        - bedtime (never recall at bedtime)
        - mode is already safety/privacy/boundary/low_expression
        - no companion_object_service configured
        """
        if self._companion_object_service is None:
            return None
        if bedtime:
            return None
        # Don't override safety/boundary/low_expression modes
        if current_mode in (
            OpeningMode.BOUNDARY_RESPECT,
            OpeningMode.LOW_EXPRESSION_SUPPORT,
        ):
            return None
        try:
            companion = self._companion_object_service.can_recall(
                child_id, session_id=session_id, is_bedtime=False,
            )
            return companion
        except Exception as exc:
            logger.warning(
                "companion_recall_check_failed: %s: %s",
                exc.__class__.__name__,
                exc,
            )
            return None

    def _check_star_seed_eligible(
        self,
        *,
        child_id: str,
        bedtime: bool,
        current_mode: OpeningMode,
    ) -> bool:
        """Check if first-open star naming seed should be offered.

        Returns True if:
        - companion_object_service is configured
        - not bedtime
        - child has no companion history (no active, paused, or retired)
        - current mode is safe (DEFAULT_LIGHT or INTEREST_CALLBACK)
        """
        if self._companion_object_service is None:
            return False
        if bedtime:
            return False
        if current_mode not in (OpeningMode.DEFAULT_LIGHT, OpeningMode.INTEREST_CALLBACK):
            return False
        try:
            # Check if child has any companion history
            existing = self._companion_object_service.get_active_by_child(child_id)
            if existing is not None:
                return False
            # Also check paused companions (don't offer seed if child has history)
            paused = getattr(self._companion_object_service, '_get_active_or_paused_by_child', None)
            if paused:
                try:
                    result = paused(child_id)
                    if result is not None:
                        return False
                except Exception:
                    pass
            return True
        except Exception:
            return False

    def create_opening(
        self,
        request: ConversationOpeningRequest,
    ) -> ConversationMessageResponse:
        cache_key = (request.child_id, request.session_id)
        started_at = time.perf_counter()
        cached = self._session_cache.get(cache_key)
        if cached is not None:
            cache_info = self._session_cache_info.get(cache_key)
            self._log_opening_finished(
                request=request,
                started_at=started_at,
                model_result=_ModelOpeningResult(
                    text="",
                    model_ms=0.0,
                    fallback_used=cache_info.fallback_used if cache_info else False,
                ),
                tts_result=_OpeningTtsResult(
                    tts_ms=0.0,
                    audio_url_present=cache_info.audio_url_present
                    if cache_info
                    else bool(cached.reply.audio_url),
                ),
                opening_policy_mode=None,
                cache_hit=True,
            )
            return cached

        parent_policy = self._parent_policy_service.get_policy(request.child_id)
        time_context = self._time_context_service.build_context(
            device_time=request.client_context.device_time,
            timezone=request.client_context.timezone,
            schedule=parent_policy.schedule,
        )
        opening_policy = self._opening_policy_builder.build(
            child_id=request.child_id,
            parent_policy=parent_policy,
            time_context=time_context,
        )

        # Companion recall: override to COMPANION_RECALL if applicable
        companion = self._check_companion_recall(
            child_id=request.child_id,
            session_id=request.session_id,
            bedtime=opening_policy.bedtime,
            current_mode=opening_policy.mode,
        )
        if companion is not None:
            opening_policy = OpeningPolicy(
                mode=OpeningMode.COMPANION_RECALL,
                age_band=opening_policy.age_band,
                max_chars=opening_policy.max_chars,
                max_spoken_options=opening_policy.max_spoken_options,
                seed_topic=opening_policy.seed_topic,
                seed_recall_allowed=False,
                seed_recall_reason="companion_recall",
                boundary_kind=opening_policy.boundary_kind,
                boundary_topic=opening_policy.boundary_topic,
                boundary_cooldown_active=opening_policy.boundary_cooldown_active,
                bedtime=opening_policy.bedtime,
                exciting_topic_deferred=opening_policy.exciting_topic_deferred,
                must_offer_topic_switch=True,
                must_allow_no_chat=True,
                prefer_parent_bridge=opening_policy.prefer_parent_bridge,
                parent_goal_hint=opening_policy.parent_goal_hint,
                forbidden_phrases=opening_policy.forbidden_phrases,
                prompt_rules=opening_policy.prompt_rules,
                companion_name=companion.name,
                companion_light_location=companion.light_location,
                companion_object_type=companion.object_type,
                companion_id=str(companion.id),
            )
        elif companion is None and self._check_star_seed_eligible(
            child_id=request.child_id,
            bedtime=opening_policy.bedtime,
            current_mode=opening_policy.mode,
        ):
            opening_policy = OpeningPolicy(
                mode=OpeningMode.COMPANION_STAR_SEED,
                age_band=opening_policy.age_band,
                max_chars=opening_policy.max_chars,
                max_spoken_options=opening_policy.max_spoken_options,
                seed_topic=opening_policy.seed_topic,
                seed_recall_allowed=False,
                seed_recall_reason="companion_star_seed",
                boundary_kind=opening_policy.boundary_kind,
                boundary_topic=opening_policy.boundary_topic,
                boundary_cooldown_active=opening_policy.boundary_cooldown_active,
                bedtime=opening_policy.bedtime,
                exciting_topic_deferred=opening_policy.exciting_topic_deferred,
                must_offer_topic_switch=True,
                must_allow_no_chat=True,
                prefer_parent_bridge=opening_policy.prefer_parent_bridge,
                parent_goal_hint=opening_policy.parent_goal_hint,
                forbidden_phrases=opening_policy.forbidden_phrases,
                prompt_rules=opening_policy.prompt_rules,
            )
        fallback_text = self._build_opening_text(
            parent_policy=parent_policy,
            opening_policy=opening_policy,
        )
        model_result = self._generate_model_opening(
            parent_policy=parent_policy,
            time_context=time_context,
            opening_policy=opening_policy,
            fallback_text=fallback_text,
        )
        reply = Reply(
            text=model_result.text,
            voice_enabled=True,
            emotion=self._emotion_for(time_context),
            agent_motion=self._motion_for(time_context),
        )
        tts_result = self._attach_audio_url(reply)
        if not reply.audio_url:
            reply.voice_enabled = False
        # Build ui_actions and session_state based on mode
        if opening_policy.mode == OpeningMode.COMPANION_STAR_SEED:
            ui_actions = [
                UiAction(actions=[
                    QuickAction(id="companion_name", label="起个名字"),
                    QuickAction(id="companion_skip", label="先看看"),
                ])
            ]
            companion_meta = CompanionObjectMeta(
                id="star_seed",
                name="小星星",
                object_type="star",
                light_location="窗边",
                state="seed",
                action="name_seed",
            )
        elif opening_policy.mode == OpeningMode.COMPANION_RECALL and opening_policy.companion_id:
            ui_actions = [
                UiAction(actions=[
                    QuickAction(id="companion_continue", label="加一个朋友"),
                    QuickAction(id="companion_skip", label="先聊别的"),
                ])
            ]
            companion_meta = CompanionObjectMeta(
                id=opening_policy.companion_id,
                name=opening_policy.companion_name or "",
                object_type=opening_policy.companion_object_type or "other",
                light_location=opening_policy.companion_light_location or "窗边",
                state="active",
                action="recall",
            )
            # Mark as recalled
            if self._companion_object_service is not None:
                try:
                    self._companion_object_service.mark_recalled(
                        opening_policy.companion_id,
                        session_id=request.session_id,
                    )
                except Exception:
                    pass
        else:
            ui_actions = [
                UiAction(actions=[QuickAction(id="start_voice", label="按一下开始说")])
            ]
            companion_meta = None

        response = ConversationMessageResponse(
            reply=reply,
            ui_actions=ui_actions,
            session_state=SessionState(
                base_scene="conversation.open",
                active_scene="conversation.open",
                needs_input=None,
                requires_parent_attention=None,
                companion_object=companion_meta,
            ),
        )
        self._opening_policy_builder.record_policy_used(
            child_id=request.child_id,
            policy=opening_policy,
        )
        self._conversation_history_service.record_turn(
            session_id=request.session_id,
            child_text="",
            agent_text=response.reply.text,
        )
        self._session_cache[cache_key] = response
        self._session_cache_info[cache_key] = _OpeningCacheInfo(
            fallback_used=model_result.fallback_used,
            audio_url_present=tts_result.audio_url_present,
        )
        self._log_opening_finished(
            request=request,
            started_at=started_at,
            model_result=model_result,
            tts_result=tts_result,
            opening_policy_mode=opening_policy.mode.value,
            cache_hit=False,
        )
        return response

    def _generate_model_opening(
        self,
        *,
        parent_policy: ParentPolicy,
        time_context: TimeContext,
        opening_policy: OpeningPolicy,
        fallback_text: str,
    ) -> _ModelOpeningResult:
        started_at = time.perf_counter()
        try:
            response = self._request_model_opening_with_soft_timeout(
                parent_policy=parent_policy,
                time_context=time_context,
                opening_policy=opening_policy,
                user_content="请生成开场白。",
                retry=False,
            )
        except Exception as exc:
            return _ModelOpeningResult(
                text=fallback_text,
                model_ms=self._elapsed_ms(started_at),
                fallback_used=True,
                error_type=exc.__class__.__name__,
            )
        if response.metadata.get("mock"):
            return _ModelOpeningResult(
                text=fallback_text,
                model_ms=self._elapsed_ms(started_at),
                fallback_used=True,
            )
        text = self._sanitize_opening_text(
            response.response_text,
            opening_policy=opening_policy,
        )
        if text:
            return _ModelOpeningResult(
                text=text,
                model_ms=self._elapsed_ms(started_at),
                fallback_used=False,
            )
        try:
            retry_response = self._request_model_opening_with_soft_timeout(
                parent_policy=parent_policy,
                time_context=time_context,
                opening_policy=opening_policy,
                user_content="请只输出一句中文开场白，不要解释，不要 JSON。",
                retry=True,
            )
        except Exception as exc:
            return _ModelOpeningResult(
                text=fallback_text,
                model_ms=self._elapsed_ms(started_at),
                fallback_used=True,
                error_type=exc.__class__.__name__,
            )
        retry_text = self._sanitize_opening_text(
            retry_response.response_text,
            opening_policy=opening_policy,
        )
        return _ModelOpeningResult(
            text=retry_text or fallback_text,
            model_ms=self._elapsed_ms(started_at),
            fallback_used=not bool(retry_text),
        )

    def _request_model_opening_with_soft_timeout(
        self,
        *,
        parent_policy: ParentPolicy,
        time_context: TimeContext,
        opening_policy: OpeningPolicy,
        user_content: str,
        retry: bool,
    ):
        if self._model_soft_timeout_ms <= 0:
            return self._request_model_opening(
                parent_policy=parent_policy,
                time_context=time_context,
                opening_policy=opening_policy,
                user_content=user_content,
                retry=retry,
            )

        context = copy_context()
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="opening-model")
        future = executor.submit(
            context.run,
            self._request_model_opening,
            parent_policy=parent_policy,
            time_context=time_context,
            opening_policy=opening_policy,
            user_content=user_content,
            retry=retry,
        )
        try:
            return future.result(timeout=self._model_soft_timeout_ms / 1000)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _request_model_opening(
        self,
        *,
        parent_policy: ParentPolicy,
        time_context: TimeContext,
        opening_policy: OpeningPolicy,
        user_content: str,
        retry: bool,
    ):
        return self._model_registry.generate(
            ModelRequest(
                task_type=ModelTaskType.CHILD_CHAT,
                messages=[
                    ModelMessage(
                        role="system",
                        content=self._opening_prompt(
                            parent_policy=parent_policy,
                            time_context=time_context,
                            opening_policy=opening_policy,
                        ),
                    ),
                    ModelMessage(role="user", content=user_content),
                ],
                input_text=user_content,
                context={
                    "conversation": {
                        "child_id": parent_policy.child_id,
                    }
                },
                metadata={"opening_greeting": True, "opening_retry": retry},
            )
        )

    def _opening_prompt(
        self,
        *,
        parent_policy: ParentPolicy,
        time_context: TimeContext,
        opening_policy: OpeningPolicy,
    ) -> str:
        name = self._child_call_name(parent_policy)
        parent_message = self._parent_message_for_prompt(parent_policy, opening_policy)
        policy_data = self._policy_data_for_profile(parent_policy)
        profile_block = render_child_profile_for_prompt(policy_data)
        prompt_rules = "\n- ".join(opening_policy.prompt_rules)
        forbidden = "；".join(self._forbidden_phrases_for_prompt(opening_policy))
        schedule_goal = self._text_for_prompt(
            time_context.schedule_goal or "无",
            opening_policy,
        )
        preferred_interactions = [
            self._text_for_prompt(value, opening_policy)
            for value in time_context.preferred_interactions
        ]
        avoid = [
            self._text_for_prompt(value, opening_policy)
            for value in time_context.avoid
        ]
        return (
            "你是小白狐。请给孩子一句自然、短、亲切的开场白，适合直接朗读。"
            "根据当前时间段、家长寄语、孩子称呼和家庭沟通偏好调整语气。"
            "不要像老师点名，不要查岗，不要强行追问日间经历，不要每次都问固定日常问题。"
            "如果是晚上，低刺激、短句；如果刚放学，轻松欢迎回来。"
            "opening 必须遵守 opening policy，不要自己扩大目标。"
            "必须直接输出一句或两句中文开场白，不输出空内容、none、null，不使用 Markdown 或 JSON。"
            "如果不确定怎么写，也必须输出一条 8 个中文字符以上的安全短开场白。"
            "不要在开场白中提及家长设置的偏好标签、性格描述或支持方式。"
            f"\n孩子称呼：{name or '无'}"
            f"\n当前时间段：{time_context.time_period.value}"
            f"\n时间目标：{schedule_goal}"
            f"\n推荐互动：{'、'.join(preferred_interactions)}"
            f"\n避免事项：{'、'.join(avoid)}"
            f"\n孩子画像：\n{profile_block}"
            f"\nopening_mode：{opening_policy.mode.value}"
            f"\n年龄段：{opening_policy.age_band}"
            f"\n最大字数：{opening_policy.max_chars}"
            f"\n最多口头选项数：{opening_policy.max_spoken_options}"
            f"\n可轻回访兴趣：{opening_policy.seed_topic or '无'}"
            f"\n兴趣回访允许：{opening_policy.seed_recall_allowed}"
            f"\n回访原因：{opening_policy.seed_recall_reason or '无'}"
            f"\n边界类型：{opening_policy.boundary_kind or '无'}"
            f"\n边界冷却中：{opening_policy.boundary_cooldown_active}"
            f"\n家长目标低压力转译：{opening_policy.parent_goal_hint or '无'}"
            f"\n必须给孩子选择权：{opening_policy.must_offer_topic_switch}"
            f"\n必须允许孩子不聊：{opening_policy.must_allow_no_chat}"
            f"\nopening policy rules：\n- {prompt_rules}"
            f"\n禁止话术：{forbidden}"
            f"\n家长寄语背景：{parent_message[:500]}"
        )

    def _sanitize_opening_text(
        self,
        text: str,
        *,
        opening_policy: OpeningPolicy,
    ) -> str:
        compact = " ".join(text.strip().split())
        compact = compact.strip("\"'“”")
        if not compact:
            return ""
        if self._contains_forbidden_phrase(compact, opening_policy):
            return ""
        if len(compact) > opening_policy.max_chars:
            compact = compact[: opening_policy.max_chars].rstrip("，。！？,.!? ") + "。"
        return compact

    def _build_opening_text(
        self,
        *,
        parent_policy: ParentPolicy,
        opening_policy: OpeningPolicy,
    ) -> str:
        name = self._child_call_name(parent_policy)
        prefix = f"{name}，" if name else ""
        topic = opening_policy.seed_topic or ""

        # Memory-aware opening only for safe modes — bedtime/boundary/low-expression
        # modes must stay low-stimulation and must not pull the child back into old topics.
        if self._memory_aware_opening_allowed(opening_policy):
            memory_opening = self._memory_aware_opening(
                prefix=prefix,
                parent_policy=parent_policy,
                opening_policy=opening_policy,
            )
            if memory_opening:
                return memory_opening

        if opening_policy.mode == OpeningMode.INTEREST_CALLBACK and topic:
            templates = self._interest_callback_templates(prefix, topic, opening_policy)
            text = self._select_by_variation(templates, parent_policy)
        elif opening_policy.mode == OpeningMode.BOUNDARY_RESPECT:
            templates = self._boundary_respect_templates(prefix, opening_policy)
            text = self._select_by_variation(templates, parent_policy)
        elif opening_policy.mode == OpeningMode.LOW_EXPRESSION_SUPPORT:
            text = f"{prefix}你可以只说一个词。说不完整也没关系。"
        elif opening_policy.mode == OpeningMode.BEDTIME_CLOSURE:
            bedtime_mem = self._bedtime_memory_opening(
                prefix=prefix, parent_policy=parent_policy, opening_policy=opening_policy,
            )
            text = bedtime_mem or f"{prefix}小白狐在这里。现在有点晚，我们可以慢慢说一小会儿，也可以明天再说。"
        elif opening_policy.mode == OpeningMode.BEDTIME_DEFER_INTEREST and topic:
            # BEDTIME_DEFER_INTEREST: topic is exciting, use generic bedtime
            # template that does NOT mention the topic (low stimulation).
            bedtime_mem = self._bedtime_memory_opening(
                prefix=prefix, parent_policy=parent_policy, opening_policy=opening_policy,
            )
            if bedtime_mem:
                text = bedtime_mem
            else:
                text = f"{prefix}小白狐在这里。现在有点晚，我们可以慢慢说一小会儿，也可以明天再说。"
        elif opening_policy.mode == OpeningMode.PARENT_BRIDGE_LIGHT:
            text = f"{prefix}这句话也可以告诉家长。小白狐先听你说。"
        elif opening_policy.mode == OpeningMode.COMPANION_STAR_SEED:
            text = f"{prefix}窗边这颗小星星还没有名字\n要不要给它起一个？"
        elif opening_policy.mode == OpeningMode.COMPANION_RECALL:
            name = opening_policy.companion_name or "小星星"
            location = opening_policy.companion_light_location or "窗边"
            text = f"{prefix}{name}今天在{location}呢\n要不要给它加一个朋友？"
        else:
            templates = self._default_greeting_templates(prefix, opening_policy)
            text = self._select_by_variation(templates, parent_policy)
        return self._sanitize_opening_text(
            text,
            opening_policy=opening_policy,
        )

    def _memory_aware_opening_allowed(self, opening_policy: OpeningPolicy) -> bool:
        """Memory callbacks for INTEREST_CALLBACK and DEFAULT_LIGHT only.

        Bedtime modes have their own low-stimulation path via _bedtime_memory_opening.
        BOUNDARY_RESPECT / LOW_EXPRESSION_SUPPORT / PARENT_BRIDGE_LIGHT never use memory.
        """
        if opening_policy.boundary_cooldown_active:
            return False
        return opening_policy.mode in (
            OpeningMode.INTEREST_CALLBACK,
            OpeningMode.DEFAULT_LIGHT,
        )

    # High-stimulation topics that must NOT be opened at bedtime.
    _BEDTIME_EXCITING_MARKERS = (
        "比赛", "输赢", "排名", "恐龙", "大战", "冒险",
        "挑战", "任务", "奖励", "游戏", "cs", "反恐",
    )

    def _bedtime_memory_opening(
        self,
        *,
        prefix: str,
        parent_policy: ParentPolicy,
        opening_policy: OpeningPolicy,
    ) -> str | None:
        """Bedtime-friendly memory touch: warm, short, low-stimulus, allows declining."""
        child_id = parent_policy.child_id
        if not child_id:
            return None

        # Try low-sensitivity memories only: interest seed, show-and-tell, unfinished thread.
        for fetcher in (latest_interest_seed, latest_show_and_tell_event, latest_unfinished_thread):
            mem = fetcher(self._memory_service, child_id=child_id)
            if not mem:
                continue
            if mem.sensitivity != MemorySensitivity.LOW:
                continue
            safe_hook = self._safe_memory_hook(mem.content or "")
            if not safe_hook:
                continue
            # Block high-stimulation topics at bedtime
            if any(marker in safe_hook for marker in self._BEDTIME_EXCITING_MARKERS):
                continue
            text = (
                f"{prefix}小白狐还记得你聊过{safe_hook}。"
                "今晚可以只说一小点，不想说也没关系。"
            )
            sanitized = self._sanitize_opening_text(text, opening_policy=opening_policy)
            if sanitized:
                return sanitized

        return None

    def _memory_aware_opening(
        self,
        *,
        prefix: str,
        parent_policy: ParentPolicy,
        opening_policy: OpeningPolicy,
    ) -> str | None:
        """Try to build an opening from recent memory (unfinished thread, show-and-tell, interest)."""
        child_id = parent_policy.child_id
        if not child_id:
            return None

        # Unfinished thread — light callback, explicitly allow not continuing
        unfinished = latest_unfinished_thread(self._memory_service, child_id=child_id)
        if unfinished:
            hook = unfinished.content or ""
            # Extract a safe summary (e.g., "英语打卡") from the thread
            safe_hook = self._safe_memory_hook(hook)
            if safe_hook:
                text = f"{prefix}上次你说要去{safe_hook}，今天不用接着说，想换个话题也可以。"
                sanitized = self._sanitize_opening_text(text, opening_policy=opening_policy)
                if sanitized:
                    return sanitized

        # Show-and-tell event — light callback
        show_tell = latest_show_and_tell_event(self._memory_service, child_id=child_id)
        if show_tell:
            topic = show_tell.content or ""
            safe_topic = self._safe_memory_hook(topic)
            if safe_topic:
                text = f"{prefix}还记得你上次给小白狐看的{safe_topic}。今天想聊点什么？"
                sanitized = self._sanitize_opening_text(text, opening_policy=opening_policy)
                if sanitized:
                    return sanitized

        # Interest seed — light callback
        interest = latest_interest_seed(self._memory_service, child_id=child_id)
        if interest:
            topic = interest.content or ""
            safe_topic = self._safe_memory_hook(topic)
            if safe_topic:
                text = f"{prefix}小白狐记得你聊过{safe_topic}。今天想慢慢聊，还是先换个轻松的？"
                sanitized = self._sanitize_opening_text(text, opening_policy=opening_policy)
                if sanitized:
                    return sanitized

        return None

    def _safe_memory_hook(self, text: str) -> str:
        """Extract a safe, short summary from memory content."""
        # Remove common prefixes
        for prefix in ("孩子近期自然聊到", "孩子自然提到", "可作为低压力回访的兴趣种子。"):
            text = text.replace(prefix, "")
        # Take first clause only
        for sep in ("，", "。", "、"):
            if sep in text:
                text = text.split(sep)[0]
        return text.strip()[:20]

    def _interest_callback_templates(
        self,
        prefix: str,
        topic: str,
        opening_policy: OpeningPolicy,
    ) -> list[str]:
        if opening_policy.age_band == "age_5_6":
            return [
                f"{prefix}小白狐记得{topic}。想聊就聊，不想聊也行。",
                f"{prefix}{topic}可以先放在这里。你也可以换个轻松的。",
            ]
        if opening_policy.age_band == "age_9_10":
            return [
                f"{prefix}我记得你提过{topic}。想聊它也可以，换个轻松的也可以。",
                f"{prefix}{topic}今天可以接着说，也可以换个新话题。",
            ]
        return [
            f"{prefix}我记得你提过{topic}。今天想聊它，还是换个轻松的？",
            f"{prefix}小白狐记得{topic}。想说就说，不想说也行。",
        ]

    def _boundary_respect_templates(
        self,
        prefix: str,
        opening_policy: OpeningPolicy,
    ) -> list[str]:
        return [
            f"{prefix}上次那个我们先不聊。今天可以说新的，也可以先安静一下。",
            f"{prefix}那个话题我们先放一放。今天可以换个轻松的。",
        ]

    def _default_greeting_templates(
        self,
        prefix: str,
        opening_policy: OpeningPolicy,
    ) -> list[str]:
        return [
            f"{prefix}我在这里。你可以慢慢说一句，也可以先听小白狐说一句。",
            f"{prefix}小白狐在这里。今天可以先聊一件小事，也可以给小白狐看看。",
            f"{prefix}回来啦。想聊什么都可以，不想说也没关系。",
        ]

    def _select_by_variation(
        self,
        templates: list[str],
        parent_policy: ParentPolicy,
    ) -> str:
        """Select a template based on session_id/date hash for variation."""
        if len(templates) <= 1:
            return templates[0] if templates else ""
        # Use child_id + today's date to create variation
        today = self._now_date()
        seed = f"{parent_policy.child_id}:{today}"
        index = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(templates)
        return templates[index]

    def _now_date(self) -> str:
        """Get current date as string for variation hashing."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _child_call_name(self, parent_policy: ParentPolicy) -> str:
        return (
            (parent_policy.child_nickname or "").strip()
            or (parent_policy.child_display_name or "").strip()
        )

    def _policy_data_for_profile(self, parent_policy: ParentPolicy) -> dict[str, object]:
        return {
            "child_nickname": parent_policy.child_nickname,
            "child_display_name": parent_policy.child_display_name,
            "parent_message_raw": parent_policy.parent_message_raw,
            "communication_preferences": parent_policy.communication_preferences,
        }

    def _attach_audio_url(self, reply: Reply) -> _OpeningTtsResult:
        started_at = time.perf_counter()
        if not reply.voice_enabled:
            return _OpeningTtsResult(
                tts_ms=self._elapsed_ms(started_at),
                audio_url_present=False,
            )
        try:
            audio_url = self._generate_tts_with_soft_timeout(
                text=reply.text,
                emotion=reply.emotion,
            )
        except FutureTimeoutError as exc:
            return _OpeningTtsResult(
                tts_ms=self._elapsed_ms(started_at),
                audio_url_present=False,
                error_type=exc.__class__.__name__,
            )
        except Exception as exc:
            return _OpeningTtsResult(
                tts_ms=self._elapsed_ms(started_at),
                audio_url_present=False,
                error_type=exc.__class__.__name__,
            )
        if audio_url:
            reply.audio_url = audio_url
        return _OpeningTtsResult(
            tts_ms=self._elapsed_ms(started_at),
            audio_url_present=bool(audio_url),
        )

    def _generate_tts_with_soft_timeout(self, *, text: str, emotion: str) -> str | None:
        if self._tts_soft_timeout_ms <= 0:
            return self._tts_service.generate_for_conversation(
                text=text,
                emotion=emotion,
            )

        context = copy_context()
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="opening-tts")
        future = executor.submit(
            context.run,
            self._tts_service.generate_for_conversation,
            text=text,
            emotion=emotion,
        )
        try:
            return future.result(timeout=self._tts_soft_timeout_ms / 1000)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _emotion_for(self, time_context: TimeContext) -> str:
        if time_context.time_period == TimePeriod.BEDTIME:
            return "sleepy"
        return "warm"

    def _motion_for(self, time_context: TimeContext) -> str:
        if time_context.time_period == TimePeriod.BEDTIME:
            return "sleepy_blink"
        return "gentle_idle"

    def _contains_forbidden_phrase(
        self,
        text: str,
        opening_policy: OpeningPolicy,
    ) -> bool:
        return any(phrase in text for phrase in opening_policy.forbidden_phrases)

    def _forbidden_phrases_for_prompt(
        self,
        opening_policy: OpeningPolicy,
    ) -> tuple[str, ...]:
        if not any("不提固定场所" in rule for rule in opening_policy.prompt_rules):
            return opening_policy.forbidden_phrases
        return tuple(
            phrase.replace("学校", "日间场所")
            for phrase in opening_policy.forbidden_phrases
        )

    def _parent_message_for_prompt(
        self,
        parent_policy: ParentPolicy,
        opening_policy: OpeningPolicy,
    ) -> str:
        parent_message = (parent_policy.parent_message_raw or "").strip()
        return self._text_for_prompt(parent_message, opening_policy)

    def _text_for_prompt(
        self,
        text: str,
        opening_policy: OpeningPolicy,
    ) -> str:
        if any("不提固定场所" in rule for rule in opening_policy.prompt_rules):
            return text.replace("学校", "日间场所")
        return text

    def _log_opening_finished(
        self,
        *,
        request: ConversationOpeningRequest,
        started_at: float,
        model_result: _ModelOpeningResult,
        tts_result: _OpeningTtsResult,
        opening_policy_mode: str | None,
        cache_hit: bool,
    ) -> None:
        logger.info(
            "conversation_opening_finished",
            extra={
                "event": "conversation_opening_finished",
                "request_id": get_request_id(),
                "child_id_hash": hash_identifier(request.child_id),
                "session_id_hash": hash_identifier(request.session_id),
                "opening_policy_mode": opening_policy_mode,
                "cache_hit": cache_hit,
                "model_ms": model_result.model_ms,
                "tts_ms": tts_result.tts_ms,
                "total_ms": self._elapsed_ms(started_at),
                "audio_url_present": tts_result.audio_url_present,
                "fallback_used": model_result.fallback_used,
                "model_error_type": model_result.error_type,
                "tts_error_type": tts_result.error_type,
                "opening_text_chars": len(model_result.text)
                if model_result.text
                else None,
            },
        )

    def _elapsed_ms(self, started_at: float) -> float:
        return round((time.perf_counter() - started_at) * 1000, 1)


_opening_service: OpeningService | None = None


def get_opening_service() -> OpeningService:
    global _opening_service
    if _opening_service is None:
        from app.services.companion_object_service import get_companion_object_service
        try:
            companion_svc = get_companion_object_service()
        except Exception:
            companion_svc = None
        _opening_service = OpeningService(companion_object_service=companion_svc)
    return _opening_service
