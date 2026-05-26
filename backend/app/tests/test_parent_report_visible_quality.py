"""Parent Report v2 visible quality tests (Task 21).

Verifies:
  1. report fallback mentions match/competition, image/object/show-and-tell, English check-in when those materials exist.
  2. report uses support_style ask_fewer_questions by recommending one small question or not追问.
  3. report respects boundary "不要追问比赛输赢".
  4. report does not contain internal words: 接一句, 桥接, 结构化摘要, 表达入口.
  5. report does not expose raw transcript.
  6. model payload includes relationship_memory_type or equivalent safe memory type marker.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from app.domain.memory import (
    MemoryEvidence,
    MemoryItem,
    MemorySensitivity,
    MemoryType,
)
from app.domain.model_types import ModelResponse
from app.repositories.conversation_persistence_repository import ConversationReportMessage
from app.domain.schemas.parent_policy import ParentPolicy
from app.repositories.memory_repository import InMemoryMemoryRepository
from app.services.memory_service import MemoryService
from app.services.parent_report_service import ParentReportService
from app.services.relationship_memory import (
    INTEREST_SEED,
    SHOW_AND_TELL_EVENT,
    UNFINISHED_THREAD,
    relationship_metadata,
)


FIXED_NOW = datetime(2026, 5, 26, 20, 0, tzinfo=timezone.utc)

CHILD_ID = "child_report_quality"
TARGET_DATE = date(2026, 5, 26)

# Internal words that must never appear in parent-facing report
INTERNAL_WORDS = ("接一句", "桥接", "结构化摘要", "表达入口")

# Raw transcript fragments that should NOT be exposed
RAW_TRANSCRIPT = ("比赛前有点紧张", "我跑得很快", "英语打卡好难")


def _make_memory(
    memory_id: str,
    content: str,
    *,
    memory_type: MemoryType = MemoryType.EVENT,
    relationship_type: str | None = None,
) -> MemoryItem:
    evidence_meta: dict[str, Any] = {}
    if relationship_type:
        evidence_meta.update(relationship_metadata(
            relationship_memory_type=relationship_type,
            topic=content[:20],
        ))
    return MemoryItem(
        id=memory_id,
        child_id=CHILD_ID,
        memory_type=memory_type,
        content=content,
        tags=[],
        evidence=[
            MemoryEvidence(
                source="test",
                quote_summary=content[:50],
                metadata=evidence_meta,
            )
        ],
        confidence=0.9,
        importance=0.5,
        sensitivity=MemorySensitivity.LOW,
        visible_to_parent=True,
        visible_to_child=False,
        requires_parent_attention=False,
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
    )


def _make_parent_policy(**overrides: Any) -> ParentPolicy:
    base: dict[str, Any] = {
        "child_id": CHILD_ID,
        "child_nickname": "航航",
        "child_display_name": None,
        "parent_message_raw": None,
        "communication_preferences": {
            "child_age": 7,
            "child_interests": ["跑步比赛", "画画"],
            "topic_boundaries": ["不要追问比赛输赢"],
            "support_style_preferences": ["ask_fewer_questions"],
        },
        "created_at": FIXED_NOW,
        "updated_at": FIXED_NOW,
    }
    base.update(overrides)
    return ParentPolicy(**base)


def _make_conversation_message(
    actor: str,
    text: str,
    *,
    active_scene: str = "open_conversation",
    attachments: int = 0,
) -> ConversationReportMessage:
    return ConversationReportMessage(
        id=f"msg_{actor}_{hash(text) % 10000}",
        session_id="report_quality_session",
        actor=actor,
        message_type="text",
        normalized_text=text,
        active_scene=active_scene,
        risk_level=None,
        attachments_count=attachments,
        created_at=FIXED_NOW,
    )


def _build_report(
    *,
    memories: list[MemoryItem] | None = None,
    conversation_messages: list[ConversationReportMessage] | None = None,
    parent_policy: ParentPolicy | None = None,
) -> tuple[Any, dict[str, list[str]]]:
    repo = InMemoryMemoryRepository()
    memory_service = MemoryService(repository=repo)

    # Store memories if provided
    if memories:
        for mem in memories:
            repo.save(mem)

    pp = parent_policy or _make_parent_policy()

    # Create a stub parent policy service
    class _StubPolicyService:
        def get_policy(self, child_id: str) -> ParentPolicy:
            return pp

    service = ParentReportService(
        parent_policy_service=_StubPolicyService(),
        memory_service=memory_service,
        model_registry=None,
        now_provider=lambda: FIXED_NOW,
    )

    msgs = conversation_messages or []
    conversation = service._conversation_analysis(msgs)
    fallback = service._deterministic_fallback_report(
        child_id=CHILD_ID,
        target_date=TARGET_DATE,
        memories=memories or [],
        conversation_messages=msgs,
        conversation=conversation,
        support_style=["ask_fewer_questions"],
    )
    return fallback, conversation


# --- Test 1: report fallback mentions match, show-and-tell, English check-in ---


def test_report_fallback_mentions_session_materials() -> None:
    """When session has match/competition, show-and-tell, and unfinished thread,
    the fallback report should mention them."""
    memories = [
        _make_memory(
            "mem_match",
            "孩子今天聊了跑步比赛的感受",
            relationship_type=INTEREST_SEED,
        ),
        _make_memory(
            "mem_show_tell",
            "孩子展示了一幅自己画的小狐狸",
            relationship_type=SHOW_AND_TELL_EVENT,
        ),
        _make_memory(
            "mem_thread",
            "孩子说要去英语打卡",
            relationship_type=UNFINISHED_THREAD,
        ),
    ]

    conversation_messages = [
        _make_conversation_message("child", "我今天跑步比赛了"),
        _make_conversation_message("agent", "跑步比赛感觉怎么样？"),
        _make_conversation_message("child", "我要去英语打卡了"),
    ]

    fallback, _ = _build_report(
        memories=memories,
        conversation_messages=conversation_messages,
    )

    summary = fallback.summary or ""
    # Should mention running/match
    assert any(
        word in summary for word in ("跑步", "比赛", "运动")
    ), f"Should mention match: {summary}"
    # Should mention show-and-tell or drawing
    assert any(
        word in summary for word in ("画", "展示", "给小白狐看")
    ), f"Should mention show-and-tell: {summary}"
    # Should mention unfinished thread (打卡/做别的事)
    assert any(
        word in summary for word in ("打卡", "做别的事")
    ), f"Should mention unfinished thread: {summary}"


# --- Test 2: support_style ask_fewer_questions ---


def test_report_uses_ask_fewer_questions_support_style() -> None:
    """With ask_fewer_questions support style, report should recommend
    one small question or not追问."""
    memories = [
        _make_memory(
            "mem_interest",
            "孩子今天聊了画画",
            relationship_type=INTEREST_SEED,
        ),
    ]

    conversation_messages = [
        _make_conversation_message("child", "我今天画画了"),
        _make_conversation_message("agent", "画了什么呀？"),
        _make_conversation_message("child", "画了一只小狐狸"),
    ]

    fallback, _ = _build_report(
        memories=memories,
        conversation_messages=conversation_messages,
    )

    bridge = fallback.tonight_parent_bridge or ""
    actions = fallback.suggested_parent_actions or []

    # With ask_fewer_questions, bridge should recommend gentle approach
    assert any(
        phrase in bridge
        for phrase in ("轻轻", "一句", "不用多问", "不用追问", "一个就好", "不追问")
    ), f"Should recommend gentle approach: {bridge}"

    # Actions should include advice about not追问
    all_text = bridge + " ".join(actions)
    assert any(
        phrase in all_text
        for phrase in ("不要追问", "少追问", "不追问", "轻轻问", "一个就好")
    ), f"Should advise gentle approach: bridge={bridge}, actions={actions}"


# --- Test 3: report respects boundary "不要追问比赛输赢" ---


def test_report_respects_boundary_no_followup_on_match_result() -> None:
    """With boundary '不要追问比赛输赢', report should advise against
    asking about win/loss/ranking."""
    memories = [
        _make_memory(
            "mem_sports",
            "孩子今天聊了跑步比赛",
            relationship_type=INTEREST_SEED,
        ),
    ]

    conversation_messages = [
        _make_conversation_message("child", "我今天有跑步比赛"),
        _make_conversation_message("agent", "跑步比赛呀，感觉怎么样？"),
        _make_conversation_message("child", "还行吧"),
    ]

    fallback, _ = _build_report(
        memories=memories,
        conversation_messages=conversation_messages,
    )

    avoid = fallback.avoid_followup or []
    all_avoid = " ".join(avoid)

    # Should advise against追问比赛输赢
    assert any(
        phrase in all_avoid
        for phrase in ("不要追问", "输赢", "排名", "赢了吗", "第几")
    ), f"Should advise against追问比赛结果: {avoid}"


# --- Test 4: report does not contain internal words ---


def test_report_does_not_contain_internal_words() -> None:
    """Report text must not contain internal product words."""
    memories = [
        _make_memory(
            "mem_internal",
            "孩子今天聊了画画",
            relationship_type=INTEREST_SEED,
        ),
    ]

    conversation_messages = [
        _make_conversation_message("child", "我画了一幅画"),
        _make_conversation_message("agent", "画了什么呢？"),
        _make_conversation_message("child", "一只小猫"),
    ]

    fallback, _ = _build_report(
        memories=memories,
        conversation_messages=conversation_messages,
    )

    all_text = " ".join([
        fallback.summary or "",
        fallback.tonight_parent_bridge or "",
        " ".join(fallback.suggested_parent_actions or []),
        " ".join(fallback.avoid_followup or []),
    ])

    for word in INTERNAL_WORDS:
        assert word not in all_text, f"Internal word '{word}' found in report: {all_text}"


# --- Test 5: report does not expose raw transcript ---


def test_report_does_not_expose_raw_transcript() -> None:
    """Report should not contain raw child transcript fragments."""
    conversation_messages = [
        _make_conversation_message("child", "比赛前有点紧张"),
        _make_conversation_message("agent", "紧张是正常的。"),
        _make_conversation_message("child", "我跑得很快"),
    ]

    fallback, _ = _build_report(
        memories=[],
        conversation_messages=conversation_messages,
    )

    all_text = " ".join([
        fallback.summary or "",
        fallback.tonight_parent_bridge or "",
        " ".join(fallback.suggested_parent_actions or []),
    ])

    # The deterministic fallback should not contain verbatim child transcript
    for fragment in RAW_TRANSCRIPT:
        assert fragment not in all_text, f"Raw transcript '{fragment}' found in report: {all_text}"


# --- Test 6: model payload includes relationship_memory_type ---


def test_model_payload_includes_relationship_memory_type() -> None:
    """The model payload memory_summaries should include relationship_memory_type
    when available."""
    repo = InMemoryMemoryRepository()
    memory_service = MemoryService(repository=repo)

    mem = _make_memory(
        "mem_payload",
        "孩子展示了一幅自己画的小狐狸",
        relationship_type=SHOW_AND_TELL_EVENT,
    )
    repo.save(mem)

    pp = _make_parent_policy()

    class _StubPolicyService:
        def get_policy(self, child_id: str) -> ParentPolicy:
            return pp

    # Stub model registry that captures the payload
    captured_payload: dict[str, Any] = {}

    class _CapturingModelRegistry:
        def generate(self, request: Any) -> ModelResponse:
            import json
            content = request.messages[-1].content
            captured_payload.update(json.loads(content))
            return ModelResponse(
                response_text='{"summary": "test"}',
                structured_output={"daily_report": '{"summary": "test"}'},
                model_ms=100,
            )

    service = ParentReportService(
        parent_policy_service=_StubPolicyService(),
        memory_service=memory_service,
        model_registry=_CapturingModelRegistry(),
        now_provider=lambda: FIXED_NOW,
    )

    # Call the model payload method directly
    conversation_messages = [
        _make_conversation_message("child", "你看这个"),
    ]
    conversation = service._conversation_analysis(conversation_messages)

    from app.services.parent_report_service import ParentReport, ParentReportGenerationStatus
    fallback_report = ParentReport(
        child_id=CHILD_ID,
        date=TARGET_DATE,
        summary="测试摘要",
        topic_overview=[],
        conversation_summary=None,
        learning_observations=[],
        expression_observations=[],
        emotion_observations=[],
        safety_alerts=[],
        suggested_parent_actions=[],
        tonight_parent_bridge="今晚可以轻轻聊",
        avoid_followup=[],
        created_at=FIXED_NOW,
        generation_status=ParentReportGenerationStatus.DETERMINISTIC_FALLBACK,
        generated_by="test",
        generation_error_code=None,
        material_fingerprint="test_fp",
    )

    payload = service._parent_report_model_payload(
        target_date=TARGET_DATE,
        memories=[mem],
        conversation_messages=conversation_messages,
        conversation=conversation,
        fallback_report=fallback_report,
        support_style=["ask_fewer_questions"],
        topic_boundaries=["不要追问比赛输赢"],
    )

    # Check memory_summaries has relationship_memory_type
    memory_summaries = payload.get("memory_summaries", [])
    assert len(memory_summaries) >= 1, "Should have memory summaries"
    summary = memory_summaries[0]
    assert summary.get("relationship_memory_type") == SHOW_AND_TELL_EVENT, (
        f"Should include relationship_memory_type: {summary}"
    )

    # Check topic_boundaries is included
    assert payload.get("topic_boundaries") == ["不要追问比赛输赢"], (
        f"Should include topic_boundaries: {payload.get('topic_boundaries')}"
    )

    # Check support_style_preferences is included
    assert payload.get("support_style_preferences") == ["ask_fewer_questions"], (
        f"Should include support_style_preferences: {payload.get('support_style_preferences')}"
    )


# --- Additional: fallback with no materials ---


def test_fallback_with_no_materials() -> None:
    """When there are no memories and no conversation, fallback should
    produce a safe generic report without crashing."""
    fallback, _ = _build_report(
        memories=[],
        conversation_messages=[],
    )

    assert fallback.summary, "Should have a summary even with no materials"
    assert fallback.generation_status.value == "deterministic_fallback"


# --- Additional: topic_boundaries lookup from parent policy ---


def test_topic_boundaries_sourced_from_parent_policy() -> None:
    """topic_boundaries should be sourced from parent policy communication_preferences."""
    repo = InMemoryMemoryRepository()
    memory_service = MemoryService(repository=repo)

    pp = _make_parent_policy(
        communication_preferences={
            "child_age": 7,
            "topic_boundaries": ["不要追问比赛输赢", "不要聊恐怖故事"],
        },
    )

    class _StubPolicyService:
        def get_policy(self, child_id: str) -> ParentPolicy:
            return pp

    service = ParentReportService(
        parent_policy_service=_StubPolicyService(),
        memory_service=memory_service,
        model_registry=None,
        now_provider=lambda: FIXED_NOW,
    )

    boundaries = service._lookup_topic_boundaries(CHILD_ID)
    assert boundaries == ["不要追问比赛输赢", "不要聊恐怖故事"], (
        f"Should lookup from parent policy: {boundaries}"
    )
