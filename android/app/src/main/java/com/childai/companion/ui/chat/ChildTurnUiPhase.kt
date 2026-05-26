package com.childai.companion.ui.chat

import com.childai.companion.voice.TtsUiState

enum class ChildTurnUiPhase {
    Ready,
    Listening,
    Recognizing,
    Sending,
    Thinking,
    SpeakingPending,
    Speaking,
    ImageProcessing,
    NeedsRetry,
    PermissionNeeded,
    Resting,
    ServiceError,
}

data class ChildInteractionPresentation(
    val phase: ChildTurnUiPhase,
    val primaryButtonText: String,
    val primaryButtonEnabled: Boolean,
    val showStopSpeaking: Boolean,
    val showMuteToggle: Boolean,
    val showImageInput: Boolean,
    val statusText: String,
    val agent: FoxAgentUiState,
)

internal fun childInteractionPresentation(
    voice: VoiceUiState = VoiceUiState(),
    tts: TtsUiState = TtsUiState(),
    isSending: Boolean = false,
    phaseHint: ChildTurnUiPhase? = null,
    fallbackAgent: FoxAgentUiState = FoxAgentUiState(),
): ChildInteractionPresentation {
    val phase = childTurnUiPhase(
        voice = voice,
        tts = tts,
        isSending = isSending,
        phaseHint = phaseHint,
        fallbackAgent = fallbackAgent,
    )
    return ChildInteractionPresentation(
        phase = phase,
        primaryButtonText = phase.primaryButtonText(),
        primaryButtonEnabled = phase.primaryButtonEnabled(),
        showStopSpeaking = phase == ChildTurnUiPhase.SpeakingPending ||
            phase == ChildTurnUiPhase.Speaking,
        showMuteToggle = phase == ChildTurnUiPhase.SpeakingPending ||
            phase == ChildTurnUiPhase.Speaking,
        showImageInput = phase in setOf(
            ChildTurnUiPhase.Ready,
            ChildTurnUiPhase.NeedsRetry,
            ChildTurnUiPhase.PermissionNeeded,
            ChildTurnUiPhase.Resting,
            ChildTurnUiPhase.ServiceError,
        ),
        statusText = phase.statusText(),
        agent = phase.agentFor(fallbackAgent),
    )
}

internal fun childTurnUiPhase(
    voice: VoiceUiState,
    tts: TtsUiState,
    isSending: Boolean,
    phaseHint: ChildTurnUiPhase?,
    fallbackAgent: FoxAgentUiState,
): ChildTurnUiPhase {
    return when {
        voice.inputMode == VoiceInputMode.PermissionDenied -> ChildTurnUiPhase.PermissionNeeded
        voice.inputMode == VoiceInputMode.Listening -> ChildTurnUiPhase.Listening
        voice.inputMode == VoiceInputMode.Uploading -> ChildTurnUiPhase.Recognizing
        voice.inputMode == VoiceInputMode.NeedsRetry -> ChildTurnUiPhase.NeedsRetry
        tts.isSpeaking -> ChildTurnUiPhase.Speaking
        tts.isSpeakingPending -> ChildTurnUiPhase.SpeakingPending
        phaseHint != null -> phaseHint
        voice.inputMode == VoiceInputMode.Failed -> ChildTurnUiPhase.ServiceError
        fallbackAgent.mood == FoxMood.NetworkError ||
            fallbackAgent.motion == FoxMotion.NetworkError -> ChildTurnUiPhase.ServiceError
        isSending -> ChildTurnUiPhase.Thinking
        else -> ChildTurnUiPhase.Ready
    }
}

