from app.domain.schemas.conversation import (
    ConversationDebug,
    ConversationMessageRequest,
    ConversationMessageResponse,
    ParentPolicyDebug,
    QuickAction,
    Reply,
    SessionState,
    UiAction,
)
from app.services.parent_policy_service import (
    ParentPolicyService,
    get_parent_policy_service,
)
from app.services.time_context_service import (
    TimeContextService,
    get_time_context_service,
)


class ConversationService:
    """Temporary mock conversation flow for the S01 backend skeleton."""

    def __init__(
        self,
        *,
        time_context_service: TimeContextService | None = None,
        parent_policy_service: ParentPolicyService | None = None,
        debug_enabled: bool = True,
    ) -> None:
        self._time_context_service = time_context_service or get_time_context_service()
        self._parent_policy_service = (
            parent_policy_service or get_parent_policy_service()
        )
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

        if self._is_learning_help_mock(request.input.text):
            response = self._learning_help_response()
        else:
            response = self._general_checkin_response()

        if self._debug_enabled:
            response.debug = ConversationDebug(
                time_context=time_context,
                parent_policy=ParentPolicyDebug(
                    goals=parent_policy.goals,
                    communication_preferences=parent_policy.communication_preferences,
                    safety_rules=parent_policy.safety_rules,
                ),
            )
        return response

    def _is_learning_help_mock(self, text: str) -> bool:
        learning_keywords = ("题", "作业", "不会", "数学", "语文", "英语")
        return any(keyword in text for keyword in learning_keywords)

    def _learning_help_response(self) -> ConversationMessageResponse:
        return ConversationMessageResponse(
            reply=Reply(
                text=(
                    "可以，我们一起拆开它。你先不用急着要答案，"
                    "可以拍一张题目的照片，或者先把题目读给我听。"
                )
            ),
            ui_actions=[
                UiAction(
                    actions=[
                        QuickAction(id="take_photo", label="拍题目"),
                        QuickAction(id="speak_problem", label="读题目"),
                    ]
                )
            ],
            session_state=SessionState(
                base_scene="daily.after_school_checkin",
                active_scene="learning.homework_help",
                needs_input="problem_content",
            ),
        )

    def _general_checkin_response(self) -> ConversationMessageResponse:
        return ConversationMessageResponse(
            reply=Reply(
                text=(
                    "我在这里。你可以先选一个最想说的小事情："
                    "今天开心的事、遇到的难题，或者想安静一会儿。"
                )
            ),
            ui_actions=[
                UiAction(
                    actions=[
                        QuickAction(id="happy_moment", label="开心的事"),
                        QuickAction(id="hard_thing", label="遇到的难题"),
                        QuickAction(id="quiet_time", label="想安静一会儿"),
                    ]
                )
            ],
            session_state=SessionState(
                base_scene="daily.after_school_checkin",
                active_scene="daily.after_school_checkin",
                needs_input="child_choice",
            ),
        )
