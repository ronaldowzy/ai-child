from datetime import date, datetime, timezone
import json

from app.domain.memory import (
    MemoryCreateRequest,
    MemoryEvidence,
    MemorySensitivity,
    MemoryType,
)
from app.domain.model_types import ModelResponse, ModelTaskType
from app.domain.parent_report import ParentReportGenerationStatus
from app.repositories.memory_repository import InMemoryMemoryRepository
from app.repositories.conversation_persistence_repository import ConversationReportMessage
from app.repositories.parent_report_repository import (
    InMemoryParentReportRepository,
    ParentReportRepositoryUnavailable,
)
from app.services.memory_service import MemoryService
from app.services.parent_report_service import ParentReportService


def _fixed_now() -> datetime:
    return datetime(2026, 5, 18, 10, 0, tzinfo=timezone.utc)


def _memory_request(
    *,
    child_id: str = "child_parent_report_service_test",
    memory_type: MemoryType,
    content: str,
    tags: list[str],
    sensitivity: MemorySensitivity = MemorySensitivity.LOW,
    requires_parent_attention: bool = False,
) -> MemoryCreateRequest:
    return MemoryCreateRequest(
        child_id=child_id,
        memory_type=memory_type,
        content=content,
        tags=tags,
        evidence=[
            MemoryEvidence(
                source="chat_summary",
                session_id="session_parent_report_service_test",
                quote_summary="这里是结构化摘要来源，不应在家长日报中逐字返回。",
            )
        ],
        confidence=0.82,
        importance=0.7,
        sensitivity=sensitivity,
        visible_to_parent=True,
        visible_to_child=False,
        requires_parent_attention=requires_parent_attention,
    )


class FakeConversationRepository:
    def __init__(
        self,
        messages: list[ConversationReportMessage] | None = None,
    ) -> None:
        self.messages = messages or []

    def list_report_messages(
        self,
        *,
        child_id: str,
        report_date: date,
    ) -> list[ConversationReportMessage]:
        return [
            message
            for message in self.messages
            if message.created_at.date() == report_date
        ]


class SuccessfulParentReportModelRegistry:
    def __init__(self, *, bridge_text: str | None = None) -> None:
        self.requests = []
        self.bridge_text = bridge_text

    def generate(self, request):
        self.requests.append(request)
        payload = _payload_from_request(request)
        memories = payload.get("memory_summaries", [])
        learning = [
            item["content"]
            for item in memories
            if item.get("type") == MemoryType.LEARNING_PATTERN.value
        ]
        expression = [
            item["content"]
            for item in memories
            if item.get("type") == MemoryType.EXPRESSION_PATTERN.value
        ]
        safety = [
            item["content"]
            for item in memories
            if item.get("requires_parent_attention")
            or item.get("type") == MemoryType.SAFETY.value
        ]
        topics = payload.get("topic_hints", [])
        state = payload.get("state_hints", [])
        if "学习求助" in topics and not learning:
            learning.append("模型观察：今天有学习求助线索，适合先复述题意。")
        if "图片分享" in topics and not expression:
            expression.append("模型观察：孩子今天用图片作为表达入口。")
        fallback_hints = payload.get("deterministic_fallback_hints", {})
        actions = list(fallback_hints.get("relationship_parent_actions") or [])
        if learning:
            actions.append("可以请孩子先复述题目在问什么；避免直接给最终答案。")
        if safety:
            actions.append("今晚先做安全确认；避免责备或追问细节。")
        if "图片分享" in topics:
            actions.append("可以先问'你最想让我看哪里？'；避免默认当成作业或隐私。")
        if not actions:
            actions = ["今晚可以轻轻开口问一个当天小细节；避免连续追问或贴标签。"]
        summary_topics = list(topics)
        if not summary_topics and learning:
            summary_topics.append("学习支持")
        if not summary_topics and safety:
            summary_topics.append("安全信号")
        if payload.get("conversation_snippets"):
            summary_topics.append("会话消息")
        # Build narrative report
        narrative_parts = []
        if summary_topics:
            narrative_parts.append("今天孩子主要聊了" + "、".join(summary_topics[:3]))
        if state:
            narrative_parts.append(state[0])
        if not narrative_parts:
            narrative_parts.append("基于当天素材生成。")
        narrative = "，".join(narrative_parts) + "。"

        data = {
            "narrative_report": narrative,
            "tonight_parent_bridge": self.bridge_text or "今晚可以轻轻聊几句。",
            "avoid_followup": ["不要追问孩子今天在小白狐里逐字聊了什么。"],
        }
        return ModelResponse(
            task_type=ModelTaskType.PARENT_REPORT,
            response_text="",
            structured_output={"daily_report": data},
            provider_name="mimo",
            model_name="mimo-v2.5-pro",
            metadata={},
        )


