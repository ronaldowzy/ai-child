from __future__ import annotations

from pathlib import Path
import time

from sqlalchemy import text

from app.core.config import Settings, get_settings
from app.db.session import build_engine


class HealthService:
    def __init__(self, *, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def detail(self) -> dict[str, object]:
        components = {
            "postgres": self._postgres_health(),
            "tts_cache": self._tts_cache_health(),
            "xiaobaohu_voice_sample": self._voice_sample_health(),
            "model_config": self._model_config_health(),
            "vision_config": self._vision_config_health(),
            "asr_config": self._asr_config_health(),
            "mimo_tts_config": self._mimo_tts_config_health(),
        }
        status = "ok"
        if any(
            component.get("status") in {"degraded", "missing_config", "missing_policy"}
            for component in components.values()
        ):
            status = "degraded"
        return {
            "status": status,
            "environment": self._settings.environment,
            "mockRuntimeAllowed": self._settings.allow_mock_runtime,
            "components": components,
        }

    def _model_config_health(self) -> dict[str, object]:
        return self._mimo_model_config_health(
            provider=self._settings.model_provider,
            requires_image=False,
        )

    def _vision_config_health(self) -> dict[str, object]:
        return self._mimo_model_config_health(
            provider=self._settings.vision_provider,
            requires_image=True,
        )

    def _mimo_model_config_health(
        self,
        *,
        provider: str,
        requires_image: bool,
    ) -> dict[str, object]:
        provider = provider.strip().lower()
        enabled = self._settings.mimo_enabled or provider == "mimo"
        api_key_present = bool(self._settings.mimo_api_key)
        base_url_present = bool(self._settings.mimo_base_url)
        child_data_allowed = self._settings.mimo_allow_child_data
        image_allowed = self._settings.mimo_allow_image
        retention_policy_checked = self._settings.mimo_retention_policy_checked
        status = "configured"
        if provider != "mimo" or not enabled or not (api_key_present and base_url_present):
            status = "missing_config"
        elif not (child_data_allowed and retention_policy_checked):
            status = "missing_policy"
        elif requires_image and not image_allowed:
            status = "missing_policy"
        return {
            "status": status,
            "provider": provider,
            "enabled": enabled,
            "apiKeyPresent": api_key_present,
            "baseUrlPresent": base_url_present,
            "childDataAllowed": child_data_allowed,
            "imageAllowed": image_allowed,
            "retentionPolicyChecked": retention_policy_checked,
        }

    def _asr_config_health(self) -> dict[str, object]:
        provider = self._settings.asr_provider
        fallback_provider = self._settings.asr_fallback_provider
        local_model = self._settings.resolve_repo_path(
            self._settings.local_sensevoice_model_path
        )
        local_tokens = self._settings.resolve_repo_path(
            self._settings.local_sensevoice_tokens_path
        )
        status = "configured"
        if provider == "mock" or fallback_provider == "mock":
            status = "missing_config"
        elif provider == "local_sensevoice" and not (
            self._settings.local_sensevoice_enabled
            and local_model.exists()
            and local_tokens.exists()
        ):
            status = "missing_config"
        return {
            "status": status,
            "provider": provider,
            "fallbackProvider": fallback_provider,
            "localSenseVoiceEnabled": self._settings.local_sensevoice_enabled,
            "localModelPresent": local_model.exists(),
            "localTokensPresent": local_tokens.exists(),
        }

    def _postgres_health(self) -> dict[str, object]:
        started_at = time.perf_counter()
        engine = None
        try:
            engine = build_engine(self._settings.database_url)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return {
                "status": "ok",
                "latencyMs": round((time.perf_counter() - started_at) * 1000, 1),
            }
        except Exception as exc:
            return {
                "status": "degraded",
                "latencyMs": round((time.perf_counter() - started_at) * 1000, 1),
                "errorType": exc.__class__.__name__,
            }
        finally:
            if engine is not None:
                engine.dispose()

    def _tts_cache_health(self) -> dict[str, object]:
        cache_dir = self._settings.resolve_repo_path(self._settings.tts_cache_dir)
        check_file = cache_dir / ".healthcheck"
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            check_file.write_text("ok", encoding="utf-8")
            check_file.unlink(missing_ok=True)
            return {
                "status": "ok",
                "exists": cache_dir.exists(),
                "writable": True,
            }
        except Exception as exc:
            return {
                "status": "degraded",
                "exists": cache_dir.exists(),
                "writable": False,
                "errorType": exc.__class__.__name__,
            }

    def _voice_sample_health(self) -> dict[str, object]:
        sample_path = self._voice_sample_path()
        return {
            "status": "ok" if sample_path.exists() else "degraded",
            "exists": sample_path.exists(),
        }

    def _mimo_tts_config_health(self) -> dict[str, object]:
        provider = self._settings.tts_provider
        enabled = self._settings.mimo_tts_enabled or provider == "mimo"
        api_key_present = bool(self._settings.mimo_tts_api_key)
        base_url_present = bool(self._settings.mimo_tts_base_url)
        voice_sample_present = self._voice_sample_path().exists()
        child_text_allowed = self._settings.mimo_tts_allow_child_text
        retention_policy_checked = (
            self._settings.mimo_tts_retention_policy_checked
        )

        status = "disabled"
        if enabled:
            if not (api_key_present and base_url_present and voice_sample_present):
                status = "missing_config"
            elif not (child_text_allowed and retention_policy_checked):
                status = "missing_policy"
            else:
                status = "configured"

        return {
            "status": status,
            "provider": provider,
            "enabled": enabled,
            "apiKeyPresent": api_key_present,
            "baseUrlPresent": base_url_present,
            "voiceSamplePresent": voice_sample_present,
            "childTextAllowed": child_text_allowed,
            "retentionPolicyChecked": retention_policy_checked,
        }

    def _voice_sample_path(self) -> Path:
        return self._settings.resolve_repo_path(
            self._settings.xiaobaihu_voice_sample_path
        )
