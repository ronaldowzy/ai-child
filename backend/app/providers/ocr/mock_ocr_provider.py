from app.domain.attachment import AttachmentType, RecognizedContent
from app.providers.ocr.base import (
    BaseOCRProvider,
    OCRProviderDisabledError,
    OCRRequest,
)


class MockOCRProvider(BaseOCRProvider):
    """OCR placeholder for v0.1 homework-photo flow."""

    _DEFAULT_HOMEWORK_TEXT = "小明有24个苹果，平均分给6个同学，每人几个？"
    _LOW_CONFIDENCE_MARKERS = ("low", "blur", "blurry", "unclear", "bad_photo")

    def __init__(
        self, *, provider_name: str = "mock_ocr", enabled: bool = True
    ) -> None:
        super().__init__(provider_name=provider_name, enabled=enabled)

    def recognize(self, request: OCRRequest) -> RecognizedContent:
        if not self.enabled:
            raise OCRProviderDisabledError(
                f"OCR provider {self.provider_name} is disabled"
            )
        if request.attachment_type != AttachmentType.HOMEWORK_PHOTO:
            return RecognizedContent(
                text=None,
                confidence=0.0,
                provider_name=self.provider_name,
                fallback_action="unsupported_attachment_type",
            )

        requested_confidence = request.mock_confidence
        if self._looks_low_confidence(request.file_id) and requested_confidence is None:
            requested_confidence = 0.35

        if request.mock_ocr_text:
            return RecognizedContent(
                text=request.mock_ocr_text.strip(),
                confidence=requested_confidence if requested_confidence is not None else 0.93,
                provider_name=self.provider_name,
                fallback_action=None,
            )

        confidence = requested_confidence if requested_confidence is not None else 0.93
        if confidence < 0.75:
            return RecognizedContent(
                text=None,
                confidence=confidence,
                provider_name=self.provider_name,
                fallback_action="retake_or_speak_problem",
            )

        return RecognizedContent(
            text=self._DEFAULT_HOMEWORK_TEXT,
            confidence=confidence,
            provider_name=self.provider_name,
            fallback_action=None,
        )

    def _looks_low_confidence(self, file_id: str | None) -> bool:
        if not file_id:
            return False
        normalized = file_id.strip().lower()
        return any(marker in normalized for marker in self._LOW_CONFIDENCE_MARKERS)
