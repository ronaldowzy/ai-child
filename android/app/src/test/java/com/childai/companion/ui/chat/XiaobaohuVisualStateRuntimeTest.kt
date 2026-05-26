package com.childai.companion.ui.chat

import com.childai.companion.mascot.MascotState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * JVM unit tests for [XiaobaohuVisualStateRuntime] transition throttle.
 *
 * All tests use explicit nowMs — no wall-clock dependency.
 */
class XiaobaohuVisualStateRuntimeTest {

    // --- Test 1: initial requested state displays immediately ---

    @Test
    fun `initial state displays immediately`() {
        val result = XiaobaohuVisualStateRuntime.reduce(
            current = null,
            requested = MascotState.Thinking,
            requestedMinHoldMs = 500L,
            nowMs = 1000L,
        )
        assertEquals(MascotState.Thinking, result.mascotState)
        assertEquals(1000L, result.displaySinceMs)
        assertEquals(500L, result.minHoldMs)
        assertNull(result.pendingState)
    }

    // --- Test 2: thinking holds for at least THINKING_MIN_HOLD_MS ---

    @Test
    fun `thinking holds for min hold before switching to idle`() {
        val current = XiaobaohuDisplayedVisualState(
            mascotState = MascotState.Thinking,
            displaySinceMs = 1000L,
            minHoldMs = 500L,
        )

        // At 1200ms — only 200ms elapsed, hold active
        val tooEarly = XiaobaohuVisualStateRuntime.reduce(
            current = current,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 1200L,
        )
        assertEquals(MascotState.Thinking, tooEarly.mascotState)
        assertEquals(MascotState.Idle, tooEarly.pendingState)

        // At 1500ms — exactly 500ms elapsed, hold expired
        val holdExpired = XiaobaohuVisualStateRuntime.reduce(
            current = current,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 1500L,
        )
        assertEquals(MascotState.Idle, holdExpired.mascotState)
        assertNull(holdExpired.pendingState)
    }

    // --- Test 3: safety_concern holds for at least SAFETY_CONCERN_MIN_HOLD_MS ---

    @Test
    fun `safety concern holds for min hold before returning to idle`() {
        val current = XiaobaohuDisplayedVisualState(
            mascotState = MascotState.SafetyConcern,
            displaySinceMs = 1000L,
            minHoldMs = 1500L,
        )

        // At 2000ms — only 1000ms elapsed, hold active
        val tooEarly = XiaobaohuVisualStateRuntime.reduce(
            current = current,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 2000L,
        )
        assertEquals(MascotState.SafetyConcern, tooEarly.mascotState)
        assertEquals(MascotState.Idle, tooEarly.pendingState)

        // At 2500ms — exactly 1500ms elapsed, hold expired
        val holdExpired = XiaobaohuVisualStateRuntime.reduce(
            current = current,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 2500L,
        )
        assertEquals(MascotState.Idle, holdExpired.mascotState)
    }

    // --- Test 4: privacy_boundary holds for at least PRIVACY_BOUNDARY_MIN_HOLD_MS ---

    @Test
    fun `privacy boundary holds for min hold`() {
        val current = XiaobaohuDisplayedVisualState(
            mascotState = MascotState.PrivacyBoundary,
            displaySinceMs = 1000L,
            minHoldMs = 1200L,
        )

        // At 1800ms — only 800ms elapsed
        val tooEarly = XiaobaohuVisualStateRuntime.reduce(
            current = current,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 1800L,
        )
        assertEquals(MascotState.PrivacyBoundary, tooEarly.mascotState)

        // At 2200ms — 1200ms elapsed, hold expired
        val holdExpired = XiaobaohuVisualStateRuntime.reduce(
            current = current,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 2200L,
        )
        assertEquals(MascotState.Idle, holdExpired.mascotState)
    }

    // --- Test 5: network_error holds for at least NETWORK_ERROR_MIN_HOLD_MS ---

    @Test
    fun `network error holds for min hold`() {
        val current = XiaobaohuDisplayedVisualState(
            mascotState = MascotState.NetworkError,
            displaySinceMs = 1000L,
            minHoldMs = 1200L,
        )

        // At 1500ms — only 500ms elapsed
        val tooEarly = XiaobaohuVisualStateRuntime.reduce(
            current = current,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 1500L,
        )
        assertEquals(MascotState.NetworkError, tooEarly.mascotState)

        // At 2200ms — 1200ms elapsed, hold expired
        val holdExpired = XiaobaohuVisualStateRuntime.reduce(
            current = current,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 2200L,
        )
        assertEquals(MascotState.Idle, holdExpired.mascotState)
    }

    // --- Test 6: speaking can replace thinking promptly ---

