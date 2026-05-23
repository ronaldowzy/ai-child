from app.domain.enums import IntentType, RiskLevel
from app.domain.scene import (
    SceneAction,
    SceneDefinition,
    SceneId,
    SceneRouteDecision,
    SceneRouteRequest,
    SceneTransitionType,
)
from app.repositories.routing_decision_repository import (
    InMemoryRoutingDecisionRepository,
    get_routing_decision_repository,
)


class SceneRegistry:
    def __init__(self) -> None:
        self._definitions: dict[SceneId, SceneDefinition] = {
            SceneId.OPEN_CONVERSATION: SceneDefinition(
                scene_id=SceneId.OPEN_CONVERSATION,
                display_name="开放对话",
                prompt_template="conversation_open_v0_1",
                default_transition=SceneTransitionType.MERGE,
                default_needs_input=None,
                priority=20,
            ),
            SceneId.DAILY_AFTER_SCHOOL_CHECKIN: SceneDefinition(
                scene_id=SceneId.DAILY_AFTER_SCHOOL_CHECKIN,
                display_name="放学后交流",
                prompt_template="daily_after_school_checkin_v0_1",
                default_transition=SceneTransitionType.REPLACE,
                default_needs_input="child_choice",
                priority=30,
            ),
            SceneId.LEARNING_HOMEWORK_HELP: SceneDefinition(
                scene_id=SceneId.LEARNING_HOMEWORK_HELP,
                display_name="学习求助",
                prompt_template="learning_homework_help_v0_1",
                default_transition=SceneTransitionType.PUSH,
                default_needs_input="problem_content",
                priority=60,
            ),
            SceneId.DAILY_BEDTIME_REFLECTION: SceneDefinition(
                scene_id=SceneId.DAILY_BEDTIME_REFLECTION,
                display_name="睡前复盘",
                prompt_template="daily_bedtime_reflection_v0_1",
                default_transition=SceneTransitionType.REPLACE,
                default_needs_input="low_stimulation_reflection",
                priority=40,
            ),
            SceneId.SAFETY_GUARDIAN: SceneDefinition(
                scene_id=SceneId.SAFETY_GUARDIAN,
                display_name="安全守护",
                prompt_template="safety_guardian_v0_1",
                default_transition=SceneTransitionType.REPLACE,
                default_needs_input="trusted_adult_support",
                priority=100,
                is_safety_scene=True,
            ),
            SceneId.SAFETY_GENTLE_CHECKIN: SceneDefinition(
                scene_id=SceneId.SAFETY_GENTLE_CHECKIN,
                display_name="安全温和确认",
                prompt_template="safety_gentle_checkin_v0_1",
                default_transition=SceneTransitionType.MERGE,
                default_needs_input="gentle_checkin",
                priority=80,
                is_safety_scene=True,
            ),
            SceneId.PRIVACY_BOUNDARY: SceneDefinition(
                scene_id=SceneId.PRIVACY_BOUNDARY,
                display_name="隐私边界提醒",
                prompt_template="privacy_boundary_v0_1",
                default_transition=SceneTransitionType.MERGE,
                default_needs_input="privacy_boundary_ack",
                priority=70,
            ),
        }

    def get(self, scene_id: SceneId) -> SceneDefinition:
        return self._definitions[scene_id]

    def list_scene_ids(self) -> list[SceneId]:
        return list(self._definitions.keys())


