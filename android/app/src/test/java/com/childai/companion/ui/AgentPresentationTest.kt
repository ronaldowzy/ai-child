package com.childai.companion.ui

import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.ui.chat.FoxMood
import com.childai.companion.ui.chat.FoxMotion
import com.childai.companion.ui.chat.toFoxAgentUiState
import com.childai.companion.ui.chat.toVoiceUiState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AgentPresentationTest {
    @Test
    fun mapsReplyEmotionAndMotionToFoxState() {
        val reply = ConversationReply(
            type = "agent_message",
            text = "我在听。",
            voiceEnabled = true,
            audioUrl = null,
            emotion = "thinking",
            agentMotion = "thinking_blink",
        )

        val agent = reply.toFoxAgentUiState()

        assertEquals(FoxMood.Thinking, agent.mood)
        assertEquals(FoxMotion.ThinkingBlink, agent.motion)
        assertEquals("我先想一想。", agent.statusText)
    }

    @Test
    fun keepsVoiceAsReservedWhenBackendHasNoAudioUrl() {
        val reply = ConversationReply(
            type = "agent_message",
            text = "我在听。",
            voiceEnabled = true,
            audioUrl = null,
            emotion = "warm",
            agentMotion = "gentle_idle",
        )

        val voice = reply.toVoiceUiState()

        assertTrue(voice.isVoiceInputReserved)
        assertFalse(voice.isTtsAvailable)
        assertEquals("现在先用文字说", voice.statusText)
    }

    @Test
    fun marksTtsAvailableOnlyWhenAudioUrlIsPresent() {
        val reply = ConversationReply(
            type = "agent_message",
            text = "我在听。",
            voiceEnabled = true,
            audioUrl = "https://example.test/audio.mp3",
            emotion = "warm",
            agentMotion = "gentle_idle",
        )

        val voice = reply.toVoiceUiState()

        assertTrue(voice.isTtsAvailable)
        assertEquals("https://example.test/audio.mp3", voice.audioUrl)
        assertEquals("朗读稍后接上", voice.statusText)
    }
}
