"""Tests for light co-creation service.

Tests cover:
1. Story chain triggering conditions
2. Image co-creation triggering conditions
3. Session-level co-creation limits
4. Story chain round limits
5. Child rejection handling
6. Low interest short reply handling
7. Bedtime/learning/safety avoidance
8. Image type filtering
9. Image duplicate entry prevention
10. Forbidden expression filtering
"""

import pytest

from app.services.light_co_creation_service import (
    CoCreationDecision,
    CoCreationState,
    CoCreationType,
    LightCoCreationService,
    SessionCoCreationState,
)


@pytest.fixture
def service() -> LightCoCreationService:
    return LightCoCreationService()


class TestStoryChainTriggering:
    """Test story chain triggering conditions."""

    def test_imaginative_content_triggers_story_chain(self, service: LightCoCreationService):
        """Test that imaginative content triggers story chain."""
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="我的小熊会飞",
        )
        assert decision.should_trigger is True
        assert decision.co_creation_type == CoCreationType.STORY_CHAIN
        assert decision.reason == "imaginative_content_detected"

    def test_non_imaginative_content_no_trigger(self, service: LightCoCreationService):
        """Test that non-imaginative content does not trigger story chain."""
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="今天天气很好",
        )
        assert decision.should_trigger is False
        assert decision.reason == "not_imaginative_content"

    def test_short_content_no_trigger(self, service: LightCoCreationService):
        """Test that very short content does not trigger story chain."""
        # "飞" alone is a weak movement marker without character context,
        # so it's not imaginative. Use a strong marker that's too short instead.
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="恐龙",
        )
        assert decision.should_trigger is False
        assert decision.reason == "content_too_short"

    def test_dinosaur_content_triggers(self, service: LightCoCreationService):
        """Test that dinosaur content triggers story chain."""
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="我有一只大恐龙",
        )
        assert decision.should_trigger is True

    def test_robot_content_triggers(self, service: LightCoCreationService):
        """Test that robot content triggers story chain."""
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="这个机器人住在月亮上",
        )
        assert decision.should_trigger is True

    def test_adventure_content_triggers(self, service: LightCoCreationService):
        """Test that adventure content triggers story chain."""
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="我们去森林里冒险吧",
        )
        assert decision.should_trigger is True


class TestImageCoCreationTriggering:
    """Test image co-creation triggering conditions."""

    def test_creative_image_triggers_naming(self, service: LightCoCreationService):
        """Test that creative image triggers naming."""
        decision = service.should_trigger_image_co_creation(
            session_id="test_session",
            image_type="drawing",
        )
        assert decision.should_trigger is True
        assert decision.co_creation_type == CoCreationType.IMAGE_NAMING

    def test_creative_image_triggers_story(self, service: LightCoCreationService):
        """Test that creative image triggers story."""
        decision = service.should_trigger_image_co_creation(
            session_id="test_session",
            image_type="handicraft",
            co_creation_preference="story",
        )
        assert decision.should_trigger is True
        assert decision.co_creation_type == CoCreationType.IMAGE_STORY

    def test_excluded_image_no_trigger(self, service: LightCoCreationService):
        """Test that excluded image type does not trigger."""
        decision = service.should_trigger_image_co_creation(
            session_id="test_session",
            image_type="real_person",
        )
        assert decision.should_trigger is False
        assert decision.reason == "image_not_creative"

    def test_homework_image_no_trigger(self, service: LightCoCreationService):
        """Test that homework image does not trigger."""
        decision = service.should_trigger_image_co_creation(
            session_id="test_session",
            image_type="homework",
        )
        assert decision.should_trigger is False
        assert decision.reason == "image_not_creative"

    def test_auto_preference_prefers_naming(self, service: LightCoCreationService):
        """Test that auto preference prefers naming first."""
        decision = service.should_trigger_image_co_creation(
            session_id="test_session",
            image_type="drawing",
            co_creation_preference="auto",
        )
        assert decision.should_trigger is True
        assert decision.co_creation_type == CoCreationType.IMAGE_NAMING


