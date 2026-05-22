from pydantic import BaseModel, Field

from app.domain.attachment import AttachmentStatus, ImagePurpose, RecognizedContent
from app.domain.schemas.conversation import QuickAction


class ModalityDecision(BaseModel):
    status: AttachmentStatus
    recognized_content: RecognizedContent
    reply_text: str
    needs_input: str | None
    sub_scene: str
    active_scene: str = "conversation.open"
    reply_emotion: str = "warm"
    quick_actions: list[QuickAction] = Field(default_factory=list)


class ModalityManager:
    """Quality gate for v0.1 multimodal homework intake."""

    HOMEWORK_OCR_CONFIDENCE_THRESHOLD = 0.75

    def decide_homework_photo(
        self, recognized_content: RecognizedContent
    ) -> ModalityDecision:
        return self.decide_image_attachment(recognized_content)

    def decide_image_attachment(
        self, recognized_content: RecognizedContent
    ) -> ModalityDecision:
        if recognized_content.type == "privacy_sensitive":
            return ModalityDecision(
                status=AttachmentStatus.IMAGE_READY,
                recognized_content=recognized_content,
                reply_text=(
                    "这张图里好像有家庭地址、电话、学校名字或类似隐私信息。"
                    "这些内容不要随便发给 AI 或陌生人，先请爸爸妈妈帮你确认。"
                ),
                needs_input="privacy_boundary_ack",
                sub_scene="privacy_boundary",
                active_scene="privacy.boundary",
                reply_emotion="steady",
                quick_actions=[
                    QuickAction(id="understand_privacy", label="我知道了"),
                    QuickAction(id="ask_parent", label="问爸爸妈妈"),
                ],
            )

        if recognized_content.image_purpose != ImagePurpose.LEARNING_HOMEWORK:
            text = recognized_content.text or "这张图片"
            return ModalityDecision(
                status=AttachmentStatus.IMAGE_READY,
                recognized_content=recognized_content,
                reply_text=(
                    f"我看到你想分享的是：{text}。"
                    "你想让我陪你聊聊它，还是说说你想问哪里？"
                ),
                needs_input=None,
                sub_scene="image_share",
                active_scene="conversation.open",
                reply_emotion="curious",
                quick_actions=[
                    QuickAction(id="talk_about_image", label="聊聊它"),
                    QuickAction(id="make_story", label="编个故事"),
                    QuickAction(id="ask_what_is_this", label="问这是什么"),
                ],
            )

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
                active_scene="learning.homework_help",
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
            active_scene="learning.homework_help",
            quick_actions=[
                QuickAction(id="take_photo", label="重拍题目"),
                QuickAction(id="speak_problem", label="读题目"),
            ],
        )


_modality_manager = ModalityManager()


def get_modality_manager() -> ModalityManager:
    return _modality_manager
