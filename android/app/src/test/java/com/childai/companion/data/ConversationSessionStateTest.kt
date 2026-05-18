package com.childai.companion.data

import com.childai.companion.data.conversation.ConversationSessionState
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ConversationSessionStateTest {
    @Test
    fun displayTextIncludesActiveSceneAndNeededInput() {
        val state = ConversationSessionState(
            baseScene = "daily.after_school_checkin",
            activeScene = "learning.homework_help",
            needsInput = "problem_content",
            requiresParentAttention = false,
        )

        val text = state.toDisplayText()

        assertTrue(text.contains("active=learning.homework_help"))
        assertTrue(text.contains("needs=problem_content"))
        assertFalse(text.contains("parent_attention=true"))
    }

    @Test
    fun displayTextMarksParentAttentionWhenRequired() {
        val state = ConversationSessionState(
            baseScene = "safety.guardian",
            activeScene = "safety.guardian",
            needsInput = "trusted_adult_support",
            requiresParentAttention = true,
        )

        assertTrue(state.toDisplayText().contains("parent_attention=true"))
    }
}
