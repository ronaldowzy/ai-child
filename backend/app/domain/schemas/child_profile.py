"""Canonical child profile schema.

Single source of truth for child profile fields used across
registration, parent settings, auth/me, prompt rendering,
opening, topic suggestions, and parent report.

Gender/call preference are ONLY for respectful addressing,
never for inferring interests, ability, or personality.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# --- Enums ---

CHILD_GENDER_OPTIONS: dict[str, str] = {
    "boy": "男孩",
    "girl": "女孩",
    "prefer_not_to_say": "不填写",
    "custom": "自定义称呼",
    "unknown": "未设置",
}

CHILD_TEMPERAMENT_OPTIONS: dict[str, str] = {
    "warms_up_slowly": "慢热，需要一点时间",
    "expressive": "爱表达，话比较多",
    "concise": "说话短，需要小选择",
    "imaginative": "爱想象/编故事",
    "active": "喜欢运动和动手",
    "sensitive_to_pressure": "不喜欢被追问或催促",
    "easily_frustrated": "遇到困难容易急",
    "curious": "爱问为什么",
}

SUPPORT_STYLE_OPTIONS: dict[str, str] = {
    "offer_two_choices": "多给二选一",
    "ask_fewer_questions": "少追问",
    "encourage_gently": "多温和鼓励",
    "slow_down_explanations": "解释慢一点",
    "use_shorter_sentences": "句子短一点",
    "invite_show_and_tell": "多鼓励展示作品/物品",
    "avoid_competition_framing": "少用输赢/排名框架",
}

LEARNING_SUPPORT_OPTIONS: dict[str, str] = {
    "hint_first": "先提示，不直接给答案",
    "ask_what_child_knows": "先问孩子知道什么",
    "use_examples": "用例子解释",
    "keep_homework_short": "作业帮助要短",
}

# --- Canonical profile schema key ---

CHILD_PROFILE_SCHEMA_VERSION = "child_profile_v0_2"

# All keys stored in communication_preferences
COMMUNICATION_PREFERENCE_KEYS = {
    "child_age",
    "child_grade",
    "child_gender",
    "child_call_preference",
    "child_interests",
    "topic_boundaries",
    "child_temperament",
    "support_style_preferences",
    "learning_support_preferences",
    "child_profile_schema",
}


class ChildProfileUpdate(BaseModel):
    """Fields a parent can update for a child profile."""

    child_nickname: str | None = Field(default=None, max_length=80)
    child_display_name: str | None = Field(default=None, max_length=120)
    child_age: int | None = Field(default=None, ge=5, le=10)
    child_grade: str | None = Field(default=None, max_length=80)
    child_gender: str | None = Field(default=None, max_length=40)
    child_call_preference: str | None = Field(default=None, max_length=120)
    child_interests: list[str] = Field(default_factory=list, max_length=12)
    topic_boundaries: list[str] = Field(default_factory=list, max_length=12)
    child_temperament: list[str] = Field(default_factory=list, max_length=8)
    support_style_preferences: list[str] = Field(default_factory=list, max_length=7)
    learning_support_preferences: list[str] = Field(default_factory=list, max_length=4)


def child_profile_to_communication_preferences(
    profile: ChildProfileUpdate,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge canonical child profile fields into communication_preferences dict."""
    preferences = dict(existing or {})

    if profile.child_age is not None:
        preferences["child_age"] = profile.child_age
    if profile.child_grade is not None:
        preferences["child_grade"] = profile.child_grade.strip()
    if profile.child_gender is not None:
        preferences["child_gender"] = profile.child_gender.strip()
    if profile.child_call_preference is not None:
        preferences["child_call_preference"] = profile.child_call_preference.strip()

    preferences["child_interests"] = _compact_list(profile.child_interests, max_items=12)
    preferences["topic_boundaries"] = _compact_list(profile.topic_boundaries, max_items=12)
    preferences["child_temperament"] = _validate_enum_list(
        profile.child_temperament, CHILD_TEMPERAMENT_OPTIONS
    )
    preferences["support_style_preferences"] = _validate_enum_list(
        profile.support_style_preferences, SUPPORT_STYLE_OPTIONS
    )
    preferences["learning_support_preferences"] = _validate_enum_list(
        profile.learning_support_preferences, LEARNING_SUPPORT_OPTIONS
    )
    preferences["child_profile_schema"] = CHILD_PROFILE_SCHEMA_VERSION

    return preferences


