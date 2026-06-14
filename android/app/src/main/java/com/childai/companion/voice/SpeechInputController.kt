package com.childai.companion.voice

import com.childai.companion.config.DevSettings
import com.childai.companion.data.asr.AsrApiException
import com.childai.companion.data.asr.AsrRepository
import com.childai.companion.data.asr.AsrTranscriber

sealed interface SpeechInputResult {
    data class Transcript(
        val text: String,
        val provider: String? = null,
        val model: String? = null,
        val durationMs: Int? = null,
    ) : SpeechInputResult
    data class NeedsRetry(val message: String) : SpeechInputResult
    data class PolicyBlocked(val message: String) : SpeechInputResult
    data class Failed(val message: String) : SpeechInputResult
}

interface SpeechInputController {
    suspend fun startRecording()
    suspend fun stopAndTranscribe(
        childId: String,
        sessionId: String,
        timezone: String = DevSettings.TIMEZONE,
    ): SpeechInputResult
    suspend fun cancel()
    fun shutdown()
}

class BackendSpeechInputController(
    internal val recorder: VoiceRecorder,
    private val transcriber: AsrTranscriber = AsrRepository(),
) : SpeechInputController {
    override suspend fun startRecording() {
        recorder.start()
    }

    override suspend fun stopAndTranscribe(
        childId: String,
        sessionId: String,
        timezone: String,
    ): SpeechInputResult {
        val audio = recorder.stop()
        return try {
            val response = transcriber.transcribe(
                childId = childId,
                sessionId = sessionId,
                audio = audio,
                timezone = timezone,
            )
            when (response.status) {
                "ok" -> {
                    val transcript = response.transcript.orEmpty().trim()
                    if (transcript.isBlank()) {
                        SpeechInputResult.NeedsRetry(NEEDS_RETRY_MESSAGE)
                    } else {
                        SpeechInputResult.Transcript(
                            text = transcript,
                            provider = response.provider,
                            model = response.model,
                            durationMs = response.durationMs,
                        )
                    }
                }
                "needs_retry" -> SpeechInputResult.NeedsRetry(NEEDS_RETRY_MESSAGE)
                "blocked" -> SpeechInputResult.PolicyBlocked(POLICY_BLOCKED_MESSAGE)
                else -> SpeechInputResult.Failed(TEXT_FALLBACK_MESSAGE)
            }
        } catch (exception: AsrApiException) {
            exception.toSpeechInputResult()
        } finally {
            audio.deleteTemporaryFile()
        }
    }

    override suspend fun cancel() {
        recorder.cancel()
    }

    override fun shutdown() {
        recorder.shutdown()
    }

    private fun AsrApiException.toSpeechInputResult(): SpeechInputResult {
        return when (statusCode) {
            403 -> SpeechInputResult.PolicyBlocked(POLICY_BLOCKED_MESSAGE)
            400 -> when (detail) {
                "audio_too_long" -> SpeechInputResult.NeedsRetry(AUDIO_TOO_LONG_MESSAGE)
                "unsupported_audio_format", "invalid_audio_data" ->
                    SpeechInputResult.NeedsRetry(NEEDS_RETRY_MESSAGE)
                else -> SpeechInputResult.Failed(TEXT_FALLBACK_MESSAGE)
            }
            413 -> SpeechInputResult.NeedsRetry(AUDIO_TOO_LONG_MESSAGE)
            504 -> SpeechInputResult.NeedsRetry(PROVIDER_TIMEOUT_MESSAGE)
            else -> SpeechInputResult.Failed(TEXT_FALLBACK_MESSAGE)
        }
    }

    companion object {
        const val NEEDS_RETRY_MESSAGE = "我刚才没听清，可以再说一次。"
        const val AUDIO_TOO_LONG_MESSAGE = "这次说得有点长，可以短一点重说。"
        const val PROVIDER_TIMEOUT_MESSAGE = "刚才没有传好，我们可以再试一次。"
        const val POLICY_BLOCKED_MESSAGE = "我现在还不能听懂声音，请家长帮忙看看。"
        const val TEXT_FALLBACK_MESSAGE = "这次没有听懂声音，请家长帮忙看看。"
    }
}
