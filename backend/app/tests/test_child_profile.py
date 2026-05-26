"""Tests for canonical child profile schema, prompt rendering, and auth integration."""

from __future__ import annotations

from typing import Any

from app.domain.schemas.auth import (
    AuthRegisterRequest,
    profile_preferences_from_input,
)
from app.domain.schemas.child_profile import (
    CHILD_PROFILE_SCHEMA_VERSION,
    ChildProfileUpdate,
    child_profile_to_communication_preferences,
    render_child_profile_for_prompt,
)
from app.services.prompt_manager import PromptManager


# --- Schema tests ---


def test_child_profile_update_accepts_all_fields() -> None:
    profile = ChildProfileUpdate(
        child_nickname="小明",
        child_display_name="张明",
        child_age=7,
        child_grade="二年级",
        child_gender="boy",
        child_call_preference="叫小明",
        child_interests=["恐龙", "画画"],
        topic_boundaries=["学校细节"],
        child_temperament=["warms_up_slowly", "curious"],
        support_style_preferences=["offer_two_choices", "ask_fewer_questions"],
        learning_support_preferences=["hint_first"],
    )
    assert profile.child_gender == "boy"
    assert profile.child_temperament == ["warms_up_slowly", "curious"]
    assert profile.support_style_preferences == ["offer_two_choices", "ask_fewer_questions"]
    assert profile.learning_support_preferences == ["hint_first"]


def test_child_profile_update_defaults_empty() -> None:
    profile = ChildProfileUpdate()
    assert profile.child_gender is None
    assert profile.child_temperament == []
    assert profile.support_style_preferences == []
    assert profile.learning_support_preferences == []


def test_child_profile_to_communication_preferences_includes_all_fields() -> None:
    profile = ChildProfileUpdate(
        child_age=8,
        child_gender="girl",
        child_interests=["画画"],
        child_temperament=["imaginative"],
        support_style_preferences=["encourage_gently"],
        learning_support_preferences=["use_examples"],
    )
    prefs = child_profile_to_communication_preferences(profile)
    assert prefs["child_age"] == 8
    assert prefs["child_gender"] == "girl"
    assert prefs["child_temperament"] == ["imaginative"]
    assert prefs["support_style_preferences"] == ["encourage_gently"]
    assert prefs["learning_support_preferences"] == ["use_examples"]
    assert prefs["child_profile_schema"] == CHILD_PROFILE_SCHEMA_VERSION


def test_child_profile_validates_enum_lists() -> None:
    profile = ChildProfileUpdate(
        child_temperament=["warms_up_slowly", "invalid_value", "curious"],
        support_style_preferences=["offer_two_choices", "not_a_real_option"],
    )
    prefs = child_profile_to_communication_preferences(profile)
    assert prefs["child_temperament"] == ["warms_up_slowly", "curious"]
    assert prefs["support_style_preferences"] == ["offer_two_choices"]


def test_profile_preferences_from_input_includes_new_fields() -> None:
    request = AuthRegisterRequest(
        username="testuser",
        password="testpassword123",
        child_nickname="小明",
        child_age=7,
        child_gender="boy",
        child_temperament=["warms_up_slowly"],
        support_style_preferences=["offer_two_choices"],
        learning_support_preferences=["hint_first"],
    )
    prefs = profile_preferences_from_input(request)
    assert prefs["child_gender"] == "boy"
    assert prefs["child_temperament"] == ["warms_up_slowly"]
    assert prefs["support_style_preferences"] == ["offer_two_choices"]
    assert prefs["learning_support_preferences"] == ["hint_first"]
    assert prefs["child_profile_schema"] == "child_profile_v0_2"


# --- Prompt rendering tests ---


def test_render_child_profile_includes_gender_with_no_inference_note() -> None:
    policy_data: dict[str, Any] = {
        "child_nickname": "小明",
        "communication_preferences": {
            "child_age": 7,
            "child_gender": "boy",
        },
    }
    result = render_child_profile_for_prompt(policy_data)
    assert "child_gender: 男孩" in result
    assert "不推断性格、能力、兴趣或偏好" in result


def test_render_child_profile_includes_temperament() -> None:
    policy_data: dict[str, Any] = {
        "child_nickname": "小明",
        "communication_preferences": {
            "child_temperament": ["warms_up_slowly", "curious"],
        },
    }
    result = render_child_profile_for_prompt(policy_data)
    assert "child_temperament" in result
    assert "慢热" in result
    assert "爱问为什么" in result
    assert "不要给孩子贴标签" in result


