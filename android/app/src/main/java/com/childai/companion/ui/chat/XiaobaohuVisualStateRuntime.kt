package com.childai.companion.ui.chat

import com.childai.companion.mascot.MascotState

/**
 * Runtime transition throttle for Xiaobaihu visual state.
 *
 * Prevents mascot state flickering by enforcing minHoldMs from [XiaobaohuVisualStateResolver].
 * Pure function — no framework dependency, deterministic with explicit nowMs.
 *
 * Design goals:
 *  - safety/privacy/network states do not flash away;
 *  - thinking holds briefly to avoid Recognizing → Thinking → Speaking flicker;
 *  - speaking/listening remain responsive to actual audio state;
 *  - jumping_happy and sleepy are not wired into reward/retention paths.
 */
data class XiaobaohuDisplayedVisualState(
    val mascotState: MascotState,
    val displaySinceMs: Long,
    val minHoldMs: Long,
    val pendingState: MascotState? = null,
    val pendingMinHoldMs: Long = 0L,
)

object XiaobaohuVisualStateRuntime {

    /**
     * Precedence for immediate interruption — states that can break an active hold.
     *
     * Sleepy and JumpingHappy are included so that bedtime and encouraging
     * signals from the backend can display their correct mascot states.
     * Sleepy is placed low (quiet state, only interrupts idle).
     * JumpingHappy is placed below Speaking (brief celebration).
     */
    private val INTERRUPT_PRECEDENCE: List<MascotState> = listOf(
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

    private fun precedenceRank(state: MascotState): Int {
        val index = INTERRUPT_PRECEDENCE.indexOf(state)
        return if (index >= 0) index else Int.MAX_VALUE
    }

    /**
     * Pure reducer: given current displayed state, a requested state, and the current
     * timestamp, returns the next displayed state.
     *
     * Rules:
     *  1. No current state → display requested immediately.
     *  2. Same state → keep it, refresh metadata.
     *  3. Hold expired → switch to pending or requested.
     *  4. Hold active + requested has strictly higher precedence → interrupt immediately.
     *  5. Hold active + lower/equal precedence → store as pending, keep current.
     */
    fun reduce(
        current: XiaobaohuDisplayedVisualState?,
        requested: MascotState,
        requestedMinHoldMs: Long,
        nowMs: Long,
    ): XiaobaohuDisplayedVisualState {
        if (current == null) {
            return XiaobaohuDisplayedVisualState(
                mascotState = requested,
                displaySinceMs = nowMs,
                minHoldMs = requestedMinHoldMs,
            )
        }

        // Same state — keep, refresh hold metadata, clear pending
        if (requested == current.mascotState) {
            return current.copy(
                minHoldMs = requestedMinHoldMs,
                pendingState = null,
                pendingMinHoldMs = 0L,
            )
        }

        val elapsed = nowMs - current.displaySinceMs
        val holdExpired = elapsed >= current.minHoldMs

        // Hold expired — switch to pending or requested
        if (holdExpired) {
            return XiaobaohuDisplayedVisualState(
                mascotState = requested,
                displaySinceMs = nowMs,
                minHoldMs = requestedMinHoldMs,
            )
        }

        // Hold active — check if requested can interrupt
        if (canInterrupt(current.mascotState, requested)) {
            return XiaobaohuDisplayedVisualState(
                mascotState = requested,
                displaySinceMs = nowMs,
                minHoldMs = requestedMinHoldMs,
            )
        }

        // Hold active, cannot interrupt — store as pending with its minHoldMs
        return current.copy(
            pendingState = requested,
            pendingMinHoldMs = requestedMinHoldMs,
        )
    }

    /**
     * A requested state can interrupt the current hold if it has strictly higher
     * precedence in the resolver's state ordering.
     *
     * This means:
     *  - network_error can interrupt safety_concern (higher precedence);
     *  - safety_concern can interrupt privacy_boundary;
     *  - speaking can interrupt thinking (audio playback must be responsive);
     *  - thinking CANNOT interrupt safety/privacy/network (those must hold calmly);
     *  - idle CANNOT interrupt thinking (thinking needs its 500ms hold).
     */
    internal fun canInterrupt(current: MascotState, requested: MascotState): Boolean {
        return precedenceRank(requested) < precedenceRank(current)
    }
}