    @Test
    fun `speaking interrupts thinking immediately`() {
        val current = XiaobaohuDisplayedVisualState(
            mascotState = MascotState.Thinking,
            displaySinceMs = 1000L,
            minHoldMs = 500L,
        )

        // At 1100ms — only 100ms into thinking hold, but speaking should interrupt
        val result = XiaobaohuVisualStateRuntime.reduce(
            current = current,
            requested = MascotState.Speaking,
            requestedMinHoldMs = 0L,
            nowMs = 1100L,
        )
        assertEquals(MascotState.Speaking, result.mascotState)
        assertNull(result.pendingState)
    }

    // --- Test 7: pending state is applied after hold expires ---

    @Test
    fun `pending state applied after hold expires`() {
        // Simulate: thinking is displayed, idle is requested (stored as pending),
        // then thinking hold expires and next reduce picks up idle
        val thinking = XiaobaohuDisplayedVisualState(
            mascotState = MascotState.Thinking,
            displaySinceMs = 1000L,
            minHoldMs = 500L,
        )

        // At 1200ms — hold active, idle stored as pending
        val withPending = XiaobaohuVisualStateRuntime.reduce(
            current = thinking,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 1200L,
        )
        assertEquals(MascotState.Thinking, withPending.mascotState)
        assertEquals(MascotState.Idle, withPending.pendingState)

        // At 1500ms — hold expired, pending should be applied
        val afterHold = XiaobaohuVisualStateRuntime.reduce(
            current = withPending,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 1500L,
        )
        assertEquals(MascotState.Idle, afterHold.mascotState)
        assertNull(afterHold.pendingState)
    }

    // --- Test 8: jumping_happy is not introduced by the runtime throttle ---

    @Test
    fun `jumping happy is not auto-triggered by throttle`() {
        // jumping_happy has very low precedence and cannot interrupt anything
        val canInterrupt = XiaobaohuVisualStateRuntime.canInterrupt(
            MascotState.Thinking, MascotState.JumpingHappy,
        )
        // JumpingHappy is not in the interrupt precedence list, so rank = MAX_VALUE
        // It should NOT be able to interrupt thinking
        assertEquals(false, canInterrupt)

        // Also verify it's not in the interrupt precedence list at all
        // (by checking it can't interrupt even Idle)
        val canInterruptIdle = XiaobaohuVisualStateRuntime.canInterrupt(
            MascotState.Idle, MascotState.JumpingHappy,
        )
        assertEquals(false, canInterruptIdle)
    }

    // --- Test 9: debug override path remains deterministic ---

    @Test
    fun `debug override bypasses throttle — first call with null current`() {
        // When debug override is active, CartoonAgentView skips the throttle entirely.
        // This test verifies the reduce function itself is deterministic —
        // a null current always displays immediately regardless of state.
        val states = listOf(
            MascotState.Idle,
            MascotState.Thinking,
            MascotState.SafetyConcern,
            MascotState.JumpingHappy,
            MascotState.Sleepy,
        )
        for (state in states) {
            val result = XiaobaohuVisualStateRuntime.reduce(
                current = null,
                requested = state,
                requestedMinHoldMs = 0L,
                nowMs = 5000L,
            )
            assertEquals("Debug override should display $state immediately", state, result.mascotState)
            assertEquals(5000L, result.displaySinceMs)
        }
    }

    // --- Additional: same state refreshes metadata ---

    @Test
    fun `same state refreshes hold metadata and clears pending`() {
        val current = XiaobaohuDisplayedVisualState(
            mascotState = MascotState.Thinking,
            displaySinceMs = 1000L,
            minHoldMs = 500L,
            pendingState = MascotState.Idle,
        )

        val result = XiaobaohuVisualStateRuntime.reduce(
            current = current,
            requested = MascotState.Thinking,
            requestedMinHoldMs = 600L,
            nowMs = 1200L,
        )
        assertEquals(MascotState.Thinking, result.mascotState)
        assertEquals(1000L, result.displaySinceMs) // preserves display time
        assertEquals(600L, result.minHoldMs) // refreshes hold
        assertNull(result.pendingState) // clears pending
    }

    // --- Additional: lower-priority state cannot interrupt ---

    @Test
    fun `idle cannot interrupt thinking hold`() {
        val current = XiaobaohuDisplayedVisualState(
            mascotState = MascotState.Thinking,
            displaySinceMs = 1000L,
            minHoldMs = 500L,
        )

        val result = XiaobaohuVisualStateRuntime.reduce(
            current = current,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 1100L,
        )
        assertEquals(MascotState.Thinking, result.mascotState)
        assertEquals(MascotState.Idle, result.pendingState)
    }

    // --- Additional: listening does NOT interrupt thinking ---