def test_render_child_profile_includes_support_style() -> None:
    policy_data: dict[str, Any] = {
        "child_nickname": "小明",
        "communication_preferences": {
            "support_style_preferences": ["offer_two_choices", "ask_fewer_questions"],
        },
    }
    result = render_child_profile_for_prompt(policy_data)
    assert "support_style_preferences" in result
    assert "多给二选一" in result
    assert "少追问" in result


def test_render_child_profile_includes_learning_support() -> None:
    policy_data: dict[str, Any] = {
        "child_nickname": "小明",
        "communication_preferences": {
            "learning_support_preferences": ["hint_first", "use_examples"],
        },
    }
    result = render_child_profile_for_prompt(policy_data)
    assert "learning_support_preferences" in result
    assert "先提示" in result
    assert "用例子解释" in result


def test_render_child_profile_excludes_unknown_gender() -> None:
    policy_data: dict[str, Any] = {
        "child_nickname": "小明",
        "communication_preferences": {
            "child_gender": "unknown",
        },
    }
    result = render_child_profile_for_prompt(policy_data)
    assert "child_gender" not in result


def test_render_child_profile_empty_when_no_data() -> None:
    result = render_child_profile_for_prompt({})
    assert "当前没有单独的孩子画像" in result


def test_render_child_profile_call_preference_no_inference() -> None:
    policy_data: dict[str, Any] = {
        "communication_preferences": {
            "child_call_preference": "叫哥哥",
        },
    }
    result = render_child_profile_for_prompt(policy_data)
    assert "叫哥哥" in result
    assert "不推断性格、能力或兴趣" in result


# --- PromptManager integration tests ---


def test_prompt_manager_renders_new_profile_fields() -> None:
    pm = PromptManager()
    parent_policy: dict[str, Any] = {
        "child_nickname": "小明",
        "child_display_name": "张明",
        "parent_message_raw": "",
        "communication_preferences": {
            "child_age": 7,
            "child_grade": "二年级",
            "child_gender": "boy",
            "child_call_preference": "叫小明",
            "child_interests": ["恐龙", "画画"],
            "topic_boundaries": ["学校细节"],
            "child_temperament": ["warms_up_slowly", "curious"],
            "support_style_preferences": ["offer_two_choices"],
            "learning_support_preferences": ["hint_first"],
        },
    }
    composed = pm.compose("conversation.open", parent_policy=parent_policy)
    prompt = composed.prompt

    # Gender with no-inference note
    assert "child_gender: 男孩" in prompt
    assert "不推断性格、能力、兴趣或偏好" in prompt

    # Temperament
    assert "child_temperament" in prompt
    assert "慢热" in prompt

    # Support style
    assert "support_style_preferences" in prompt
    assert "多给二选一" in prompt

    # Learning support
    assert "learning_support_preferences" in prompt
    assert "先提示" in prompt


def test_prompt_manager_renders_profile_with_minimal_fields() -> None:
    pm = PromptManager()
    parent_policy: dict[str, Any] = {
        "child_nickname": "小明",
        "communication_preferences": {},
    }
    composed = pm.compose("conversation.open", parent_policy=parent_policy)
    prompt = composed.prompt
    assert "child_nickname: 小明" in prompt


def test_prompt_manager_renders_empty_profile() -> None:
    pm = PromptManager()
    composed = pm.compose("conversation.open", parent_policy=None)
    prompt = composed.prompt
    assert "当前没有单独的孩子画像" in prompt


# --- AuthAccountProfile tests ---


def test_auth_account_profile_has_new_fields() -> None:
    from app.domain.schemas.auth import AuthAccountProfile

    profile = AuthAccountProfile(
        child_account_id="acct_test",
        child_id="child_test",
        username="testuser",
        child_nickname="小明",
        child_age=7,
        child_gender="boy",
        child_temperament=["warms_up_slowly"],
        support_style_preferences=["offer_two_choices"],
        learning_support_preferences=["hint_first"],
    )
    assert profile.child_gender == "boy"
    assert profile.child_temperament == ["warms_up_slowly"]
    assert profile.support_style_preferences == ["offer_two_choices"]
    assert profile.learning_support_preferences == ["hint_first"]


def test_auth_account_profile_defaults_empty_lists() -> None:
    from app.domain.schemas.auth import AuthAccountProfile

    profile = AuthAccountProfile(
        child_account_id="acct_test",
        child_id="child_test",
        username="testuser",
    )
    assert profile.child_gender is None
    assert profile.child_temperament == []
    assert profile.support_style_preferences == []
    assert profile.learning_support_preferences == []
