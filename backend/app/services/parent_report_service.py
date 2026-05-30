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
from app.services.companion_object_service import (
    CompanionObjectService,
    get_companion_object_service,
)
from app.services.memory_service import MemoryService, get_memory_service
from app.services.model_registry import ModelRegistry, get_model_registry
from app.services.parent_policy_service import ParentPolicyService
from app.services.parent_report_language_v4 import (
    avoid_followup_v4,
    companion_deterministic_summary,
    deterministic_narrative_v4,
    parent_report_system_prompt_v4,
)
from app.services.relationship_memory import (
    memory_relationship_next_hook,
    memory_relationship_topic,
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
        parent_policy_service: ParentPolicyService | None = None,
        companion_object_service: CompanionObjectService | None = None,
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
        self._parent_policy_service = parent_policy_service
        self._companion_object_service = companion_object_service
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
        companion_signal = self._get_companion_signal(child_id, target_date)
        existing = self._get_persisted_report(child_id, target_date)
        if existing is not None and not self._is_stale(
            existing,
            memories=memories,
            conversation_messages=conversation_messages,
            companion_signal=companion_signal,
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

    def _lookup_support_style(self, child_id: str) -> list[str]:
        if self._parent_policy_service is None:
            return []
        try:
            policy = self._parent_policy_service.get_policy(child_id)
        except Exception:  # noqa: BLE001
            return []
        preferences = getattr(policy, "communication_preferences", None)
        if not isinstance(preferences, dict):
            return []
        support_style = preferences.get("support_style_preferences")
        if isinstance(support_style, list):
            return [str(item) for item in support_style]
        return []

    def _lookup_topic_boundaries(self, child_id: str) -> list[str]:
        if self._parent_policy_service is None:
            return []
        try:
            policy = self._parent_policy_service.get_policy(child_id)
        except Exception:  # noqa: BLE001
            return []
        preferences = getattr(policy, "communication_preferences", None)
        if not isinstance(preferences, dict):
            return []
        boundaries = preferences.get("topic_boundaries")
        if isinstance(boundaries, list):
            return [str(item) for item in boundaries if str(item).strip()]
        return []

    def _has_sufficient_material(
        self,
        *,
        memories: list[MemoryItem],
        conversation_messages: list[ConversationReportMessage],
    ) -> bool:
        if memories:
            return True
        child_messages = [
            msg for msg in conversation_messages if msg.actor == "child"
        ]
        return len(child_messages) >= 1

    def _get_companion_signal(
        self,
        child_id: str,
        target_date: date,
    ) -> dict[str, object]:
        """Fetch companion object signal for parent report.

        Returns dict with has_companion (bool) and source_type (str).
        Only returns ACTIVE companions created/updated on target_date.
        """
        if self._companion_object_service is None:
            try:
                self._companion_object_service = get_companion_object_service()
            except Exception:  # noqa: BLE001
                return {"has_companion": False, "source_type": ""}
        try:
            companion = self._companion_object_service.get_active_by_child(child_id)
        except Exception:  # noqa: BLE001
            return {"has_companion": False, "source_type": ""}
        if companion is None:
            return {"has_companion": False, "source_type": ""}
        # Only show ACTIVE companions in parent report (not PAUSED)
        from app.domain.companion_object import CompanionObjectStatus

        if companion.status != CompanionObjectStatus.ACTIVE:
            return {"has_companion": False, "source_type": ""}
        # Only include if created or updated on target_date
        created_date = companion.created_at.date()
        updated_date = companion.updated_at.date()
        if created_date != target_date and updated_date != target_date:
            return {"has_companion": False, "source_type": ""}
        return {
            "has_companion": True,
            "source_type": companion.source_type.value
            if hasattr(companion.source_type, "value")
            else str(companion.source_type),
        }

    def _generate_daily_report_from_materials(
        self,
        *,
        child_id: str,
        target_date: date,
        memories: list[MemoryItem],
        conversation_messages: list[ConversationReportMessage],
    ) -> ParentReport:
        if not self._has_sufficient_material(
            memories=memories,
            conversation_messages=conversation_messages,
        ):
            return self._material_insufficient_report(
                child_id=child_id,
                target_date=target_date,
            )
        support_style = self._lookup_support_style(child_id)
        topic_boundaries = self._lookup_topic_boundaries(child_id)
        conversation = self._conversation_analysis(conversation_messages)
        companion_signal = self._get_companion_signal(child_id, target_date)
        fallback_report = self._deterministic_fallback_report(
            child_id=child_id,
            target_date=target_date,
            memories=memories,
            conversation_messages=conversation_messages,
            conversation=conversation,
            support_style=support_style,
            companion_signal=companion_signal,
        )
        material_fingerprint = self._material_fingerprint(
            memories=memories,
            conversation_messages=conversation_messages,
            companion_signal=companion_signal,
        )
        model_result = self._model_daily_report(
            child_id=child_id,
            target_date=target_date,
            memories=memories,
            conversation_messages=conversation_messages,
            conversation=conversation,
            fallback_report=fallback_report,
            material_fingerprint=material_fingerprint,
            support_style=support_style,
            topic_boundaries=topic_boundaries,
            companion_signal=companion_signal,
        )
        if model_result.report is not None:
            return model_result.report
        return self._failed_report(
            child_id=child_id,
            target_date=target_date,
            error_code=model_result.error_code or "model_unavailable",
            material_fingerprint=material_fingerprint,
            companion_signal=companion_signal,
        )

    def _deterministic_fallback_report(
        self,
        *,
        child_id: str,
        target_date: date,
        memories: list[MemoryItem],
        conversation_messages: list[ConversationReportMessage],
        conversation: dict[str, list[str]],
        support_style: list[str] | None = None,
        companion_signal: dict[str, object] | None = None,
    ) -> ParentReport:
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

        companion_summary = None
        tonight_bridge = None
        if companion_signal and companion_signal.get("has_companion"):
            companion_summary = companion_deterministic_summary(
                has_companion=True,
                source_type=str(companion_signal.get("source_type", "")),
            )
            tonight_bridge = "今晚可以轻轻问一句：你今天给小白狐看了什么呀？"

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
            tonight_parent_bridge=tonight_bridge,
            avoid_followup=[],
            companion_summary=companion_summary,
            created_at=self._now(),
            generation_status=ParentReportGenerationStatus.DETERMINISTIC_FALLBACK,
            generated_by="deterministic_fallback",
            generation_error_code=None,
            material_fingerprint=self._material_fingerprint(
                memories=memories,
                conversation_messages=conversation_messages,
                companion_signal=companion_signal,
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
        support_style: list[str] | None = None,
        topic_boundaries: list[str] | None = None,
        companion_signal: dict[str, object] | None = None,
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
                support_style=support_style,
                topic_boundaries=topic_boundaries,
                companion_signal=companion_signal,
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
                    support_style=support_style,
                    topic_boundaries=topic_boundaries,
                    companion_signal=companion_signal,
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
        companion_summary = None
        tonight_bridge = None
        if companion_signal and companion_signal.get("has_companion"):
            companion_summary = companion_deterministic_summary(
                has_companion=True,
                source_type=str(companion_signal.get("source_type", "")),
            )
            tonight_bridge = "今晚可以轻轻问一句：你今天给小白狐看了什么呀？"

        return _ModelDailyReportResult(
            report=ParentReport(
                child_id=child_id,
                date=target_date,
                summary=parsed["summary"],
                topic_overview=parsed["topic_overview"]
                or fallback_report.topic_overview,
                conversation_summary=None,
                learning_observations=[],
                expression_observations=[],
                emotion_observations=[],
                safety_alerts=parsed["safety_alerts"],
                suggested_parent_actions=[],
                tonight_parent_bridge=tonight_bridge,
                avoid_followup=[],
                companion_summary=companion_summary,
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
        companion_signal: dict[str, object] | None = None,
    ) -> ParentReport:
        status = (
            ParentReportGenerationStatus.MODEL_BLOCKED
            if "policy" in error_code.lower() or "blocked" in error_code.lower()
            else ParentReportGenerationStatus.MODEL_FAILED
        )
        companion_summary = None
        tonight_bridge = None
        if companion_signal and companion_signal.get("has_companion"):
            companion_summary = companion_deterministic_summary(
                has_companion=True,
                source_type=str(companion_signal.get("source_type", "")),
            )
            tonight_bridge = "今晚可以轻轻问一句：你今天给小白狐看了什么呀？"
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
            suggested_parent_actions=[],
            tonight_parent_bridge=tonight_bridge,
            avoid_followup=[],
            companion_summary=companion_summary,
            created_at=self._now(),
            generation_status=status,
            generated_by="model",
            generation_error_code=error_code,
            material_fingerprint=material_fingerprint,
        )

    def _material_insufficient_report(
        self,
        *,
        child_id: str,
        target_date: date,
    ) -> ParentReport:
        return ParentReport(
            child_id=child_id,
            date=target_date,
            summary="今天聊得还不多，小结会短一点。",
            topic_overview=[],
            conversation_summary=None,
            learning_observations=[],
            expression_observations=[],
            emotion_observations=[],
            safety_alerts=[],
            suggested_parent_actions=[],
            tonight_parent_bridge=None,
            avoid_followup=[],
            companion_summary=None,
            created_at=self._now(),
            generation_status=ParentReportGenerationStatus.MATERIAL_INSUFFICIENT,
            generated_by="system",
            generation_error_code=None,
            material_fingerprint=None,
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
        support_style: list[str] | None = None,
        topic_boundaries: list[str] | None = None,
        companion_signal: dict[str, object] | None = None,
    ):
        payload = self._parent_report_model_payload(
            target_date=target_date,
            memories=memories,
            conversation_messages=conversation_messages,
            conversation=conversation,
            fallback_report=fallback_report,
            support_style=support_style,
            topic_boundaries=topic_boundaries,
            companion_signal=companion_signal,
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
        return parent_report_system_prompt_v4()

    def _parent_report_model_payload(
        self,
        *,
        target_date: date,
        memories: list[MemoryItem],
        conversation_messages: list[ConversationReportMessage],
        conversation: dict[str, list[str]],
        fallback_report: ParentReport,
        support_style: list[str] | None = None,
        topic_boundaries: list[str] | None = None,
        companion_signal: dict[str, object] | None = None,
    ) -> dict[str, object]:
        # Build memory summaries with relationship_memory_type
        memory_summaries = []
        for memory in memories[:6]:
            rel_type = self._memory_relationship_type(memory)
            summary: dict[str, object] = {
                "type": memory.memory_type.value,
                "content": self._safe_text(memory.content)[:80],
                "requires_parent_attention": memory.requires_parent_attention,
            }
            if rel_type:
                summary["relationship_memory_type"] = rel_type
            memory_summaries.append(summary)

        # Build short_content_hint from conversation snippets
        short_hints = []
        for msg in conversation_messages[:2]:
            hint = self._conversation_snippet(msg).get("short_content_hint", "")
            if hint:
                short_hints.append(str(hint)[:40])

        payload: dict[str, object] = {
            "report_date": target_date.isoformat(),
            "material_policy": (
                "Only structured summaries are provided; do not quote child text verbatim. "
                "Use safe summaries and topic labels only."
            ),
            "topic_hints": conversation["topics"],
            "topic_overview_hints": [
                {
                    "topic": item.topic,
                    "summary": item.summary[:120],
                    "parent_bridge": item.parent_bridge[:120],
                }
                for item in conversation["topic_overview"][:4]
            ],
            "state_hints": conversation["state_summary"][:2],
            "conversation_summary_hint": (
                conversation["conversation_summary"][0][:180]
            )
            if conversation["conversation_summary"]
            else "",
            "short_content_hint": "; ".join(short_hints)[:120] if short_hints else "",
            "avoid_followup_hints": conversation["avoid_followup"],
            "observation_hints": {
                "learning": [
                    item[:100] for item in conversation["learning_observations"][:2]
                ],
                "expression": [
                    item[:100] for item in conversation["expression_observations"][:2]
                ],
                "emotion": [
                    item[:100] for item in conversation["emotion_observations"][:2]
                ],
                "safety": [item[:100] for item in conversation["safety_alerts"][:2]],
            },
            "memory_summaries": memory_summaries,
            "conversation_snippets": [
                self._conversation_snippet(message)
                for message in conversation_messages[:2]
            ],
            "report_schema": (
                "Return strict JSON. Keys: summary, mentioned_items, attention_items."
            ),
            "deterministic_fallback_hints": {
                "topics": conversation["topics"],
            },
        }
        if support_style:
            payload["support_style_preferences"] = support_style

        # Add topic_boundaries from parent policy
        if topic_boundaries:
            payload["topic_boundaries"] = topic_boundaries[:3]

        # Add companion signal (boolean/enum only, no names/locations/counts)
        if companion_signal and companion_signal.get("has_companion"):
            payload["companion_hints"] = {
                "had_light_cocreation": True,
                "cocreation_kind": companion_signal.get("source_type", ""),
            }

        return payload

    def _memory_relationship_type(self, memory: MemoryItem) -> str | None:
        """Extract relationship_memory_type from memory evidence metadata."""
        for evidence in memory.evidence:
            value = evidence.metadata.get("relationship_memory_type")
            if isinstance(value, str):
                return value
        return None

    def _conversation_snippet(
        self,
        message: ConversationReportMessage,
    ) -> dict[str, object]:
        raw_text = message.normalized_text or ""
        safe_text = self._safe_text(raw_text)
        short_hint = safe_text[:40] if safe_text and "[redacted]" not in safe_text else ""
        return {
            "actor": message.actor,
            "message_type": message.message_type,
            "scene": message.active_scene,
            "risk_level": message.risk_level,
            "has_attachment": message.attachments_count > 0,
            "text_signal": self._conversation_text_signal(raw_text),
            "short_content_hint": short_hint,
        }

    def _conversation_text_signal(self, text: str) -> str:
        safe = self._safe_text(text)
        if "[redacted]" in safe:
            return "[redacted]"
        if self._is_game_text(safe):
            return "game_or_cs"
        if self._is_learning_help_text(safe):
            return "learning_help"
        if self._contains_any(safe, ("图片", "照片", "拍", "看", "这是什么")):
            return "image_or_photo"
        if self._contains_any(
            safe,
            ("难过", "害怕", "担心", "生气", "烦", "累", "困", "不想", "没听清"),
        ):
            return "emotion_or_boundary"
        return "general_child_message"

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

        # New schema: summary + mentioned_items + attention_items
        summary = self._safe_text(str(raw.get("summary") or ""))
        if summary:
            mentioned = raw.get("mentioned_items")
            attention = raw.get("attention_items")
            topic_overview: list[ParentReportTopicOverview] = []
            if isinstance(mentioned, list):
                for item in mentioned[:4]:
                    text = self._safe_text(str(item))[:60]
                    if text:
                        topic_overview.append(
                            ParentReportTopicOverview(
                                topic=text,
                                child_intent="",
                                summary=text,
                                emotion_tone="",
                                parent_bridge="",
                            )
                        )
            safety_alerts: list[str] = []
            if isinstance(attention, list):
                for item in attention[:3]:
                    text = self._safe_text(str(item))
                    if text:
                        safety_alerts.append(text)
            return {
                "summary": summary[:500],
                "topic_overview": topic_overview,
                "conversation_summary": None,
                "learning_observations": [],
                "expression_observations": [],
                "emotion_observations": [],
                "safety_alerts": safety_alerts,
                "suggested_parent_actions": [],
                "tonight_parent_bridge": None,
                "avoid_followup": [],
            }

        # Legacy format: narrative_report
        narrative = self._safe_text(str(raw.get("narrative_report") or ""))
        if narrative:
            return {
                "summary": narrative[:500],
                "topic_overview": [],
                "conversation_summary": None,
                "learning_observations": [],
                "expression_observations": [],
                "emotion_observations": [],
                "safety_alerts": [],
                "suggested_parent_actions": [],
                "tonight_parent_bridge": None,
                "avoid_followup": [],
            }

        # Legacy format: summary
        legacy_summary = self._safe_text(str(raw.get("summary") or ""))
        if not legacy_summary:
            return None
        return {
            "summary": legacy_summary[:500],
            "topic_overview": self._model_topic_overview(raw),
            "conversation_summary": self._safe_text(
                str(raw.get("conversation_summary") or ""),
            )[:600]
            or None,
            "learning_observations": self._model_list(raw, "learning_observations"),
            "expression_observations": self._model_list(raw, "expression_observations"),
            "emotion_observations": self._model_list(raw, "emotion_observations"),
            "safety_alerts": self._model_list(raw, "safety_alerts"),
            "suggested_parent_actions": [],
            "tonight_parent_bridge": None,
            "avoid_followup": [],
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
        if isinstance(value, str):
            text = self._safe_text(value)
            return [text] if text else []
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
        companion_signal: dict[str, object] | None = None,
    ) -> bool:
        if report.generation_status != ParentReportGenerationStatus.MODEL_GENERATED:
            return True
        if not report.summary:
            return True
        material_fingerprint = self._material_fingerprint(
            memories=memories,
            conversation_messages=conversation_messages,
            companion_signal=companion_signal,
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
        game_detail_summary = self._game_detail_summary(child_texts)
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
                "孩子今天围绕运动比赛、跑步或速度感受连续表达；家长可以顺着孩子主动提起的部分轻轻接一句，不核对成绩和真假。"
            )
        if has_game_topic:
            topics.append("游戏/CS")
            expression_observations.append(
                "孩子今天围绕游戏、地图、队友或规则表达兴趣；家长可以把它当作普通兴趣入口，不把游戏话题变成盘问或限制谈判。"
            )
            if game_detail_summary:
                state_summary.append(game_detail_summary)
        if attachment_count:
            topics.append("图片分享")
            expression_observations.append(
                '孩子今天有通过图片表达或展示的倾向；家长可以顺着孩子愿意分享的部分看一眼，不需要追问具体是哪张图。'
            )
        elif image_question_count:
            topics.append("看图交流")
            expression_observations.append(
                "孩子今天围绕图片或“这是什么”发起交流；适合让孩子先补充一个画面细节，再陪他一起判断。"
            )
        if any(scene.startswith("privacy.") or scene.startswith("safety.") for scene in scenes):
            topics.append("安全或隐私边界")
            safety_alerts.append(
                "今天对话触发过安全或隐私边界。建议家长平静确认是否只是误触发，必要时再做具体了解。"
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
                "今天出现过情绪、疲惫或“没听清”一类状态线索；家长可以先确认孩子是不是累了、被打断了，或只是想重说一遍。"
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
                "孩子今天更多使用短句或指令式表达；家长可以用二选一、三选一或让孩子先说一个关键词来降低开口压力。"
            )
            state_summary.append("孩子今天更多是短句或指令式表达，需要更具体、低压力的追问来展开。")
        else:
            expression_observations.append(
                "孩子今天愿意围绕一个主题多说几句；家长可以围绕孩子主动提到的主题轻轻接一个具体细节，不要连续追问。"
            )
            state_summary.append("孩子今天愿意围绕一个主题多说几句，适合围绕他主动发起的话题轻轻延展。")
        if attachment_count:
            state_summary.append("孩子今天更多是通过图片来表达自己，不要默认当成作业或隐私问题。")
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
                game_detail_summary=game_detail_summary,
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
        game_detail_summary: str | None,
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
                        parent_bridge="如果孩子自己提起跑步，可以先顺着他说一小句，不核对成绩和真假。",
                    )
                )
            elif topic == "游戏/CS" and has_game:
                overview.append(
                    ParentReportTopicOverview(
                        topic=topic,
                        child_intent="分享游戏里的地图、规则或队友体验",
                        summary=game_detail_summary
                        or "今天游戏话题更像是孩子在分享兴趣；如果孩子回复变短，后续适合给换题选择。",
                        emotion_tone="有兴趣，但可能不想被继续盘问",
                        parent_bridge="如果孩子自己提起游戏，可以先把它当作普通兴趣听一句，不急着谈时长或输赢。",
                    )
                )
            elif topic in {"图片分享", "看图交流"} and (
                attachment_count or image_question_count
            ):
                overview.append(
                    ParentReportTopicOverview(
                        topic=topic,
                        child_intent="通过图片表达或展示自己看到、做出的东西",
                        summary="今天图片更像是孩子表达或展示的入口。家长可以给一个开放分享机会，不需要追问具体是哪张图。",
                        emotion_tone="好奇或想分享",
                        parent_bridge="今晚可以自然留个入口：“今天有没有什么想给我看看，或者想讲给我听的小东西？”如果孩子不想说，就不用追问。",
                    )
                )
            elif topic == "安全或隐私边界":
                overview.append(
                    ParentReportTopicOverview(
                        topic=topic,
                        child_intent="对话触发了边界提醒",
                        summary="需要家长平静确认是否只是误触发；如果确有不舒服的事，再做具体了解。",
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
        base = f"今天有一些轻量互动，主要围绕{topic_text}。"
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
        return avoid_followup_v4(
            topics=topics,
            has_topic_change=has_topic_change,
            has_sports_fatigue=has_sports_fatigue,
            has_safety="安全或隐私边界" in topics,
        )

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

    def _game_detail_summary(self, child_texts: list[str]) -> str | None:
        if not any(self._is_game_text(text) for text in child_texts):
            return None
        details: list[str] = []
        if any(self._contains_any(text, ("地图", "沙二", "dust")) for text in child_texts):
            details.append("地图")
        if any(
            self._contains_any(text, ("队友", "朋友", "同学", "组队", "配合"))
            for text in child_texts
        ):
            details.append("队友或朋友配合")
        if any(
            self._contains_any(text, ("输了", "输掉", "没赢", "最后输了", "赢了"))
            for text in child_texts
        ):
            details.append("输赢感受")
        if not details:
            details.append("规则或玩法")
        detail_text = "、".join(self._dedupe_and_limit(details, limit=3))
        return (
            f"孩子围绕游戏/CS聊到{detail_text}，更像是在分享兴趣和规则理解；"
            "如果后面回复变短，今晚不适合继续追问时长、输赢或细节。"
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
            "今天出现需要家长关注的安全信号。请用平静语气确认孩子是否遇到让他不舒服、要求保密或涉及陌生人的情况。"
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
        support_style: list[str] | None = None,
    ) -> list[str]:
        style = support_style or []
        offer_two = "offer_two_choices" in style
        ask_fewer = "ask_fewer_questions" in style
        gentle = "encourage_gently" in style

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
            if offer_two:
                actions.append(
                    "开场给两个简单选择就好，例如“今天想说开心的事，还是想安静一会儿？”不追问，让孩子自己选。"
                )
            else:
                actions.append(
                    "开场先给二选一或三选一，例如“今天想说开心的事、难的事，还是想安静一会儿？”"
                )
        if has_emotion:
            if gentle:
                actions.append(
                    "如果孩子表达低落或紧张，先温和回应感受，给他时间；不急着问怎么办，先陪一会儿。"
                )
            else:
                actions.append(
                    "如果孩子表达低落或紧张，先回应感受，再问他想休息、被陪一会儿，还是一起想一个小办法。"
                )
        if conversation_topics and "图片分享" in conversation_topics:
            actions.append(
                "孩子今天有通过图片表达或展示的倾向；家长可以顺着孩子愿意分享的部分看一眼，不需要追问具体是哪张图。"
            )
        if conversation_topics and "运动比赛/跑步" in conversation_topics:
            actions.append(
                "如果孩子聊到比赛或跑后“要死了”一类夸张疲惫，可以温和确认跑后是否只是累、有没有疼痛；不要否定夸张表达，也不要追问太久。"
            )
        if conversation_topics and "游戏/CS" in conversation_topics:
            actions.append(
                "如果孩子聊到游戏，可以先接一个规则或创意点；避免把话题变成时长盘问、输赢评价或连续追问。"
            )

        actions.extend(self._relationship_parent_actions(memories, support_style=style))

        strategy_memories = [
            memory for memory in memories if memory.memory_type == MemoryType.STRATEGY
        ]
        if strategy_memories:
            actions.append(self._safe_text(strategy_memories[0].content))

        if not actions:
            if ask_fewer:
                actions.append(
                    "今晚只轻轻问一个很小的事就好，例如“今天有没有一件还不错的小事？”不追问，给孩子空间。"
                )
            else:
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
        return tonight_parent_bridge_v4(
            has_material=has_material,
            has_safety=has_safety,
            topics=topics,
        )

    def _safe_bridge_text(self, text: str) -> str | None:
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

    def _relationship_parent_actions(
        self,
        memories: list[MemoryItem],
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
        companion_signal: dict[str, object] | None = None,
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
        if companion_signal:
            payload["companion"] = companion_signal
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
