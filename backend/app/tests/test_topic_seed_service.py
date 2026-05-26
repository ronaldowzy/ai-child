import json
from datetime import date
from pathlib import Path

import pytest

from app.services.topic_seed_service import BoundaryCategory, TopicSeedService


def test_topic_seed_pack_returns_age_aware_safe_labels() -> None:
    service = TopicSeedService(today_provider=lambda: date(2026, 5, 24))

    labels = service.seeds_for_parent_policy(
        {"communication_preferences": {"child_age": 8}},
        limit=3,
    )
    seeds = service.seed_objects_for_parent_policy(
        {"communication_preferences": {"child_age": 8}},
        limit=3,
    )

    assert "恐龙或太空小问题" in labels
    assert all(seed.source == "curated_v0_1" for seed in seeds)
    assert all(seed.safety_notes for seed in seeds)
    assert all(seed.expires_at >= date(2026, 5, 24) for seed in seeds)
    assert all("age_7_8" in seed.age_bands for seed in seeds)


def test_topic_seed_pack_skips_expired_seed(tmp_path: Path) -> None:
    pack_path = tmp_path / "seeds.json"
    pack_path.write_text(
        json.dumps(
            {
                "seeds": [
                    _seed(
                        seed_id="expired_seed",
                        label="过期小话题",
                        expires_at="2026-01-01",
                    ),
                    _seed(
                        seed_id="active_seed",
                        label="画画或手工",
                        expires_at="2026-12-31",
                    ),
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TopicSeedService(
        seed_pack_path=pack_path,
        today_provider=lambda: date(2026, 5, 24),
    )

    assert service.seeds_for_parent_policy(None) == ["画画或手工"]


def test_topic_seed_pack_rejects_missing_or_unsafe_fields(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.json"
    missing_path.write_text(
        json.dumps({"seeds": [{"id": "bad"}]}),
        encoding="utf-8",
    )
    unsafe_path = tmp_path / "unsafe.json"
    unsafe_path.write_text(
        json.dumps(
            {
                "seeds": [
                    _seed(
                        seed_id="unsafe_seed",
                        label="抽卡排行榜",
                    )
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing fields"):
        TopicSeedService(seed_pack_path=missing_path)._load_seed_objects()
    with pytest.raises(ValueError, match="unsafe marker"):
        TopicSeedService(seed_pack_path=unsafe_path)._load_seed_objects()


def test_topic_choice_labels_prefer_profile_interests() -> None:
    service = TopicSeedService(today_provider=lambda: date(2026, 5, 24))

    labels = service.topic_choice_labels(
        {
            "communication_preferences": {
                "child_age": 8,
                "child_interests": ["恐龙", "画画", "跑步"],
            }
        },
        limit=3,
    )

    assert labels == ["聊恐龙", "聊画画", "聊跑步"]


def test_topic_choice_labels_filter_boundaries_and_recent_topic_synonyms() -> None:
    service = TopicSeedService(today_provider=lambda: date(2026, 5, 24))

    labels = service.topic_choice_labels(
        {
            "communication_preferences": {
                "child_age": 8,
                "child_interests": ["恐龙", "画画", "跑步", "CS"],
                "topic_boundaries": ["跑步", "游戏"],
            }
        },
        recent_topic="游戏/CS",
        limit=4,
    )

    assert labels[:2] == ["聊恐龙", "聊画画"]
    assert all("跑步" not in label for label in labels)
    assert all("CS" not in label and "游戏" not in label for label in labels)


def test_topic_choice_labels_offer_two_choices_limits_to_two() -> None:
    service = TopicSeedService(today_provider=lambda: date(2026, 5, 24))

    labels = service.topic_choice_labels(
        {
            "communication_preferences": {
                "child_age": 8,
                "child_interests": ["恐龙", "画画", "跑步"],
                "support_style_preferences": ["offer_two_choices"],
            }
        },
        limit=3,
    )

    assert len(labels) == 2
    assert labels == ["聊恐龙", "聊画画"]


def test_topic_choice_labels_offer_two_choices_with_boundaries() -> None:
    service = TopicSeedService(today_provider=lambda: date(2026, 5, 24))

    labels = service.topic_choice_labels(
        {
            "communication_preferences": {
                "child_age": 8,
                "child_interests": ["恐龙", "画画", "跑步"],
                "topic_boundaries": ["恐龙"],
                "support_style_preferences": ["offer_two_choices"],
            }
        },
        limit=3,
    )

    assert len(labels) == 2
    assert "聊恐龙" not in labels


# --- Boundary semantics v2 tests ---


def test_classify_boundary_avoid_followup() -> None:
    """'不要追问比赛输赢' should be classified as avoid_followup."""
    service = TopicSeedService(today_provider=lambda: date(2026, 5, 24))

    assert service.classify_boundary("不要追问比赛输赢") == BoundaryCategory.AVOID_FOLLOWUP
    assert service.classify_boundary("少追问比赛") == BoundaryCategory.AVOID_FOLLOWUP
    assert service.classify_boundary("别问这个") == BoundaryCategory.AVOID_FOLLOWUP


def test_classify_boundary_avoid_topic() -> None:
    """'不要聊游戏' should be classified as avoid_topic."""
    service = TopicSeedService(today_provider=lambda: date(2026, 5, 24))

    assert service.classify_boundary("不要聊游戏") == BoundaryCategory.AVOID_TOPIC
    assert service.classify_boundary("不想聊这个") == BoundaryCategory.AVOID_TOPIC
    assert service.classify_boundary("别聊政治") == BoundaryCategory.AVOID_TOPIC


def test_classify_boundary_avoid_framing() -> None:
    """'不要问排名' should be classified as avoid_framing."""
    service = TopicSeedService(today_provider=lambda: date(2026, 5, 24))

    assert service.classify_boundary("不要问排名") == BoundaryCategory.AVOID_FRAMING
    assert service.classify_boundary("别提成绩") == BoundaryCategory.AVOID_FRAMING


def test_classify_boundary_unknown() -> None:
    """Boundary without known markers should be unknown."""
    service = TopicSeedService(today_provider=lambda: date(2026, 5, 24))

    assert service.classify_boundary("随便什么") == BoundaryCategory.UNKNOWN


def test_boundary_nuance_avoid_followup_allows_safe_topic() -> None:
    """'不要追问比赛输赢' should allow '聊跑步比赛' but not '聊比赛输赢'."""
    service = TopicSeedService(today_provider=lambda: date(2026, 5, 24))

    labels = service.topic_choice_labels(
        {
            "communication_preferences": {
                "child_age": 7,
                "child_interests": ["跑步比赛", "画画"],
                "topic_boundaries": ["不要追问比赛输赢"],
            }
        },
        limit=3,
    )

    # 聊跑步比赛 should be allowed (safe topic)
    assert any("跑步比赛" in lbl for lbl in labels), (
        f"Should include safe 跑步比赛 label: {labels}"
    )
    # 聊画画 should be allowed
    assert any("画画" in lbl for lbl in labels), (
        f"Should include 画画 label: {labels}"
    )
    # No label should contain forbidden framing
    for label in labels:
        for fw in ("输赢", "谁赢", "谁输", "赢了吗", "输了", "赢了"):
            assert fw not in label, (
                f"Label '{label}' contains forbidden framing '{fw}'"
            )


def test_boundary_nuance_avoid_topic_hard_filter() -> None:
    """'不要聊游戏' should filter out all 游戏-related topics."""
    service = TopicSeedService(today_provider=lambda: date(2026, 5, 24))

    labels = service.topic_choice_labels(
        {
            "communication_preferences": {
                "child_age": 7,
                "child_interests": ["游戏", "画画"],
                "topic_boundaries": ["不要聊游戏"],
            }
        },
        limit=3,
    )

    # No game-related labels
    assert all("游戏" not in lbl and "cs" not in lbl.lower() for lbl in labels), (
        f"Should not include game labels: {labels}"
    )
    # 画画 should still be there
    assert any("画画" in lbl for lbl in labels), (
        f"Should include 画画 label: {labels}"
    )


def test_boundary_nuance_avoid_followup_no追问_in_label() -> None:
    """Labels should not contain追问 when boundary is avoid_followup."""
    service = TopicSeedService(today_provider=lambda: date(2026, 5, 24))

    labels = service.topic_choice_labels(
        {
            "communication_preferences": {
                "child_age": 7,
                "child_interests": ["跑步比赛", "画画"],
                "topic_boundaries": ["不要追问比赛输赢"],
            }
        },
        limit=3,
    )

    for label in labels:
        assert "追问" not in label, f"Label should not contain追问: {label}"


def _seed(
    *,
    seed_id: str,
    label: str,
    expires_at: str = "2026-12-31",
) -> dict[str, object]:
    return {
        "id": seed_id,
        "label": label,
        "age_bands": ["unknown"],
        "prompt_hint": "给一个轻松、可停止的小话题。",
        "safety_notes": "avoid purchase pressure; avoid ranking/collection mechanics",
        "expires_at": expires_at,
        "source": "curated_v0_1",
    }
