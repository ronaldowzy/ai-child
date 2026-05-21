from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import logging
import re
from typing import Any


_STANDARD_RECORD_FIELDS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
    "asctime",
}


_SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)((?:api[_-]?key|token|secret)\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{12,}"),
)


def hash_identifier(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def redact_string(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(r"\1[REDACTED]", redacted)
    if "?" in redacted and ("/media/tts/" in redacted or "audio" in redacted):
        redacted = redacted.split("?", 1)[0] + "?[REDACTED]"
    return redacted


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_string(value)
    if isinstance(value, dict):
        return {str(key): redact_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    return value


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        from app.middleware.request_id import get_request_id

        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", None) or record.getMessage(),
            "request_id": getattr(record, "request_id", None) or get_request_id(),
        }
        message = record.getMessage()
        if message and message != payload["event"]:
            payload["message"] = message

        for key, value in record.__dict__.items():
            if key in _STANDARD_RECORD_FIELDS or key in payload:
                continue
            payload[key] = redact_value(value)

        if record.exc_info:
            payload["error_type"] = (
                payload.get("error_type") or record.exc_info[0].__name__
            )
            payload["exception"] = redact_string(self.formatException(record.exc_info))

        return json.dumps(
            redact_value(payload),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
