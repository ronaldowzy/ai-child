from typing import Any

from app.domain.enums import IntentType, RiskCategory, RiskLevel
from app.domain.memory import (
    MemoryCreateRequest,
    MemoryEvidence,
    MemoryItem,
    MemorySensitivity,
    MemoryType,
)
from app.domain.scene import SceneId, SceneRouteDecision
from app.services.intent_classifier import IntentClassification
from app.services.memory_service import MemoryService, get_memory_service
from app.services.relationship_memory import (
    INTEREST_SEED,
    PROUD_MOMENT,
    RELATIONSHIP_MEMORY_TYPE_KEY,
    TOPIC_BOUNDARY,
    relationship_metadata,
)
from app.services.safety_engine import SafetyClassification


class ConversationMemoryHooks:
    """Rule-first memory hooks for conversation turns.

    v0.1 stores only structured summaries. Child text is intentionally not copied
    into memory content or evidence.
    """

    def __init__(self, *, memory_service: MemoryService | None = None) -> None:
        self._memory_service = memory_service or get_memory_service()

    def retrieve_context(
        self,
        *,
        child_id: str,
        current_text: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        memories = self._memory_service.retrieve(
            child_id,
            query=current_text,
            limit=limit,
            include_safety=False,
        )
        return [
            self._memory_to_runtime_context(memory)
            for memory in memories
            if memory.memory_type != MemoryType.SAFETY
        ]

    def record_turn(
        self,
        *,
        child_id: str,
        session_id: str,
        child_text: str,
        safety: SafetyClassification,
        intent: IntentClassification,
        route_decision: SceneRouteDecision,
    ) -> list[MemoryItem]:
        requests = self._memory_requests_for_turn(
            child_id=child_id,
            session_id=session_id,
            child_text=child_text,
            safety=safety,
            intent=intent,
            route_decision=route_decision,
        )
        return self._memory_service.create_many(requests)

    def _memory_requests_for_turn(
        self,
        *,
        child_id: str,
        session_id: str,
        child_text: str,
        safety: SafetyClassification,
        intent: IntentClassification,
        route_decision: SceneRouteDecision,
    ) -> list[MemoryCreateRequest]:
        requests: list[MemoryCreateRequest] = []

        if route_decision.active_scene == SceneId.LEARNING_HOMEWORK_HELP:
            requests.append(
                self._request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.LEARNING_PATTERN,
                    content="孩子本次遇到学习求助，系统引导其先说明题目在问什么。",
                    tags=["学习求助", "题", "题意复述", "第一步"],
                    quote_summary=(
                        "孩子表达有学习求助，系统引导先说明题目在问什么。"
                    ),
                    sensitivity=MemorySensitivity.MEDIUM,
                    confidence=0.84,
                    importance=0.66,
                    route_decision=route_decision,
                )
            )

        if (
            intent.sub_intent == "direct_answer_request"
            or route_decision.reason == "learning_direct_answer_request"
        ):
            requests.append(
                self._request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.LEARNING_PATTERN,
                    content=(
                        "孩子在学习求助中有直接要答案倾向，适合继续使用"
                        "“题意复述 + 第一步思考”的引导策略。"
                    ),
                    tags=["学习求助", "答案", "直接要答案", "题意复述", "第一步"],
                    quote_summary=(
                        "孩子在学习求助中请求直接答案，系统改为题意复述和第一步思考。"
                    ),
                    sensitivity=MemorySensitivity.MEDIUM,
                    confidence=0.88,
                    importance=0.74,
                    route_decision=route_decision,
                )
            )

        if self._should_record_low_energy_emotion(safety, intent, route_decision):
            requests.append(
                self._request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.EMOTION_OBSERVATION,
                    content=(
                        "孩子本次表达低能量或不想继续说话，适合先接住感受，"
                        "并提供安静一下或稍后再说的选择。"
                    ),
                    tags=["情绪观察", "不想说话", "低能量", "低压力"],
                    quote_summary=(
                        "孩子表达低能量状态，系统提供安静一下或稍后再说的选择。"
                    ),
                    sensitivity=MemorySensitivity.MEDIUM,
                    confidence=0.8,
                    importance=0.58,
                    route_decision=route_decision,
                )
            )

        if route_decision.active_scene == SceneId.SAFETY_GUARDIAN:
            requests.append(
                self._request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.SAFETY,
                    content=(
                        "本次会话出现需要家长关注的安全信号，系统鼓励孩子告诉"
                        "家长或可信成人，并提醒不需要保守让自己不舒服的秘密。"
                    ),
                    tags=["安全提醒", "家长关注", "可信成人"],
                    quote_summary=(
                        "会话出现高风险安全信号，系统鼓励孩子告诉家长或可信成人。"
                    ),
                    sensitivity=(
                        MemorySensitivity.CRITICAL
                        if safety.risk_level == RiskLevel.CRITICAL
                        else MemorySensitivity.HIGH
                    ),
                    confidence=0.94,
                    importance=0.94,
                    visible_to_parent=True,
                    requires_parent_attention=True,
                    route_decision=route_decision,
                )
            )

        if route_decision.active_scene == SceneId.SAFETY_GENTLE_CHECKIN:
            requests.append(
                self._request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.EMOTION_OBSERVATION,
                    content=(
                        "孩子本次提到学校同伴互动中有让他不舒服的情况，"
                        "系统温和鼓励告诉家长或老师。"
                    ),
                    tags=["watch_observation", "同学", "欺负", "老师", "情绪观察"],
                    quote_summary=(
                        "孩子提到同伴互动中有不舒服的情况，系统温和鼓励告诉家长或老师。"
                    ),
                    sensitivity=MemorySensitivity.MEDIUM,
                    confidence=0.82,
                    importance=0.68,
                    visible_to_parent=True,
                    requires_parent_attention=False,
                    route_decision=route_decision,
                )
            )

        if route_decision.active_scene == SceneId.PRIVACY_BOUNDARY:
            requests.append(
                self._request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.STRATEGY,
                    content=(
                        "系统本次提醒孩子不要分享家庭地址、电话、学校名字或照片，"
                        "涉及真实信息时先问家长。"
                    ),
                    tags=["隐私边界", "地址", "电话", "学校名字", "照片"],
                    quote_summary=(
                        "系统提醒孩子不要分享家庭地址、电话、学校名字或照片。"
                    ),
                    sensitivity=MemorySensitivity.MEDIUM,
                    confidence=0.86,
                    importance=0.62,
                    route_decision=route_decision,
                )
            )

        if (
            route_decision.active_scene == SceneId.DAILY_AFTER_SCHOOL_CHECKIN
            and intent.sub_intent == "arrival_checkin"
        ):
            requests.append(
                self._request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.EVENT,
                    content="孩子本次以放学到家开场，系统提供低压力选择式 check-in。",
                    tags=["放学后", "到家", "低压力"],
                    quote_summary="孩子以到家或放学开场，系统提供低压力选择式 check-in。",
                    sensitivity=MemorySensitivity.LOW,
                    confidence=0.72,
                    importance=0.36,
                    route_decision=route_decision,
                )
            )

        requests.extend(
            self._relationship_memory_requests_for_turn(
                child_id=child_id,
                session_id=session_id,
                child_text=child_text,
                safety=safety,
                route_decision=route_decision,
            )
        )
        return requests

    def _request(
        self,
        *,
        child_id: str,
        session_id: str,
        memory_type: MemoryType,
        content: str,
        tags: list[str],
        quote_summary: str,
        sensitivity: MemorySensitivity,
        confidence: float,
        importance: float,
        route_decision: SceneRouteDecision,
        visible_to_parent: bool = True,
        requires_parent_attention: bool = False,
    ) -> MemoryCreateRequest:
        return MemoryCreateRequest(
            child_id=child_id,
            memory_type=memory_type,
            content=content,
            tags=tags,
            evidence=[
                MemoryEvidence(
                    source="conversation_summary",
                    session_id=session_id,
                    quote_summary=quote_summary,
                    metadata={
                        "active_scene": route_decision.active_scene.value,
                        "route_reason": route_decision.reason,
                        "risk_level": route_decision.risk_level.value,
                    },
                )
            ],
            confidence=confidence,
            importance=importance,
            sensitivity=sensitivity,
            visible_to_parent=visible_to_parent,
            visible_to_child=False,
            requires_parent_attention=requires_parent_attention,
        )

    def _should_record_low_energy_emotion(
        self,
        safety: SafetyClassification,
        intent: IntentClassification,
        route_decision: SceneRouteDecision,
    ) -> bool:
        if route_decision.active_scene == SceneId.SAFETY_GENTLE_CHECKIN:
            return False
        if intent.intent == IntentType.EMOTION_EXPRESSION:
            return True
        return (
            safety.risk_level == RiskLevel.LOW
            and RiskCategory.MENTAL_DISTRESS in safety.categories
        )

    def _relationship_memory_requests_for_turn(
        self,
        *,
        child_id: str,
        session_id: str,
        child_text: str,
        safety: SafetyClassification,
        route_decision: SceneRouteDecision,
    ) -> list[MemoryCreateRequest]:
        text = self._normalize_text(child_text)
        if not text or self._should_skip_relationship_memory(text, safety):
            return []

        requests: list[MemoryCreateRequest] = []
        boundary = self._topic_boundary(text)
        if boundary and not self._has_relationship_memory(
            child_id=child_id,
            session_id=session_id,
            relationship_type=TOPIC_BOUNDARY,
            topic=boundary["topic"],
        ):
            requests.append(
                self._relationship_request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.STRATEGY,
                    relationship_type=TOPIC_BOUNDARY,
                    topic=boundary["topic"],
                    content=boundary["content"],
                    quote_summary=boundary["quote_summary"],
                    tags=["relationship_memory", "topic_boundary", "尊重边界"],
                    next_hook=boundary["next_hook"],
                    sensitivity=MemorySensitivity.LOW,
                    confidence=0.84,
                    importance=0.62,
                    route_decision=route_decision,
                    extra_metadata={"boundary_kind": boundary["kind"]},
                )
            )

        proud = self._proud_moment(text)
        if proud and not self._has_relationship_memory(
            child_id=child_id,
            session_id=session_id,
            relationship_type=PROUD_MOMENT,
            topic=proud["topic"],
        ):
            requests.append(
                self._relationship_request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.EXPRESSION_PATTERN,
                    relationship_type=PROUD_MOMENT,
                    topic=proud["topic"],
                    content=proud["content"],
                    quote_summary=proud["quote_summary"],
                    tags=[
                        "relationship_memory",
                        "proud_moment",
                        "表达进步",
                        proud["topic"],
                    ],
                    next_hook=proud["next_hook"],
                    sensitivity=MemorySensitivity.LOW,
                    confidence=0.78,
                    importance=0.56,
                    route_decision=route_decision,
                    extra_metadata={"growth_signal": proud["growth_signal"]},
                )
            )

        interest = self._interest_seed(text)
        if interest and not self._has_relationship_memory(
            child_id=child_id,
            session_id=session_id,
            relationship_type=INTEREST_SEED,
            topic=interest["topic"],
        ):
            requests.append(
                self._relationship_request(
                    child_id=child_id,
                    session_id=session_id,
                    memory_type=MemoryType.INTEREST,
                    relationship_type=INTEREST_SEED,
                    topic=interest["topic"],
                    content=interest["content"],
                    quote_summary=interest["quote_summary"],
                    tags=[
                        "relationship_memory",
                        "interest_seed",
                        interest["topic"],
                    ],
                    next_hook=interest["next_hook"],
                    sensitivity=MemorySensitivity.LOW,
                    confidence=0.76,
                    importance=0.5,
                    route_decision=route_decision,
                )
            )
        return requests

    def _relationship_request(
        self,
        *,
        child_id: str,
        session_id: str,
        memory_type: MemoryType,
        relationship_type: str,
        topic: str,
        content: str,
        quote_summary: str,
        tags: list[str],
        next_hook: str,
        sensitivity: MemorySensitivity,
        confidence: float,
        importance: float,
        route_decision: SceneRouteDecision,
        extra_metadata: dict[str, object] | None = None,
    ) -> MemoryCreateRequest:
        metadata = relationship_metadata(
            relationship_memory_type=relationship_type,
            topic=topic,
            next_hook=next_hook,
            do_not_overask=True,
            extra={
                "active_scene": route_decision.active_scene.value,
                "route_reason": route_decision.reason,
                "risk_level": route_decision.risk_level.value,
                **(extra_metadata or {}),
            },
        )
        return MemoryCreateRequest(
            child_id=child_id,
            memory_type=memory_type,
            content=content,
            tags=tags,
            evidence=[
                MemoryEvidence(
                    source="conversation_summary",
                    session_id=session_id,
                    quote_summary=quote_summary,
                    metadata=metadata,
                )
            ],
            confidence=confidence,
            importance=importance,
            sensitivity=sensitivity,
            visible_to_parent=True,
            visible_to_child=False,
            requires_parent_attention=False,
        )

    def _interest_seed(self, text: str) -> dict[str, str] | None:
        creation_topic_map: tuple[tuple[tuple[str, ...], str, str], ...] = (
            (
                ("我画", "画画", "画了", "画一幅", "涂色", "作品"),
                "画画",
                "下次可问孩子想给画起什么名字",
            ),
            (
                ("手工", "剪纸", "折纸", "我做"),
                "手工",
                "下次可问孩子最想做哪一步",
            ),
            (
                ("积木", "乐高"),
                "积木",
                "下次可问孩子搭的东西最特别的一块在哪里",
            ),
            (
                ("故事", "想象", "编一个", "编个", "我编"),
                "故事想象",
                "下次可一起接一句轻松的小故事",
            ),
        )
        for markers, topic, next_hook in creation_topic_map:
            if self._contains_any(text, markers):
                return {
                    "topic": topic,
                    "next_hook": next_hook,
                    "content": f"孩子近期自然聊到{topic}，可作为低压力回访的兴趣种子。",
                    "quote_summary": f"孩子自然提到{topic}相关内容，适合短期轻回访。",
                }

        if self._is_running_or_sports_interest_text(text):
            return {
                "topic": "跑步比赛",
                "next_hook": "下次可问比赛是短跑还是接力，或讲小白狐运动会故事",
                "content": "孩子近期自然聊到跑步比赛，可作为低压力回访的兴趣种子。",
                "quote_summary": "孩子自然提到跑步比赛相关内容，适合短期轻回访。",
            }

        topic_map: tuple[tuple[tuple[str, ...], str, str], ...] = (
            (("恐龙",), "恐龙", "下次可聊喜欢哪种恐龙，或一起编一个恐龙小故事"),
            (
                ("动物", "小猫", "小狗", "狐狸"),
                "动物",
                "下次可让孩子选一种动物编小故事",
            ),
            (("玩具",), "玩具", "下次可问孩子想让玩具角色发生什么故事"),
            (
                ("看书", "读书", "绘本", "书"),
                "书和阅读",
                "下次可问孩子最记得哪一页或哪个角色",
            ),
            (
                ("植物", "花", "树叶"),
                "植物",
                "下次可问孩子发现了植物的哪个小变化",
            ),
        )
        for markers, topic, next_hook in topic_map:
            if self._contains_any(text, markers):
                return {
                    "topic": topic,
                    "next_hook": next_hook,
                    "content": f"孩子近期自然聊到{topic}，可作为低压力回访的兴趣种子。",
                    "quote_summary": f"孩子自然提到{topic}相关内容，适合短期轻回访。",
                }
        return None

    def _topic_boundary(self, text: str) -> dict[str, str] | None:
        if self._contains_any(text, ("明天再聊", "我要睡觉", "我得睡觉", "晚安", "困了")):
            return {
                "kind": "bedtime_close",
                "topic": "睡前收尾",
                "content": "孩子表达需要睡觉或结束会话，后续应短收尾，不拉长对话。",
                "quote_summary": "孩子表达睡前收尾或明天再聊的边界。",
                "next_hook": "后续睡前只轻轻收尾，不继续追问旧话题。",
            }
        if self._contains_any(
            text,
            ("换个话题", "聊点别的", "别聊这个", "不说了", "算了", "今天不聊了"),
        ):
            return {
                "kind": "topic_change",
                "topic": "换话题边界",
                "content": "孩子明确表达想换话题，后续应尊重转场，不继续追问旧话题。",
                "quote_summary": "孩子表达想换个话题或不继续当前话题。",
                "next_hook": "下次可给两个轻松方向，并允许孩子自己说别的。",
            }
        return None

    def _proud_moment(self, text: str) -> dict[str, str] | None:
        if (
            self._is_running_or_sports_interest_text(text)
            and self._contains_any(text, ("感觉", "项目", "参加", "快"))
        ):
            return {
                "topic": "运动比赛表达",
                "growth_signal": "topic_project_feeling",
                "content": "孩子能把运动比赛、项目或感受连起来表达，适合给低压力成长反馈。",
                "quote_summary": "孩子围绕运动比赛表达了主题、项目或感受。",
                "next_hook": "家长可具体肯定孩子把事情说清楚了，再轻轻问一个最喜欢的瞬间。",
            }
        if self._contains_any(text, ("我画", "我做", "我搭", "我编", "我的作品")):
            return {
                "topic": "作品分享表达",
                "growth_signal": "created_work_shared",
                "content": "孩子主动分享作品或共创内容，适合肯定表达和创作过程。",
                "quote_summary": "孩子主动分享作品或故事共创线索。",
                "next_hook": "家长可先问作品里孩子最喜欢的一处，不做评分。",
            }
        return None

    def _is_running_or_sports_interest_text(self, text: str) -> bool:
        if "运动比赛" in text:
            return True
        return self._contains_any(
            text,
            ("跑步", "跑完", "短跑", "接力", "快的感觉", "公里", "十五公里"),
        ) or (
            self._contains_any(text, ("运动", "跑"))
            and not self._contains_any(text, ("英语比赛", "数学比赛", "作文比赛"))
        )

    def _should_skip_relationship_memory(
        self,
        text: str,
        safety: SafetyClassification,
    ) -> bool:
        if safety.primary_category == RiskCategory.SELF_HARM or safety.is_at_least(
            RiskLevel.HIGH
        ):
            return True
        if self._contains_any(
            text,
            (
                "家庭住址",
                "我家地址",
                "家里地址",
                "手机号",
                "电话号码",
                "电话",
                "学校名字",
                "学校名称",
                "真实姓名",
                "身份证",
                "照片隐私",
                "地址",
            ),
        ):
            return True
        if self._contains_any(
            text,
            (
                "胸口疼",
                "喘不过气",
                "头晕",
                "想吐",
                "站不稳",
                "流血",
                "吃错药",
            ),
        ):
            return True
        if self._contains_any(
            text,
            ("妈妈说", "爸爸让我说", "老师让你问", "你跟他说", "大人让我说"),
        ):
            return True
        operation_markers = (
            "按一下",
            "点这个",
            "说完再按",
            "取消",
            "重说",
            "按钮",
            "麦克风",
            "发送",
            "录音",
        )
        if self._contains_any(text, operation_markers) and not (
            self._interest_seed(text)
            or self._topic_boundary(text)
            or self._proud_moment(text)
        ):
            return True
        if len(text) <= 4:
            return True
        return False

    def _has_relationship_memory(
        self,
        *,
        child_id: str,
        session_id: str,
        relationship_type: str,
        topic: str,
    ) -> bool:
        memory_types = {
            INTEREST_SEED: MemoryType.INTEREST,
            TOPIC_BOUNDARY: MemoryType.STRATEGY,
            PROUD_MOMENT: MemoryType.EXPRESSION_PATTERN,
        }
        memories = self._memory_service.list_memories(
            child_id,
            memory_type=memory_types[relationship_type],
            active_only=True,
            include_safety=False,
        )
        for memory in memories:
            for evidence in memory.evidence:
                if (
                    relationship_type != INTEREST_SEED
                    and evidence.session_id != session_id
                ):
                    continue
                if (
                    evidence.metadata.get(RELATIONSHIP_MEMORY_TYPE_KEY)
                    != relationship_type
                ):
                    continue
                if evidence.metadata.get("topic") == topic:
                    return True
        return False

    def _normalize_text(self, text: str) -> str:
        return text.strip().lower().replace(" ", "")

    def _contains_any(self, text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)

    def _memory_to_runtime_context(self, memory: MemoryItem) -> dict[str, Any]:
        return {
            "memory_type": memory.memory_type.value,
            "content": memory.content,
            "tags": memory.tags[:6],
            "confidence": round(memory.confidence, 2),
        }


_conversation_memory_hooks = ConversationMemoryHooks()


def get_conversation_memory_hooks() -> ConversationMemoryHooks:
    return _conversation_memory_hooks
