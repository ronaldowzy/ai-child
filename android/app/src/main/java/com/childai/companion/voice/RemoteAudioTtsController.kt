package com.childai.companion.voice

import android.util.Log

class RemoteAudioTtsController(
    private val audioUrlPlayer: AudioUrlPlayer,
    private val fallbackController: TtsController,
    private val backendBaseUrl: String,
) : TtsController {
    override fun speak(request: TtsRequest, callbacks: TtsCallbacks): Boolean {
        val requestedAtMs = System.currentTimeMillis()
        val audioUrl = request.audioUrl?.trim().orEmpty()
        if (audioUrl.isBlank()) {
            logTiming(
                event = "remote_audio_url_missing",
                request = request,
                requestedAtMs = requestedAtMs,
                result = "missing",
            )
            callbacks.onDiagnostics(
                VoiceDiagnostics(
                    isAvailable = false,
                    isInitializing = false,
                    isInitialized = false,
                    lastRequestedTextPreview = request.text.previewForDiagnostics(),
                    lastFailureReason = "remote_audio_url_missing",
                    lastSpeakResult = "SKIPPED_NO_REMOTE_AUDIO",
                    playbackSource = "remote_audio",
                    audioUrl = null,
                ),
            )
            callbacks.onError(TtsController.AUDIO_PLAYBACK_UNAVAILABLE_MESSAGE)
            return false
        }

        val resolvedUrl = resolveAudioUrl(
            audioUrl = audioUrl,
            backendBaseUrl = request.backendBaseUrl ?: backendBaseUrl,
        )
        logTiming(
            event = "remote_audio_url_received",
            request = request,
            requestedAtMs = requestedAtMs,
            result = "pending",
        )
        callbacks.onDiagnostics(
            VoiceDiagnostics(
                isAvailable = true,
                isInitializing = false,
                isInitialized = true,
                lastRequestedTextPreview = request.text.previewForDiagnostics(),
                lastSpeakResult = "REMOTE_AUDIO_PENDING",
                playbackSource = "remote_audio",
                audioUrl = audioUrl,
            ),
        )

        fun reportRemoteAudioError(reason: String): Boolean {
            logTiming(
                event = "remote_audio_error",
                request = request,
                requestedAtMs = requestedAtMs,
                result = reason,
            )
            callbacks.onDiagnostics(
                VoiceDiagnostics(
                    isAvailable = false,
                    isInitializing = false,
                    isInitialized = false,
                    lastRequestedTextPreview = request.text.previewForDiagnostics(),
                    lastFailureReason = reason,
                    lastSpeakResult = "REMOTE_AUDIO_ERROR",
                    playbackSource = "remote_audio",
                    audioUrl = audioUrl,
                ),
            )
            callbacks.onError(TtsController.AUDIO_PLAYBACK_UNAVAILABLE_MESSAGE)
            return false
        }

        val remoteAccepted = audioUrlPlayer.play(
            url = resolvedUrl,
            callbacks = AudioUrlPlayerCallbacks(
                onStart = {
                    logTiming(
                        event = "remote_audio_playback_started",
                        request = request,
                        requestedAtMs = requestedAtMs,
                        result = "playing",
                    )
                    callbacks.onDiagnostics(
                        VoiceDiagnostics(
                            isAvailable = true,
                            isInitializing = false,
                            isInitialized = true,
                            lastRequestedTextPreview = request.text.previewForDiagnostics(),
                            lastSpeakResult = "REMOTE_AUDIO_PLAYING",
                            playbackSource = "remote_audio",
                            audioUrl = audioUrl,
                        ),
                    )
                    callbacks.onStart()
                },
                onDone = {
                    logTiming(
                        event = "remote_audio_playback_done",
                        request = request,
                        requestedAtMs = requestedAtMs,
                        result = "done",
                    )
                    callbacks.onDone()
                },
                onError = { reason ->
                    reportRemoteAudioError(reason)
                },
            ),
        )

        if (remoteAccepted) return true
        return reportRemoteAudioError("remote_audio_play_rejected")
    }

    override fun stop() {
        audioUrlPlayer.stop()
        fallbackController.stop()
    }

    override fun shutdown() {
        audioUrlPlayer.release()
        fallbackController.shutdown()
    }

    companion object {
        private const val TAG = "XiaobaohuTtsTiming"

        private fun logTiming(
            event: String,
            request: TtsRequest,
            requestedAtMs: Long,
            result: String,
        ) {
            runCatching {
                Log.i(
                    TAG,
                    "event=$event" +
                        " request_id=${request.requestId.orEmpty()}" +
                        " turn_id=${request.turnId.orEmpty()}" +
                        " segment_index=${request.segmentIndex ?: -1}" +
                        " elapsed_ms=${System.currentTimeMillis() - requestedAtMs}" +
                        " audio_url_present=${!request.audioUrl.isNullOrBlank()}" +
                        " result=$result",
                )
            }
        }

        fun resolveAudioUrl(audioUrl: String, backendBaseUrl: String): String {
            val trimmedAudioUrl = audioUrl.trim()
            if (
                trimmedAudioUrl.startsWith("http://", ignoreCase = true) ||
                trimmedAudioUrl.startsWith("https://", ignoreCase = true)
            ) {
                return trimmedAudioUrl
            }
            val base = backendBaseUrl.trim().trimEnd('/')
            if (base.isBlank()) return trimmedAudioUrl
            val path = if (trimmedAudioUrl.startsWith("/")) {
                trimmedAudioUrl
            } else {
                "/$trimmedAudioUrl"
            }
            return base + path
        }
    }
}