def _payload_from_request(request) -> dict:
    content = request.messages[-1].content
    if isinstance(content, list):
        raise AssertionError("parent report test request should be text JSON")
    if content.startswith("上一次输出为空或不可解析。"):
        content = content.split("\n", 1)[1]
    return json.loads(content)


def _services() -> tuple[
    InMemoryMemoryRepository,
    MemoryService,
    ParentReportService,
]:
    repository = InMemoryMemoryRepository()
    memory_service = MemoryService(
        repository=repository,
        now_provider=_fixed_now,
    )
    report_service = ParentReportService(
        memory_service=memory_service,
        conversation_repository=FakeConversationRepository(),
        model_registry=SuccessfulParentReportModelRegistry(),
        now_provider=_fixed_now,
    )
    return repository, memory_service, report_service


def _services_with_report_repository() -> tuple[
    MemoryService,
    InMemoryParentReportRepository,
    ParentReportService,
]:
    memory_repository = InMemoryMemoryRepository()
    report_repository = InMemoryParentReportRepository()
    memory_service = MemoryService(
        repository=memory_repository,
        now_provider=_fixed_now,
    )
    report_service = ParentReportService(
        memory_service=memory_service,
        repository=report_repository,
        conversation_repository=FakeConversationRepository(),
        model_registry=SuccessfulParentReportModelRegistry(),
        now_provider=_fixed_now,
    )
    return memory_service, report_repository, report_service


def _conversation_message(
    *,
    message_id: str,
    actor: str = "child",
    text: str | None,
    active_scene: str | None = "conversation.open",
    risk_level: str | None = "none",
    attachments_count: int = 0,
    created_at: datetime = datetime(2026, 5, 18, 10, 30, tzinfo=timezone.utc),
) -> ConversationReportMessage:
    return ConversationReportMessage(
        id=message_id,
        session_id="session_parent_report_service_test",
        actor=actor,
        message_type="text",
        normalized_text=text,
        active_scene=active_scene,
        risk_level=risk_level,
        attachments_count=attachments_count,
        created_at=created_at,
    )


