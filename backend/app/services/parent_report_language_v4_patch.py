"""Runtime attachment for ParentReportService narrative v4 wording.

The main ParentReportService is intentionally large and owns repository/model
plumbing. This patch only replaces high-sensitivity parent-facing language
methods with v4 copy; it does not change Android, providers, auth, image upload,
or database schema behavior.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.domain.memory import MemorySensitivity, MemoryType
from app.repositories.conversation_persistence_repository import ConversationReportMessage
from app.services.parent_report_language_v4 import (
    avoid_followup_v4,
    deterministic_narrative_v4,
    parent_report_system_prompt_v4,
    tonight_parent_bridge_v4,
)


def apply_parent_report_language_v4(parent_report_module: Any) -> None:
    service_cls = getattr(parent_report_module, "ParentReportService", None)
    if service_cls is None or getattr(service_cls, "_parent_report_language_v4_applied", False):
        return

    ParentReport = parent_report_module.ParentReport
    ParentReportGenerationStatus = parent_report_module.ParentReportGenerationStatus

    def _parent_report_system_prompt(self: Any) -> str:
        return parent_report_system_prompt_v4()

    def _deterministic_fallback_report(
        self: Any,
        *,
        child_id: str,
        target_date: date,
        memories: list[Any],
        conversation_messages: list[ConversationReportMessage],
        conversation: dict[str, list[str]],
        support_style: list[str] | None = None,
    ) -> Any:
        has_material = bool(memories or conversation_messages)
        topics = conversation.get("topics", [])
        safety_memories = self._safety_memories(memories)
        has_safety = bool(safety_memories) or bool(conversation.get("safety_alerts"))
        has_show_tell = any(
            self._memory_relationship_type(memory) == "show_and_tell_event"
            for memory in memories
        )
        has_unfinished = any(
            self._memory_relationship_type(memory) == "unfinished_thread"
            for memory in memories
        )
        child_texts = [
            message.normalized_text or ""
            for message in conversation_messages
            if message.actor == "child"
        ]
        has_topic_change = any(
            self._contains_any(
                text,
                ("换个话题", "聊点别的", "别聊这个", "不说了", "算了"),
            )
            for text in child_texts
        )
        has_sports_fatigue = any(
            self._has_sports_fatigue_expression(text) for text in child_texts
        )

        narrative = deterministic_narrative_v4(
            has_material=has_material,
            has_safety=has_safety,
            topics=topics,
            has_show_tell=has_show_tell,
            has_unfinished=has_unfinished,
        )
        tonight_parent_bridge = tonight_parent_bridge_v4(
            has_material=has_material,
            has_safety=has_safety,
            topics=topics,
        )
        avoid_followup = avoid_followup_v4(
            topics=topics,
            has_topic_change=has_topic_change,
            has_sports_fatigue=has_sports_fatigue,
            has_safety=has_safety,
        )

        return ParentReport(
            child_id=child_id,
            date=target_date,
            summary=narrative,
            topic_overview=[],
            conversation_summary=None,
            learning_observations=[],
            expression_observations=[],
            emotion_observations=[],
            safety_alerts=list(conversation.get("safety_alerts", [])),
            suggested_parent_actions=[],
            tonight_parent_bridge=tonight_parent_bridge,
            avoid_followup=avoid_followup,
            created_at=self._now(),
            generation_status=ParentReportGenerationStatus.DETERMINISTIC_FALLBACK,
            generated_by="deterministic_fallback",
            generation_error_code=None,
            material_fingerprint=self._material_fingerprint(
                memories=memories,
                conversation_messages=conversation_messages,
            ),
        )

    def _tonight_parent_bridge(
        self: Any,
        *,
        actions: list[str],
        topics: list[str],
        has_material: bool,
        has_safety: bool,
    ) -> str:
        return tonight_parent_bridge_v4(
            has_material=has_material,
            has_safety=has_safety,
            topics=topics,
        )

    def _avoid_followup(
        self: Any,
        *,
        topics: list[str],
        has_topic_change: bool,
        has_sports_fatigue: bool,
    ) -> list[str]:
        return avoid_followup_v4(
            topics=topics,
            has_topic_change=has_topic_change,
            has_sports_fatigue=has_sports_fatigue,
            has_safety="安全或隐私边界" in topics,
        )

    def _summary(
        self: Any,
        *,
        memories: list[Any],
        conversation_messages: list[ConversationReportMessage],
        conversation_topics: list[str],
        conversation_state: list[str],
        has_learning: bool,
        has_expression: bool,
        has_emotion: bool,
        has_safety: bool,
    ) -> str:
        has_show_tell = any(
            self._memory_relationship_type(memory) == "show_and_tell_event"
            for memory in memories
        )
        has_unfinished = any(
            self._memory_relationship_type(memory) == "unfinished_thread"
            for memory in memories
        )
        return deterministic_narrative_v4(
            has_material=bool(memories or conversation_messages),
            has_safety=has_safety,
            topics=conversation_topics,
            has_show_tell=has_show_tell,
            has_unfinished=has_unfinished,
        )

    def _relationship_parent_actions(
        self: Any,
        memories: list[Any],
        *,
        support_style: list[str] | None = None,
    ) -> list[str]:
        actions: list[str] = []
        if any(self._memory_relationship_type(memory) == "show_and_tell_event" for memory in memories):
            actions.append(
                "孩子今天有通过图片或作品来表达、展示的倾向；家长可以给一个现实里的分享机会，不需要追问具体是哪张图。"
            )
        if any(self._memory_relationship_type(memory) == "unfinished_thread" for memory in memories):
            actions.append(
                "孩子有自然收尾或转去做别的事的信号；家长可以尊重这个节奏，不把话题拉回 App。"
            )
        if any(self._memory_relationship_type(memory) == "topic_boundary" for memory in memories):
            actions.append(
                "孩子表达不想聊或想换题时，家长可以尊重停顿，给两个轻松选择，不把话题拉回旧问题。"
            )
        if not actions:
            actions.append("今晚可以轻轻问一件小事；孩子不想说也没关系。")
        return actions[:4]

    def _safe_bridge_text(self: Any, text: str) -> str | None:
        safe = self._safe_text(text)
        if not safe:
            return None
        forbidden = (
            "backend", "provider", "config", "debug", "模型配置", "后端",
            "逐字聊天记录", "那张图", "给小白狐看的是什么", "给小白狐看的东西",
            "条孩子消息", "条小白狐回复", "消息数量",
        )
        if self._contains_any(safe, forbidden):
            return None
        return safe[:260]

    def _safety_memories(self: Any, memories: list[Any]) -> list[Any]:
        return [
            memory
            for memory in memories
            if memory.memory_type == MemoryType.SAFETY
            or memory.requires_parent_attention
            or memory.sensitivity in {MemorySensitivity.HIGH, MemorySensitivity.CRITICAL}
        ]

    service_cls._parent_report_system_prompt = _parent_report_system_prompt
    service_cls._deterministic_fallback_report = _deterministic_fallback_report
    service_cls._tonight_parent_bridge = _tonight_parent_bridge
    service_cls._avoid_followup = _avoid_followup
    service_cls._summary = _summary
    service_cls._relationship_parent_actions = _relationship_parent_actions
    service_cls._safe_bridge_text = _safe_bridge_text
    service_cls._safety_memories = _safety_memories
    service_cls._parent_report_language_v4_applied = True
