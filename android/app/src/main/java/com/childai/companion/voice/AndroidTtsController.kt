package com.childai.companion.voice

import android.content.Context
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.util.Log
import java.util.Locale
import java.util.UUID

class AndroidTtsController(
    context: Context,
    private val defaultVoiceProfile: VoiceProfile = VoiceProfile.default(),
) : TtsController, TextToSpeech.OnInitListener {
    private var textToSpeech: TextToSpeech? = null
    private var isInitialized = false
    private var progressListenerConfigured = false
    private var initializationFailed = false
    private var activeUtteranceId: String? = null
    private var activeCallbacks: TtsCallbacks? = null
    private var pendingRequest: PendingRequest? = null
    private var diagnostics = VoiceDiagnostics(
        isAvailable = false,
        isInitializing = true,
        isInitialized = false,
    )

    init {
        textToSpeech = runCatching {
            TextToSpeech(context.applicationContext, this)
        }.getOrElse {
            initializationFailed = true
            diagnostics = diagnostics.copy(
                isAvailable = false,
                isInitializing = false,
                isInitialized = false,
                lastFailureReason = "TextToSpeech constructor failed: ${it.message}",
            )
            Log.w(TAG, "TextToSpeech constructor failed", it)
            null
        }
        val createdTts = textToSpeech
        if (createdTts == null && !initializationFailed) {
            initializationFailed = true
            diagnostics = diagnostics.copy(
                isAvailable = false,
                isInitializing = false,
                isInitialized = false,
                lastFailureReason = "No TextToSpeech engine was returned by Android.",
                lastSpeakResult = "SKIPPED_NO_ENGINE",
            )
        } else {
            diagnostics = diagnostics.copy(
                isAvailable = createdTts != null,
                isInitializing = createdTts != null && !isInitialized,
                isInitialized = isInitialized,
                enginePackageName = createdTts?.defaultEngine,
            )
            configureProgressListenerIfReady()
            flushPendingRequestIfReady()
        }
    }

    override fun onInit(status: Int) {
        if (status != TextToSpeech.SUCCESS) {
            initializationFailed = true
            diagnostics = diagnostics.copy(
                isAvailable = false,
                isInitializing = false,
                isInitialized = false,
                lastFailureReason = "TextToSpeech onInit ${ttsResultName(status)}",
                enginePackageName = textToSpeech?.defaultEngine,
            )
            Log.w(TAG, "TextToSpeech init failed: ${diagnostics.lastFailureReason}")
            pendingRequest?.callbacks?.onDiagnostics(diagnostics)
            pendingRequest?.callbacks?.onError(TtsController.UNAVAILABLE_MESSAGE)
            pendingRequest = null
            return
        }

        isInitialized = true
        initializationFailed = false
        diagnostics = diagnostics.copy(
            isAvailable = true,
            isInitializing = false,
            isInitialized = true,
            enginePackageName = textToSpeech?.defaultEngine,
            lastFailureReason = null,
        )
        Log.d(TAG, "TextToSpeech init succeeded, engine=${diagnostics.enginePackageName}")
        configureProgressListenerIfReady()
        flushPendingRequestIfReady()
    }

    private fun configureProgressListenerIfReady() {
        val tts = textToSpeech ?: return
        if (!isInitialized || progressListenerConfigured) return
        progressListenerConfigured = true
        tts.setOnUtteranceProgressListener(
            object : UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) {
                    if (utteranceId == activeUtteranceId) {
                        activeCallbacks?.onDiagnostics(diagnostics)
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
                        diagnostics = diagnostics.copy(
                            isAvailable = true,
                            isInitializing = false,
                            isInitialized = true,
                            lastFailureReason = "Utterance error code=$errorCode",
                            lastSpeakResult = "ERROR_CALLBACK_$errorCode",
                        )
                        Log.w(TAG, "TextToSpeech utterance error: $errorCode")
                        clearActive()
                        callbacks?.onDiagnostics(diagnostics)
                        callbacks?.onError(TtsController.UNAVAILABLE_MESSAGE)
                    }
                }
            },
        )
    }

    private fun flushPendingRequestIfReady() {
        if (!isInitialized || textToSpeech == null) return
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
        diagnostics = diagnostics.copy(
            lastRequestedTextPreview = text.previewForDiagnostics(),
            lastFailureReason = null,
            lastSpeakResult = null,
        )

        if (initializationFailed || textToSpeech == null) {
            diagnostics = diagnostics.copy(
                isAvailable = false,
                isInitializing = false,
                isInitialized = false,
                lastFailureReason = diagnostics.lastFailureReason
                    ?: "TextToSpeech is unavailable",
                lastSpeakResult = "SKIPPED_UNAVAILABLE",
                enginePackageName = textToSpeech?.defaultEngine,
            )
            callbacks.onDiagnostics(diagnostics)
            Log.w(TAG, "TextToSpeech unavailable before speak")
            callbacks.onError(TtsController.UNAVAILABLE_MESSAGE)
            return false
        }

        if (!isInitialized) {
            diagnostics = diagnostics.copy(
                isAvailable = true,
                isInitializing = true,
                isInitialized = false,
                enginePackageName = textToSpeech?.defaultEngine,
                lastSpeakResult = "PENDING_INIT",
            )
            pendingRequest = PendingRequest(
                request = request.copy(text = text),
                callbacks = callbacks,
            )
            callbacks.onDiagnostics(diagnostics)
            Log.d(TAG, "TextToSpeech speak queued while initializing")
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
            diagnostics = diagnostics.copy(
                isAvailable = false,
                isInitializing = false,
                isInitialized = false,
                lastFailureReason = "TextToSpeech object is null",
                lastSpeakResult = "SKIPPED_NULL_TTS",
            )
            callbacks.onDiagnostics(diagnostics)
            callbacks.onError(TtsController.UNAVAILABLE_MESSAGE)
            return false
        }
        val profile = request.voiceProfile
        val profileResult = applyProfile(tts, profile)
        diagnostics = diagnostics.copy(
            isAvailable = profileResult.isAvailable,
            isInitializing = false,
            isInitialized = isInitialized,
            selectedLocale = profile.locale.toLanguageTag(),
            selectedVoiceName = profileResult.selectedVoiceName,
            setLanguageResult = profileResult.setLanguageResult,
            setVoiceResult = profileResult.setVoiceResult,
            enginePackageName = tts.defaultEngine,
            lastFailureReason = profileResult.failureReason,
        )
        callbacks.onDiagnostics(diagnostics)
        if (!profileResult.isAvailable) {
            Log.w(TAG, "TextToSpeech profile unavailable: ${profileResult.failureReason}")
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
        diagnostics = diagnostics.copy(
            isAvailable = true,
            isInitializing = false,
            isInitialized = true,
            lastSpeakResult = ttsResultName(result),
            lastFailureReason = if (result == TextToSpeech.SUCCESS) {
                null
            } else {
                "TextToSpeech.speak returned ${ttsResultName(result)}"
            },
        )
        callbacks.onDiagnostics(diagnostics)
        Log.d(TAG, "TextToSpeech speak result=${diagnostics.lastSpeakResult}")
        if (result != TextToSpeech.SUCCESS) {
            clearActive()
            callbacks.onError(TtsController.UNAVAILABLE_MESSAGE)
            return false
        }
        return true
    }

    private fun applyProfile(tts: TextToSpeech, profile: VoiceProfile): ProfileApplyResult {
        val languageResult = tts.setLanguage(profile.locale)
        if (
            languageResult == TextToSpeech.LANG_MISSING_DATA ||
            languageResult == TextToSpeech.LANG_NOT_SUPPORTED
        ) {
            return ProfileApplyResult(
                isAvailable = false,
                setLanguageResult = languageResultName(languageResult),
                failureReason = "Locale ${profile.locale.toLanguageTag()} is not supported",
            )
        }

        val selectedVoice = selectVoice(tts, profile)
        val setVoiceResult = if (selectedVoice != null) {
            ttsResultName(tts.setVoice(selectedVoice))
        } else {
            "NO_MATCHING_VOICE"
        }
        tts.setSpeechRate(profile.speechRate)
        tts.setPitch(profile.pitch)
        return ProfileApplyResult(
            isAvailable = true,
            selectedVoiceName = selectedVoice?.name,
            setLanguageResult = languageResultName(languageResult),
            setVoiceResult = setVoiceResult,
        )
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

    private data class ProfileApplyResult(
        val isAvailable: Boolean,
        val selectedVoiceName: String? = null,
        val setLanguageResult: String? = null,
        val setVoiceResult: String? = null,
        val failureReason: String? = null,
    )

    private fun ttsResultName(result: Int): String {
        return when (result) {
            TextToSpeech.SUCCESS -> "SUCCESS"
            TextToSpeech.ERROR -> "ERROR"
            else -> "CODE_$result"
        }
    }

    private fun languageResultName(result: Int): String {
        return when (result) {
            TextToSpeech.LANG_AVAILABLE -> "LANG_AVAILABLE"
            TextToSpeech.LANG_COUNTRY_AVAILABLE -> "LANG_COUNTRY_AVAILABLE"
            TextToSpeech.LANG_COUNTRY_VAR_AVAILABLE -> "LANG_COUNTRY_VAR_AVAILABLE"
            TextToSpeech.LANG_MISSING_DATA -> "LANG_MISSING_DATA"
            TextToSpeech.LANG_NOT_SUPPORTED -> "LANG_NOT_SUPPORTED"
            else -> "LANG_CODE_$result"
        }
    }

    private companion object {
        const val TAG = "AndroidTtsController"
    }
}
