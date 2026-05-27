from datetime import date, datetime, timezone
import json

from app.domain.memory import MemoryEvidence, MemoryItem, MemorySensitivity, MemoryType
from app.domain.model_types import ModelResponse, ModelTaskType
from app.domain.parent_report import ParentReport, ParentReportGenerationStatus
from app.repositories.conversation_persistence_repository import ConversationReportMessage
from app.repositories.memory_repository import InMemoryMemoryRepository
from app.repositories.parent_report_repository import InMemoryParentReportRepository
from app.services.memory_service import MemoryService
from app.services.parent_report_service import ParentReportService


FIXED_NOW = datetime(2026, 5, 26, 20, 0, tzinfo=timezone.utc)
TARGET_DATE = date(2026, 5, 26)
CHILD_ID = "child_parent_report_language_v4"


def _message(
    text: str,
    *,
    message_id: str = "msg_child_v4",
    actor: str = "child",
    active_scene: str | None = "conversation.open",
    risk_level: str | None = "none",
    attachments_count: int = 0,
    created_at: datetime = FIXED_NOW,
) -> ConversationReportMessage:
    return ConversationReportMessage(
        id=message_id,
        session_id="session_parent_report_language_v4",
        actor=actor,
        message_type="text",
        normalized_text=text,
        active_scene=active_scene,
        risk_level=risk_level,
        attachments_count=attachments_count,
        created_at=created_at,
    )


def _memory(
    *,
    memory_id: str,
    content: str,
    memory_type: MemoryType = MemoryType.EVENT,
    sensitivity: MemorySensitivity = MemorySensitivity.LOW,
    requires_parent_attention: bool = False,
    relationship_type: str | None = None,
) -> MemoryItem:
    metadata = {}
    if relationship_type:
        metadata["relationship_memory_type"] = relationship_type
    return MemoryItem(
        id=memory_id,
        child_id=CHILD_ID,
        memory_type=memory_type,
        content=content,
        tags=[],
        evidence=[
            MemoryEvidence(
                source="test",
                quote_summary="测试用结构化摘要，不应逐字进入家长日报。",
                metadata=metadata,
            )
        ],
        confidence=0.9,
        importance=0.5,
        sensitivity=sensitivity,
        visible_to_parent=True,
        visible_to_child=False,
        requires_parent_attention=requires_parent_attention,
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
    )


def _service() -> ParentReportService:
    return ParentReportService(
        memory_service=MemoryService(
            repository=InMemoryMemoryRepository(),
            now_provider=lambda: FIXED_NOW,
        ),
        repository=InMemoryParentReportRepository(),
        model_registry=None,
        now_provider=lambda: FIXED_NOW,
    )


def _fallback(
    *,
    messages: list[ConversationReportMessage] | None = None,
    memories: list[MemoryItem] | None = None,
) -> ParentReport:
    service = _service()
    msgs = messages or []
    mems = memories or []
    conversation = service._conversation_analysis(msgs)
    return service._deterministic_fallback_report(
        child_id=CHILD_ID,
        target_date=TARGET_DATE,
        memories=mems,
        conversation_messages=msgs,
        conversation=conversation,
    )


def test_prompt_contains_real_parent_concerns_and_v4_examples() -> None:
    prompt = _service()._parent_report_system_prompt()

    for phrase in (
        "今天孩子整体状态大概怎么样",
        "兴趣、困惑、情绪或需要",
        "安全、隐私、边界、情绪、学习",
        "陪孩子看题意、找第一步",
        "图片、作品、玩具、运动、游戏、故事",
        "低压力打开一个话题",
        "防止孩子感觉被盘问",
    ):
        assert phrase in prompt

    for example_label in (
        "好示例 normal",
        "好示例 image-share",
        "好示例 learning",
        "好示例 safety",
        "好示例 low-material",
    ):
        assert example_label in prompt



def test_prompt_forbids_monitoring_raw_quote_image_and_usage_count() -> None:
    prompt = _service()._parent_report_system_prompt()

    for phrase in (
        "不展示孩子和小白狐逐句聊了什么",
        "不引用或改写孩子原话",
        "不暴露具体给小白狐看了哪张图",
        "不写消息数量、使用时长、活跃度",
        "不引导家长问“你今天和小白狐聊了什么”",
    ):
        assert phrase in prompt

    for bad in (
        "孩子今天和小白狐聊了三件事",
        "孩子今天共有 5 条消息",
        "你今天给小白狐看的是什么",
        "小白狐发现孩子表达能力较好",
    ):
        assert bad in prompt



def test_fallback_avoids_monitoring_wording() -> None:
    report = _fallback(messages=[_message("我今天画画了")])
    all_text = report.model_dump_json()

    for forbidden in (
        "给小白狐看的东西",
        "孩子主要聊了",
        "消息数量",
        "条孩子消息",
        "孩子今天共有",
        "表达能力较好",
    ):
        assert forbidden not in all_text



