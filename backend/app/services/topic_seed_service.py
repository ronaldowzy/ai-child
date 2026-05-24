import json
from pathlib import Path
from typing import Any

from app.services.age_band_policy import derive_age_band_reply_policy


class TopicSeedService:
    """Provides curated static topic seeds for low-energy topic shifts."""

    def __init__(self, *, seed_pack_path: Path | None = None) -> None:
        self._seed_pack_path = seed_pack_path or (
            Path(__file__).resolve().parents[1]
            / "data"
            / "topic_seed_packs_v0_1.json"
        )
        self._seed_packs: dict[str, list[str]] | None = None

    def seeds_for_parent_policy(
        self,
        parent_policy: Any | None,
        *,
        limit: int = 3,
    ) -> list[str]:
        age_band = derive_age_band_reply_policy(parent_policy).age_band
        packs = self._load_seed_packs()
        seeds = packs.get(age_band) or packs.get("unknown") or []
        return list(seeds[: max(limit, 0)])

    def _load_seed_packs(self) -> dict[str, list[str]]:
        if self._seed_packs is not None:
            return self._seed_packs
        raw = json.loads(self._seed_pack_path.read_text(encoding="utf-8"))
        packs: dict[str, list[str]] = {}
        if isinstance(raw, dict):
            for key, value in raw.items():
                if isinstance(key, str) and isinstance(value, list):
                    packs[key] = [
                        str(item).strip()
                        for item in value
                        if str(item).strip()
                    ]
        self._seed_packs = packs
        return packs
