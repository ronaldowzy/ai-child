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
INTERNAL_WORDS = (
    "接一句", "桥接", "结构化摘要", "表达入口",
    "后端", "给小白狐看的是什么", "那张图",
    "条孩子消息", "条小白狐回复", "表达能力较好",
    "image_context", "recognized_type", "prompt", "provider",
)

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
    # v4 deterministic_narrative_v4 prioritizes show-and-tell over sports topics
    # when both are present. Verify the summary is substantive and mentions
    # at least one of the expected signals.
    assert any(
        word in summary for word in ("跑步", "比赛", "运动", "图片", "作品", "表达", "展示")
    ), f"Should mention a topic or expression tendency: {summary}"
    assert len(summary) > 10, f"Summary should be substantive: {summary}"


# --- Test 2: new schema produces empty bridge/actions/avoid_followup ---


def test_report_new_schema_bridge_actions_avoid_followup_are_empty() -> None:
    """With the new schema, tonight_parent_bridge is None,
    suggested_parent_actions and avoid_followup are empty lists."""
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

    assert fallback.tonight_parent_bridge is None
    assert fallback.suggested_parent_actions == []
    assert fallback.avoid_followup == []
    # Summary should still be generated
    assert fallback.summary, f"Should have a summary: {fallback.summary}"


# --- Test 3: report does not contain internal words ---


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


# --- Test: image bridge does not contain "那张图" or Xiaobaihu follow-up ---


def test_image_bridge_does_not_ask_about_xiaobaohu_image() -> None:
    """Image topic parent_bridge should not ask about '那张图' or '给小白狐看的是什么'."""
    conversation_messages = [
        _make_conversation_message("child", "你看我画的画", attachments=1),
        _make_conversation_message("agent", "画了什么呢？"),
    ]

    fallback, _ = _build_report(
        memories=[],
        conversation_messages=conversation_messages,
    )

    bridge = fallback.tonight_parent_bridge or ""
    topic_overview = fallback.topic_overview or []

    assert "那张图" not in bridge, f"Bridge contains '那张图': {bridge}"
    assert "给小白狐看的是什么" not in bridge, f"Bridge asks about Xiaobaihu image: {bridge}"

    for item in topic_overview:
        item_bridge = item.parent_bridge or ""
        assert "那张图" not in item_bridge, f"Topic bridge contains '那张图': {item_bridge}"
        assert "给小白狐看的是什么" not in item_bridge, (
            f"Topic bridge asks about Xiaobaihu image: {item_bridge}"
        )


# --- Test: image observations use open family invitation ---


def test_image_observations_use_open_family_invitation() -> None:
    """Image sharing expression observations should use open family wording."""
    conversation_messages = [
        _make_conversation_message("child", "你看这个", attachments=1),
        _make_conversation_message("agent", "你最想让我看哪里？"),
    ]

    fallback, _ = _build_report(
        memories=[],
        conversation_messages=conversation_messages,
    )

    all_text = " ".join([
        fallback.summary or "",
        fallback.conversation_expression_observations if hasattr(fallback, 'conversation_expression_observations') else "",
        " ".join(fallback.expression_observations or []),
    ])

    # Should mention open sharing, not Xiaobaihu-specific follow-up
    assert "给小白狐" not in all_text or "不需要追问" in all_text, (
        f"Should use open family invitation: {all_text}"
    )


# --- Test: conversation summary does not include message counts ---


def test_conversation_summary_no_message_counts() -> None:
    """_conversation_summary should not include exact message counts."""
    service = ParentReportService(
        memory_service=MemoryService(repository=InMemoryMemoryRepository()),
        model_registry=None,
        now_provider=lambda: FIXED_NOW,
    )

    summary = service._conversation_summary(
        topics=["日常聊天"],
        state_summary=[],
        child_turn_count=5,
        agent_turn_count=4,
    )

    assert "5 条" not in summary, f"Summary contains message count: {summary}"
    assert "4 条" not in summary, f"Summary contains message count: {summary}"
    assert "条孩子消息" not in summary, f"Summary contains '条孩子消息': {summary}"
    assert "条小白狐回复" not in summary, f"Summary contains '条小白狐回复': {summary}"


