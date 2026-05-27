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
    """Quality gate for image intake and routing."""

    HOMEWORK_OCR_CONFIDENCE_THRESHOLD = 0.75
    IMAGE_OBSERVATION_CONFIDENCE_THRESHOLD = 0.65

    def decide_homework_photo(
        self, recognized_content: RecognizedContent
    ) -> ModalityDecision:
        return self.decide_image_attachment(recognized_content)

    _PROBLEM_NUMBER_PATTERN = re.compile(
        r"(第?\s*\d+\s*题|[\d]+\s*[\.、]|[（(]\s*\d+\s*[)）])"
    )

    def decide_image_attachment(
        self, recognized_content: RecognizedContent
    ) -> ModalityDecision:
        if recognized_content.type == "privacy_sensitive":
            return ModalityDecision(
                status=AttachmentStatus.IMAGE_READY,
                recognized_content=recognized_content,
                reply_text=(
                    "这张图可能有家庭地址、电话、学校名字或类似隐私信息。"
                    "这些内容不要随便发给 AI 或陌生人，先请家长帮你确认。"
                ),
                needs_input="privacy_boundary_ack",
                sub_scene="privacy_boundary",
                active_scene="privacy.boundary",
                reply_emotion="steady",
                quick_actions=[
                    QuickAction(id="understand_privacy", label="我知道了"),
                    QuickAction(id="ask_parent", label="问家长"),
                ],
            )

        if recognized_content.image_purpose != ImagePurpose.LEARNING_HOMEWORK:
            visible_detail = self._child_visible_image_detail(recognized_content)
            if recognized_content.confidence < self.IMAGE_OBSERVATION_CONFIDENCE_THRESHOLD:
                reply_text = (
                    "这次看得不太清楚，但我知道你是想拿给我看。"
                    "你可以告诉我它是什么，或者再拍一张更清楚的。"
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
                        QuickAction(id="tell_what_it_is", label="我来说说"),
                        QuickAction(id="retake_photo", label="再拍一张"),
                    ],
                )
            if visible_detail:
                reply_text = f"我看到像是{visible_detail}。你可以给它起个名字，或者告诉我发生了什么。"
            else:
                reply_text = "图片已经传上来啦。你可以告诉我你最想让小白狐看哪里。"
            return ModalityDecision(
                status=AttachmentStatus.IMAGE_READY,
                recognized_content=recognized_content,
                reply_text=reply_text,
                needs_input=None,
                sub_scene="image_share",
                active_scene="conversation.open",
                reply_emotion="encourage",
                quick_actions=[
                    QuickAction(id="give_name", label="起个名字"),
                    QuickAction(id="tell_story", label="讲个故事"),
                    QuickAction(id="say_what_happened", label="说说看"),
                ],
            )

        if recognized_content.text and recognized_content.confidence >= self.HOMEWORK_OCR_CONFIDENCE_THRESHOLD:
            return self._homework_intake_decision(recognized_content)

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

    def _homework_intake_decision(
        self, recognized_content: RecognizedContent
    ) -> ModalityDecision:
        text = recognized_content.text or ""
        problem_numbers = self._PROBLEM_NUMBER_PATTERN.findall(text)
        has_multiple_problems = len(problem_numbers) >= 2

        if has_multiple_problems:
            return ModalityDecision(
                status=AttachmentStatus.OCR_READY,
                recognized_content=recognized_content,
                reply_text=(
                    "我看到这张图里好像有几道题。"
                    "你告诉我题号，或者说这道题开头几个字，我先帮你把题目对准。"
                ),
                needs_input="homework_problem_locator",
                sub_scene="homework_problem_locator",
                active_scene="learning.homework_help",
                quick_actions=[
                    QuickAction(id="say_problem_number", label="说题号"),
                    QuickAction(id="read_first_words", label="读开头几个字"),
                ],
            )

        summary = self._extract_problem_summary(text)
        if summary:
            reply_text = (
                f"我先帮你对一下题目：{summary}。"
                "这道题先别急着算，我们先看它问的是什么。"
            )
        else:
            reply_text = (
                "我看到了这道题，但还想先和你对一下题目内容。"
                "你能读一下题目开头那一句吗？"
            )
        return ModalityDecision(
            status=AttachmentStatus.OCR_READY,
            recognized_content=recognized_content,
            reply_text=reply_text,
            needs_input="problem_statement_confirm",
            sub_scene="homework_statement_confirm",
            active_scene="learning.homework_help",
        )

    @staticmethod
    def _extract_problem_summary(text: str) -> str | None:
        cleaned = text.strip()
        if not cleaned:
            return None
        separators = ["。", "！", "？", "\n"]
        first_sentence_end = len(cleaned)
        for sep in separators:
            idx = cleaned.find(sep)
            if 0 <= idx < first_sentence_end:
                first_sentence_end = idx
        first_sentence = cleaned[:first_sentence_end].strip()
        if len(first_sentence) > 40:
            first_sentence = first_sentence[:40].rstrip("，,、；;：:")
            first_sentence += "……"
        return first_sentence if len(first_sentence) >= 4 else None

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
