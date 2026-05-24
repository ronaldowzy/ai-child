package com.childai.companion.voice

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AudioSegmentQueuePlayerTest {
    @Test
    fun enqueuesAndPlaysSegmentsInOrder() {
        val controller = RecordingTtsController(autoComplete = true)
        val started = mutableListOf<Int>()
        val player = AudioSegmentQueuePlayer(
            ttsController = controller,
            backendBaseUrl = "http://127.0.0.1:8000/",
            isMuted = { false },
            callbacks = AudioSegmentQueueCallbacks(
                onStart = { started.add(it.index) },
            ),
        )

        player.enqueue(AudioSegment(audioUrl = "/media/tts/one.wav", text = "一", index = 0))
        player.enqueue(AudioSegment(audioUrl = "/media/tts/two.wav", text = "二", index = 1))

        assertEquals(listOf(0, 1), started)
        assertEquals(
            listOf("/media/tts/one.wav", "/media/tts/two.wav"),
            controller.requests.map { it.audioUrl },
        )
        assertEquals(0, player.queuedCount)
    }

    @Test
    fun mutedQueueSkipsAudio() {
        val controller = RecordingTtsController(autoComplete = true)
        val player = AudioSegmentQueuePlayer(
            ttsController = controller,
            backendBaseUrl = "http://127.0.0.1:8000/",
            isMuted = { true },
            callbacks = AudioSegmentQueueCallbacks(),
        )

        player.enqueue(AudioSegment(audioUrl = "/media/tts/one.wav", text = "一", index = 0))

        assertTrue(controller.requests.isEmpty())
        assertEquals(0, player.queuedCount)
    }

    @Test
    fun stopClearsQueuedSegmentsAndStopsCurrentPlayback() {
        val controller = RecordingTtsController(autoComplete = false)
        val player = AudioSegmentQueuePlayer(
            ttsController = controller,
            backendBaseUrl = "http://127.0.0.1:8000/",
            isMuted = { false },
            callbacks = AudioSegmentQueueCallbacks(),
        )

        player.enqueue(AudioSegment(audioUrl = "/media/tts/one.wav", text = "一", index = 0))
        player.enqueue(AudioSegment(audioUrl = "/media/tts/two.wav", text = "二", index = 1))
        assertEquals(2, player.queuedCount)

        player.stopAndClear()

        assertTrue(controller.stopCalled)
        assertEquals(0, player.queuedCount)
    }

    @Test
    fun rejectedSegmentDoesNotBlockLaterSegments() {
        val controller = RecordingTtsController(autoComplete = true, accept = false)
        var errors = 0
        val player = AudioSegmentQueuePlayer(
            ttsController = controller,
            backendBaseUrl = "http://127.0.0.1:8000/",
            isMuted = { false },
            callbacks = AudioSegmentQueueCallbacks(
                onError = { errors += 1 },
            ),
        )

        player.enqueue(AudioSegment(audioUrl = "/media/tts/one.wav", text = "一", index = 0))

        assertFalse(controller.requests.isEmpty())
        assertEquals(1, errors)
        assertEquals(0, player.queuedCount)
    }

    @Test
    fun segmentPlaybackPropagatesLatencyTraceIds() {
        val controller = RecordingTtsController(autoComplete = true)
        val player = AudioSegmentQueuePlayer(
            ttsController = controller,
            backendBaseUrl = "http://127.0.0.1:8000/",
            isMuted = { false },
            callbacks = AudioSegmentQueueCallbacks(),
        )

        player.enqueue(
            AudioSegment(
                audioUrl = "/media/tts/one.wav",
                text = "一",
                index = 3,
                requestId = "req_trace_001",
                turnId = "turn_trace_001",
            ),
        )

        val request = controller.requests.single()
        assertEquals("req_trace_001", request.requestId)
        assertEquals("turn_trace_001", request.turnId)
        assertEquals(3, request.segmentIndex)
    }
}

private class RecordingTtsController(
    private val autoComplete: Boolean,
    private val accept: Boolean = true,
) : TtsController {
    val requests = mutableListOf<TtsRequest>()
    var stopCalled = false

    override fun speak(request: TtsRequest, callbacks: TtsCallbacks): Boolean {
        requests.add(request)
        if (!accept) return false
        callbacks.onStart()
        if (autoComplete) {
            callbacks.onDone()
        }
        return true
    }

    override fun stop() {
        stopCalled = true
    }

    override fun shutdown() = Unit
}
