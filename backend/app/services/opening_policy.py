from dataclasses import dataclass
from enum import StrEnum

from app.domain.memory import MemoryItem, MemoryType
from app.domain.schemas.parent_policy import ParentPolicy
from app.domain.time import TimeContext, TimePeriod
from app.services.memory_service import MemoryService, get_memory_service
from app.services.relationship_memory import (
    latest_interest_seed,
    latest_topic_boundary,
    memory_relationship_metadata,
    memory_relationship_topic,
)


class OpeningMode(StrEnum):
    DEFAULT_LIGHT = "default_light"
    INTEREST_CALLBACK = "interest_callback"
    BOUNDARY_RESPECT = "boundary_respect"
    BEDTIME_CLOSURE = "bedtime_closure"
    BEDTIME_DEFER_INTEREST = "bedtime_defer_interest"
    PARENT_BRIDGE_LIGHT = "parent_bridge_light"
    LOW_EXPRESSION_SUPPORT = "low_expression_support"


FORBIDDEN_OPENING_PHRASES: tuple[str, ...] = (
    "小白狐想你了",
    "你昨天没来",
    "我一直等你",
    "你终于来了",
    "你不来我会难过",
    "只有小白狐懂你",
    "小白狐最懂你",
    "这是我们的小秘密",
    "不要告诉家长",
    "不要告诉爸爸妈妈",
    "每天都要来",
    "再聊一会儿就有奖励",
    "连续来几天就有惊喜",
    "明天有惊喜",
    "今天必须告诉我一件学校的事",
    "你要慢慢说清楚才可以",
    "上次你说过……为什么今天不说了",
    "我们继续上次那个，不要换",
    # 设计收口文档新增禁止话术
    "你终于回来了",
    "明天一定要回来",
    "你上次给我看了那个红色",
    "你画的那只",
    "我还保存着你那张图",
    "我们来看看你以前的作品",
    "你已经做了好多作品了",
    "你的作品成长得很快",
    "上次你给我看了那个红色积木城堡",
    "你上次不是也做过类似的吗",
    "你之前很会这个呀",
    "我们接着上次那个题",
)

_EXCITING_TOPICS = (
    "跑步比赛",
    "比赛",
    "游戏",
    "恐龙大战",
    "冒险故事",
    "故事想象",
    "挑战",
    "任务",
    "奖励",
)


@dataclass(frozen=True)
class OpeningPolicy:
    mode: OpeningMode
    age_band: str
    max_chars: int
    max_spoken_options: int
    seed_topic: str | None
    seed_recall_allowed: bool
    seed_recall_reason: str | None
    boundary_kind: str | None
    boundary_topic: str | None
    boundary_cooldown_active: bool
    bedtime: bool
    exciting_topic_deferred: bool
    must_offer_topic_switch: bool
    must_allow_no_chat: bool
    prefer_parent_bridge: bool
    parent_goal_hint: str | None
    forbidden_phrases: tuple[str, ...]
    prompt_rules: tuple[str, ...]


