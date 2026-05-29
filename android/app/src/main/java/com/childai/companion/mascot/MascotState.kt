package com.childai.companion.mascot

import com.childai.companion.ui.chat.FoxAgentUiState
import com.childai.companion.ui.chat.FoxMood
import com.childai.companion.ui.chat.FoxMotion

enum class MascotState(val id: String) {
    Idle("idle"),
    Listening("listening"),
    Thinking("thinking"),
    Speaking("speaking"),
    WaitingSoft("waiting_soft"),
    PreparingSpeech("preparing_speech"),
    ImageViewing("image_viewing"),
    CoCreate("co_create"),
    Paused("paused"),
    Retry("retry"),
    ;

    companion object {
        fun fromId(id: String?): MascotState {
            return entries.firstOrNull { it.id == id } ?: Idle
        }

        fun fromAgent(agent: FoxAgentUiState): MascotState {
            return when {
                agent.motion == FoxMotion.NetworkError ||
                    agent.mood == FoxMood.NetworkError -> Retry

                agent.motion == FoxMotion.ConcernedStill ||
                    agent.mood == FoxMood.SafetyConcern -> Paused

                agent.motion == FoxMotion.SteadyBoundary ||
                    agent.mood == FoxMood.PrivacyBoundary -> Paused

                agent.motion == FoxMotion.Speaking -> Speaking

                agent.motion == FoxMotion.HomeworkFocus ||
                    agent.mood == FoxMood.HomeworkFocus -> Thinking

                agent.motion == FoxMotion.SleepyBlink ||
                    agent.mood == FoxMood.Sleepy -> Paused

                agent.motion == FoxMotion.ThinkingBlink ||
                    agent.mood == FoxMood.Thinking -> Thinking

                agent.motion == FoxMotion.ListeningTail ||
                    agent.mood == FoxMood.Listening -> Listening

                agent.motion == FoxMotion.CelebrateSmall ||
                    agent.mood == FoxMood.Encouraging -> CoCreate

                agent.motion == FoxMotion.CalmStill ||
                    agent.mood == FoxMood.Calm -> Idle

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
    )

    fun rank(state: MascotState, manifest: MascotManifest? = null): Int {
        val source = manifest?.statePriority?.takeIf { it.isNotEmpty() } ?: fallbackOrder
        val index = source.indexOf(state)
        return if (index >= 0) index else Int.MAX_VALUE
    }
}
