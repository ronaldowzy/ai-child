package com.childai.companion.ui.chat

import com.childai.companion.mascot.MascotState

/**
 * Product-facing visual state layer for Xiaobaihu.
 *
 * This resolver intentionally keeps the runtime asset target small and explicit:
 * base attention + emotional overlay + boundary overlay -> MascotState.
 *
 * It does not create new assets and it does not make every backend scene a new animation.
 */
data class XiaobaohuVisualState(
    val baseAttention: XiaobaohuBaseAttentionState,
    val emotionalOverlay: XiaobaohuEmotionalOverlay,
    val boundaryOverlay: XiaobaohuBoundaryOverlay,
    val mascotState: MascotState,
    val minHoldMs: Long,
    val reason: String,
)

enum class XiaobaohuBaseAttentionState {
    Idle,
    Listening,
    Thinking,
    Speaking,
    LookingAtImage,
    Resting,
}

enum class XiaobaohuEmotionalOverlay {
    Warm,
    Curious,
    Encouraging,
    Calm,
    Concerned,
    Sleepy,
}

enum class XiaobaohuBoundaryOverlay {
    None,
    PrivacyBoundary,
    SafetyConcern,
    NetworkError,
    HomeworkFocus,
}

object XiaobaohuVisualStateResolver {
    const val NETWORK_ERROR_MIN_HOLD_MS = 1_200L
    const val SAFETY_CONCERN_MIN_HOLD_MS = 1_500L
    const val PRIVACY_BOUNDARY_MIN_HOLD_MS = 1_200L
    const val HOMEWORK_FOCUS_MIN_HOLD_MS = 800L
    const val THINKING_MIN_HOLD_MS = 500L
    const val RESTING_MIN_HOLD_MS = 600L

    /**
     * Precedence for states that are safe to auto-resolve from current Android interaction.
     *
     * Sleepy and JumpingHappy are now included so bedtime and encouraging backend
     * signals display their correct mascot states. They remain bounded:
     *  - JumpingHappy is a ShortLoop that auto-returns to Idle after 2 loops.
     *  - Sleepy uses a minHold to prevent flicker, then transitions calmly.
     * Neither is wired into reward, streak, or retention paths.
     */
    val mascotStatePrecedence: List<MascotState> = listOf(
        MascotState.NetworkError,
        MascotState.SafetyConcern,
        MascotState.PrivacyBoundary,
        MascotState.HomeworkFocus,
        MascotState.Speaking,
        MascotState.JumpingHappy,
        MascotState.Thinking,
        MascotState.Listening,
        MascotState.Calm,
        MascotState.Sleepy,
        MascotState.Idle,
    )

    fun resolve(
        phase: ChildTurnUiPhase,
        fallbackAgent: FoxAgentUiState = FoxAgentUiState(),
    ): XiaobaohuVisualState {
        val presentation = childInteractionPresentation(
            phaseHint = phase,
            fallbackAgent = fallbackAgent,
        )
        return resolve(
            baseAttention = phase.toBaseAttentionState(),
            agent = presentation.agent,
            reason = phase.toReason(),
        )
    }

    fun resolve(
        agent: FoxAgentUiState,
        reason: String = "agent_signal",
    ): XiaobaohuVisualState {
        return resolve(
            baseAttention = agent.inferBaseAttentionState(),
            agent = agent,
            reason = reason,
        )
    }

    fun resolve(
        baseAttention: XiaobaohuBaseAttentionState,
        agent: FoxAgentUiState,
        reason: String,
    ): XiaobaohuVisualState {
        val boundaryOverlay = agent.toBoundaryOverlay()
        val emotionalOverlay = agent.toEmotionalOverlay(boundaryOverlay)
        val mascotState = resolveMascotState(
            baseAttention = baseAttention,
            emotionalOverlay = emotionalOverlay,
            boundaryOverlay = boundaryOverlay,
        )
        val finalReason = resolveReason(
            baseAttention = baseAttention,
            emotionalOverlay = emotionalOverlay,
            mascotState = mascotState,
            requestedReason = reason,
        )
        return XiaobaohuVisualState(
            baseAttention = baseAttention,
            emotionalOverlay = emotionalOverlay,
            boundaryOverlay = boundaryOverlay,
            mascotState = mascotState,
            minHoldMs = mascotState.minHoldMs(baseAttention),
            reason = finalReason,
        )
    }

