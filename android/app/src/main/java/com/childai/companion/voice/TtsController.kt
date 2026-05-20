package com.childai.companion.voice

data class TtsRequest(
    val text: String,
    val voiceProfile: VoiceProfile = VoiceProfile.default(),
    val audioUrl: String? = null,
    val backendBaseUrl: String? = null,
)

data class VoiceDiagnostics(
    val isAvailable: Boolean = true,
    val isInitializing: Boolean = false,
    val isInitialized: Boolean = false,
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
)

data class VoiceCapabilityReport(
    val isAvailable: Boolean,
    val isInitializing: Boolean,
    val isInitialized: Boolean,
    val enginePackageName: String?,
    val selectedLocale: String?,
    val selectedVoiceName: String?,
    val lastFailureReason: String?,
)

data class TtsCallbacks(
    val onDiagnostics: (VoiceDiagnostics) -> Unit = {},
    val onStart: () -> Unit = {},
    val onDone: () -> Unit = {},
    val onError: (String) -> Unit = {},
)

interface TtsController {
    fun speak(request: TtsRequest, callbacks: TtsCallbacks): Boolean
    fun stop()
    fun shutdown()

    companion object {
        const val UNAVAILABLE_MESSAGE = "我现在不能朗读，但文字还在这里。"
        const val AUDIO_PLAYBACK_UNAVAILABLE_MESSAGE = "这次声音没有放出来，但文字还在这里。"
    }
}

object NoOpTtsController : TtsController {
    override fun speak(request: TtsRequest, callbacks: TtsCallbacks): Boolean {
        callbacks.onDiagnostics(
            VoiceDiagnostics(
                isAvailable = false,
                isInitialized = false,
                lastRequestedTextPreview = request.text.previewForDiagnostics(),
                lastFailureReason = "No TTS controller attached",
                lastSpeakResult = "SKIPPED_NO_CONTROLLER",
            ),
        )
        callbacks.onError(TtsController.UNAVAILABLE_MESSAGE)
        return false
    }

    override fun stop() = Unit

    override fun shutdown() = Unit
}

fun String.previewForDiagnostics(maxLength: Int = 24): String {
    val compact = trim().replace(Regex("\\s+"), " ")
    return if (compact.length <= maxLength) compact else compact.take(maxLength) + "..."
}
