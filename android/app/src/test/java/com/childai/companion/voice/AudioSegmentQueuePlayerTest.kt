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

    @Test
    fun stopClearsQueueThenNewSegmentsPlayFromStart() {
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
        player.enqueue(AudioSegment(audioUrl = "/media/tts/three.wav", text = "三", index = 2))
        assertEquals(listOf(0, 1, 2), started)

        player.stopAndClear()
        assertEquals(0, player.queuedCount)
        assertTrue(controller.stopCalled)

        controller.stopCalled = false
        started.clear()
        player.enqueue(AudioSegment(audioUrl = "/media/tts/four.wav", text = "四", index = 3))
        player.enqueue(AudioSegment(audioUrl = "/media/tts/five.wav", text = "五", index = 4))

        assertEquals(listOf(3, 4), started)
        assertEquals(0, player.queuedCount)
    }

    @Test
    fun mutedStateSkipsEnqueueButTextStillVisible() {
        var muted = false
        val controller = RecordingTtsController(autoComplete = true)
        var lastErrorMessage: String? = "some_old_error"
        val player = AudioSegmentQueuePlayer(
            ttsController = controller,
            backendBaseUrl = "http://127.0.0.1:8000/",
            isMuted = { muted },
            callbacks = AudioSegmentQueueCallbacks(
                onError = { lastErrorMessage = it },
            ),
        )

        player.enqueue(AudioSegment(audioUrl = "/media/tts/one.wav", text = "这是文字内容。", index = 0))
        assertEquals(1, controller.requests.size)

        muted = true
        player.enqueue(AudioSegment(audioUrl = "/media/tts/two.wav", text = "第二段也有文字。", index = 1))
        assertEquals(1, controller.requests.size)
        assertEquals(0, player.queuedCount)

        assertEquals("some_old_error", lastErrorMessage)
    }

    @Test
    fun threeSegmentsPlayInStrictFifoOrder() {
        val controller = RecordingTtsController(autoComplete = true)
        val player = AudioSegmentQueuePlayer(
            ttsController = controller,
            backendBaseUrl = "http://127.0.0.1:8000/",
            isMuted = { false },
            callbacks = AudioSegmentQueueCallbacks(),
        )

        player.enqueue(AudioSegment(audioUrl = "/media/tts/a.wav", text = "第一段", index = 0))
        player.enqueue(AudioSegment(audioUrl = "/media/tts/b.wav", text = "第二段", index = 1))
        player.enqueue(AudioSegment(audioUrl = "/media/tts/c.wav", text = "第三段", index = 2))

        assertEquals(listOf(0, 1, 2), controller.playedIndices)
        assertEquals(
            listOf("/media/tts/a.wav", "/media/tts/b.wav", "/media/tts/c.wav"),
            controller.requests.map { it.audioUrl },
        )
        assertEquals(0, player.queuedCount)
    }

    @Test
    fun stopAndClearInterruptsQueuedSegmentsNotYetPlayed() {
        val controller = RecordingTtsController(autoComplete = false)
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
        player.enqueue(AudioSegment(audioUrl = "/media/tts/three.wav", text = "三", index = 2))

        assertEquals(listOf(0), started)
        assertEquals(3, player.queuedCount)

        player.stopAndClear()

        assertEquals(listOf(0), started)
        assertEquals(0, player.queuedCount)
        assertTrue(controller.stopCalled)
    }
}

private class RecordingTtsController(
    private val autoComplete: Boolean,
    private val accept: Boolean = true,
) : TtsController {
    val requests = mutableListOf<TtsRequest>()
    val playedIndices = mutableListOf<Int>()
    var stopCalled = false

    override fun speak(request: TtsRequest, callbacks: TtsCallbacks): Boolean {
        requests.add(request)
        if (!accept) return false
        playedIndices.add(request.segmentIndex ?: -1)
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
