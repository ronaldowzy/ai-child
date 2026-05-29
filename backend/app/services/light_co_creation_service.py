"""Light co-creation service for managing story chains, image naming, and image stories.

This service manages the state and rules for light co-creation features:
1. Story chain: child and fox take turns adding one sentence to a story
2. Image naming: child gives a name to their artwork
3. Image story: child tells one sentence about their artwork

Key rules:
- Same session: max 1 active co-creation initiation by fox
- Same image: max 1 co-creation entry (naming OR story, not both)
- Story chain: max 2 rounds of child input
- Child not responding: let go within 1 turn
- Low interest short replies: reduce intensity
- Bedtime/learning/safety/privacy: avoid co-creation
"""

import logging
import time
from dataclasses import dataclass, field
from enum import StrEnum

logger = logging.getLogger("app.light_co_creation")


class CoCreationType(StrEnum):
    """Types of light co-creation."""
    NONE = "none"
    STORY_CHAIN = "story_chain"
    IMAGE_NAMING = "image_naming"
    IMAGE_STORY = "image_story"


class CoCreationState(StrEnum):
    """States of co-creation flow."""
    IDLE = "idle"
    INVITED = "invited"
    CHILD_RESPONDED = "child_responded"
    FOX_RESPONDED = "fox_responded"
    COMPLETED = "completed"
    REJECTED = "rejected"


@dataclass
class SessionCoCreationState:
    """Per-session co-creation tracking."""
    # Whether fox has initiated any co-creation this session
    fox_initiated: bool = False
    # Current active co-creation type
    active_type: CoCreationType = CoCreationType.NONE
    # Current state of the flow
    state: CoCreationState = CoCreationState.IDLE
    # Number of child input rounds in current story chain
    story_chain_rounds: int = 0
    # Image hash that triggered co-creation (to prevent duplicate entries)
    image_hash: str | None = None
    # Whether image has been offered naming
    image_naming_offered: bool = False
    # Whether image has been offered story
    image_story_offered: bool = False
    # Number of consecutive child rejections
    consecutive_rejections: int = 0
    # Timestamp of last co-creation activity
    last_activity_ts: float = 0.0
    # Whether co-creation is suppressed for this session
    suppressed: bool = False

    def reset(self) -> None:
        """Reset active co-creation state (but keep session-level tracking)."""
        self.active_type = CoCreationType.NONE
        self.state = CoCreationState.IDLE
        self.story_chain_rounds = 0


@dataclass
class CoCreationDecision:
    """Decision about whether to trigger co-creation."""
    should_trigger: bool = False
    co_creation_type: CoCreationType = CoCreationType.NONE
    reason: str = ""
    # Suggested fox response for the co-creation
    fox_response_hint: str = ""


