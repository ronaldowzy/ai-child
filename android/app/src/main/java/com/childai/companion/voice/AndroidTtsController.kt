package com.childai.companion.voice

import android.content.Context
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import java.util.Locale
import java.util.UUID

class AndroidTtsController(
    context: Context,
    private val defaultVoiceProfile: VoiceProfile = VoiceProfile.default(),
) : TtsController, TextToSpeech.OnInitListener {
    private var textToSpeech: TextToSpeech? = null
    private var isInitialized = false
    private var initializationFailed = false
    private var activeUtteranceId: String? = null
    private var activeCallbacks: TtsCallbacks? = null
    private var pendingRequest: PendingRequest? = null

    init {
        textToSpeech = runCatching {
            TextToSpeech(context.applicationContext, this)
        }.getOrElse {
            initializationFailed = true
            null
        }
    }

    override fun onInit(status: Int) {
        if (status != TextToSpeech.SUCCESS || textToSpeech == null) {
            initializationFailed = true
            pendingRequest?.callbacks?.onError(TtsController.UNAVAILABLE_MESSAGE)
            pendingRequest = null
            return
        }

        isInitialized = true
        textToSpeech?.setOnUtteranceProgressListener(
            object : UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) {
                    if (utteranceId == activeUtteranceId) {
                        activeCallbacks?.onStart()
                    }
                }

                override fun onDone(utteranceId: String?) {
                    if (utteranceId == activeUtteranceId) {
                        val callbacks = activeCallbacks
                        clearActive()
                        callbacks?.onDone()
                    }
                }

                @Deprecated("Deprecated in Java")
                override fun onError(utteranceId: String?) {
                    onError(utteranceId, TextToSpeech.ERROR)
                }

                override fun onError(utteranceId: String?, errorCode: Int) {
                    if (utteranceId == activeUtteranceId) {
                        val callbacks = activeCallbacks
                        clearActive()
                        callbacks?.onError(TtsController.UNAVAILABLE_MESSAGE)
                    }
                }
            },
        )

        pendingRequest?.let { pending ->
            pendingRequest = null
            speak(pending.request, pending.callbacks)
        }
    }

    @Synchronized
    override fun speak(request: TtsRequest, callbacks: TtsCallbacks): Boolean {
        val text = request.text.trim()
        if (text.isEmpty()) return false

        stop()

        if (initializationFailed || textToSpeech == null) {
            callbacks.onError(TtsController.UNAVAILABLE_MESSAGE)
            return false
        }

        if (!isInitialized) {
            pendingRequest = PendingRequest(
                request = request.copy(text = text),
                callbacks = callbacks,
            )
            return true
        }

        return speakNow(
            request = request.copy(text = text),
            callbacks = callbacks,
        )
    }

    @Synchronized
    override fun stop() {
        pendingRequest = null
        clearActive()
        textToSpeech?.stop()
    }

    @Synchronized
    override fun shutdown() {
        pendingRequest = null
        clearActive()
        textToSpeech?.stop()
        textToSpeech?.shutdown()
        textToSpeech = null
        isInitialized = false
        initializationFailed = true
    }

    private fun speakNow(request: TtsRequest, callbacks: TtsCallbacks): Boolean {
        val tts = textToSpeech ?: run {
            callbacks.onError(TtsController.UNAVAILABLE_MESSAGE)
            return false
        }
        val profile = request.voiceProfile
        if (!applyProfile(tts, profile)) {
            callbacks.onError(TtsController.UNAVAILABLE_MESSAGE)
            return false
        }

        val utteranceId = "white-fox-${UUID.randomUUID()}"
        activeUtteranceId = utteranceId
        activeCallbacks = callbacks
        val result = tts.speak(
            request.text,
            TextToSpeech.QUEUE_FLUSH,
            Bundle(),
            utteranceId,
        )
        if (result != TextToSpeech.SUCCESS) {
            clearActive()
            callbacks.onError(TtsController.UNAVAILABLE_MESSAGE)
            return false
        }
        return true
    }

    private fun applyProfile(tts: TextToSpeech, profile: VoiceProfile): Boolean {
        val languageResult = tts.setLanguage(profile.locale)
        if (
            languageResult == TextToSpeech.LANG_MISSING_DATA ||
            languageResult == TextToSpeech.LANG_NOT_SUPPORTED
        ) {
            return false
        }

        val selectedVoice = selectVoice(tts, profile)
        if (selectedVoice != null) {
            tts.voice = selectedVoice
        }
        tts.setSpeechRate(profile.speechRate)
        tts.setPitch(profile.pitch)
        return true
    }

    private fun selectVoice(tts: TextToSpeech, profile: VoiceProfile): android.speech.tts.Voice? {
        val voices = runCatching { tts.voices }.getOrNull().orEmpty()
        profile.preferredVoiceName?.let { preferredName ->
            voices.firstOrNull { it.name == preferredName }?.let { return it }
        }

        return voices.firstOrNull { voice ->
            voice.locale.matchesLanguage(profile.locale)
        }
    }

    private fun Locale.matchesLanguage(target: Locale): Boolean {
        return language.equals(target.language, ignoreCase = true)
    }

    private fun clearActive() {
        activeUtteranceId = null
        activeCallbacks = null
    }

    private data class PendingRequest(
        val request: TtsRequest,
        val callbacks: TtsCallbacks,
    )
}
