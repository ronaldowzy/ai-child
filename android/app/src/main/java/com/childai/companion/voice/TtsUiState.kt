package com.childai.companion.voice

import com.childai.companion.config.DevSettings

data class TtsUiState(
    val isAutoReadEnabled: Boolean = DevSettings.AUTO_TTS_ENABLED,
    val isMuted: Boolean = DevSettings.TTS_MUTED,
    val isInitializing: Boolean = false,
    val isInitialized: Boolean = false,
    val isSpeaking: Boolean = false,
    val isSpeakingPending: Boolean = false,
    val isAvailable: Boolean = true,
    val errorMessage: String? = null,
    val lastRequestedTextPreview: String? = null,
    val lastFailureReason: String? = null,
    val selectedLocale: String? = null,
    val selectedVoiceName: String? = null,
    val setLanguageResult: String? = null,
    val setVoiceResult: String? = null,
    val lastSpeakResult: String? = null,
    val enginePackageName: String? = null,
    val playbackSource: String? = null,
    val audioUrl: String? = null,
) {
    val statusText: String
        get() = when {
            errorMessage != null -> errorMessage
            isSpeaking -> "小白狐正在说话。"
            isSpeakingPending -> "小白狐正在准备朗读。"
            isInitializing -> "小白狐正在准备朗读。"
            isMuted -> "朗读已静音，文字还会显示。"
            !isAutoReadEnabled -> "自动朗读已关闭。"
            isAvailable -> "朗读已开启。"
            else -> TtsController.UNAVAILABLE_MESSAGE
        }

    val needsSystemSetup: Boolean
        get() = !isAvailable ||
            lastSpeakResult == "SKIPPED_UNAVAILABLE" ||
            lastSpeakResult == "SKIPPED_NO_ENGINE" ||
            lastSpeakResult == "SKIPPED_NULL_TTS" ||
            lastSpeakResult == "ERROR" ||
            lastFailureReason?.contains("TextToSpeech", ignoreCase = true) == true ||
            lastFailureReason?.contains("TTS", ignoreCase = true) == true

    val diagnosticText: String
        get() {
            val parts = listOfNotNull(
                enginePackageName?.let { "engine=$it" },
                selectedLocale?.let { "locale=$it" },
                selectedVoiceName?.let { "voice=$it" },
                setLanguageResult?.let { "lang=$it" },
                setVoiceResult?.let { "setVoice=$it" },
                lastSpeakResult?.let { "speak=$it" },
                playbackSource?.let { "source=$it" },
                audioUrl?.let { "audio=$it" },
                lastFailureReason?.let { "failure=$it" },
                lastRequestedTextPreview?.let { "text=$it" },
            )
            return parts.joinToString(" · ")
        }

    fun withDiagnostics(diagnostics: VoiceDiagnostics): TtsUiState {
        return copy(
            isAvailable = diagnostics.isAvailable,
            isInitializing = diagnostics.isInitializing,
            isInitialized = diagnostics.isInitialized,
            lastRequestedTextPreview = diagnostics.lastRequestedTextPreview
                ?: lastRequestedTextPreview,
            lastFailureReason = diagnostics.lastFailureReason,
            selectedLocale = diagnostics.selectedLocale ?: selectedLocale,
            selectedVoiceName = diagnostics.selectedVoiceName,
            setLanguageResult = diagnostics.setLanguageResult ?: setLanguageResult,
            setVoiceResult = diagnostics.setVoiceResult ?: setVoiceResult,
            lastSpeakResult = diagnostics.lastSpeakResult ?: lastSpeakResult,
            enginePackageName = diagnostics.enginePackageName ?: enginePackageName,
            playbackSource = diagnostics.playbackSource ?: playbackSource,
            audioUrl = diagnostics.audioUrl ?: audioUrl,
        )
    }
}
