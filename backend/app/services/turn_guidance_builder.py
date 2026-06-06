from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field

from app.domain.model_types import ModelMessage
from app.services.light_co_creation_service import (
    get_light_co_creation_service,
)
from app.services.topic_seed_service import TopicSeedService


class ConversationArcState(BaseModel):
    """Lightweight per-session conversation arc tracking.

    Non-content; usable for prompt context, parent report material, and QA.
    """
    session_topic: str | None = None
    turn_count_on_topic: int = 0
    child_engagement: str = "unclear"
    current_arc_phase: str = "opening"
    last_boundary_signal: str | None = None
    real_life_bridge_hint: str | None = None
    memory_update_hint: str | None = None


class TurnGuidanceContext(BaseModel):
    hints: list[str] = Field(default_factory=list)
    guidance: dict[str, str] = Field(default_factory=dict)
    recent_topic: str | None = None
    same_topic_score: int = 0
    same_topic_turn_count: int = 0
    consecutive_recent_questions: int = 0
    boundary_signal: str | None = None
    child_engagement_signal: str = "neutral"
    topic_shift_recommended: bool = False
    topic_shift_reason: str | None = None
    suggested_topic_seeds: list[str] = Field(default_factory=list)
    arc_state: ConversationArcState = Field(default_factory=ConversationArcState)
    # Light co-creation fields
    co_creation_type: str = "none"
    co_creation_suggested: bool = False
    co_creation_reason: str | None = None


