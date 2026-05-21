package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.voice.TtsCallbacks
import com.childai.companion.voice.TtsController
import com.childai.companion.voice.TtsRequest
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatViewModelOpeningTest {
    @Test
    fun openingSuccessReplacesInitialAgentMessage() {
        val sender = OpeningSender()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.requestOpeningGreeting()

        assertEquals(1, sender.openingCalls)
        assertEquals("豆豆，回来啦。", viewModel.uiState.value.messages.first().text)
        assertEquals(1, viewModel.uiState.value.messages.size)
    }

    @Test
    fun openingAudioUrlAutoPlaysWhenAvailable() {
        val sender = OpeningSender(
            openingResponse = response(text = "豆豆，我准备好啦。", audioUrl = "/media/tts/opening.wav"),
        )
        val tts = RecordingTtsController()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            ttsController = tts,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.requestOpeningGreeting()

        assertEquals(1, tts.requests.size)
        assertEquals("/media/tts/opening.wav", tts.requests.first().audioUrl)
    }

    @Test
    fun openingFailureDoesNotBlockVoiceOrSending() {
        val sender = OpeningSender(failOpening = true)
        val viewModel = ChatViewModel(
            conversationSender = sender,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.requestOpeningGreeting()
        viewModel.sendText("我想聊恐龙")

        assertEquals(listOf("我想聊恐龙"), sender.sentTexts)
        assertTrue(viewModel.uiState.value.messages.any { it.author == MessageAuthor.Child })
    }

    @Test
    fun childInputBeforeOpeningPreventsOpeningFromOverwritingConversation() {
        val sender = OpeningSender()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.sendText("我先说")
        viewModel.requestOpeningGreeting()

        assertEquals("我先说", viewModel.uiState.value.messages[1].text)
        assertTrue(viewModel.uiState.value.messages.none { it.text == "豆豆，回来啦。" })
    }

    @Test
    fun openingIsRequestedOnlyOncePerViewModelSession() {
        val sender = OpeningSender()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.requestOpeningGreeting()
        viewModel.requestOpeningGreeting()

        assertEquals(1, sender.openingCalls)
    }
}

private class OpeningSender(
    private val openingResponse: ConversationMessageResponse = response("豆豆，回来啦。"),
    private val failOpening: Boolean = false,
) : ConversationMessageSender {
    var openingCalls = 0
    val sentTexts = mutableListOf<String>()

    override suspend fun requestOpening(
        childId: String,
        sessionId: String,
        timezone: String,
    ): ConversationMessageResponse {
        openingCalls += 1
        if (failOpening) error("opening failed")
        return openingResponse
    }

    override suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        timezone: String,
    ): ConversationMessageResponse {
        sentTexts += text
        return response("收到。", audioUrl = null)
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

private class RecordingTtsController : TtsController {
    val requests = mutableListOf<TtsRequest>()

    override fun speak(request: TtsRequest, callbacks: TtsCallbacks): Boolean {
        requests += request
        callbacks.onStart()
        callbacks.onDone()
        return true
    }

    override fun stop() = Unit

    override fun shutdown() = Unit
}

private fun response(
    text: String,
    audioUrl: String? = null,
): ConversationMessageResponse {
    return ConversationMessageResponse(
        reply = ConversationReply(
            type = "agent_message",
            text = text,
            voiceEnabled = audioUrl != null,
            audioUrl = audioUrl,
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
