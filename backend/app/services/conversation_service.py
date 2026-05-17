from app.domain.schemas.conversation import (
    ConversationMessageRequest,
    ConversationMessageResponse,
    QuickAction,
    Reply,
    SessionState,
    UiAction,
)


class ConversationService:
    """Temporary mock conversation flow for the S01 backend skeleton."""

    def handle_message(
        self, request: ConversationMessageRequest
    ) -> ConversationMessageResponse:
        if self._is_learning_help_mock(request.input.text):
            return self._learning_help_response()

        return self._general_checkin_response()

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
