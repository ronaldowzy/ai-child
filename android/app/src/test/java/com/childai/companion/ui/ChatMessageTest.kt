package com.childai.companion.ui

import com.childai.companion.ui.chat.MessageAuthor
import com.childai.companion.ui.chat.initialChatMessages
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatMessageTest {
    @Test
    fun initialMessagesStartFromAgent() {
        val messages = initialChatMessages()

        assertTrue(messages.isNotEmpty())
        assertEquals(MessageAuthor.Agent, messages.first().author)
    }

    @Test
    fun initialMessagesAvoidUnsafeSecretLanguage() {
        val text = initialChatMessages().joinToString(separator = "\n") { it.text }

        assertFalse(text.contains("保密"))
        assertFalse(text.contains("别告诉"))
        assertFalse(text.contains("只有我懂你"))
    }
}
