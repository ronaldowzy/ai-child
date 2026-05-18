from collections.abc import Callable
from datetime import date, datetime, timezone

from app.domain.memory import MemoryItem, MemorySensitivity, MemoryType
from app.domain.parent_report import ParentReport
from app.services.memory_service import MemoryService, get_memory_service


class ParentReportService:
    """Builds parent-facing daily summaries from structured memory only."""

    _FORBIDDEN_REPLACEMENTS = {
        "胆小": "需要更多安全感",
        "不合群": "在社交表达上需要更多低压力支持",
        "懒": "当前任务启动可能需要更清晰的小步骤",
        "不聪明": "当前题目理解可能需要更慢的分步引导",
        "内向是缺陷": "内向不是缺陷",
        "内向不好": "内向不是缺陷",
        "内向有问题": "内向不是缺陷",
    }

    def __init__(
        self,
        *,
        memory_service: MemoryService | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._memory_service = memory_service or get_memory_service()
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def get_daily_report(
        self,
        child_id: str,
        *,
        report_date: date | None = None,
    ) -> ParentReport:
        return self.generate_daily_report(child_id, report_date=report_date)

    def generate_daily_report(
        self,
        child_id: str,
        *,
        report_date: date | None = None,
    ) -> ParentReport:
        target_date = report_date or self._now().date()
        memories = self._daily_parent_visible_memories(child_id, target_date)

        learning = self._observations_for(memories, {MemoryType.LEARNING_PATTERN})
        expression = self._observations_for(
            memories,
            {MemoryType.EXPRESSION_PATTERN},
        )
        emotion = self._observations_for(memories, {MemoryType.EMOTION_OBSERVATION})
        safety_memories = self._safety_memories(memories)
        safety_alerts = self._safety_alerts(safety_memories)
        actions = self._suggested_actions(
            memories=memories,
            has_learning=bool(learning),
            has_expression=bool(expression),
            has_emotion=bool(emotion),
            has_safety=bool(safety_alerts),
        )

        return ParentReport(
            child_id=child_id,
            date=target_date,
            summary=self._summary(
                memories=memories,
                has_learning=bool(learning),
                has_expression=bool(expression),
                has_emotion=bool(emotion),
                has_safety=bool(safety_alerts),
            ),
            learning_observations=learning,
            expression_observations=expression,
            emotion_observations=emotion,
            safety_alerts=safety_alerts,
            suggested_parent_actions=actions,
            created_at=self._now(),
        )

    def _now(self) -> datetime:
        now = self._now_provider()
        if now.tzinfo is None:
            return now.replace(tzinfo=timezone.utc)
        return now

    def _daily_parent_visible_memories(
        self,
        child_id: str,
        report_date: date,
    ) -> list[MemoryItem]:
        memories = self._memory_service.list_memories(
            child_id,
            active_only=True,
            include_safety=True,
        )
        return [
            memory
            for memory in memories
            if memory.visible_to_parent and memory.created_at.date() == report_date
        ]

    def _observations_for(
        self,
        memories: list[MemoryItem],
        memory_types: set[MemoryType],
    ) -> list[str]:
        observations = [
            self._safe_text(memory.content)
            for memory in memories
            if memory.memory_type in memory_types
        ]
        return self._dedupe_and_limit(observations, limit=5)

    def _safety_memories(self, memories: list[MemoryItem]) -> list[MemoryItem]:
        return [
            memory
            for memory in memories
            if memory.memory_type == MemoryType.SAFETY
            or memory.requires_parent_attention
            or memory.sensitivity in {MemorySensitivity.HIGH, MemorySensitivity.CRITICAL}
        ]

    def _safety_alerts(self, memories: list[MemoryItem]) -> list[str]:
        if not memories:
            return []
        alerts = [
            "今天出现需要父亲关注的安全信号。请用平静语气确认孩子是否遇到让他不舒服、要求保密或涉及陌生人的情况。"
        ]
        for memory in memories:
            content = self._safe_text(memory.content)
            if content and content not in alerts:
                alerts.append(content)
        return self._dedupe_and_limit(alerts, limit=5)

    def _suggested_actions(
        self,
        *,
        memories: list[MemoryItem],
        has_learning: bool,
        has_expression: bool,
        has_emotion: bool,
        has_safety: bool,
    ) -> list[str]:
        actions: list[str] = []
        if has_safety:
            actions.append(
                "今晚先做安全确认：单独、平静地问孩子有没有人让他保密或让他不舒服；必要时联系老师或其他可信成人。"
            )
        if has_learning:
            actions.append(
                "遇到作业问题时，请孩子先复述题目在问什么，再一起圈出已知条件，不直接给最终答案。"
            )
        if has_expression:
            actions.append(
                "开场先给二选一或三选一，例如“今天想说开心的事、难的事，还是想安静一会儿？”"
            )
        if has_emotion:
            actions.append(
                "如果孩子表达低落或紧张，先回应感受，再问他想休息、被陪一会儿，还是一起想一个小办法。"
            )

        strategy_memories = [
            memory for memory in memories if memory.memory_type == MemoryType.STRATEGY
        ]
        if strategy_memories:
            actions.append(self._safe_text(strategy_memories[0].content))

        if not actions:
            actions.append(
                "今晚用一个具体问题轻轻收尾，例如“今天有没有一件还不错的小事？”不要追问过多。"
            )
        return self._dedupe_and_limit(actions, limit=6)

    def _summary(
        self,
        *,
        memories: list[MemoryItem],
        has_learning: bool,
        has_expression: bool,
        has_emotion: bool,
        has_safety: bool,
    ) -> str:
        if not memories:
            return "今天暂无可汇总的结构化会话素材。建议保持轻量观察，不做额外判断。"
        if has_safety:
            return (
                f"今天记录了 {len(memories)} 条结构化观察，其中包含需要父亲关注的安全信号。"
                "建议先完成安全确认，再进行学习或日常交流。"
            )

        focus: list[str] = []
        if has_learning:
            focus.append("学习支持")
        if has_expression:
            focus.append("表达方式")
        if has_emotion:
            focus.append("情绪状态")
        if not focus:
            focus.append("日常兴趣和事件")

        focus_text = "、".join(focus)
        return (
            f"今天记录了 {len(memories)} 条结构化观察，重点集中在{focus_text}。"
            "整体适合用低压力提问和具体小步骤支持孩子。"
        )

    def _safe_text(self, text: str) -> str:
        safe = " ".join(text.strip().split())
        for forbidden, replacement in self._FORBIDDEN_REPLACEMENTS.items():
            safe = safe.replace(forbidden, replacement)
        return safe[:220]

    def _dedupe_and_limit(self, values: list[str], *, limit: int) -> list[str]:
        result: list[str] = []
        for value in values:
            clean_value = value.strip()
            if clean_value and clean_value not in result:
                result.append(clean_value)
            if len(result) >= limit:
                break
        return result


_parent_report_service = ParentReportService()


def get_parent_report_service() -> ParentReportService:
    return _parent_report_service
