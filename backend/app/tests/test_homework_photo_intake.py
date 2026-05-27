from app.domain.attachment import AttachmentStatus, ImagePurpose, RecognizedContent
from app.services.modality_manager import ModalityManager


manager = ModalityManager()

MULTI_PROBLEM_TEXT = (
    "第2题：除数是9，商是103，余数是2，问被除数是多少。\n"
    "第6题：一个三位数加一个两位数的和是1065。若在两位数的末尾添一个9，"
    "则它与一个三位数相同。这两个加数分别是多少？\n"
    "第7题：略。"
)

SINGLE_PROBLEM_TEXT = (
    "一个三位数加一个两位数的和是1065。若在两位数的末尾添一个9，"
    "则它与一个三位数相同。这两个加数分别是多少？"
)

IMAGE_CONTEXT_1065 = (
    "第2题：除数是9，商是103，余数是2，问被除数是多少。\n"
    "第6题：一个三位数加一个两位数的和是1065。若在两位数的末尾添一个9，"
    "则它与一个三位数相同。这两个加数分别是多少？\n"
    "第7题：一个长方形的周长是30厘米。"
)


def _make_content(
    text: str,
    *,
    confidence: float = 0.9,
    purpose: ImagePurpose = ImagePurpose.LEARNING_HOMEWORK,
) -> RecognizedContent:
    return RecognizedContent(
        type="homework_problem",
        text=text,
        confidence=confidence,
        provider_name="test",
        image_purpose=purpose,
    )


def test_multi_problem_photo_asks_for_problem_number() -> None:
    content = _make_content(MULTI_PROBLEM_TEXT)
    decision = manager.decide_image_attachment(content)

    assert decision.needs_input == "homework_problem_locator"
    assert decision.sub_scene == "homework_problem_locator"
    assert decision.active_scene == "learning.homework_help"
    assert "题号" in decision.reply_text or "开头几个字" in decision.reply_text
    assert "除数是9" not in decision.reply_text
    assert "答案" not in decision.reply_text
    assert decision.status == AttachmentStatus.OCR_READY


def test_multi_problem_photo_has_locator_quick_actions() -> None:
    content = _make_content(MULTI_PROBLEM_TEXT)
    decision = manager.decide_image_attachment(content)

    action_ids = {a.id for a in decision.quick_actions}
    assert action_ids == {"say_problem_number", "read_first_words"}


def test_single_problem_photo_confirms_statement() -> None:
    content = _make_content(SINGLE_PROBLEM_TEXT)
    decision = manager.decide_image_attachment(content)

    assert decision.needs_input == "problem_statement_confirm"
    assert decision.sub_scene == "homework_statement_confirm"
    assert decision.active_scene == "learning.homework_help"
    assert "对一下题目" in decision.reply_text
    assert "1065" in decision.reply_text or "三位数" in decision.reply_text
    assert decision.status == AttachmentStatus.OCR_READY


def test_low_confidence_homework_photo_asks_to_retake_or_read() -> None:
    content = _make_content("", confidence=0.4)
    decision = manager.decide_image_attachment(content)

    assert decision.needs_input == "problem_content"
    assert decision.sub_scene == "homework_problem_intake"
    assert decision.active_scene == "learning.homework_help"
    assert "没看清楚" in decision.reply_text
    assert decision.status == AttachmentStatus.NEEDS_RETRY


def test_low_confidence_homework_photo_has_retake_actions() -> None:
    content = _make_content("", confidence=0.4)
    decision = manager.decide_image_attachment(content)

    action_ids = {a.id for a in decision.quick_actions}
    assert action_ids == {"take_photo", "speak_problem"}


def test_extract_problem_summary_short_sentence() -> None:
    summary = ModalityManager._extract_problem_summary(SINGLE_PROBLEM_TEXT)
    assert summary is not None
    assert "三位数" in summary or "1065" in summary
    assert len(summary) <= 44  # 40 chars + "……"


def test_extract_problem_summary_empty() -> None:
    assert ModalityManager._extract_problem_summary("") is None
    assert ModalityManager._extract_problem_summary("   ") is None


def test_normal_image_not_routed_to_homework() -> None:
    content = RecognizedContent(
        type="image_observation",
        text="一个红色的积木城堡",
        confidence=0.85,
        provider_name="test",
        image_purpose=ImagePurpose.SHARE,
    )
    decision = manager.decide_image_attachment(content)

    assert decision.active_scene == "conversation.open"
    assert decision.sub_scene == "image_share"
    assert "homework_problem_locator" not in (decision.needs_input or "")
    assert decision.status == AttachmentStatus.IMAGE_READY
