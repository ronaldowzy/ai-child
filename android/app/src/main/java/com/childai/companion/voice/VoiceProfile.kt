package com.childai.companion.voice

import java.util.Locale

data class VoiceProfile(
    val preferredVoiceName: String? = null,
    val locale: Locale = Locale.SIMPLIFIED_CHINESE,
    val speechRate: Float = DEFAULT_SPEECH_RATE,
    val pitch: Float = DEFAULT_PITCH,
) {
    companion object {
        const val DEFAULT_SPEECH_RATE = 0.9f
        const val DEFAULT_PITCH = 1.08f

        fun default(): VoiceProfile = VoiceProfile()
    }
}
