package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.data.tts.XiaobaohuTtsAudioGenerator
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoMethod
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoState
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoSnapshot
import com.childai.companion.ui.chat.strangedoor.StrangeDoorMechanismType
import com.childai.companion.ui.chat.strangedoor.StrangeDoorState
import com.childai.companion.ui.chat.strangedoor.toHomeEventUiModel
import com.childai.companion.voice.TtsCallbacks
import com.childai.companion.voice.TtsController
import com.childai.companion.voice.TtsRequest
import com.childai.companion.voice.SpeechInputController
import com.childai.companion.voice.SpeechInputResult
import java.io.File
import java.nio.file.Files
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatViewModelStrangeDoorDemoTest {
    @Test
    fun openingGreetingIsDeferredWhileStrangeDoorDemoIsActive() {
        val sender = StrangeDoorDemoSender()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.requestOpeningGreeting()

        assertEquals(0, sender.openingCalls)
        assertNotNull(viewModel.uiState.value.strangeDoorDemo)

        viewModel.exitStrangeDoorDemoAndRequestOpening()

        assertEquals(1, sender.openingCalls)
        assertEquals("豆豆，回来啦。", viewModel.uiState.value.messages.first().text)
        assertEquals(null, viewModel.uiState.value.strangeDoorDemo)
    }

    @Test
    fun exitDemoRestoresOpeningAndPreventsAutomaticReactivationInCurrentLifecycle() {
        val sender = StrangeDoorDemoSender()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.exitStrangeDoorDemoAndRequestOpening()
        viewModel.activateStrangeDoorDemo()

        assertEquals(1, sender.openingCalls)
        assertNull(viewModel.uiState.value.strangeDoorDemo)
        assertTrue(strangeDoorShouldShowNormalInputBar(viewModel.uiState.value))
    }

    @Test
    fun activatingDemoStartsAtChoosingMethodWithClosedDoor() {
        val viewModel = ChatViewModel(
            conversationSender = StrangeDoorDemoSender(),
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.activateStrangeDoorDemo()

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorDemoState.ChoosingMethod, snapshot.demoState)
        assertEquals(StrangeDoorState.Closed, snapshot.doorState)
        assertEquals(StrangeDoorMechanismType.Round, snapshot.mechanismType)
        assertFalse(strangeDoorShouldShowNormalInputBar(viewModel.uiState.value))
    }

    @Test
    fun choosingPhotoAndRiddleUpdateOnlyLocalDemoState() {
        val sender = StrangeDoorDemoSender()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()

        val photoSnapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorDemoState.PhotoPrompt, photoSnapshot.demoState)
        assertEquals(StrangeDoorDemoMethod.Photo, photoSnapshot.lastMethod)
        assertEquals(0, sender.sentTexts.size)
        assertEquals(0, sender.openingCalls)

        viewModel.returnToStrangeDoorMethodChoice()
        viewModel.chooseStrangeDoorRiddleMethod()

        val riddleSnapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorDemoState.RiddlePrompt, riddleSnapshot.demoState)
        assertEquals(StrangeDoorDemoMethod.Riddle, riddleSnapshot.lastMethod)
        assertTrue(viewModel.uiState.value.quickActions.isEmpty())
    }

    @Test
    fun casualChatTextDuringRiddlePromptExitsDemoAndSendsConversation() {
        val sender = StrangeDoorDemoSender()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorRiddleMethod()
        viewModel.sendText("聊变形金刚")

        assertNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(listOf("聊变形金刚"), sender.sentTexts)
    }

    @Test
    fun storyRequestDuringRiddlePromptExitsDemoAndSendsConversation() {
        val sender = StrangeDoorDemoSender()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorRiddleMethod()
        viewModel.sendText("你给我讲个故事")

        assertNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(listOf("你给我讲个故事"), sender.sentTexts)
    }

    @Test
    fun storyAsrDuringRiddlePromptExitsDemoAndSendsConversation() {
        val sender = StrangeDoorDemoSender()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            speechInputController = StrangeDoorDemoSpeechInputController(
                SpeechInputResult.Transcript("你给我讲个故事"),
            ),
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorRiddleMethod()
        viewModel.startVoiceRecording(tempDir())
        viewModel.stopVoiceRecordingAndUpload()

        assertNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(listOf("你给我讲个故事"), sender.sentTexts)
    }

    @Test
    fun strangeDoorAutoEntryIsOneShotByLocalFlag() {
        assertTrue(
            shouldAutoActivateStrangeDoorOnChatEntry(
                hasShownBefore = false,
                autoEntryEnabled = true,
            ),
        )
        assertFalse(
            shouldAutoActivateStrangeDoorOnChatEntry(
                hasShownBefore = true,
                autoEntryEnabled = true,
            ),
        )
        assertFalse(
            shouldAutoActivateStrangeDoorOnChatEntry(
                hasShownBefore = false,
                autoEntryEnabled = false,
            ),
        )
    }

    @Test
    fun strangeDoorActionLayoutUsesTwoColumnsForFourButtonsOnPhoneWidth() {
        assertEquals(2, strangeDoorActionColumnCount(actionCount = 4, availableWidthDp = 390f))
        assertEquals(2, strangeDoorActionColumnCount(actionCount = 3, availableWidthDp = 390f))
        assertEquals(2, strangeDoorActionColumnCount(actionCount = 2, availableWidthDp = 390f))
        assertEquals(1, strangeDoorActionColumnCount(actionCount = 4, availableWidthDp = 320f))
    }

    @Test
    fun completedActionLabelsAreSplitAcrossRowsOnPhoneWidth() {
        val actions = StrangeDoorDemoSnapshot(
            demoState = StrangeDoorDemoState.Completed,
            doorState = StrangeDoorState.Open,
        ).toHomeEventUiModel().actions

        val rows = strangeDoorActionRows(actions = actions, availableWidthDp = 390f)

        assertEquals(
            listOf(
                listOf("再玩一次", "再找一个"),
                listOf("去小展台看看", "先聊别的"),
            ),
            rows.map { row -> row.map { it.label } },
        )
    }

    @Test
    fun replayDemoResetsToChoosingMethodAndClosedDoor() {
        val viewModel = ChatViewModel(
            conversationSender = StrangeDoorDemoSender(),
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorRiddleMethod()
        viewModel.answerStrangeDoorRiddle("水")
        val completed = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorDemoState.Completed, completed.demoState)
        assertEquals(StrangeDoorState.Open, completed.doorState)
        assertEquals(1, completed.attemptsCount)

        viewModel.replayStrangeDoorDemo()

        val replayed = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorDemoState.ChoosingMethod, replayed.demoState)
        assertEquals(StrangeDoorState.Closed, replayed.doorState)
        assertEquals(StrangeDoorMechanismType.Soft, replayed.mechanismType)
        assertEquals(0, replayed.attemptsCount)
        assertNull(replayed.lastPhotoTransform)
        assertNull(replayed.lastRiddleEvaluation)
        assertNull(replayed.lastPhotoMessageId)
        assertNull(replayed.showcaseSavedName)
    }

    @Test
    fun strangeDoorLocalStatesUseExistingTtsForVisibleCopy() {
        val feedbackTts = StrangeDoorDemoFeedbackTts()
        val tts = StrangeDoorDemoRecordingTts()
        val viewModel = ChatViewModel(
            conversationSender = StrangeDoorDemoSender(),
            feedbackTtsAudioGenerator = feedbackTts,
            ttsController = tts,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorRiddleMethod()

        assertEquals(2, feedbackTts.requestedTexts.size)
        assertTrue(feedbackTts.requestedTexts[0].contains("奇怪小门挡住了小白狐"))
        assertTrue(feedbackTts.requestedTexts[0].contains("我被这扇奇怪小门挡住了"))
        assertFalse(feedbackTts.requestedTexts[1].contains("奇怪小门挡住了小白狐"))
        assertTrue(feedbackTts.requestedTexts[1].contains("什么东西越洗越脏？"))
        assertEquals(feedbackTts.requestedTexts, tts.requests.map { it.text })
    }

    @Test
    fun strangeDoorLocalTtsRetriesOnceWhenAudioGenerationFails() {
        val feedbackTts = StrangeDoorDemoFailOnceFeedbackTts()
        val tts = StrangeDoorDemoRecordingTts()
        val viewModel = ChatViewModel(
            conversationSender = StrangeDoorDemoSender(),
            feedbackTtsAudioGenerator = feedbackTts,
            ttsController = tts,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.activateStrangeDoorDemo()

        assertEquals(2, feedbackTts.attempts)
        assertEquals(1, tts.requests.size)
        assertTrue(tts.requests.first().text.contains("我被这扇奇怪小门挡住了"))
    }
}

private fun tempDir(): File {
    return Files.createTempDirectory("strange-door-demo-test").toFile()
}

private class StrangeDoorDemoSpeechInputController(
    private val result: SpeechInputResult,
) : SpeechInputController {
    override suspend fun startRecording() = Unit

    override suspend fun stopAndTranscribe(
        childId: String,
        sessionId: String,
        timezone: String,
    ): SpeechInputResult {
        return result
    }

    override suspend fun cancel() = Unit

    override fun shutdown() = Unit
}

private class StrangeDoorDemoSender : ConversationMessageSender {
    var openingCalls = 0
    val sentTexts = mutableListOf<String>()

    override suspend fun requestOpening(
        childId: String,
        sessionId: String,
        timezone: String,
    ): ConversationMessageResponse {
        openingCalls += 1
        return strangeDoorDemoResponse("豆豆，回来啦。")
    }

    override suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        quickActionId: String?,
        timezone: String,
    ): ConversationMessageResponse {
        sentTexts += text
        return strangeDoorDemoResponse("收到。")
    }

    override suspend fun streamTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        quickActionId: String?,
        timezone: String,
        includeTts: Boolean,
        onEvent: (ConversationStreamEvent) -> Unit,
    ) = Unit
}

private fun strangeDoorDemoResponse(text: String): ConversationMessageResponse {
    return ConversationMessageResponse(
        reply = ConversationReply(
            type = "agent_message",
            text = text,
            voiceEnabled = false,
            audioUrl = null,
            emotion = "warm",
            agentMotion = "gentle_idle",
        ),
        sessionState = ConversationSessionState(
            baseScene = "conversation.open",
            activeScene = "conversation.open",
            needsInput = null,
            requiresParentAttention = false,
        ),
        uiActions = emptyList(),
    )
}

private class StrangeDoorDemoFeedbackTts : XiaobaohuTtsAudioGenerator {
    val requestedTexts = mutableListOf<String>()

    override suspend fun generateAudioUrl(text: String, emotion: String): String? {
        requestedTexts += text
        return "/media/tts/strange-door-${requestedTexts.size}.wav"
    }
}

private class StrangeDoorDemoFailOnceFeedbackTts : XiaobaohuTtsAudioGenerator {
    var attempts = 0

    override suspend fun generateAudioUrl(text: String, emotion: String): String? {
        attempts += 1
        if (attempts == 1) error("temporary tts failure")
        return "/media/tts/retry-ok.wav"
    }
}

private class StrangeDoorDemoRecordingTts : TtsController {
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
