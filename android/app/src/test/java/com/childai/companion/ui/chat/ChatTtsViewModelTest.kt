package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.voice.TtsCallbacks
import com.childai.companion.voice.TtsController
import com.childai.companion.voice.TtsRequest
import com.childai.companion.voice.TtsUiState
import com.childai.companion.voice.VoiceProfile
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatTtsViewModelTest {
    @Test
    fun doesNotSpeakWhenReplyVoiceIsDisabled() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.renderAgentReply(response(reply(voiceEnabled = false)))

        assertTrue(fakeTts.requests.isEmpty())
        assertFalse(viewModel.uiState.value.tts.isSpeaking)
    }

    @Test
    fun doesNotSpeakWhenAutoReadIsDisabled() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(
            ttsController = fakeTts,
            initialTtsUiState = TtsUiState(isAutoReadEnabled = false),
        )

        viewModel.renderAgentReply(response(reply()))

        assertTrue(fakeTts.requests.isEmpty())
        assertFalse(viewModel.uiState.value.tts.isSpeaking)
    }

    @Test
    fun autoReadsAgentReplyAndSwitchesFoxToSpeaking() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.renderAgentReply(response(reply()))

        assertEquals(listOf("我在这里。"), fakeTts.requests.map { it.text })
        assertTrue(viewModel.uiState.value.tts.isSpeaking)
        assertEquals(FoxMotion.Speaking, viewModel.uiState.value.agent.motion)
    }

    @Test
    fun childMessageDoesNotTriggerTts() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.recordChildMessage("我想聊恐龙")

        assertTrue(fakeTts.requests.isEmpty())
        assertFalse(viewModel.uiState.value.tts.isSpeaking)
    }

    @Test
    fun mutedStatePreventsAutoRead() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.toggleTtsMuted()
        viewModel.renderAgentReply(response(reply()))

        assertTrue(fakeTts.requests.isEmpty())
        assertTrue(viewModel.uiState.value.tts.isMuted)
        assertFalse(viewModel.uiState.value.tts.isSpeaking)
    }

    @Test
    fun newAgentReplyStopsPreviousPlaybackBeforeSpeaking() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.renderAgentReply(response(reply()))
        val stopCountAfterFirstReply = fakeTts.stopCount
        viewModel.renderAgentReply(response(reply(text = "新的回复。")))

        assertEquals(stopCountAfterFirstReply + 1, fakeTts.stopCount)
        assertEquals(listOf("我在这里。", "新的回复。"), fakeTts.requests.map { it.text })
        assertTrue(viewModel.uiState.value.tts.isSpeaking)
    }

    @Test
    fun stopRestoresBaseFoxState() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.renderAgentReply(
            response(
                reply(
                    emotion = "thinking",
                    agentMotion = "thinking_blink",
                ),
            ),
        )
        assertEquals(FoxMotion.Speaking, viewModel.uiState.value.agent.motion)
        val stopCountAfterAutoStart = fakeTts.stopCount

        viewModel.stopTtsPlayback()

        assertEquals(stopCountAfterAutoStart + 1, fakeTts.stopCount)
        assertFalse(viewModel.uiState.value.tts.isSpeaking)
        assertEquals(FoxMood.Thinking, viewModel.uiState.value.agent.mood)
        assertEquals(FoxMotion.ThinkingBlink, viewModel.uiState.value.agent.motion)
    }

    @Test
    fun finishRestoresBaseFoxState() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.renderAgentReply(
            response(
                reply(
                    emotion = "encouraging",
                    agentMotion = "celebrate_small",
                ),
            ),
        )
        fakeTts.finish()

        assertFalse(viewModel.uiState.value.tts.isSpeaking)
        assertEquals(FoxMood.Encouraging, viewModel.uiState.value.agent.mood)
        assertEquals(FoxMotion.CelebrateSmall, viewModel.uiState.value.agent.motion)
    }

    @Test
    fun ttsUnavailableDoesNotCrashAndShowsGentleError() {
        val fakeTts = FakeTtsController(isAvailable = false)
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.renderAgentReply(response(reply()))

        assertFalse(viewModel.uiState.value.tts.isSpeaking)
        assertFalse(viewModel.uiState.value.tts.isAvailable)
        assertEquals(
            TtsController.UNAVAILABLE_MESSAGE,
            viewModel.uiState.value.tts.errorMessage,
        )
    }

    @Test
    fun voiceProfileDefaultUsesGentleChineseSettings() {
        val profile = VoiceProfile.default()

        assertEquals("zh-CN", profile.locale.toLanguageTag())
        assertTrue(profile.speechRate in 0.88f..0.95f)
        assertTrue(profile.pitch in 1.05f..1.15f)
        assertEquals(null, profile.preferredVoiceName)
    }

    private fun response(reply: ConversationReply): ConversationMessageResponse {
        return ConversationMessageResponse(
            reply = reply,
            uiActions = emptyList(),
            sessionState = ConversationSessionState(
                baseScene = "daily.after_school_checkin",
                activeScene = "daily.after_school_checkin",
                needsInput = null,
                requiresParentAttention = false,
            ),
        )
    }

    private fun reply(
        voiceEnabled: Boolean = true,
        text: String = "我在这里。",
        emotion: String = "warm",
        agentMotion: String = "gentle_idle",
    ): ConversationReply {
        return ConversationReply(
            type = "agent_message",
            text = text,
            voiceEnabled = voiceEnabled,
            audioUrl = null,
            emotion = emotion,
            agentMotion = agentMotion,
        )
    }

    private class FakeTtsController(
        private val isAvailable: Boolean = true,
    ) : TtsController {
        val requests = mutableListOf<TtsRequest>()
        var stopCount = 0
        private var callbacks: TtsCallbacks? = null

        override fun speak(request: TtsRequest, callbacks: TtsCallbacks): Boolean {
            if (!isAvailable) {
                callbacks.onError(TtsController.UNAVAILABLE_MESSAGE)
                return false
            }
            requests += request
            this.callbacks = callbacks
            callbacks.onStart()
            return true
        }

        override fun stop() {
            stopCount += 1
            callbacks = null
        }

        override fun shutdown() {
            callbacks = null
        }

        fun finish() {
            callbacks?.onDone()
        }
    }
}
