package com.childai.companion.mascot

import com.childai.companion.ui.chat.FoxAgentUiState

class MascotController(
    private val manifest: MascotManifest? = null,
) {
    fun stateFor(agent: FoxAgentUiState): MascotState {
        return MascotState.fromAgent(agent)
    }

    fun higherPriority(
        first: MascotState,
        second: MascotState,
    ): MascotState {
        val firstRank = MascotStatePriority.rank(first, manifest)
        val secondRank = MascotStatePriority.rank(second, manifest)
        return if (firstRank <= secondRank) first else second
    }

    fun shouldReplace(
        current: MascotState,
        requested: MascotState,
    ): Boolean {
        return MascotStatePriority.rank(requested, manifest) <=
            MascotStatePriority.rank(current, manifest)
    }

    fun stateAfterCompletion(
        completed: MascotState,
        baseState: MascotState,
    ): MascotState {
        val type = manifest?.states?.get(completed)?.animationType
        return when (type) {
            MascotAnimationType.ShortLoop -> baseState
            else -> completed
        }
    }
}
