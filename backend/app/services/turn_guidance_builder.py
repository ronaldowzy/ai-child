from collections.abc import Sequence

from pydantic import BaseModel, Field

from app.domain.model_types import ModelMessage


class TurnGuidanceContext(BaseModel):
    hints: list[str] = Field(default_factory=list)
    guidance: dict[str, str] = Field(default_factory=dict)
    recent_topic: str | None = None
    same_topic_score: int = 0


class TurnGuidanceBuilder:
    """Builds lightweight prompt guidance for one child speech turn."""

    _OPERATION_ASIDE_MARKERS = (
        "按一下",
        "说完",
        "按钮",
        "录音",
        "再按",
        "点一下",
        "结束录音",
    )
    _EXAGGERATION_MARKERS = (
        "每天十五公里",
        "十五公里",
        "累死了",
        "要死了",
        "快不行了",
        "超级",
        "无敌",
        "特别特别",
    )
    _SPORT_CONTEXT_MARKERS = (
        "跑完",
        "跑步",
        "运动",
        "比赛",
        "玩完",
        "练完",
        "训练",
        "跑",
    )
    _DISCOMFORT_MARKERS = ("要死了", "累死了", "快不行了", "喘死了")
    _TOPIC_CHANGE_MARKERS = (
        "换个话题",
        "聊点别的",
        "别聊这个",
        "不说了",
        "算了",
    )
    _BEDTIME_CLOSE_MARKERS = (
        "明天再聊",
        "我要睡觉",
        "我得睡觉",
        "晚安",
        "困了",
    )

    def build(
        self,
        *,
        child_text: str,
        conversation_history: Sequence[ModelMessage] | None = None,
    ) -> TurnGuidanceContext:
        normalized = self._normalize(child_text)
        hints: list[str] = []
        guidance: dict[str, str] = {}

        self._add_hint(
            normalized,
            hints=hints,
            guidance=guidance,
            hint="possible_operation_aside",
            markers=self._OPERATION_ASIDE_MARKERS,
            instruction="本轮可能包含操作旁白，优先回应孩子真实内容，不围绕按按钮、录音、说完再按展开。",
        )
        self._add_hint(
            normalized,
            hints=hints,
            guidance=guidance,
            hint="possible_child_exaggeration",
            markers=self._EXAGGERATION_MARKERS,
            instruction="本轮可能有儿童夸张、玩笑或误听表达，先软确认，不要把数字或程度词立刻事实化、医学化。",
        )
        if self._contains_any(
            normalized,
            self._SPORT_CONTEXT_MARKERS,
        ) and self._contains_any(normalized, self._DISCOMFORT_MARKERS):
            self._set_hint(
                hints=hints,
                guidance=guidance,
                hint="body_discomfort_watch_lite",
                instruction="运动、跑步或比赛语境里的“要死了/累死了”优先理解为可能的夸张疲惫；只做一轮温和确认，若孩子否认疼痛或说父母知道，就快速收束。",
            )
        self._add_hint(
            normalized,
            hints=hints,
            guidance=guidance,
            hint="child_requests_topic_change",
            markers=self._TOPIC_CHANGE_MARKERS,
            instruction="孩子要求换题时立即尊重，不再追问原话题；给两个轻松可选方向，也允许孩子自己说别的。",
        )
        self._add_hint(
            normalized,
            hints=hints,
            guidance=guidance,
            hint="bedtime_close_requested",
            markers=self._BEDTIME_CLOSE_MARKERS,
            instruction="孩子表达明天再聊、睡觉或晚安时，短收尾，不再提问，不拉长对话。",
        )

        recent_topic, same_topic_score = self._recent_topic(
            child_text=child_text,
            conversation_history=conversation_history or [],
        )
        if same_topic_score >= 4 and self._is_short_or_boundary_reply(normalized):
            self._set_hint(
                hints=hints,
                guidance=guidance,
                hint="same_topic_too_long",
                instruction="最近多轮可能持续围绕同一普通话题且孩子回答变短，提供换轨机会，不继续追问旧话题。",
            )

        return TurnGuidanceContext(
            hints=hints,
            guidance=guidance,
            recent_topic=recent_topic,
            same_topic_score=same_topic_score,
        )

    def _recent_topic(
        self,
        *,
        child_text: str,
        conversation_history: Sequence[ModelMessage],
    ) -> tuple[str | None, int]:
        user_texts = [
            message.content
            for message in conversation_history[-8:]
            if message.role == "user" and isinstance(message.content, str)
        ]
        user_texts.append(child_text)
        normalized_texts = [self._normalize(text) for text in user_texts]

        sports_score = sum(
            1
            for text in normalized_texts
            if self._contains_any(text, self._SPORT_CONTEXT_MARKERS)
        )
        body_score = sum(
            1
            for text in normalized_texts
            if self._contains_any(text, ("腿", "疼", "酸", "累", "喘", "身体"))
        )
        if sports_score >= max(body_score, 2):
            return "运动比赛/跑步", sports_score
        if body_score >= 3:
            return "身体感受", body_score
        return None, max(sports_score, body_score)

    def _add_hint(
        self,
        normalized: str,
        *,
        hints: list[str],
        guidance: dict[str, str],
        hint: str,
        markers: tuple[str, ...],
        instruction: str,
    ) -> None:
        if self._contains_any(normalized, markers):
            self._set_hint(
                hints=hints,
                guidance=guidance,
                hint=hint,
                instruction=instruction,
            )

    def _set_hint(
        self,
        *,
        hints: list[str],
        guidance: dict[str, str],
        hint: str,
        instruction: str,
    ) -> None:
        if hint not in hints:
            hints.append(hint)
        guidance[hint] = instruction

    def _is_short_or_boundary_reply(self, normalized: str) -> bool:
        if len(normalized) <= 8:
            return True
        return self._contains_any(normalized, self._TOPIC_CHANGE_MARKERS)

    def _normalize(self, text: str) -> str:
        return text.strip().lower().replace(" ", "")

    def _contains_any(self, text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)
