from collections.abc import Callable
import logging
import re
import time
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import hash_identifier, redact_string
from app.domain.model_debug_trace import ModelDebugTraceCreate
from app.domain.model_types import ModelProfile, ModelRequest, ModelResponse
from app.middleware.request_id import get_request_id
from app.repositories.model_debug_trace_repository import (
    ModelDebugTraceRepository,
)


logger = logging.getLogger("app.model_debug_trace")

_SECRET_KEY_MARKERS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "token",
    "secret",
    "password",
)
_RAW_MEDIA_KEYS = (
    "image_data_uri",
    "audio_data_uri",
    "input_audio",
    "input_image",
    "base64",
)
_DATA_URI_RE = re.compile(
    r"data:(?:image|audio|application/octet-stream)/[^;,\s]+;base64,[A-Za-z0-9+/=\r\n]+",
    re.IGNORECASE,
)
_LONG_BASE64_RE = re.compile(r"\b[A-Za-z0-9+/]{120,}={0,2}\b")


class ModelDebugTraceService:
    """Best-effort local model prompt/response trace recorder.

    This is intentionally opt-in and local-dev oriented. It records full text
    prompts when enabled, but still strips secrets and raw media payloads.
    """

    def __init__(
        self,
        *,
        repository: ModelDebugTraceRepository | None = None,
        settings_provider: Callable[[], Settings] = get_settings,
        enabled: bool | None = None,
        full_text: bool | None = None,
        max_text_chars: int | None = None,
    ) -> None:
        self._repository = repository or ModelDebugTraceRepository()
        self._settings_provider = settings_provider
        self._enabled = enabled
        self._full_text = full_text
        self._max_text_chars = max_text_chars

    def record_model_call(
        self,
        *,
        request: ModelRequest,
        profile: ModelProfile | None,
        response: ModelResponse | None,
        started_at: float,
        fallback_used: bool,
        policy_blocked: bool,
        error_type: str | None,
        error_detail: str | None,
    ) -> None:
        settings = self._settings_provider()
        enabled = (
            self._enabled
            if self._enabled is not None
            else settings.model_debug_trace_enabled
        )
        if not enabled:
            return

        try:
            self._repository.save(
                self._trace_create(
                    request=request,
                    profile=profile,
                    response=response,
                    started_at=started_at,
                    fallback_used=fallback_used,
                    policy_blocked=policy_blocked,
                    error_type=error_type,
                    error_detail=error_detail,
                    settings=settings,
                )
            )
        except Exception as exc:
            conversation_context = self._conversation_context(request.context)
            logger.warning(
                "model_debug_trace_failed",
                extra={
                    "event": "model_debug_trace_failed",
                    "request_id": get_request_id(),
                    "task_type": request.task_type.value,
                    "child_id_hash": hash_identifier(
                        conversation_context.get("child_id")
                    ),
                    "session_id_hash": hash_identifier(
                        conversation_context.get("session_id")
                    ),
                    "error_type": exc.__class__.__name__,
                },
            )

    def _trace_create(
        self,
        *,
        request: ModelRequest,
        profile: ModelProfile | None,
        response: ModelResponse | None,
        started_at: float,
        fallback_used: bool,
        policy_blocked: bool,
        error_type: str | None,
        error_detail: str | None,
        settings: Settings,
    ) -> ModelDebugTraceCreate:
        conversation_context = self._conversation_context(request.context)
        max_text_chars = self._effective_max_text_chars(settings)
        full_text = (
            self._full_text
            if self._full_text is not None
            else settings.model_debug_trace_full_text
        )
        provider_name = (
            response.provider_name
            if response
            else (profile.provider_name if profile else None)
        )
        model_name = (
            response.model_name
            if response
            else (profile.model_name if profile else None)
        )
        return ModelDebugTraceCreate(
            request_id=get_request_id(),
            task_type=request.task_type.value,
            profile_name=profile.profile_name if profile else None,
            provider_name=provider_name,
            model_name=model_name,
            child_id=conversation_context.get("child_id"),
            session_id=conversation_context.get("session_id"),
            child_id_hash=hash_identifier(conversation_context.get("child_id")),
            session_id_hash=hash_identifier(conversation_context.get("session_id")),
            request_messages_json=[
                self._sanitize_value(
                    message.model_dump(mode="json"),
                    max_text_chars=max_text_chars,
                    full_text=full_text,
                )
                for message in request.messages
            ],
            request_input_text=self._sanitize_text(
                request.input_text,
                max_text_chars=max_text_chars,
                full_text=full_text,
            ),
            request_context_json=self._sanitize_value(
                request.context,
                max_text_chars=max_text_chars,
                full_text=full_text,
            ),
            request_metadata_json=self._sanitize_value(
                request.metadata,
                max_text_chars=max_text_chars,
                full_text=full_text,
            ),
            request_params_json=(
                profile.default_params.model_dump(mode="json") if profile else None
            ),
            response_text=self._sanitize_text(
                response.response_text if response else None,
                max_text_chars=max_text_chars,
                full_text=full_text,
            ),
            response_structured_output_json=(
                self._sanitize_value(
                    response.structured_output,
                    max_text_chars=max_text_chars,
                    full_text=full_text,
                )
                if response
                else None
            ),
            response_metadata_json=(
                self._sanitize_value(
                    response.metadata,
                    max_text_chars=max_text_chars,
                    full_text=full_text,
                )
                if response
                else None
            ),
            fallback_used=fallback_used,
            policy_blocked=policy_blocked,
            error_type=error_type,
            error_detail=self._sanitize_text(
                error_detail,
                max_text_chars=500,
                full_text=True,
            ),
            elapsed_ms=round((time.perf_counter() - started_at) * 1000, 1),
            environment=settings.environment,
        )

    def _sanitize_value(
        self,
        value: Any,
        *,
        max_text_chars: int,
        full_text: bool,
    ) -> Any:
        if isinstance(value, dict):
            sanitized: dict[str, Any] = {}
            for key, item in value.items():
                key_text = str(key)
                key_lower = key_text.lower()
                if self._is_secret_key(key_lower):
                    sanitized[key_text] = "[redacted]"
                elif self._is_raw_media_key(key_lower):
                    sanitized[key_text] = "[raw_media_omitted]"
                else:
                    sanitized[key_text] = self._sanitize_value(
                        item,
                        max_text_chars=max_text_chars,
                        full_text=full_text,
                    )
            return sanitized
        if isinstance(value, list):
            return [
                self._sanitize_value(
                    item,
                    max_text_chars=max_text_chars,
                    full_text=full_text,
                )
                for item in value
            ]
        if isinstance(value, str):
            return self._sanitize_text(
                value,
                max_text_chars=max_text_chars,
                full_text=full_text,
            )
        return value

    def _sanitize_text(
        self,
        value: str | None,
        *,
        max_text_chars: int,
        full_text: bool,
    ) -> str | None:
        if value is None:
            return None
        if not full_text:
            return "[omitted_by_config]"
        redacted = redact_string(value)
        redacted = _DATA_URI_RE.sub("[raw_media_omitted]", redacted)
        redacted = _LONG_BASE64_RE.sub("[raw_media_omitted]", redacted)
        if len(redacted) > max_text_chars:
            return f"{redacted[:max_text_chars]}...[truncated]"
        return redacted

    def _effective_max_text_chars(self, settings: Settings) -> int:
        raw_value = (
            self._max_text_chars
            if self._max_text_chars is not None
            else settings.model_debug_trace_max_text_chars
        )
        return max(256, int(raw_value))

    def _conversation_context(self, context: dict[str, Any]) -> dict[str, str]:
        raw_context = context.get("conversation")
        if not isinstance(raw_context, dict):
            return {}
        return {
            key: value
            for key, value in raw_context.items()
            if key in {"child_id", "session_id"} and isinstance(value, str)
        }

    def _is_secret_key(self, key_lower: str) -> bool:
        normalized = key_lower.replace("-", "_")
        return any(marker in normalized for marker in _SECRET_KEY_MARKERS)

    def _is_raw_media_key(self, key_lower: str) -> bool:
        normalized = key_lower.replace("-", "_")
        return any(marker in normalized for marker in _RAW_MEDIA_KEYS)
