package com.childai.companion.config

import com.childai.companion.BuildConfig

object DevSettings {
    const val CHILD_ID = "child_demo_001"
    const val TIMEZONE = "Asia/Shanghai"
    const val DEV_PARENT_PIN = "0000"
    const val SHOW_SESSION_STATE_DEBUG = false
    const val FOX_ASSET_MODE = "auto"
    const val AUTO_TTS_ENABLED = true
    const val TTS_MUTED = false

    val conversationApiBaseUrl: String = BuildConfig.CONVERSATION_API_BASE_URL
}
