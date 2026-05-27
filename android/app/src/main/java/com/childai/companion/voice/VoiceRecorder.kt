package com.childai.companion.voice

import java.io.File

data class RecordedVoiceAudio(
    val file: File,
    val format: String = "wav",
    val sampleRateHz: Int = 16_000,
    val channelCount: Int = 1,
    val durationMs: Long,
    val stoppedBySilence: Boolean = false,
) {
    fun deleteTemporaryFile() {
        runCatching {
            if (file.exists()) {
                file.delete()
            }
        }
    }
}

interface VoiceRecorder {
    suspend fun start()
    suspend fun stop(): RecordedVoiceAudio
    suspend fun cancel()
    fun shutdown()
}
