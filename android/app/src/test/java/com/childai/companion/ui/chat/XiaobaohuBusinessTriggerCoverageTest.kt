package com.childai.companion.ui.chat

import com.childai.companion.mascot.MascotState
import org.junit.Assert.assertEquals
import org.junit.Test

class XiaobaohuBusinessTriggerCoverageTest {
    @Test
    fun normalChildInteractionTriggersResolveToSafeBaseAttentionStates() {
        assertBusinessTrigger(
            name = "Ready -> idle",
            phase = ChildTurnUiPhase.Ready,
            expectedBase = XiaobaohuBaseAttentionState.Idle,
            expectedMascot = MascotState.Idle,
            expectedReason = "ready_idle",
        )
        assertBusinessTrigger(
            name = "Listening -> listening",
            phase = ChildTurnUiPhase.Listening,
            expectedBase = XiaobaohuBaseAttentionState.Listening,
            expectedMascot = MascotState.Listening,
            expectedReason = "voice_listening",
        )
        assertBusinessTrigger(
            name = "Recognizing -> thinking",
            phase = ChildTurnUiPhase.Recognizing,
            expectedBase = XiaobaohuBaseAttentionState.Thinking,
            expectedMascot = MascotState.Thinking,
            expectedReason = "recognizing_uses_thinking_asset",
        )
        assertBusinessTrigger(
            name = "Sending -> thinking",
            phase = ChildTurnUiPhase.Sending,
            expectedBase = XiaobaohuBaseAttentionState.Thinking,
            expectedMascot = MascotState.Thinking,
            expectedReason = "sending_uses_thinking_asset",
        )
        assertBusinessTrigger(
            name = "Thinking -> thinking",
            phase = ChildTurnUiPhase.Thinking,
            expectedBase = XiaobaohuBaseAttentionState.Thinking,
            expectedMascot = MascotState.Thinking,
            expectedReason = "thinking",
        )
    }

    @Test
    fun ttsAndImageBusinessTriggersResolveToSpeakingOrImageThinkingFallback() {
        assertBusinessTrigger(
            name = "SpeakingPending -> speaking",
            phase = ChildTurnUiPhase.SpeakingPending,
            expectedBase = XiaobaohuBaseAttentionState.Speaking,
            expectedMascot = MascotState.Speaking,
            expectedReason = "speaking_pending",
        )
        assertBusinessTrigger(
            name = "Speaking -> speaking",
            phase = ChildTurnUiPhase.Speaking,
            expectedBase = XiaobaohuBaseAttentionState.Speaking,
            expectedMascot = MascotState.Speaking,
            expectedReason = "speaking",
        )
        assertBusinessTrigger(
            name = "ImageProcessing -> looking_at_image using thinking asset",
            phase = ChildTurnUiPhase.ImageProcessing,
            expectedBase = XiaobaohuBaseAttentionState.LookingAtImage,
            expectedMascot = MascotState.Thinking,
            expectedReason = "looking_at_image_uses_thinking_asset",
        )
    }

    @Test
    fun boundaryAndFailureBusinessTriggersResolveToHighPriorityOverlays() {
        val permissionNeeded = XiaobaohuVisualStateResolver.resolve(ChildTurnUiPhase.PermissionNeeded)
        assertEquals(XiaobaohuBoundaryOverlay.SafetyConcern, permissionNeeded.boundaryOverlay)
        assertEquals(MascotState.SafetyConcern, permissionNeeded.mascotState)
        assertEquals(
            XiaobaohuVisualStateResolver.SAFETY_CONCERN_MIN_HOLD_MS,
            permissionNeeded.minHoldMs,
        )

        val serviceError = XiaobaohuVisualStateResolver.resolve(ChildTurnUiPhase.ServiceError)
        assertEquals(XiaobaohuBoundaryOverlay.NetworkError, serviceError.boundaryOverlay)
        assertEquals(MascotState.NetworkError, serviceError.mascotState)
        assertEquals(
            XiaobaohuVisualStateResolver.NETWORK_ERROR_MIN_HOLD_MS,
            serviceError.minHoldMs,
        )
    }

    @Test
    fun backendBoundarySignalsResolveWithoutCreatingScenePerAnimationMapping() {
        val privacy = XiaobaohuVisualStateResolver.resolve(
            agent = FoxAgentUiState(
                mood = FoxMood.PrivacyBoundary,
                motion = FoxMotion.SteadyBoundary,
            ),
            reason = "backend_privacy_signal",
        )
        assertEquals(XiaobaohuBoundaryOverlay.PrivacyBoundary, privacy.boundaryOverlay)
        assertEquals(MascotState.PrivacyBoundary, privacy.mascotState)
        assertEquals("backend_privacy_signal", privacy.reason)

        val homework = XiaobaohuVisualStateResolver.resolve(
            agent = FoxAgentUiState(
                mood = FoxMood.HomeworkFocus,
                motion = FoxMotion.HomeworkFocus,
            ),
            reason = "backend_homework_signal",
        )
        assertEquals(XiaobaohuBoundaryOverlay.HomeworkFocus, homework.boundaryOverlay)
        assertEquals(MascotState.HomeworkFocus, homework.mascotState)
        assertEquals("backend_homework_signal", homework.reason)

        val safety = XiaobaohuVisualStateResolver.resolve(
            agent = FoxAgentUiState(
                mood = FoxMood.SafetyConcern,
                motion = FoxMotion.ConcernedStill,
            ),
            reason = "backend_safety_signal",
        )
        assertEquals(XiaobaohuBoundaryOverlay.SafetyConcern, safety.boundaryOverlay)
        assertEquals(MascotState.SafetyConcern, safety.mascotState)
        assertEquals("backend_safety_signal", safety.reason)
    }

    @Test
    fun rewardRetentionLikeSignalsDoNotResolveToJumpingHappyOrSleepyByDefault() {
        val maybeReward = XiaobaohuVisualStateResolver.resolve(
            agent = FoxAgentUiState(
                mood = FoxMood.Encouraging,
                motion = FoxMotion.CelebrateSmall,
            ),
            reason = "generic_encouragement_signal",
        )
        assertEquals(XiaobaohuEmotionalOverlay.Encouraging, maybeReward.emotionalOverlay)
        assertEquals(MascotState.Idle, maybeReward.mascotState)
        assertEquals("encouraging_overlay_no_jumping_happy_by_default", maybeReward.reason)

        val sleepy = XiaobaohuVisualStateResolver.resolve(
            agent = FoxAgentUiState(
                mood = FoxMood.Sleepy,
                motion = FoxMotion.SleepyBlink,
            ),
            reason = "generic_sleepy_signal",
        )
        assertEquals(XiaobaohuEmotionalOverlay.Sleepy, sleepy.emotionalOverlay)
        assertEquals(MascotState.Idle, sleepy.mascotState)
        assertEquals("sleepy_overlay_not_auto_triggered", sleepy.reason)
    }

    private fun assertBusinessTrigger(
        name: String,
        phase: ChildTurnUiPhase,
        expectedBase: XiaobaohuBaseAttentionState,
        expectedMascot: MascotState,
        expectedReason: String,
    ) {
        val visualState = XiaobaohuVisualStateResolver.resolve(phase)

        assertEquals("$name base", expectedBase, visualState.baseAttention)
        assertEquals("$name boundary", XiaobaohuBoundaryOverlay.None, visualState.boundaryOverlay)
        assertEquals("$name mascot", expectedMascot, visualState.mascotState)
        assertEquals("$name reason", expectedReason, visualState.reason)
    }
}
