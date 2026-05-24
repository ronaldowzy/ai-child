import re
from typing import Any

from app.domain.agent_runtime import (
    AgentRuntimeRequest,
    AgentRuntimeResult,
    AgentRuntimeSource,
)
from app.domain.enums import RiskLevel
from app.domain.model_types import ModelMessage, ModelRequest, ModelTaskType
from app.domain.prompt import PromptVersion
from app.domain.scene import SceneAction, SceneId
from app.services.age_band_policy import (
    AgeBandReplyPolicy,
    derive_age_band_reply_policy,
)
from app.services.model_registry import ModelRegistry, get_model_registry
from app.services.prompt_manager import PromptManager, get_prompt_manager
from app.services.safety_engine import SafetyEngine, get_safety_engine
from app.services.turn_guidance_builder import (
    TurnGuidanceBuilder,
    TurnGuidanceContext,
)


class ChildAgentRuntime:
    """Executes the child-facing model turn after scene routing."""

    SELF_HARM_GUARDIAN_REPLY = (
        "谢谢你告诉我。这个时候不要一个人待着，先去找爸爸妈妈、"
        "老师或身边安全的大人，好吗？小白狐会提醒爸爸来陪你。"
    )
    BEDTIME_CLOSE_REPLY = "好的，我们今天先轻轻收个尾。晚安，睡个好觉。"
    _STAGE_DIRECTION_PATTERN = re.compile(
        r"[（(]\s*(?:用|以)?[^（）()]{0,30}"
        r"(?:语气|语调|口吻|声音|温柔|温和|轻声|轻轻|平静|柔和|好奇)"
        r"[^（）()]{0,30}[）)]"
    )

    def __init__(
        self,
        *,
        prompt_manager: PromptManager | None = None,
        model_registry: ModelRegistry | None = None,
        safety_engine: SafetyEngine | None = None,
        turn_guidance_builder: TurnGuidanceBuilder | None = None,
    ) -> None:
        self._prompt_manager = prompt_manager or get_prompt_manager()
        self._model_registry = model_registry or get_model_registry()
        self._safety_engine = safety_engine or get_safety_engine()
        self._turn_guidance_builder = turn_guidance_builder or TurnGuidanceBuilder()

    def run(self, request: AgentRuntimeRequest) -> AgentRuntimeResult:
        prompt_versions: dict[str, PromptVersion] = {}
        turn_guidance_context = self._build_turn_guidance_context(request)
        age_policy = derive_age_band_reply_policy(request.parent_policy)
        try:
            composed_prompt = self._prompt_manager.compose(
                request.route_decision.active_scene.value,
                parent_policy=request.parent_policy,
                time_context=request.time_context,
                image_context=request.conversation_metadata.get("image_context"),
                turn_guidance_context=turn_guidance_context,
                memory_context=request.memory_context,
            )
            prompt_versions = composed_prompt.prompt_versions
        except Exception:
            return self._fallback_result(
                request,
                fallback_reason="prompt_compose_failed",
                prompt_versions=prompt_versions,
            )

        model_request = ModelRequest(
            task_type=ModelTaskType.CHILD_CHAT,
            messages=[
                ModelMessage(role="system", content=composed_prompt.prompt),
                *request.conversation_history,
                ModelMessage(role="user", content=request.child_text),
            ],
            input_text=request.child_text,
            context=self._model_context(request, turn_guidance_context, age_policy),
            metadata=self._model_metadata(
                request,
                prompt_versions,
                turn_guidance_context,
                age_policy,
            ),
        )

        try:
            model_response = self._model_registry.generate(model_request)
        except Exception:
            return self._fallback_result(
                request,
                fallback_reason="model_generate_failed",
                prompt_versions=prompt_versions,
            )

        registry_fallback_reason = self._registry_fallback_reason(
            model_response.metadata
        )
        if registry_fallback_reason is not None:
            return self._fallback_result(
                request,
                fallback_reason=registry_fallback_reason,
                prompt_versions=prompt_versions,
                provider_name=model_response.provider_name,
                model_name=model_response.model_name,
                model_metadata=model_response.metadata,
            )

        model_response.metadata.setdefault("age_band", age_policy.age_band)
        model_response.metadata.setdefault("reply_char_budget", age_policy.reply_char_budget)
        model_response.metadata.setdefault(
            "turn_guidance_hints",
            list(turn_guidance_context.hints),
        )
        raw_reply_text = model_response.response_text.strip()
        reply_text = self._normalize_model_reply(
            raw_reply_text,
            request,
            turn_guidance_context,
            age_policy,
        )
        image_context_reply = self._image_context_repair_reply(request, reply_text)
        if image_context_reply:
            reply_text = image_context_reply
            model_response.metadata["image_context_reply_repaired"] = True
        if reply_text != raw_reply_text:
            model_response.metadata["reply_normalized"] = True
        if not reply_text:
            return self._fallback_result(
                request,
                fallback_reason="empty_model_response",
                prompt_versions=prompt_versions,
                provider_name=model_response.provider_name,
                model_name=model_response.model_name,
                model_metadata=model_response.metadata,
                turn_guidance_context=turn_guidance_context,
                age_policy=age_policy,
            )
        if self._requires_deterministic_self_harm_reply(request):
            return self._fallback_result(
                request,
                fallback_reason="deterministic_self_harm_guardian",
                prompt_versions=prompt_versions,
                provider_name=model_response.provider_name,
                model_name=model_response.model_name,
                model_metadata=model_response.metadata,
                turn_guidance_context=turn_guidance_context,
                age_policy=age_policy,
            )

        output_safety = self._safety_engine.classify_output(reply_text)
        if output_safety.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            return self._fallback_result(
                request,
                fallback_reason="unsafe_model_output",
                prompt_versions=prompt_versions,
                provider_name=model_response.provider_name,
                model_name=model_response.model_name,
                model_metadata=model_response.metadata,
                output_risk_level=output_safety.risk_level,
                turn_guidance_context=turn_guidance_context,
                age_policy=age_policy,
            )
        if self._looks_like_direct_homework_answer(request, reply_text):
            return self._fallback_result(
                request,
                fallback_reason="learning_direct_answer_output",
                prompt_versions=prompt_versions,
                provider_name=model_response.provider_name,
                model_name=model_response.model_name,
                model_metadata=model_response.metadata,
                output_risk_level=output_safety.risk_level,
                turn_guidance_context=turn_guidance_context,
                age_policy=age_policy,
            )

        self._attach_healthy_engagement_metrics(
            model_response.metadata,
            request=request,
            turn_guidance_context=turn_guidance_context,
            age_policy=age_policy,
            reply_text=reply_text,
            reply_normalized=model_response.metadata.get("reply_normalized") is True,
        )
        return AgentRuntimeResult(
            reply_text=reply_text,
            source=AgentRuntimeSource.MODEL,
            provider_name=model_response.provider_name,
            model_name=model_response.model_name,
            prompt_versions=prompt_versions,
            model_metadata=model_response.metadata,
            output_risk_level=output_safety.risk_level,
        )

    def _fallback_result(
        self,
        request: AgentRuntimeRequest,
        *,
        fallback_reason: str,
        prompt_versions: dict[str, PromptVersion],
        provider_name: str | None = None,
        model_name: str | None = None,
        model_metadata: dict[str, Any] | None = None,
        output_risk_level: RiskLevel | None = None,
        turn_guidance_context: TurnGuidanceContext | None = None,
        age_policy: AgeBandReplyPolicy | None = None,
    ) -> AgentRuntimeResult:
        reply_text = request.route_decision.reply_text
        if self._requires_deterministic_self_harm_reply(request):
            reply_text = self.SELF_HARM_GUARDIAN_REPLY
            fallback_reason = "deterministic_self_harm_guardian"
        metadata = dict(model_metadata or {})
        self._attach_healthy_engagement_metrics(
            metadata,
            request=request,
            turn_guidance_context=turn_guidance_context
            or self._build_turn_guidance_context(request),
            age_policy=age_policy or derive_age_band_reply_policy(request.parent_policy),
            reply_text=reply_text,
            reply_normalized=metadata.get("reply_normalized") is True,
        )
        return AgentRuntimeResult(
            reply_text=reply_text,
            source=AgentRuntimeSource.FALLBACK,
            provider_name=provider_name,
            model_name=model_name,
            fallback_reason=fallback_reason,
            prompt_versions=prompt_versions,
            model_metadata=metadata,
            output_risk_level=output_risk_level,
        )

    def _build_turn_guidance_context(
        self,
        request: AgentRuntimeRequest,
    ) -> TurnGuidanceContext:
        return self._turn_guidance_builder.build(
            child_text=request.child_text,
            conversation_history=request.conversation_history,
        )

    def _model_context(
        self,
        request: AgentRuntimeRequest,
        turn_guidance_context: TurnGuidanceContext,
        age_policy: AgeBandReplyPolicy,
    ) -> dict[str, Any]:
        decision = request.route_decision
        return {
            "conversation": {
                "child_id": request.child_id,
                "session_id": request.session_id,
                "recent_history_turns": len(request.conversation_history),
                **request.conversation_metadata,
            },
            "time_context": request.time_context.model_dump(mode="json"),
            "parent_policy": self._dump_context_value(request.parent_policy),
            "memory_context": self._dump_context_value(request.memory_context),
            "turn_guidance": turn_guidance_context.model_dump(mode="json"),
            "age_policy": age_policy.model_dump(),
            "scene_route": {
                "base_scene": decision.base_scene.value,
                "active_scene": decision.active_scene.value,
                "transition": decision.transition.value,
                "reason": decision.reason,
                "sub_scene": decision.sub_scene,
                "risk_level": decision.risk_level.value,
                "requires_parent_attention": decision.requires_parent_attention,
                "needs_input": decision.needs_input,
                "quick_actions": [
                    self._action_to_context(action)
                    for action in decision.quick_actions
                ],
                "fallback_reply_text": decision.reply_text,
            },
        }

    def _model_metadata(
        self,
        request: AgentRuntimeRequest,
        prompt_versions: dict[str, PromptVersion],
        turn_guidance_context: TurnGuidanceContext,
        age_policy: AgeBandReplyPolicy,
    ) -> dict[str, Any]:
        return {
            "contains_child_data": True,
            "contains_image": bool(request.conversation_metadata.get("contains_image")),
            "contains_audio": False,
            "task_type": ModelTaskType.CHILD_CHAT.value,
            "active_scene": request.route_decision.active_scene.value,
            "reply_style": "voice_first_short_natural_one_question",
            "age_band": age_policy.age_band,
            "reply_char_budget": age_policy.reply_char_budget,
            "uses_recent_conversation_history": bool(request.conversation_history),
            "prompt_version_layers": sorted(prompt_versions.keys()),
            "turn_guidance_hints": list(turn_guidance_context.hints),
        }

    def _registry_fallback_reason(self, metadata: dict[str, Any]) -> str | None:
        if metadata.get("policy_blocked") is True:
            return "model_policy_blocked"
        if metadata.get("fallback_used") is True:
            return "model_registry_fallback"
        return None

    def _attach_healthy_engagement_metrics(
        self,
        metadata: dict[str, Any],
        *,
        request: AgentRuntimeRequest,
        turn_guidance_context: TurnGuidanceContext,
        age_policy: AgeBandReplyPolicy,
        reply_text: str,
        reply_normalized: bool,
    ) -> None:
        metadata["healthy_engagement"] = self._healthy_engagement_metrics(
            request=request,
            turn_guidance_context=turn_guidance_context,
            age_policy=age_policy,
            reply_text=reply_text,
            reply_normalized=reply_normalized,
        )

    def _healthy_engagement_metrics(
        self,
        *,
        request: AgentRuntimeRequest,
        turn_guidance_context: TurnGuidanceContext,
        age_policy: AgeBandReplyPolicy,
        reply_text: str,
        reply_normalized: bool,
    ) -> dict[str, Any]:
        question_count = self._question_count(reply_text)
        boundary_signal = turn_guidance_context.boundary_signal
        previous_topic_revived = self._revives_previous_topic(
            reply_text,
            turn_guidance_context,
        )
        boundary_respected = None
        if boundary_signal is not None:
            boundary_respected = question_count == 0 and not previous_topic_revived
        return {
            "turn_index": None,
            "recent_history_turns": len(request.conversation_history),
            "active_scene": request.route_decision.active_scene.value,
            "age_band": age_policy.age_band,
            "reply_char_count": len(reply_text),
            "question_count": question_count,
            "turn_guidance_hints": list(turn_guidance_context.hints),
            "boundary_signal": boundary_signal,
            "boundary_respected": boundary_respected,
            "previous_topic_revived": previous_topic_revived,
            "same_topic_score": turn_guidance_context.same_topic_score,
            "consecutive_recent_questions": (
                turn_guidance_context.consecutive_recent_questions
            ),
            "reply_normalized": reply_normalized,
            "first_text_ms": None,
            "first_audio_ms": None,
            "turn_total_ms": None,
        }

    def _question_count(self, text: str) -> int:
        return text.count("？") + text.count("?")

    def _revives_previous_topic(
        self,
        reply_text: str,
        turn_guidance_context: TurnGuidanceContext,
    ) -> bool:
        if turn_guidance_context.boundary_signal is None:
            return False
        recent_topic = turn_guidance_context.recent_topic
        if not recent_topic:
            return False
        normalized = reply_text.strip().lower().replace(" ", "")
        if any(marker in normalized for marker in ("不聊", "先不聊", "不说这个")):
            return False
        topic_markers = self._topic_markers(recent_topic)
        if not topic_markers or not any(marker in normalized for marker in topic_markers):
            return False
        revival_markers = (
            "继续",
            "接着",
            "再聊",
            "聊聊",
            "再说",
            "说说",
            "回到",
            "刚才",
            "还是",
        )
        return any(marker in normalized for marker in revival_markers)

    def _topic_markers(self, recent_topic: str) -> tuple[str, ...]:
        if recent_topic == "运动比赛/跑步":
            return ("运动", "比赛", "跑步", "跑")
        if recent_topic == "身体感受":
            return ("身体", "腿", "疼", "酸", "累", "喘")
        return ()

    def _looks_like_direct_homework_answer(
        self, request: AgentRuntimeRequest, reply_text: str
    ) -> bool:
        if request.route_decision.active_scene != SceneId.LEARNING_HOMEWORK_HELP:
            return False
        normalized = reply_text.strip().lower().replace(" ", "")
        direct_answer_markers = (
            "答案是",
            "最终答案",
            "直接答案",
            "所以答案",
            "结果是",
            "得数是",
        )
        if any(marker in normalized for marker in direct_answer_markers):
            return True
        math_answer_patterns = (
            r"\d+(?:\.\d+)?(?:\+|加|-|减|×|x|\*|乘|÷|/|除以)\d+(?:\.\d+)?(?:=|等于|是)\d+",
            r"(?:=|等于)\d+(?:\.\d+)?(?:。|！|!|$)",
        )
        return any(re.search(pattern, normalized) for pattern in math_answer_patterns)

    def _normalize_model_reply(
        self,
        reply_text: str,
        request: AgentRuntimeRequest,
        turn_guidance_context: TurnGuidanceContext,
        age_policy: AgeBandReplyPolicy,
    ) -> str:
        text = reply_text.strip()
        if not text:
            return ""

        text = self._strip_markdown_for_voice(text)
        text = self._strip_stage_directions(text)
        text = self._soften_topic_change_echo(request, text)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"([。！？!?])\s+", r"\1", text)
        if self._should_force_bedtime_close(request, text):
            return self.BEDTIME_CLOSE_REPLY
        if request.route_decision.active_scene != SceneId.SAFETY_GUARDIAN:
            if self._should_remove_question_hook(request, turn_guidance_context):
                text = self._remove_question_hook(text, request, turn_guidance_context)
            else:
                text = self._keep_one_main_question(text)
        return self._limit_to_sentence_boundary(
            text,
            max_chars=self._reply_max_chars(request.route_decision.active_scene, age_policy),
        )

    def _image_context_repair_reply(
        self,
        request: AgentRuntimeRequest,
        reply_text: str,
    ) -> str | None:
        image_context = request.conversation_metadata.get("image_context")
        if not isinstance(image_context, dict):
            if self._child_is_asking_to_share_image(request.child_text) and (
                not reply_text or self._looks_like_image_refusal(reply_text)
            ):
                return "可以的。请点“拍给小白狐看”拍照或选图，上传后我再跟你一起看。"
            return None
        if not self._looks_like_image_refusal(reply_text):
            return None

        recognized_type = str(image_context.get("recognized_type") or "")
        recognized_text = str(
            image_context.get("recognized_text")
            or image_context.get("text")
            or ""
        ).strip()
        summary = self._short_image_summary(recognized_text)
        if recognized_type == "homework_problem":
            if summary:
                return f"我看到这张图像是一道题，里面大概是：{summary}。我们先看题目在问什么。"
            return "我看到这张图像是一道题，但内容还不够清楚。你可以把题目读一小句给我听。"
        if recognized_type == "privacy_sensitive":
            return "这张图可能有隐私内容，我们先不展开细节。可以请爸爸妈妈一起看一下。"
        if summary:
            return f"我看到这张图里像是：{summary}。你最想让我看哪里？"
        return "图片已经传上来了，但这次识别不够清楚。你可以换一张更清楚的，或者告诉我你想让我看哪里。"

    def _looks_like_image_refusal(self, text: str) -> bool:
        compact = text.replace(" ", "")
        refusal_markers = (
            "看不到图片",
            "无法看到图片",
            "不能看到图片",
            "没办法看到图片",
            "没有看图功能",
            "不能看照片",
            "无法看照片",
            "看不到照片",
            "只能看到文字",
            "把图片里的内容说给我听",
        )
        if any(marker in compact for marker in refusal_markers):
            return True
        return any(
            re.search(pattern, compact)
            for pattern in (
                r"没办法看(?:到)?[^。！？!?]{0,8}图片",
                r"无法看(?:到)?[^。！？!?]{0,8}图片",
                r"不能看(?:到)?[^。！？!?]{0,8}图片",
                r"看不到[^。！？!?]{0,8}照片",
                r"没办法看(?:到)?[^。！？!?]{0,8}照片",
            )
        )

    def _child_is_asking_to_share_image(self, text: str) -> bool:
        compact = text.replace(" ", "")
        return any(
            marker in compact
            for marker in (
                "拍给你看",
                "拍照给你看",
                "给你看看",
                "发张图",
                "发照片",
                "看图片",
                "看照片",
            )
        )

    def _short_image_summary(self, text: str) -> str:
        cleaned = re.sub(r"\s+", " ", text).strip()
        cleaned = re.sub(r"^(图片描述|context_summary|child_summary)[：:]\s*", "", cleaned)
        if len(cleaned) <= 80:
            return cleaned
        boundary = max(cleaned.rfind(char, 0, 80) for char in ("。", "，", "；", "、", " "))
        if boundary >= 12:
            return cleaned[:boundary].strip("，。；、 ")
        return cleaned[:80].rstrip("，。；、 ")

    def _reply_max_chars(
        self,
        active_scene: SceneId,
        age_policy: AgeBandReplyPolicy,
    ) -> int:
        return min(self._scene_reply_max_chars(active_scene), age_policy.max_chars)

    def _scene_reply_max_chars(self, active_scene: SceneId) -> int:
        if active_scene == SceneId.OPEN_CONVERSATION:
            return 520
        if active_scene == SceneId.DAILY_AFTER_SCHOOL_CHECKIN:
            return 360
        if active_scene == SceneId.LEARNING_HOMEWORK_HELP:
            return 280
        if active_scene == SceneId.SAFETY_GUARDIAN:
            return 240
        if active_scene == SceneId.SAFETY_GENTLE_CHECKIN:
            return 260
        if active_scene == SceneId.PRIVACY_BOUNDARY:
            return 220
        if active_scene == SceneId.DAILY_BEDTIME_REFLECTION:
            return 220
        return 320

    def _strip_markdown_for_voice(self, text: str) -> str:
        text = re.sub(r"[\U00010000-\U0010ffff]", "", text)
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"(?m)^\s*(?:#{1,6}\s*)+", "", text)
        text = re.sub(r"(?m)^\s*(?:[-*•]|\d+[.)、]|[一二三四五六七八九十]+[、.])\s*", "", text)
        text = re.sub(r"[*_`#>|]+", "", text)
        text = re.sub(r"^\s*(?:小白狐|小狐狸|助手|AI|ai)\s*[：:]\s*", "", text)
        return text

    def _strip_stage_directions(self, text: str) -> str:
        previous = None
        cleaned = text
        while previous != cleaned:
            previous = cleaned
            cleaned = self._STAGE_DIRECTION_PATTERN.sub("", cleaned)
        cleaned = re.sub(
            r"(?:舞台说明|语气说明)\s*[：:].*?(?=[。！？!?]|$)",
            "",
            cleaned,
        )
        return cleaned.strip()

    def _soften_topic_change_echo(
        self,
        request: AgentRuntimeRequest,
        text: str,
    ) -> str:
        normalized = request.child_text.replace(" ", "")
        if not any(
            marker in normalized
            for marker in ("换个话题", "换一个话题", "聊点别的", "别聊这个")
        ):
            return text
        text = text.replace("我们换个话题", "我们换一个轻松的")
        text = text.replace("换个话题", "换一个轻松的")
        text = text.replace("换一个话题", "换一个轻松的")
        return text

    def _keep_one_main_question(self, text: str) -> str:
        question_positions = [
            position
            for position, char in enumerate(text)
            if char in {"?", "？"}
        ]
        if len(question_positions) <= 1:
            return text
        return text[: question_positions[0] + 1].strip()

    def _should_remove_question_hook(
        self,
        request: AgentRuntimeRequest,
        turn_guidance_context: TurnGuidanceContext,
    ) -> bool:
        if request.route_decision.active_scene != SceneId.OPEN_CONVERSATION:
            return False
        hints = set(turn_guidance_context.hints)
        return bool(
            hints
            & {
                "too_many_recent_questions",
                "child_requests_topic_change",
                "bedtime_close_requested",
                "child_correction",
            }
        )

    def _remove_question_hook(
        self,
        text: str,
        request: AgentRuntimeRequest,
        turn_guidance_context: TurnGuidanceContext,
    ) -> str:
        segments = re.findall(r"[^。！？!?]+[。！？!?]?", text)
        kept = [
            segment.strip()
            for segment in segments
            if segment.strip() and "？" not in segment and "?" not in segment
        ]
        if kept:
            return "".join(kept).strip()

        hints = set(turn_guidance_context.hints)
        if "bedtime_close_requested" in hints:
            return self.BEDTIME_CLOSE_REPLY
        if "child_correction" in hints:
            return "我可能听错了。我们先按你刚才说的来。"
        if "child_requests_topic_change" in hints:
            return "好，我们换一个轻松的。"
        return "我听见了。我们先顺着你刚才说的聊。"

    def _requires_deterministic_self_harm_reply(
        self,
        request: AgentRuntimeRequest,
    ) -> bool:
        if request.route_decision.active_scene != SceneId.SAFETY_GUARDIAN:
            return False
        signals = request.route_decision.signals or {}
        evidence = signals.get("safety_evidence")
        if isinstance(evidence, list) and "self_harm" in evidence:
            return True
        normalized = request.child_text.replace(" ", "")
        return request.route_decision.risk_level == RiskLevel.CRITICAL and any(
            marker in normalized
            for marker in ("不想活", "想死", "自杀", "伤害自己", "杀了自己")
        )

    def _should_force_bedtime_close(
        self,
        request: AgentRuntimeRequest,
        text: str,
    ) -> bool:
        normalized = request.child_text.replace(" ", "")
        bedtime_requested = any(
            marker in normalized
            for marker in ("明天再聊", "我要睡觉", "我得睡觉", "睡觉了", "晚安", "困了")
        )
        if not bedtime_requested and (
            request.route_decision.active_scene != SceneId.DAILY_BEDTIME_REFLECTION
        ):
            return False
        return (
            "？" in text
            or "?" in text
            or "明天" in text
            or "下次" in text
            or "再聊" in text
        )

    def _limit_to_sentence_boundary(self, text: str, *, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text

        segments = re.findall(r"[^。！？!?]+[。！？!?]?", text)
        selected: list[str] = []
        total = 0
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            if selected and total + len(segment) > max_chars:
                break
            if not selected and len(segment) > max_chars:
                suffix = "。" if max_chars > 1 else ""
                return segment[: max_chars - len(suffix)].rstrip("，,；;：: ") + suffix
            selected.append(segment)
            total += len(segment)
        if selected:
            return "".join(selected).strip()
        return text[:max_chars].rstrip("，,；;：: ") + "。"

    def _action_to_context(self, action: SceneAction) -> dict[str, str]:
        return {"id": action.id, "label": action.label}

    def _dump_context_value(self, value: Any) -> Any:
        if value is None:
            return None
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        if isinstance(value, list):
            return [self._dump_context_value(item) for item in value]
        if isinstance(value, dict):
            return {
                str(key): self._dump_context_value(item)
                for key, item in value.items()
            }
        return value


_child_agent_runtime = ChildAgentRuntime()


def get_child_agent_runtime() -> ChildAgentRuntime:
    return _child_agent_runtime
