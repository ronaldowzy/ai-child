from app.core.config import Settings


class RuntimeProviderConfigurationError(RuntimeError):
    pass


class RuntimeProviderGuard:
    """Fails fast when a child-facing runtime would silently use test doubles."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def validate(self) -> None:
        if self._settings.allow_mock_runtime:
            return

        violations = self._mock_provider_violations()
        violations.extend(self._formal_provider_config_violations())

        if violations:
            joined = ", ".join(violations)
            raise RuntimeProviderConfigurationError(
                "Formal runtime provider configuration is incomplete. "
                "Configure real providers before starting a child-facing service. "
                f"Violations: {joined}"
            )

    def _mock_provider_violations(self) -> list[str]:
        violations: list[str] = []
        if self._is_mock(self._settings.model_provider):
            violations.append("CHILD_AI_MODEL_PROVIDER")
        if self._is_mock(self._settings.vision_provider):
            violations.append("CHILD_AI_VISION_PROVIDER")
        if self._is_mock(self._settings.tts_provider):
            violations.append("CHILD_AI_TTS_PROVIDER")
        if self._is_mock(self._settings.asr_provider):
            violations.append("CHILD_AI_ASR_PROVIDER")
        if self._is_mock(self._settings.asr_fallback_provider):
            violations.append("CHILD_AI_ASR_FALLBACK_PROVIDER")
        return violations

    def _formal_provider_config_violations(self) -> list[str]:
        violations: list[str] = []
        if self._settings.model_provider.strip().lower() == "mimo":
            self._require_mimo_model_policy(violations, requires_image=False)
        if self._settings.vision_provider.strip().lower() == "mimo":
            self._require_mimo_model_policy(violations, requires_image=True)
        if self._settings.tts_provider.strip().lower() == "mimo":
            self._require_mimo_tts_policy(violations)
        if self._settings.asr_provider.strip().lower() == "local_sensevoice":
            self._require_local_sensevoice(violations)
        if self._settings.asr_provider.strip().lower() == "mimo":
            self._require_mimo_asr_policy(violations)
        if self._settings.asr_fallback_provider.strip().lower() == "mimo":
            self._require_mimo_asr_policy(violations)
        return list(dict.fromkeys(violations))

    def _require_mimo_model_policy(
        self,
        violations: list[str],
        *,
        requires_image: bool,
    ) -> None:
        if not self._settings.mimo_enabled:
            violations.append("CHILD_AI_MIMO_ENABLED")
        if not self._settings.mimo_api_key:
            violations.append("CHILD_AI_MIMO_API_KEY")
        if not self._settings.mimo_allow_child_data:
            violations.append("CHILD_AI_MIMO_ALLOW_CHILD_DATA")
        if requires_image and not self._settings.mimo_allow_image:
            violations.append("CHILD_AI_MIMO_ALLOW_IMAGE")
        if not self._settings.mimo_retention_policy_checked:
            violations.append("CHILD_AI_MIMO_RETENTION_POLICY_CHECKED")

    def _require_mimo_tts_policy(self, violations: list[str]) -> None:
        if not self._settings.mimo_tts_enabled:
            violations.append("CHILD_AI_MIMO_TTS_ENABLED")
        if not self._settings.mimo_tts_api_key:
            violations.append("CHILD_AI_MIMO_TTS_API_KEY")
        if not self._settings.mimo_tts_allow_child_text:
            violations.append("CHILD_AI_MIMO_TTS_ALLOW_CHILD_TEXT")
        if not self._settings.mimo_tts_retention_policy_checked:
            violations.append("CHILD_AI_MIMO_TTS_RETENTION_POLICY_CHECKED")
        voice_sample = self._settings.resolve_repo_path(
            self._settings.xiaobaihu_voice_sample_path
        )
        if not voice_sample.exists():
            violations.append("CHILD_AI_XIAOBAIHU_VOICE_SAMPLE_PATH")

    def _require_local_sensevoice(self, violations: list[str]) -> None:
        if not self._settings.local_sensevoice_enabled:
            violations.append("CHILD_AI_LOCAL_SENSEVOICE_ENABLED")
        model_path = self._settings.resolve_repo_path(
            self._settings.local_sensevoice_model_path
        )
        tokens_path = self._settings.resolve_repo_path(
            self._settings.local_sensevoice_tokens_path
        )
        if not model_path.exists():
            violations.append("CHILD_AI_LOCAL_SENSEVOICE_MODEL_PATH")
        if not tokens_path.exists():
            violations.append("CHILD_AI_LOCAL_SENSEVOICE_TOKENS_PATH")

    def _require_mimo_asr_policy(self, violations: list[str]) -> None:
        if not self._settings.mimo_asr_enabled:
            violations.append("CHILD_AI_MIMO_ASR_ENABLED")
        if not self._settings.effective_mimo_asr_api_key:
            violations.append("CHILD_AI_MIMO_ASR_API_KEY")
        if not self._settings.mimo_asr_allow_child_audio:
            violations.append("CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO")
        if not self._settings.mimo_asr_retention_policy_checked:
            violations.append("CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED")
        if not self._settings.mimo_asr_no_training_confirmed:
            violations.append("CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED")

    @staticmethod
    def _is_mock(value: str | None) -> bool:
        return (value or "").strip().lower() == "mock"
