package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.ConversationReply

data class FoxAgentUiState(
    val mood: FoxMood = FoxMood.Warm,
    val motion: FoxMotion = FoxMotion.GentleIdle,
    val statusText: String = "慢慢说，一次说一件事就好。",
)

enum class FoxMood {
    Warm,
    Listening,
    Thinking,
    Encouraging,
    Calm,
}

enum class FoxMotion {
    GentleIdle,
    ListeningTail,
    ThinkingBlink,
    CelebrateSmall,
    CalmStill,
    Speaking,
}

data class VoiceUiState(
    val isVoiceInputReserved: Boolean = true,
    val isTtsAvailable: Boolean = false,
    val audioUrl: String? = null,
) {
    val statusText: String
        get() = when {
            isTtsAvailable -> "朗读稍后接上"
            isVoiceInputReserved -> "现在先用文字说"
            else -> "文字交流"
        }
}

fun ConversationReply.toFoxAgentUiState(): FoxAgentUiState {
    val mood = emotion.toFoxMood()
    val motion = agentMotion.toFoxMotion()
    return FoxAgentUiState(
        mood = mood,
        motion = motion,
        statusText = agentStatusText(mood = mood, motion = motion),
    )
}

fun ConversationReply.toVoiceUiState(): VoiceUiState {
    return VoiceUiState(
        isVoiceInputReserved = true,
        isTtsAvailable = voiceEnabled && !audioUrl.isNullOrBlank(),
        audioUrl = audioUrl,
    )
}

private fun String.toFoxMood(): FoxMood {
    return when (lowercase()) {
        "listening", "curious" -> FoxMood.Listening
        "thinking", "focused" -> FoxMood.Thinking
        "encouraging", "happy", "proud" -> FoxMood.Encouraging
        "calm", "safety", "gentle" -> FoxMood.Calm
        else -> FoxMood.Warm
    }
}

private fun String.toFoxMotion(): FoxMotion {
    return when (lowercase()) {
        "speaking", "talking" -> FoxMotion.Speaking
        "listening_tail", "tail_wag", "gentle_tail" -> FoxMotion.ListeningTail
        "thinking_blink", "blink", "thinking" -> FoxMotion.ThinkingBlink
        "celebrate_small", "small_bounce", "encourage" -> FoxMotion.CelebrateSmall
        "calm_still", "still", "safety_still" -> FoxMotion.CalmStill
        else -> FoxMotion.GentleIdle
    }
}

private fun agentStatusText(mood: FoxMood, motion: FoxMotion): String {
    return when {
        motion == FoxMotion.Speaking -> "我在说给你听。"
        motion == FoxMotion.ThinkingBlink || mood == FoxMood.Thinking -> "我先想一想。"
        motion == FoxMotion.ListeningTail || mood == FoxMood.Listening -> "我在听你说。"
        motion == FoxMotion.CelebrateSmall || mood == FoxMood.Encouraging -> "你刚才说得很清楚。"
        motion == FoxMotion.CalmStill || mood == FoxMood.Calm -> "我们慢一点说。"
        else -> "慢慢说，一次说一件事就好。"
    }
}

fun FoxAgentUiState.asSpeaking(): FoxAgentUiState {
    return copy(
        motion = FoxMotion.Speaking,
        statusText = "我在说给你听。",
    )
}
