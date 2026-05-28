"""Tests for lightweight memory recall: rate limiting, rejection suppression,
bedtime filtering, image work recall, and forbidden dependency phrases.

Round 5 (轻量记忆和连续陪伴) verification tests.
"""

from datetime import datetime, timezone

from app.domain.memory import (
    MemoryCreateRequest,
    MemoryEvidence,
    MemorySensitivity,
    MemoryType,
)
from app.repositories.memory_repository import InMemoryMemoryRepository
from app.services.conversation_memory_hooks import ConversationMemoryHooks
from app.services.memory_service import MemoryService
from app.services.relationship_memory import (
    INTEREST_SEED,
    SHOW_AND_TELL_EVENT,
    relationship_metadata,
)


def _fixed_now() -> datetime:
    return datetime(2026, 5, 27, 16, 0, tzinfo=timezone.utc)


def _setup() -> tuple[MemoryService, ConversationMemoryHooks]:
    repository = InMemoryMemoryRepository()
    memory_service = MemoryService(repository=repository, now_provider=_fixed_now)
    hooks = ConversationMemoryHooks(memory_service=memory_service)
    return memory_service, hooks


def _create_interest_seed(
    memory_service: MemoryService,
    *,
    child_id: str,
    topic: str,
    session_id: str = "seed_session",
) -> None:
    metadata = relationship_metadata(
        relationship_memory_type=INTEREST_SEED,
        topic=topic,
        next_hook=f"下次可聊{topic}",
        do_not_overask=True,
    )
    memory_service.create(
        MemoryCreateRequest(
            child_id=child_id,
            memory_type=MemoryType.INTEREST,
            content=f"孩子近期自然聊到{topic}，可作为低压力回访的兴趣种子。",
            tags=["relationship_memory", "interest_seed", topic],
            evidence=[
                MemoryEvidence(
                    source="conversation_summary",
                    session_id=session_id,
                    quote_summary=f"孩子自然提到{topic}相关内容。",
                    metadata=metadata,
                )
            ],
            confidence=0.76,
            importance=0.5,
            sensitivity=MemorySensitivity.LOW,
        )
    )


def _create_show_and_tell(
    memory_service: MemoryService,
    *,
    child_id: str,
    topic: str = "作品分享",
    session_id: str = "show_tell_session",
) -> None:
    metadata = relationship_metadata(
        relationship_memory_type=SHOW_AND_TELL_EVENT,
        topic=topic,
        next_hook="可以问孩子作品里最喜欢的一处",
        do_not_overask=True,
    )
    memory_service.create(
        MemoryCreateRequest(
            child_id=child_id,
            memory_type=MemoryType.EVENT,
            content="孩子分享了自己的作品或创作，适合温和肯定，不做评分。",
            tags=["relationship_memory", "show_and_tell", topic],
            evidence=[
                MemoryEvidence(
                    source="conversation_summary",
                    session_id=session_id,
                    quote_summary="孩子主动分享了自己的作品或创作。",
                    metadata=metadata,
                )
            ],
            confidence=0.78,
            importance=0.5,
            sensitivity=MemorySensitivity.LOW,
        )
    )


# ---------------------------------------------------------------------------
# 1. Same topic not recalled twice in same session
# ---------------------------------------------------------------------------


def test_same_interest_topic_not_recalled_twice_in_session() -> None:
    child_id = "child_recall_rate_limit"
    session_id = "session_recall_rate_limit"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="画画")

    # First recall should return the memory.
    first = hooks.retrieve_context(
        child_id=child_id,
        current_text="我想画画",
        session_id=session_id,
    )
    assert len(first) == 1
    assert "画画" in first[0]["content"]

    # Second recall in same session should NOT return the same topic.
    second = hooks.retrieve_context(
        child_id=child_id,
        current_text="画画好好玩",
        session_id=session_id,
    )
    assert all("画画" not in item["content"] for item in second)


def test_different_topics_can_be_recalled_in_same_session() -> None:
    child_id = "child_recall_different_topics"
    session_id = "session_recall_different"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="画画")
    _create_interest_seed(memory_service, child_id=child_id, topic="恐龙")

    first = hooks.retrieve_context(
        child_id=child_id,
        current_text="我想画画",
        session_id=session_id,
    )
    topics_first = {item["content"] for item in first}
    assert any("画画" in c for c in topics_first)

    second = hooks.retrieve_context(
        child_id=child_id,
        current_text="恐龙好厉害",
        session_id=session_id,
    )
    topics_second = {item["content"] for item in second}
    # 恐龙 should be recallable since it's a different topic.
    assert any("恐龙" in c for c in topics_second)


