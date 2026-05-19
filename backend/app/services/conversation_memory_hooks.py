from typing import Any

from app.domain.enums import IntentType, RiskCategory, RiskLevel
from app.domain.memory import (
    MemoryCreateRequest,
    MemoryEvidence,
    MemoryItem,
    MemorySensitivity,
    MemoryType,
)
from app.domain.scene import SceneId, SceneRouteDecision
from app.services.intent_classifier import IntentClassification
from app.services.memory_service import MemoryService, get_memory_service
from app.services.safety_engine import SafetyClassification


class ConversationMemoryHooks:
    """Rule-first memory hooks for conversation turns.

    v0.1 stores only structured summaries. Child text is intentionally not copied
    into memory content or evidence.
    """

    def __init__(self, *, memory_service: MemoryService | None = None) -> None:
        self._memory_service = memory_service or get_memory_service()

    def retrieve_context(
        self,
        *,
        child_id: str,
        current_text: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        memories = self._memory_service.retrieve(
            child_id,
            query=current_text,
            limit=limit,
            include_safety=False,
        )
        return [
            self._memory_to_runtime_context(memory)
            for memory in memories
            if memory.memory_type != MemoryType.SAFETY
        ]

    def record_turn(
        self,
        *,
        child_id: str,
        session_id: str,
        safety: SafetyClassification,
        intent: IntentClassification,
        route_decision: SceneRouteDecision,
    ) -> list[MemoryItem]:
        requests = self._memory_requests_for_turn(
            child_id=child_id,
            session_id=session_id,
            safety=safety,
            intent=intent,
            route_decision=route_decision,
        )
        return self._memory_service.create_many(requests)

    def _memory_requests_for_turn(
        self,
        *,
        child_id: str,
        session_id: str,
        safety: SafetyClassification,
        intent: IntentClassification,
        route_decision: SceneRouteDecision,
    ) -> list[MemoryCreateRequest]:
        requests: list[MemoryCreateRequest] = []

        if route_decision.active_scene == SceneId.LEARNING_HOMEWORK_HELP:
            requests.append(
                self._request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.LEARNING_PATTERN,
                    content="孩子本次遇到学习求助，系统引导其先说明题目在问什么。",
                    tags=["学习求助", "题", "题意复述", "第一步"],
                    quote_summary=(
                        "孩子表达有学习求助，系统引导先说明题目在问什么。"
                    ),
                    sensitivity=MemorySensitivity.MEDIUM,
                    confidence=0.84,
                    importance=0.66,
                    route_decision=route_decision,
                )
            )

        if (
            intent.sub_intent == "direct_answer_request"
            or route_decision.reason == "learning_direct_answer_request"
        ):
            requests.append(
                self._request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.LEARNING_PATTERN,
                    content=(
                        "孩子在学习求助中有直接要答案倾向，适合继续使用"
                        "“题意复述 + 第一步思考”的引导策略。"
                    ),
                    tags=["学习求助", "答案", "直接要答案", "题意复述", "第一步"],
                    quote_summary=(
                        "孩子在学习求助中请求直接答案，系统改为题意复述和第一步思考。"
                    ),
                    sensitivity=MemorySensitivity.MEDIUM,
                    confidence=0.88,
                    importance=0.74,
                    route_decision=route_decision,
                )
            )

        if self._should_record_low_energy_emotion(safety, intent, route_decision):
            requests.append(
                self._request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.EMOTION_OBSERVATION,
                    content=(
                        "孩子本次表达低能量或不想继续说话，适合先接住感受，"
                        "并提供安静一下或稍后再说的选择。"
                    ),
                    tags=["情绪观察", "不想说话", "低能量", "低压力"],
                    quote_summary=(
                        "孩子表达低能量状态，系统提供安静一下或稍后再说的选择。"
                    ),
                    sensitivity=MemorySensitivity.MEDIUM,
                    confidence=0.8,
                    importance=0.58,
                    route_decision=route_decision,
                )
            )

        if route_decision.active_scene == SceneId.SAFETY_GUARDIAN:
            requests.append(
                self._request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.SAFETY,
                    content=(
                        "本次会话出现需要父亲关注的安全信号，系统鼓励孩子告诉"
                        "父母或可信成人，并提醒不需要保守让自己不舒服的秘密。"
                    ),
                    tags=["安全提醒", "父亲关注", "可信成人"],
                    quote_summary=(
                        "会话出现高风险安全信号，系统鼓励孩子告诉父母或可信成人。"
                    ),
                    sensitivity=(
                        MemorySensitivity.CRITICAL
                        if safety.risk_level == RiskLevel.CRITICAL
                        else MemorySensitivity.HIGH
                    ),
                    confidence=0.94,
                    importance=0.94,
                    visible_to_parent=True,
                    requires_parent_attention=True,
                    route_decision=route_decision,
                )
            )

        if route_decision.active_scene == SceneId.SAFETY_GENTLE_CHECKIN:
            requests.append(
                self._request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.EMOTION_OBSERVATION,
                    content=(
                        "孩子本次提到学校同伴互动中有让他不舒服的情况，"
                        "系统温和鼓励告诉父母或老师。"
                    ),
                    tags=["watch_observation", "同学", "欺负", "老师", "情绪观察"],
                    quote_summary=(
                        "孩子提到同伴互动中有不舒服的情况，系统温和鼓励告诉父母或老师。"
                    ),
                    sensitivity=MemorySensitivity.MEDIUM,
                    confidence=0.82,
                    importance=0.68,
                    visible_to_parent=True,
                    requires_parent_attention=False,
                    route_decision=route_decision,
                )
            )

        if route_decision.active_scene == SceneId.PRIVACY_BOUNDARY:
            requests.append(
                self._request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.STRATEGY,
                    content=(
                        "系统本次提醒孩子不要分享家庭地址、电话、学校名字或照片，"
                        "涉及真实信息时先问父母。"
                    ),
                    tags=["隐私边界", "地址", "电话", "学校名字", "照片"],
                    quote_summary=(
                        "系统提醒孩子不要分享家庭地址、电话、学校名字或照片。"
                    ),
                    sensitivity=MemorySensitivity.MEDIUM,
                    confidence=0.86,
                    importance=0.62,
                    route_decision=route_decision,
                )
            )

        if (
            route_decision.active_scene == SceneId.DAILY_AFTER_SCHOOL_CHECKIN
            and intent.sub_intent == "arrival_checkin"
        ):
            requests.append(
                self._request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.EVENT,
                    content="孩子本次以放学到家开场，系统提供低压力选择式 check-in。",
                    tags=["放学后", "到家", "低压力"],
                    quote_summary="孩子以到家或放学开场，系统提供低压力选择式 check-in。",
                    sensitivity=MemorySensitivity.LOW,
                    confidence=0.72,
                    importance=0.36,
                    route_decision=route_decision,
                )
            )

        return requests

    def _request(
        self,
        *,
        child_id: str,
        session_id: str,
        memory_type: MemoryType,
        content: str,
        tags: list[str],
        quote_summary: str,
        sensitivity: MemorySensitivity,
        confidence: float,
        importance: float,
        route_decision: SceneRouteDecision,
        visible_to_parent: bool = True,
        requires_parent_attention: bool = False,
    ) -> MemoryCreateRequest:
        return MemoryCreateRequest(
            child_id=child_id,
            memory_type=memory_type,
            content=content,
            tags=tags,
            evidence=[
                MemoryEvidence(
                    source="conversation_summary",
                    session_id=session_id,
                    quote_summary=quote_summary,
                    metadata={
                        "active_scene": route_decision.active_scene.value,
                        "route_reason": route_decision.reason,
                        "risk_level": route_decision.risk_level.value,
                    },
                )
            ],
            confidence=confidence,
            importance=importance,
            sensitivity=sensitivity,
            visible_to_parent=visible_to_parent,
            visible_to_child=False,
            requires_parent_attention=requires_parent_attention,
        )

    def _should_record_low_energy_emotion(
        self,
        safety: SafetyClassification,
        intent: IntentClassification,
        route_decision: SceneRouteDecision,
    ) -> bool:
        if route_decision.active_scene == SceneId.SAFETY_GENTLE_CHECKIN:
            return False
        if intent.intent == IntentType.EMOTION_EXPRESSION:
            return True
        return (
            safety.risk_level == RiskLevel.LOW
            and RiskCategory.MENTAL_DISTRESS in safety.categories
        )

    def _memory_to_runtime_context(self, memory: MemoryItem) -> dict[str, Any]:
        return {
            "memory_type": memory.memory_type.value,
            "content": memory.content,
            "tags": memory.tags[:6],
            "confidence": round(memory.confidence, 2),
        }


_conversation_memory_hooks = ConversationMemoryHooks()


def get_conversation_memory_hooks() -> ConversationMemoryHooks:
    return _conversation_memory_hooks
