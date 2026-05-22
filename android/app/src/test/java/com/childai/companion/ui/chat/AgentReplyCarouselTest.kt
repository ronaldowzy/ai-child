package com.childai.companion.ui.chat

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class AgentReplyCarouselTest {
    @Test
    fun splitsLongAgentReplyIntoReadableSegments() {
        val segments = agentReplyCarouselSegments(
            text = "晚上好呀，今天过得怎么样？你今天有没有遇到什么想跟我说的小事？我们可以慢慢聊。",
            maxChars = 24,
        )

        assertTrue(segments.size > 1)
        assertTrue(segments.all { it.length <= 24 })
        assertEquals("晚上好呀，今天过得怎么样？", segments.first())
    }

    @Test
    fun blankReplyReturnsNoSegments() {
        assertEquals(emptyList<String>(), agentReplyCarouselSegments("   "))
    }
}
