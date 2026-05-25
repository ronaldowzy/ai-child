package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.voice.TtsCallbacks
import com.childai.companion.voice.TtsController
import com.childai.companion.voice.TtsRequest
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.asCoroutineDispatcher
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
    fun openingTextWithoutAudioDoesNotUseLocalTtsFallback() {
        val sender = OpeningSender(
            openingResponse = response(
                text = "豆豆，我准备好啦。",
                audioUrl = null,
                voiceEnabled = false,
            ),
        )
        val tts = RecordingTtsController()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            ttsController = tts,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.requestOpeningGreeting()

        assertEquals("豆豆，我准备好啦。", viewModel.uiState.value.messages.first().text)
        assertEquals(0, tts.requests.size)
    }

    @Test
    fun lateOpeningAfterChildInputIsSuppressedAndDoesNotPlayAudio() {
        val sender = BlockingOpeningSender(
            openingResponse = response(
                text = "豆豆，迟到的开场。",
                audioUrl = "/media/tts/late-opening.wav",
            ),
        )
        val tts = RecordingTtsController()
        val dispatcher = Executors.newSingleThreadExecutor().asCoroutineDispatcher()
        try {
            val viewModel = ChatViewModel(
                conversationSender = sender,
                ttsController = tts,
                sendDispatcher = dispatcher,
            )

            viewModel.requestOpeningGreeting()
            assertTrue(sender.openingStarted.await(1, TimeUnit.SECONDS))
            viewModel.sendText("我先说")
            sender.releaseOpening()
            assertTrue(sender.sendStarted.await(1, TimeUnit.SECONDS))

            assertEquals(listOf("我先说"), sender.sentTexts)
            assertTrue(viewModel.uiState.value.messages.none { it.text == "豆豆，迟到的开场。" })
            assertEquals(0, tts.requests.size)
        } finally {
            dispatcher.close()
        }
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

private class BlockingOpeningSender(
    private val openingResponse: ConversationMessageResponse,
) : ConversationMessageSender {
    val openingStarted = CountDownLatch(1)
    val sendStarted = CountDownLatch(1)
    private val releaseOpening = CountDownLatch(1)
    val sentTexts = mutableListOf<String>()

    fun releaseOpening() {
        releaseOpening.countDown()
    }

    override suspend fun requestOpening(
        childId: String,
        sessionId: String,
        timezone: String,
    ): ConversationMessageResponse {
        openingStarted.countDown()
        assertTrue(releaseOpening.await(1, TimeUnit.SECONDS))
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
        sendStarted.countDown()
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
    voiceEnabled: Boolean = audioUrl != null,
): ConversationMessageResponse {
    return ConversationMessageResponse(
        reply = ConversationReply(
            type = "agent_message",
            text = text,
            voiceEnabled = voiceEnabled,
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
