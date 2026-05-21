from pydantic import BaseModel, Field

from app.domain.enums import IntentType, RiskCategory, RiskLevel
from app.domain.model_types import ModelRequest, ModelTaskType
from app.domain.time import TimeContext, TimePeriod
from app.services.model_registry import ModelRegistry, get_model_registry
from app.services.safety_engine import SafetyClassification


class IntentClassification(BaseModel):
    intent: IntentType
    sub_intent: str | None = None
    emotion: str = "neutral"
    risk_level: RiskLevel = RiskLevel.NONE
    needs_modality: bool = False
    suggested_modalities: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    evidence: list[str] = Field(default_factory=list)


class IntentClassifier:
    """Keyword-first intent classifier with MockModelProvider fallback."""

    def __init__(self, *, model_registry: ModelRegistry | None = None) -> None:
        self._model_registry = model_registry or get_model_registry()

    def classify(
        self,
        text: str,
        *,
        time_context: TimeContext | None = None,
        safety: SafetyClassification | None = None,
    ) -> IntentClassification:
        normalized = text.strip().lower().replace(" ", "")

        if safety and (
            safety.requires_parent_attention
            or safety.is_at_least(RiskLevel.HIGH)
        ):
            return IntentClassification(
                intent=IntentType.SAFETY_RISK,
                sub_intent=safety.primary_category.value,
                emotion="concerned",
                risk_level=safety.risk_level,
                confidence=0.98,
                evidence=["safety_priority", *safety.evidence],
            )

        if safety and safety.primary_category == RiskCategory.PRIVACY:
            return IntentClassification(
                intent=IntentType.PRIVACY_QUESTION,
                sub_intent="privacy_boundary",
                risk_level=safety.risk_level,
                confidence=0.86,
                evidence=["privacy_rule"],
            )

        if safety and safety.risk_level == RiskLevel.WATCH:
            return self._watch_intent(safety)

        direct_answer_markers = (
            "直接告诉我答案",
            "告诉我答案",
            "给我答案",
            "直接说答案",
            "答案吧",
            "最终答案",
        )
        if self._contains_any(normalized, direct_answer_markers):
            return IntentClassification(
                intent=IntentType.LEARNING_HELP,
                sub_intent="direct_answer_request",
                risk_level=safety.risk_level if safety else RiskLevel.NONE,
                needs_modality=False,
                suggested_modalities=["text"],
                confidence=0.9,
                evidence=["direct_answer_request_keyword"],
            )

        bedtime_markers = ("晚安", "困了", "要睡", "想睡觉", "我要睡觉", "准备睡")
        if self._contains_any(normalized, bedtime_markers):
            return IntentClassification(
                intent=IntentType.BEDTIME_REFLECTION,
                sub_intent="bedtime_closeout",
                risk_level=safety.risk_level if safety else RiskLevel.NONE,
                confidence=0.92,
                evidence=[
                    "bedtime_keyword",
                    *(
                        ["bedtime_context"]
                        if time_context
                        and time_context.time_period == TimePeriod.BEDTIME
                        else []
                    ),
                ],
            )

        if self._is_explicit_learning_help(normalized):
            return IntentClassification(
                intent=IntentType.LEARNING_HELP,
                sub_intent="homework_problem_unknown_content",
                risk_level=safety.risk_level if safety else RiskLevel.NONE,
                needs_modality=True,
                suggested_modalities=["photo", "voice_description", "text"],
                confidence=0.94,
                evidence=["explicit_learning_help_keyword"],
            )

        tired_markers = ("不想说话", "好累", "很烦", "难过", "生气", "害怕")
        if self._contains_any(normalized, tired_markers):
            emotion = "tired" if "不想说话" in normalized or "累" in normalized else "frustrated"
            return IntentClassification(
                intent=IntentType.EMOTION_EXPRESSION,
                sub_intent="low_energy_or_frustrated",
                emotion=emotion,
                risk_level=safety.risk_level if safety else RiskLevel.NONE,
                confidence=0.86,
                evidence=["emotion_keyword"],
            )

        social_markers = ("同学", "朋友", "老师", "学校里")
        if self._contains_any(normalized, social_markers):
            return IntentClassification(
                intent=IntentType.SOCIAL_ISSUE,
                sub_intent="school_social_context",
                risk_level=safety.risk_level if safety else RiskLevel.NONE,
                confidence=0.74,
                evidence=["social_keyword"],
            )

        after_school_markers = ("我回来了", "放学了", "到家了")
        if self._contains_any(normalized, after_school_markers):
            return IntentClassification(
                intent=IntentType.AFTER_SCHOOL_CHECKIN,
                sub_intent="arrival_checkin",
                risk_level=safety.risk_level if safety else RiskLevel.NONE,
                confidence=0.9,
                evidence=["after_school_keyword"],
            )

        return self._mock_model_fallback(text, safety=safety)

    def _mock_model_fallback(
        self, text: str, *, safety: SafetyClassification | None
    ) -> IntentClassification:
        response = self._model_registry.generate(
            ModelRequest(
                task_type=ModelTaskType.INTENT_CLASSIFICATION,
                input_text=text,
            )
        )
        raw_intent = response.structured_output.get("intent")
        normalized_intent = self._normalize_model_intent(raw_intent)
        return IntentClassification(
            intent=normalized_intent,
            risk_level=safety.risk_level if safety else RiskLevel.NONE,
            confidence=float(response.structured_output.get("confidence", 0.5)),
            evidence=["mock_model_fallback"],
        )

    def _watch_intent(self, safety: SafetyClassification) -> IntentClassification:
        if safety.primary_category == RiskCategory.BULLYING:
            return IntentClassification(
                intent=IntentType.SOCIAL_ISSUE,
                sub_intent=RiskCategory.BULLYING.value,
                emotion="concerned",
                risk_level=safety.risk_level,
                confidence=0.88,
                evidence=["safety_watch", *safety.evidence],
            )
        if safety.primary_category == RiskCategory.MENTAL_DISTRESS:
            return IntentClassification(
                intent=IntentType.EMOTION_EXPRESSION,
                sub_intent=RiskCategory.MENTAL_DISTRESS.value,
                emotion="sad",
                risk_level=safety.risk_level,
                confidence=0.84,
                evidence=["safety_watch", *safety.evidence],
            )
        return IntentClassification(
            intent=IntentType.SAFETY_RISK,
            sub_intent=safety.primary_category.value,
            emotion="concerned",
            risk_level=safety.risk_level,
            confidence=0.82,
            evidence=["safety_watch", *safety.evidence],
        )

    def _normalize_model_intent(self, raw_intent: object) -> IntentType:
        if raw_intent == IntentType.LEARNING_HELP.value:
            return IntentType.LEARNING_HELP
        if raw_intent == IntentType.SAFETY_RISK.value:
            return IntentType.SAFETY_RISK
        return IntentType.CASUAL_CHAT

    def _contains_any(self, text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)

    def _is_explicit_learning_help(self, normalized: str) -> bool:
        if self._is_general_not_know_expression(normalized):
            return False

        explicit_phrases = (
            "我有一道题不会",
            "有一道题不会",
            "有题不会",
            "这道题不会",
            "这题不会",
            "一道题不会",
            "这道题怎么做",
            "这题怎么做",
            "这道题要怎么做",
            "这题要怎么做",
            "帮我看看作业",
            "帮我看作业",
            "看看作业",
            "数学题不会",
            "语文题不会",
            "英语题不会",
            "英语作业",
            "语文作业",
            "数学作业",
            "口算题",
            "应用题",
            "练习册",
            "课文作业",
            "作文作业",
        )
        if self._contains_any(normalized, explicit_phrases):
            return True

        learning_subjects = (
            "作业",
            "数学题",
            "语文题",
            "英语题",
            "口算",
            "应用题",
            "练习册",
            "课文",
            "作文",
            "课本题",
        )
        help_markers = (
            "不会",
            "不懂",
            "怎么做",
            "要怎么做",
            "帮我",
            "帮忙",
            "看看",
            "讲讲",
            "检查",
        )
        return self._contains_any(normalized, learning_subjects) and self._contains_any(
            normalized,
            help_markers,
        )

    def _is_general_not_know_expression(self, normalized: str) -> bool:
        general_markers = (
            "不会画",
            "不会搭",
            "不会拼",
            "不会玩",
            "玩具",
            "积木",
            "小怪兽",
            "游戏里",
            "谜题",
            "问题考你",
            "考考你",
            "想出一个问题",
        )
        return self._contains_any(normalized, general_markers)


_intent_classifier = IntentClassifier()


def get_intent_classifier() -> IntentClassifier:
    return _intent_classifier