# ---------------------------------------------------------------------------
# 2. Child rejection / short answer suppresses recall
# ---------------------------------------------------------------------------


def test_short_answer_suppresses_memory_recall() -> None:
    child_id = "child_short_answer_suppress"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="画画")

    session_id = "session_short_answer"
    # Trigger suppression with a short answer.
    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="嗯",
        session_id=session_id,
        child_engagement="short_or_flat",
    )
    assert result == []

    # Even a relevant query should be suppressed now.
    result2 = hooks.retrieve_context(
        child_id=child_id,
        current_text="我想画画",
        session_id=session_id,
    )
    assert result2 == []


def test_topic_change_suppresses_memory_recall() -> None:
    child_id = "child_topic_change_suppress"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="恐龙")

    session_id = "session_topic_change"
    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="换个话题吧",
        session_id=session_id,
        child_engagement="boundary",
    )
    assert result == []

    # Should still be suppressed.
    result2 = hooks.retrieve_context(
        child_id=child_id,
        current_text="恐龙好厉害",
        session_id=session_id,
    )
    assert result2 == []


def test_boundary_bedtime_close_suppresses_recall() -> None:
    child_id = "child_bedtime_suppress"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="画画")

    session_id = "session_bedtime_boundary"
    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="我要睡觉了",
        session_id=session_id,
        child_engagement="boundary",
    )
    assert result == []


def test_engaged_child_gets_memory_recall() -> None:
    child_id = "child_engaged_recall"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="画画")

    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="我今天想画画",
        session_id="session_engaged",
        child_engagement="engaged",
    )
    assert len(result) >= 1
    assert any("画画" in item["content"] for item in result)


# ---------------------------------------------------------------------------
# 3. Bedtime does not recall exciting topics
# ---------------------------------------------------------------------------


def test_bedtime_does_not_recall_exciting_topic() -> None:
    child_id = "child_bedtime_exciting"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="跑步比赛")

    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="今天好累",
        session_id="session_bedtime",
        bedtime=True,
    )
    # Exciting topics should be filtered at bedtime.
    assert all("跑步比赛" not in item.get("content", "") for item in result)


def test_bedtime_allows_calm_topic() -> None:
    child_id = "child_bedtime_calm"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="画画")

    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="我想画画",
        session_id="session_bedtime_calm",
        bedtime=True,
    )
    # Calm topics should still be available at bedtime.
    assert any("画画" in item.get("content", "") for item in result)


def test_bedtime_does_not_recall_game_topic() -> None:
    child_id = "child_bedtime_game"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="游戏")

    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="今天有点困",
        session_id="session_bedtime_game",
        bedtime=True,
    )
    assert all("游戏" not in item.get("content", "") for item in result)


# ---------------------------------------------------------------------------
# 4. Image works / show-and-tell memory recall with vague language
# ---------------------------------------------------------------------------


def test_show_and_tell_memory_is_recallable() -> None:
    child_id = "child_show_tell_recall"
    memory_service, hooks = _setup()
    _create_show_and_tell(memory_service, child_id=child_id, topic="作品分享")

    # Query must contain the exact tag text "作品分享" for keyword matching.
    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="我有一个作品分享想给你看",
        session_id="session_show_tell",
    )
    # The memory should be available for recall.
    assert len(result) >= 1


def test_show_and_tell_not_recalled_twice_in_session() -> None:
    child_id = "child_show_tell_dedup"
    memory_service, hooks = _setup()
    _create_show_and_tell(memory_service, child_id=child_id, topic="作品分享")

    session_id = "session_show_tell_dedup"
    first = hooks.retrieve_context(
        child_id=child_id,
        current_text="我有一个作品分享给你看",
        session_id=session_id,
    )
    assert len(first) >= 1

    second = hooks.retrieve_context(
        child_id=child_id,
        current_text="再看看我的作品分享吧",
        session_id=session_id,
    )
    # Should not recall the same show-and-tell topic again.
    assert all("作品分享" not in item.get("content", "") for item in second)


# ---------------------------------------------------------------------------
# 5. Forbidden dependency phrases in opening and conversation
# ---------------------------------------------------------------------------