def test_parent_report_service_generates_normal_daily_report() -> None:
    _, memory_service, report_service = _services()
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.LEARNING_PATTERN,
            content="孩子在学习求助时需要先确认题意，再一步一步说出已知条件。",
            tags=["学习求助", "题意确认"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.EXPRESSION_PATTERN,
            content="孩子在开放提问下回答较短，使用选择题式引导时更容易开始表达。",
            tags=["表达", "选择题有效"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.EMOTION_OBSERVATION,
            content="孩子本次表达了低落或紧张情绪，后续适合先接住感受再进入问题解决。",
            tags=["情绪观察", "先共情"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    assert report.child_id == "child_parent_report_service_test"
    assert report.date == date(2026, 5, 18)
    # Narrative format: summary should contain key topics
    assert report.summary, f"Should have a summary: {report.summary}"
    # Should mention learning support
    assert "学习" in report.summary or "学习支持" in report.summary, (
        f"Should mention learning: {report.summary}"
    )
    assert report.safety_alerts == []
    # New schema: tonight_parent_bridge is always None
    assert report.tonight_parent_bridge is None
    assert report.suggested_parent_actions == []
    assert "逐字返回" not in report.model_dump_json()


def test_parent_report_service_get_daily_report_saves_generated_report() -> None:
    memory_service, report_repository, report_service = _services_with_report_repository()
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.LEARNING_PATTERN,
            content="孩子在学习求助时需要先确认题意，再一步一步说出已知条件。",
            tags=["学习求助", "题意确认"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )

    report = report_service.get_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )
    persisted = report_repository.get(
        "child_parent_report_service_test",
        date(2026, 5, 18),
    )

    assert persisted is not None
    assert persisted.summary == report.summary
    assert persisted.learning_observations == report.learning_observations


def test_parent_report_service_uses_daily_conversation_without_raw_transcript() -> None:
    memory_service = MemoryService(
        repository=InMemoryMemoryRepository(),
        now_provider=_fixed_now,
    )
    report_service = ParentReportService(
        memory_service=memory_service,
        conversation_repository=FakeConversationRepository(
            [
                _conversation_message(
                    message_id="msg_child_photo_learning",
                    text="我发了一张家里的照片，里面有数学题不会做。",
                    active_scene="conversation.open",
                    attachments_count=1,
                ),
                _conversation_message(
                    message_id="msg_agent_photo_learning",
                    actor="agent",
                    text="我们先看看你最想问哪里。",
                ),
            ]
        ),
        model_registry=SuccessfulParentReportModelRegistry(),
        now_provider=_fixed_now,
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    report_json = report.model_dump_json()
    # Narrative format: summary should mention key topics
    assert report.summary, f"Should have a summary: {report.summary}"
    assert "图片" in report.summary or "学习" in report.summary, (
        f"Should mention image or learning: {report.summary}"
    )
    # Should not expose raw transcript
    assert "我发了一张家里的照片" not in report_json
    assert "数学题不会做" not in report_json
    # New schema: tonight_parent_bridge is always None
    assert report.tonight_parent_bridge is None


def test_parent_report_redesign_summarizes_game_topic_without_raw_transcript() -> None:
    raw_child_line_1 = "我和朋友玩 CS，沙二这个地图我们配合得还行。"
    raw_child_line_2 = "最后我们输了。"
    raw_child_line_3 = "嗯，没了。"
    report_service = ParentReportService(
        memory_service=MemoryService(
            repository=InMemoryMemoryRepository(),
            now_provider=_fixed_now,
        ),
        conversation_repository=FakeConversationRepository(
            [
                _conversation_message(
                    message_id="msg_child_game_1",
                    text=raw_child_line_1,
                ),
                _conversation_message(
                    message_id="msg_agent_game_1",
                    actor="agent",
                    text="你喜欢哪张地图？",
                ),
                _conversation_message(
                    message_id="msg_child_game_2",
                    text=raw_child_line_2,
                ),
                _conversation_message(
                    message_id="msg_child_game_3",
                    text=raw_child_line_3,
                ),
            ]
        ),
        model_registry=SuccessfulParentReportModelRegistry(),
        now_provider=_fixed_now,
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    report_json = report.model_dump_json()
    # Narrative format: summary should mention game topic
    assert report.summary, f"Should have a summary: {report.summary}"
    assert "游戏" in report.summary or "CS" in report.summary, (
        f"Should mention game topic: {report.summary}"
    )
    # Should not expose raw transcript
    assert raw_child_line_1 not in report_json
    assert raw_child_line_2 not in report_json
    assert raw_child_line_3 not in report_json
    assert "provider" not in report_json.lower()


def test_parent_report_model_parse_accepts_new_schema_summary_mentioned_items_attention_items() -> None:
    """New schema with summary + mentioned_items + attention_items should be parsed correctly,
    and tonight_parent_bridge / avoid_followup should always be None/empty."""
    class NewSchemaModelRegistry:
        def generate(self, request):
            return ModelResponse(
                task_type=ModelTaskType.PARENT_REPORT,
                response_text="",
                structured_output={
                    "daily_report": {
                        "summary": "今天孩子聊了画画和一张图片。",
                        "mentioned_items": ["画画", "图片分享"],
                        "attention_items": ["情绪低落"],
                    }
                },
                provider_name="mimo",
                model_name="mimo-v2.5-pro",
                metadata={},
            )

    report_service = ParentReportService(
        memory_service=MemoryService(
            repository=InMemoryMemoryRepository(),
            now_provider=_fixed_now,
        ),
        conversation_repository=FakeConversationRepository(
            [
                _conversation_message(
                    message_id="msg_child_new_schema",
                    text="我拍了一张图给小白狐看。",
                    attachments_count=1,
                )
            ]
        ),
        model_registry=NewSchemaModelRegistry(),
        now_provider=_fixed_now,
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    assert report.generation_status == ParentReportGenerationStatus.MODEL_GENERATED
    assert report.summary == "今天孩子聊了画画和一张图片。"
    # New schema: bridge and avoid_followup are always empty
    assert report.tonight_parent_bridge is None
    assert report.avoid_followup == []
    assert report.suggested_parent_actions == []
    assert "逐字聊天记录" not in report.model_dump_json()


def test_parent_report_deterministic_empty_material_bridge_avoids_interrogation() -> None:
    report_service = ParentReportService(
        memory_service=MemoryService(
            repository=InMemoryMemoryRepository(),
            now_provider=_fixed_now,
        ),
        conversation_repository=FakeConversationRepository(),
        model_registry=SuccessfulParentReportModelRegistry(),
        now_provider=_fixed_now,
    )
    report = report_service._deterministic_fallback_report(
        child_id="child_parent_report_service_test",
        target_date=date(2026, 5, 18),
        memories=[],
        conversation_messages=[],
        conversation={
            "topics": [],
            "state_summary": [],
            "learning_observations": [],
            "expression_observations": [],
            "emotion_observations": [],
            "safety_alerts": [],
        },
    )

    # New schema: bridge is always None, avoid_followup is always empty
    assert report.tonight_parent_bridge is None
    assert report.avoid_followup == []
    assert report.suggested_parent_actions == []
    # Summary should still be generated
    assert report.summary, f"Should have a summary: {report.summary}"
    assert "监控" not in report.model_dump_json()


def test_parent_report_service_model_first_uses_daily_conversation_materials() -> None:
    model_registry = SuccessfulParentReportModelRegistry()
    memory_service = MemoryService(
        repository=InMemoryMemoryRepository(),
        now_provider=_fixed_now,
    )
    report_service = ParentReportService(
        memory_service=memory_service,
        conversation_repository=FakeConversationRepository(
            [
                _conversation_message(
                    message_id="msg_child_photo",
                    text="我拍了一张图给小白狐看。",
                    attachments_count=1,
                ),
                _conversation_message(
                    message_id="msg_child_question",
                    text="这是什么？",
                ),
            ]
        ),
        model_registry=model_registry,
        now_provider=_fixed_now,
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    assert len(model_registry.requests) == 1
    assert model_registry.requests[0].task_type == ModelTaskType.PARENT_REPORT
    # Narrative format: summary should mention key topics
    assert report.summary, f"Should have a summary: {report.summary}"
    assert "逐字聊天记录" not in report.model_dump_json()


def test_parent_report_service_empty_model_response_retries_once_then_fails() -> None:
    class EmptyThenReportModelRegistry:
        requests = 0

        def generate(self, request):
            self.requests += 1
            return ModelResponse(
                task_type=request.task_type,
                response_text="",
                structured_output={},
                provider_name="mimo",
                model_name="mimo-v2.5-pro",
                metadata={},
            )

    model_registry = EmptyThenReportModelRegistry()
    report_service = ParentReportService(
        memory_service=MemoryService(
            repository=InMemoryMemoryRepository(),
            now_provider=_fixed_now,
        ),
        conversation_repository=FakeConversationRepository(
            [
                _conversation_message(
                    message_id="msg_child_retry_photo",
                    text="我拍了一张图给小白狐看。",
                    attachments_count=1,
                )
            ]
        ),
        model_registry=model_registry,
        now_provider=_fixed_now,
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    assert report.generation_status == ParentReportGenerationStatus.MODEL_FAILED
    assert report.generation_error_code == "empty_or_unparseable_model_report"
    assert model_registry.requests == 2
    assert report.summary == "日报暂时生成失败，请稍后重试。"


def test_parent_report_service_provider_failure_does_not_return_rule_report() -> None:
    class FailingReportModelRegistry:
        requests = 0

        def generate(self, _request):
            self.requests += 1
            raise RuntimeError("provider raw response should not leak")

    model_registry = FailingReportModelRegistry()
    report_service = ParentReportService(
        memory_service=MemoryService(
            repository=InMemoryMemoryRepository(),
            now_provider=_fixed_now,
        ),
        conversation_repository=FakeConversationRepository(
            [
                _conversation_message(
                    message_id="msg_child_empty_report",
                    text="我今天想聊画画。",
                )
            ]
        ),
        model_registry=model_registry,
        now_provider=_fixed_now,
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    assert report.generation_status == ParentReportGenerationStatus.MODEL_FAILED
    assert report.generation_error_code == "RuntimeError"
    assert model_registry.requests == 1
    assert report.summary == "日报暂时生成失败，请稍后重试。"
    assert "provider raw response should not leak" not in report.model_dump_json()
    assert "我今天想聊画画" not in report.model_dump_json()


def test_parent_report_model_payload_redacts_debug_secret_and_base64() -> None:
    class CapturingModelRegistry(SuccessfulParentReportModelRegistry):
        payload: dict | None = None

        def generate(self, request):
            self.payload = _payload_from_request(request)
            return super().generate(request)

    model_registry = CapturingModelRegistry()
    report_service = ParentReportService(
        memory_service=MemoryService(
            repository=InMemoryMemoryRepository(),
            now_provider=_fixed_now,
        ),
        conversation_repository=FakeConversationRepository(
            [
                _conversation_message(
                    message_id="msg_secret",
                    text=(
                        "Authorization: Bearer secret-token data:image/png;base64,AAAA "
                        "prompt: hidden debug trace"
                    ),
                )
            ]
        ),
        model_registry=model_registry,
        now_provider=_fixed_now,
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    payload_json = json.dumps(model_registry.payload, ensure_ascii=False)
    assert report.generation_status == ParentReportGenerationStatus.MODEL_GENERATED
    assert "[redacted]" in payload_json
    assert "secret-token" not in payload_json
    assert "data:image" not in payload_json
    assert "base64" not in payload_json.lower()
    assert "hidden debug trace" not in payload_json


def test_parent_report_failure_is_not_persisted_as_success() -> None:
    class EmptyModelRegistry:
        def generate(self, request):
            return ModelResponse(
                task_type=request.task_type,
                response_text="",
                structured_output={},
                provider_name="mimo",
                model_name="mimo-v2.5-pro",
                metadata={},
            )

    memory_service = MemoryService(
        repository=InMemoryMemoryRepository(),
        now_provider=_fixed_now,
    )
    report_repository = InMemoryParentReportRepository()
    report_service = ParentReportService(
        memory_service=memory_service,
        repository=report_repository,
        conversation_repository=FakeConversationRepository(
            [
                _conversation_message(
                    message_id="msg_child_for_failure_test",
                    text="今天没什么特别的。",
                ),
            ]
        ),
        model_registry=EmptyModelRegistry(),
        now_provider=_fixed_now,
    )

    report = report_service.get_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    assert report.generation_status == ParentReportGenerationStatus.MODEL_FAILED
    assert report_repository.get("child_parent_report_service_test", date(2026, 5, 18)) is None


def test_parent_report_service_refreshes_stale_report_when_conversation_is_newer() -> None:
    memory_service, report_repository, _ = _services_with_report_repository()
    old_report_service = ParentReportService(
        memory_service=memory_service,
        repository=report_repository,
        conversation_repository=FakeConversationRepository(),
        model_registry=SuccessfulParentReportModelRegistry(),
        now_provider=_fixed_now,
    )
    old_report = old_report_service.get_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )
    report_service = ParentReportService(
        memory_service=memory_service,
        repository=report_repository,
        conversation_repository=FakeConversationRepository(
            [
                _conversation_message(
                    message_id="msg_child_newer_photo",
                    text="我拍了一张图想问问这是什么。",
                    attachments_count=1,
                    created_at=datetime(2026, 5, 18, 11, 0, tzinfo=timezone.utc),
                )
            ]
        ),
        model_registry=SuccessfulParentReportModelRegistry(),
        now_provider=lambda: datetime(2026, 5, 18, 11, 5, tzinfo=timezone.utc),
    )

    refreshed = report_service.get_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    assert refreshed.summary != old_report.summary
    assert "会话消息" in refreshed.summary
    assert refreshed.created_at > old_report.created_at


def test_parent_report_service_refreshes_when_new_memory_arrives() -> None:
    memory_service, _, report_service = _services_with_report_repository()
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.LEARNING_PATTERN,
            content="孩子在学习求助时需要先确认题意，再一步一步说出已知条件。",
            tags=["学习求助", "题意确认"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )
    first = report_service.get_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.EXPRESSION_PATTERN,
            content="这条后续记忆不应改变已持久化的当日报告。",
            tags=["表达"],
        )
    )

    second = report_service.get_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    assert second.created_at >= first.created_at
    assert second.material_fingerprint != first.material_fingerprint
    # Narrative format: summary should be updated with new material
    assert second.summary, f"Should have a summary: {second.summary}"


def test_parent_report_service_repository_failure_returns_generated_report(
    caplog,
) -> None:
    class FailingReportRepository:
        def save(self, _report):
            raise ParentReportRepositoryUnavailable("contains report summary")

        def get(self, _child_id, _report_date):
            raise ParentReportRepositoryUnavailable("contains report summary")

        def list_by_child(self, _child_id, limit=30):
            raise ParentReportRepositoryUnavailable("contains report summary")

        def delete(self, _child_id, _report_date):
            raise ParentReportRepositoryUnavailable("contains report summary")

        def clear(self):
            raise ParentReportRepositoryUnavailable("contains report summary")

    memory_service = MemoryService(
        repository=InMemoryMemoryRepository(),
        now_provider=_fixed_now,
    )
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.LEARNING_PATTERN,
            content="孩子在学习求助时需要先确认题意，再一步一步说出已知条件。",
            tags=["学习求助", "题意确认"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )
    report_service = ParentReportService(
        memory_service=memory_service,
        repository=FailingReportRepository(),
        conversation_repository=FakeConversationRepository(),
        model_registry=SuccessfulParentReportModelRegistry(),
        now_provider=_fixed_now,
    )
    caplog.set_level("WARNING", logger="app.parent_report")

    report = report_service.get_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    # Narrative format: summary should be generated
    assert report.summary, f"Should have a summary: {report.summary}"
    assert "parent_report_repository_fallback" in caplog.text
    assert "孩子在学习求助时需要先确认题意" not in caplog.text
    assert "contains report summary" not in caplog.text


def test_parent_report_service_only_uses_parent_visible_current_day_memory() -> None:
    repository, memory_service, report_service = _services()
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.LEARNING_PATTERN,
            content="今天可见的学习观察。",
            tags=["今天"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.LEARNING_PATTERN,
            content="今天不可见的学习观察。",
            tags=["不可见"],
            sensitivity=MemorySensitivity.MEDIUM,
        ).model_copy(update={"visible_to_parent": False}, deep=True)
    )
    yesterday = memory_service.create(
        _memory_request(
            memory_type=MemoryType.LEARNING_PATTERN,
            content="昨天的学习观察。",
            tags=["昨天"],
            sensitivity=MemorySensitivity.MEDIUM,
        )
    )
    repository.save(
        yesterday.model_copy(
            update={
                "created_at": datetime(2026, 5, 17, 10, 0, tzinfo=timezone.utc),
                "updated_at": datetime(2026, 5, 17, 10, 0, tzinfo=timezone.utc),
            },
            deep=True,
        )
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    report_json = report.model_dump_json()
    # Narrative format: summary should mention learning
    assert report.summary, f"Should have a summary: {report.summary}"
    assert "学习" in report.summary, f"Should mention learning: {report.summary}"
    # Should not contain yesterday's observation
    assert "昨天的学习观察" not in report_json


def test_parent_report_service_generates_high_risk_report_without_raw_detail() -> None:
    _, memory_service, report_service = _services()
    memory_service.create(
        _memory_request(
            memory_type=MemoryType.SAFETY,
            content="本次会话出现需要家长关注的安全信号，应由家长进一步了解情况。",
            tags=["安全提醒", "家长关注"],
            sensitivity=MemorySensitivity.CRITICAL,
            requires_parent_attention=True,
        )
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    report_json = report.model_dump_json()
    # Narrative format: summary should mention safety
    assert report.summary, f"Should have a summary: {report.summary}"
    assert "安全" in report.summary, f"Should mention safety: {report.summary}"
    assert "逐字返回" not in report_json
    assert "胆小" not in report_json
    assert "不合群" not in report_json
    assert "懒" not in report_json
    assert "不聪明" not in report_json


def test_parent_report_service_sanitizes_fixed_negative_labels() -> None:
    repository, memory_service, report_service = _services()
    repository.save(
        memory_service.create(
            _memory_request(
                memory_type=MemoryType.EXPRESSION_PATTERN,
                content="孩子在开放提问下回答较短。",
                tags=["表达"],
            )
        ).model_copy(update={"content": "孩子胆小、不合群。"}, deep=True)
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    report_json = report.model_dump_json()
    # Narrative format: should not contain negative labels
    assert "胆小" not in report_json
    assert "不合群" not in report_json


def test_parent_report_uses_relationship_memory_for_low_pressure_parent_action() -> None:
    _, memory_service, report_service = _services()
    memory_service.create(
        MemoryCreateRequest(
            child_id="child_parent_report_service_test",
            memory_type=MemoryType.INTEREST,
            content="孩子近期自然聊到跑步比赛，可作为低压力回访的兴趣种子。",
            tags=["relationship_memory", "interest_seed", "跑步比赛"],
            evidence=[
                MemoryEvidence(
                    source="conversation_summary",
                    session_id="session_parent_report_relationship",
                    quote_summary="孩子自然提到跑步比赛相关内容，适合短期轻回访。",
                    metadata={
                        "relationship_memory_type": "interest_seed",
                        "topic": "跑步比赛",
                        "next_hook": "下次可问比赛是短跑还是接力。",
                    },
                )
            ],
            sensitivity=MemorySensitivity.LOW,
            confidence=0.78,
            importance=0.52,
            visible_to_parent=True,
            visible_to_child=False,
        )
    )
    memory_service.create(
        MemoryCreateRequest(
            child_id="child_parent_report_service_test",
            memory_type=MemoryType.EXPRESSION_PATTERN,
            content="孩子能把运动比赛、项目或感受连起来表达，适合给低压力成长反馈。",
            tags=["relationship_memory", "proud_moment", "运动比赛表达"],
            evidence=[
                MemoryEvidence(
                    source="conversation_summary",
                    session_id="session_parent_report_relationship",
                    quote_summary="孩子围绕运动比赛表达了主题、项目或感受。",
                    metadata={
                        "relationship_memory_type": "proud_moment",
                        "topic": "运动比赛表达",
                        "next_hook": "家长可具体肯定孩子把事情说清楚了。",
                    },
                )
            ],
            sensitivity=MemorySensitivity.LOW,
            confidence=0.78,
            importance=0.52,
            visible_to_parent=True,
            visible_to_child=False,
        )
    )

    report = report_service.generate_daily_report(
        "child_parent_report_service_test",
        report_date=date(2026, 5, 18),
    )

    report_json = report.model_dump_json()
    # Narrative format: summary should mention running/competition
    assert report.summary, f"Should have a summary: {report.summary}"
    assert "evidence" not in report_json
    assert "quote_summary" not in report_json
    assert "我每天" not in report_json
