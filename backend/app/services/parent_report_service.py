from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
import json
import logging

from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import hash_identifier
from app.domain.memory import MemoryItem, MemorySensitivity, MemoryType
from app.domain.model_types import ModelMessage, ModelRequest, ModelResponse, ModelTaskType
from app.domain.parent_report import (
    ParentReport,
    ParentReportGenerationStatus,
    ParentReportTopicOverview,
)
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
from app.services.model_registry import ModelRegistry, get_model_registry
from app.services.relationship_memory import (
    INTEREST_SEED,
    PROUD_MOMENT,
    TOPIC_BOUNDARY,
    memory_relationship_next_hook,
    memory_relationship_topic,
    relationship_memories,
)


logger = logging.getLogger("app.parent_report")


@dataclass(frozen=True)
class _ModelDailyReportResult:
    report: ParentReport | None
    error_code: str | None


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
        model_registry: ModelRegistry | None = None,
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
        self._model_registry = model_registry or get_model_registry()
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
        if report.generation_status == ParentReportGenerationStatus.MODEL_GENERATED:
            return self._save_generated_report(report)
        return report

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
        fallback_report = self._deterministic_fallback_report(
            child_id=child_id,
            target_date=target_date,
            memories=memories,
            conversation_messages=conversation_messages,
            conversation=conversation,
        )
        material_fingerprint = self._material_fingerprint(
            memories=memories,
            conversation_messages=conversation_messages,
        )
        model_result = self._model_daily_report(
            child_id=child_id,
            target_date=target_date,
            memories=memories,
            conversation_messages=conversation_messages,
            conversation=conversation,
            fallback_report=fallback_report,
            material_fingerprint=material_fingerprint,
        )
        if model_result.report is not None:
            return model_result.report
        return self._failed_report(
            child_id=child_id,
            target_date=target_date,
            error_code=model_result.error_code or "model_unavailable",
            material_fingerprint=material_fingerprint,
        )

    def _deterministic_fallback_report(
        self,
        *,
        child_id: str,
        target_date: date,
        memories: list[MemoryItem],
        conversation_messages: list[ConversationReportMessage],
        conversation: dict[str, list[str]],
    ) -> ParentReport:

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
        tonight_parent_bridge = self._tonight_parent_bridge(
            actions=actions,
            topics=conversation["topics"],
            has_material=bool(memories or conversation_messages),
            has_safety=bool(safety_alerts),
        )

        return ParentReport(
            child_id=child_id,
            date=target_date,
            summary=self._summary(
                memories=memories,
                conversation_messages=conversation_messages,
                conversation_topics=conversation["topics"],
                conversation_state=conversation["state_summary"],
                has_learning=bool(learning),
                has_expression=bool(expression),
                has_emotion=bool(emotion),
                has_safety=bool(safety_alerts),
            ),
            topic_overview=conversation.get("topic_overview", []),
            conversation_summary=conversation.get("conversation_summary", [None])[0]
            if conversation.get("conversation_summary")
            else None,
            learning_observations=learning,
            expression_observations=expression,
            emotion_observations=emotion,
            safety_alerts=safety_alerts,
            suggested_parent_actions=actions,
            tonight_parent_bridge=tonight_parent_bridge,
            avoid_followup=conversation.get(
                "avoid_followup",
                ["不要追问孩子今天在小白狐里聊了什么。"],
            ),
            created_at=self._now(),
            generation_status=ParentReportGenerationStatus.DETERMINISTIC_FALLBACK,
            generated_by="deterministic_fallback",
            generation_error_code=None,
            material_fingerprint=self._material_fingerprint(
                memories=memories,
                conversation_messages=conversation_messages,
            ),
        )

    def _model_daily_report(
        self,
        *,
        child_id: str,
        target_date: date,
        memories: list[MemoryItem],
        conversation_messages: list[ConversationReportMessage],
        conversation: dict[str, list[str]],
        fallback_report: ParentReport,
        material_fingerprint: str,
    ) -> _ModelDailyReportResult:
        try:
            response = self._request_model_report(
                child_id=child_id,
                target_date=target_date,
                memories=memories,
                conversation_messages=conversation_messages,
                conversation=conversation,
                fallback_report=fallback_report,
                retry=False,
            )
        except Exception as exc:  # noqa: BLE001 - report generation must not block.
            error_type = exc.__class__.__name__
            self._log_model_fallback(
                child_id=child_id,
                report_date=target_date,
                error_type=error_type,
            )
            return _ModelDailyReportResult(report=None, error_code=error_type)

        blocked_error = self._model_response_blocked_error(response)
        if blocked_error is not None:
            self._log_model_fallback(
                child_id=child_id,
                report_date=target_date,
                error_type=blocked_error,
            )
            return _ModelDailyReportResult(report=None, error_code=blocked_error)
        parsed = self._parse_model_report(
            response.structured_output.get("daily_report")
            or response.structured_output.get("text")
            or response.response_text,
        )
        if parsed is None:
            try:
                retry_response = self._request_model_report(
                    child_id=child_id,
                    target_date=target_date,
                    memories=memories,
                    conversation_messages=conversation_messages,
                    conversation=conversation,
                    fallback_report=fallback_report,
                    retry=True,
                )
            except Exception as exc:  # noqa: BLE001 - report fallback must hold.
                error_type = exc.__class__.__name__
                self._log_model_fallback(
                    child_id=child_id,
                    report_date=target_date,
                    error_type=error_type,
                )
                return _ModelDailyReportResult(report=None, error_code=error_type)
            blocked_error = self._model_response_blocked_error(retry_response)
            if blocked_error is not None:
                self._log_model_fallback(
                    child_id=child_id,
                    report_date=target_date,
                    error_type=blocked_error,
                )
                return _ModelDailyReportResult(report=None, error_code=blocked_error)
            parsed = self._parse_model_report(
                retry_response.structured_output.get("daily_report")
                or retry_response.structured_output.get("text")
                or retry_response.response_text,
            )
        if parsed is None:
            self._log_model_fallback(
                child_id=child_id,
                report_date=target_date,
                error_type="empty_or_unparseable_model_report",
            )
            return _ModelDailyReportResult(
                report=None,
                error_code="empty_or_unparseable_model_report",
            )
        return _ModelDailyReportResult(
            report=ParentReport(
                child_id=child_id,
                date=target_date,
                summary=parsed["summary"],
                topic_overview=parsed["topic_overview"]
                or fallback_report.topic_overview,
                conversation_summary=parsed["conversation_summary"]
                or fallback_report.conversation_summary,
                learning_observations=parsed["learning_observations"],
                expression_observations=parsed["expression_observations"],
                emotion_observations=parsed["emotion_observations"],
                safety_alerts=parsed["safety_alerts"],
                suggested_parent_actions=parsed["suggested_parent_actions"],
                tonight_parent_bridge=parsed["tonight_parent_bridge"]
                or self._tonight_parent_bridge(
                    actions=parsed["suggested_parent_actions"],
                    topics=conversation["topics"],
                    has_material=bool(memories or conversation_messages),
                    has_safety=bool(parsed["safety_alerts"]),
                ),
                avoid_followup=parsed["avoid_followup"]
                or fallback_report.avoid_followup,
                created_at=self._now(),
                generation_status=ParentReportGenerationStatus.MODEL_GENERATED,
                generated_by="model",
                generation_error_code=None,
                material_fingerprint=material_fingerprint,
            ),
            error_code=None,
        )

    def _model_response_blocked_error(self, response: ModelResponse) -> str | None:
        if response.metadata.get("policy_blocked"):
            return "policy_blocked"
        if response.metadata.get("fallback_used"):
            return str(response.metadata.get("failure_type") or "provider_fallback")
        if response.metadata.get("mock") or response.provider_name == "mock":
            return "mock_provider_not_formal_report"
        return None

    def _failed_report(
        self,
        *,
        child_id: str,
        target_date: date,
        error_code: str,
        material_fingerprint: str,
    ) -> ParentReport:
        status = (
            ParentReportGenerationStatus.MODEL_BLOCKED
            if "policy" in error_code.lower() or "blocked" in error_code.lower()
            else ParentReportGenerationStatus.MODEL_FAILED
        )
        return ParentReport(
            child_id=child_id,
            date=target_date,
            summary="日报暂时生成失败，请稍后重试。",
            topic_overview=[],
            conversation_summary=None,
            learning_observations=[],
            expression_observations=[],
            emotion_observations=[],
            safety_alerts=[],
            suggested_parent_actions=["请稍后重试生成父亲日报；不要把当前失败状态当作孩子当天表现。"],
            tonight_parent_bridge=(
                "今天的小结还没准备好。今晚先轻松陪孩子做一件日常小事，"
                "不要追问孩子在小白狐里聊了什么。"
            ),
            avoid_followup=["不要把日报生成失败当作孩子当天表现。"],
            created_at=self._now(),
            generation_status=status,
            generated_by="model",
            generation_error_code=error_code,
            material_fingerprint=material_fingerprint,
        )

    def _request_model_report(
        self,
        *,
        child_id: str,
        target_date: date,
        memories: list[MemoryItem],
        conversation_messages: list[ConversationReportMessage],
        conversation: dict[str, list[str]],
        fallback_report: ParentReport,
        retry: bool,
    ):
        payload = self._parent_report_model_payload(
            target_date=target_date,
            memories=memories,
            conversation_messages=conversation_messages,
            conversation=conversation,
            fallback_report=fallback_report,
        )
        user_prefix = (
            "上一次输出为空或不可解析。请只返回严格 JSON object，不要解释。\n"
            if retry
            else ""
        )
        return self._model_registry.generate(
            ModelRequest(
                task_type=ModelTaskType.PARENT_REPORT,
                messages=[
                    ModelMessage(
                        role="system",
                        content=self._parent_report_system_prompt(),
                    ),
                    ModelMessage(
                        role="user",
                        content=user_prefix
                        + json.dumps(payload, ensure_ascii=False),
                    ),
                ],
                context={"conversation": {"child_id": child_id}},
                metadata={
                    "contains_child_data": True,
                    "report_date": target_date.isoformat(),
                    "parent_report_retry": retry,
                    "material_counts": {
                        "memories": len(memories),
                        "conversation_messages": len(conversation_messages),
                    },
                },
            )
        )

    def _parent_report_system_prompt(self) -> str:
        return (
            "你是小白狐项目的父亲日报分析器。请只基于当天受控素材生成父亲可读的中文日报，"
            "不要编造素材里没有的事实。重点回答：孩子今天实际关注了什么、内容主线是什么、"
            "表达状态怎样、有没有学习、情绪或安全线索、父亲今晚应该怎么跟进。不要输出逐字聊天记录，"
            "不要输出图片识别报告，不要输出 prompt、debug、provider 信息，不要给孩子贴固定负面标签。"
            "必须输出非空、可解析的严格 JSON object；不要返回空字符串、none、null、Markdown 或解释文字。"
            "suggested_parent_actions 每条建议都应包含 starter + avoid 语义：可以怎么轻轻开口，以及避免怎么追问。"
            "tonight_parent_bridge 必须是一句现实可执行的父亲接话或动作，不要像监控报告，"
            "孩子不想说时要提醒不追问或换轻松方式。"
            "topic_overview 要归纳为父亲看得懂的话题卡片，不引用孩子原话；avoid_followup 写清今晚不要追问什么。"
            "返回严格 JSON，字段为 summary、topic_overview、conversation_summary、learning_observations、"
            "expression_observations、emotion_observations、safety_alerts、suggested_parent_actions、"
            "tonight_parent_bridge、avoid_followup。"
        )

    def _parent_report_model_payload(
        self,
        *,
        target_date: date,
        memories: list[MemoryItem],
        conversation_messages: list[ConversationReportMessage],
        conversation: dict[str, list[str]],
        fallback_report: ParentReport,
    ) -> dict[str, object]:
        return {
            "report_date": target_date.isoformat(),
            "material_policy": (
                "conversation_snippets are capped analysis snippets; do not quote them verbatim."
            ),
            "topic_hints": conversation["topics"],
            "topic_overview_hints": [
                item.model_dump(mode="json")
                for item in conversation["topic_overview"]
            ],
            "state_hints": conversation["state_summary"],
            "conversation_summary_hint": conversation["conversation_summary"][0]
            if conversation["conversation_summary"]
            else "",
            "avoid_followup_hints": conversation["avoid_followup"],
            "memory_summaries": [
                {
                    "type": memory.memory_type.value,
                    "content": self._safe_text(memory.content),
                    "tags": [self._safe_text(tag) for tag in memory.tags[:5]],
                    "requires_parent_attention": memory.requires_parent_attention,
                    "relationship": self._relationship_memory_payload(memory),
                }
                for memory in memories[:12]
            ],
            "conversation_snippets": [
                self._conversation_snippet(message)
                for message in conversation_messages[:24]
            ],
            "report_schema": {
                "summary": "非空中文字符串，必须由当天素材归纳，不要逐字引用。",
                "topic_overview": (
                    "list[object]，每项字段 topic、child_intent、summary、emotion_tone、"
                    "parent_bridge；只做归纳，不引用孩子原文。"
                ),
                "conversation_summary": (
                    "非空中文字符串，说明今天聊了什么和内容主线，不输出逐字记录。"
                ),
                "learning_observations": "list[str]",
                "expression_observations": "list[str]",
                "emotion_observations": "list[str]",
                "safety_alerts": "list[str]",
                "suggested_parent_actions": "list[str]，每条包含 starter + avoid 语义",
                "tonight_parent_bridge": (
                    "非空中文字符串。父亲今晚可以自然接的一句话或一个动作；"
                    "不要逐字引用敏感内容，不要追问，孩子不想说时换轻松方式。"
                ),
                "avoid_followup": "list[str]，今晚避免追问、纠错、监控式盘问的点。",
            },
            "deterministic_fallback_hints": {
                "topics": conversation["topics"],
                "topic_overview": [
                    item.model_dump(mode="json")
                    for item in fallback_report.topic_overview
                ],
                "conversation_summary": fallback_report.conversation_summary,
                "avoid_followup": fallback_report.avoid_followup,
                "state_summary": conversation["state_summary"],
                "tonight_parent_bridge": fallback_report.tonight_parent_bridge,
                "relationship_parent_actions": [
                    action
                    for action in fallback_report.suggested_parent_actions
                    if "今晚可以轻轻问" in action
                    or "孩子表达不想聊" in action
                    or "孩子今天有表达展开" in action
                ][:4],
            },
        }

    def _conversation_snippet(
        self,
        message: ConversationReportMessage,
    ) -> dict[str, object]:
        return {
            "actor": message.actor,
            "message_type": message.message_type,
            "scene": message.active_scene,
            "risk_level": message.risk_level,
            "has_attachment": message.attachments_count > 0,
            "text_summary": self._safe_text(message.normalized_text or "")[:120],
        }

    def _parse_model_report(self, value: object) -> dict[str, object] | None:
        raw: object = value
        if isinstance(value, str):
            stripped = self._strip_json_fence(value)
            try:
                raw = json.loads(stripped)
            except json.JSONDecodeError:
                return None
        if not isinstance(raw, dict):
            return None

        summary = self._safe_text(str(raw.get("summary") or ""))
        if not summary:
            return None
        return {
            "summary": summary[:500],
            "topic_overview": self._model_topic_overview(raw),
            "conversation_summary": self._safe_text(
                str(raw.get("conversation_summary") or ""),
            )[:600]
            or None,
            "learning_observations": self._model_list(raw, "learning_observations"),
            "expression_observations": self._model_list(raw, "expression_observations"),
            "emotion_observations": self._model_list(raw, "emotion_observations"),
            "safety_alerts": self._model_list(raw, "safety_alerts"),
            "suggested_parent_actions": self._model_list(
                raw,
                "suggested_parent_actions",
            ),
            "tonight_parent_bridge": self._safe_bridge_text(
                str(raw.get("tonight_parent_bridge") or ""),
            ),
            "avoid_followup": self._model_list(raw, "avoid_followup"),
        }

    def _strip_json_fence(self, value: str) -> str:
        stripped = value.strip()
        if not stripped.startswith("```"):
            return stripped
        stripped = stripped.strip("`").strip()
        if stripped.startswith("json"):
            return stripped[4:].strip()
        return stripped

    def _model_list(self, raw: dict[str, object], key: str) -> list[str]:
        value = raw.get(key)
        if not isinstance(value, list):
            return []
        return self._dedupe_and_limit(
            [self._safe_text(str(item)) for item in value],
            limit=6,
        )

    def _model_topic_overview(
        self,
        raw: dict[str, object],
    ) -> list[ParentReportTopicOverview]:
        value = raw.get("topic_overview")
        if not isinstance(value, list):
            return []
        items: list[ParentReportTopicOverview] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            topic = self._safe_text(str(item.get("topic") or ""))
            if not topic:
                continue
            items.append(
                ParentReportTopicOverview(
                    topic=topic[:120],
                    child_intent=self._safe_text(
                        str(item.get("child_intent") or ""),
                    )[:180],
                    summary=self._safe_text(str(item.get("summary") or ""))[:260],
                    emotion_tone=self._safe_text(
                        str(item.get("emotion_tone") or ""),
                    )[:120],
                    parent_bridge=self._safe_bridge_text(
                        str(item.get("parent_bridge") or ""),
                    )
                    or "",
                )
            )
        return items[:6]

    def _log_model_fallback(
        self,
        *,
        child_id: str,
        report_date: date,
        error_type: str,
    ) -> None:
        logger.warning(
            "parent_report_model_fallback",
            extra={
                "event": "parent_report_model_fallback",
                "child_id_hash": hash_identifier(child_id),
                "report_date": report_date.isoformat(),
                "error_type": error_type,
            },
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
                self._repository.save(report)
                self._fallback_repository.save(report)
                return report
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
        if report.generation_status != ParentReportGenerationStatus.MODEL_GENERATED:
            return True
        if not report.topic_overview or not report.conversation_summary:
            return True
        material_fingerprint = self._material_fingerprint(
            memories=memories,
            conversation_messages=conversation_messages,
        )
        if report.material_fingerprint != material_fingerprint:
            return True
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
                "topic_overview": [],
                "conversation_summary": [],
                "avoid_followup": ["不要追问孩子今天在小白狐里聊了什么。"],
                "state_summary": [],
                "learning_observations": [],
                "expression_observations": [],
                "emotion_observations": [],
                "safety_alerts": [],
            }

        scenes = {message.active_scene or "" for message in child_messages}
        child_texts = [message.normalized_text or "" for message in child_messages]
        all_texts = [message.normalized_text or "" for message in messages]
        attachment_count = sum(message.attachments_count for message in child_messages)
        child_turn_count = len(child_messages)
        agent_turn_count = len([message for message in messages if message.actor == "agent"])
        image_question_count = sum(
            1
            for text in child_texts
            if self._contains_any(text, ("图片", "照片", "拍", "看", "这是什么"))
        )
        topics: list[str] = []
        state_summary: list[str] = []
        learning_observations: list[str] = []
        expression_observations: list[str] = []
        emotion_observations: list[str] = []
        safety_alerts: list[str] = []

        has_learning_topic = any(
            scene.startswith("learning.") for scene in scenes
        ) or any(self._is_learning_help_text(text) for text in child_texts)
        has_sports_topic = any(self._is_sports_text(text) for text in child_texts)
        has_game_topic = any(self._is_game_text(text) for text in child_texts)
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

        if has_learning_topic:
            topics.append("学习求助")
            learning_observations.append(
                "今天出现学习或题目线索，先确认孩子是在分享图片还是在问题目；如果是在问题，继续用复述题意、圈出已知条件、分步思考的方式陪伴。"
            )
        if has_sports_topic:
            topics.append("运动比赛/跑步")
            expression_observations.append(
                "孩子今天围绕运动比赛、跑步或速度感受连续表达，说明他能把一个主动话题延展开；父亲可以轻轻问比赛项目或他最在意的一个细节。"
            )
        if has_game_topic:
            topics.append("游戏/CS")
            expression_observations.append(
                "孩子今天围绕游戏、地图、队友或规则表达兴趣；父亲可以把它当作普通兴趣入口，不把游戏话题变成盘问或限制谈判。"
            )
        if attachment_count:
            topics.append("图片分享")
            expression_observations.append(
                "孩子今天把图片作为表达入口；更像是在把看到的东西交给小白狐一起看，父亲可以先问“你最想让我看哪里？”再判断是否需要进入学习帮助。"
            )
        elif image_question_count:
            topics.append("看图交流")
            expression_observations.append(
                "孩子今天围绕图片或“这是什么”发起交流；适合让孩子先补充一个画面细节，再陪他一起判断。"
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
            for text in all_texts
        ):
            topics.append("情绪表达")
            emotion_observations.append(
                "今天出现过情绪、疲惫或“没听清”一类状态线索；父亲可以先确认孩子是不是累了、被打断了，或只是想重说一遍。"
            )
        if has_sports_fatigue:
            emotion_observations.append(
                "孩子在跑步、运动或比赛语境下用了“要死了、累死了、快不行了”一类夸张疲惫表达；更适合先确认跑后身体感受，不应直接当作高危心理信号。"
            )
        if has_topic_change:
            expression_observations.append(
                "孩子明确表达过想换个话题，这是主动表达边界和转场需求；后续不要把同一话题追问太久。"
            )
            state_summary.append("孩子会主动提出换话题，适合尊重转场并给两个轻松选择。")
        if not topics:
            topics.append("日常聊天")

        avg_len = sum(len(text.strip()) for text in child_texts) / max(
            len(child_texts),
            1,
        )
        if avg_len <= 8:
            expression_observations.append(
                "孩子今天更多使用短句或指令式表达；父亲可以用二选一、三选一或让孩子先说一个关键词来降低开口压力。"
            )
            state_summary.append("孩子今天更多是短句或指令式表达，需要更具体、低压力的追问来展开。")
        else:
            expression_observations.append(
                "孩子今天整体能连续表达；父亲可以围绕孩子主动提到的主题轻轻接一个具体细节，不要连续追问。"
            )
            state_summary.append("孩子今天能持续表达自己的关注点，适合围绕他主动发起的话题轻轻延展。")
        if attachment_count:
            state_summary.append("孩子今天明显在使用图片作为表达入口，不要默认当成作业或隐私问题。")
        if has_sports_topic:
            state_summary.append("孩子今天的主线更接近运动比赛和跑步体验，不应误判为学习求助。")
        if agent_turn_count and child_turn_count:
            state_summary.append(
                "当天有孩子和小白狐的互动摘要，可作为今晚低压力沟通的参考。"
            )

        deduped_topics = self._dedupe_and_limit(topics, limit=6)
        deduped_state = self._dedupe_and_limit(state_summary, limit=3)
        return {
            "topics": deduped_topics,
            "topic_overview": self._topic_overview_for_conversation(
                topics=deduped_topics,
                has_learning=has_learning_topic,
                has_sports=has_sports_topic,
                has_game=has_game_topic,
                has_topic_change=has_topic_change,
                has_sports_fatigue=has_sports_fatigue,
                attachment_count=attachment_count,
                image_question_count=image_question_count,
            ),
            "conversation_summary": [
                self._conversation_summary(
                    topics=deduped_topics,
                    state_summary=deduped_state,
                    child_turn_count=child_turn_count,
                    agent_turn_count=agent_turn_count,
                )
            ],
            "avoid_followup": self._avoid_followup(
                topics=deduped_topics,
                has_topic_change=has_topic_change,
                has_sports_fatigue=has_sports_fatigue,
            ),
            "state_summary": deduped_state,
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

    def _topic_overview_for_conversation(
        self,
        *,
        topics: list[str],
        has_learning: bool,
        has_sports: bool,
        has_game: bool,
        has_topic_change: bool,
        has_sports_fatigue: bool,
        attachment_count: int,
        image_question_count: int,
    ) -> list[ParentReportTopicOverview]:
        overview: list[ParentReportTopicOverview] = []
        for topic in topics[:6]:
            if topic == "学习求助" and has_learning:
                overview.append(
                    ParentReportTopicOverview(
                        topic=topic,
                        child_intent="想解决题目或学习卡点",
                        summary="今天出现学习求助线索，重点是先弄清题目在问什么，而不是直接追答案。",
                        emotion_tone="需要低压力分步支持",
                        parent_bridge="今晚可以说：“如果有题卡住，我们先听你说题目在问什么。”",
                    )
                )
            elif topic == "运动比赛/跑步" and has_sports:
                overview.append(
                    ParentReportTopicOverview(
                        topic=topic,
                        child_intent="主动分享比赛、速度或跑后感受",
                        summary="孩子围绕运动比赛或跑步体验展开，可能也用了夸张疲惫表达。",
                        emotion_tone="兴奋里带一点疲惫"
                        if has_sports_fatigue
                        else "有主动表达兴趣",
                        parent_bridge="今晚可以轻轻问跑步里最有意思的一段，不追问距离真假。",
                    )
                )
            elif topic == "游戏/CS" and has_game:
                overview.append(
                    ParentReportTopicOverview(
                        topic=topic,
                        child_intent="分享游戏里的地图、规则或队友体验",
                        summary="今天游戏话题更像兴趣表达入口；如果孩子回复变短，后续适合给换题选择。",
                        emotion_tone="有兴趣，但可能不想被继续盘问",
                        parent_bridge="今晚可以轻轻接一句游戏里的创意规则，再给孩子换话题自由。",
                    )
                )
            elif topic in {"图片分享", "看图交流"} and (
                attachment_count or image_question_count
            ):
                overview.append(
                    ParentReportTopicOverview(
                        topic=topic,
                        child_intent="把看到的东西交给小白狐一起看",
                        summary="今天图片更像是表达入口，父亲可以先顺着孩子想看的点，而不是默认当成作业。",
                        emotion_tone="好奇或想分享",
                        parent_bridge="今晚可以问：“那张图你最想让我看哪里？”孩子不想说就换轻松话题。",
                    )
                )
            elif topic == "安全或隐私边界":
                overview.append(
                    ParentReportTopicOverview(
                        topic=topic,
                        child_intent="对话触发了边界提醒",
                        summary="需要父亲平静确认是否只是误触发；如果确有不舒服的事，再做具体了解。",
                        emotion_tone="需要稳定、安全的成人支持",
                        parent_bridge="今晚先平静确认有没有需要大人帮忙的事，不追问细节。",
                    )
                )
            elif topic == "情绪表达":
                overview.append(
                    ParentReportTopicOverview(
                        topic=topic,
                        child_intent="表达累、困、不想聊或类似状态",
                        summary="今天出现过状态线索，适合先确认孩子是不是累了或只是想重说一遍。",
                        emotion_tone="需要被接住和放慢",
                        parent_bridge="今晚可以先问想休息还是一起做件轻松的小事。",
                    )
                )
            else:
                overview.append(
                    ParentReportTopicOverview(
                        topic=topic,
                        child_intent="日常自由聊天",
                        summary="今天主要是轻量日常交流，适合用一个具体小细节自然连接现实生活。",
                        emotion_tone="平稳",
                        parent_bridge="今晚可以轻轻问一件还不错的小事；孩子不想说就不追问。",
                    )
                )
        if has_topic_change and overview:
            overview[0] = overview[0].model_copy(
                update={
                    "summary": overview[0].summary
                    + " 孩子也表达过换题需求，后续要尊重转场。",
                }
            )
        return overview

    def _conversation_summary(
        self,
        *,
        topics: list[str],
        state_summary: list[str],
        child_turn_count: int,
        agent_turn_count: int,
    ) -> str:
        if not topics:
            return "今天没有足够会话素材，不做额外判断。"
        topic_text = "、".join(topics[:4])
        base = (
            f"今天主要聊了{topic_text}。"
            f"可用素材包含 {child_turn_count} 个孩子回合和 {agent_turn_count} 个小白狐回合的结构化摘要。"
        )
        if state_summary:
            base += f" {state_summary[0]}"
        return base

    def _avoid_followup(
        self,
        *,
        topics: list[str],
        has_topic_change: bool,
        has_sports_fatigue: bool,
    ) -> list[str]:
        avoid = ["不要追问孩子今天在小白狐里逐字聊了什么。"]
        if has_topic_change:
            avoid.append("孩子已经表达换题时，不要把话题拉回旧问题。")
        if has_sports_fatigue or "运动比赛/跑步" in topics:
            avoid.append("不要连续核对跑了多远、真假或成绩。")
        if "学习求助" in topics:
            avoid.append("不要直接追问最终答案或替孩子完成作业。")
        if "图片分享" in topics or "看图交流" in topics:
            avoid.append("不要把所有图片都默认当成作业或隐私问题。")
        if "游戏/CS" in topics:
            avoid.append("不要把游戏话题立刻变成时长盘问、输赢评价或禁令谈判。")
        return self._dedupe_and_limit(avoid, limit=5)

    def _contains_any(self, text: str, markers: tuple[str, ...]) -> bool:
        normalized = text.strip().lower().replace(" ", "")
        return any(marker in normalized for marker in markers)

    def _is_learning_help_text(self, text: str) -> bool:
        normalized = text.strip().lower().replace(" ", "")
        if self._contains_any(normalized, ("换个话题", "题外话")):
            return False
        explicit_learning_phrases = (
            "我有一道题不会",
            "有一道题不会",
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
        )
        if self._contains_any(normalized, explicit_learning_phrases):
            return True
        learning_subjects = (
            "作业",
            "数学题",
            "语文题",
            "英语题",
            "口算",
            "应用题",
            "练习册",
            "课本题",
        )
        help_markers = ("不会", "不懂", "怎么做", "帮我", "看看", "检查")
        return self._contains_any(normalized, learning_subjects) and self._contains_any(
            normalized,
            help_markers,
        )

    def _is_sports_text(self, text: str) -> bool:
        return self._contains_any(
            text,
            ("比赛", "运动", "跑步", "跑完", "十五公里", "公里", "快的感觉"),
        )

    def _has_sports_fatigue_expression(self, text: str) -> bool:
        return self._is_sports_text(text) and self._contains_any(
            text,
            ("要死了", "累死了", "快不行了", "喘死了"),
        )

    def _is_game_text(self, text: str) -> bool:
        return self._contains_any(
            text,
            ("游戏", "cs", "反恐", "地图", "队友", "排位", "关卡", "打游戏"),
        )

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
        if conversation_topics and "运动比赛/跑步" in conversation_topics:
            actions.append(
                "如果孩子聊到比赛或跑后“要死了”一类夸张疲惫，可以温和确认跑后是否只是累、有没有疼痛；不要否定夸张表达，也不要追问太久。"
            )
        if conversation_topics and "游戏/CS" in conversation_topics:
            actions.append(
                "如果孩子聊到游戏，可以先接一个规则或创意点；避免把话题变成时长盘问、输赢评价或连续追问。"
            )

        actions.extend(self._relationship_parent_actions(memories))

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

    def _tonight_parent_bridge(
        self,
        *,
        actions: list[str],
        topics: list[str],
        has_material: bool,
        has_safety: bool,
    ) -> str:
        if not has_material:
            return (
                "今晚可以轻轻说：“今天如果不想聊也没关系，我们一起做一件轻松的小事。”"
                "不要追问孩子今天在小白狐里说了什么。"
            )
        if has_safety:
            return (
                "今晚先用平静语气确认孩子有没有不舒服或需要大人帮忙的事；"
                "如果孩子不想说，先陪在身边，不追问细节。"
            )
        if "图片分享" in topics or "看图交流" in topics:
            return (
                "今晚可以轻轻问：“你今天那张图，最想让我看哪里？”"
                "如果孩子不想说，就一起看一眼图片或换轻松话题，不追问。"
            )
        if "运动比赛/跑步" in topics:
            return (
                "今晚可以轻轻问：“你今天说到跑步，最有意思的是哪一段？”"
                "如果孩子不想说，就换成整理鞋子或喝水休息，不追问。"
            )
        if "游戏/CS" in topics:
            return (
                "今晚可以轻轻说：“你今天说到游戏里的规则，听起来有点像在设计玩法。”"
                "如果孩子不想接，就给他换个轻松话题，不追问时长或输赢。"
            )
        if "学习求助" in topics:
            return (
                "今晚可以轻轻说：“如果有题卡住，我们先听你说题目在问什么。”"
                "如果孩子不想说，就先休息，不追问答案。"
            )

        first_action = next((action for action in actions if action.strip()), "")
        if first_action.startswith("今晚可以"):
            bridge = first_action
        else:
            bridge = "今晚可以轻轻问：“今天有没有一件还不错的小事？”"
            if first_action:
                bridge += f" 也可以参考：{first_action}"
        if not self._contains_any(bridge, ("不追问", "不要追问", "避免连续追问", "换轻松")):
            bridge += " 如果孩子不想说，就换轻松方式，不追问。"
        return self._safe_bridge_text(bridge) or (
            "今晚可以轻轻问一个小细节；如果孩子不想说，就换轻松方式，不追问。"
        )

    def _safe_bridge_text(self, text: str) -> str | None:
        safe = self._safe_text(text)
        if not safe:
            return None
        if self._contains_any(
            safe,
            ("backend", "provider", "config", "debug", "模型配置", "后端", "逐字聊天记录"),
        ):
            return None
        return safe[:260]

    def _relationship_parent_actions(self, memories: list[MemoryItem]) -> list[str]:
        actions: list[str] = []
        for memory in relationship_memories(
            memories,
            relationship_memory_type=INTEREST_SEED,
        )[:2]:
            topic = memory_relationship_topic(memory) or "孩子最近主动提到的兴趣"
            if topic == "跑步比赛":
                starter = "我听说你最近聊到跑步比赛，你最喜欢跑得快的哪一刻？"
                avoid = "避免连续追问距离真假或身体问题。"
            else:
                starter = f"我听说你最近聊到{topic}，你最喜欢里面哪一小点？"
                avoid = "避免连续追问或把兴趣变成任务。"
            hook = memory_relationship_next_hook(memory)
            suffix = f"也可以参考：{hook}。" if hook else ""
            actions.append(f"今晚可以轻轻问：“{starter}”{avoid}{suffix}")

        if relationship_memories(memories, relationship_memory_type=PROUD_MOMENT):
            actions.append(
                "孩子今天有表达展开的小进步；可以具体反馈“你刚才把事情说清楚了”，不要用积分、排名或比较来强化。"
            )
        if relationship_memories(memories, relationship_memory_type=TOPIC_BOUNDARY):
            actions.append(
                "孩子表达不想聊或想换题时，父亲可以尊重停顿，给两个轻松选择，不把话题拉回旧问题。"
            )
        return actions

    def _relationship_memory_payload(
        self,
        memory: MemoryItem,
    ) -> dict[str, object] | None:
        relationship_type = None
        for evidence in memory.evidence:
            value = evidence.metadata.get("relationship_memory_type")
            if isinstance(value, str):
                relationship_type = value
                break
        if relationship_type is None:
            return None
        return {
            "type": relationship_type,
            "topic": self._safe_text(memory_relationship_topic(memory) or ""),
            "next_hook": self._safe_text(memory_relationship_next_hook(memory) or ""),
        }

    def _summary(
        self,
        *,
        memories: list[MemoryItem],
        conversation_messages: list[ConversationReportMessage],
        conversation_topics: list[str],
        conversation_state: list[str],
        has_learning: bool,
        has_expression: bool,
        has_emotion: bool,
        has_safety: bool,
    ) -> str:
        if not memories and not conversation_messages:
            return "今天暂无可汇总的结构化会话素材。建议保持轻量观察，不做额外判断。"
        if has_safety:
            return (
                "今天的结构化素材里包含需要父亲关注的安全信号或隐私边界。"
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
        state_text = conversation_state[0] if conversation_state else (
            "整体适合用低压力提问和具体小步骤支持孩子。"
        )
        return (
            f"今天的结构化素材重点集中在{focus_text}。"
            f"{state_text}"
        )

    def _safe_text(self, text: str) -> str:
        safe = " ".join(text.strip().split())
        for forbidden, replacement in self._FORBIDDEN_REPLACEMENTS.items():
            safe = safe.replace(forbidden, replacement)
        lowered = safe.lower()
        secret_markers = (
            "authorization:",
            "bearer ",
            "api_key",
            "apikey",
            "secret",
            "token",
            "data:image",
            "data:audio",
            ";base64,",
            "provider raw",
            "debug trace",
            "prompt:",
        )
        if any(marker in lowered for marker in secret_markers):
            return "[redacted]"
        return safe[:220]

    def _material_fingerprint(
        self,
        *,
        memories: list[MemoryItem],
        conversation_messages: list[ConversationReportMessage],
    ) -> str:
        payload = {
            "memories": [
                {
                    "id": memory.id,
                    "updated_at": self._aware_datetime(memory.updated_at).isoformat(),
                }
                for memory in memories
            ],
            "messages": [
                {
                    "id": message.id,
                    "created_at": self._aware_datetime(message.created_at).isoformat(),
                }
                for message in conversation_messages
            ],
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return sha256(raw.encode("utf-8")).hexdigest()[:32]

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
