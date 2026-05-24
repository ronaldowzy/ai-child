import re

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
    IMAGE_OBSERVATION_CONFIDENCE_THRESHOLD = 0.65

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
            visible_detail = self._child_visible_image_detail(recognized_content)
            if (
                recognized_content.type == "image_observation"
                and recognized_content.confidence >= self.IMAGE_OBSERVATION_CONFIDENCE_THRESHOLD
                and visible_detail
            ):
                reply_text = (
                    f"我看到图里像是{visible_detail}。"
                    "你想先讲讲它哪里最有意思吗？"
                )
            else:
                reply_text = (
                    "这张图我看得还不太清楚。"
                    "你可以告诉我，你最想让我看哪里？"
                )
            return ModalityDecision(
                status=AttachmentStatus.IMAGE_READY,
                recognized_content=recognized_content,
                reply_text=reply_text,
                needs_input=None,
                sub_scene="image_share",
                active_scene="conversation.open",
                reply_emotion="encourage",
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

    def _child_visible_image_detail(
        self,
        recognized_content: RecognizedContent,
    ) -> str | None:
        text = (recognized_content.text or "").strip()
        if not text:
            return None
        if _looks_private_for_child_detail(text):
            return None

        cleaned = _strip_image_detail_labels(text)
        if not cleaned:
            return None
        if _looks_too_vague_for_child_detail(cleaned):
            return None

        first_part = _first_child_safe_clause(cleaned)
        if not first_part or _looks_too_vague_for_child_detail(first_part):
            return None
        if _looks_private_for_child_detail(first_part):
            return None

        first_part = _strip_image_lead_in(first_part)
        first_part = first_part[:56].strip(" ，,。；;：:")
        if not first_part or _looks_too_vague_for_child_detail(first_part):
            return None
        return first_part


_modality_manager = ModalityManager()


_DETAIL_LABEL_RE = re.compile(
    r"(?i)(child_summary|context_summary|图片描述|图片内容|图片摘要|识别内容|描述|summary|recognized_text)\s*[:：]\s*"
)
_PRIVATE_DETAIL_RE = re.compile(
    r"(\d[\d\-\s]{7,}\d|地址|住址|门牌|电话|手机号|身份证|学校|校名|班级|年级|小区|楼栋)"
)
_VAGUE_DETAIL_RE = re.compile(
    r"(一张图片|一张照片|这张图|测试图|测试图片|想分享给小白狐|看不清|不太清楚|不知道|无法确认|没有明显内容|不确定)"
)
_LEAD_IN_RE = re.compile(r"^(我看到|可以看到|图片里|图里|照片里|画面里|这里)\s*(有|是|像是)?\s*")


def _strip_image_detail_labels(text: str) -> str:
    lines = []
    for raw_line in text.replace("\r", "\n").split("\n"):
        line = _DETAIL_LABEL_RE.sub("", raw_line).strip()
        if line:
            lines.append(line)
    return " ".join(lines).strip()


def _first_child_safe_clause(text: str) -> str:
    separator_indexes = [
        text.find(separator)
        for separator in ("。", "！", "？", "，", ",", "；", ";", "\n")
        if text.find(separator) >= 0
    ]
    if separator_indexes:
        text = text[: min(separator_indexes)]
    return text.strip()


def _strip_image_lead_in(text: str) -> str:
    return _LEAD_IN_RE.sub("", text.strip()).strip()


def _looks_private_for_child_detail(text: str) -> bool:
    return bool(_PRIVATE_DETAIL_RE.search(text))


def _looks_too_vague_for_child_detail(text: str) -> bool:
    normalized = text.strip()
    return len(normalized) < 3 or bool(_VAGUE_DETAIL_RE.search(normalized))


def get_modality_manager() -> ModalityManager:
    return _modality_manager
