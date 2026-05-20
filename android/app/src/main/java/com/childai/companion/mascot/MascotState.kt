package com.childai.companion.mascot

import com.childai.companion.ui.chat.FoxAgentUiState
import com.childai.companion.ui.chat.FoxMood
import com.childai.companion.ui.chat.FoxMotion

enum class MascotState(val id: String) {
    Idle("idle"),
    Listening("listening"),
    Thinking("thinking"),
    Speaking("speaking"),
    HomeworkFocus("homework_focus"),
    Calm("calm"),
    Sleepy("sleepy"),
    PrivacyBoundary("privacy_boundary"),
    SafetyConcern("safety_concern"),
    NetworkError("network_error"),
    JumpingHappy("jumping_happy"),
    ;

    companion object {
        fun fromId(id: String?): MascotState {
            return entries.firstOrNull { it.id == id } ?: Idle
        }

        fun fromAgent(agent: FoxAgentUiState): MascotState {
            return when {
                agent.motion == FoxMotion.ConcernedStill ||
                    agent.mood == FoxMood.SafetyConcern -> SafetyConcern

                agent.motion == FoxMotion.SteadyBoundary ||
                    agent.mood == FoxMood.PrivacyBoundary -> PrivacyBoundary

                agent.motion == FoxMotion.NetworkError ||
                    agent.mood == FoxMood.NetworkError -> NetworkError

                agent.motion == FoxMotion.Speaking -> Speaking

                agent.motion == FoxMotion.HomeworkFocus ||
                    agent.mood == FoxMood.HomeworkFocus -> HomeworkFocus

                agent.motion == FoxMotion.SleepyBlink ||
                    agent.mood == FoxMood.Sleepy -> Sleepy

                agent.motion == FoxMotion.ThinkingBlink ||
                    agent.mood == FoxMood.Thinking -> Thinking

                agent.motion == FoxMotion.ListeningTail ||
                    agent.mood == FoxMood.Listening -> Listening

                agent.motion == FoxMotion.CelebrateSmall ||
                    agent.mood == FoxMood.Encouraging -> JumpingHappy

                agent.motion == FoxMotion.CalmStill ||
                    agent.mood == FoxMood.Calm -> Calm

                else -> Idle
            }
        }
    }
}

enum class MascotAnimationType {
    Loop,
    OneShotHold,
    ShortLoop,
    ;

    companion object {
        fun fromRaw(raw: String?): MascotAnimationType {
            return when (raw?.lowercase()) {
                "oneshot_hold" -> OneShotHold
                "short_loop" -> ShortLoop
                else -> Loop
            }
        }
    }
}

object MascotStatePriority {
    val fallbackOrder = listOf(
        MascotState.SafetyConcern,
        MascotState.PrivacyBoundary,
        MascotState.NetworkError,
        MascotState.Speaking,
        MascotState.Thinking,
        MascotState.Listening,
        MascotState.HomeworkFocus,
        MascotState.Calm,
        MascotState.Sleepy,
        MascotState.JumpingHappy,
        MascotState.Idle,
    )

    fun rank(state: MascotState, manifest: MascotManifest? = null): Int {
        val source = manifest?.statePriority?.takeIf { it.isNotEmpty() } ?: fallbackOrder
        val index = source.indexOf(state)
        return if (index >= 0) index else Int.MAX_VALUE
    }
}
