package com.childai.companion.data.asr

import com.childai.companion.config.DevSettings
import com.childai.companion.voice.RecordedVoiceAudio
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Base64

interface AsrTranscriber {
    suspend fun transcribe(
        childId: String,
        sessionId: String,
        audio: RecordedVoiceAudio,
        timezone: String = DevSettings.TIMEZONE,
    ): AsrTranscriptionResponse
}

class AsrRepository(
    private val apiClient: AsrApiClient = AsrApiClient(),
) : AsrTranscriber {
    override suspend fun transcribe(
        childId: String,
        sessionId: String,
        audio: RecordedVoiceAudio,
        timezone: String,
    ): AsrTranscriptionResponse {
        val encodedAudio = Base64.getEncoder().encodeToString(audio.file.readBytes())
        return apiClient.transcribe(
            AsrTranscriptionRequest(
                childId = childId,
                sessionId = sessionId,
                audio = AsrAudioPayload(
                    data = "data:audio/${audio.format};base64,$encodedAudio",
                    format = audio.format,
                    sampleRateHz = audio.sampleRateHz,
                    channelCount = audio.channelCount,
                    durationMs = audio.durationMs.toInt().coerceAtLeast(1),
                ),
                clientContext = AsrClientContext(
                    deviceTime = nowIsoOffset(timezone),
                    timezone = timezone,
                ),
            ),
        )
    }

    private fun nowIsoOffset(timezone: String): String {
        val zone = runCatching { ZoneId.of(timezone) }
            .getOrElse { ZoneId.systemDefault() }
        return OffsetDateTime.now(zone).format(DateTimeFormatter.ISO_OFFSET_DATE_TIME)
    }
}
