import pytest

from app.domain.model_types import (
    ModelDataPolicy,
    ModelProfile,
    ModelProviderType,
    ModelRequest,
    ModelTaskType,
)
from app.services.model_data_policy_guard import (
    ModelDataPolicyBlockedError,
    ModelDataPolicyGuard,
)


def _profile(
    *,
    provider_type: ModelProviderType = ModelProviderType.OPENAI_COMPATIBLE,
    data_policy: ModelDataPolicy | None = None,
) -> ModelProfile:
    return ModelProfile(
        id="external_child_chat",
        profile_name="external_child_chat",
        provider_name="external",
        provider_type=provider_type,
        model_name="external-model",
        task_type=ModelTaskType.CHILD_CHAT,
        data_policy=data_policy
        or ModelDataPolicy(
            external_transmission=True,
            allow_child_data=False,
            retention_policy_checked=False,
        ),
    )


def _request(**metadata: bool) -> ModelRequest:
    return ModelRequest(
        task_type=ModelTaskType.CHILD_CHAT,
        input_text="fictional test message",
        metadata=metadata,
    )


def test_guard_blocks_child_data_when_external_profile_does_not_allow_it() -> None:
    guard = ModelDataPolicyGuard()

    with pytest.raises(ModelDataPolicyBlockedError, match="child_data_not_allowed"):
        guard.validate(
            request=_request(contains_child_data=True),
            profile=_profile(
                data_policy=ModelDataPolicy(
                    external_transmission=True,
                    allow_child_data=False,
                    retention_policy_checked=True,
                )
            ),
        )


def test_guard_blocks_child_data_when_retention_policy_is_not_checked() -> None:
    guard = ModelDataPolicyGuard()

    with pytest.raises(
        ModelDataPolicyBlockedError, match="retention_policy_not_checked"
    ):
        guard.validate(
            request=_request(contains_child_data=True),
            profile=_profile(
                data_policy=ModelDataPolicy(
                    external_transmission=True,
                    allow_child_data=True,
                    retention_policy_checked=False,
                )
            ),
        )


@pytest.mark.parametrize(
    ("metadata_key", "expected_reason"),
    [
        ("contains_image", "image_not_allowed"),
        ("contains_audio", "audio_not_allowed"),
    ],
)
def test_guard_blocks_image_and_audio_without_explicit_policy(
    metadata_key: str, expected_reason: str
) -> None:
    guard = ModelDataPolicyGuard()

    with pytest.raises(ModelDataPolicyBlockedError, match=expected_reason):
        guard.validate(
            request=_request(**{metadata_key: True}),
            profile=_profile(
                data_policy=ModelDataPolicy(
                    external_transmission=True,
                    allow_child_data=True,
                    retention_policy_checked=True,
                )
            ),
        )


def test_guard_blocks_external_image_when_retention_policy_is_not_checked() -> None:
    guard = ModelDataPolicyGuard()

    with pytest.raises(
        ModelDataPolicyBlockedError, match="retention_policy_not_checked"
    ):
        guard.validate(
            request=_request(contains_image=True),
            profile=_profile(
                data_policy=ModelDataPolicy(
                    external_transmission=True,
                    allow_image=True,
                    retention_policy_checked=False,
                )
            ),
        )


def test_guard_allows_external_child_data_when_policy_is_complete() -> None:
    guard = ModelDataPolicyGuard()

    guard.validate(
        request=_request(contains_child_data=True),
        profile=_profile(
            data_policy=ModelDataPolicy(
                external_transmission=True,
                allow_child_data=True,
                retention_policy_checked=True,
            )
        ),
    )


def test_guard_does_not_apply_to_mock_profiles() -> None:
    guard = ModelDataPolicyGuard()

    guard.validate(
        request=_request(
            contains_child_data=True,
            contains_image=True,
            contains_audio=True,
        ),
        profile=_profile(provider_type=ModelProviderType.MOCK),
    )
