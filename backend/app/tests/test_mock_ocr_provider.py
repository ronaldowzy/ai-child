from app.domain.attachment import AttachmentType
from app.providers.ocr.base import OCRRequest
from app.providers.ocr.mock_ocr_provider import MockOCRProvider


def test_mock_ocr_provider_returns_high_confidence_homework_text() -> None:
    provider = MockOCRProvider()

    result = provider.recognize(
        OCRRequest(
            attachment_type=AttachmentType.HOMEWORK_PHOTO,
            file_id="mock_homework_photo",
            mock_ocr_text="小明有24个苹果，平均分给6个同学，每人几个？",
            mock_confidence=0.92,
        )
    )

    assert result.type == "homework_problem"
    assert result.text == "小明有24个苹果，平均分给6个同学，每人几个？"
    assert result.confidence == 0.92
    assert result.provider_name == "mock_ocr"
    assert result.fallback_action is None


def test_mock_ocr_provider_marks_unclear_photo_as_low_confidence() -> None:
    provider = MockOCRProvider()

    result = provider.recognize(
        OCRRequest(
            attachment_type=AttachmentType.HOMEWORK_PHOTO,
            file_id="blurry_homework_photo",
        )
    )

    assert result.text is None
    assert result.confidence < 0.75
    assert result.fallback_action == "retake_or_speak_problem"
