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
    ) -> None:
        self._parent_policy_service = (
            parent_policy_service or get_parent_policy_service()
        )
        self._time_context_service = time_context_service or get_time_context_service()
        self._tts_service = tts_service or get_tts_service()
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
        text = self._build_opening_text(
            parent_policy=parent_policy,
            time_context=time_context,
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

    def _build_opening_text(
        self,
        *,
        parent_policy: ParentPolicy,
        time_context: TimeContext,
    ) -> str:
        name = self._child_call_name(parent_policy)
        prefix = f"{name}，" if name else ""
        parent_message = (parent_policy.parent_message_raw or "").strip()
        avoid_school_check = (
            "不要查岗学校" in parent_message
            or "不要问学校" in parent_message
            or "别问学校" in parent_message
        )

        if time_context.time_period == TimePeriod.BEDTIME:
            return f"{prefix}晚上好。我们轻轻说一小句就好。"
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