class OpeningPolicyBuilder:
    """Builds a structured opening policy from local context and memory."""

    def __init__(self, *, memory_service: MemoryService | None = None) -> None:
        self._memory_service = memory_service or get_memory_service()
        self._interest_recall_counts: dict[tuple[str, str], int] = {}
        self._boundary_cooldown_counts: dict[tuple[str, str, str], int] = {}
        self._last_opening_recalled: dict[str, bool] = {}  # child_id -> recalled last time

    def build(
        self,
        *,
        child_id: str,
        parent_policy: ParentPolicy,
        time_context: TimeContext,
    ) -> OpeningPolicy:
        age_band = self._age_band(parent_policy)
        max_chars, max_spoken_options = self._age_limits(age_band)
        bedtime = time_context.time_period == TimePeriod.BEDTIME
        interest_seed, boundary, low_expression_state = self._safe_memory_context(
            child_id
        )
        seed_topic = memory_relationship_topic(interest_seed) if interest_seed else None
        boundary_kind, boundary_topic = self._boundary_info(boundary)
        boundary_cooldown_active = self._boundary_cooldown_active(
            child_id=child_id,
            boundary_kind=boundary_kind,
            boundary_topic=boundary_topic,
        )
        recall_blocked = self._interest_recall_count(child_id, seed_topic) > 0
        # 连续两次打开不要都主动回访
        last_recalled = self._last_opening_recalled.get(child_id, False)
        if last_recalled:
            recall_blocked = True
        parent_goal_hint = self._parent_goal_hint(parent_policy, time_context)
        prefer_parent_bridge = bedtime or self._contains_any(
            self._parent_text(parent_policy),
            ("家长", "爸爸妈妈", "爸爸", "妈妈", "父母"),
        )
        no_school_check = self._no_school_check(parent_policy)

        mode = OpeningMode.DEFAULT_LIGHT
        seed_recall_allowed = False
        seed_recall_reason: str | None = "no_seed"
        exciting_topic_deferred = False

        if bedtime:
            if seed_topic and self._is_exciting_topic(seed_topic):
                mode = OpeningMode.BEDTIME_DEFER_INTEREST
                seed_recall_reason = "bedtime_defer_exciting_topic"
                exciting_topic_deferred = True
            else:
                mode = OpeningMode.BEDTIME_CLOSURE
                seed_recall_reason = "bedtime_closure"
        elif boundary_cooldown_active:
            mode = OpeningMode.BOUNDARY_RESPECT
            seed_recall_reason = f"boundary_{boundary_kind or 'active'}"
        elif low_expression_state is not None:
            mode = OpeningMode.LOW_EXPRESSION_SUPPORT
            seed_recall_reason = "low_expression_state"
        elif not seed_topic:
            seed_topic = self._profile_interest_seed(parent_policy, boundary_topic)
            recall_blocked = recall_blocked or self._interest_recall_count(child_id, seed_topic) > 0
            if seed_topic and not recall_blocked:
                mode = OpeningMode.INTEREST_CALLBACK
                seed_recall_allowed = True
                seed_recall_reason = "profile_interest_seed"
        if mode == OpeningMode.DEFAULT_LIGHT and seed_topic and not recall_blocked:
            mode = OpeningMode.INTEREST_CALLBACK
            seed_recall_allowed = True
            seed_recall_reason = "low_sensitivity_interest_seed"
        elif mode == OpeningMode.DEFAULT_LIGHT and recall_blocked:
            seed_recall_reason = "recently_recalled" if not last_recalled else "consecutive_skip"
        elif mode == OpeningMode.DEFAULT_LIGHT and parent_goal_hint and self._contains_any(
            parent_goal_hint,
            ("家长", "爸爸妈妈", "爸爸", "妈妈", "一起告诉"),
        ):
            mode = OpeningMode.PARENT_BRIDGE_LIGHT
            seed_recall_reason = "parent_bridge"

        return self._policy(
            mode=mode,
            age_band=age_band,
            max_chars=max_chars,
            max_spoken_options=max_spoken_options,
            seed_topic=seed_topic if seed_recall_allowed or exciting_topic_deferred else None,
            seed_recall_allowed=seed_recall_allowed,
            seed_recall_reason=seed_recall_reason,
            boundary_kind=boundary_kind,
            boundary_topic=boundary_topic,
            boundary_cooldown_active=boundary_cooldown_active,
            bedtime=bedtime,
            exciting_topic_deferred=exciting_topic_deferred,
            prefer_parent_bridge=prefer_parent_bridge,
            parent_goal_hint=parent_goal_hint,
            no_school_check=no_school_check,
        )

    def record_policy_used(self, *, child_id: str, policy: OpeningPolicy) -> None:
        if policy.seed_recall_allowed and policy.seed_topic:
            key = (child_id, policy.seed_topic)
            self._interest_recall_counts[key] = self._interest_recall_counts.get(key, 0) + 1
        # Track whether this opening recalled a topic (for consecutive skip).
        self._last_opening_recalled[child_id] = policy.seed_recall_allowed
        if policy.boundary_cooldown_active and policy.boundary_kind:
            key = (
                child_id,
                policy.boundary_kind,
                policy.boundary_topic or "*",
            )
            self._boundary_cooldown_counts[key] = (
                self._boundary_cooldown_counts.get(key, 0) + 1
            )

    def _safe_memory_context(
        self,
        child_id: str,
    ) -> tuple[MemoryItem | None, MemoryItem | None, MemoryItem | None]:
        try:
            return (
                latest_interest_seed(self._memory_service, child_id=child_id),
                latest_topic_boundary(self._memory_service, child_id=child_id),
                self._latest_low_expression_state(child_id),
            )
        except Exception:
            return None, None, None

    def _policy(
        self,
        *,
        mode: OpeningMode,
        age_band: str,
        max_chars: int,
        max_spoken_options: int,
        seed_topic: str | None,
        seed_recall_allowed: bool,
        seed_recall_reason: str | None,
        boundary_kind: str | None,
        boundary_topic: str | None,
        boundary_cooldown_active: bool,
        bedtime: bool,
        exciting_topic_deferred: bool,
        prefer_parent_bridge: bool,
        parent_goal_hint: str | None,
        no_school_check: bool,
    ) -> OpeningPolicy:
        rules = [
            f"opening_mode={mode.value}",
            f"max_chars={max_chars}",
            f"max_spoken_options={max_spoken_options}",
            "必须让孩子知道可以继续、换话题或不聊。",
            "不要暗示孩子必须延续上次话题。",
            "不要制造留存压力、奖励悬念、秘密关系或排他依赖。",
        ]
        if seed_topic and seed_recall_allowed:
            rules.append(f"最多只轻轻回访一个低敏 topic：{seed_topic}。")
        if bedtime:
            rules.append("睡前必须低刺激、短句、可收尾，不开启兴奋话题。")
        if boundary_cooldown_active:
            rules.append("尊重孩子上次表达的边界，不主动拉回旧话题。")
        if no_school_check:
            rules.append("家长要求不做日间经历查岗，不提固定场所。")
        if parent_goal_hint:
            rules.append(f"家长目标只能低压力转译：{parent_goal_hint}")

        return OpeningPolicy(
            mode=mode,
            age_band=age_band,
            max_chars=max_chars,
            max_spoken_options=max_spoken_options,
            seed_topic=seed_topic,
            seed_recall_allowed=seed_recall_allowed,
            seed_recall_reason=seed_recall_reason,
            boundary_kind=boundary_kind,
            boundary_topic=boundary_topic,
            boundary_cooldown_active=boundary_cooldown_active,
            bedtime=bedtime,
            exciting_topic_deferred=exciting_topic_deferred,
            must_offer_topic_switch=True,
            must_allow_no_chat=True,
            prefer_parent_bridge=prefer_parent_bridge,
            parent_goal_hint=parent_goal_hint,
            forbidden_phrases=FORBIDDEN_OPENING_PHRASES,
            prompt_rules=tuple(rules),
        )

    def _boundary_info(
        self,
        boundary: MemoryItem | None,
    ) -> tuple[str | None, str | None]:
        if boundary is None:
            return None, None
        metadata = memory_relationship_metadata(boundary)
        kind = metadata.get("boundary_kind")
        topic = memory_relationship_topic(boundary)
        if not isinstance(kind, str):
            if topic == "睡前收尾":
                kind = "bedtime_close"
            elif topic == "换话题边界":
                kind = "topic_change"
            else:
                kind = "topic_boundary"
        return kind, topic

    def _latest_low_expression_state(self, child_id: str) -> MemoryItem | None:
        memories = self._memory_service.list_memories(
            child_id,
            active_only=True,
            include_safety=False,
        )
        candidates = [
            memory
            for memory in memories
            if memory.memory_type
            in {MemoryType.EMOTION_OBSERVATION, MemoryType.EXPRESSION_PATTERN}
            and self._contains_any(
                " ".join([memory.content, *memory.tags]),
                ("低能量", "不想说话", "短句", "说不完整", "低压力"),
            )
        ]
        return max(
            candidates,
            key=lambda memory: (
                memory.updated_at,
                memory.created_at,
                memory.importance,
                memory.confidence,
            ),
            default=None,
        )

    def _boundary_cooldown_active(
        self,
        *,
        child_id: str,
        boundary_kind: str | None,
        boundary_topic: str | None,
    ) -> bool:
        if boundary_kind is None:
            return False
        key = (child_id, boundary_kind, boundary_topic or "*")
        used_count = self._boundary_cooldown_counts.get(key, 0)
        if boundary_kind == "topic_change":
            return used_count < 3
        if boundary_kind == "bedtime_close":
            return used_count < 1
        if boundary_kind == "refusal":
            return True
        return used_count < 1

    def _interest_recall_count(self, child_id: str, seed_topic: str | None) -> int:
        if not seed_topic:
            return 0
        return self._interest_recall_counts.get((child_id, seed_topic), 0)

    def _age_band(self, parent_policy: ParentPolicy) -> str:
        preferences = parent_policy.communication_preferences
        explicit = preferences.get("age_band")
        if explicit in {"age_5_6", "age_7_8", "age_9_10", "unknown"}:
            return str(explicit)
        raw_age = preferences.get("child_age") or preferences.get("age")
        try:
            age = int(raw_age)
        except (TypeError, ValueError):
            return "age_7_8"
        if age <= 6:
            return "age_5_6"
        if age >= 9:
            return "age_9_10"
        return "age_7_8"

    def _age_limits(self, age_band: str) -> tuple[int, int]:
        if age_band == "age_5_6":
            return 36, 2
        if age_band == "age_9_10":
            return 60, 3
        if age_band == "unknown":
            return 42, 2
        return 48, 2

    def _parent_goal_hint(
        self,
        parent_policy: ParentPolicy,
        time_context: TimeContext,
    ) -> str | None:
        text = " ".join(parent_policy.goals + [self._parent_text(parent_policy)])
        if time_context.time_period == TimePeriod.BEDTIME or self._contains_any(
            text,
            ("早点睡", "睡眠", "睡觉", "早睡"),
        ):
            return "低刺激收束，必要时提醒可以告诉家长后去休息。"
        if self._contains_any(text, ("学习", "作业", "题目", "复习")):
            return "如果孩子主动提到学习，只提供一个小问题或帮他拆开一点。"
        if self._contains_any(text, ("家长", "爸爸妈妈", "父母", "告诉爸爸", "告诉妈妈")):
            return "这句话也可以告诉家长，小白狐只先听一点点。"
        return None

    def _parent_text(self, parent_policy: ParentPolicy) -> str:
        return (parent_policy.parent_message_raw or "").strip()

    def _no_school_check(self, parent_policy: ParentPolicy) -> bool:
        text = self._parent_text(parent_policy)
        return self._contains_any(
            text,
            ("不要查岗学校", "不要问学校", "别问学校"),
        )

    def _profile_interest_seed(
        self,
        parent_policy: ParentPolicy,
        boundary_topic: str | None,
    ) -> str | None:
        interests = parent_policy.communication_preferences.get("child_interests")
        if isinstance(interests, str):
            candidates = [
                item.strip()
                for item in interests.replace("、", "，").replace(",", "，").split("，")
                if item.strip()
            ]
        elif isinstance(interests, list):
            candidates = [str(item).strip() for item in interests if str(item).strip()]
        else:
            candidates = []
        boundary = (boundary_topic or "").strip()
        for candidate in candidates:
            if boundary and boundary in candidate:
                continue
            if self._is_exciting_topic(candidate):
                continue
            return candidate[:40]
        return None

    def _is_exciting_topic(self, topic: str) -> bool:
        return self._contains_any(topic, _EXCITING_TOPICS)

    def _contains_any(self, text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)
