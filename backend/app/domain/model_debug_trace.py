from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _trace_id() -> str:
    return f"model_trace_{uuid4().hex}"


class ModelDebugTraceCreate(BaseModel):
    id: str = Field(default_factory=_trace_id)
    created_at: datetime = Field(default_factory=_utc_now)
    request_id: str | None = None
    task_type: str
    profile_name: str | None = None
    provider_name: str | None = None
    model_name: str | None = None
    child_id: str | None = None
    session_id: str | None = None
    child_id_hash: str | None = None
    session_id_hash: str | None = None
    request_messages_json: list[dict[str, Any]] | None = None
    request_input_text: str | None = None
    request_context_json: dict[str, Any] | None = None
    request_metadata_json: dict[str, Any] | None = None
    request_params_json: dict[str, Any] | None = None
    response_text: str | None = None
    response_structured_output_json: dict[str, Any] | None = None
    response_metadata_json: dict[str, Any] | None = None
    fallback_used: bool = False
    policy_blocked: bool = False
    error_type: str | None = None
    error_detail: str | None = None
    elapsed_ms: float | None = None
    trace_source: str = "model_registry"
    environment: str | None = None


class ModelDebugTrace(ModelDebugTraceCreate):
    pass
