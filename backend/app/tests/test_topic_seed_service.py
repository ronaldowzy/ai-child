import json
from datetime import date
from pathlib import Path

import pytest

from app.services.topic_seed_service import TopicSeedService


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