class TurnGuidanceBuilder:
    """Builds lightweight prompt guidance for one child speech turn."""

    def __init__(
        self,
        *,
        topic_seed_service: TopicSeedService | None = None,
        light_co_creation_service: Any | None = None,
    ) -> None:
        self._topic_seed_service = topic_seed_service or TopicSeedService()
        self._light_co_creation_service = (
            light_co_creation_service or get_light_co_creation_service()
        )

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
    _GAME_CONTEXT_MARKERS = (
        "游戏",
        "打游戏",
        "cs",
        "反恐",
        "队友",
        "地图",
        "枪",
        "排位",
        "关卡",
    )
    _CREATION_CONTEXT_MARKERS = (
        "画",
        "画画",
        "手工",
        "积木",
        "故事",
        "编一个",
        "编个",
    )
    _ANIMAL_SPACE_CONTEXT_MARKERS = (
        "恐龙",
        "太空",
        "星球",
        "动物",
        "昆虫",
        "植物",
    )
    _DISCOMFORT_MARKERS = ("要死了", "累死了", "快不行了", "喘死了")
    _TOPIC_CHANGE_MARKERS = (
        "换个话题",
        "聊点别的",
        "别聊这个",
        "不聊了",
        "不想聊了",
        "不要聊了",
        "不说了",
        "算了",
        # 设计收口文档新增：轻微烦躁或抗拒
        "你别说这个",
        "不好玩",
        "别问了",
        "不要问了",
    )
    _BEDTIME_CLOSE_MARKERS = (
        "明天再聊",
        "我要睡觉",
        "我得睡觉",
        "睡觉了",
        "晚安",
        "困了",
    )
    _CORRECTION_MARKERS = (
        "不是",
        "你说错了",
        "我还没跑",
        "我没有跑",
        "听错了",
    )
    _LEAVE_FOR_TASK_MARKERS = (
        "去英语打卡",
        "英语打卡",
        "去写作业",
        "要去上课",
        "妈妈叫我",
        "爸爸叫我",
        "我要走了",
        "得走了",
        "一会再聊",
        "等会再聊",
    )

    def build(
        self,
        *,
        child_text: str,
        conversation_history: Sequence[ModelMessage] | None = None,
        parent_policy: Any | None = None,
        session_id: str | None = None,
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
        self._add_hint(
            normalized,
            hints=hints,
            guidance=guidance,
            hint="child_correction",
            markers=self._CORRECTION_MARKERS,
            instruction="孩子在纠正你或 ASR 误听时，先承认可能理解错了，按孩子修正后的说法继续；本轮不要新增追问钩子。",
        )
        self._add_hint(
            normalized,
            hints=hints,
            guidance=guidance,
            hint="child_leave_for_task",
            markers=self._LEAVE_FOR_TASK_MARKERS,
            instruction="孩子说要去做别的事情（打卡、写作业、家长叫），立即温柔收束，不追问、不拉长；可以轻轻说一句回来再聊。",
        )

        recent_topic, same_topic_score = self._recent_topic(
            child_text=child_text,
            conversation_history=conversation_history or [],
        )
        child_engagement_signal = self._child_engagement_signal(normalized, hints)
        consecutive_recent_questions = self._recent_assistant_question_count(
            conversation_history or []
        )
        if consecutive_recent_questions >= 2:
            self._set_hint(
                hints=hints,
                guidance=guidance,
                hint="too_many_recent_questions",
                instruction="最近小白狐已经连续提问，本轮先回应和陈述，不再添加新的追问钩子；需要转场时给一个轻松陈述或短收束。",
            )
        if same_topic_score >= 4 and self._is_short_or_boundary_reply(normalized):
            self._set_hint(
                hints=hints,
                guidance=guidance,
                hint="same_topic_too_long",
                instruction="最近多轮可能持续围绕同一普通话题且孩子回答变短，提供换轨机会，不继续追问旧话题。",
            )
        if (
            child_engagement_signal == "short_or_flat"
            and same_topic_score >= 2
        ):
            self._set_hint(
                hints=hints,
                guidance=guidance,
                hint="consecutive_short_reply_stop_pushing",
                instruction=(
                    "孩子连续多轮短答，不再追问、不表现委屈、不继续拉旧话题；"
                    "可以轻轻说一句'没关系，先放一放'或给一个换题机会，"
                    "也可以自然收束，不补催促句。"
                ),
            )
        topic_shift_recommended = (
            same_topic_score >= 3
            and child_engagement_signal in {"short_or_flat", "boundary"}
            and recent_topic is not None
        )
        topic_shift_reason = None
        suggested_topic_seeds: list[str] = []
        if topic_shift_recommended:
            topic_shift_reason = (
                "same_topic_3_plus_with_low_child_engagement"
            )
            suggested_topic_seeds = self._topic_seed_service.seeds_for_parent_policy(
                parent_policy,
                limit=3,
            )
            seed_text = "、".join(suggested_topic_seeds)
            self._set_hint(
                hints=hints,
                guidance=guidance,
                hint="topic_shift_recommended",
                instruction=(
                    "同一普通话题已经持续多轮且孩子回复变短或变平，"
                    "本轮给换题机会，不继续追问旧话题；可以给孩子两个轻松方向"
                    f"{f'，例如：{seed_text}' if seed_text else ''}。"
                ),
            )

        boundary_signal = self._boundary_signal(normalized, hints)
        arc_state = self._build_arc_state(
            recent_topic=recent_topic,
            same_topic_score=same_topic_score,
            child_engagement_signal=child_engagement_signal,
            boundary_signal=boundary_signal,
            hints=hints,
        )

        # Light co-creation detection
        co_creation_type = "none"
        co_creation_suggested = False
        co_creation_reason = None
        if self._light_co_creation_service and session_id:
            # Check bedtime context
            is_bedtime = "bedtime_close_requested" in hints
            # Check learning context (simplified - full check happens in service)
            is_learning = False
            # Check safety context
            is_safety = False

            # Only check for story chain in open conversation (not images)
            decision = self._light_co_creation_service.should_trigger_story_chain(
                session_id=session_id,
                child_text=child_text,
                is_bedtime=is_bedtime,
                is_learning=is_learning,
                is_safety=is_safety,
                child_engagement=child_engagement_signal,
            )
            if decision.should_trigger:
                co_creation_type = decision.co_creation_type.value
                co_creation_suggested = True
                co_creation_reason = decision.reason
                self._set_hint(
                    hints=hints,
                    guidance=guidance,
                    hint="light_co_creation_story_chain",
                    instruction=(
                        "孩子说了想象性、轻松、可接一句的内容，可以轻轻发起故事接龙。"
                        "用温和、好奇的语气邀请，例如：'这个听起来像一个小故事。你想接一句也可以。'"
                        "如果孩子不接、短答或换题，立即放下，不追问。"
                        "故事接龙最多推进 2 轮孩子输入，然后自然收住。"
                        "不要说'挑战''任务''完成''奖励'等表达。"
                    ),
                )

        return TurnGuidanceContext(
            hints=hints,
            guidance=guidance,
            recent_topic=recent_topic,
            same_topic_score=same_topic_score,
            same_topic_turn_count=same_topic_score,
            consecutive_recent_questions=consecutive_recent_questions,
            boundary_signal=boundary_signal,
            child_engagement_signal=child_engagement_signal,
            topic_shift_recommended=topic_shift_recommended,
            topic_shift_reason=topic_shift_reason,
            suggested_topic_seeds=suggested_topic_seeds,
            arc_state=arc_state,
            co_creation_type=co_creation_type,
            co_creation_suggested=co_creation_suggested,
            co_creation_reason=co_creation_reason,
        )

    def _recent_topic(
        self,
        *,
        child_text: str,
        conversation_history: Sequence[ModelMessage],
    ) -> tuple[str | None, int]:
        recent_messages = [
            message
            for message in conversation_history[-10:]
            if isinstance(message.content, str)
        ]
        normalized_texts = [self._normalize(message.content) for message in recent_messages]
        normalized_texts.append(self._normalize(child_text))

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
        game_score = sum(
            1
            for text in normalized_texts
            if self._contains_any(text, self._GAME_CONTEXT_MARKERS)
        )
        creation_score = sum(
            1
            for text in normalized_texts
            if self._contains_any(text, self._CREATION_CONTEXT_MARKERS)
        )
        animal_space_score = sum(
            1
            for text in normalized_texts
            if self._contains_any(text, self._ANIMAL_SPACE_CONTEXT_MARKERS)
        )
        if game_score >= max(creation_score, animal_space_score, 3):
            return "游戏/CS", game_score
        if creation_score >= max(game_score, animal_space_score, 3):
            return "创作/画画", creation_score
        if animal_space_score >= max(game_score, creation_score, 3):
            return "自然/太空/恐龙", animal_space_score
        return None, max(sports_score, body_score)

    def _recent_assistant_question_count(
        self,
        conversation_history: Sequence[ModelMessage],
    ) -> int:
        count = 0
        for message in reversed(conversation_history[-6:]):
            if message.role == "user":
                continue
            if message.role != "assistant" or not isinstance(message.content, str):
                continue
            if "？" in message.content or "?" in message.content:
                count += 1
                continue
            break
        return count

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

    def _child_engagement_signal(self, normalized: str, hints: list[str]) -> str:
        if "child_requests_topic_change" in hints:
            # Distinguish explicit refusal from general topic change.
            if self._contains_any(
                normalized,
                ("不想聊", "别问", "不要问", "别说", "你别说", "我不想说"),
            ):
                return "refused"
            return "boundary"
        flat_replies = (
            "嗯",
            "哦",
            "好吧",
            "不知道",
            "还行",
            "随便",
            "没有",
            "没了",
            "算了",
            "都行",
        )
        # Exact match: only these standalone words count as flat
        if normalized in flat_replies:
            return "short_or_flat"
        # Short replies with substantive content are not flat
        # e.g. "嗯，是我画的" "对，还有一个" "嗯嗯好的"
        context_markers = ("是", "有", "对", "好", "画", "做", "写", "看", "玩", "吃", "说")
        if len(normalized) <= 8 and self._contains_any(normalized, context_markers):
            return "neutral"
        if len(normalized) <= 4:
            return "short_or_flat"
        if len(normalized) <= 8 and not self._contains_any(normalized, ("？", "?")):
            return "short_or_flat"
        if len(normalized) >= 18:
            return "engaged"
        return "neutral"

    def _build_arc_state(
        self,
        *,
        recent_topic: str | None,
        same_topic_score: int,
        child_engagement_signal: str,
        boundary_signal: str | None,
        hints: list[str],
    ) -> ConversationArcState:
        if boundary_signal == "bedtime":
            arc_phase = "closing"
        elif boundary_signal == "no_chat":
            arc_phase = "closing"
        elif "child_leave_for_task" in hints:
            arc_phase = "handoff"
        elif boundary_signal == "topic_change":
            arc_phase = "soft_shift"
        elif same_topic_score >= 3 and child_engagement_signal in {"short_or_flat", "boundary"}:
            arc_phase = "soft_shift"
        elif child_engagement_signal == "engaged":
            arc_phase = "deepening"
        elif recent_topic:
            arc_phase = "exploring"
        else:
            arc_phase = "opening"

        bridge_hint = None
        memory_hint = None
        if boundary_signal == "bedtime":
            bridge_hint = "孩子睡前说了晚安，家长明天可以轻轻问一句睡得好不好"
        elif "child_leave_for_task" in hints:
            bridge_hint = "孩子去做别的事了，家长今晚可以轻轻问一句事情做完了吗"
        elif recent_topic and same_topic_score >= 2:
            memory_hint = f"孩子今天聊到了{recent_topic}"

        return ConversationArcState(
            session_topic=recent_topic,
            turn_count_on_topic=same_topic_score,
            child_engagement=child_engagement_signal,
            current_arc_phase=arc_phase,
            last_boundary_signal=boundary_signal,
            real_life_bridge_hint=bridge_hint,
            memory_update_hint=memory_hint,
        )

    def _boundary_signal(self, normalized: str, hints: list[str]) -> str | None:
        if "bedtime_close_requested" in hints:
            return "bedtime"
        if "child_leave_for_task" in hints:
            return "leave_for_task"
        if "child_requests_topic_change" in hints:
            if self._contains_any(
                normalized,
                ("不聊", "不想聊", "不要聊", "不说", "算了", "别问", "不要问", "别说"),
            ):
                return "no_chat"
            return "topic_change"
        if "child_correction" in hints:
            return "correction"
        return None

    def _normalize(self, text: str) -> str:
        return text.strip().lower().replace(" ", "")

    def _contains_any(self, text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)
