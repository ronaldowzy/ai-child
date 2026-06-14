package com.childai.companion.config

import com.childai.companion.BuildConfig

object DevSettings {
    const val CHILD_ID = "child_demo_001"
    const val TIMEZONE = "Asia/Shanghai"
    const val SHOW_SESSION_STATE_DEBUG = false
    const val SHOW_HOUSE_OBJECT_DEBUG_TOOLS = true
    const val FOX_ASSET_MODE = "auto"
    const val FOX_RENDER_MODE = "animation_v1"
    const val FOX_ANIMATION_ENABLED = true
    const val FOX_ANIMATION_PRELOAD_ENABLED = true
    const val FOX_ANIMATION_LOW_PERFORMANCE_MODE = false
    const val SHOW_MASCOT_DEBUG_SWITCHER = false
    const val AUTO_TTS_ENABLED = true
    const val TTS_MUTED = false
    const val SHOW_TTS_DIAGNOSTICS = true
    const val USE_STREAMING_CONVERSATION = true
    const val CHILD_VOICE_FIRST_MODE = true
    const val VOICE_CONFIRM_BEFORE_SEND = false
    const val SHOW_TEXT_INPUT_FOR_CHILD = false
    const val NATURAL_WAITING_ENABLED = true
    const val NATURAL_WAITING_TIMEOUT_MS = 5_000L
    const val STRANGE_DOOR_AUTO_ENTRY_ENABLED = false
    const val LANGUAGE_GAME_AUTO_PROMPT_ENABLED = false
    const val INTERACTION_TRACE_ENABLED = true

    val conversationApiBaseUrl: String = BuildConfig.CONVERSATION_API_BASE_URL
    val debugToolsToken: String = BuildConfig.DEBUG_TOOLS_TOKEN
    val houseObjectDebugToolsEnabled: Boolean =
        BuildConfig.DEBUG && SHOW_HOUSE_OBJECT_DEBUG_TOOLS
}