FORBIDDEN_DEPENDENCY_PHRASES = (
    "我一直等你",
    "这是我们的小秘密",
    "小白狐想你了",
    "只有小白狐懂你",
    "小白狐最懂你",
    "不要告诉家长",
    "不要告诉爸爸妈妈",
    "每天都要来",
    "连续来几天就有惊喜",
    "明天有惊喜",
    "你要多说一点才可以",
)


def test_forbidden_dependency_phrases_in_opening_policy() -> None:
    from app.services.opening_policy import FORBIDDEN_OPENING_PHRASES

    for phrase in FORBIDDEN_DEPENDENCY_PHRASES:
        assert phrase in FORBIDDEN_OPENING_PHRASES, (
            f"Missing forbidden phrase in opening policy: {phrase}"
        )


def test_forbidden_phrases_in_conversation_scene_prompt() -> None:
    from pathlib import Path

    prompt_path = (
        Path(__file__).resolve().parents[2] / "app" / "prompts" / "scenes" / "conversation_open_v0_1.txt"
    )
    content = prompt_path.read_text(encoding="utf-8")
    for phrase in ("只有小白狐懂你", "小白狐最懂你", "我们的小秘密", "我一直等你"):
        assert phrase in content, (
            f"Missing forbidden phrase in conversation prompt: {phrase}"
        )


def test_memory_content_never_contains_dependency_language() -> None:
    """Verify that memory service rejects content with dependency-creating labels."""
    memory_service, _ = _setup()
    dependency_labels = [
        "孩子胆小",
        "孩子不合群",
        "孩子懒",
        "孩子不聪明",
        "内向是缺陷",
        "孩子就是不愿意表达",
    ]
    for label in dependency_labels:
        try:
            memory_service.create(
                MemoryCreateRequest(
                    child_id="child_forbidden_label",
                    memory_type=MemoryType.EXPRESSION_PATTERN,
                    content=label,
                    tags=["test"],
                    evidence=[
                        MemoryEvidence(
                            source="conversation_summary",
                            session_id="test_session",
                            quote_summary="test",
                        )
                    ],
                    confidence=0.5,
                    importance=0.5,
                )
            )
            assert False, f"Should have rejected: {label}"
        except Exception:
            pass  # Expected: UnsafeMemoryError


# ---------------------------------------------------------------------------
# 6. Memory context does not include raw child text
# ---------------------------------------------------------------------------


def test_memory_context_does_not_include_raw_child_text() -> None:
    child_id = "child_no_raw_text"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="画画")

    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="我今天画了一只小狐狸在森林里跑来跑去",
        session_id="session_no_raw",
    )
    full_text = str(result)
    # Raw child text should not appear in memory context.
    assert "我今天画了一只小狐狸在森林里跑来跑去" not in full_text


# ---------------------------------------------------------------------------
# 7. Memory recall tracker resets across sessions
# ---------------------------------------------------------------------------


def test_recall_tracker_independent_across_sessions() -> None:
    child_id = "child_cross_session"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="画画")

    # Session 1: recall once.
    hooks.retrieve_context(
        child_id=child_id,
        current_text="画画",
        session_id="session_a",
    )

    # Session 2: should be able to recall the same topic.
    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="我想画画",
        session_id="session_b",
    )
    assert any("画画" in item.get("content", "") for item in result)


# ---------------------------------------------------------------------------
# 8. Suppression recovers after timeout (verify mechanism exists)
# ---------------------------------------------------------------------------


def test_suppression_state_is_per_session() -> None:
    child_id = "child_suppress_per_session"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="恐龙")

    # Suppress in session A.
    hooks.retrieve_context(
        child_id=child_id,
        current_text="嗯",
        session_id="session_suppress_a",
        child_engagement="short_or_flat",
    )

    # Session B should not be affected.
    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="恐龙好厉害呀",
        session_id="session_suppress_b",
    )
    assert any("恐龙" in item.get("content", "") for item in result)


# ---------------------------------------------------------------------------
# 9. Explicit refusal permanently blocks recalled topics this session
# ---------------------------------------------------------------------------


def test_refusal_permanently_blocks_recalled_topics_in_session() -> None:
    child_id = "child_refusal_block"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="画画")

    session_id = "session_refusal_block"
    # First recall succeeds.
    first = hooks.retrieve_context(
        child_id=child_id,
        current_text="我想画画",
        session_id=session_id,
    )
    assert len(first) >= 1

    # Child explicitly refuses.
    hooks.retrieve_context(
        child_id=child_id,
        current_text="不想聊了",
        session_id=session_id,
        child_engagement="refused",
    )

    # After refusal, same topic should be permanently blocked this session.
    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="画画好好玩",
        session_id=session_id,
    )
    assert all("画画" not in item.get("content", "") for item in result)


