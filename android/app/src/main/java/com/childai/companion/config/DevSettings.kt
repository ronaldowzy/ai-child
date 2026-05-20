package com.childai.companion.config

import com.childai.companion.BuildConfig

object DevSettings {
    const val CHILD_ID = "child_demo_001"
    const val TIMEZONE = "Asia/Shanghai"
    const val DEV_PARENT_PIN = "0000"
    const val SHOW_SESSION_STATE_DEBUG = false
    const val FOX_ASSET_MODE = "auto"
    const val FOX_RENDER_MODE = "animation_v1"
    const val FOX_ANIMATION_ENABLED = true
    const val FOX_ANIMATION_PRELOAD_ENABLED = true
    const val FOX_ANIMATION_LOW_PERFORMANCE_MODE = false
    const val SHOW_MASCOT_DEBUG_SWITCHER = false
    const val AUTO_TTS_ENABLED = true
    const val TTS_MUTED = false
    const val SHOW_TTS_DIAGNOSTICS = true

    val conversationApiBaseUrl: String = BuildConfig.CONVERSATION_API_BASE_URL
}
