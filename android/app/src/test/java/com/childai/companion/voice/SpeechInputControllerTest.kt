package com.childai.companion.voice

import com.childai.companion.data.asr.AsrTranscriber
import com.childai.companion.data.asr.AsrTranscriptionResponse
import java.io.File
import java.nio.file.Files
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SpeechInputControllerTest {
    @Test
    fun stopAndTranscribeDeletesTemporaryAudioAfterUpload() = runBlocking {
        val audioFile = Files.createTempFile("asr-upload", ".wav").toFile()
        audioFile.writeBytes(byteArrayOf(1, 2, 3))
        val controller = BackendSpeechInputController(
            recorder = FakeVoiceRecorder(
                audio = RecordedVoiceAudio(
                    file = audioFile,
                    sampleRateHz = 16000,
                    channelCount = 1,
                    durationMs = 1000,
                ),
            ),
            transcriber = OkTranscriber(),
        )

        val result = controller.stopAndTranscribe(
            childId = "child_demo_001",
            sessionId = "android-session",
        )

        assertTrue(result is SpeechInputResult.Transcript)
        assertFalse(audioFile.exists())
    }

    @Test
    fun cancelDelegatesToRecorderForTemporaryCleanup() = runBlocking {
        val recorder = FakeVoiceRecorder()
        val controller = BackendSpeechInputController(
            recorder = recorder,
            transcriber = OkTranscriber(),
        )

        controller.cancel()

        assertTrue(recorder.cancelCalled)
    }
}

private class FakeVoiceRecorder(
    private val audio: RecordedVoiceAudio = RecordedVoiceAudio(
        file = File.createTempFile("voice-input", ".wav"),
        durationMs = 1000,
    ),
) : VoiceRecorder {
    var cancelCalled = false

    override suspend fun start() = Unit

    override suspend fun stop(): RecordedVoiceAudio = audio

    override suspend fun cancel() {
        cancelCalled = true
        audio.deleteTemporaryFile()
    }

    override fun shutdown() = Unit
}

private class OkTranscriber : AsrTranscriber {
    override suspend fun transcribe(
        childId: String,
        sessionId: String,
        audio: RecordedVoiceAudio,
        timezone: String,
    ): AsrTranscriptionResponse {
        return AsrTranscriptionResponse(
            status = "ok",
            transcript = "测试语音。",
            requiresConfirmation = true,
            provider = "mock",
            model = "mock-asr-v0",
            language = "zh-CN",
            durationMs = 1000,
            confidence = null,
            errorCode = null,
            fallbackAction = null,
        )
    }
}