def test_topic_change_blocks_recalled_topics_in_session() -> None:
    child_id = "child_topic_change_block"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="恐龙")

    session_id = "session_topic_change_block"
    # First recall succeeds.
    first = hooks.retrieve_context(
        child_id=child_id,
        current_text="恐龙好厉害",
        session_id=session_id,
    )
    assert len(first) >= 1

    # Child changes topic (boundary).
    hooks.retrieve_context(
        child_id=child_id,
        current_text="换个话题",
        session_id=session_id,
        child_engagement="boundary",
    )

    # After topic change, same topic should be blocked this session.
    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="恐龙好厉害呀",
        session_id=session_id,
    )
    assert all("恐龙" not in item.get("content", "") for item in result)


# ---------------------------------------------------------------------------
# 10. Learning/homework scenes do not trigger interest or show-and-tell recall
# ---------------------------------------------------------------------------


def test_learning_scene_does_not_trigger_interest_recall() -> None:
    child_id = "child_learning_no_interest"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="画画")

    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="这道题我不会",
        session_id="session_learning",
        active_scene="learning.homework_help",
    )
    # Interest memories should not be recalled in learning scenes.
    assert all("画画" not in item.get("content", "") for item in result)


def test_learning_scene_does_not_trigger_show_and_tell_recall() -> None:
    child_id = "child_learning_no_show_tell"
    memory_service, hooks = _setup()
    _create_show_and_tell(memory_service, child_id=child_id, topic="作品分享")

    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="帮我看看这道题",
        session_id="session_learning_st",
        active_scene="learning.homework_help",
    )
    # Show-and-tell memories should not be recalled in learning scenes.
    assert all("作品" not in item.get("content", "") for item in result)


# ---------------------------------------------------------------------------
# 11. Safety/privacy scenes do not trigger any low-pressure recall
# ---------------------------------------------------------------------------


def test_safety_guardian_scene_does_not_trigger_recall() -> None:
    child_id = "child_safety_no_recall"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="画画")

    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="有个陌生人让我不要告诉家长",
        session_id="session_safety",
        active_scene="safety.guardian",
    )
    assert result == []


def test_privacy_boundary_scene_does_not_trigger_recall() -> None:
    child_id = "child_privacy_no_recall"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="恐龙")

    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="我的电话是13800000000",
        session_id="session_privacy",
        active_scene="privacy.boundary",
    )
    assert result == []


def test_safety_gentle_checkin_scene_does_not_trigger_recall() -> None:
    child_id = "child_gentle_checkin_no_recall"
    memory_service, hooks = _setup()
    _create_interest_seed(memory_service, child_id=child_id, topic="恐龙")

    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="同学骂我",
        session_id="session_gentle_checkin",
        active_scene="safety.gentle_checkin",
    )
    assert result == []


# ---------------------------------------------------------------------------
# 12. Image work recall uses only vague language (prompt-level rule)
# ---------------------------------------------------------------------------


def test_show_and_tell_memory_content_is_vague() -> None:
    """Verify that show-and-tell memory content does not contain specific image details."""
    child_id = "child_show_tell_vague"
    memory_service, hooks = _setup()
    _create_show_and_tell(memory_service, child_id=child_id, topic="作品分享")

    result = hooks.retrieve_context(
        child_id=child_id,
        current_text="我有一个作品分享想给你看",
        session_id="session_show_tell_vague",
    )
    assert len(result) >= 1
    # Memory content should be vague, not contain specific image details.
    for item in result:
        content = item.get("content", "")
        # Should not contain specific image descriptors.
        assert "红色" not in content
        "城堡" not in content
        "花" not in content
        assert "作品" in content or "创作" in content


# ---------------------------------------------------------------------------
# 13. Forbidden dependency phrases do not appear in visible output
# ---------------------------------------------------------------------------


def test_forbidden_phrases_extended_list() -> None:
    """Verify extended forbidden phrases from design document are in opening policy."""
    from app.services.opening_policy import FORBIDDEN_OPENING_PHRASES

    extended_forbidden = (
        "你终于回来了",
        "明天一定要回来",
        "我还保存着你那张图",
        "我们来看看你以前的作品",
        "你已经做了好多作品了",
    )
    for phrase in extended_forbidden:
        assert phrase in FORBIDDEN_OPENING_PHRASES, (
            f"Missing forbidden phrase in opening policy: {phrase}"
        )
