package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.data.tts.XiaobaohuTtsAudioGenerator
import com.childai.companion.ui.chat.languagegame.BrainTeaserGameState
import com.childai.companion.ui.chat.languagegame.LanguageGameState
import com.childai.companion.ui.chat.languagegame.toLanguageGameEntryUiModel
import com.childai.companion.voice.SpeechInputController
import com.childai.companion.voice.SpeechInputResult
import java.io.File
import java.nio.file.Files
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatViewModelLanguageGameTest {
    @Test
    fun entryPromptAppearsOnceAfterOpening() {
        val viewModel = viewModel()

        viewModel.requestOpeningGreeting()

        val model = requireNotNull(viewModel.uiState.value.languageGame)
            .toLanguageGameEntryUiModel()
        assertEquals(
            listOf("我们随便聊聊天", "还是玩一个小游戏？"),
            model.lines,
        )
        assertEquals(
            listOf("随便聊聊", "玩个小游戏"),
            model.actions.map { it.label },
        )

        viewModel.requestOpeningGreeting()

        assertTrue(requireNotNull(viewModel.uiState.value.languageGame).autoPromptShown)
    }

    @Test
    fun casualChatDismissesEntryPromptForCurrentLifecycle() {
        val viewModel = viewModel()

        viewModel.requestOpeningGreeting()
        viewModel.dismissLanguageGameEntry()
        viewModel.requestOpeningGreeting()

        assertNull(viewModel.uiState.value.languageGame)
    }

    @Test
    fun openGameMenuOnlyShowsBrainTeaserAndExit() {
        val viewModel = viewModel()

        viewModel.openLanguageGameMenu()

        val model = requireNotNull(viewModel.uiState.value.languageGame)
            .toLanguageGameEntryUiModel()
        assertEquals(LanguageGameState.GameMenu, viewModel.uiState.value.languageGame?.state)
        assertEquals(
            listOf("脑筋急转弯", "先聊别的"),
            model.actions.map { it.label },
        )
        assertTrue(model.actions.none { it.label == "词语接龙" })
        assertTrue(model.actions.none { it.label == "猜谜语" })
    }

    @Test
    fun startBrainTeaserShowsFirstQuestion() {
        val viewModel = viewModel()

        viewModel.startBrainTeaserGame()

        val snapshot = requireNotNull(viewModel.uiState.value.languageGame)
        assertEquals(LanguageGameState.BrainTeaser, snapshot.state)
        assertEquals(0, snapshot.brainTeaser?.questionIndex)
        assertEquals(BrainTeaserGameState.Question, snapshot.brainTeaser?.gameState)
        assertEquals(
            listOf("什么东西越洗越脏？"),
            snapshot.toLanguageGameEntryUiModel().lines,
        )
    }

    @Test
    fun brainTeaserVoiceAnswerDoesNotSendConversationWhenCorrect() {
        val sender = LanguageGameSender()
        val viewModel = viewModel(
            sender = sender,
            speech = FakeLanguageGameSpeechInputController(
                result = SpeechInputResult.Transcript("水"),
            ),
        )
        viewModel.startBrainTeaserGame()

        viewModel.startVoiceRecording(tempDir())
        viewModel.stopVoiceRecordingAndUpload()

        val snapshot = requireNotNull(viewModel.uiState.value.languageGame)
        assertEquals(BrainTeaserGameState.Correct, snapshot.brainTeaser?.gameState)
        assertTrue(sender.sentTexts.isEmpty())
    }

    @Test
    fun nonMatchingAnswerEntersHintAndHintCanThenBecomeCorrect() {
        val sender = LanguageGameSender()
        val viewModel = viewModel(sender = sender)
        viewModel.startBrainTeaserGame()

        viewModel.sendText("毛巾")

        var snapshot = requireNotNull(viewModel.uiState.value.languageGame)
        assertEquals(BrainTeaserGameState.Hint, snapshot.brainTeaser?.gameState)
        assertEquals(
            listOf(
                "这个答案也有点意思",
                "不过这题的小机关不是它",
                "我给你一个提示",
                "它常常在杯子里、河里、盆里",
            ),
            snapshot.toLanguageGameEntryUiModel().lines,
        )

        viewModel.sendText("是水")

        snapshot = requireNotNull(viewModel.uiState.value.languageGame)
        assertEquals(BrainTeaserGameState.Correct, snapshot.brainTeaser?.gameState)
        assertTrue(sender.sentTexts.isEmpty())
    }

    @Test
    fun hintRevealAndNextQuestionWorkLocally() {
        val viewModel = viewModel()
        viewModel.startBrainTeaserGame()

        viewModel.requestBrainTeaserHint()
        assertEquals(
            BrainTeaserGameState.Hint,
            viewModel.uiState.value.languageGame?.brainTeaser?.gameState,
        )

        viewModel.revealBrainTeaserAnswer()
        assertEquals(
            BrainTeaserGameState.Revealed,
            viewModel.uiState.value.languageGame?.brainTeaser?.gameState,
        )

        viewModel.nextBrainTeaserQuestion()
        assertEquals(1, viewModel.uiState.value.languageGame?.brainTeaser?.questionIndex)
        assertEquals(
            BrainTeaserGameState.Question,
            viewModel.uiState.value.languageGame?.brainTeaser?.gameState,
        )
    }

    @Test
    fun fifthQuestionNextLoopsBackToFirst() {
        val viewModel = viewModel()
        viewModel.startBrainTeaserGame()

        repeat(5) {
            viewModel.nextBrainTeaserQuestion()
        }

        assertEquals(0, viewModel.uiState.value.languageGame?.brainTeaser?.questionIndex)
    }

    @Test
    fun changeGameReturnsToMenuAndExitRestoresConversation() {
        val sender = LanguageGameSender()
        val viewModel = viewModel(sender = sender)
        viewModel.startBrainTeaserGame()

        viewModel.returnToLanguageGameMenu()
        assertEquals(LanguageGameState.GameMenu, viewModel.uiState.value.languageGame?.state)

        viewModel.exitLanguageGame()
        viewModel.sendText("我想聊恐龙")

        assertNull(viewModel.uiState.value.languageGame)
        assertEquals(listOf("我想聊恐龙"), sender.sentTexts)
    }

    @Test
    fun gameKeywordsRouteLocallyWithoutConversation() {
        val sender = LanguageGameSender()
        val viewModel = viewModel(sender = sender)

        viewModel.sendText("玩游戏")

        assertEquals(LanguageGameState.GameMenu, viewModel.uiState.value.languageGame?.state)
        assertTrue(sender.sentTexts.isEmpty())

        val secondViewModel = viewModel(sender = sender)
        secondViewModel.sendText("脑筋急转弯")

        assertEquals(LanguageGameState.BrainTeaser, secondViewModel.uiState.value.languageGame?.state)
        assertTrue(sender.sentTexts.isEmpty())

        val thirdViewModel = viewModel(sender = sender)
        thirdViewModel.sendText("词语接龙")

        assertEquals(LanguageGameState.GameMenu, thirdViewModel.uiState.value.languageGame?.state)
        assertTrue(sender.sentTexts.isEmpty())
    }

    @Test
    fun strangeDoorActivePreventsLanguageGameTrigger() {
        val sender = LanguageGameSender()
        val viewModel = viewModel(sender = sender)

        viewModel.activateStrangeDoorDemo()
        viewModel.sendText("脑筋急转弯")

        assertNull(viewModel.uiState.value.languageGame)
        assertEquals(listOf("脑筋急转弯"), sender.sentTexts)
    }

    private fun viewModel(
        sender: LanguageGameSender = LanguageGameSender(),
        speech: SpeechInputController = FakeLanguageGameSpeechInputController(),
    ): ChatViewModel {
        return ChatViewModel(
            conversationSender = sender,
            speechInputController = speech,
            feedbackTtsAudioGenerator = NoOpLanguageGameFeedbackTts,
            sendDispatcher = Dispatchers.Unconfined,
        )
    }

    private fun tempDir(): File {
        return Files.createTempDirectory("language-game-test").toFile()
    }
}

private object NoOpLanguageGameFeedbackTts : XiaobaohuTtsAudioGenerator {
    override suspend fun generateAudioUrl(text: String, emotion: String): String? = null
}

private class FakeLanguageGameSpeechInputController(
    private val result: SpeechInputResult = SpeechInputResult.Transcript("水"),
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

private class LanguageGameSender : ConversationMessageSender {
    var openingCalls = 0
    val sentTexts = mutableListOf<String>()

    override suspend fun requestOpening(
        childId: String,
        sessionId: String,
        timezone: String,
    ): ConversationMessageResponse {
        openingCalls += 1
        return languageGameResponse("豆豆，回来啦。")
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
        return languageGameResponse("收到。")
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

private fun languageGameResponse(text: String): ConversationMessageResponse {
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
