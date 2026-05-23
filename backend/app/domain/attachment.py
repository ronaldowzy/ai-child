import base64
import binascii
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, Field, field_validator

from app.domain.schemas.conversation import Reply, SessionState, UiAction


class AttachmentType(StrEnum):
    IMAGE = "image"
    HOMEWORK_PHOTO = "homework_photo"


class ImagePurpose(StrEnum):
    SHARE = "share"
    ASK_WHAT_IS_THIS = "ask_what_is_this"
    TELL_STORY = "tell_story"
    LEARNING_HOMEWORK = "learning_homework"
    READING_TEXT = "reading_text"
    ART_FEEDBACK = "art_feedback"
    PRIVACY_SENSITIVE = "privacy_sensitive"
    UNSAFE_UNKNOWN = "unsafe_unknown"


class AttachmentStatus(StrEnum):
    OCR_READY = "ocr_ready"
    IMAGE_READY = "image_ready"
    NEEDS_RETRY = "needs_retry"


class RecognizedContent(BaseModel):
    type: Literal[
        "homework_problem",
        "image_observation",
        "privacy_sensitive",
        "unsafe_unknown",
    ] = "image_observation"
    text: str | None = Field(default=None, max_length=2000)
    confidence: float = Field(..., ge=0.0, le=1.0)
    provider_name: str
    image_purpose: ImagePurpose | None = None
    child_caption: str | None = Field(default=None, max_length=1000)
    fallback_action: str | None = None


class AttachmentCreateRequest(BaseModel):
    MAX_IMAGE_BYTES: ClassVar[int] = 5 * 1024 * 1024
    ALLOWED_IMAGE_DATA_URI_PREFIXES: ClassVar[tuple[str, ...]] = (
        "data:image/png;base64,",
        "data:image/jpeg;base64,",
        "data:image/webp;base64,",
    )

    child_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    attachment_type: AttachmentType
    image_purpose: ImagePurpose | None = None
    file_id: str | None = Field(default=None, min_length=1, max_length=200)
    image_data_uri: str | None = Field(default=None, max_length=7_000_000)
    mock_ocr_text: str | None = Field(default=None, max_length=2000)
    mock_vision_text: str | None = Field(default=None, max_length=2000)
    child_caption: str | None = Field(default=None, max_length=1000)
    mock_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("image_data_uri")
    @classmethod
    def validate_image_data_uri(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.startswith(cls.ALLOWED_IMAGE_DATA_URI_PREFIXES):
            raise ValueError("image_data_uri must be png, jpeg, or webp data URI")
        _, encoded = value.split(",", 1)
        try:
            decoded = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("image_data_uri must contain valid base64") from exc
        if len(decoded) > cls.MAX_IMAGE_BYTES:
            raise ValueError("image_data_uri decoded image exceeds 5MB")
        return value


class AttachmentRecord(BaseModel):
    id: str
    child_id: str
    session_id: str
    attachment_type: AttachmentType
    image_purpose: ImagePurpose | None = None
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
    mime_type: str | None = None
    size_bytes: int | None = None
    created_at: datetime | None = None
