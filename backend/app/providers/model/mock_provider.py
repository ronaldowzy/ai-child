from typing import Any

from app.domain.model_types import (
    ModelProfile,
    ModelRequest,
    ModelResponse,
    ModelTaskType,
)
from app.providers.model.base import BaseModelProvider, ModelProviderDisabledError


class MockModelProvider(BaseModelProvider):
    def __init__(self, *, provider_name: str = "mock", enabled: bool = True) -> None:
        super().__init__(provider_name=provider_name, enabled=enabled)

    def generate(
        self,
        request: ModelRequest,
        *,
        profile: ModelProfile | None = None,
    ) -> ModelResponse:
        if not self.enabled:
            raise ModelProviderDisabledError(f"Provider {self.provider_name} is disabled")

        model_name = profile.model_name if profile else "mock-model-v0"
        response_text, structured_output = self._mock_output(request)
        return ModelResponse(
            task_type=request.task_type,
            response_text=response_text,
            structured_output=structured_output,
            provider_name=self.provider_name,
            model_name=model_name,
            metadata={
                "mock": True,
                "profile_name": profile.profile_name if profile else None,
                "timeout_ms": profile.default_params.timeout_ms if profile else None,
            },
        )

    def _mock_output(self, request: ModelRequest) -> tuple[str, dict[str, Any]]:
        task_type = request.task_type
        if task_type == ModelTaskType.CHILD_CHAT:
            return self._child_chat_output(request)
        if task_type == ModelTaskType.INTENT_CLASSIFICATION:
            return self._intent_output(request.input_text or "")
        if task_type == ModelTaskType.SAFETY_CLASSIFICATION:
            return self._safety_output(request.input_text or "")
        if task_type == ModelTaskType.MEMORY_EXTRACTION:
            return self._memory_output()
        if task_type == ModelTaskType.PARENT_REPORT:
            return self._parent_report_output()
        if task_type == ModelTaskType.VISION:
            return self._vision_output()
        if task_type == ModelTaskType.OCR:
            return self._ocr_output()

        return (
            "Mock 模型暂时没有这个任务的专用输出。",
            {"task_type": str(task_type), "handled": False},
        )

    def _child_chat_output(
        self, request: ModelRequest
    ) -> tuple[str, dict[str, Any]]:
        scene_route = request.context.get("scene_route", {})
        fallback_reply_text = scene_route.get("fallback_reply_text")
        active_scene = scene_route.get("active_scene")
        text, strategy = self._mock_child_dialogue_text(
            input_text=request.input_text or "",
            active_scene=str(active_scene or ""),
            sub_scene=scene_route.get("sub_scene"),
            needs_input=scene_route.get("needs_input"),
            parent_policy=request.context.get("parent_policy"),
            image_context=request.context.get("conversation", {}).get("image_context"),
            turn_guidance=request.context.get("turn_guidance"),
            fallback_reply_text=(
                fallback_reply_text
                if isinstance(fallback_reply_text, str)
                else None
            ),
        )
        conversation_control = self._mock_conversation_control(
            request.context.get("turn_guidance"),
            text,
        )
        return (
            text,
            {
                "reply": text,
                "conversation_control": conversation_control,
                "scene_hint": active_scene or "daily.after_school_checkin",
                "requires_parent_attention": bool(
                    scene_route.get("requires_parent_attention", False)
                ),
                "mock_child_chat_strategy": strategy,
            },
        )

    def _mock_child_dialogue_text(
        self,
        *,
        input_text: str,
        active_scene: str,
        sub_scene: object,
        needs_input: object,
        parent_policy: object,
        image_context: object,
        turn_guidance: object,
        fallback_reply_text: str | None,
    ) -> tuple[str, str]:
        """Return a deterministic but less scripted child-chat reply.

        This keeps local tests mock-first while making the default UX closer to a
        free child conversation. Hard safety and homework boundaries still use
        scene-scoped wording.
        """
        normalized = input_text.strip().lower().replace(" ", "")

        if active_scene == "safety.guardian" and fallback_reply_text:
            return fallback_reply_text, "safety_scene_fallback"
        if active_scene == "privacy.boundary" and fallback_reply_text:
            return fallback_reply_text, "privacy_scene_fallback"
        if active_scene == "safety.gentle_checkin":
            return (
                "听起来这件事让你不舒服。你可以告诉家长或老师。现在你想先说一句，还是先安静一下？",
                "watch_gentle_checkin",
            )
        if active_scene == "learning.homework_help":
            if sub_scene == "scaffold_before_answer" and fallback_reply_text:
                return fallback_reply_text, "learning_direct_answer_fallback"
            if sub_scene == "ask_problem_understanding":
                return (
                    "我看到了题目。我们先不急着算，你先说说：这道题是在问什么？",
                    "learning_problem_understanding",
                )
            return (
                "可以，我们一步一步来。你先不用急着要答案，可以拍一张题目的照片，或者把题目读给我听。",
                "learning_problem_intake",
            )
        if active_scene == "daily.bedtime_reflection":
            return (
                "晚安。我们轻轻收个尾就好：今天有一件还不错的小事吗？不想说也可以直接休息。",
                "bedtime_closeout",
            )

        if self._contains_any(normalized, ("不想说话", "好累", "很烦")):
            return (
                "可以的，我们先不聊很多。你可以安静一会儿，我就在这里等你。等你想说时，只说一个字也可以。",
                "low_energy_support",
            )

        image_reply = self._image_context_reply(normalized, image_context)
        if image_reply:
            return image_reply, "image_context_continuity"

        if self._contains_any(normalized, ("我回来了", "放学了", "到家了")):
            goal_text = self._compact_parent_goals(parent_policy)
            if "小困难" in goal_text:
                return (
                    "回来啦。我们不用急着汇报学校。如果你愿意，可以从一个很小的地方开始：今天有没有一个小困难，或者一个让你停了一下的瞬间？",
                    "after_school_arrival_parent_goal",
                )
            return (
                "回来啦。我们不用急着汇报学校。你想先聊刚想到的事，还是先安静一小会儿？",
                "after_school_arrival",
            )

        topic = self._topic_hint(input_text)
        if topic:
            return (
                f"{topic}听起来可以聊。你想先说它有趣的地方，还是说你为什么想到它？",
                "free_dialogue_topic_echo",
            )
        if self._mock_control_topic_continuity(turn_guidance) == "soft_shift":
            return (
                "好，我们先换个轻松的。可以聊画画，也可以拍个东西给小白狐看。",
                "model_control_soft_shift",
            )

        if needs_input == "child_choice" and fallback_reply_text:
            return fallback_reply_text, "checkin_scene_fallback"
        return (
            "我在听。你可以随便说一件现在想到的小事，我会跟着你的话题慢慢聊。",
            "free_dialogue_default",
        )

    def _image_context_reply(
        self,
        normalized: str,
        image_context: object,
    ) -> str | None:
        if not isinstance(image_context, dict):
            return None
        recognized_type = image_context.get("recognized_type")
        if recognized_type == "privacy_sensitive":
            return (
                "这张图片里可能有隐私信息，我们先不要继续展开。"
                "如果需要处理它，请先让家长帮你确认。"
            )
        text = str(
            image_context.get("recognized_text")
            or image_context.get("child_caption")
            or ""
        ).strip()
        if not text:
            return None
        phrase = self._compact_image_phrase(text)
        if self._contains_any(normalized, ("故事", "编")):
            return f"那我们可以把这张图里的“{phrase}”当成开头，编一个轻轻的小故事。你想让它发生在家里，还是森林里？"
        if self._contains_any(normalized, ("是什么", "这是什么", "问")):
            return f"我先按图片描述来猜：这里像是“{phrase}”。你可以再告诉我一个细节，我们一起判断。"
        return f"我们继续聊这张图吧。我记得你刚刚分享的是“{phrase}”。你最想先说它哪里有趣？"

    def _mock_conversation_control(
        self,
        turn_guidance: object,
        reply_text: str,
    ) -> dict[str, Any]:
        continuity = self._mock_control_topic_continuity(turn_guidance)
        engagement = "unclear"
        shift_intent = "unclear"
        reason = "mock_unclear"
        moves = [
            {"id": "continue_current", "label": "接着说这个"},
            {"id": "shift_topic", "label": "换个轻松话题"},
            {"id": "show_something", "label": "拍给小白狐看"},
        ]
        if continuity == "soft_shift":
            engagement = "low"
            shift_intent = "likely"
            reason = "short_answer_after_repeated_topic"
        elif continuity == "continue":
            engagement = "high"
            shift_intent = "unlikely"
            reason = "child_added_vivid_detail"
        elif continuity == "stop":
            engagement = "low"
            shift_intent = "explicit"
            reason = "explicit_boundary"
            moves = []
        return {
            "child_engagement": engagement,
            "topic_continuity": continuity,
            "topic_shift_intent": shift_intent,
            "reason": reason,
            "suggested_next_moves": moves,
        }

    def _mock_control_topic_continuity(self, turn_guidance: object) -> str:
        if not isinstance(turn_guidance, dict):
            return "unclear"
        boundary = turn_guidance.get("boundary_signal")
        if boundary in {"bedtime", "no_chat"}:
            return "stop"
        if boundary == "topic_change" or turn_guidance.get("topic_shift_recommended") is True:
            return "soft_shift"
        if turn_guidance.get("child_engagement_signal") == "engaged":
            return "continue"
        return "unclear"

    def _compact_image_phrase(self, text: str) -> str:
        compact = " ".join(text.strip().split())
        if len(compact) <= 48:
            return compact
        return f"{compact[:48]}..."

    def _compact_parent_goals(self, parent_policy: object) -> str:
        if not isinstance(parent_policy, dict):
            return ""
        goals = parent_policy.get("goals")
        if isinstance(goals, list):
            return "，".join(str(goal) for goal in goals)
        return str(goals or "")

    def _topic_hint(self, input_text: str) -> str:
        text = input_text.strip()
        if not text:
            return ""
        prefixes = (
            "我想聊",
            "我喜欢",
            "我今天看到",
            "我在想",
            "我想说",
        )
        for prefix in prefixes:
            if text.startswith(prefix) and len(text) > len(prefix):
                return text[len(prefix) : len(prefix) + 12].strip("，。！？ ")
        if len(text) <= 16 and not self._contains_any(text, ("吗", "?", "？")):
            return text.strip("，。！？ ")
        return ""

    def _intent_output(self, input_text: str) -> tuple[str, dict[str, Any]]:
        normalized = input_text.strip().lower().replace(" ", "")
        learning_keywords = (
            "我有一道题不会",
            "有一道题不会",
            "有题不会",
            "这道题不会",
            "这题不会",
            "这道题怎么做",
            "这题怎么做",
            "帮我看看作业",
            "帮我看作业",
            "数学题不会",
            "语文题不会",
            "英语题不会",
            "英语作业",
            "语文作业",
            "数学作业",
            "口算题",
            "应用题",
            "练习册",
            "课文作业",
            "作文作业",
        )
        general_not_know = (
            "不会画",
            "不会搭",
            "不会拼",
            "游戏里",
            "谜题",
            "问题考你",
            "考考你",
        )
        intent = (
            "learning_help"
            if any(keyword in normalized for keyword in learning_keywords)
            and not any(marker in normalized for marker in general_not_know)
            else "general_checkin"
        )
        return (
            "Mock 意图分类已完成。",
            {
                "intent": intent,
                "confidence": 0.8,
                "evidence": "keyword_mock",
            },
        )

    def _contains_any(self, text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)

    def _safety_output(self, input_text: str) -> tuple[str, dict[str, Any]]:
        high_risk_markers = (
            "不要告诉爸爸",
            "不要告诉妈妈",
            "别告诉爸爸",
            "别告诉妈妈",
            "陌生人",
            "保密",
        )
        is_high_risk = any(marker in input_text for marker in high_risk_markers)
        return (
            "Mock 安全分类已完成。",
            {
                "risk_level": "high" if is_high_risk else "low",
                "risk_category": (
                    "unsafe_secret_or_stranger_contact"
                    if is_high_risk
                    else "none"
                ),
                "requires_parent_attention": is_high_risk,
                "safe_response_hint": (
                    "encourage_trusted_adult"
                    if is_high_risk
                    else "continue_normal_flow"
                ),
            },
        )

    def _memory_output(self) -> tuple[str, dict[str, Any]]:
        return (
            "Mock 记忆抽取已完成。",
            {
                "memories": [],
                "write_allowed": True,
                "retention": "structured_only",
            },
        )

    def _parent_report_output(self) -> tuple[str, dict[str, Any]]:
        return (
            "今天的日报暂时由 Mock 模型生成，后续会接入结构化摘要。",
            {
                "summary": "暂无需要家长立即处理的事项。",
                "requires_attention": False,
                "highlights": [],
            },
        )

    def _vision_output(self) -> tuple[str, dict[str, Any]]:
        return (
            "我现在还不能真正看图，可以请你把图片里的内容说给我听。",
            {
                "recognized_content": None,
                "confidence": 0.0,
                "fallback_action": "ask_child_to_describe",
            },
        )

    def _ocr_output(self) -> tuple[str, dict[str, Any]]:
        return (
            "我现在先用占位识别。你可以把题目读给我听，我们先确认题目在问什么。",
            {
                "recognized_text": None,
                "confidence": 0.0,
                "fallback_action": "speak_problem",
            },
        )
