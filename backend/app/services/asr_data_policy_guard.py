from dataclasses import dataclass

from app.domain.schemas.asr import AsrProviderName


class AsrDataPolicyBlockedError(RuntimeError):
    pass


@dataclass(frozen=True)
class AsrDataPolicySettings:
    provider: AsrProviderName = AsrProviderName.MOCK
    provider_enabled: bool = False
    api_key_present: bool = False
    allow_child_audio: bool = False
    retention_policy_checked: bool = False
    no_training_confirmed: bool = False


class AsrDataPolicyGuard:
    def validate(self, settings: AsrDataPolicySettings) -> None:
        if settings.provider == AsrProviderName.MOCK:
            return

        reasons: list[str] = []
        if settings.provider == AsrProviderName.MIMO:
            if not settings.provider_enabled:
                reasons.append("mimo_asr_disabled")
            if not settings.api_key_present:
                reasons.append("missing_mimo_asr_api_key")
            if not settings.allow_child_audio:
                reasons.append("child_audio_not_allowed")
            if not settings.retention_policy_checked:
                reasons.append("retention_policy_not_checked")
            if not settings.no_training_confirmed:
                reasons.append("no_training_not_confirmed")

        if reasons:
            raise AsrDataPolicyBlockedError(
                "ASR data policy blocked external provider call: "
                f"provider={settings.provider.value}, reasons={','.join(reasons)}"
            )