def render_child_profile_for_prompt(
    policy_data: dict[str, Any],
) -> str:
    """Render child profile as internal prompt context.

    Returns a string block for inclusion in the system prompt.
    Gender/call preference are explicitly marked as address-only,
    not for inference of interests, ability, or personality.
    """
    nickname = str(policy_data.get("child_nickname") or "").strip()
    display_name = str(policy_data.get("child_display_name") or "").strip()
    raw_message = str(policy_data.get("parent_message_raw") or "").strip()

    communication_preferences = policy_data.get("communication_preferences")
    preferences = dict(communication_preferences) if isinstance(communication_preferences, dict) else {}

    child_age = _scalar(preferences.get("child_age"))
    child_grade = _scalar(preferences.get("child_grade"))
    child_gender = _scalar(preferences.get("child_gender"))
    call_preference = _scalar(preferences.get("child_call_preference"))
    child_interests = _list(preferences.get("child_interests"))
    topic_boundaries = _list(preferences.get("topic_boundaries"))
    temperament = _list(preferences.get("child_temperament"))
    support_style = _list(preferences.get("support_style_preferences"))
    learning_support = _list(preferences.get("learning_support_preferences"))

    lines: list[str] = []
    if nickname:
        lines.append(f"- child_nickname: {nickname}")
    if display_name:
        lines.append(f"- child_display_name: {display_name}")
    if child_age:
        lines.append(f"- child_age: {child_age}")
    if child_grade:
        lines.append(f"- child_grade: {child_grade}")

    # Gender and call preference - strictly for addressing only
    if child_gender and child_gender not in ("unknown", "未设置"):
        gender_label = CHILD_GENDER_OPTIONS.get(child_gender, child_gender)
        lines.append(
            f"- child_gender: {gender_label}。"
            "只用于尊重称呼和措辞，不推断性格、能力、兴趣或偏好。"
        )
    if call_preference:
        lines.append(
            f"- child_call_preference: {call_preference}。"
            "只用于尊重称呼和措辞，不推断性格、能力或兴趣。"
        )

    if child_interests:
        lines.append(
            "- child_interests: "
            f"{'，'.join(child_interests[:8])}。这是可尝试的轻话题，不要变成任务。"
        )
    if topic_boundaries:
        lines.append(
            "- topic_boundaries: "
            f"{'，'.join(topic_boundaries[:8])}。孩子不想聊时优先尊重，不拉回旧话题。"
        )
    if temperament:
        labels = [CHILD_TEMPERAMENT_OPTIONS.get(t, t) for t in temperament[:6]]
        lines.append(
            "- child_temperament: "
            f"{'，'.join(labels)}。"
            "这些是家长提供的背景参考，不要给孩子贴标签或直接说出来。"
        )
    if support_style:
        labels = [SUPPORT_STYLE_OPTIONS.get(s, s) for s in support_style[:5]]
        lines.append(
            "- support_style_preferences: "
            f"{'，'.join(labels)}。"
            "在回复中自然体现这些支持方式，不要告诉孩子家长设置了这些偏好。"
        )
    if learning_support:
        labels = [LEARNING_SUPPORT_OPTIONS.get(s, s) for s in learning_support[:4]]
        lines.append(
            "- learning_support_preferences: "
            f"{'，'.join(labels)}。"
            "在学习帮助场景中自然体现这些方式。"
        )

    if not raw_message and not lines:
        return "当前没有单独的孩子画像。不要编造孩子的小名、性格或家庭信息。"

    header = (
        "孩子画像来自结构化家长设置和家长寄语的背景信息。"
        "可以用它理解孩子的兴趣、近期状态和沟通节奏；"
        "不要把它当成固定标签，也不要编造寄语中没有的事实。"
    )
    return "\n".join([header, *lines])


def _compact_list(items: list[str], *, max_items: int = 12) -> list[str]:
    compacted: list[str] = []
    for item in items:
        text = str(item).strip()
        if text and text not in compacted:
            compacted.append(text[:40])
    return compacted[:max_items]


def _validate_enum_list(
    items: list[str],
    valid_options: dict[str, str],
) -> list[str]:
    return [item for item in items if item in valid_options]


def _scalar(value: Any) -> str:
    if value is None or isinstance(value, bool):
        return ""
    text = str(value).strip()
    return text[:80]


def _list(value: Any) -> list[str]:
    if isinstance(value, str):
        source = value.replace("，", "\n").replace("、", "\n").replace(",", "\n")
        items = source.splitlines()
    elif isinstance(value, list):
        items = [str(item) for item in value if item is not None]
    else:
        return []
    cleaned = []
    for item in items:
        text = " ".join(item.strip().split())
        if text:
            cleaned.append(text[:60])
    return cleaned
