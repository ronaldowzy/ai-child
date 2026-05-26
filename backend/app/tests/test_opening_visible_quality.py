"""Opening v3 visible quality tests (Task 21).

Verifies:
  1. profile-only opening uses nickname + interest, no labels.
  2. unfinished-thread opening mentions previous thread lightly and explicitly allows not continuing.
  3. boundary "不要追问比赛输赢" does not produce "谁赢了/输了没/排名".
  4. two context types produce different deterministic fallback openings.
  5. no gender stereotypes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.domain.memory import (
    MemoryEvidence,
    MemoryItem,
    MemorySensitivity,
    MemoryType,
)
from app.domain.schemas.parent_policy import ParentPolicy
from app.repositories.memory_repository import InMemoryMemoryRepository
from app.services.memory_service import MemoryService
from app.services.opening_policy import OpeningMode, OpeningPolicy
from app.services.opening_service import OpeningService
from app.services.relationship_memory import (
    INTEREST_SEED,
    SHOW_AND_TELL_EVENT,
    UNFINISHED_THREAD,
    relationship_metadata,
)


FIXED_NOW = datetime(2026, 5, 26, 8, 0, tzinfo=timezone.utc)

CHILD_ID = "child_opening_quality"

# Forbidden labels that must never appear in child-facing opening text
FORBIDDEN_LABELS = (
    "慢热", "容易受挫", "说话短", "男孩", "女孩",
    "类型", "属于", "敏感", "内向", "外向",
)

# Forbidden framing from boundary "不要追问比赛输赢"
FORBIDDEN_FRAMING = ("谁赢", "赢了吗", "输了没", "排名", "第几", "成绩")

# Gender stereotype markers
GENDER_STEREOTYPE = ("男孩就应该", "女孩就应该", "男生喜欢", "女生喜欢", "男孩子都")


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
            "child_interests": ["画画", "跑步"],
            "topic_boundaries": ["不要追问比赛输赢"],
            "support_style_preferences": ["offer_two_choices", "ask_fewer_questions"],
        },
        "created_at": FIXED_NOW,
        "updated_at": FIXED_NOW,
    }
    base.update(overrides)
    return ParentPolicy(**base)


def _make_opening_policy(**overrides: Any) -> OpeningPolicy:
    base: dict[str, Any] = {
        "mode": OpeningMode.INTEREST_CALLBACK,
        "age_band": "age_7_8",
        "max_chars": 80,
        "max_spoken_options": 2,
        "seed_topic": "画画",
        "seed_recall_allowed": True,
        "seed_recall_reason": None,
        "boundary_kind": None,
        "boundary_topic": None,
        "boundary_cooldown_active": False,
        "bedtime": False,
        "exciting_topic_deferred": False,
        "must_offer_topic_switch": False,
        "must_allow_no_chat": True,
        "prefer_parent_bridge": False,
        "parent_goal_hint": None,
        "forbidden_phrases": (),
        "prompt_rules": (),
    }
    base.update(overrides)
    return OpeningPolicy(**base)


def _build_opening(
    *,
    parent_policy: ParentPolicy | None = None,
    opening_policy: OpeningPolicy | None = None,
    memory_service: MemoryService | None = None,
) -> str:
    service = OpeningService(
        parent_policy_service=None,
        time_context_service=None,
        tts_service=None,
        model_registry=None,
        memory_service=memory_service,
    )
    pp = parent_policy or _make_parent_policy()
    op = opening_policy or _make_opening_policy()
    return service._build_opening_text(parent_policy=pp, opening_policy=op)


# --- Test 1: profile-only opening uses nickname + interest, no labels ---


def test_profile_only_opening_uses_nickname_and_interest_no_labels() -> None:
    """Opening with INTEREST_CALLBACK mode should mention nickname and interest,
    but never expose profile labels like 慢热/说话短/类型."""
    repo = InMemoryMemoryRepository()
    memory_service = MemoryService(repository=repo)

    text = _build_opening(memory_service=memory_service)

    assert "航航" in text, f"Should use nickname: {text}"
    assert "画画" in text, f"Should mention interest: {text}"
    for label in FORBIDDEN_LABELS:
        assert label not in text, f"Should not contain label '{label}': {text}"


# --- Test 2: unfinished-thread opening mentions thread, allows not continuing ---


def test_unfinished_thread_opening_mentions_thread_and_allows_not_continuing() -> None:
    """When an unfinished thread exists, opening should mention it lightly
    and explicitly allow the child to not continue."""
    repo = InMemoryMemoryRepository()
    memory_service = MemoryService(repository=repo)

    # Store an unfinished thread
    mem = _make_memory(
        "mem_thread",
        "孩子说要去英语打卡",
        relationship_type=UNFINISHED_THREAD,
    )
    repo.save(mem)

    text = _build_opening(memory_service=memory_service)

    assert "英语" in text, f"Should mention the thread: {text}"
    # Should explicitly allow not continuing
    assert any(
        phrase in text
        for phrase in ("不用接着说", "想换个话题也可以", "不想说也没关系", "可以换")
    ), f"Should allow not continuing: {text}"


# --- Test 3: boundary "不要追问比赛输赢" doesn't produce forbidden framing ---


def test_boundary_does_not_produce_forbidden_framing() -> None:
    """With boundary '不要追问比赛输赢', opening must not contain
    framing words like 谁赢/输了没/排名."""
    repo = InMemoryMemoryRepository()
    memory_service = MemoryService(repository=repo)

    # Store an interest seed about running
    mem = _make_memory(
        "mem_interest",
        "孩子自然提到跑步比赛",
        memory_type=MemoryType.INTEREST,
        relationship_type=INTEREST_SEED,
    )
    repo.save(mem)

    parent_policy = _make_parent_policy()
    opening_policy = _make_opening_policy(
        mode=OpeningMode.INTEREST_CALLBACK,
        seed_topic="跑步比赛",
    )

    text = _build_opening(
        parent_policy=parent_policy,
        opening_policy=opening_policy,
        memory_service=memory_service,
    )

    for word in FORBIDDEN_FRAMING:
        assert word not in text, f"Boundary violation: '{word}' in '{text}'"


# --- Test 4: two context types produce different deterministic fallback openings ---


def test_two_context_types_produce_different_openings() -> None:
    """INTEREST_CALLBACK and BOUNDARY_RESPECT modes should produce
    different fallback opening text."""
    repo = InMemoryMemoryRepository()
    memory_service = MemoryService(repository=repo)

    interest_policy = _make_opening_policy(
        mode=OpeningMode.INTEREST_CALLBACK,
        seed_topic="画画",
    )
    boundary_policy = _make_opening_policy(
        mode=OpeningMode.BOUNDARY_RESPECT,
        seed_topic=None,
        boundary_kind="avoid_followup",
        boundary_topic="比赛",
    )

    text_interest = _build_opening(
        opening_policy=interest_policy,
        memory_service=memory_service,
    )
    text_boundary = _build_opening(
        opening_policy=boundary_policy,
        memory_service=memory_service,
    )

    assert text_interest != text_boundary, (
        f"Different modes should produce different text: "
        f"interest='{text_interest}', boundary='{text_boundary}'"
    )
    # Interest mode should mention the topic
    assert "画画" in text_interest, f"Interest mode should mention topic: {text_interest}"
    # Boundary mode should hint at avoiding the topic
    assert any(
        phrase in text_boundary
        for phrase in ("先不聊", "先放一放", "上次那个")
    ), f"Boundary mode should hint at avoidance: {text_boundary}"


# --- Test 5: no gender stereotypes ---


def test_no_gender_stereotypes() -> None:
    """Opening must not contain gender-based stereotypes."""
    repo = InMemoryMemoryRepository()
    memory_service = MemoryService(repository=repo)

    # Test with boy profile
    boy_policy = _make_parent_policy(
        communication_preferences={
            "child_age": 7,
            "child_gender": "boy",
            "child_interests": ["画画"],
        },
    )
    text_boy = _build_opening(
        parent_policy=boy_policy,
        memory_service=memory_service,
    )
    for marker in GENDER_STEREOTYPE:
        assert marker not in text_boy, f"Gender stereotype in boy opening: '{marker}' in '{text_boy}'"

    # Test with girl profile
    girl_policy = _make_parent_policy(
        child_id="child_girl_quality",
        child_nickname="小花",
        communication_preferences={
            "child_age": 7,
            "child_gender": "girl",
            "child_interests": ["画画"],
        },
    )
    text_girl = _build_opening(
        parent_policy=girl_policy,
        memory_service=memory_service,
    )
    for marker in GENDER_STEREOTYPE:
        assert marker not in text_girl, f"Gender stereotype in girl opening: '{marker}' in '{text_girl}'"


# --- Additional: variation test ---


def test_variation_selects_different_templates_across_child_ids() -> None:
    """_select_by_variation should pick different templates for different child_ids."""
    repo = InMemoryMemoryRepository()
    memory_service = MemoryService(repository=repo)

    templates = ["模板A", "模板B", "模板C"]

    service = OpeningService(
        parent_policy_service=None,
        time_context_service=None,
        tts_service=None,
        model_registry=None,
        memory_service=memory_service,
    )

    # Different child_ids should (potentially) select different templates
    results = set()
    for i in range(10):
        pp = _make_parent_policy(
            child_id=f"child_var_{i}",
            child_nickname=f"孩子{i}",
        )
        result = service._select_by_variation(templates, pp)
        results.add(result)

    # With 10 different child_ids and 3 templates, we should get at least 2 different results
    assert len(results) >= 2, f"Should get variation across child_ids: {results}"


# --- Additional: show-and-tell memory opening ---


def test_show_and_tell_memory_opening() -> None:
    """When a show-and-tell event exists, opening should reference it lightly."""
    repo = InMemoryMemoryRepository()
    memory_service = MemoryService(repository=repo)

    mem = _make_memory(
        "mem_show_tell",
        "孩子展示了一幅自己画的小狐狸",
        relationship_type=SHOW_AND_TELL_EVENT,
    )
    repo.save(mem)

    text = _build_opening(memory_service=memory_service)

    assert "小狐狸" in text or "画" in text, f"Should reference show-and-tell: {text}"
    assert "航航" in text, f"Should use nickname: {text}"


# --- Additional: default greeting mode ---


def test_default_greeting_mode() -> None:
    """DEFAULT_LIGHT mode should produce a gentle, non-intrusive greeting."""
    repo = InMemoryMemoryRepository()
    memory_service = MemoryService(repository=repo)

    opening_policy = _make_opening_policy(
        mode=OpeningMode.DEFAULT_LIGHT,
        seed_topic=None,
    )

    text = _build_opening(opening_policy=opening_policy, memory_service=memory_service)

    assert "航航" in text, f"Should use nickname: {text}"
    assert any(
        phrase in text
        for phrase in ("慢慢说", "我在这里", "小白狐在这里", "回来啦", "想聊什么都可以")
    ), f"Should be a gentle greeting: {text}"
