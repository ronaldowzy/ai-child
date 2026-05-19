package com.childai.companion.voice

import com.childai.companion.config.DevSettings

data class TtsUiState(
    val isAutoReadEnabled: Boolean = DevSettings.AUTO_TTS_ENABLED,
    val isMuted: Boolean = DevSettings.TTS_MUTED,
    val isSpeaking: Boolean = false,
    val isAvailable: Boolean = true,
    val errorMessage: String? = null,
) {
    val statusText: String
        get() = when {
            errorMessage != null -> errorMessage
            isSpeaking -> "小白狐正在说话。"
            isMuted -> "朗读已静音，文字还会显示。"
            !isAutoReadEnabled -> "自动朗读已关闭。"
            isAvailable -> "小白狐会读出自己的回复。"
            else -> TtsController.UNAVAILABLE_MESSAGE
        }
}
