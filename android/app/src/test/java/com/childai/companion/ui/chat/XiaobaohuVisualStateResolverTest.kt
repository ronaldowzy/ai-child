package com.childai.companion.ui.chat

import com.childai.companion.mascot.MascotState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class XiaobaohuVisualStateResolverTest {
    @Test
    fun childTurnPhasesResolveToLayeredVisualStates() {
        val cases = listOf(
            VisualStateCase(
                name = "Ready",
                phase = ChildTurnUiPhase.Ready,
                baseAttention = XiaobaohuBaseAttentionState.Idle,
                emotionalOverlay = XiaobaohuEmotionalOverlay.Warm,
                boundaryOverlay = XiaobaohuBoundaryOverlay.None,
                mascotState = MascotState.Idle,
                minHoldMs = 0L,
                reason = "ready_idle",
            ),
            VisualStateCase(
                name = "Listening",
                phase = ChildTurnUiPhase.Listening,
                baseAttention = XiaobaohuBaseAttentionState.Listening,
                emotionalOverlay = XiaobaohuEmotionalOverlay.Warm,
                boundaryOverlay = XiaobaohuBoundaryOverlay.None,
                mascotState = MascotState.Listening,
                minHoldMs = 0L,
                reason = "voice_listening",
            ),
            VisualStateCase(
                name = "Recognizing",
                phase = ChildTurnUiPhase.Recognizing,
                baseAttention = XiaobaohuBaseAttentionState.Thinking,
                emotionalOverlay = XiaobaohuEmotionalOverlay.Curious,
                boundaryOverlay = XiaobaohuBoundaryOverlay.None,
                mascotState = MascotState.Thinking,
                minHoldMs = XiaobaohuVisualStateResolver.THINKING_MIN_HOLD_MS,
                reason = "recognizing_uses_thinking_asset",
            ),
            VisualStateCase(
                name = "Sending",
                phase = ChildTurnUiPhase.Sending,
                baseAttention = XiaobaohuBaseAttentionState.Thinking,
                emotionalOverlay = XiaobaohuEmotionalOverlay.Curious,
                boundaryOverlay = XiaobaohuBoundaryOverlay.None,
                mascotState = MascotState.Thinking,
                minHoldMs = XiaobaohuVisualStateResolver.THINKING_MIN_HOLD_MS,
                reason = "sending_uses_thinking_asset",
            ),
            VisualStateCase(
                name = "Thinking",
                phase = ChildTurnUiPhase.Thinking,
                baseAttention = XiaobaohuBaseAttentionState.Thinking,
                emotionalOverlay = XiaobaohuEmotionalOverlay.Curious,
                boundaryOverlay = XiaobaohuBoundaryOverlay.None,
                mascotState = MascotState.Thinking,
                minHoldMs = XiaobaohuVisualStateResolver.THINKING_MIN_HOLD_MS,
                reason = "thinking",
            ),
            VisualStateCase(
                name = "SpeakingPending",
                phase = ChildTurnUiPhase.SpeakingPending,
                baseAttention = XiaobaohuBaseAttentionState.Speaking,
                emotionalOverlay = XiaobaohuEmotionalOverlay.Warm,
                boundaryOverlay = XiaobaohuBoundaryOverlay.None,
                mascotState = MascotState.Speaking,
                minHoldMs = 0L,
                reason = "speaking_pending",
            ),
            VisualStateCase(
                name = "Speaking",
                phase = ChildTurnUiPhase.Speaking,
                baseAttention = XiaobaohuBaseAttentionState.Speaking,
                emotionalOverlay = XiaobaohuEmotionalOverlay.Warm,
                boundaryOverlay = XiaobaohuBoundaryOverlay.None,
                mascotState = MascotState.Speaking,
                minHoldMs = 0L,
                reason = "speaking",
            ),
            VisualStateCase(
                name = "ImageProcessing",
                phase = ChildTurnUiPhase.ImageProcessing,
                baseAttention = XiaobaohuBaseAttentionState.LookingAtImage,
                emotionalOverlay = XiaobaohuEmotionalOverlay.Curious,
                boundaryOverlay = XiaobaohuBoundaryOverlay.None,
                mascotState = MascotState.ImageViewing,
                minHoldMs = 0L,
                reason = "looking_at_image",
            ),
            VisualStateCase(
                name = "PermissionNeeded",
                phase = ChildTurnUiPhase.PermissionNeeded,
                baseAttention = XiaobaohuBaseAttentionState.Idle,
                emotionalOverlay = XiaobaohuEmotionalOverlay.Concerned,
                boundaryOverlay = XiaobaohuBoundaryOverlay.SafetyConcern,
                mascotState = MascotState.Paused,
                minHoldMs = XiaobaohuVisualStateResolver.SAFETY_CONCERN_MIN_HOLD_MS,
                reason = "permission_needed_uses_safety_concern",
            ),
            VisualStateCase(
                name = "ServiceError",
                phase = ChildTurnUiPhase.ServiceError,
                baseAttention = XiaobaohuBaseAttentionState.Idle,
                emotionalOverlay = XiaobaohuEmotionalOverlay.Concerned,
                boundaryOverlay = XiaobaohuBoundaryOverlay.NetworkError,
                mascotState = MascotState.Retry,
                minHoldMs = XiaobaohuVisualStateResolver.NETWORK_ERROR_MIN_HOLD_MS,
                reason = "service_error_network_error",
            ),
            VisualStateCase(
                name = "Resting",
                phase = ChildTurnUiPhase.Resting,
                baseAttention = XiaobaohuBaseAttentionState.Resting,
                emotionalOverlay = XiaobaohuEmotionalOverlay.Calm,
                boundaryOverlay = XiaobaohuBoundaryOverlay.None,
                mascotState = MascotState.WaitingSoft,
                minHoldMs = XiaobaohuVisualStateResolver.RESTING_MIN_HOLD_MS,
                reason = "resting_uses_calm_asset",
            ),
        )

        cases.forEach { case ->
            val visualState = XiaobaohuVisualStateResolver.resolve(case.phase)

            assertEquals("${case.name} base", case.baseAttention, visualState.baseAttention)
            assertEquals("${case.name} emotional", case.emotionalOverlay, visualState.emotionalOverlay)
            assertEquals("${case.name} boundary", case.boundaryOverlay, visualState.boundaryOverlay)
            assertEquals("${case.name} mascot", case.mascotState, visualState.mascotState)
            assertEquals("${case.name} minHoldMs", case.minHoldMs, visualState.minHoldMs)
            assertEquals("${case.name} reason", case.reason, visualState.reason)
        }
    }

    @Test
    fun backendSignalsResolveToBoundaryOverlaysWithExplicitPrecedence() {
        assertEquals(
            MascotState.Paused,
            XiaobaohuVisualStateResolver.resolve(
                FoxAgentUiState(
                    mood = FoxMood.PrivacyBoundary,
                    motion = FoxMotion.SteadyBoundary,
                ),
            ).mascotState,
        )
        assertEquals(
            MascotState.Thinking,
            XiaobaohuVisualStateResolver.resolve(
                FoxAgentUiState(
                    mood = FoxMood.HomeworkFocus,
                    motion = FoxMotion.HomeworkFocus,
                ),
            ).mascotState,
        )
        assertEquals(
            MascotState.Paused,
            XiaobaohuVisualStateResolver.resolve(
                FoxAgentUiState(
                    mood = FoxMood.SafetyConcern,
                    motion = FoxMotion.ConcernedStill,
                ),
            ).mascotState,
        )

        val networkBeatsSafety = XiaobaohuVisualStateResolver.resolve(
            FoxAgentUiState(
                mood = FoxMood.SafetyConcern,
                motion = FoxMotion.NetworkError,
            ),
        )
        assertEquals(XiaobaohuBoundaryOverlay.NetworkError, networkBeatsSafety.boundaryOverlay)
        assertEquals(MascotState.Retry, networkBeatsSafety.mascotState)
        assertEquals(
            XiaobaohuVisualStateResolver.NETWORK_ERROR_MIN_HOLD_MS,
            networkBeatsSafety.minHoldMs,
        )

        val homeworkBeatsSpeaking = XiaobaohuVisualStateResolver.resolve(
            FoxAgentUiState(
                mood = FoxMood.HomeworkFocus,
                motion = FoxMotion.Speaking,
            ),
        )
        assertEquals(XiaobaohuBoundaryOverlay.HomeworkFocus, homeworkBeatsSpeaking.boundaryOverlay)
        assertEquals(MascotState.Thinking, homeworkBeatsSpeaking.mascotState)
    }

    @Test
    fun precedenceListIncludesAllV2States() {
        assertEquals(
            listOf(
                MascotState.Retry,
                MascotState.Paused,
                MascotState.Listening,
                MascotState.Speaking,
                MascotState.PreparingSpeech,
                MascotState.Thinking,
                MascotState.ImageViewing,
                MascotState.CoCreate,
                MascotState.WaitingSoft,
                MascotState.Idle,
            ),
            XiaobaohuVisualStateResolver.mascotStatePrecedence,
        )
        assertTrue(XiaobaohuVisualStateResolver.mascotStatePrecedence.contains(MascotState.Paused))
        assertTrue(XiaobaohuVisualStateResolver.mascotStatePrecedence.contains(MascotState.CoCreate))
    }

    @Test
    fun encouragingSignalMapsToJumpingHappyState() {
        val encouraging = XiaobaohuVisualStateResolver.resolve(
            FoxAgentUiState(
                mood = FoxMood.Encouraging,
                motion = FoxMotion.CelebrateSmall,
            ),
        )
        assertEquals(XiaobaohuEmotionalOverlay.Encouraging, encouraging.emotionalOverlay)
        assertEquals(MascotState.CoCreate, encouraging.mascotState)
        assertEquals("encouraging_co_create_state", encouraging.reason)
    }

    @Test
    fun sleepySignalMapsToSleepyState() {
        val sleepy = XiaobaohuVisualStateResolver.resolve(
            FoxAgentUiState(
                mood = FoxMood.Sleepy,
                motion = FoxMotion.SleepyBlink,
            ),
        )
        assertEquals(XiaobaohuEmotionalOverlay.Sleepy, sleepy.emotionalOverlay)
        assertEquals(MascotState.Paused, sleepy.mascotState)
        assertEquals("bedtime_paused_state", sleepy.reason)
        assertEquals(XiaobaohuVisualStateResolver.SAFETY_CONCERN_MIN_HOLD_MS, sleepy.minHoldMs)
    }

    @Test
    fun resolverStillExposesAllLayerAxes() {
        assertTrue(XiaobaohuBaseAttentionState.entries.contains(XiaobaohuBaseAttentionState.LookingAtImage))
        assertTrue(XiaobaohuEmotionalOverlay.entries.contains(XiaobaohuEmotionalOverlay.Sleepy))
        assertTrue(XiaobaohuBoundaryOverlay.entries.contains(XiaobaohuBoundaryOverlay.NetworkError))
    }

    private data class VisualStateCase(
        val name: String,
        val phase: ChildTurnUiPhase,
        val baseAttention: XiaobaohuBaseAttentionState,
        val emotionalOverlay: XiaobaohuEmotionalOverlay,
        val boundaryOverlay: XiaobaohuBoundaryOverlay,
        val mascotState: MascotState,
        val minHoldMs: Long,
        val reason: String,
    )
}
