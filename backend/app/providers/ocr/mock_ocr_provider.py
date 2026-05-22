from app.domain.attachment import AttachmentType, ImagePurpose, RecognizedContent
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
        if request.attachment_type == AttachmentType.IMAGE:
            return self._recognize_generic_image(request)

        if request.attachment_type != AttachmentType.HOMEWORK_PHOTO:
            return RecognizedContent(
                type="unsafe_unknown",
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
                type="homework_problem",
                text=request.mock_ocr_text.strip(),
                confidence=requested_confidence if requested_confidence is not None else 0.93,
                provider_name=self.provider_name,
                image_purpose=ImagePurpose.LEARNING_HOMEWORK,
                fallback_action=None,
            )

        confidence = requested_confidence if requested_confidence is not None else 0.93
        if confidence < 0.75:
            return RecognizedContent(
                type="homework_problem",
                text=None,
                confidence=confidence,
                provider_name=self.provider_name,
                image_purpose=ImagePurpose.LEARNING_HOMEWORK,
                fallback_action="retake_or_speak_problem",
            )

        return RecognizedContent(
            type="homework_problem",
            text=self._DEFAULT_HOMEWORK_TEXT,
            confidence=confidence,
            provider_name=self.provider_name,
            image_purpose=ImagePurpose.LEARNING_HOMEWORK,
            fallback_action=None,
        )

    def _recognize_generic_image(self, request: OCRRequest) -> RecognizedContent:
        purpose = request.image_purpose or ImagePurpose.SHARE
        confidence = request.mock_confidence if request.mock_confidence is not None else 0.9
        text = (request.mock_vision_text or request.mock_ocr_text or "").strip()
        if not text:
            text = "孩子拍了一张想分享给小白狐看的图片。"

        if purpose == ImagePurpose.LEARNING_HOMEWORK or self._looks_like_homework(text):
            return RecognizedContent(
                type="homework_problem",
                text=text,
                confidence=confidence,
                provider_name=self.provider_name,
                image_purpose=purpose,
                child_caption=request.child_caption,
                fallback_action=None,
            )
        if purpose == ImagePurpose.PRIVACY_SENSITIVE:
            return RecognizedContent(
                type="privacy_sensitive",
                text=text,
                confidence=confidence,
                provider_name=self.provider_name,
                image_purpose=ImagePurpose.PRIVACY_SENSITIVE,
                child_caption=request.child_caption,
                fallback_action="privacy_boundary",
            )
        return RecognizedContent(
            type="image_observation",
            text=text,
            confidence=confidence,
            provider_name=self.provider_name,
            image_purpose=purpose,
            child_caption=request.child_caption,
            fallback_action=None,
        )

    def _looks_low_confidence(self, file_id: str | None) -> bool:
        if not file_id:
            return False
        normalized = file_id.strip().lower()
        return any(marker in normalized for marker in self._LOW_CONFIDENCE_MARKERS)

    def _looks_like_homework(self, text: str) -> bool:
        normalized = text.strip().lower().replace(" ", "")
        markers = ("题", "作业", "算式", "应用题", "课文", "口算", "数学")
        return any(marker in normalized for marker in markers)