private fun ChildTurnUiPhase.statusText(): String {
    return when (this) {
        ChildTurnUiPhase.Ready -> "我准备好听你说。"
        ChildTurnUiPhase.Listening -> "我在听你说。"
        ChildTurnUiPhase.Recognizing -> "我在听懂刚才的话。"
        ChildTurnUiPhase.Sending -> "我先想一想。"
        ChildTurnUiPhase.Thinking -> "我先想一想。"
        ChildTurnUiPhase.SpeakingPending -> "我马上说给你听。"
        ChildTurnUiPhase.Speaking -> "我在说给你听。"
        ChildTurnUiPhase.ImageProcessing -> "我在看这张图片。"
        ChildTurnUiPhase.NeedsRetry -> "我刚才没听清，可以再说一次。"
        ChildTurnUiPhase.PermissionNeeded -> "需要大人帮忙打开麦克风。"
        ChildTurnUiPhase.Resting -> "我们可以先歇一小会儿。"
        ChildTurnUiPhase.ServiceError -> "我们先请大人检查一下。"
    }
}

private fun ChildTurnUiPhase.primaryButtonText(): String {
    return when (this) {
        ChildTurnUiPhase.Listening -> "说完了"
        ChildTurnUiPhase.Recognizing -> "正在听懂"
        ChildTurnUiPhase.NeedsRetry -> "再说一次"
        ChildTurnUiPhase.PermissionNeeded -> "请大人帮忙看看"
        ChildTurnUiPhase.ServiceError -> "按一下开始说"
        ChildTurnUiPhase.Sending,
        ChildTurnUiPhase.Thinking,
        ChildTurnUiPhase.ImageProcessing -> "等一下"
        ChildTurnUiPhase.SpeakingPending,
        ChildTurnUiPhase.Speaking -> "小白狐在说"
        ChildTurnUiPhase.Ready,
        ChildTurnUiPhase.Resting -> "按一下开始说"
    }
}

private fun ChildTurnUiPhase.primaryButtonEnabled(): Boolean {
    return when (this) {
        ChildTurnUiPhase.Recognizing,
        ChildTurnUiPhase.Sending,
        ChildTurnUiPhase.Thinking,
        ChildTurnUiPhase.SpeakingPending,
        ChildTurnUiPhase.Speaking,
        ChildTurnUiPhase.ImageProcessing -> false
        ChildTurnUiPhase.Ready,
        ChildTurnUiPhase.Listening,
        ChildTurnUiPhase.NeedsRetry,
        ChildTurnUiPhase.PermissionNeeded,
        ChildTurnUiPhase.Resting,
        ChildTurnUiPhase.ServiceError -> true
    }
}

private fun ChildTurnUiPhase.agentFor(fallbackAgent: FoxAgentUiState): FoxAgentUiState {
    val status = statusText()
    return when (this) {
        ChildTurnUiPhase.Ready -> fallbackAgent.copy(statusText = status)
        ChildTurnUiPhase.Listening,
        ChildTurnUiPhase.NeedsRetry -> FoxAgentUiState(
            mood = FoxMood.Listening,
            motion = FoxMotion.ListeningTail,
            statusText = status,
        )
        ChildTurnUiPhase.Recognizing,
        ChildTurnUiPhase.Sending,
        ChildTurnUiPhase.Thinking,
        ChildTurnUiPhase.ImageProcessing -> FoxAgentUiState(
            mood = FoxMood.Thinking,
            motion = FoxMotion.ThinkingBlink,
            statusText = status,
        )
        ChildTurnUiPhase.SpeakingPending,
        ChildTurnUiPhase.Speaking -> fallbackAgent.copy(
            motion = FoxMotion.Speaking,
            statusText = status,
        )
        ChildTurnUiPhase.PermissionNeeded -> FoxAgentUiState(
            mood = FoxMood.SafetyConcern,
            motion = FoxMotion.ConcernedStill,
            statusText = status,
        )
        ChildTurnUiPhase.Resting -> FoxAgentUiState(
            mood = FoxMood.Calm,
            motion = FoxMotion.CalmStill,
            statusText = status,
        )
        ChildTurnUiPhase.ServiceError -> FoxAgentUiState(
            mood = FoxMood.NetworkError,
            motion = FoxMotion.NetworkError,
            statusText = status,
        )
    }
}
