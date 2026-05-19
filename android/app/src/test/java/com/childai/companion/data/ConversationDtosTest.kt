package com.childai.companion.data

import com.childai.companion.data.conversation.ConversationMessageResponse
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ConversationDtosTest {
    @Test
    fun parsesVoiceAndAgentMotionFieldsForFutureFoxAnimation() {
        val response = ConversationMessageResponse.fromJsonString(
            """
            {
              "reply": {
                "type": "agent_message",
                "text": "我在听。",
                "voice_enabled": true,
                "audio_url": null,
                "emotion": "warm",
                "agent_motion": "listening_tail"
              },
              "ui_actions": [],
              "session_state": {
                "base_scene": "daily.after_school_checkin",
                "active_scene": "daily.after_school_checkin",
                "needs_input": "child_choice"
              }
            }
            """.trimIndent(),
        )

        assertTrue(response.reply.voiceEnabled)
        assertNull(response.reply.audioUrl)
        assertEquals("warm", response.reply.emotion)
        assertEquals("listening_tail", response.reply.agentMotion)
    }

    @Test
    fun defaultsVoiceAndAgentMotionForOlderBackendResponses() {
        val response = ConversationMessageResponse.fromJsonString(
            """
            {
              "reply": {
                "type": "agent_message",
                "text": "我在听。",
                "emotion": "warm"
              },
              "ui_actions": [],
              "session_state": {
                "base_scene": "daily.after_school_checkin",
                "active_scene": "daily.after_school_checkin"
              }
            }
            """.trimIndent(),
        )

        assertTrue(response.reply.voiceEnabled)
        assertNull(response.reply.audioUrl)
        assertEquals("gentle_idle", response.reply.agentMotion)
    }
}
