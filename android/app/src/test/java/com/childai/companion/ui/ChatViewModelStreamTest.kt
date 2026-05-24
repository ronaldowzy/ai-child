package com.childai.companion.ui

import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.ui.chat.ChatViewModel
import com.childai.companion.ui.chat.ChildTurnUiPhase
import com.childai.companion.ui.chat.ConversationMessageSender
import com.childai.companion.ui.chat.MessageAuthor
import com.childai.companion.ui.chat.PendingImageContextUiState
import com.childai.companion.ui.chat.QuickActionUi
import com.childai.companion.voice.TtsCallbacks
import com.childai.companion.voice.TtsController
import com.childai.companion.voice.TtsRequest
import com.childai.companion.voice.TtsUiState
import kotlinx.coroutines.Dispatchers
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatViewModelStreamTest {
    @Test
    fun photoQuickActionsDoNotOpenMockAttachmentFlow() {
        val viewModel = ChatViewModel(conversationSender = NoopConversationSender())

        viewModel.onQuickAction(QuickActionUi(id = "share_photo", label = "拍给小白狐看"))

        val state = viewModel.uiState.value
        assertEquals(null, state.mockPhoto)
        assertEquals(MessageAuthor.Agent, state.messages.last().author)
        assertTrue(state.messages.last().text.contains("拍给小白狐看"))
    }

    @Test
    fun textDeltaAppendsToCurrentAgentBubbleAndDoneStopsLoading() {
        val viewModel = ChatViewModel(conversationSender = NoopConversationSender())

        viewModel.applyStreamEvent(streamEvent("session_started"))
        assertEquals(
            ChildTurnUiPhase.Thinking,
            viewModel.uiState.value.interactionPresentation.phase,
        )
        viewModel.applyStreamEvent(streamEvent("text_delta", "delta" to "你好"))
        viewModel.applyStreamEvent(streamEvent("text_delta", "delta" to "呀"))
        viewModel.applyStreamEvent(streamEvent("done"))

        val state = viewModel.uiState.value
        assertFalse(state.isSending)
        assertEquals(MessageAuthor.Agent, state.messages.last().author)
        assertEquals("你好呀", state.messages.last().text)
        assertEquals("你好呀", state.agentReplyText)
    }

    @Test
    fun textFinalReplacesProgressiveText() {
        val viewModel = ChatViewModel(conversationSender = NoopConversationSender())

        viewModel.applyStreamEvent(streamEvent("text_delta", "delta" to "临时"))
        viewModel.applyStreamEvent(streamEvent("text_final", "text" to "最终文本"))

        assertEquals("最终文本", viewModel.uiState.value.messages.last().text)
        assertEquals("最终文本", viewModel.uiState.value.agentReplyText)
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
        assertEquals(
            ChildTurnUiPhase.Ready,
            viewModel.uiState.value.interactionPresentation.phase,
        )
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
    fun ttsErrorDoesNotMixSystemFallbackVoiceWhenNotMuted() {
        val ttsController = RecordingTtsController()
        val viewModel = ChatViewModel(
            conversationSender = NoopConversationSender(),
            ttsController = ttsController,
        )

        viewModel.applyStreamEvent(streamEvent("text_delta", "delta" to "前一句。"))
        viewModel.applyStreamEvent(
            streamEvent(
                "error",
                "stage" to "tts",
                "code" to "tts_timeout",
                "text" to "中间这句也应该被读出来。",
                "sentence_index" to 1,
            ),
        )

        assertTrue(ttsController.requests.isEmpty())
        assertEquals(
            "小白狐这次没有接稳，但已经显示的文字还在这里。",
            viewModel.uiState.value.tts.errorMessage,
        )
    }

    @Test
    fun mutedStateSkipsTtsErrorFallback() {
        val ttsController = RecordingTtsController()
        val viewModel = ChatViewModel(
            conversationSender = NoopConversationSender(),
            ttsController = ttsController,
            initialTtsUiState = TtsUiState(isMuted = true),
        )

        viewModel.applyStreamEvent(
            streamEvent(
                "error",
                "stage" to "tts",
                "code" to "tts_timeout",
                "text" to "静音时不应该 fallback 朗读。",
                "sentence_index" to 1,
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
        assertEquals(
            ChildTurnUiPhase.Speaking,
            viewModel.uiState.value.interactionPresentation.phase,
        )
        viewModel.stopTtsPlayback()

        assertTrue(ttsController.stopCalled)
        assertFalse(viewModel.uiState.value.tts.isSpeaking)
    }

    @Test
    fun streamFailureFallsBackToMessageEndpoint() {
        val sender = StreamFailureConversationSender()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.sendText("我们聊恐龙")

        val state = viewModel.uiState.value
        assertEquals(1, sender.messageCalls)
        assertFalse(state.isSending)
        assertEquals("fallback reply", state.messages.last().text)
    }

    @Test
    fun textAfterImageUploadCarriesPendingAttachmentContext() {
        val sender = AttachmentRecordingConversationSender()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            sendDispatcher = Dispatchers.Unconfined,
        )
        viewModel.renderAgentReply(
            reply = ConversationReply(
                type = "agent_message",
                text = "我看到这张图片了。",
                voiceEnabled = false,
                audioUrl = null,
                emotion = "curious",
                agentMotion = "gentle_idle",
            ),
            uiActions = emptyList(),
            sessionState = ConversationSessionState(
                baseScene = "conversation.open",
                activeScene = "conversation.open",
                needsInput = null,
                requiresParentAttention = false,
            ),
            pendingImageContext = PendingImageContextUiState(
                attachmentId = "att_camera_001",
                summary = "一张测试图片",
                imagePurpose = "share",
                recognizedType = "image_observation",
            ),
        )

        viewModel.sendText("我们继续聊这张图")

        assertEquals(listOf("att_camera_001"), sender.streamAttachments.single())
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

private class StreamFailureConversationSender : ConversationMessageSender {
    var messageCalls = 0

    override suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        timezone: String,
    ): ConversationMessageResponse {
        messageCalls += 1
        return ConversationMessageResponse(
            reply = ConversationReply(
                type = "agent_message",
                text = "fallback reply",
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
    ) {
        onEvent(streamEvent("session_started"))
        onEvent(streamEvent("text_delta", "delta" to "partial"))
        error("stream failed")
    }
}

private class AttachmentRecordingConversationSender : ConversationMessageSender {
    val streamAttachments = mutableListOf<List<String>>()

    override suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        timezone: String,
    ): ConversationMessageResponse {
        error("stream should handle this test")
    }

    override suspend fun streamTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        timezone: String,
        includeTts: Boolean,
        onEvent: (ConversationStreamEvent) -> Unit,
    ) {
        streamAttachments += attachments
        onEvent(streamEvent("done"))
    }
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
