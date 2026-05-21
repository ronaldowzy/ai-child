package com.childai.companion.ui

import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.ui.chat.ChatViewModel
import com.childai.companion.ui.chat.ConversationMessageSender
import com.childai.companion.ui.chat.MessageAuthor
import com.childai.companion.voice.TtsCallbacks
import com.childai.companion.voice.TtsController
import com.childai.companion.voice.TtsRequest
import com.childai.companion.voice.TtsUiState
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatViewModelStreamTest {
    @Test
    fun textDeltaAppendsToCurrentAgentBubbleAndDoneStopsLoading() {
        val viewModel = ChatViewModel(conversationSender = NoopConversationSender())

        viewModel.applyStreamEvent(streamEvent("session_started"))
        viewModel.applyStreamEvent(streamEvent("text_delta", "delta" to "你好"))
        viewModel.applyStreamEvent(streamEvent("text_delta", "delta" to "呀"))
        viewModel.applyStreamEvent(streamEvent("done"))

        val state = viewModel.uiState.value
        assertFalse(state.isSending)
        assertEquals(MessageAuthor.Agent, state.messages.last().author)
        assertEquals("你好呀", state.messages.last().text)
    }

    @Test
    fun textFinalReplacesProgressiveText() {
        val viewModel = ChatViewModel(conversationSender = NoopConversationSender())

        viewModel.applyStreamEvent(streamEvent("text_delta", "delta" to "临时"))
        viewModel.applyStreamEvent(streamEvent("text_final", "text" to "最终文本"))

        assertEquals("最终文本", viewModel.uiState.value.messages.last().text)
    }

    @Test
    fun audioReadyUsesQueueWhenNotMuted() {
        val ttsController = RecordingTtsController()
        val viewModel = ChatViewModel(
            conversationSender = NoopConversationSender(),
            ttsController = ttsController,
        )

        viewModel.applyStreamEvent(
            streamEvent(
                "audio_ready",
                "audioUrl" to "/media/tts/segment.wav",
                "text" to "你好",
                "index" to 0,
            ),
        )

        assertEquals(1, ttsController.requests.size)
        assertEquals("/media/tts/segment.wav", ttsController.requests.first().audioUrl)
        assertEquals("你好", ttsController.requests.first().text)
    }

    @Test
    fun mutedStateSkipsAudioQueue() {
        val ttsController = RecordingTtsController()
        val viewModel = ChatViewModel(
            conversationSender = NoopConversationSender(),
            ttsController = ttsController,
            initialTtsUiState = TtsUiState(isMuted = true),
        )

        viewModel.applyStreamEvent(
            streamEvent(
                "audio_ready",
                "audioUrl" to "/media/tts/segment.wav",
                "text" to "你好",
                "index" to 0,
            ),
        )

        assertTrue(ttsController.requests.isEmpty())
    }

    @Test
    fun stopClearsStreamingAudioQueue() {
        val ttsController = RecordingTtsController(autoComplete = false)
        val viewModel = ChatViewModel(
            conversationSender = NoopConversationSender(),
            ttsController = ttsController,
        )

        viewModel.applyStreamEvent(
            streamEvent(
                "audio_ready",
                "audioUrl" to "/media/tts/segment.wav",
                "text" to "你好",
                "index" to 0,
            ),
        )
        viewModel.stopTtsPlayback()

        assertTrue(ttsController.stopCalled)
        assertFalse(viewModel.uiState.value.tts.isSpeaking)
    }
}

private fun streamEvent(type: String, vararg payloadValues: Pair<String, Any>): ConversationStreamEvent {
    val payload = JSONObject()
    payloadValues.forEach { (key, value) -> payload.put(key, value) }
    return ConversationStreamEvent(type = type, payload = payload)
}

private class NoopConversationSender : ConversationMessageSender {
    override suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        timezone: String,
    ): ConversationMessageResponse {
        return ConversationMessageResponse(
            reply = ConversationReply(
                type = "agent_message",
                text = "fallback",
                voiceEnabled = false,
                audioUrl = null,
                emotion = "warm",
                agentMotion = "gentle_idle",
            ),
            uiActions = emptyList(),
            sessionState = ConversationSessionState(
                baseScene = "conversation.open",
                activeScene = "conversation.open",
                needsInput = null,
                requiresParentAttention = false,
            ),
        )
    }

    override suspend fun streamTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        timezone: String,
        includeTts: Boolean,
        onEvent: (ConversationStreamEvent) -> Unit,
    ) = Unit
}

private class RecordingTtsController(
    private val autoComplete: Boolean = true,
) : TtsController {
    val requests = mutableListOf<TtsRequest>()
    var stopCalled = false

    override fun speak(request: TtsRequest, callbacks: TtsCallbacks): Boolean {
        requests.add(request)
        callbacks.onStart()
        if (autoComplete) {
            callbacks.onDone()
        }
        return true
    }

    override fun stop() {
        stopCalled = true
    }

    override fun shutdown() = Unit
}