class LightCoCreationService:
    """Service managing light co-creation rules and state."""

    # Maximum story chain rounds (child input rounds)
    MAX_STORY_CHAIN_ROUNDS = 2
    # Maximum consecutive rejections before suppressing
    MAX_CONSECUTIVE_REJECTIONS = 2
    # Co-creation suppression duration after rejection (seconds)
    REJECTION_SUPPRESS_SECONDS = 300.0

    # Image types suitable for co-creation
    _CREATIVE_IMAGE_TYPES = {
        "drawing",
        "handicraft",
        "building_blocks",
        "toy",
        "clay",
        "origami",
        "artwork",
        "creation",
        "craft",
    }

    # Image types NOT suitable for co-creation
    _EXCLUDED_IMAGE_TYPES = {
        "real_person",
        "family_photo",
        "school_photo",
        "document",
        "id_card",
        "medical",
        "homework",
        "test_paper",
        "grade_report",
        "sensitive",
        "privacy_sensitive",
    }

    # Strong imagination signals: characters, story triggers, fantasy settings.
    # These alone are enough to suggest co-creation.
    _STRONG_IMAGINATION_MARKERS = (
        "小熊", "小猫", "小狗", "小兔", "恐龙", "机器人", "外星人",
        "公主", "王子", "超人", "奥特曼", "怪兽", "精灵", "魔法",
        "冒险", "探险",
        "森林", "海洋", "太空", "月亮", "星球", "城堡",
        "故事", "编", "想象", "如果", "要是",
        "云朵", "星星", "彩虹",
        "小车", "小船", "飞机", "火箭",
    )

    # Weak movement words: common in everyday speech (跑步, 跳绳, 打球).
    # Only trigger co-creation when combined with a character or story context.
    _WEAK_MOVEMENT_MARKERS = (
        "飞", "跑", "跳", "游", "爬",
    )

    # Character/context markers that make movement words imaginative.
    _CHARACTER_MARKERS = (
        "小熊", "小猫", "小狗", "小兔", "恐龙", "机器人", "外星人",
        "公主", "王子", "超人", "奥特曼", "怪兽", "精灵",
        "城堡", "星球", "月亮", "太空", "森林", "海洋",
    )

    # Combined set for backward compatibility (used by _is_imaginative_content)
    _IMAGINATIVE_MARKERS = _STRONG_IMAGINATION_MARKERS

    # Low interest short reply markers
    _LOW_INTEREST_MARKERS = (
        "嗯", "哦", "好吧", "不知道", "还行", "随便",
        "没有", "没了", "算了", "都行", "不想", "不要",
        "不用", "换个话题", "说别的", "别聊这个",
    )

    # Content markers that indicate short replies are NOT low interest
    _SUBSTANTIVE_MARKERS = (
        "是", "有", "对", "好", "画", "做", "写", "看",
        "玩", "吃", "说", "想", "要", "会", "能",
    )

    # Bedtime markers
    _BEDTIME_MARKERS = (
        "睡觉", "晚安", "困了", "要休息", "明天再聊",
    )

    # Learning markers
    _LEARNING_MARKERS = (
        "作业", "题目", "考试", "成绩", "练习", "试卷",
        "拍题", "做题", "不会做", "答案",
    )

    def __init__(self) -> None:
        self._session_states: dict[str, SessionCoCreationState] = {}

    def _get_session_state(self, session_id: str) -> SessionCoCreationState:
        """Get or create session state."""
        if session_id not in self._session_states:
            self._session_states[session_id] = SessionCoCreationState()
        return self._session_states[session_id]

    def should_trigger_story_chain(
        self,
        *,
        session_id: str,
        child_text: str,
        is_bedtime: bool = False,
        is_learning: bool = False,
        is_safety: bool = False,
        child_engagement: str = "neutral",
    ) -> CoCreationDecision:
        """Decide whether to trigger story chain based on child's input."""
        state = self._get_session_state(session_id)

        # Check suppression conditions
        if state.suppressed:
            return CoCreationDecision(reason="session_suppressed")

        if is_bedtime:
            return CoCreationDecision(reason="bedtime_avoid")

        if is_learning:
            return CoCreationDecision(reason="learning_avoid")

        if is_safety:
            return CoCreationDecision(reason="safety_avoid")

        # Check if already initiated this session
        if state.fox_initiated:
            return CoCreationDecision(reason="already_initiated_this_session")

        # Check if child's content is imaginative and continuation-friendly
        normalized = child_text.strip().lower().replace(" ", "")
        if not self._is_imaginative_content(normalized):
            return CoCreationDecision(reason="not_imaginative_content")

        # Check if content is long enough to be meaningful
        if len(normalized) < 4:
            return CoCreationDecision(reason="content_too_short")

        # For imaginative content, we should be more lenient with engagement signals
        # Only reject if child explicitly refused or showed boundary
        if child_engagement in ("refused", "boundary"):
            return CoCreationDecision(reason="child_low_interest")

        # Short_or_flat engagement is acceptable for imaginative content
        # because the content itself shows engagement

        # All checks passed, suggest story chain
        return CoCreationDecision(
            should_trigger=True,
            co_creation_type=CoCreationType.STORY_CHAIN,
            reason="imaginative_content_detected",
        )

    def should_trigger_image_co_creation(
        self,
        *,
        session_id: str,
        image_type: str,
        image_hash: str | None = None,
        is_bedtime: bool = False,
        is_learning: bool = False,
        is_safety: bool = False,
        child_engagement: str = "neutral",
        co_creation_preference: str = "auto",
    ) -> CoCreationDecision:
        """Decide whether to trigger image naming or image story."""
        state = self._get_session_state(session_id)

        # Check suppression conditions
        if state.suppressed:
            return CoCreationDecision(reason="session_suppressed")

        if is_bedtime:
            return CoCreationDecision(reason="bedtime_avoid")

        if is_learning:
            return CoCreationDecision(reason="learning_avoid")

        if is_safety:
            return CoCreationDecision(reason="safety_avoid")

        # Check if child is showing low interest
        if child_engagement in ("short_or_flat", "refused", "boundary"):
            return CoCreationDecision(reason="child_low_interest")

        # Check if image type is suitable
        if not self._is_creative_image(image_type):
            return CoCreationDecision(reason="image_not_creative")

        # Check if this specific image has already been offered any co-creation
        # Same image can only have ONE co-creation entry (naming OR story, not both)
        if image_hash and image_hash == state.image_hash:
            if state.image_naming_offered or state.image_story_offered:
                return CoCreationDecision(reason="image_already_offered_once")

        # Check if already initiated this session (but not for the same image)
        if state.fox_initiated and (not image_hash or image_hash != state.image_hash):
            return CoCreationDecision(reason="already_initiated_this_session")

        # Decide which type to offer based on preference
        if co_creation_preference == "naming":
            return CoCreationDecision(
                should_trigger=True,
                co_creation_type=CoCreationType.IMAGE_NAMING,
                reason="creative_image_naming",
            )
        elif co_creation_preference == "story":
            return CoCreationDecision(
                should_trigger=True,
                co_creation_type=CoCreationType.IMAGE_STORY,
                reason="creative_image_story",
            )
        else:
            # Auto: prefer naming first
            return CoCreationDecision(
                should_trigger=True,
                co_creation_type=CoCreationType.IMAGE_NAMING,
                reason="creative_image_naming",
            )

    def record_co_creation_initiated(
        self,
        *,
        session_id: str,
        co_creation_type: CoCreationType,
        image_hash: str | None = None,
    ) -> None:
        """Record that fox has initiated a co-creation."""
        state = self._get_session_state(session_id)
        state.fox_initiated = True
        state.active_type = co_creation_type
        state.state = CoCreationState.INVITED
        state.last_activity_ts = time.monotonic()

        if image_hash:
            state.image_hash = image_hash
            if co_creation_type == CoCreationType.IMAGE_NAMING:
                state.image_naming_offered = True
            elif co_creation_type == CoCreationType.IMAGE_STORY:
                state.image_story_offered = True

        logger.info(
            "co_creation_initiated",
            extra={
                "session_id": session_id,
                "co_creation_type": co_creation_type.value,
                "has_image_hash": image_hash is not None,
            },
        )

    def record_child_response(
        self,
        *,
        session_id: str,
        is_rejection: bool = False,
        is_low_interest: bool = False,
    ) -> None:
        """Record child's response to co-creation invitation."""
        state = self._get_session_state(session_id)

        if is_rejection or is_low_interest:
            state.consecutive_rejections += 1
            if state.consecutive_rejections >= self.MAX_CONSECUTIVE_REJECTIONS:
                state.suppressed = True
                logger.info(
                    "co_creation_suppressed_due_to_rejections",
                    extra={"session_id": session_id},
                )
            state.state = CoCreationState.REJECTED
            # Reset active co-creation
            state.reset()
        else:
            state.consecutive_rejections = 0
            state.state = CoCreationState.CHILD_RESPONDED
            if state.active_type == CoCreationType.STORY_CHAIN:
                state.story_chain_rounds += 1

    def record_fox_response(
        self,
        *,
        session_id: str,
    ) -> None:
        """Record fox's response in co-creation flow."""
        state = self._get_session_state(session_id)
        state.state = CoCreationState.FOX_RESPONDED
        state.last_activity_ts = time.monotonic()

        # Check if story chain should end
        if state.active_type == CoCreationType.STORY_CHAIN:
            if state.story_chain_rounds >= self.MAX_STORY_CHAIN_ROUNDS:
                state.state = CoCreationState.COMPLETED
                state.reset()

    def record_co_creation_completed(
        self,
        *,
        session_id: str,
    ) -> None:
        """Record that co-creation has completed."""
        state = self._get_session_state(session_id)
        state.state = CoCreationState.COMPLETED
        state.reset()

    def get_current_state(
        self,
        session_id: str,
    ) -> SessionCoCreationState:
        """Get current co-creation state for a session."""
        return self._get_session_state(session_id)

    def is_in_co_creation(
        self,
        session_id: str,
    ) -> bool:
        """Check if session is currently in an active co-creation flow."""
        state = self._get_session_state(session_id)
        return state.active_type != CoCreationType.NONE and state.state not in (
            CoCreationState.IDLE,
            CoCreationState.COMPLETED,
            CoCreationState.REJECTED,
        )

    def should_continue_story_chain(
        self,
        *,
        session_id: str,
        child_text: str,
        child_engagement: str = "neutral",
    ) -> bool:
        """Check if story chain should continue based on child's input."""
        state = self._get_session_state(session_id)

        # Not in story chain
        if state.active_type != CoCreationType.STORY_CHAIN:
            return False

        # Already completed
        if state.state == CoCreationState.COMPLETED:
            return False

        # Check if child is rejecting or showing low interest
        if child_engagement in ("short_or_flat", "refused", "boundary"):
            return False

        # Check if max rounds reached
        if state.story_chain_rounds >= self.MAX_STORY_CHAIN_ROUNDS:
            return False

        # Check if content is still continuation-friendly
        normalized = child_text.strip().lower().replace(" ", "")
        if len(normalized) < 2:
            return False

        return True

    def _is_imaginative_content(self, normalized: str) -> bool:
        """Check if content is imaginative and suitable for story chain.

        Strong imagination markers (characters, story triggers, fantasy settings)
        alone are sufficient. Weak movement words (飞/跑/跳/游/爬) only trigger
        when combined with a character or story context, to avoid false positives
        on everyday speech like "跑步" or "跳绳".
        """
        # Strong markers alone are enough
        if any(marker in normalized for marker in self._STRONG_IMAGINATION_MARKERS):
            return True
        # Weak movement words require a character/context marker
        has_movement = any(m in normalized for m in self._WEAK_MOVEMENT_MARKERS)
        has_character = any(m in normalized for m in self._CHARACTER_MARKERS)
        return has_movement and has_character

    def _is_creative_image(self, image_type: str) -> bool:
        """Check if image type is creative and suitable for co-creation."""
        normalized = image_type.strip().lower().replace(" ", "_")
        if normalized in self._EXCLUDED_IMAGE_TYPES:
            return False
        if normalized in self._CREATIVE_IMAGE_TYPES:
            return True
        # Default: if we can't determine, assume it's not creative
        return False

    def is_low_interest_reply(self, text: str) -> bool:
        """Check if text is a low interest short reply."""
        normalized = text.strip().lower().replace(" ", "")

        # Check for exact matches of low interest markers
        if normalized in self._LOW_INTEREST_MARKERS:
            return True

        # Check for short replies with substantive content
        # e.g., "嗯，是我画的" "对，还有一个"
        if len(normalized) <= 8:
            has_substantive = any(
                marker in normalized for marker in self._SUBSTANTIVE_MARKERS
            )
            if has_substantive:
                return False
            # Very short replies without substantive content
            if len(normalized) <= 4:
                return True

        return False

    def is_bedtime_context(self, text: str) -> bool:
        """Check if text indicates bedtime context."""
        normalized = text.strip().lower().replace(" ", "")
        return any(marker in normalized for marker in self._BEDTIME_MARKERS)

    def is_learning_context(self, text: str) -> bool:
        """Check if text indicates learning context."""
        normalized = text.strip().lower().replace(" ", "")
        return any(marker in normalized for marker in self._LEARNING_MARKERS)


_light_co_creation_service: LightCoCreationService | None = None


def get_light_co_creation_service() -> LightCoCreationService:
    """Get singleton instance of LightCoCreationService."""
    global _light_co_creation_service
    if _light_co_creation_service is None:
        _light_co_creation_service = LightCoCreationService()
    return _light_co_creation_service