    private fun resolveMascotState(
        baseAttention: XiaobaohuBaseAttentionState,
        emotionalOverlay: XiaobaohuEmotionalOverlay,
        boundaryOverlay: XiaobaohuBoundaryOverlay,
    ): MascotState {
        return when (boundaryOverlay) {
            XiaobaohuBoundaryOverlay.NetworkError -> MascotState.NetworkError
            XiaobaohuBoundaryOverlay.SafetyConcern -> MascotState.SafetyConcern
            XiaobaohuBoundaryOverlay.PrivacyBoundary -> MascotState.PrivacyBoundary
            XiaobaohuBoundaryOverlay.HomeworkFocus -> MascotState.HomeworkFocus
            XiaobaohuBoundaryOverlay.None -> when (baseAttention) {
                XiaobaohuBaseAttentionState.Speaking -> MascotState.Speaking
                XiaobaohuBaseAttentionState.Thinking,
                XiaobaohuBaseAttentionState.LookingAtImage -> MascotState.Thinking
                XiaobaohuBaseAttentionState.Listening -> MascotState.Listening
                XiaobaohuBaseAttentionState.Resting -> MascotState.Calm
                XiaobaohuBaseAttentionState.Idle -> when (emotionalOverlay) {
                    XiaobaohuEmotionalOverlay.Sleepy -> MascotState.Sleepy
                    XiaobaohuEmotionalOverlay.Encouraging -> MascotState.JumpingHappy
                    XiaobaohuEmotionalOverlay.Calm -> MascotState.Calm
                    else -> MascotState.Idle
                }
            }
        }
    }

    private fun resolveReason(
        baseAttention: XiaobaohuBaseAttentionState,
        emotionalOverlay: XiaobaohuEmotionalOverlay,
        mascotState: MascotState,
        requestedReason: String,
    ): String {
        return when {
            baseAttention == XiaobaohuBaseAttentionState.LookingAtImage &&
                mascotState == MascotState.Thinking -> "looking_at_image_uses_thinking_asset"
            emotionalOverlay == XiaobaohuEmotionalOverlay.Sleepy &&
                mascotState == MascotState.Sleepy -> "bedtime_sleepy_state"
            emotionalOverlay == XiaobaohuEmotionalOverlay.Encouraging &&
                mascotState == MascotState.JumpingHappy -> "encouraging_happy_state"
            else -> requestedReason
        }
    }

    private fun MascotState.minHoldMs(baseAttention: XiaobaohuBaseAttentionState): Long {
        return when (this) {
            MascotState.NetworkError -> NETWORK_ERROR_MIN_HOLD_MS
            MascotState.SafetyConcern -> SAFETY_CONCERN_MIN_HOLD_MS
            MascotState.PrivacyBoundary -> PRIVACY_BOUNDARY_MIN_HOLD_MS
            MascotState.HomeworkFocus -> HOMEWORK_FOCUS_MIN_HOLD_MS
            MascotState.Thinking -> THINKING_MIN_HOLD_MS
            MascotState.Calm -> if (baseAttention == XiaobaohuBaseAttentionState.Resting) {
                RESTING_MIN_HOLD_MS
            } else {
                0L
            }
            MascotState.Sleepy -> RESTING_MIN_HOLD_MS
            MascotState.Speaking,
            MascotState.Listening,
            MascotState.Idle,
            MascotState.JumpingHappy -> 0L
        }
    }

    private fun ChildTurnUiPhase.toBaseAttentionState(): XiaobaohuBaseAttentionState {
        return when (this) {
            ChildTurnUiPhase.Ready -> XiaobaohuBaseAttentionState.Idle
            ChildTurnUiPhase.Listening,
            ChildTurnUiPhase.WaitingChild,
            ChildTurnUiPhase.NeedsRetry -> XiaobaohuBaseAttentionState.Listening
            ChildTurnUiPhase.Recognizing,
            ChildTurnUiPhase.Sending,
            ChildTurnUiPhase.Thinking -> XiaobaohuBaseAttentionState.Thinking
            ChildTurnUiPhase.SpeakingPending,
            ChildTurnUiPhase.Speaking -> XiaobaohuBaseAttentionState.Speaking
            ChildTurnUiPhase.ImageProcessing -> XiaobaohuBaseAttentionState.LookingAtImage
            ChildTurnUiPhase.PermissionNeeded -> XiaobaohuBaseAttentionState.Idle
            ChildTurnUiPhase.Resting -> XiaobaohuBaseAttentionState.Resting
            ChildTurnUiPhase.ServiceError -> XiaobaohuBaseAttentionState.Idle
        }
    }

