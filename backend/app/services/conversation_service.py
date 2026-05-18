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
from app.domain.enums import IntentType
from app.services.intent_classifier import (
    IntentClassifier,
    get_intent_classifier,
)
from app.services.parent_policy_service import (
    ParentPolicyService,
    get_parent_policy_service,
)
from app.services.safety_engine import SafetyEngine, get_safety_engine
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
        safety_engine: SafetyEngine | None = None,
        intent_classifier: IntentClassifier | None = None,
        debug_enabled: bool = True,
    ) -> None:
        self._time_context_service = time_context_service or get_time_context_service()
        self._parent_policy_service = (
            parent_policy_service or get_parent_policy_service()
        )
        self._safety_engine = safety_engine or get_safety_engine()
        self._intent_classifier = intent_classifier or get_intent_classifier()
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

        if intent.intent == IntentType.SAFETY_RISK:
            response = self._safety_guardian_response()
        elif intent.intent == IntentType.LEARNING_HELP:
            response = self._learning_help_response()
        elif intent.intent == IntentType.BEDTIME_REFLECTION:
            response = self._bedtime_reflection_response()
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

    def _bedtime_reflection_response(self) -> ConversationMessageResponse:
        return ConversationMessageResponse(
            reply=Reply(
                text=(
                    "晚安。我们轻轻收个尾：今天有一件还不错的小事吗？"
                    "如果不想说，也可以只选一个心情。"
                ),
                emotion="calm",
            ),
            ui_actions=[
                UiAction(
                    actions=[
                        QuickAction(id="good_moment", label="还不错的小事"),
                        QuickAction(id="mood_only", label="只选心情"),
                        QuickAction(id="sleep_now", label="直接睡觉"),
                    ]
                )
            ],
            session_state=SessionState(
                base_scene="daily.bedtime_reflection",
                active_scene="daily.bedtime_reflection",
                needs_input="low_stimulation_reflection",
            ),
        )

    def _safety_guardian_response(self) -> ConversationMessageResponse:
        return ConversationMessageResponse(
            reply=Reply(
                text=(
                    "这件事需要让爸爸妈妈或可信任的大人知道。"
                    "你不用一个人处理，也不用替别人保守让你不舒服的秘密。"
                    "如果那个人还在附近，请先去爸爸妈妈、老师或安全的大人身边。"
                ),
                emotion="steady",
            ),
            ui_actions=[
                UiAction(
                    actions=[
                        QuickAction(id="tell_parent", label="告诉爸爸妈妈"),
                        QuickAction(id="find_trusted_adult", label="找可信任的大人"),
                    ]
                )
            ],
            session_state=SessionState(
                base_scene="safety.guardian",
                active_scene="safety.guardian",
                needs_input="trusted_adult_support",
                requires_parent_attention=True,
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
