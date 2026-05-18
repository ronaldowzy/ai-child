from app.domain.enums import IntentType, RiskLevel
from app.domain.scene import (
    SceneAction,
    SceneDefinition,
    SceneId,
    SceneRouteDecision,
    SceneRouteRequest,
    SceneTransitionType,
)
from app.domain.time import TimePeriod
from app.repositories.routing_decision_repository import (
    InMemoryRoutingDecisionRepository,
    get_routing_decision_repository,
)


class SceneRegistry:
    def __init__(self) -> None:
        self._definitions: dict[SceneId, SceneDefinition] = {
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
        elif self._should_pop_learning_scene(request, current_stack):
            decision = self._pop_to_previous_scene(request, current_stack)
        elif request.intent == IntentType.LEARNING_HELP:
            decision = self._learning_homework_help(request, current_stack)
        elif request.intent == IntentType.BEDTIME_REFLECTION:
            decision = self._bedtime_reflection(request)
        elif request.intent == IntentType.AFTER_SCHOOL_CHECKIN:
            decision = self._after_school_checkin(request)
        else:
            decision = self._fallback_checkin(request, current_stack)

        self._session_stacks[request.session_id] = decision.scene_stack
        self._routing_decision_repository.save(decision)
        return decision

    def get_session_stack(self, session_id: str) -> list[SceneId]:
        return list(self._session_stacks.get(session_id, []))

    def reset_session(self, session_id: str) -> None:
        self._session_stacks.pop(session_id, None)

    def _requires_safety_guardian(self, request: SceneRouteRequest) -> bool:
        return (
            request.intent == IntentType.SAFETY_RISK
            or request.safety_requires_parent_attention
            or request.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}
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
            reply_text=(
                "这件事需要让爸爸妈妈或可信任的大人知道。"
                "你不用一个人处理，也不用替别人保守让你不舒服的秘密。"
                "如果那个人还在附近，请先去爸爸妈妈、老师或安全的大人身边。"
            ),
            reply_emotion="steady",
            quick_actions=[
                SceneAction(id="tell_parent", label="告诉爸爸妈妈"),
                SceneAction(id="find_trusted_adult", label="找可信任的大人"),
            ],
            signals=self._signals(request, transition=SceneTransitionType.REPLACE),
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
        scene_id = SceneId.DAILY_AFTER_SCHOOL_CHECKIN
        return self._checkin_decision(
            request,
            scene_id=scene_id,
            transition=SceneTransitionType.REPLACE,
            reason="after_school_checkin_intent",
            confidence=max(request.intent_confidence, 0.9),
        )

    def _fallback_checkin(
        self, request: SceneRouteRequest, current_stack: list[SceneId]
    ) -> SceneRouteDecision:
        if current_stack:
            active_scene = current_stack[-1]
            if active_scene == SceneId.LEARNING_HOMEWORK_HELP:
                return self._learning_homework_help(request, current_stack)
            if active_scene == SceneId.DAILY_BEDTIME_REFLECTION:
                return self._bedtime_reflection(request)

        return self._checkin_decision(
            request,
            scene_id=SceneId.DAILY_AFTER_SCHOOL_CHECKIN,
            transition=SceneTransitionType.REPLACE,
            reason="default_low_pressure_checkin",
            confidence=max(request.intent_confidence, 0.72),
        )

    def _pop_to_previous_scene(
        self, request: SceneRouteRequest, current_stack: list[SceneId]
    ) -> SceneRouteDecision:
        next_stack = current_stack[:-1] or [SceneId.DAILY_AFTER_SCHOOL_CHECKIN]
        active_scene = next_stack[-1]
        return self._checkin_decision(
            request,
            scene_id=active_scene,
            transition=SceneTransitionType.POP,
            reason="learning_scene_completed",
            confidence=max(request.intent_confidence, 0.86),
            scene_stack=next_stack,
            reply_text="好，我们先把这道题放回作业本里。现在可以选一个轻松的小话题收一下尾。",
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
        if request.time_context.time_period == TimePeriod.BEDTIME:
            return SceneId.DAILY_BEDTIME_REFLECTION
        return SceneId.DAILY_AFTER_SCHOOL_CHECKIN

    def _signals(
        self,
        request: SceneRouteRequest,
        *,
        transition: SceneTransitionType,
    ) -> dict[str, object]:
        return {
            "time_period": request.time_context.time_period.value,
            "intent": request.intent.value,
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