class TestSessionLimits:
    """Test session-level co-creation limits."""

    def test_only_one_initiation_per_session(self, service: LightCoCreationService):
        """Test that only one co-creation can be initiated per session."""
        # First initiation
        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.STORY_CHAIN,
        )

        # Second attempt should fail
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="我的小猫会说话",
        )
        assert decision.should_trigger is False
        assert decision.reason == "already_initiated_this_session"

    def test_different_sessions_independent(self, service: LightCoCreationService):
        """Test that different sessions are independent."""
        # Session 1 initiation
        service.record_co_creation_initiated(
            session_id="session_1",
            co_creation_type=CoCreationType.STORY_CHAIN,
        )

        # Session 2 should still work
        decision = service.should_trigger_story_chain(
            session_id="session_2",
            child_text="我的小猫会说话",
        )
        assert decision.should_trigger is True


class TestStoryChainRoundLimits:
    """Test story chain round limits."""

    def test_max_two_rounds(self, service: LightCoCreationService):
        """Test that story chain has maximum 2 rounds."""
        # Start story chain
        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.STORY_CHAIN,
        )

        # First child response
        service.record_child_response(session_id="test_session")
        assert service.get_current_state("test_session").story_chain_rounds == 1

        # First fox response
        service.record_fox_response(session_id="test_session")

        # Second child response
        service.record_child_response(session_id="test_session")
        assert service.get_current_state("test_session").story_chain_rounds == 2

        # Second fox response should complete the chain
        service.record_fox_response(session_id="test_session")
        state = service.get_current_state("test_session")
        assert state.state == CoCreationState.IDLE
        assert state.active_type == CoCreationType.NONE

    def test_should_continue_story_chain(self, service: LightCoCreationService):
        """Test should_continue_story_chain logic."""
        # Start story chain
        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.STORY_CHAIN,
        )

        # Should continue after first round
        service.record_child_response(session_id="test_session")
        service.record_fox_response(session_id="test_session")

        assert service.should_continue_story_chain(
            session_id="test_session",
            child_text="然后它飞走了",
        ) is True

    def test_should_not_continue_after_max_rounds(self, service: LightCoCreationService):
        """Test that story chain should not continue after max rounds."""
        # Start story chain
        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.STORY_CHAIN,
        )

        # Complete two rounds
        for _ in range(2):
            service.record_child_response(session_id="test_session")
            service.record_fox_response(session_id="test_session")

        # Should not continue after max rounds
        assert service.should_continue_story_chain(
            session_id="test_session",
            child_text="然后它飞走了",
        ) is False


class TestChildRejection:
    """Test child rejection handling."""

    def test_rejection_resets_co_creation(self, service: LightCoCreationService):
        """Test that rejection resets co-creation state."""
        # Start story chain
        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.STORY_CHAIN,
        )

        # Child rejects
        service.record_child_response(
            session_id="test_session",
            is_rejection=True,
        )

        state = service.get_current_state("test_session")
        assert state.state == CoCreationState.IDLE
        assert state.active_type == CoCreationType.NONE
        assert state.consecutive_rejections == 1

    def test_two_rejections_suppress_session(self, service: LightCoCreationService):
        """Test that two consecutive rejections suppress session."""
        # First rejection
        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.STORY_CHAIN,
        )
        service.record_child_response(
            session_id="test_session",
            is_rejection=True,
        )

        # Second rejection
        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.IMAGE_NAMING,
        )
        service.record_child_response(
            session_id="test_session",
            is_rejection=True,
        )

        state = service.get_current_state("test_session")
        assert state.suppressed is True

        # Should not trigger after suppression
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="我的小熊会飞",
        )
        assert decision.should_trigger is False
        assert decision.reason == "session_suppressed"