class SceneOrchestrator:
    """Rule-first scene router and lightweight scene stack manager."""

    def __init__(
        self,
        *,
        scene_registry: SceneRegistry | None = None,
        routing_decision_repository: InMemoryRoutingDecisionRepository | None = None,
    ) -> None:
        self._scene_registry = scene_registry or SceneRegistry()
        self._routing_decision_repository = (
            routing_decision_repository or get_routing_decision_repository()
        )
        self._session_stacks: dict[str, list[SceneId]] = {}

    def route(self, request: SceneRouteRequest) -> SceneRouteDecision:
        current_stack = request.current_stack or self._session_stacks.get(
            request.session_id, []
        )

        if self._requires_safety_guardian(request):
            decision = self._safety_guardian(request)
        elif self._requires_privacy_boundary(request):
            decision = self._privacy_boundary(request, current_stack)
        elif request.risk_level == RiskLevel.WATCH:
            decision = self._safety_gentle_checkin(request, current_stack)
        elif self._should_pop_learning_scene(request, current_stack):
            decision = self._pop_to_previous_scene(request, current_stack)
        elif request.intent == IntentType.LEARNING_HELP:
            decision = self._learning_homework_help(request, current_stack)
        elif request.intent == IntentType.BEDTIME_REFLECTION:
            decision = self._bedtime_reflection(request)
        elif request.intent == IntentType.AFTER_SCHOOL_CHECKIN:
            decision = self._after_school_checkin(request)
        elif request.intent == IntentType.EMOTION_EXPRESSION:
            decision = self._emotion_open_support(request, current_stack)
        else:
            decision = self._open_conversation(request, current_stack)

        self._session_stacks[request.session_id] = decision.scene_stack
        self._routing_decision_repository.save(decision)
        return decision

    def get_session_stack(self, session_id: str) -> list[SceneId]:
        return list(self._session_stacks.get(session_id, []))

    def reset_session(self, session_id: str) -> None:
        self._session_stacks.pop(session_id, None)

    def _requires_safety_guardian(self, request: SceneRouteRequest) -> bool:
        return (
            request.safety_requires_parent_attention
            or request.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}
        )

    def _requires_privacy_boundary(self, request: SceneRouteRequest) -> bool:
        return (
            request.intent == IntentType.PRIVACY_QUESTION
            or request.sub_intent == "privacy_boundary"
        )

    def _should_pop_learning_scene(
        self, request: SceneRouteRequest, current_stack: list[SceneId]
    ) -> bool:
        if not current_stack or current_stack[-1] != SceneId.LEARNING_HOMEWORK_HELP:
            return False
        if request.intent in {IntentType.LEARNING_HELP, IntentType.SAFETY_RISK}:
            return False

        normalized = request.text.strip().lower().replace(" ", "")
        completion_markers = ("做完了", "完成了", "会了", "谢谢", "不用了")
        return any(marker in normalized for marker in completion_markers)

    def _safety_guardian(self, request: SceneRouteRequest) -> SceneRouteDecision:
        scene_id = SceneId.SAFETY_GUARDIAN
        if "self_harm" in request.safety_evidence:
            reply_text = (
                "谢谢你告诉我。这个时候不要一个人待着，先去找爸爸妈妈、"
                "老师或身边安全的大人，好吗？小白狐会提醒爸爸来陪你。"
            )
        else:
            reply_text = (
                "这件事需要让爸爸妈妈或可信任的大人知道。"
                "你不用一个人处理，也不用替别人保守让你不舒服的秘密。"
                "如果那个人还在附近，请先去爸爸妈妈、老师或安全的大人身边。"
            )
        return SceneRouteDecision(
            message_id=request.message_id,
            session_id=request.session_id,
            primary_intent=request.intent,
            base_scene=scene_id,
            active_scene=scene_id,
            transition=SceneTransitionType.REPLACE,
            scene_stack=[scene_id],
            risk_level=request.risk_level,
            confidence=max(request.intent_confidence, 0.99),
            reason="safety_priority",
            requires_parent_attention=True,
            needs_input=self._scene_registry.get(scene_id).default_needs_input,
            reply_text=reply_text,
            reply_emotion="steady",
            quick_actions=[
                SceneAction(id="tell_parent", label="告诉爸爸妈妈"),
                SceneAction(id="find_trusted_adult", label="找可信任的大人"),
            ],
            signals=self._signals(request, transition=SceneTransitionType.REPLACE),
        )

    def _safety_gentle_checkin(
        self, request: SceneRouteRequest, current_stack: list[SceneId]
    ) -> SceneRouteDecision:
        scene_id = SceneId.SAFETY_GENTLE_CHECKIN
        base_scene = self._base_scene_from_stack_or_time(request, current_stack)
        stack = [base_scene] if base_scene == scene_id else [base_scene, scene_id]
        transition = self._scene_registry.get(scene_id).default_transition
        return SceneRouteDecision(
            message_id=request.message_id,
            session_id=request.session_id,
            primary_intent=request.intent,
            base_scene=base_scene,
            active_scene=scene_id,
            transition=transition,
            scene_stack=stack,
            risk_level=request.risk_level,
            confidence=max(request.intent_confidence, 0.86),
            reason="watch_safety_gentle_checkin",
            sub_scene=request.sub_intent,
            side_context=["watch_observation"],
            requires_parent_attention=False,
            needs_input=self._scene_registry.get(scene_id).default_needs_input,
            reply_text=(
                "听起来这件事让你不舒服，谢谢你告诉我。"
                "你可以把这件事告诉爸爸妈妈或老师，让他们一起帮你想办法。"
                "现在你想先说一句发生了什么，还是先安静一下？"
            ),
            reply_emotion="gentle",
            quick_actions=[
                SceneAction(id="tell_parent_or_teacher", label="告诉大人"),
                SceneAction(id="one_sentence", label="说一句"),
                SceneAction(id="quiet_time", label="先安静一下"),
            ],
            signals=self._signals(request, transition=transition),
        )

    def _privacy_boundary(
        self, request: SceneRouteRequest, current_stack: list[SceneId]
    ) -> SceneRouteDecision:
        scene_id = SceneId.PRIVACY_BOUNDARY
        base_scene = self._base_scene_from_stack_or_time(request, current_stack)
        transition = self._scene_registry.get(scene_id).default_transition
        return SceneRouteDecision(
            message_id=request.message_id,
            session_id=request.session_id,
            primary_intent=request.intent,
            base_scene=base_scene,
            active_scene=scene_id,
            transition=transition,
            scene_stack=(
                [base_scene] if base_scene == scene_id else [base_scene, scene_id]
            ),
            risk_level=request.risk_level,
            confidence=max(request.intent_confidence, 0.86),
            reason="privacy_boundary",
            sub_scene=request.sub_intent,
            requires_parent_attention=False,
            needs_input=self._scene_registry.get(scene_id).default_needs_input,
            reply_text=(
                "可以问我，但不要把家庭地址、电话、学校名字或照片"
                "随便告诉 AI 或陌生人。需要填写这些信息时，先问爸爸妈妈。"
                "你可以只说“我想问隐私问题”，不用说真实信息。"
            ),
            reply_emotion="steady",
            quick_actions=[
                SceneAction(id="understand_privacy", label="我知道了"),
                SceneAction(id="ask_parent", label="问爸爸妈妈"),
            ],
            signals=self._signals(request, transition=transition),
        )

    def _learning_homework_help(
        self, request: SceneRouteRequest, current_stack: list[SceneId]
    ) -> SceneRouteDecision:
        scene_id = SceneId.LEARNING_HOMEWORK_HELP
        base_scene = self._base_scene_from_stack_or_time(request, current_stack)
        base_stack = current_stack or [base_scene]
        if base_stack[-1] == scene_id:
            transition = SceneTransitionType.MERGE
            next_stack = base_stack
        else:
            transition = SceneTransitionType.PUSH
            next_stack = [*base_stack, scene_id]

        has_clear_problem = (
            bool(request.homework_problem_text)
            and request.homework_problem_confidence is not None
            and request.homework_problem_confidence >= 0.75
        )
        if request.sub_intent == "direct_answer_request":
            return SceneRouteDecision(
                message_id=request.message_id,
                session_id=request.session_id,
                primary_intent=request.intent,
                base_scene=next_stack[0],
                active_scene=scene_id,
                transition=transition,
                scene_stack=next_stack,
                risk_level=request.risk_level,
                confidence=max(request.intent_confidence, 0.9),
                reason="learning_direct_answer_request",
                sub_scene="scaffold_before_answer",
                needs_input="problem_understanding",
                reply_text=(
                    "我不会直接告诉你最终答案。我们先把题目拆开："
                    "这道题是在问什么？你觉得第一步可以先看哪个条件？"
                ),
                quick_actions=[
                    SceneAction(id="describe_problem", label="说题意"),
                    SceneAction(id="first_step", label="说第一步"),
                ],
                signals=self._signals(request, transition=transition),
            )

        if has_clear_problem:
            return SceneRouteDecision(
                message_id=request.message_id,
                session_id=request.session_id,
                primary_intent=request.intent,
                base_scene=next_stack[0],
                active_scene=scene_id,
                transition=transition,
                scene_stack=next_stack,
                risk_level=request.risk_level,
                confidence=max(request.intent_confidence, 0.96),
                reason="homework_attachment_ready",
                sub_scene="ask_problem_understanding",
                needs_input="problem_understanding",
                reply_text=(
                    "我看清楚了。我们先不急着算。"
                    "你能告诉我：这道题是在问什么吗？"
                ),
                quick_actions=[],
                signals=self._signals(request, transition=transition),
            )

        return SceneRouteDecision(
            message_id=request.message_id,
            session_id=request.session_id,
            primary_intent=request.intent,
            base_scene=next_stack[0],
            active_scene=scene_id,
            transition=transition,
            scene_stack=next_stack,
            risk_level=request.risk_level,
            confidence=max(request.intent_confidence, 0.94),
            reason="learning_help_intent",
            sub_scene="homework_problem_intake",
            needs_input=self._scene_registry.get(scene_id).default_needs_input,
            reply_text=(
                "可以，我们一起一步一步拆开它。你先不用急着要答案，"
                "可以拍一张题目的照片，或者先把题目读给我听。"
            ),
            quick_actions=[
                SceneAction(id="take_photo", label="拍题目"),
                SceneAction(id="speak_problem", label="读题目"),
            ],
            signals=self._signals(request, transition=transition),
        )

    def _bedtime_reflection(self, request: SceneRouteRequest) -> SceneRouteDecision:
        scene_id = SceneId.DAILY_BEDTIME_REFLECTION
        return SceneRouteDecision(
            message_id=request.message_id,
            session_id=request.session_id,
            primary_intent=request.intent,
            base_scene=scene_id,
            active_scene=scene_id,
            transition=SceneTransitionType.REPLACE,
            scene_stack=[scene_id],
            risk_level=request.risk_level,
            confidence=max(request.intent_confidence, 0.92),
            reason="bedtime_reflection_intent",
            needs_input=self._scene_registry.get(scene_id).default_needs_input,
            reply_text=(
                "晚安。我们轻轻收个尾：今天有一件还不错的小事吗？"
                "如果不想说，也可以只选一个心情。"
            ),
            reply_emotion="calm",
            quick_actions=[
                SceneAction(id="good_moment", label="还不错的小事"),
                SceneAction(id="mood_only", label="只选心情"),
                SceneAction(id="sleep_now", label="直接睡觉"),
            ],
            signals=self._signals(request, transition=SceneTransitionType.REPLACE),
        )

    def _after_school_checkin(self, request: SceneRouteRequest) -> SceneRouteDecision:
        scene_id = SceneId.OPEN_CONVERSATION
        return SceneRouteDecision(
            message_id=request.message_id,
            session_id=request.session_id,
            primary_intent=request.intent,
            base_scene=scene_id,
            active_scene=scene_id,
            transition=SceneTransitionType.REPLACE,
            scene_stack=[scene_id],
            risk_level=request.risk_level,
            confidence=max(request.intent_confidence, 0.9),
            reason="arrival_context_open_conversation",
            side_context=["after_school_arrival"],
            needs_input=None,
            reply_text=(
                "回来啦。我们不用急着汇报学校，你想先聊刚想到的事，"
                "还是先安静一小会儿？"
            ),
            reply_emotion="listening",
            quick_actions=[],
            signals=self._signals(request, transition=SceneTransitionType.REPLACE),
        )

    def _emotion_open_support(
        self, request: SceneRouteRequest, current_stack: list[SceneId]
    ) -> SceneRouteDecision:
        if current_stack:
            active_scene = current_stack[-1]
            if active_scene == SceneId.LEARNING_HOMEWORK_HELP:
                return self._learning_homework_help(request, current_stack)
            if active_scene == SceneId.DAILY_BEDTIME_REFLECTION:
                return self._bedtime_reflection(request)

        scene_id = SceneId.OPEN_CONVERSATION
        return SceneRouteDecision(
            message_id=request.message_id,
            session_id=request.session_id,
            primary_intent=request.intent,
            base_scene=scene_id,
            active_scene=scene_id,
            transition=SceneTransitionType.REPLACE,
            scene_stack=[scene_id],
            risk_level=request.risk_level,
            confidence=max(request.intent_confidence, 0.72),
            reason="emotion_context_open_conversation",
            side_context=["low_pressure_emotion_support"],
            needs_input=None,
            reply_text=(
                "可以的，我们先不聊很多。你可以安静一会儿，"
                "也可以只说一个字或一个小表情。"
            ),
            reply_emotion="calm",
            quick_actions=[],
            signals=self._signals(request, transition=SceneTransitionType.REPLACE),
        )

    def _open_conversation(
        self, request: SceneRouteRequest, current_stack: list[SceneId]
    ) -> SceneRouteDecision:
        scene_id = SceneId.OPEN_CONVERSATION
        stack = [scene_id]
        if current_stack and current_stack[-1] == scene_id:
            transition = SceneTransitionType.MERGE
        else:
            transition = SceneTransitionType.REPLACE
        return SceneRouteDecision(
            message_id=request.message_id,
            session_id=request.session_id,
            primary_intent=request.intent,
            base_scene=scene_id,
            active_scene=scene_id,
            transition=transition,
            scene_stack=stack,
            risk_level=request.risk_level,
            confidence=max(request.intent_confidence, 0.72),
            reason="open_conversation",
            needs_input=None,
            reply_text=(
                "我在听。你可以接着说这个话题，我会顺着你的想法聊。"
            ),
            reply_emotion="listening",
            quick_actions=[],
            signals=self._signals(request, transition=transition),
        )

    def _pop_to_previous_scene(
        self, request: SceneRouteRequest, current_stack: list[SceneId]
    ) -> SceneRouteDecision:
        next_stack = current_stack[:-1] or [SceneId.OPEN_CONVERSATION]
        active_scene = next_stack[-1]
        if active_scene == SceneId.OPEN_CONVERSATION:
            return SceneRouteDecision(
                message_id=request.message_id,
                session_id=request.session_id,
                primary_intent=request.intent,
                base_scene=SceneId.OPEN_CONVERSATION,
                active_scene=SceneId.OPEN_CONVERSATION,
                transition=SceneTransitionType.POP,
                scene_stack=[SceneId.OPEN_CONVERSATION],
                risk_level=request.risk_level,
                confidence=max(request.intent_confidence, 0.86),
                reason="learning_scene_completed",
                needs_input=None,
                reply_text="好，我们先把这道题放回作业本里。接下来你想聊什么都可以。",
                reply_emotion="warm",
                quick_actions=[],
                signals=self._signals(request, transition=SceneTransitionType.POP),
            )
        return self._checkin_decision(
            request,
            scene_id=active_scene,
            transition=SceneTransitionType.POP,
            reason="learning_scene_completed",
            confidence=max(request.intent_confidence, 0.86),
            scene_stack=next_stack,
            reply_text="好，我们先把这道题放回作业本里。现在可以轻轻收一下尾。",
        )

    def _checkin_decision(
        self,
        request: SceneRouteRequest,
        *,
        scene_id: SceneId,
        transition: SceneTransitionType,
        reason: str,
        confidence: float,
        scene_stack: list[SceneId] | None = None,
        reply_text: str | None = None,
    ) -> SceneRouteDecision:
        stack = scene_stack or [scene_id]
        return SceneRouteDecision(
            message_id=request.message_id,
            session_id=request.session_id,
            primary_intent=request.intent,
            base_scene=stack[0],
            active_scene=scene_id,
            transition=transition,
            scene_stack=stack,
            risk_level=request.risk_level,
            confidence=confidence,
            reason=reason,
            needs_input=self._scene_registry.get(scene_id).default_needs_input,
            reply_text=reply_text
            or self._checkin_reply_text(request),
            quick_actions=[
                SceneAction(id="happy_moment", label="开心的事"),
                SceneAction(id="hard_thing", label="遇到的难题"),
                SceneAction(id="quiet_time", label="想安静一会儿"),
            ],
            signals=self._signals(request, transition=transition),
        )

    def _checkin_reply_text(self, request: SceneRouteRequest) -> str:
        if request.intent == IntentType.EMOTION_EXPRESSION:
            return (
                "可以的，我们先不聊很多。你可以安静一会儿，"
                "也可以选想安静一会儿；等你想说时再说。"
            )
        goal_text = "，".join(request.parent_goals)
        if "小困难" in goal_text:
            return (
                "我在这里。今天如果愿意，可以只说一个小困难；"
                "也可以先选一个轻松选项：开心的事、遇到的难题，"
                "或者想安静一会儿。"
            )
        if "学校小事" in goal_text:
            return (
                "我在这里。你可以只说一件学校小事，不用说很多；"
                "也可以选今天开心的事、遇到的难题，或者想安静一会儿。"
            )
        return (
            "我在这里。你可以先选一个最想说的小事情："
            "今天开心的事、遇到的难题，或者想安静一会儿。"
        )

    def _base_scene_from_stack_or_time(
        self, request: SceneRouteRequest, current_stack: list[SceneId]
    ) -> SceneId:
        if current_stack:
            return current_stack[0]
        return SceneId.OPEN_CONVERSATION

    def _signals(
        self,
        request: SceneRouteRequest,
        *,
        transition: SceneTransitionType,
    ) -> dict[str, object]:
        return {
            "time_period": request.time_context.time_period.value,
            "intent": request.intent.value,
            "sub_intent": request.sub_intent,
            "intent_evidence": request.intent_evidence,
            "needs_modality": request.needs_modality,
            "suggested_modalities": request.suggested_modalities,
            "risk_level": request.risk_level.value,
            "safety_requires_parent_attention": (
                request.safety_requires_parent_attention
            ),
            "safety_evidence": request.safety_evidence,
            "parent_goal_count": len(request.parent_goals),
            "has_homework_attachment": bool(request.homework_problem_text),
            "homework_problem_confidence": request.homework_problem_confidence,
            "transition": transition.value,
        }


_scene_orchestrator = SceneOrchestrator()


def get_scene_orchestrator() -> SceneOrchestrator:
    return _scene_orchestrator
