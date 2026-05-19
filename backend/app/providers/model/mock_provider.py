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
        text = (
            fallback_reply_text
            if isinstance(fallback_reply_text, str) and fallback_reply_text.strip()
            else "我会先陪你把想法说清楚。我们一步一步来，不急着要答案。"
        )
        active_scene = scene_route.get("active_scene")
        return (
            text,
            {
                "reply": text,
                "scene_hint": active_scene or "daily.after_school_checkin",
                "requires_parent_attention": bool(
                    scene_route.get("requires_parent_attention", False)
                ),
                "mock_child_chat_strategy": (
                    "scene_fallback_text"
                    if isinstance(fallback_reply_text, str)
                    else "default_child_chat_text"
                ),
            },
        )

    def _intent_output(self, input_text: str) -> tuple[str, dict[str, Any]]:
        learning_keywords = ("题", "作业", "不会", "数学", "语文", "英语")
        intent = (
            "learning_help"
            if any(keyword in input_text for keyword in learning_keywords)
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
                "summary": "暂无需要父亲立即处理的事项。",
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