    @Test
    fun `listening cannot interrupt thinking`() {
        // Thinking has higher precedence than Listening in the resolver list.
        // Thinking's 500ms hold prevents Recognizing → Thinking → Speaking flicker.
        // Listening (0ms hold) does not need to interrupt thinking.
        val canInterrupt = XiaobaohuVisualStateRuntime.canInterrupt(
            MascotState.Thinking, MascotState.Listening,
        )
        assertEquals(false, canInterrupt)
    }

    // --- Additional: safety states interrupt each other by precedence ---

    @Test
    fun `network error can interrupt safety concern`() {
        val canInterrupt = XiaobaohuVisualStateRuntime.canInterrupt(
            MascotState.SafetyConcern, MascotState.NetworkError,
        )
        assertEquals(true, canInterrupt)
    }

    @Test
    fun `safety concern can interrupt privacy boundary`() {
        val canInterrupt = XiaobaohuVisualStateRuntime.canInterrupt(
            MascotState.PrivacyBoundary, MascotState.SafetyConcern,
        )
        assertEquals(true, canInterrupt)
    }

    @Test
    fun `thinking cannot interrupt safety concern`() {
        val canInterrupt = XiaobaohuVisualStateRuntime.canInterrupt(
            MascotState.SafetyConcern, MascotState.Thinking,
        )
        assertEquals(false, canInterrupt)
    }

    @Test
    fun `idle cannot interrupt safety concern`() {
        val canInterrupt = XiaobaohuVisualStateRuntime.canInterrupt(
            MascotState.SafetyConcern, MascotState.Idle,
        )
        assertEquals(false, canInterrupt)
    }

    // --- Additional: pending metadata carries minHoldMs for scheduled expiry ---

    @Test
    fun `pending state carries min hold metadata for scheduled expiry`() {
        // Scenario: Thinking is displayed (500ms hold). Speaking arrives at 100ms.
        // Speaking has higher precedence → interrupts immediately.
        // No pending needed.
        val thinking = XiaobaohuDisplayedVisualState(
            mascotState = MascotState.Thinking,
            displaySinceMs = 1000L,
            minHoldMs = 500L,
        )

        // Thinking → Idle at 1200ms (hold active, Idle can't interrupt)
        val withPending = XiaobaohuVisualStateRuntime.reduce(
            current = thinking,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 1200L,
        )
        assertEquals(MascotState.Thinking, withPending.mascotState)
        assertEquals(MascotState.Idle, withPending.pendingState)
        assertEquals(0L, withPending.pendingMinHoldMs)

        // Thinking → Listening at 1200ms (hold active, Listening can't interrupt Thinking)
        val withPendingListening = XiaobaohuVisualStateRuntime.reduce(
            current = thinking,
            requested = MascotState.Listening,
            requestedMinHoldMs = 0L,
            nowMs = 1200L,
        )
        assertEquals(MascotState.Thinking, withPendingListening.mascotState)
        assertEquals(MascotState.Listening, withPendingListening.pendingState)
        assertEquals(0L, withPendingListening.pendingMinHoldMs)

        // SafetyConcern → Idle at 200ms (hold active, 1500ms hold, Idle can't interrupt)
        val safety = XiaobaohuDisplayedVisualState(
            mascotState = MascotState.SafetyConcern,
            displaySinceMs = 1000L,
            minHoldMs = 1500L,
        )
        val safetyPending = XiaobaohuVisualStateRuntime.reduce(
            current = safety,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 1200L,
        )
        assertEquals(MascotState.SafetyConcern, safetyPending.mascotState)
        assertEquals(MascotState.Idle, safetyPending.pendingState)
        assertEquals(0L, safetyPending.pendingMinHoldMs)

        // Same state clears pending metadata
        val sameState = XiaobaohuVisualStateRuntime.reduce(
            current = withPending,
            requested = MascotState.Thinking,
            requestedMinHoldMs = 500L,
            nowMs = 1300L,
        )
        assertEquals(MascotState.Thinking, sameState.mascotState)
        assertNull(sameState.pendingState)
        assertEquals(0L, sameState.pendingMinHoldMs)
    }

    // --- Additional: homework focus holds ---

    @Test
    fun `homework focus holds for min hold`() {
        val current = XiaobaohuDisplayedVisualState(
            mascotState = MascotState.HomeworkFocus,
            displaySinceMs = 1000L,
            minHoldMs = 800L,
        )

        // At 1500ms — only 500ms elapsed
        val tooEarly = XiaobaohuVisualStateRuntime.reduce(
            current = current,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 1500L,
        )
        assertEquals(MascotState.HomeworkFocus, tooEarly.mascotState)

        // At 1800ms — 800ms elapsed
        val holdExpired = XiaobaohuVisualStateRuntime.reduce(
            current = current,
            requested = MascotState.Idle,
            requestedMinHoldMs = 0L,
            nowMs = 1800L,
        )
        assertEquals(MascotState.Idle, holdExpired.mascotState)
    }
}
