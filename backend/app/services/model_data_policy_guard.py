from typing import Any

from app.domain.model_types import ModelProfile, ModelProviderType, ModelRequest


class ModelDataPolicyBlockedError(RuntimeError):
    pass


class ModelDataPolicyGuard:
    def validate(self, *, request: ModelRequest, profile: ModelProfile) -> None:
        if profile.provider_type == ModelProviderType.MOCK:
            return

        metadata = request.metadata
        policy = profile.data_policy
        reasons: list[str] = []

        if policy.external_transmission and self._metadata_flag(
            metadata, "contains_child_data"
        ):
            if not policy.allow_child_data:
                reasons.append("child_data_not_allowed")
            if not policy.retention_policy_checked:
                reasons.append("retention_policy_not_checked")

        if self._metadata_flag(metadata, "contains_image") and not policy.allow_image:
            reasons.append("image_not_allowed")

        if self._metadata_flag(metadata, "contains_audio") and not policy.allow_audio:
            reasons.append("audio_not_allowed")

        if reasons:
            raise ModelDataPolicyBlockedError(
                "Model data policy blocked external provider call: "
                f"profile={profile.profile_name}, "
                f"provider={profile.provider_name}, "
                f"reasons={','.join(reasons)}"
            )

    def _metadata_flag(self, metadata: dict[str, Any], key: str) -> bool:
        value = metadata.get(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return False
