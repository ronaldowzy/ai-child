package com.childai.companion.voice

data class AudioSegment(
    val audioUrl: String?,
    val text: String,
    val index: Int,
)

data class AudioSegmentQueueCallbacks(
    val onStart: (AudioSegment) -> Unit = {},
    val onDone: (AudioSegment) -> Unit = {},
    val onQueueDrained: () -> Unit = {},
    val onDiagnostics: (VoiceDiagnostics) -> Unit = {},
    val onError: (String) -> Unit = {},
)

class AudioSegmentQueuePlayer(
    private var ttsController: TtsController,
    private val backendBaseUrl: String,
    private val isMuted: () -> Boolean,
    private val callbacks: AudioSegmentQueueCallbacks,
) {
    private val queue = ArrayDeque<AudioSegment>()
    private var currentSegment: AudioSegment? = null

    val queuedCount: Int
        get() = queue.size + if (currentSegment == null) 0 else 1

    fun updateController(controller: TtsController) {
        ttsController = controller
    }

    fun enqueue(segment: AudioSegment) {
        if (isMuted()) return
        queue.addLast(segment)
        if (currentSegment == null) {
            playNext()
        }
    }

    fun stopAndClear() {
        queue.clear()
        currentSegment = null
        ttsController.stop()
    }

    private fun playNext() {
        if (currentSegment != null) return
        if (isMuted()) {
            queue.clear()
            callbacks.onQueueDrained()
            return
        }

        val next = queue.removeFirstOrNull()
        if (next == null) {
            callbacks.onQueueDrained()
            return
        }
        currentSegment = next

        val accepted = ttsController.speak(
            request = TtsRequest(
                text = next.text,
                audioUrl = next.audioUrl,
                backendBaseUrl = backendBaseUrl,
                voiceProfile = VoiceProfile.default(),
            ),
            callbacks = TtsCallbacks(
                onDiagnostics = callbacks.onDiagnostics,
                onStart = {
                    callbacks.onStart(next)
                },
                onDone = {
                    callbacks.onDone(next)
                    currentSegment = null
                    playNext()
                },
                onError = { message ->
                    callbacks.onError(message)
                    currentSegment = null
                    playNext()
                },
            ),
        )

        if (!accepted) {
            callbacks.onError(TtsController.AUDIO_PLAYBACK_UNAVAILABLE_MESSAGE)
            currentSegment = null
            playNext()
        }
    }
}
