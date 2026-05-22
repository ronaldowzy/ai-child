from collections.abc import Callable
from datetime import date, datetime, timezone
import logging

from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import hash_identifier
from app.domain.memory import MemoryItem, MemorySensitivity, MemoryType
from app.domain.parent_report import ParentReport
from app.repositories.conversation_persistence_repository import (
    ConversationPersistenceRepository,
    ConversationPersistenceRepositoryUnavailable,
    ConversationReportMessage,
)
from app.repositories.parent_report_repository import (
    InMemoryParentReportRepository,
    ParentReportRepository,
    ParentReportRepositoryProtocol,
    ParentReportRepositoryUnavailable,
)
from app.services.memory_service import MemoryService, get_memory_service


logger = logging.getLogger("app.parent_report")


class ParentReportService:
    """Builds parent-facing daily summaries from structured local signals."""

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
        repository: ParentReportRepositoryProtocol | None = None,
        conversation_repository: ConversationPersistenceRepository | None = None,
        fallback_repository: InMemoryParentReportRepository | None = None,
        now_provider: Callable[[], datetime] | None = None,
        fallback_to_memory: bool = True,
    ) -> None:
        self._memory_service = memory_service or get_memory_service()
        self._repository = repository or ParentReportRepository()
        self._fallback_repository = (
            fallback_repository or InMemoryParentReportRepository()
        )
        self._conversation_repository = (
            conversation_repository or ConversationPersistenceRepository()
        )
        self._fallback_to_memory = fallback_to_memory
        self._repository_available = True
        self._conversation_repository_available = True
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def get_daily_report(
        self,
        child_id: str,
        *,
        report_date: date | None = None,
    ) -> ParentReport:
        target_date = report_date or self._now().date()
        memories = self._daily_parent_visible_memories(child_id, target_date)
        conversation_messages = self._daily_conversation_messages(
            child_id,
            target_date,
        )
        existing = self._get_persisted_report(child_id, target_date)
        if existing is not None and not self._is_stale(
            existing,
            memories=memories,
            conversation_messages=conversation_messages,
        ):
            return existing
        report = self._generate_daily_report_from_materials(
            child_id=child_id,
            target_date=target_date,
            memories=memories,
            conversation_messages=conversation_messages,
        )
        return self._save_generated_report(report)

    def generate_daily_report(
        self,
        child_id: str,
        *,
        report_date: date | None = None,
    ) -> ParentReport:
        target_date = report_date or self._now().date()
        memories = self._daily_parent_visible_memories(child_id, target_date)
        conversation_messages = self._daily_conversation_messages(
            child_id,
            target_date,
        )
        return self._generate_daily_report_from_materials(
            child_id=child_id,
            target_date=target_date,
            memories=memories,
            conversation_messages=conversation_messages,
        )

    def _generate_daily_report_from_materials(
        self,
        *,
        child_id: str,
        target_date: date,
        memories: list[MemoryItem],
        conversation_messages: list[ConversationReportMessage],
    ) -> ParentReport:
        conversation = self._conversation_analysis(conversation_messages)

        learning = self._observations_for(memories, {MemoryType.LEARNING_PATTERN})
        expression = self._observations_for(
            memories,
            {MemoryType.EXPRESSION_PATTERN},
        )
        emotion = self._observations_for(memories, {MemoryType.EMOTION_OBSERVATION})
        learning.extend(conversation["learning_observations"])
        expression.extend(conversation["expression_observations"])
        emotion.extend(conversation["emotion_observations"])
        learning = self._dedupe_and_limit(learning, limit=5)
        expression = self._dedupe_and_limit(expression, limit=5)
        emotion = self._dedupe_and_limit(emotion, limit=5)

        safety_memories = self._safety_memories(memories)
        safety_alerts = self._safety_alerts(safety_memories)
        safety_alerts.extend(conversation["safety_alerts"])
        safety_alerts = self._dedupe_and_limit(safety_alerts, limit=5)
        actions = self._suggested_actions(
            memories=memories,
            has_learning=bool(learning),
            has_expression=bool(expression),
            has_emotion=bool(emotion),
            has_safety=bool(safety_alerts),
            conversation_topics=conversation["topics"],
        )

        return ParentReport(
            child_id=child_id,
            date=target_date,
            summary=self._summary(
                memories=memories,
                conversation_messages=conversation_messages,
                conversation_topics=conversation["topics"],
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

    def _get_persisted_report(
        self,
        child_id: str,
        report_date: date,
    ) -> ParentReport | None:
        if self._repository_available:
            try:
                return self._repository.get(child_id, report_date)
            except (ParentReportRepositoryUnavailable, SQLAlchemyError) as exc:
                self._log_repository_fallback(
                    child_id=child_id,
                    report_date=report_date,
                    operation="get",
                    error_type=exc.__class__.__name__,
                )
                if not self._fallback_to_memory:
                    raise
                self._repository_available = False
        return self._fallback_repository.get(child_id, report_date)

    def _save_generated_report(self, report: ParentReport) -> ParentReport:
        if self._repository_available:
            try:
                saved = self._repository.save(report)
                self._fallback_repository.save(saved)
                return saved
            except (ParentReportRepositoryUnavailable, SQLAlchemyError) as exc:
                self._log_repository_fallback(
                    child_id=report.child_id,
                    report_date=report.date,
                    operation="save",
                    error_type=exc.__class__.__name__,
                )
                if not self._fallback_to_memory:
                    raise
                self._repository_available = False
        return self._fallback_repository.save(report)

    def _log_repository_fallback(
        self,
        *,
        child_id: str,
        report_date: date,
        operation: str,
        error_type: str,
    ) -> None:
        logger.warning(
            "parent_report_repository_fallback",
            extra={
                "event": "parent_report_repository_fallback",
                "operation": operation,
                "child_id_hash": hash_identifier(child_id),
                "report_date": report_date.isoformat(),
                "error_type": error_type,
            },
        )

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

    def _daily_conversation_messages(
        self,
        child_id: str,
        report_date: date,
    ) -> list[ConversationReportMessage]:
        if not self._conversation_repository_available:
            return []
        try:
            return self._conversation_repository.list_report_messages(
                child_id=child_id,
                report_date=report_date,
            )
        except (ConversationPersistenceRepositoryUnavailable, SQLAlchemyError) as exc:
            self._log_conversation_fallback(
                child_id=child_id,
                report_date=report_date,
                error_type=exc.__class__.__name__,
            )
            self._conversation_repository_available = False
            return []

    def _log_conversation_fallback(
        self,
        *,
        child_id: str,
        report_date: date,
        error_type: str,
    ) -> None:
        logger.warning(
            "parent_report_conversation_fallback",
            extra={
                "event": "parent_report_conversation_fallback",
                "child_id_hash": hash_identifier(child_id),
                "report_date": report_date.isoformat(),
                "error_type": error_type,
            },
        )

    def _is_stale(
        self,
        report: ParentReport,
        *,
        memories: list[MemoryItem],
        conversation_messages: list[ConversationReportMessage],
    ) -> bool:
        latest = self._latest_material_time(
            memories=memories,
            conversation_messages=conversation_messages,
        )
        if latest is None:
            return False
        return latest > self._aware_datetime(report.created_at)

    def _latest_material_time(
        self,
        *,
        memories: list[MemoryItem],
        conversation_messages: list[ConversationReportMessage],
    ) -> datetime | None:
        timestamps: list[datetime] = [
            self._aware_datetime(memory.updated_at) for memory in memories
        ]
        timestamps.extend(
            self._aware_datetime(message.created_at)
            for message in conversation_messages
        )
        return max(timestamps, default=None)

    def _aware_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def _conversation_analysis(
        self,
        messages: list[ConversationReportMessage],
    ) -> dict[str, list[str]]:
        child_messages = [message for message in messages if message.actor == "child"]
        if not child_messages:
            return {
                "topics": [],
                "learning_observations": [],
                "expression_observations": [],
                "emotion_observations": [],
                "safety_alerts": [],
            }

        scenes = {message.active_scene or "" for message in child_messages}
        child_texts = [message.normalized_text or "" for message in child_messages]
        attachment_count = sum(message.attachments_count for message in child_messages)
        topics: list[str] = []
        learning_observations: list[str] = []
        expression_observations: list[str] = []
        emotion_observations: list[str] = []
        safety_alerts: list[str] = []

        if any(scene.startswith("learning.") for scene in scenes) or any(
            self._contains_any(text, ("作业", "题", "数学", "怎么做", "不会"))
            for text in child_texts
        ):
            topics.append("学习求助")
            learning_observations.append(
                "今天的对话里出现学习或题目相关内容，适合继续用复述题意、圈出已知条件、分步思考的方式陪伴。"
            )
        if attachment_count:
            topics.append("图片分享")
            expression_observations.append(
                "孩子今天用图片和小白狐互动，可以顺着图片内容请孩子讲一讲他想分享或想问的部分。"
            )
        if any(scene.startswith("privacy.") or scene.startswith("safety.") for scene in scenes):
            topics.append("安全或隐私边界")
            safety_alerts.append(
                "今天对话触发过安全或隐私边界。建议父亲平静确认是否只是误触发，必要时再做具体了解。"
            )
        if any(
            self._contains_any(
                text,
                ("难过", "害怕", "担心", "生气", "烦", "累", "困", "不想", "没听清"),
            )
            for text in child_texts
        ):
            topics.append("情绪表达")
            emotion_observations.append(
                "孩子今天表达过情绪或状态线索，适合先回应感受，再给出休息、陪伴或小步骤选择。"
            )
        if not topics:
            topics.append("日常聊天")

        avg_len = sum(len(text.strip()) for text in child_texts) / max(
            len(child_texts),
            1,
        )
        if avg_len <= 8:
            expression_observations.append(
                "孩子今天的表达偏短，父亲可以用二选一、三选一或让孩子先说一个关键词来降低开口压力。"
            )
        else:
            expression_observations.append(
                "孩子今天有连续表达内容，父亲可以围绕孩子主动提到的主题继续追问一个具体细节。"
            )

        return {
            "topics": self._dedupe_and_limit(topics, limit=6),
            "learning_observations": self._dedupe_and_limit(
                learning_observations,
                limit=3,
            ),
            "expression_observations": self._dedupe_and_limit(
                expression_observations,
                limit=4,
            ),
            "emotion_observations": self._dedupe_and_limit(
                emotion_observations,
                limit=3,
            ),
            "safety_alerts": self._dedupe_and_limit(safety_alerts, limit=3),
        }

    def _contains_any(self, text: str, markers: tuple[str, ...]) -> bool:
        normalized = text.strip().lower().replace(" ", "")
        return any(marker in normalized for marker in markers)

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
        conversation_topics: list[str] | None = None,
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
        if conversation_topics and "图片分享" in conversation_topics:
            actions.append(
                "如果孩子今天分享了图片，可以先问“你最想让我看哪里？”而不是直接判断这是题目或隐私。"
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
        conversation_messages: list[ConversationReportMessage],
        conversation_topics: list[str],
        has_learning: bool,
        has_expression: bool,
        has_emotion: bool,
        has_safety: bool,
    ) -> str:
        if not memories and not conversation_messages:
            return "今天暂无可汇总的结构化会话素材。建议保持轻量观察，不做额外判断。"
        if has_safety:
            return (
                f"今天记录了 {len(memories)} 条结构化观察和 {len(conversation_messages)} 条会话消息，其中包含需要父亲关注的安全信号或隐私边界。"
                "建议先完成安全确认，再进行学习或日常交流。"
            )

        focus: list[str] = []
        if has_learning:
            focus.append("学习支持")
        if has_expression:
            focus.append("表达方式")
        if has_emotion:
            focus.append("情绪状态")
        focus.extend(conversation_topics)
        if not focus:
            focus.append("日常兴趣和事件")
        focus = self._dedupe_and_limit(focus, limit=6)

        focus_text = "、".join(focus)
        return (
            f"今天记录了 {len(memories)} 条结构化观察和 {len(conversation_messages)} 条会话消息，重点集中在{focus_text}。"
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
