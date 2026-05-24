from app.services.age_band_policy import derive_age_band_reply_policy


def test_age_band_policy_defaults_to_age_7_8() -> None:
    policy = derive_age_band_reply_policy(parent_policy=None)

    assert policy.age_band == "age_7_8"
    assert policy.min_chars == 60
    assert policy.max_chars == 140
    assert "每轮最多一个主问题" in policy.question_policy


def test_age_band_policy_uses_explicit_age_band() -> None:
    policy = derive_age_band_reply_policy(
        {"communication_preferences": {"age_band": "age_5_6"}}
    )

    assert policy.age_band == "age_5_6"
    assert policy.reply_char_budget == "30-80 个汉字"


def test_age_band_policy_uses_numeric_child_age() -> None:
    policy = derive_age_band_reply_policy(
        {"communication_preferences": {"child_age": 10}}
    )

    assert policy.age_band == "age_9_10"
    assert policy.reply_char_budget == "90-220 个汉字"


def test_age_band_policy_allows_explicit_unknown_budget() -> None:
    policy = derive_age_band_reply_policy(
        {"communication_preferences": {"age_band": "unknown"}}
    )

    assert policy.age_band == "unknown"
    assert policy.reply_char_budget == "60-120 个汉字"