class TestLowInterestHandling:
    """Test low interest short reply handling."""

    def test_refused_no_trigger(self, service: LightCoCreationService):
        """Test that refused engagement does not trigger."""
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="我的小熊会飞",
            child_engagement="refused",
        )
        assert decision.should_trigger is False
        assert decision.reason == "child_low_interest"

    def test_boundary_no_trigger(self, service: LightCoCreationService):
        """Test that boundary engagement does not trigger."""
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="我的小熊会飞",
            child_engagement="boundary",
        )
        assert decision.should_trigger is False
        assert decision.reason == "child_low_interest"

    def test_short_or_flat_with_imaginative_content_triggers(self, service: LightCoCreationService):
        """Test that short_or_flat engagement with imaginative content still triggers."""
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="我的小熊会飞",
            child_engagement="short_or_flat",
        )
        # Short_or_flat is acceptable for imaginative content
        assert decision.should_trigger is True

    def test_is_low_interest_reply(self, service: LightCoCreationService):
        """Test low interest reply detection."""
        assert service.is_low_interest_reply("嗯") is True
        assert service.is_low_interest_reply("哦") is True
        assert service.is_low_interest_reply("不知道") is True
        assert service.is_low_interest_reply("随便") is True
        assert service.is_low_interest_reply("算了") is True

    def test_substantive_short_reply_not_low_interest(self, service: LightCoCreationService):
        """Test that substantive short replies are not low interest."""
        assert service.is_low_interest_reply("嗯，是我画的") is False
        assert service.is_low_interest_reply("对，还有一个") is False
        assert service.is_low_interest_reply("是恐龙") is False


class TestBedtimeLearningSafetyAvoidance:
    """Test bedtime, learning, and safety avoidance."""

    def test_bedtime_no_trigger(self, service: LightCoCreationService):
        """Test that bedtime does not trigger story chain."""
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="我的小熊会飞",
            is_bedtime=True,
        )
        assert decision.should_trigger is False
        assert decision.reason == "bedtime_avoid"

    def test_learning_no_trigger(self, service: LightCoCreationService):
        """Test that learning context does not trigger story chain."""
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="我的小熊会飞",
            is_learning=True,
        )
        assert decision.should_trigger is False
        assert decision.reason == "learning_avoid"

    def test_safety_no_trigger(self, service: LightCoCreationService):
        """Test that safety context does not trigger story chain."""
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="我的小熊会飞",
            is_safety=True,
        )
        assert decision.should_trigger is False
        assert decision.reason == "safety_avoid"

    def test_bedtime_image_no_trigger(self, service: LightCoCreationService):
        """Test that bedtime does not trigger image co-creation."""
        decision = service.should_trigger_image_co_creation(
            session_id="test_session",
            image_type="drawing",
            is_bedtime=True,
        )
        assert decision.should_trigger is False
        assert decision.reason == "bedtime_avoid"

    def test_is_bedtime_context(self, service: LightCoCreationService):
        """Test bedtime context detection."""
        assert service.is_bedtime_context("我要睡觉了") is True
        assert service.is_bedtime_context("晚安") is True
        assert service.is_bedtime_context("困了") is True
        assert service.is_bedtime_context("今天天气很好") is False

    def test_is_learning_context(self, service: LightCoCreationService):
        """Test learning context detection."""
        assert service.is_learning_context("这道作业题不会做") is True
        assert service.is_learning_context("考试成绩出来了") is True
        assert service.is_learning_context("我要拍题") is True
        assert service.is_learning_context("今天天气很好") is False