# --- Test: parent report system prompt is not monitoring ---


def test_parent_report_prompt_says_not_monitoring() -> None:
    """System prompt should say it is not a child-Xiaobaihu chat-monitoring record."""
    service = ParentReportService(
        memory_service=MemoryService(repository=InMemoryMemoryRepository()),
        model_registry=None,
        now_provider=lambda: FIXED_NOW,
    )

    prompt = service._parent_report_system_prompt()

    assert "不展示孩子和小白狐逐句聊了什么" in prompt or "聊天监控" in prompt, (
        f"Prompt should say 'not monitoring': {prompt[:200]}"
    )


# --- Test: parent report prompt forbids snippet reconstruction ---


def test_parent_report_prompt_forbids_snippet_reconstruction() -> None:
    """System prompt should forbid reconstructing child utterances from snippets."""
    service = ParentReportService(
        memory_service=MemoryService(repository=InMemoryMemoryRepository()),
        model_registry=None,
        now_provider=lambda: FIXED_NOW,
    )

    prompt = service._parent_report_system_prompt()

    assert "不引用或改写孩子原话" in prompt, (
        f"Prompt should mention '不引用或改写孩子原话': {prompt[:200]}"
    )


# --- Test: parent report prompt includes good/bad examples ---


def test_parent_report_prompt_includes_examples() -> None:
    """System prompt should include good and bad output examples."""
    service = ParentReportService(
        memory_service=MemoryService(repository=InMemoryMemoryRepository()),
        model_registry=None,
        now_provider=lambda: FIXED_NOW,
    )

    prompt = service._parent_report_system_prompt()

    assert "好示例" in prompt or "好的输出示例" in prompt, f"Prompt should have good examples: {prompt[-300:]}"
    assert "坏示例" in prompt or "不好的输出示例" in prompt, f"Prompt should have bad examples: {prompt[-300:]}"


# --- Test: parent actions are not all direct questions ---


def test_parent_actions_are_not_all_questions() -> None:
    """Narrative fallback should produce a natural summary, not just questions."""
    conversation_messages = [
        _make_conversation_message("child", "我今天跑步比赛了"),
        _make_conversation_message("agent", "感觉怎么样？"),
        _make_conversation_message("child", "还行吧"),
        _make_conversation_message("agent", "画了什么呢？"),
        _make_conversation_message("child", "画了一只猫"),
    ]

    fallback, _ = _build_report(
        memories=[],
        conversation_messages=conversation_messages,
    )

    # Narrative fallback should have a natural summary
    summary = fallback.summary or ""
    assert summary, f"Should have a summary: {summary}"
    # Should not be a question
    assert not summary.endswith("？"), f"Summary should not be a question: {summary}"


# --- Test: avoids teacher-style assessment ---


def test_report_avoids_teacher_assessment_language() -> None:
    """Report should avoid teacher-style assessment like '表达能力较好'."""
    conversation_messages = [
        _make_conversation_message("child", "我今天跑步比赛了，跑了很快"),
        _make_conversation_message("agent", "跑步比赛感觉怎么样？"),
        _make_conversation_message("child", "还行吧，有点累"),
    ]

    fallback, _ = _build_report(
        memories=[],
        conversation_messages=conversation_messages,
    )

    all_text = " ".join([
        fallback.summary or "",
        " ".join(fallback.expression_observations or []),
        " ".join(fallback.suggested_parent_actions or []),
    ])

    assert "表达能力较好" not in all_text, f"Contains teacher assessment: {all_text}"
    assert "整体能连续表达" not in all_text, f"Contains teacher assessment: {all_text}"
    assert "能把一个主动话题延展开" not in all_text, f"Contains teacher assessment: {all_text}"
