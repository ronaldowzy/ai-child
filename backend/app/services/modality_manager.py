from pydantic import BaseModel, Field

from app.domain.attachment import AttachmentStatus, RecognizedContent
from app.domain.schemas.conversation import QuickAction


class ModalityDecision(BaseModel):
    status: AttachmentStatus
    recognized_content: RecognizedContent
    reply_text: str
    needs_input: str
    sub_scene: str
    quick_actions: list[QuickAction] = Field(default_factory=list)


class ModalityManager:
    """Quality gate for v0.1 multimodal homework intake."""

    HOMEWORK_OCR_CONFIDENCE_THRESHOLD = 0.75

    def decide_homework_photo(
        self, recognized_content: RecognizedContent
    ) -> ModalityDecision:
        if (
            recognized_content.text
            and recognized_content.confidence >= self.HOMEWORK_OCR_CONFIDENCE_THRESHOLD
        ):
            return ModalityDecision(
                status=AttachmentStatus.OCR_READY,
                recognized_content=recognized_content,
                reply_text=(
                    "我看清楚了。我们先不急着算。"
                    "你能告诉我：这道题是在问什么吗？"
                ),
                needs_input="problem_understanding",
                sub_scene="ask_problem_understanding",
            )

        fallback_content = recognized_content.model_copy(
            update={"text": None, "fallback_action": "retake_or_speak_problem"}
        )
        return ModalityDecision(
            status=AttachmentStatus.NEEDS_RETRY,
            recognized_content=fallback_content,
            reply_text=(
                "这张照片我还没看清楚。你可以重新拍一张更清楚的，"
                "也可以把题目读给我听。"
            ),
            needs_input="problem_content",
            sub_scene="homework_problem_intake",
            quick_actions=[
                QuickAction(id="take_photo", label="重拍题目"),
                QuickAction(id="speak_problem", label="读题目"),
            ],
        )


_modality_manager = ModalityManager()


def get_modality_manager() -> ModalityManager:
    return _modality_manager
