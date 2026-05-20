package com.childai.companion.voice

class RemoteAudioTtsController(
    private val audioUrlPlayer: AudioUrlPlayer,
    private val fallbackController: TtsController,
    private val backendBaseUrl: String,
) : TtsController {
    override fun speak(request: TtsRequest, callbacks: TtsCallbacks): Boolean {
        val audioUrl = request.audioUrl?.trim().orEmpty()
        if (audioUrl.isBlank()) {
            return fallbackController.speak(request, callbacks)
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

        var fallbackAttempted = false
        var fallbackAccepted = false
        fun fallbackToSystem(reason: String): Boolean {
            if (fallbackAttempted) return fallbackAccepted
            fallbackAttempted = true
            callbacks.onDiagnostics(
                VoiceDiagnostics(
                    isAvailable = true,
                    isInitializing = false,
                    isInitialized = true,
                    lastRequestedTextPreview = request.text.previewForDiagnostics(),
                    lastFailureReason = reason,
                    lastSpeakResult = "REMOTE_AUDIO_ERROR",
                    playbackSource = "remote_audio",
                    audioUrl = audioUrl,
                ),
            )
            fallbackAccepted = fallbackController.speak(
                request = request.copy(audioUrl = null),
                callbacks = TtsCallbacks(
                    onDiagnostics = { diagnostics ->
                        callbacks.onDiagnostics(
                            diagnostics.copy(playbackSource = "system_tts_fallback"),
                        )
                    },
                    onStart = callbacks.onStart,
                    onDone = callbacks.onDone,
                    onError = {
                        callbacks.onError(TtsController.AUDIO_PLAYBACK_UNAVAILABLE_MESSAGE)
                    },
                ),
            )
            return fallbackAccepted
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
                    fallbackToSystem(reason)
                },
            ),
        )

        if (remoteAccepted) return true
        if (fallbackAttempted) return fallbackAccepted
        return fallbackToSystem("remote_audio_play_rejected")
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
