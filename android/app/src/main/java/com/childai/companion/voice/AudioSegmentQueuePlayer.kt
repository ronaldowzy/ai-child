package com.childai.companion.voice

import android.util.Log

private const val QUEUE_TAG = "AudioSegQueue"

data class AudioSegment(
    val audioUrl: String?,
    val text: String,
    val index: Int,
    val requestId: String? = null,
    val turnId: String? = null,
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
        if (isMuted()) {
            logQueue("enqueue_skip_muted index=${segment.index} textLen=${segment.text.length}")
            return
        }
        queue.addLast(segment)
        logQueue("enqueue index=${segment.index} queued=${queue.size} textLen=${segment.text.length}")
        if (currentSegment == null) {
            playNext()
        }
    }

    fun stopAndClear() {
        val clearedCount = queue.size
        queue.clear()
        currentSegment = null
        ttsController.stop()
        logQueue("stopAndClear cleared=$clearedCount")
    }

    private fun playNext() {
        if (currentSegment != null) return
        if (isMuted()) {
            val droppedCount = queue.size
            queue.clear()
            logQueue("playNext_skip_muted dropped=$droppedCount")
            callbacks.onQueueDrained()
            return
        }

        val next = queue.removeFirstOrNull()
        if (next == null) {
            logQueue("playNext_drained")
            callbacks.onQueueDrained()
            return
        }
        currentSegment = next
        logQueue("playNext_start index=${next.index} remaining=${queue.size} textLen=${next.text.length}")

        val accepted = ttsController.speak(
            request = TtsRequest(
                text = next.text,
                audioUrl = next.audioUrl,
                backendBaseUrl = backendBaseUrl,
                voiceProfile = VoiceProfile.default(),
                requestId = next.requestId,
                turnId = next.turnId,
                segmentIndex = next.index,
            ),
            callbacks = TtsCallbacks(
                onDiagnostics = callbacks.onDiagnostics,
                onStart = {
                    logQueue("playback_start index=${next.index}")
                    callbacks.onStart(next)
                },
                onDone = {
                    logQueue("playback_done index=${next.index}")
                    callbacks.onDone(next)
                    currentSegment = null
                    playNext()
                },
                onError = { message ->
                    logQueue("playback_error index=${next.index} msg=${message.take(40)}")
                    callbacks.onError(message)
                    currentSegment = null
                    playNext()
                },
            ),
        )

        if (!accepted) {
            logQueue("playNext_rejected index=${next.index}")
            callbacks.onError(TtsController.AUDIO_PLAYBACK_UNAVAILABLE_MESSAGE)
            currentSegment = null
            playNext()
        }
    }

    private fun logQueue(message: String) {
        runCatching { Log.d(QUEUE_TAG, message) }
    }
}
