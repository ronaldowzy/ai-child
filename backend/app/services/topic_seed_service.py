import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from app.services.age_band_policy import derive_age_band_reply_policy


ALLOWED_AGE_BANDS = {"age_5_6", "age_7_8", "age_9_10", "unknown"}
REQUIRED_SEED_FIELDS = {
    "id",
    "label",
    "age_bands",
    "prompt_hint",
    "safety_notes",
    "expires_at",
    "source",
}
UNSAFE_LABEL_MARKERS = (
    "抽卡",
    "签到",
    "排行榜",
    "排名",
    "稀有",
    "皮肤",
    "充值",
    "购买",
    "买",
    "热搜",
    "八卦",
    "明天有惊喜",
)


@dataclass(frozen=True)
class TopicSeed:
    id: str
    label: str
    age_bands: tuple[str, ...]
    prompt_hint: str
    safety_notes: str
    expires_at: date
    source: str

    def is_active_for(self, age_band: str, *, today: date) -> bool:
        return age_band in self.age_bands and self.expires_at >= today

    def prompt_label(self) -> str:
        return self.label

    def metadata(self) -> dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "age_bands": list(self.age_bands),
            "prompt_hint": self.prompt_hint,
            "safety_notes": self.safety_notes,
            "expires_at": self.expires_at.isoformat(),
            "source": self.source,
        }


class TopicSeedService:
    """Provides reviewed static topic seeds for low-energy topic shifts."""

    def __init__(
        self,
        *,
        seed_pack_path: Path | None = None,
        today_provider: Callable[[], date] | None = None,
    ) -> None:
        self._seed_pack_path = seed_pack_path or (
            Path(__file__).resolve().parents[1]
            / "data"
            / "topic_seed_packs_v0_1.json"
        )
        self._today_provider = today_provider or date.today
        self._seed_objects: list[TopicSeed] | None = None

    def seeds_for_parent_policy(
        self,
        parent_policy: Any | None,
        *,
        limit: int = 3,
    ) -> list[str]:
        return [
            seed.prompt_label()
            for seed in self.seed_objects_for_parent_policy(
                parent_policy,
                limit=limit,
            )
        ]

    def seed_objects_for_parent_policy(
        self,
        parent_policy: Any | None,
        *,
        limit: int = 3,
    ) -> list[TopicSeed]:
        age_band = derive_age_band_reply_policy(parent_policy).age_band
        seeds = self._active_seeds_for_age_band(age_band)
        if not seeds and age_band != "unknown":
            seeds = self._active_seeds_for_age_band("unknown")
        return seeds[: max(limit, 0)]

    def _active_seeds_for_age_band(self, age_band: str) -> list[TopicSeed]:
        today = self._today_provider()
        return [
            seed
            for seed in self._load_seed_objects()
            if seed.is_active_for(age_band, today=today)
        ]

    def _load_seed_objects(self) -> list[TopicSeed]:
        if self._seed_objects is not None:
            return self._seed_objects
        raw = json.loads(self._seed_pack_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or not isinstance(raw.get("seeds"), list):
            raise ValueError("Topic seed pack must contain a seeds list")
        seeds = [self._parse_seed(item) for item in raw["seeds"]]
        self._seed_objects = seeds
        return seeds

    def _parse_seed(self, item: Any) -> TopicSeed:
        if not isinstance(item, dict):
            raise ValueError("Topic seed item must be an object")
        missing = REQUIRED_SEED_FIELDS - set(item)
        if missing:
            raise ValueError(f"Topic seed missing fields: {sorted(missing)}")

        seed_id = self._required_string(item, "id")
        label = self._required_string(item, "label")
        prompt_hint = self._required_string(item, "prompt_hint")
        safety_notes = self._required_string(item, "safety_notes")
        source = self._required_string(item, "source")
        if source != "curated_v0_1":
            raise ValueError(f"Topic seed source must be curated_v0_1: {seed_id}")
        if self._contains_unsafe_label(label):
            raise ValueError(f"Topic seed label contains unsafe marker: {seed_id}")
        if "avoid" not in safety_notes.lower():
            raise ValueError(
                "Topic seed safety_notes must include avoid guidance: "
                f"{seed_id}"
            )

        age_bands_raw = item["age_bands"]
        if not isinstance(age_bands_raw, list) or not age_bands_raw:
            raise ValueError(
                f"Topic seed age_bands must be a non-empty list: {seed_id}"
            )
        age_bands = tuple(str(value).strip() for value in age_bands_raw)
        if any(age_band not in ALLOWED_AGE_BANDS for age_band in age_bands):
            raise ValueError(f"Topic seed has unsupported age_band: {seed_id}")

        expires_at = date.fromisoformat(self._required_string(item, "expires_at"))
        return TopicSeed(
            id=seed_id,
            label=label,
            age_bands=age_bands,
            prompt_hint=prompt_hint,
            safety_notes=safety_notes,
            expires_at=expires_at,
            source=source,
        )

    def _required_string(self, item: dict[str, Any], key: str) -> str:
        value = str(item.get(key) or "").strip()
        if not value:
            raise ValueError(f"Topic seed field must not be blank: {key}")
        return value

    def _contains_unsafe_label(self, label: str) -> bool:
        normalized = label.lower().replace(" ", "")
        return any(marker.lower() in normalized for marker in UNSAFE_LABEL_MARKERS)
