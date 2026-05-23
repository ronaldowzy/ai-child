package com.childai.companion.voice

class RemoteAudioTtsController(
    private val audioUrlPlayer: AudioUrlPlayer,
    private val fallbackController: TtsController,
    private val backendBaseUrl: String,
) : TtsController {
    override fun speak(request: TtsRequest, callbacks: TtsCallbacks): Boolean {
        val audioUrl = request.audioUrl?.trim().orEmpty()
        if (audioUrl.isBlank()) {
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
                onDone = callbacks.onDone,
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