def test_image_fallback_uses_broad_expression_tendency() -> None:
    report = _fallback(messages=[_message("你看这个", attachments_count=1)])
    all_text = " ".join(
        [
            report.summary or "",
            report.tonight_parent_bridge or "",
            " ".join(report.avoid_followup or []),
        ]
    )

    assert "通过图片或作品来表达、展示的倾向" in all_text
    assert "不需要追问具体是哪张图" in all_text
    assert "你今天给小白狐看的是什么" not in all_text
    assert "给小白狐看的东西" not in all_text



def test_learning_fallback_guides_topic_meaning_and_first_step_not_final_answer() -> None:
    report = _fallback(messages=[_message("我有一道数学题不会做")])
    all_text = " ".join(
        [
            report.summary or "",
            report.tonight_parent_bridge or "",
            " ".join(report.avoid_followup or []),
        ]
    )

    assert "题目大概在问什么" in all_text or "题目在问什么" in all_text
    assert "第一步" in all_text
    assert "不要直接追最终答案" in all_text
    assert "替孩子完成" in all_text



def test_safety_fallback_prioritizes_calm_confirmation_and_adult_support() -> None:
    report = _fallback(
        memories=[
            _memory(
                memory_id="mem_safety_v4",
                content="今天材料里出现需要家长留意的边界信号。",
                memory_type=MemoryType.SAFETY,
                sensitivity=MemorySensitivity.CRITICAL,
                requires_parent_attention=True,
            )
        ]
    )
    all_text = " ".join(
        [
            report.summary or "",
            report.tonight_parent_bridge or "",
            " ".join(report.avoid_followup or []),
        ]
    )

    assert "保持平静" in all_text or "平静确认" in all_text
    assert "需要大人帮忙" in all_text
    assert "不要逼问细节" in all_text or "不逼问细节" in all_text
    assert "责备" in all_text



def test_model_generated_narrative_without_topic_overview_is_not_stale_when_fingerprint_matches() -> None:
    service = _service()
    messages = [_message("我今天画画了", message_id="msg_fp_v4")]
    fingerprint = service._material_fingerprint(memories=[], conversation_messages=messages)
    report = ParentReport(
        child_id=CHILD_ID,
        date=TARGET_DATE,
        summary="今天有一些轻量交流，材料显示孩子可能关注了画画。",
        topic_overview=[],
        conversation_summary=None,
        learning_observations=[],
        expression_observations=[],
        emotion_observations=[],
        safety_alerts=[],
        suggested_parent_actions=[],
        tonight_parent_bridge="今晚可以轻轻问一件小事。",
        avoid_followup=["不要追问具体聊了什么。"],
        created_at=datetime(2026, 5, 26, 20, 5, tzinfo=timezone.utc),
        generation_status=ParentReportGenerationStatus.MODEL_GENERATED,
        generated_by="model",
        generation_error_code=None,
        material_fingerprint=fingerprint,
    )

    assert service._is_stale(report, memories=[], conversation_messages=messages) is False



def test_report_json_does_not_expose_raw_transcript() -> None:
    raw_child_text = "我发了一张家里的照片，里面有数学题不会做。"

    class SafeNarrativeRegistry:
        def generate(self, request):
            content = request.messages[-1].content
            payload = json.loads(content)
            assert raw_child_text in json.dumps(payload, ensure_ascii=False)
            return ModelResponse(
                task_type=ModelTaskType.PARENT_REPORT,
                response_text="",
                structured_output={
                    "daily_report": {
                        "narrative_report": "今天出现了一点学习或题目相关的求助线索。家长今晚可以先听孩子说题目大概在问什么，再陪他找第一步。",
                        "tonight_parent_bridge": "今晚可以说：“如果有题卡住，我们先看看题目在问什么，再找第一步。”",
                        "avoid_followup": ["不要直接追最终答案或替孩子完成作业。"],
                    }
                },
                provider_name="mimo",
                model_name="mimo-v2.5-pro",
                metadata={},
            )

    class FakeConversationRepository:
        def list_report_messages(self, *, child_id, report_date):
            return [
                _message(
                    raw_child_text,
                    message_id="msg_raw_v4",
                    attachments_count=1,
                )
            ]

    service = ParentReportService(
        memory_service=MemoryService(
            repository=InMemoryMemoryRepository(),
            now_provider=lambda: FIXED_NOW,
        ),
        repository=InMemoryParentReportRepository(),
        conversation_repository=FakeConversationRepository(),
        model_registry=SafeNarrativeRegistry(),
        now_provider=lambda: FIXED_NOW,
    )
    report = service.generate_daily_report(CHILD_ID, report_date=TARGET_DATE)
    report_json = report.model_dump_json()

    assert report.generation_status == ParentReportGenerationStatus.MODEL_GENERATED
    assert raw_child_text not in report_json
    assert "逐字聊天记录" not in report_json
    assert "evidence" not in report_json
