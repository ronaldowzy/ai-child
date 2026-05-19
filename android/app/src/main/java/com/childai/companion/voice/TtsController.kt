package com.childai.companion.voice

data class TtsRequest(
    val text: String,
    val voiceProfile: VoiceProfile = VoiceProfile.default(),
)

data class TtsCallbacks(
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
    }
}

object NoOpTtsController : TtsController {
    override fun speak(request: TtsRequest, callbacks: TtsCallbacks): Boolean {
        callbacks.onError(TtsController.UNAVAILABLE_MESSAGE)
        return false
    }

    override fun stop() = Unit

    override fun shutdown() = Unit
}
