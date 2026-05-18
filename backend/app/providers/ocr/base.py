from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from app.domain.attachment import AttachmentType, RecognizedContent


class OCRProviderError(RuntimeError):
    """Base error for OCR provider failures."""


class OCRProviderDisabledError(OCRProviderError):
    pass


class OCRRequest(BaseModel):
    attachment_type: AttachmentType
    file_id: str | None = None
    mock_ocr_text: str | None = None
    mock_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseOCRProvider(ABC):
    def __init__(self, *, provider_name: str, enabled: bool = True) -> None:
        self.provider_name = provider_name
        self.enabled = enabled

    @abstractmethod
    def recognize(self, request: OCRRequest) -> RecognizedContent:
        raise NotImplementedError
