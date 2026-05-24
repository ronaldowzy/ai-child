from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgeBandReplyPolicy:
    age_band: str
    min_chars: int
    max_chars: int
    question_policy: str

    @property
    def reply_char_budget(self) -> str:
        return f"{self.min_chars}-{self.max_chars} 个汉字"

    def model_dump(self) -> dict[str, Any]:
        return {
            "age_band": self.age_band,
            "reply_char_budget": {
                "min_chars": self.min_chars,
                "max_chars": self.max_chars,
                "label": self.reply_char_budget,
            },
            "question_policy": self.question_policy,
        }


_BUDGETS = {
    "age_5_6": (30, 80),
    "age_7_8": (60, 140),
    "age_9_10": (90, 220),
    "unknown": (60, 120),
}

_QUESTION_POLICY = (
    "每轮最多一个主问题；连续多轮已经提问时，本轮先回应和陈述，"
    "不要再添加新的追问钩子；孩子表达换话题、不聊了、睡觉了或纠正你时，"
    "先尊重边界或修正理解。"
)


def derive_age_band_reply_policy(parent_policy: Any | None) -> AgeBandReplyPolicy:
    preferences = _communication_preferences(parent_policy)
    explicit_age_band = _normalize_age_band(preferences.get("age_band"))
    if explicit_age_band is not None:
        return _policy_for(explicit_age_band)

    numeric_age = _coerce_age(preferences.get("child_age"))
    if numeric_age is None:
        numeric_age = _coerce_age(preferences.get("age"))
    if numeric_age is None:
        return _policy_for("age_7_8")
    if 5 <= numeric_age <= 6:
        return _policy_for("age_5_6")
    if 7 <= numeric_age <= 8:
        return _policy_for("age_7_8")
    if 9 <= numeric_age <= 10:
        return _policy_for("age_9_10")
    return _policy_for("unknown")


def _policy_for(age_band: str) -> AgeBandReplyPolicy:
    min_chars, max_chars = _BUDGETS[age_band]
    return AgeBandReplyPolicy(
        age_band=age_band,
        min_chars=min_chars,
        max_chars=max_chars,
        question_policy=_QUESTION_POLICY,
    )


def _communication_preferences(parent_policy: Any | None) -> dict[str, Any]:
    data = _to_mapping(parent_policy)
    preferences = data.get("communication_preferences")
    if isinstance(preferences, Mapping):
        return dict(preferences)
    return {}


def _normalize_age_band(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower().replace("-", "_")
    normalized = normalized.replace("岁", "").replace(" ", "")
    aliases = {
        "5_6": "age_5_6",
        "age_5_6": "age_5_6",
        "7_8": "age_7_8",
        "age_7_8": "age_7_8",
        "9_10": "age_9_10",
        "age_9_10": "age_9_10",
        "unknown": "unknown",
        "age_unknown": "unknown",
    }
    return aliases.get(normalized)


def _coerce_age(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
    return None


def _to_mapping(value: Any | None) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return {}
