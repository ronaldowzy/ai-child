from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.domain.schemas.conversation import Reply, SessionState, UiAction


class AttachmentType(StrEnum):
    HOMEWORK_PHOTO = "homework_photo"


class AttachmentStatus(StrEnum):
    OCR_READY = "ocr_ready"
    NEEDS_RETRY = "needs_retry"


class RecognizedContent(BaseModel):
    type: Literal["homework_problem"] = "homework_problem"
    text: str | None = Field(default=None, max_length=2000)
    confidence: float = Field(..., ge=0.0, le=1.0)
    provider_name: str
    fallback_action: str | None = None


class AttachmentCreateRequest(BaseModel):
    child_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    attachment_type: AttachmentType
    file_id: str | None = Field(default=None, min_length=1, max_length=200)
    mock_ocr_text: str | None = Field(default=None, max_length=2000)
    mock_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AttachmentRecord(BaseModel):
    id: str
    child_id: str
    session_id: str
    attachment_type: AttachmentType
    status: AttachmentStatus
    recognized_content: RecognizedContent
    file_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class AttachmentCreateResponse(BaseModel):
    attachment_id: str
    recognized_content: RecognizedContent
    reply: Reply
    ui_actions: list[UiAction] = Field(default_factory=list)
    session_state: SessionState
