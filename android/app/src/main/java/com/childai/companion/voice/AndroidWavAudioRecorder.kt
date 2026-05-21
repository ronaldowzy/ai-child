package com.childai.companion.voice

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.SystemClock
import java.io.File
import java.io.FileOutputStream
import java.io.RandomAccessFile
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class AndroidWavAudioRecorder(
    private val cacheDirectory: File,
    private val preferredSampleRateHz: Int = DEFAULT_SAMPLE_RATE_HZ,
    private val maxDurationMs: Long = MAX_DURATION_MS,
) : VoiceRecorder {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val lock = Any()
    private var activeRecording: ActiveRecording? = null

    @SuppressLint("MissingPermission")
    override suspend fun start() = withContext(Dispatchers.IO) {
        synchronized(lock) {
            check(activeRecording == null) { "Voice recording is already active" }
        }

        val outputDirectory = File(cacheDirectory, "voice-input").apply { mkdirs() }
        val outputFile = File.createTempFile("voice-input-", ".wav", outputDirectory)
        val audioConfig = resolveAudioConfig()
        val bufferSize = maxOf(
            audioConfig.minBufferSize,
            audioConfig.sampleRateHz * BYTES_PER_SAMPLE / 5,
        )
        val recorder = AudioRecord(
            MediaRecorder.AudioSource.VOICE_RECOGNITION,
            audioConfig.sampleRateHz,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
            bufferSize,
        )
        if (recorder.state != AudioRecord.STATE_INITIALIZED) {
            recorder.release()
            outputFile.delete()
            error("AudioRecord failed to initialize")
        }

        val output = FileOutputStream(outputFile)
        output.write(ByteArray(WAV_HEADER_BYTES))
        val startedAtMs = SystemClock.elapsedRealtime()
        val active = ActiveRecording(
            file = outputFile,
            recorder = recorder,
            output = output,
            startedAtMs = startedAtMs,
            sampleRateHz = audioConfig.sampleRateHz,
        )

        try {
            recorder.startRecording()
        } catch (throwable: Throwable) {
            recorder.release()
            runCatching { output.close() }
            outputFile.delete()
            throw throwable
        }
        synchronized(lock) {
            activeRecording = active
        }
        active.job = scope.launch {
            recordPcm(active = active, bufferSize = bufferSize)
        }
    }

    override suspend fun stop(): RecordedVoiceAudio {
        val active = synchronized(lock) {
            activeRecording.also { activeRecording = null }
        } ?: error("Voice recording is not active")

        active.job?.cancelAndJoin()
        return withContext(Dispatchers.IO) {
            finishRecording(active = active, deleteFile = false)
            RecordedVoiceAudio(
                file = active.file,
                sampleRateHz = active.sampleRateHz,
                channelCount = 1,
                durationMs = (
                    SystemClock.elapsedRealtime() - active.startedAtMs
                    ).coerceIn(1L, maxDurationMs),
            )
        }
    }

    override suspend fun cancel() {
        val active = synchronized(lock) {
            activeRecording.also { activeRecording = null }
        } ?: return

        active.job?.cancelAndJoin()
        withContext(Dispatchers.IO) {
            finishRecording(active = active, deleteFile = true)
        }
    }

    override fun shutdown() {
        scope.cancel()
        val active = synchronized(lock) {
            activeRecording.also { activeRecording = null }
        }
        active?.let {
            runCatching { it.recorder.stop() }
            it.recorder.release()
            runCatching { it.output.close() }
            it.file.delete()
        }
    }

    private suspend fun recordPcm(active: ActiveRecording, bufferSize: Int) {
        val buffer = ByteArray(bufferSize)
        try {
            while (
                currentCoroutineContext().isActive &&
                SystemClock.elapsedRealtime() - active.startedAtMs < maxDurationMs
            ) {
                val read = active.recorder.read(buffer, 0, buffer.size)
                if (read > 0) {
                    active.output.write(buffer, 0, read)
                    active.pcmBytesWritten += read
                }
            }
        } finally {
            runCatching { active.recorder.stop() }
        }
    }

    private fun finishRecording(active: ActiveRecording, deleteFile: Boolean) {
        runCatching { active.recorder.stop() }
        active.recorder.release()
        runCatching { active.output.flush() }
        active.output.close()
        if (deleteFile) {
            active.file.delete()
            return
        }
        writeWavHeader(
            file = active.file,
            sampleRateHz = active.sampleRateHz,
            channelCount = 1,
            pcmBytes = active.pcmBytesWritten,
        )
    }

    private fun resolveAudioConfig(): AudioRecordConfig {
        val sampleRates = listOf(preferredSampleRateHz, 44_100, 48_000).distinct()
        sampleRates.forEach { sampleRate ->
            val minBufferSize = AudioRecord.getMinBufferSize(
                sampleRate,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
            )
            if (minBufferSize > 0) {
                return AudioRecordConfig(
                    sampleRateHz = sampleRate,
                    minBufferSize = minBufferSize,
                )
            }
        }
        error("AudioRecord does not support mono PCM recording")
    }

    private data class ActiveRecording(
        val file: File,
        val recorder: AudioRecord,
        val output: FileOutputStream,
        val startedAtMs: Long,
        val sampleRateHz: Int,
        var pcmBytesWritten: Int = 0,
        var job: Job? = null,
    )

    private data class AudioRecordConfig(
        val sampleRateHz: Int,
        val minBufferSize: Int,
    )

    companion object {
        const val DEFAULT_SAMPLE_RATE_HZ = 16_000
        const val MAX_DURATION_MS = 30_000L
        private const val BYTES_PER_SAMPLE = 2
        private const val WAV_HEADER_BYTES = 44

        fun writeWavHeader(
            file: File,
            sampleRateHz: Int,
            channelCount: Int,
            pcmBytes: Int,
        ) {
            val byteRate = sampleRateHz * channelCount * BYTES_PER_SAMPLE
            val blockAlign = channelCount * BYTES_PER_SAMPLE
            RandomAccessFile(file, "rw").use { wav ->
                wav.seek(0)
                wav.write("RIFF".toByteArray(Charsets.US_ASCII))
                wav.writeIntLe(36 + pcmBytes)
                wav.write("WAVE".toByteArray(Charsets.US_ASCII))
                wav.write("fmt ".toByteArray(Charsets.US_ASCII))
                wav.writeIntLe(16)
                wav.writeShortLe(1)
                wav.writeShortLe(channelCount)
                wav.writeIntLe(sampleRateHz)
                wav.writeIntLe(byteRate)
                wav.writeShortLe(blockAlign)
                wav.writeShortLe(16)
                wav.write("data".toByteArray(Charsets.US_ASCII))
                wav.writeIntLe(pcmBytes)
            }
        }

        private fun RandomAccessFile.writeIntLe(value: Int) {
            write(value and 0xff)
            write(value shr 8 and 0xff)
            write(value shr 16 and 0xff)
            write(value shr 24 and 0xff)
        }

        private fun RandomAccessFile.writeShortLe(value: Int) {
            write(value and 0xff)
            write(value shr 8 and 0xff)
        }
    }
}
