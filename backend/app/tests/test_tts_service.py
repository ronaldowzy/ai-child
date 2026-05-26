"""Tests for TtsService fallback and config-gating behavior."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings
from app.domain.tts import TtsProviderName, TtsProviderRequest, TtsProviderResult, TtsEmotion, TtsVoiceVersion
from app.providers.tts.base import TtsProviderConfigurationError, TtsProviderError
from app.services.tts_data_policy_guard import TtsDataPolicyBlockedError
from app.services.tts_service import TtsService


def _make_settings(**overrides) -> Settings:
    defaults = dict(
        tts_provider="mimo",
        tts_fallback_provider="",
        tts_enable_local_fallback=False,
        conversation_tts_enabled=False,
        mimo_tts_enabled=True,
        mimo_tts_api_key="test-key",
        mimo_tts_base_url="https://example.com",
        mimo_tts_model="mimo-v2.5-tts-voiceclone",
        mimo_tts_timeout_ms=30000,
        mimo_tts_allow_child_text=True,
        mimo_tts_retention_policy_checked=True,
        sherpa_onnx_tts_enabled=False,
        sherpa_onnx_tts_model_dir="backend/models/tts/sherpa-onnx-zipvoice-distill-int8-zh-en-emilia",
        sherpa_onnx_tts_vocoder_path="backend/models/tts/vocos_24khz.onnx",
        sherpa_onnx_tts_num_threads=2,
        sherpa_onnx_tts_num_steps=4,
        sherpa_onnx_tts_voice_reference_text="ref text",
        xiaobaihu_voice_sample_path="backend/assets/voices/xiaobaohu_voice_v01.wav",
        tts_cache_dir="backend/storage/tts_cache",
        tts_public_base_url="/media/tts",
        tts_max_text_chars=600,
    )
    defaults.update(overrides)
    return Settings(**defaults)


def _make_request() -> TtsProviderRequest:
    return TtsProviderRequest(
        text="你好呀",
        emotion=TtsEmotion.ENCOURAGE,
        voice_version=TtsVoiceVersion.XIAOBAIHU_V01,
        voice_sample_path="/fake/sample.wav",
        voice_sample_sha256="abc123",
        style_prompt="test style prompt",
    )


def _make_result(provider: TtsProviderName = TtsProviderName.MIMO) -> TtsProviderResult:
    return TtsProviderResult(
        audio_bytes=b"RIFF fake wav",
        audio_format="wav",
        content_type="audio/wav",
        duration=1.5,
        provider=provider,
        model="test-model",
    )


class TestLocalFallbackNotUsedByDefault:
    """Local fallback must not activate unless config explicitly enables it."""

    def test_primary_provider_used_when_available(self) -> None:
        settings = _make_settings(tts_provider="mimo", mimo_tts_enabled=True)
        service = TtsService(settings=settings)

        mock_provider = MagicMock()
        mock_provider.generate.return_value = _make_result(TtsProviderName.MIMO)

        with patch.object(service, "_provider", return_value=mock_provider):
            with patch.object(service._data_policy_guard, "validate"):
                result = service._generate_with_fallback(
                    provider=TtsProviderName.MIMO,
                    request=_make_request(),
                )

        assert result.provider == TtsProviderName.MIMO
        mock_provider.generate.assert_called_once()

    def test_primary_error_raises_when_local_fallback_disabled(self) -> None:
        settings = _make_settings(
            tts_provider="mimo",
            sherpa_onnx_tts_enabled=True,
            tts_enable_local_fallback=False,
        )
        service = TtsService(settings=settings)

        mock_provider = MagicMock()
        mock_provider.generate.side_effect = TtsProviderError("remote timeout")

        with patch.object(service, "_provider", return_value=mock_provider):
            with patch.object(service._data_policy_guard, "validate"):
                with pytest.raises(TtsProviderError, match="remote timeout"):
                    service._generate_with_fallback(
                        provider=TtsProviderName.MIMO,
                        request=_make_request(),
                    )

    def test_primary_error_raises_when_sherpa_disabled_even_if_flag_on(self) -> None:
        settings = _make_settings(
            tts_provider="mimo",
            sherpa_onnx_tts_enabled=False,
            tts_enable_local_fallback=True,
        )
        service = TtsService(settings=settings)

        mock_provider = MagicMock()
        mock_provider.generate.side_effect = TtsProviderError("remote timeout")

        with patch.object(service, "_provider", return_value=mock_provider):
            with patch.object(service._data_policy_guard, "validate"):
                with pytest.raises(TtsProviderError, match="remote timeout"):
                    service._generate_with_fallback(
                        provider=TtsProviderName.MIMO,
                        request=_make_request(),
                    )


class TestLocalFallbackWhenEnabled:
    """When both flags are on, transient errors should fall back to sherpa-onnx."""

    def test_transient_error_falls_back_to_sherpa(self) -> None:
        settings = _make_settings(
            tts_provider="mimo",
            sherpa_onnx_tts_enabled=True,
            tts_enable_local_fallback=True,
        )
        service = TtsService(settings=settings)

        mimo_provider = MagicMock()
        mimo_provider.generate.side_effect = TtsProviderError("connection refused")

        sherpa_provider = MagicMock()
        sherpa_provider.generate.return_value = _make_result(TtsProviderName.SHERPA_ONNX)

        def provider_switch(name):
            if name == TtsProviderName.MIMO:
                return mimo_provider
            return sherpa_provider

        with patch.object(service, "_provider", side_effect=provider_switch):
            with patch.object(service._data_policy_guard, "validate"):
                result = service._generate_with_fallback(
                    provider=TtsProviderName.MIMO,
                    request=_make_request(),
                )

        assert result.provider == TtsProviderName.SHERPA_ONNX

    def test_data_policy_blocked_falls_back_to_sherpa(self) -> None:
        settings = _make_settings(
            tts_provider="mimo",
            sherpa_onnx_tts_enabled=True,
            tts_enable_local_fallback=True,
        )
        service = TtsService(settings=settings)

        mimo_provider = MagicMock()
        mimo_provider.generate.side_effect = TtsDataPolicyBlockedError("blocked")

        sherpa_provider = MagicMock()
        sherpa_provider.generate.return_value = _make_result(TtsProviderName.SHERPA_ONNX)

        def provider_switch(name):
            if name == TtsProviderName.MIMO:
                return mimo_provider
            return sherpa_provider

        with patch.object(service, "_provider", side_effect=provider_switch):
            with patch.object(service._data_policy_guard, "validate"):
                result = service._generate_with_fallback(
                    provider=TtsProviderName.MIMO,
                    request=_make_request(),
                )

        assert result.provider == TtsProviderName.SHERPA_ONNX


class TestConfigErrorNotMasked:
    """Provider config errors must always raise, never silently fall back."""

    def test_config_error_raises_even_with_fallback_enabled(self) -> None:
        settings = _make_settings(
            tts_provider="mimo",
            sherpa_onnx_tts_enabled=True,
            tts_enable_local_fallback=True,
        )
        service = TtsService(settings=settings)

        mock_provider = MagicMock()
        mock_provider.generate.side_effect = TtsProviderConfigurationError(
            "missing model files"
        )

        with patch.object(service, "_provider", return_value=mock_provider):
            with patch.object(service._data_policy_guard, "validate"):
                with pytest.raises(TtsProviderConfigurationError, match="missing model files"):
                    service._generate_with_fallback(
                        provider=TtsProviderName.MIMO,
                        request=_make_request(),
                    )


class TestProviderIdentityInResult:
    """Result must identify which provider produced the audio."""

    def test_mimo_result_has_mimo_provider(self) -> None:
        settings = _make_settings(tts_provider="mimo")
        service = TtsService(settings=settings)

        mock_provider = MagicMock()
        mock_provider.generate.return_value = _make_result(TtsProviderName.MIMO)

        with patch.object(service, "_provider", return_value=mock_provider):
            with patch.object(service._data_policy_guard, "validate"):
                result = service._generate_with_fallback(
                    provider=TtsProviderName.MIMO,
                    request=_make_request(),
                )

        assert result.provider == TtsProviderName.MIMO

    def test_sherpa_result_has_sherpa_provider(self) -> None:
        settings = _make_settings(
            tts_provider="mimo",
            sherpa_onnx_tts_enabled=True,
            tts_enable_local_fallback=True,
        )
        service = TtsService(settings=settings)

        mimo_provider = MagicMock()
        mimo_provider.generate.side_effect = TtsProviderError("fail")

        sherpa_provider = MagicMock()
        sherpa_provider.generate.return_value = _make_result(TtsProviderName.SHERPA_ONNX)

        def provider_switch(name):
            if name == TtsProviderName.MIMO:
                return mimo_provider
            return sherpa_provider

        with patch.object(service, "_provider", side_effect=provider_switch):
            with patch.object(service._data_policy_guard, "validate"):
                result = service._generate_with_fallback(
                    provider=TtsProviderName.MIMO,
                    request=_make_request(),
                )

        assert result.provider == TtsProviderName.SHERPA_ONNX
        assert result.model == "test-model"
