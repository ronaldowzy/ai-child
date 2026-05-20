from app.core.config import Settings
from app.domain.tts import TtsProviderName


class TtsDataPolicyBlockedError(RuntimeError):
    pass


class TtsDataPolicyGuard:
    def validate(
        self,
        *,
        provider: TtsProviderName,
        settings: Settings,
        contains_child_text: bool = True,
    ) -> None:
        if provider == TtsProviderName.MOCK:
            return

        reasons: list[str] = []
        if provider == TtsProviderName.MIMO:
            if not settings.mimo_tts_enabled:
                reasons.append("mimo_tts_disabled")
            if not settings.mimo_tts_api_key:
                reasons.append("missing_mimo_tts_api_key")
            if contains_child_text and not settings.mimo_tts_allow_child_text:
                reasons.append("child_text_not_allowed")
            if not settings.mimo_tts_retention_policy_checked:
                reasons.append("retention_policy_not_checked")

        if reasons:
            raise TtsDataPolicyBlockedError(
                "TTS data policy blocked external provider call: "
                f"provider={provider.value}, reasons={','.join(reasons)}"
            )
