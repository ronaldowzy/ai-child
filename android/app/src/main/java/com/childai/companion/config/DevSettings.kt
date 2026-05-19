package com.childai.companion.config

import com.childai.companion.BuildConfig

object DevSettings {
    const val CHILD_ID = "child_demo_001"
    const val TIMEZONE = "Asia/Shanghai"
    const val DEV_PARENT_PIN = "0000"

    val conversationApiBaseUrl: String = BuildConfig.CONVERSATION_API_BASE_URL
}