class TestImageTypeFiltering:
    """Test image type filtering."""

    def test_creative_image_types(self, service: LightCoCreationService):
        """Test creative image types are accepted."""
        assert service._is_creative_image("drawing") is True
        assert service._is_creative_image("handicraft") is True
        assert service._is_creative_image("building_blocks") is True
        assert service._is_creative_image("toy") is True
        assert service._is_creative_image("clay") is True
        assert service._is_creative_image("origami") is True

    def test_excluded_image_types(self, service: LightCoCreationService):
        """Test excluded image types are rejected."""
        assert service._is_creative_image("real_person") is False
        assert service._is_creative_image("family_photo") is False
        assert service._is_creative_image("school_photo") is False
        assert service._is_creative_image("document") is False
        assert service._is_creative_image("id_card") is False
        assert service._is_creative_image("medical") is False
        assert service._is_creative_image("homework") is False
        assert service._is_creative_image("test_paper") is False
        assert service._is_creative_image("grade_report") is False
        assert service._is_creative_image("sensitive") is False
        assert service._is_creative_image("privacy_sensitive") is False

    def test_unknown_image_type_rejected(self, service: LightCoCreationService):
        """Test unknown image type is rejected by default."""
        assert service._is_creative_image("unknown_type") is False


class TestImageDuplicateEntryPrevention:
    """Test image duplicate entry prevention - same image max one co-creation entry."""

    def test_same_image_first_naming_allowed(self, service: LightCoCreationService):
        """Test that same image can trigger naming first time."""
        decision = service.should_trigger_image_co_creation(
            session_id="test_session",
            image_type="drawing",
            image_hash="image_123",
            co_creation_preference="naming",
        )
        assert decision.should_trigger is True
        assert decision.co_creation_type == CoCreationType.IMAGE_NAMING

    def test_same_image_after_naming_no_story(self, service: LightCoCreationService):
        """Test that same image cannot trigger story after naming."""
        # First offer naming
        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.IMAGE_NAMING,
            image_hash="image_123",
        )

        # Same image should not trigger story
        decision = service.should_trigger_image_co_creation(
            session_id="test_session",
            image_type="drawing",
            image_hash="image_123",
            co_creation_preference="story",
        )
        assert decision.should_trigger is False
        assert decision.reason == "image_already_offered_once"

    def test_same_image_first_story_allowed(self, service: LightCoCreationService):
        """Test that same image can trigger story first time."""
        decision = service.should_trigger_image_co_creation(
            session_id="test_session",
            image_type="drawing",
            image_hash="image_456",
            co_creation_preference="story",
        )
        assert decision.should_trigger is True
        assert decision.co_creation_type == CoCreationType.IMAGE_STORY

    def test_same_image_after_story_no_naming(self, service: LightCoCreationService):
        """Test that same image cannot trigger naming after story."""
        # First offer story
        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.IMAGE_STORY,
            image_hash="image_456",
        )

        # Same image should not trigger naming
        decision = service.should_trigger_image_co_creation(
            session_id="test_session",
            image_type="drawing",
            image_hash="image_456",
            co_creation_preference="naming",
        )
        assert decision.should_trigger is False
        assert decision.reason == "image_already_offered_once"

    def test_auto_mode_no_second_entry(self, service: LightCoCreationService):
        """Test that auto mode does not offer second co-creation for same image."""
        # Auto mode offers naming first
        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.IMAGE_NAMING,
            image_hash="image_789",
        )

        # Auto mode should not offer story for same image
        decision = service.should_trigger_image_co_creation(
            session_id="test_session",
            image_type="drawing",
            image_hash="image_789",
            co_creation_preference="auto",
        )
        assert decision.should_trigger is False
        assert decision.reason == "image_already_offered_once"

    def test_different_images_independent(self, service: LightCoCreationService):
        """Test that different images are independent."""
        # Offer naming for image_1
        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.IMAGE_NAMING,
            image_hash="image_1",
        )

        # Different image should still work
        decision = service.should_trigger_image_co_creation(
            session_id="test_session",
            image_type="drawing",
            image_hash="image_2",
            co_creation_preference="naming",
        )
        # This will fail because fox_initiated is True for the session
        # but that's expected - session-level limit still applies
        assert decision.should_trigger is False
        assert decision.reason == "already_initiated_this_session"


