package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.ConversationReply
import java.io.File

data class FoxAgentUiState(
    val mood: FoxMood = FoxMood.Warm,
    val motion: FoxMotion = FoxMotion.GentleIdle,
    val statusText: String = "慢慢说就好",
)

enum class FoxMood {
    Warm,
    Listening,
    Thinking,
    Encouraging,
    Calm,
    Sleepy,
    SafetyConcern,
    PrivacyBoundary,
    HomeworkFocus,
    NetworkError,
}

enum class FoxMotion {
    GentleIdle,
    ListeningTail,
    ThinkingBlink,
    CelebrateSmall,
    CalmStill,
    Speaking,
    SleepyBlink,
    ConcernedStill,
    SteadyBoundary,
    HomeworkFocus,
    NetworkError,
}

data class VoiceUiState(
    val isVoiceInputReserved: Boolean = true,
    val isTtsAvailable: Boolean = false,
    val audioUrl: String? = null,
    val inputMode: VoiceInputMode = VoiceInputMode.Idle,
    val pendingTranscript: String = "",
    val errorMessage: String? = null,
    val actions: VoiceInputActions = VoiceInputActions(),
) {
    val hasPendingTranscript: Boolean
        get() = inputMode == VoiceInputMode.PendingTranscript

    val isRecording: Boolean
        get() = inputMode == VoiceInputMode.Listening

    val isUploading: Boolean
        get() = inputMode == VoiceInputMode.Uploading

    val statusText: String
        get() = when {
            errorMessage != null -> errorMessage
            inputMode == VoiceInputMode.Listening -> "我在听"
            inputMode == VoiceInputMode.WaitingForChild -> "想说再说"
            inputMode == VoiceInputMode.Uploading -> "我在想你刚才说的话"
            inputMode == VoiceInputMode.PendingTranscript -> "可以改一下再发"
            inputMode == VoiceInputMode.NeedsRetry -> "刚才没听清，可以再说一遍"
            inputMode == VoiceInputMode.PermissionDenied -> "还不能用麦克风，请家长帮忙打开"
            isTtsAvailable -> "声音马上来"
            isVoiceInputReserved -> "按一下开始说"
            else -> "打字也可以"
        }
}

enum class VoiceInputMode {
    Idle,
    Listening,
    WaitingForChild,
    Uploading,
    PendingTranscript,
    NeedsRetry,
    PermissionDenied,
    Failed,
}

data class VoiceInputActions(
    val onStartRecording: (File) -> Unit = {},
    val onStopRecordingAndUpload: () -> Unit = {},
    val onPermissionDenied: () -> Unit = {},
    val onPendingTranscriptChange: (String) -> Unit = {},
    val onSendPendingTranscript: () -> Unit = {},
    val onCancelVoiceInput: () -> Unit = {},
)

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

fun VoiceUiState.withReplyVoice(reply: ConversationReply): VoiceUiState {
    return copy(
        isVoiceInputReserved = true,
        isTtsAvailable = reply.voiceEnabled && !reply.audioUrl.isNullOrBlank(),
        audioUrl = reply.audioUrl,
    )
}

private fun String.toFoxMood(): FoxMood {
    return when (lowercase()) {
        "listening", "curious" -> FoxMood.Listening
        "thinking", "focused" -> FoxMood.Thinking
        "encouraging", "happy", "proud" -> FoxMood.Encouraging
        "calm", "safety", "gentle" -> FoxMood.Calm
        "sleepy", "bedtime" -> FoxMood.Sleepy
        "safety_concern", "concerned" -> FoxMood.SafetyConcern
        "privacy", "privacy_boundary", "steady" -> FoxMood.PrivacyBoundary
        "homework", "homework_focus" -> FoxMood.HomeworkFocus
        "network_error" -> FoxMood.NetworkError
        else -> FoxMood.Warm
    }
}

private fun String.toFoxMotion(): FoxMotion {
    return when (lowercase()) {
        "speaking", "talking" -> FoxMotion.Speaking
        "listening_tail", "tail_wag", "gentle_tail" -> FoxMotion.ListeningTail
        "thinking_blink", "blink", "thinking" -> FoxMotion.ThinkingBlink
        "thinking_nod", "homework_focus" -> FoxMotion.HomeworkFocus
        "celebrate_small", "small_bounce", "encourage" -> FoxMotion.CelebrateSmall
        "calm_still", "still", "safety_still", "calm_breathe" -> FoxMotion.CalmStill
        "sleepy_blink" -> FoxMotion.SleepyBlink
        "concerned_still" -> FoxMotion.ConcernedStill
        "steady_boundary" -> FoxMotion.SteadyBoundary
        "network_error" -> FoxMotion.NetworkError
        else -> FoxMotion.GentleIdle
    }
}

private fun agentStatusText(mood: FoxMood, motion: FoxMotion): String {
    return when {
        motion == FoxMotion.Speaking -> ""
        motion == FoxMotion.HomeworkFocus || mood == FoxMood.HomeworkFocus -> "我们一步一步看"
        motion == FoxMotion.SleepyBlink || mood == FoxMood.Sleepy -> "我们慢慢收个尾"
        motion == FoxMotion.ConcernedStill || mood == FoxMood.SafetyConcern -> "这件事要告诉家长或老师"
        motion == FoxMotion.SteadyBoundary || mood == FoxMood.PrivacyBoundary -> "这些信息先别说出来"
        motion == FoxMotion.NetworkError || mood == FoxMood.NetworkError -> "这张图还没看到"
        motion == FoxMotion.ThinkingBlink || mood == FoxMood.Thinking -> "我想想"
        motion == FoxMotion.ListeningTail || mood == FoxMood.Listening -> "我在听"
        motion == FoxMotion.CelebrateSmall || mood == FoxMood.Encouraging -> "我听清楚啦"
        motion == FoxMotion.CalmStill || mood == FoxMood.Calm -> "我们慢慢说"
        else -> "慢慢说就好"
    }
}

fun FoxAgentUiState.asSpeaking(): FoxAgentUiState {
    return copy(
        motion = FoxMotion.Speaking,
        statusText = "",
    )
}

fun FoxAgentUiState.asSpeakingPending(): FoxAgentUiState {
    return copy(
        motion = FoxMotion.Speaking,
        statusText = "我准备说",
    )
}
