import pytest

from app.core.config import Settings
from app.services.runtime_provider_guard import (
    RuntimeProviderConfigurationError,
    RuntimeProviderGuard,
)


def test_runtime_provider_guard_rejects_mock_runtime_provider() -> None:
    settings = Settings(
        model_provider="mock",
        vision_provider="mimo",
        tts_provider="mimo",
        asr_provider="local_sensevoice",
        asr_fallback_provider="mimo",
        allow_mock_runtime=False,
    )

    with pytest.raises(RuntimeProviderConfigurationError) as exc:
        RuntimeProviderGuard(settings).validate()

    assert "CHILD_AI_MODEL_PROVIDER" in str(exc.value)


def test_runtime_provider_guard_allows_test_doubles_only_when_explicit() -> None:
    settings = Settings(
        model_provider="mock",
        vision_provider="mock",
        tts_provider="mock",
        asr_provider="mock",
        asr_fallback_provider="mock",
        allow_mock_runtime=True,
    )

    RuntimeProviderGuard(settings).validate()
