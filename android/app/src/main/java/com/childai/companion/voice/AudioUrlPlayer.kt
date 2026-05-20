package com.childai.companion.voice

data class AudioUrlPlayerCallbacks(
    val onStart: () -> Unit = {},
    val onDone: () -> Unit = {},
    val onError: (String) -> Unit = {},
)

interface AudioUrlPlayer {
    fun play(url: String, callbacks: AudioUrlPlayerCallbacks): Boolean
    fun stop()
    fun release()
}

object NoOpAudioUrlPlayer : AudioUrlPlayer {
    override fun play(url: String, callbacks: AudioUrlPlayerCallbacks): Boolean {
        callbacks.onError("No audio URL player attached")
        return false
    }

    override fun stop() = Unit

    override fun release() = Unit
}
