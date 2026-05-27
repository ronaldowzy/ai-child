package com.childai.companion.voice

import android.media.MediaPlayer
import android.util.Log

class MediaPlayerAudioUrlPlayer : AudioUrlPlayer {
    private var mediaPlayer: MediaPlayer? = null

    @Synchronized
    override fun play(url: String, callbacks: AudioUrlPlayerCallbacks): Boolean {
        stop()
        val player = MediaPlayer()
        mediaPlayer = player
        logPlayer("play url_present=${url.isNotBlank()}")
        return runCatching {
            player.setOnPreparedListener { prepared ->
                if (mediaPlayer === prepared) {
                    logPlayer("playback_start")
                    callbacks.onStart()
                    prepared.start()
                }
            }
            player.setOnCompletionListener { completed ->
                if (mediaPlayer === completed) {
                    logPlayer("playback_done")
                    clearPlayer(completed)
                    callbacks.onDone()
                }
            }
            player.setOnErrorListener { errored, what, extra ->
                if (mediaPlayer === errored) {
                    logPlayer("playback_error what=$what extra=$extra")
                    clearPlayer(errored)
                    callbacks.onError("remote_audio_failed what=$what extra=$extra")
                }
                true
            }
            player.setDataSource(url)
            player.prepareAsync()
            true
        }.getOrElse { throwable ->
            if (mediaPlayer === player) {
                clearPlayer(player)
            } else {
                player.releaseSafely()
            }
            val reason = "remote_audio_prepare_failed ${throwable.javaClass.simpleName}"
            runCatching {
                Log.w(TAG, "Remote audio prepare failed; url_present=${url.isNotBlank()}", throwable)
            }
            callbacks.onError(reason)
            false
        }
    }

    @Synchronized
    override fun stop() {
        val player = mediaPlayer ?: return
        logPlayer("stop")
        clearPlayer(player)
    }

    @Synchronized
    override fun release() {
        stop()
    }

    private fun clearPlayer(player: MediaPlayer) {
        if (mediaPlayer === player) {
            mediaPlayer = null
        }
        player.releaseSafely()
    }

    private fun MediaPlayer.releaseSafely() {
        runCatching {
            stop()
        }
        release()
    }

    private fun logPlayer(message: String) {
        runCatching { Log.d(TAG, message) }
    }

    private companion object {
        const val TAG = "MediaPlayerAudioUrl"
    }
}