    private fun ChildTurnUiPhase.toReason(): String {
        return when (this) {
            ChildTurnUiPhase.Ready -> "ready_idle"
            ChildTurnUiPhase.Listening -> "voice_listening"
            ChildTurnUiPhase.WaitingChild -> "waiting_child"
            ChildTurnUiPhase.Recognizing -> "recognizing_uses_thinking_asset"
            ChildTurnUiPhase.Sending -> "sending_uses_thinking_asset"
            ChildTurnUiPhase.Thinking -> "thinking"
            ChildTurnUiPhase.SpeakingPending -> "speaking_pending"
            ChildTurnUiPhase.Speaking -> "speaking"
            ChildTurnUiPhase.ImageProcessing -> "looking_at_image_uses_thinking_asset"
            ChildTurnUiPhase.NeedsRetry -> "needs_retry_uses_listening_asset"
            ChildTurnUiPhase.PermissionNeeded -> "permission_needed_uses_safety_concern"
            ChildTurnUiPhase.Resting -> "resting_uses_calm_asset"
            ChildTurnUiPhase.ServiceError -> "service_error_network_error"
        }
    }

    private fun FoxAgentUiState.inferBaseAttentionState(): XiaobaohuBaseAttentionState {
        return when {
            motion == FoxMotion.Speaking -> XiaobaohuBaseAttentionState.Speaking
            motion == FoxMotion.ThinkingBlink || mood == FoxMood.Thinking ->
                XiaobaohuBaseAttentionState.Thinking
            motion == FoxMotion.ListeningTail || mood == FoxMood.Listening ->
                XiaobaohuBaseAttentionState.Listening
            motion == FoxMotion.CalmStill || mood == FoxMood.Calm ->
                XiaobaohuBaseAttentionState.Resting
            else -> XiaobaohuBaseAttentionState.Idle
        }
    }

    private fun FoxAgentUiState.toBoundaryOverlay(): XiaobaohuBoundaryOverlay {
        return when {
            motion == FoxMotion.NetworkError || mood == FoxMood.NetworkError ->
                XiaobaohuBoundaryOverlay.NetworkError
            motion == FoxMotion.ConcernedStill || mood == FoxMood.SafetyConcern ->
                XiaobaohuBoundaryOverlay.SafetyConcern
            motion == FoxMotion.SteadyBoundary || mood == FoxMood.PrivacyBoundary ->
                XiaobaohuBoundaryOverlay.PrivacyBoundary
            motion == FoxMotion.HomeworkFocus || mood == FoxMood.HomeworkFocus ->
                XiaobaohuBoundaryOverlay.HomeworkFocus
            else -> XiaobaohuBoundaryOverlay.None
        }
    }

    private fun FoxAgentUiState.toEmotionalOverlay(
        boundaryOverlay: XiaobaohuBoundaryOverlay,
    ): XiaobaohuEmotionalOverlay {
        if (boundaryOverlay != XiaobaohuBoundaryOverlay.None) {
            return XiaobaohuEmotionalOverlay.Concerned
        }
        return when {
            motion == FoxMotion.SleepyBlink || mood == FoxMood.Sleepy ->
                XiaobaohuEmotionalOverlay.Sleepy
            motion == FoxMotion.CalmStill || mood == FoxMood.Calm ->
                XiaobaohuEmotionalOverlay.Calm
            motion == FoxMotion.CelebrateSmall || mood == FoxMood.Encouraging ->
                XiaobaohuEmotionalOverlay.Encouraging
            motion == FoxMotion.ThinkingBlink || mood == FoxMood.Thinking ->
                XiaobaohuEmotionalOverlay.Curious
            else -> XiaobaohuEmotionalOverlay.Warm
        }
    }
}
