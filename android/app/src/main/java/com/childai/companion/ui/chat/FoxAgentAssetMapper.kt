package com.childai.companion.ui.chat

import androidx.annotation.DrawableRes
import com.childai.companion.R
import com.childai.companion.config.DevSettings

sealed interface FoxAgentAsset {
    data class Drawable(@DrawableRes val resId: Int) : FoxAgentAsset
    data object CanvasFallback : FoxAgentAsset
}

object FoxAgentAssetMapper {
    fun resolve(
        agent: FoxAgentUiState,
        assetMode: String = DevSettings.FOX_ASSET_MODE,
    ): FoxAgentAsset {
        if (assetMode.equals("canvas", ignoreCase = true)) {
            return FoxAgentAsset.CanvasFallback
        }

        val drawableId = when {
            agent.motion == FoxMotion.Speaking ->
                R.drawable.fox_3d_speaking

            agent.motion == FoxMotion.HomeworkFocus || agent.mood == FoxMood.HomeworkFocus ->
                R.drawable.fox_3d_homework_focus

            agent.motion == FoxMotion.SleepyBlink || agent.mood == FoxMood.Sleepy ->
                R.drawable.fox_3d_sleepy

            agent.motion == FoxMotion.ConcernedStill || agent.mood == FoxMood.SafetyConcern ->
                R.drawable.fox_3d_safety_concern

            agent.motion == FoxMotion.SteadyBoundary || agent.mood == FoxMood.PrivacyBoundary ->
                R.drawable.fox_3d_privacy_boundary

            agent.motion == FoxMotion.NetworkError || agent.mood == FoxMood.NetworkError ->
                R.drawable.fox_3d_network_error

            agent.motion == FoxMotion.ListeningTail || agent.mood == FoxMood.Listening ->
                R.drawable.fox_3d_listening

            agent.motion == FoxMotion.CelebrateSmall || agent.mood == FoxMood.Encouraging ->
                R.drawable.fox_3d_jumping_happy

            agent.motion == FoxMotion.ThinkingBlink || agent.mood == FoxMood.Thinking ->
                R.drawable.fox_3d_thinking

            agent.motion == FoxMotion.CalmStill || agent.mood == FoxMood.Calm ->
                R.drawable.fox_3d_calm

            else -> R.drawable.fox_3d_neutral_idle
        }

        return FoxAgentAsset.Drawable(drawableId)
    }
}
