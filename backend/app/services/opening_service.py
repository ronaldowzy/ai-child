from app.domain.schemas.conversation import (
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
from app.services.time_context_service import (
    TimeContextService,
    get_time_context_service,
)
from app.services.tts_service import TtsService, get_tts_service


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
        self._session_cache: dict[tuple[str, str], ConversationMessageResponse] = {}

    def create_opening(
        self,
        request: ConversationOpeningRequest,
    ) -> ConversationMessageResponse:
        cache_key = (request.child_id, request.session_id)
        cached = self._session_cache.get(cache_key)
        if cached is not None:
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
        fallback_text = self._build_opening_text(
            parent_policy=parent_policy,
            opening_policy=opening_policy,
        )
        text = fallback_text
        reply = Reply(
            text=text,
            voice_enabled=True,
            emotion=self._emotion_for(time_context),
            agent_motion=self._motion_for(time_context),
        )
        self._attach_audio_url(reply)
        response = ConversationMessageResponse(
            reply=reply,
            ui_actions=[
                UiAction(actions=[QuickAction(id="start_voice", label="我想说话")])
            ],
            session_state=SessionState(
                base_scene="conversation.open",
                active_scene="conversation.open",
                needs_input=None,
                requires_parent_attention=None,
            ),
        )
        self._opening_policy_builder.record_policy_used(
            child_id=request.child_id,
            policy=opening_policy,
        )
        self._session_cache[cache_key] = response
        return response

    def _generate_model_opening(
        self,
        *,
        parent_policy: ParentPolicy,
        time_context: TimeContext,
        opening_policy: OpeningPolicy,
        fallback_text: str,
    ) -> str:
        try:
            response = self._request_model_opening(
                parent_policy=parent_policy,
                time_context=time_context,
                opening_policy=opening_policy,
                user_content="请生成开场白。",
                retry=False,
            )
        except Exception:
            return fallback_text
        if response.metadata.get("mock"):
            return fallback_text
        text = self._sanitize_opening_text(
            response.response_text,
            opening_policy=opening_policy,
        )
        if text:
            return text
        try:
            retry_response = self._request_model_opening(
                parent_policy=parent_policy,
                time_context=time_context,
                opening_policy=opening_policy,
                user_content="请只输出一句中文开场白，不要解释，不要 JSON。",
                retry=True,
            )
        except Exception:
            return fallback_text
        return (
            self._sanitize_opening_text(
                retry_response.response_text,
                opening_policy=opening_policy,
            )
            or fallback_text
        )

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
        preferences = parent_policy.communication_preferences
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
            "根据当前时间段、父母寄语、孩子称呼和家庭沟通偏好调整语气。"
            "不要像老师点名，不要查岗，不要强行追问日间经历，不要每次都问固定日常问题。"
            "如果是晚上，低刺激、短句；如果刚放学，轻松欢迎回来。"
            "opening 必须遵守 opening policy，不要自己扩大目标。"
            "必须直接输出一句或两句中文开场白，不输出空内容、none、null，不使用 Markdown 或 JSON。"
            "如果不确定怎么写，也必须输出一条 8 个中文字符以上的安全短开场白。"
            f"\n孩子称呼：{name or '无'}"
            f"\n当前时间段：{time_context.time_period.value}"
            f"\n时间目标：{schedule_goal}"
            f"\n推荐互动：{'、'.join(preferred_interactions)}"
            f"\n避免事项：{'、'.join(avoid)}"
            f"\n沟通偏好：{preferences}"
            f"\nopening_mode：{opening_policy.mode.value}"
            f"\n年龄段：{opening_policy.age_band}"
            f"\n最大字数：{opening_policy.max_chars}"
            f"\n最多口头选项数：{opening_policy.max_spoken_options}"
            f"\n可轻回访兴趣：{opening_policy.seed_topic or '无'}"
            f"\n兴趣回访允许：{opening_policy.seed_recall_allowed}"
            f"\n回访原因：{opening_policy.seed_recall_reason or '无'}"
            f"\n边界类型：{opening_policy.boundary_kind or '无'}"
            f"\n边界冷却中：{opening_policy.boundary_cooldown_active}"
            f"\n父亲目标低压力转译：{opening_policy.parent_goal_hint or '无'}"
            f"\n必须给孩子选择权：{opening_policy.must_offer_topic_switch}"
            f"\n必须允许孩子不聊：{opening_policy.must_allow_no_chat}"
            f"\nopening policy rules：\n- {prompt_rules}"
            f"\n禁止话术：{forbidden}"
            f"\n父母寄语背景：{parent_message[:500]}"
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
        if opening_policy.mode == OpeningMode.INTEREST_CALLBACK and topic:
            if opening_policy.age_band == "age_5_6":
                text = f"{prefix}小白狐记得{topic}。聊它，还是听小故事？"
            elif opening_policy.age_band == "age_9_10":
                text = f"{prefix}我记得你提过{topic}。想聊它、换轻松的，还是做个小计划？"
            else:
                text = f"{prefix}我记得你提过{topic}。今天想聊它，还是换个轻松的？"
        elif opening_policy.mode == OpeningMode.BOUNDARY_RESPECT:
            text = f"{prefix}上次那个我们先不聊。今天想说新的，还是让小白狐先讲一句？"
        elif opening_policy.mode == OpeningMode.LOW_EXPRESSION_SUPPORT:
            text = f"{prefix}你可以只说一个词。说不完整也没关系。"
        elif opening_policy.mode == OpeningMode.BEDTIME_CLOSURE:
            text = f"{prefix}晚上好。我们只说一小句，说完就休息。"
        elif opening_policy.mode == OpeningMode.BEDTIME_DEFER_INTEREST and topic:
            text = f"{prefix}{topic}我们明天白天再慢慢说。现在轻轻收个尾，好吗？"
        elif opening_policy.mode == OpeningMode.PARENT_BRIDGE_LIGHT:
            text = f"{prefix}这句话也可以告诉爸爸妈妈。小白狐先听你说一点点。"
        else:
            text = f"{prefix}我在这里。你可以慢慢说一句，也可以先听小白狐说一句。"
        return self._sanitize_opening_text(
            text,
            opening_policy=opening_policy,
        )

    def _child_call_name(self, parent_policy: ParentPolicy) -> str:
        return (
            (parent_policy.child_nickname or "").strip()
            or (parent_policy.child_display_name or "").strip()
        )

    def _attach_audio_url(self, reply: Reply) -> None:
        # Opening is shown on first screen paint. Do not block that response on a
        # cold remote TTS call; Android can still read the short text locally, and
        # conversation turns keep using segment-level MiMo TTS.
        return

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


_opening_service = OpeningService()


def get_opening_service() -> OpeningService:
    return _opening_service
