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
from app.domain.memory import MemoryItem
from app.services.memory_service import MemoryService, get_memory_service
from app.services.model_registry import ModelRegistry, get_model_registry
from app.services.parent_policy_service import (
    ParentPolicyService,
    get_parent_policy_service,
)
from app.services.time_context_service import (
    TimeContextService,
    get_time_context_service,
)
from app.services.relationship_memory import (
    latest_interest_seed,
    memory_relationship_topic,
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
    ) -> None:
        self._parent_policy_service = (
            parent_policy_service or get_parent_policy_service()
        )
        self._time_context_service = time_context_service or get_time_context_service()
        self._tts_service = tts_service or get_tts_service()
        self._model_registry = model_registry or get_model_registry()
        self._memory_service = memory_service or get_memory_service()
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
        interest_seed = self._safe_latest_interest_seed(request.child_id)
        fallback_text = self._build_opening_text(
            parent_policy=parent_policy,
            time_context=time_context,
            interest_seed=interest_seed,
        )
        text = self._generate_model_opening(
            parent_policy=parent_policy,
            time_context=time_context,
            interest_seed=interest_seed,
            fallback_text=fallback_text,
        )
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
        self._session_cache[cache_key] = response
        return response

    def _generate_model_opening(
        self,
        *,
        parent_policy: ParentPolicy,
        time_context: TimeContext,
        interest_seed: MemoryItem | None,
        fallback_text: str,
    ) -> str:
        try:
            response = self._model_registry.generate(
                ModelRequest(
                    task_type=ModelTaskType.CHILD_CHAT,
                    messages=[
                        ModelMessage(
                            role="system",
                            content=self._opening_prompt(
                                parent_policy=parent_policy,
                                time_context=time_context,
                                interest_seed=interest_seed,
                            ),
                        ),
                        ModelMessage(role="user", content="请生成开场白。"),
                    ],
                    input_text="请生成开场白。",
                    context={
                        "conversation": {
                            "child_id": parent_policy.child_id,
                        }
                    },
                    metadata={"opening_greeting": True},
                )
            )
        except Exception:
            return fallback_text
        if response.metadata.get("mock"):
            return fallback_text
        return self._sanitize_opening_text(response.response_text) or fallback_text

    def _opening_prompt(
        self,
        *,
        parent_policy: ParentPolicy,
        time_context: TimeContext,
        interest_seed: MemoryItem | None = None,
    ) -> str:
        name = self._child_call_name(parent_policy)
        parent_message = (parent_policy.parent_message_raw or "").strip()
        goals = "；".join(parent_policy.goals[:4])
        preferences = parent_policy.communication_preferences
        seed_topic = memory_relationship_topic(interest_seed) if interest_seed else ""
        return (
            "你是小白狐。请给孩子一句自然、短、亲切的开场白，适合直接朗读。"
            "根据当前时间段、父母寄语、孩子称呼和家庭沟通偏好调整语气。"
            "不要像老师点名，不要查岗，不要强行问学校，不要每次都问今天在学校怎么样。"
            "如果是晚上，低刺激、短句；如果刚放学，轻松欢迎回来。"
            "只输出一句或两句，不使用 Markdown。"
            f"\n孩子称呼：{name or '无'}"
            f"\n当前时间段：{time_context.time_period.value}"
            f"\n时间目标：{time_context.schedule_goal or '无'}"
            f"\n推荐互动：{'、'.join(time_context.preferred_interactions)}"
            f"\n避免事项：{'、'.join(time_context.avoid)}"
            f"\n父亲目标：{goals}"
            f"\n沟通偏好：{preferences}"
            f"\n可轻回访兴趣：{seed_topic or '无'}"
            f"\n父母寄语背景：{parent_message[:500]}"
        )

    def _sanitize_opening_text(self, text: str) -> str:
        compact = " ".join(text.strip().split())
        compact = compact.strip("\"'“”")
        if not compact:
            return ""
        if len(compact) > 80:
            compact = compact[:80].rstrip("，。！？,.!? ") + "。"
        return compact

    def _build_opening_text(
        self,
        *,
        parent_policy: ParentPolicy,
        time_context: TimeContext,
        interest_seed: MemoryItem | None = None,
    ) -> str:
        name = self._child_call_name(parent_policy)
        prefix = f"{name}，" if name else ""
        parent_message = (parent_policy.parent_message_raw or "").strip()
        avoid_school_check = (
            "不要查岗学校" in parent_message
            or "不要问学校" in parent_message
            or "别问学校" in parent_message
        )
        seed_topic = memory_relationship_topic(interest_seed) if interest_seed else ""

        if time_context.time_period == TimePeriod.BEDTIME:
            if seed_topic:
                return (
                    f"{prefix}晚上好。{seed_topic}我们可以明天再慢慢说，"
                    "现在轻轻收个尾就好。"
                )
            return f"{prefix}晚上好。我们轻轻说一小句就好。"
        if seed_topic:
            return (
                f"{prefix}我还记得你上次聊到{seed_topic}。"
                "今天想继续聊一点，还是先换个轻松小故事？"
            )
        if time_context.time_period == TimePeriod.AFTER_SCHOOL:
            if avoid_school_check:
                return f"{prefix}回来啦。我们不急着汇报，先说你想说的。"
            return f"{prefix}回来啦。我们先慢慢聊一件你想说的小事。"
        if time_context.time_period == TimePeriod.MORNING_BEFORE_SCHOOL:
            return f"{prefix}早上好。我准备好陪你轻轻开始今天。"
        return f"{prefix}我准备好啦。你想说什么都可以慢慢说。"

    def _child_call_name(self, parent_policy: ParentPolicy) -> str:
        return (
            (parent_policy.child_nickname or "").strip()
            or (parent_policy.child_display_name or "").strip()
        )

    def _safe_latest_interest_seed(self, child_id: str) -> MemoryItem | None:
        try:
            return latest_interest_seed(self._memory_service, child_id=child_id)
        except Exception:
            return None

    def _attach_audio_url(self, reply: Reply) -> None:
        try:
            audio_url = self._tts_service.generate_for_conversation(
                text=reply.text,
                emotion=reply.emotion,
            )
        except Exception:
            return
        if audio_url:
            reply.audio_url = audio_url

    def _emotion_for(self, time_context: TimeContext) -> str:
        if time_context.time_period == TimePeriod.BEDTIME:
            return "sleepy"
        return "warm"

    def _motion_for(self, time_context: TimeContext) -> str:
        if time_context.time_period == TimePeriod.BEDTIME:
            return "sleepy_blink"
        return "gentle_idle"


_opening_service = OpeningService()


def get_opening_service() -> OpeningService:
    return _opening_service
