"""Tests for TtsDataPolicyGuard: local vs external provider policies."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.domain.tts import TtsProviderName
from app.services.tts_data_policy_guard import TtsDataPolicyBlockedError, TtsDataPolicyGuard


def _make_settings(**overrides) -> Settings:
    defaults = dict(
        mimo_tts_enabled=True,
        mimo_tts_api_key="test-key",
        mimo_tts_allow_child_text=True,
        mimo_tts_retention_policy_checked=True,
        sherpa_onnx_tts_enabled=True,
    )
    defaults.update(overrides)
    return Settings(**defaults)


class TestLocalProvidersPassWithoutExternalChecks:
    """sherpa_onnx and mock are local-only; no external data policy checks needed."""

    def test_sherpa_onnx_passes_without_api_key(self) -> None:
        settings = _make_settings(mimo_tts_api_key="")
        guard = TtsDataPolicyGuard()

        guard.validate(
            provider=TtsProviderName.SHERPA_ONNX,
            settings=settings,
            contains_child_text=True,
        )

    def test_sherpa_onnx_passes_when_child_text_not_allowed(self) -> None:
        settings = _make_settings(mimo_tts_allow_child_text=False)
        guard = TtsDataPolicyGuard()

        guard.validate(
            provider=TtsProviderName.SHERPA_ONNX,
            settings=settings,
            contains_child_text=True,
        )

    def test_sherpa_onnx_passes_when_retention_not_checked(self) -> None:
        settings = _make_settings(mimo_tts_retention_policy_checked=False)
        guard = TtsDataPolicyGuard()

        guard.validate(
            provider=TtsProviderName.SHERPA_ONNX,
            settings=settings,
            contains_child_text=True,
        )

    def test_mock_passes_without_checks(self) -> None:
        settings = _make_settings(
            mimo_tts_enabled=False,
            mimo_tts_api_key="",
            mimo_tts_allow_child_text=False,
            mimo_tts_retention_policy_checked=False,
        )
        guard = TtsDataPolicyGuard()

        guard.validate(
            provider=TtsProviderName.MOCK,
            settings=settings,
            contains_child_text=True,
        )


class TestMimoRequiresFullPolicy:
    """MiMo is an external provider; all data policy checks must pass."""

    def test_mimo_blocks_when_disabled(self) -> None:
        settings = _make_settings(mimo_tts_enabled=False)
        guard = TtsDataPolicyGuard()

        with pytest.raises(TtsDataPolicyBlockedError, match="mimo_tts_disabled"):
            guard.validate(
                provider=TtsProviderName.MIMO,
                settings=settings,
                contains_child_text=True,
            )

    def test_mimo_blocks_when_api_key_missing(self) -> None:
        settings = _make_settings(mimo_tts_api_key="")
        guard = TtsDataPolicyGuard()

        with pytest.raises(TtsDataPolicyBlockedError, match="missing_mimo_tts_api_key"):
            guard.validate(
                provider=TtsProviderName.MIMO,
                settings=settings,
                contains_child_text=True,
            )

    def test_mimo_blocks_when_child_text_not_allowed(self) -> None:
        settings = _make_settings(mimo_tts_allow_child_text=False)
        guard = TtsDataPolicyGuard()

        with pytest.raises(TtsDataPolicyBlockedError, match="child_text_not_allowed"):
            guard.validate(
                provider=TtsProviderName.MIMO,
                settings=settings,
                contains_child_text=True,
            )

    def test_mimo_blocks_when_retention_not_checked(self) -> None:
        settings = _make_settings(mimo_tts_retention_policy_checked=False)
        guard = TtsDataPolicyGuard()

        with pytest.raises(TtsDataPolicyBlockedError, match="retention_policy_not_checked"):
            guard.validate(
                provider=TtsProviderName.MIMO,
                settings=settings,
                contains_child_text=True,
            )

    def test_mimo_passes_when_all_checks_ok(self) -> None:
        settings = _make_settings()
        guard = TtsDataPolicyGuard()

        guard.validate(
            provider=TtsProviderName.MIMO,
            settings=settings,
            contains_child_text=True,
        )

    def test_mimo_passes_without_child_text_even_if_not_allowed(self) -> None:
        settings = _make_settings(mimo_tts_allow_child_text=False)
        guard = TtsDataPolicyGuard()

        guard.validate(
            provider=TtsProviderName.MIMO,
            settings=settings,
            contains_child_text=False,
        )
