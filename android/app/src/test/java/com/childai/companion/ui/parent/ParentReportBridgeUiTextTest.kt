package com.childai.companion.ui.parent

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class ParentReportBridgeUiTextTest {
    @Test
    fun timeoutMessageIsFamilyFriendly() {
        assertEquals("今天的小结还没整理好，可以稍后再看。", PARENT_REPORT_TIMEOUT_MESSAGE)
    }

    @Test
    fun failedMessageIsFamilyFriendly() {
        assertEquals("这次没有整理成功，可以再试一次。", PARENT_REPORT_FAILED_MESSAGE)
    }

    @Test
    fun insufficientMessageIsFamilyFriendly() {
        assertEquals("今天聊得还不多，小结会短一点。", PARENT_REPORT_INSUFFICIENT_MESSAGE)
    }

    @Test
    fun noMessageExposesEngineeringWords() {
        val messages = listOf(
            PARENT_REPORT_TIMEOUT_MESSAGE,
            PARENT_REPORT_FAILED_MESSAGE,
            PARENT_REPORT_INSUFFICIENT_MESSAGE,
        )
        for (message in messages) {
            assertFalse(message.contains("backend", ignoreCase = true))
            assertFalse(message.contains("model", ignoreCase = true))
            assertFalse(message.contains("provider", ignoreCase = true))
            assertFalse(message.contains("config", ignoreCase = true))
            assertFalse(message.contains("后端"))
            assertFalse(message.contains("模型"))
            assertFalse(message.contains("配置"))
            assertFalse(message.contains("接口"))
            assertFalse(message.contains("超时"))
            assertFalse(message.contains("生成失败"))
        }
    }
}