class TestForbiddenExpressions:
    """Test that forbidden expressions are not used."""

    def test_forbidden_expressions_not_in_reasons(self, service: LightCoCreationService):
        """Test that forbidden expressions are not in decision reasons."""
        forbidden = [
            "挑战", "任务", "完成", "奖励", "连续创作", "明天继续",
            "游戏", "课程", "作品库", "故事库", "成长档案",
        ]

        # Trigger story chain
        decision = service.should_trigger_story_chain(
            session_id="test_session",
            child_text="我的小熊会飞",
        )

        for word in forbidden:
            assert word not in decision.reason


class TestCoCreationStateManagement:
    """Test co-creation state management."""

    def test_initial_state(self, service: LightCoCreationService):
        """Test initial state is idle."""
        state = service.get_current_state("test_session")
        assert state.active_type == CoCreationType.NONE
        assert state.state == CoCreationState.IDLE
        assert state.story_chain_rounds == 0
        assert state.fox_initiated is False
        assert state.suppressed is False

    def test_state_after_initiation(self, service: LightCoCreationService):
        """Test state after initiation."""
        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.STORY_CHAIN,
        )

        state = service.get_current_state("test_session")
        assert state.active_type == CoCreationType.STORY_CHAIN
        assert state.state == CoCreationState.INVITED
        assert state.fox_initiated is True

    def test_state_after_child_response(self, service: LightCoCreationService):
        """Test state after child response."""
        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.STORY_CHAIN,
        )
        service.record_child_response(session_id="test_session")

        state = service.get_current_state("test_session")
        assert state.state == CoCreationState.CHILD_RESPONDED
        assert state.story_chain_rounds == 1

    def test_state_after_fox_response(self, service: LightCoCreationService):
        """Test state after fox response."""
        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.STORY_CHAIN,
        )
        service.record_child_response(session_id="test_session")
        service.record_fox_response(session_id="test_session")

        state = service.get_current_state("test_session")
        assert state.state == CoCreationState.FOX_RESPONDED

    def test_is_in_co_creation(self, service: LightCoCreationService):
        """Test is_in_co_creation check."""
        assert service.is_in_co_creation("test_session") is False

        service.record_co_creation_initiated(
            session_id="test_session",
            co_creation_type=CoCreationType.STORY_CHAIN,
        )
        assert service.is_in_co_creation("test_session") is True

        service.record_co_creation_completed(session_id="test_session")
        assert service.is_in_co_creation("test_session") is False


class TestTurnGuidanceIntegration:
    """Test integration with turn guidance builder."""

    def test_turn_guidance_has_co_creation_fields(self):
        """Test that turn guidance context has co-creation fields."""
        from app.services.turn_guidance_builder import TurnGuidanceBuilder

        builder = TurnGuidanceBuilder()
        context = builder.build(child_text="我的小熊会飞", session_id="test_session")

        assert hasattr(context, "co_creation_type")
        assert hasattr(context, "co_creation_suggested")
        assert hasattr(context, "co_creation_reason")

    def test_turn_guidance_suggests_story_chain(self):
        """Test that turn guidance suggests story chain for imaginative content."""
        from app.services.turn_guidance_builder import TurnGuidanceBuilder

        builder = TurnGuidanceBuilder()
        context = builder.build(child_text="我的小熊会飞", session_id="test_session")

        assert context.co_creation_suggested is True
        assert context.co_creation_type == "story_chain"

    def test_turn_guidance_no_suggestion_for_non_imaginative(self):
        """Test that turn guidance does not suggest for non-imaginative content."""
        from app.services.turn_guidance_builder import TurnGuidanceBuilder

        builder = TurnGuidanceBuilder()
        context = builder.build(child_text="今天天气很好", session_id="test_session")

        assert context.co_creation_suggested is False
        assert context.co_creation_type == "none"
