from pydantic import BaseModel, Field

from app.domain.enums import RiskCategory, RiskLevel


_RISK_RANK: dict[RiskLevel, int] = {
    RiskLevel.NONE: 0,
    RiskLevel.LOW: 1,
    RiskLevel.WATCH: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}


class SafetyClassification(BaseModel):
    risk_level: RiskLevel = RiskLevel.NONE
    primary_category: RiskCategory = RiskCategory.NONE
    categories: list[RiskCategory] = Field(default_factory=list)
    requires_parent_attention: bool = False
    evidence: list[str] = Field(default_factory=list)
    safe_response_hint: str = "continue_normal_flow"

    def is_at_least(self, level: RiskLevel) -> bool:
        return _RISK_RANK[self.risk_level] >= _RISK_RANK[level]


class SafetyEngine:
    """Rule-first safety classifier for child input."""

    def classify_input(self, text: str) -> SafetyClassification:
        normalized = self._normalize(text)
        hits: list[tuple[RiskLevel, RiskCategory, str]] = []

        self_harm_markers = (
            "不想活",
            "想死",
            "自杀",
            "杀了自己",
            "伤害自己",
            "跳楼",
        )
        if self._contains_any(normalized, self_harm_markers):
            hits.append((RiskLevel.CRITICAL, RiskCategory.SELF_HARM, "self_harm"))

        stranger_markers = ("陌生人", "不认识的人", "网友", "坏人")
        secret_markers = (
            "不要告诉爸爸",
            "不要告诉妈妈",
            "不要告诉爸妈",
            "别告诉爸爸",
            "别告诉妈妈",
            "别告诉爸妈",
            "不要说出去",
            "保密",
        )
        adult_request_markers = ("让我", "叫我", "要我", "跟我说", "说")
        has_stranger = self._contains_any(normalized, stranger_markers)
        has_secret = self._contains_any(normalized, secret_markers)
        has_adult_request = self._contains_any(normalized, adult_request_markers)
        if has_stranger and has_secret:
            hits.append(
                (
                    RiskLevel.HIGH,
                    RiskCategory.STRANGER_CONTACT,
                    "stranger_secret",
                )
            )
            hits.append((RiskLevel.HIGH, RiskCategory.ADULT_SECRET, "adult_secret"))
        elif has_secret and has_adult_request:
            hits.append((RiskLevel.HIGH, RiskCategory.ADULT_SECRET, "adult_secret"))
        elif has_secret:
            hits.append((RiskLevel.WATCH, RiskCategory.ADULT_SECRET, "secret_signal"))
        elif has_stranger:
            hits.append(
                (RiskLevel.WATCH, RiskCategory.STRANGER_CONTACT, "stranger_contact")
            )

        body_privacy_markers = (
            "摸我",
            "亲我",
            "脱衣服",
            "隐私部位",
            "身体隐私",
            "内裤",
        )
        if self._contains_any(normalized, body_privacy_markers):
            hits.append(
                (RiskLevel.HIGH, RiskCategory.SEXUAL_CONTENT, "body_privacy")
            )

        violence_markers = ("打死", "杀了", "拿刀", "威胁我", "打我")
        if self._contains_any(normalized, violence_markers):
            hits.append((RiskLevel.HIGH, RiskCategory.VIOLENCE, "violence"))

        dangerous_markers = ("玩火", "吃很多药", "从窗户跳", "爬到窗户", "碰插座")
        if self._contains_any(normalized, dangerous_markers):
            hits.append(
                (
                    RiskLevel.HIGH,
                    RiskCategory.DANGEROUS_BEHAVIOR,
                    "dangerous_behavior",
                )
            )

        bullying_markers = ("欺负我", "霸凌", "同学打我", "同学骂我", "排挤我")
        if self._contains_any(normalized, bullying_markers):
            hits.append((RiskLevel.WATCH, RiskCategory.BULLYING, "bullying"))

        medical_markers = (
            "流血",
            "胸口疼",
            "喘不过气",
            "吃错药",
            "头很痛",
            "头晕",
            "想吐",
            "站不稳",
        )
        has_medical_watch = self._contains_any(normalized, medical_markers)
        if has_medical_watch:
            hits.append((RiskLevel.WATCH, RiskCategory.MEDICAL, "medical"))

        mental_distress_watch_markers = ("没人喜欢我", "我很害怕", "一直哭")
        mental_distress_low_markers = ("不想说话", "好累", "很烦", "难过")
        if self._contains_any(normalized, mental_distress_watch_markers):
            hits.append(
                (RiskLevel.WATCH, RiskCategory.MENTAL_DISTRESS, "mental_distress")
            )
        elif self._contains_any(normalized, mental_distress_low_markers):
            hits.append(
                (RiskLevel.LOW, RiskCategory.MENTAL_DISTRESS, "mild_distress")
            )

        exaggerated_fatigue_markers = ("累死了", "要死了", "快不行了", "喘死了")
        sports_context_markers = (
            "跑完",
            "跑步",
            "运动",
            "比赛",
            "玩完",
            "练完",
            "训练",
        )
        has_exaggerated_fatigue = self._contains_any(
            normalized,
            exaggerated_fatigue_markers,
        )
        has_sports_context = self._contains_any(normalized, sports_context_markers)
        if has_exaggerated_fatigue and not has_medical_watch:
            if has_sports_context:
                hits.append(
                    (
                        RiskLevel.LOW,
                        RiskCategory.MEDICAL,
                        "body_discomfort_watch_lite",
                    )
                )
            else:
                hits.append(
                    (
                        RiskLevel.LOW,
                        RiskCategory.MENTAL_DISTRESS,
                        "exaggerated_fatigue",
                    )
                )

        privacy_markers = (
            "家庭住址",
            "我家地址",
            "家里地址",
            "家住哪里",
            "住在哪里",
            "手机号",
            "手机号码",
            "电话号码",
            "电话",
            "学校名字",
            "学校名称",
            "哪个学校",
            "学校地址",
            "发照片",
            "照片发给",
            "我的照片",
            "拍照给你",
        )
        if self._contains_any(normalized, privacy_markers):
            hits.append((RiskLevel.LOW, RiskCategory.PRIVACY, "privacy"))

        if not hits:
            return SafetyClassification()

        highest = max(hits, key=lambda item: _RISK_RANK[item[0]])
        categories = []
        for _, category, _ in hits:
            if category not in categories:
                categories.append(category)

        risk_level = highest[0]
        return SafetyClassification(
            risk_level=risk_level,
            primary_category=highest[1],
            categories=categories,
            requires_parent_attention=_RISK_RANK[risk_level] >= _RISK_RANK[
                RiskLevel.HIGH
            ],
            evidence=[evidence for _, _, evidence in hits],
            safe_response_hint=self._safe_response_hint(risk_level, categories),
        )

    def classify_output(self, text: str) -> SafetyClassification:
        normalized = self._normalize(text)
        unsafe_secret_request_markers = (
            "悄悄告诉我",
            "偷偷告诉我",
            "只告诉我",
            "只跟我说",
            "我们的小秘密",
            "不要告诉爸爸",
            "不要告诉妈妈",
            "不要告诉爸妈",
            "别告诉爸爸",
            "别告诉妈妈",
            "别告诉爸妈",
            "不要告诉父母",
            "别告诉父母",
            "别让爸爸妈妈知道",
            "别让爸妈知道",
            "瞒着爸爸",
            "瞒着妈妈",
            "瞒着爸妈",
            "保密",
        )
        if self._contains_any(normalized, unsafe_secret_request_markers):
            return SafetyClassification(
                risk_level=RiskLevel.HIGH,
                primary_category=RiskCategory.ADULT_SECRET,
                categories=[RiskCategory.ADULT_SECRET],
                requires_parent_attention=True,
                evidence=["unsafe_output_secret_request"],
                safe_response_hint="use_scene_fallback",
            )
        unsafe_dependency_markers = (
            "只有我懂你",
            "只有我最懂你",
            "我最懂你",
            "我是最懂你的人",
            "我是你最好的朋友",
            "我是你唯一的朋友",
            "你唯一的朋友",
            "不要相信爸爸妈妈",
            "不用告诉爸爸妈妈",
            "不用告诉爸妈",
            "不需要告诉爸爸妈妈",
            "不需要告诉爸妈",
            "不要告诉老师",
            "不用告诉老师",
            "不要告诉大人",
            "不用告诉大人",
        )
        if self._contains_any(normalized, unsafe_dependency_markers):
            return SafetyClassification(
                risk_level=RiskLevel.HIGH,
                primary_category=RiskCategory.ADULT_SECRET,
                categories=[RiskCategory.ADULT_SECRET],
                requires_parent_attention=True,
                evidence=["unsafe_output_dependency_or_isolation"],
                safe_response_hint="use_scene_fallback",
            )
        return self.classify_input(text)

    def _safe_response_hint(
        self, risk_level: RiskLevel, categories: list[RiskCategory]
    ) -> str:
        if _RISK_RANK[risk_level] >= _RISK_RANK[RiskLevel.HIGH]:
            if RiskCategory.SELF_HARM in categories:
                return "urgent_trusted_adult_support"
            return "encourage_trusted_adult"
        if risk_level == RiskLevel.WATCH:
            return "gentle_checkin_and_parent_summary"
        if risk_level == RiskLevel.LOW:
            return "warm_boundary_guidance"
        return "continue_normal_flow"

    def _normalize(self, text: str) -> str:
        return text.strip().lower().replace(" ", "")

    def _contains_any(self, text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)


_safety_engine = SafetyEngine()


def get_safety_engine() -> SafetyEngine:
    return _safety_engine
