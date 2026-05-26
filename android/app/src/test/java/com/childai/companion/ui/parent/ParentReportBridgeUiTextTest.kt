package com.childai.companion.ui.parent

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class ParentReportBridgeUiTextTest {
    @Test
    fun bridgeSectionTitleIsTopLevelFamilyCopy() {
        assertEquals("今晚可以这样聊", PARENT_REPORT_BRIDGE_SECTION_TITLE)
    }

    @Test
    fun topicSectionTitleFocusesOnConversationContent() {
        assertEquals("今天聊了什么", PARENT_REPORT_TOPIC_SECTION_TITLE)
    }

    @Test
    fun failureMessageDoesNotExposeEngineeringWords() {
        val message = PARENT_REPORT_LOAD_FAILURE_MESSAGE

        assertEquals("今天的小结还没准备好，请稍后再试。", message)
        assertFalse(message.contains("backend", ignoreCase = true))
        assertFalse(message.contains("model", ignoreCase = true))
        assertFalse(message.contains("provider", ignoreCase = true))
        assertFalse(message.contains("config", ignoreCase = true))
        assertFalse(message.contains("后端"))
        assertFalse(message.contains("模型"))
        assertFalse(message.contains("配置"))
    }
}
