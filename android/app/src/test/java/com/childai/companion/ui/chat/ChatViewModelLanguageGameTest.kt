package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.data.tts.XiaobaohuTtsAudioGenerator
import com.childai.companion.ui.chat.languagegame.BrainTeaserGameState
import com.childai.companion.ui.chat.languagegame.LanguageGameState
import com.childai.companion.ui.chat.languagegame.RiddleGameState
import com.childai.companion.ui.chat.languagegame.WordChainGameState
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
    fun entryPromptDoesNotAppearAutomaticallyAfterOpeningByDefault() {
        val viewModel = viewModel()

        viewModel.requestOpeningGreeting()

        assertNull(viewModel.uiState.value.languageGame)
    }

    @Test
    fun explicitGameMenuStillShowsLanguageGameChoices() {
        val viewModel = viewModel()

        viewModel.sendText("玩游戏")

        val model = requireNotNull(viewModel.uiState.value.languageGame)
            .toLanguageGameEntryUiModel()
        assertEquals(LanguageGameState.GameMenu, viewModel.uiState.value.languageGame?.state)
        assertEquals(
            listOf("脑筋急转弯", "词语接龙", "猜谜语", "先聊别的"),
            model.actions.map { it.label },
        )
    }

    @Test
    fun casualChatDismissesLanguageGameForCurrentLifecycle() {
        val viewModel = viewModel()

        viewModel.openLanguageGameMenu()
        viewModel.dismissLanguageGameEntry()
        viewModel.requestOpeningGreeting()

        assertNull(viewModel.uiState.value.languageGame)
    }

    @Test
    fun openGameMenuShowsBrainTeaserWordChainRiddleAndExit() {
        val viewModel = viewModel()

        viewModel.openLanguageGameMenu()

        val model = requireNotNull(viewModel.uiState.value.languageGame)
            .toLanguageGameEntryUiModel()
        assertEquals(LanguageGameState.GameMenu, viewModel.uiState.value.languageGame?.state)
        assertEquals(
            listOf("脑筋急转弯", "词语接龙", "猜谜语", "先聊别的"),
            model.actions.map { it.label },
        )
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
    fun repeatedBrainTeaserStartsRotateStartingQuestion() {
        val viewModel = viewModel()

        viewModel.startBrainTeaserGame()
        val firstIndex = viewModel.uiState.value.languageGame?.brainTeaser?.questionIndex

        viewModel.startBrainTeaserGame()
        val secondIndex = viewModel.uiState.value.languageGame?.brainTeaser?.questionIndex

        assertEquals(0, firstIndex)
        assertEquals(1, secondIndex)
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
    fun startWordChainShowsFixedFirstWord() {
        val viewModel = viewModel()

        viewModel.startWordChainGame()

        val snapshot = requireNotNull(viewModel.uiState.value.languageGame)
        assertEquals(LanguageGameState.WordChain, snapshot.state)
        assertEquals(WordChainGameState.Start, snapshot.wordChain?.gameState)
        assertEquals("苹果", snapshot.wordChain?.previousWord)
        assertEquals(
            listOf(
                "我们玩词语接龙",
                "我先说一个词",
                "苹果",
                "你接一个从“果”开始的词就行",
            ),
            snapshot.toLanguageGameEntryUiModel().lines,
        )
    }

    @Test
    fun repeatedWordChainStartsRotateStartingWord() {
        val viewModel = viewModel()

        viewModel.startWordChainGame()
        val firstWord = viewModel.uiState.value.languageGame?.wordChain?.previousWord

        viewModel.startWordChainGame()
        val secondWord = viewModel.uiState.value.languageGame?.wordChain?.previousWord

        assertEquals("苹果", firstWord)
        assertEquals("月亮", secondWord)
    }

    @Test
    fun wordChainVoiceAnswerDoesNotSendConversationWhenConnected() {
        val sender = LanguageGameSender()
        val viewModel = viewModel(
            sender = sender,
            speech = FakeLanguageGameSpeechInputController(
                result = SpeechInputResult.Transcript("果汁"),
            ),
        )
        viewModel.startWordChainGame()

        viewModel.startVoiceRecording(tempDir())
        viewModel.stopVoiceRecordingAndUpload()

        val snapshot = requireNotNull(viewModel.uiState.value.languageGame)
        assertEquals(WordChainGameState.Correct, snapshot.wordChain?.gameState)
        assertEquals("汁水", snapshot.wordChain?.previousWord)
        assertEquals(
            listOf(
                "接上啦",
                "“苹果”接“果汁”",
                "这个小词跑得还挺快",
                "我来接一个",
                "“果汁”接“汁水”",
            ),
            snapshot.toLanguageGameEntryUiModel().lines,
        )
        assertTrue(sender.sentTexts.isEmpty())
    }

    @Test
    fun wordChainNonMatchingAnswerEntersHintWithoutConversation() {
        val sender = LanguageGameSender()
        val viewModel = viewModel(sender = sender)
        viewModel.startWordChainGame()

        viewModel.sendText("毛巾")

        val snapshot = requireNotNull(viewModel.uiState.value.languageGame)
        assertEquals(WordChainGameState.Hint, snapshot.wordChain?.gameState)
        assertEquals(
            listOf(
                "这个词也可以玩",
                "不过这次要从“果”开始",
                "我给你换个容易的",
            ),
            snapshot.toLanguageGameEntryUiModel().lines,
        )
        assertTrue(sender.sentTexts.isEmpty())
    }

    @Test
    fun wordChainSecondMissAutoAssistsAndLowersDifficulty() {
        val sender = LanguageGameSender()
        val viewModel = viewModel(sender = sender)
        viewModel.startWordChainGame()

        viewModel.sendText("毛巾")
        viewModel.sendText("毛巾")

        val snapshot = requireNotNull(viewModel.uiState.value.languageGame)
        assertEquals(WordChainGameState.Hint, snapshot.wordChain?.gameState)
        assertEquals(1, snapshot.wordChain?.roundIndex)
        assertEquals("果汁", snapshot.wordChain?.previousWord)
        assertEquals(
            listOf(
                "这个词也可以玩",
                "不过这次要从“果”开始",
                "我给你换个容易的",
                "我来接一个",
                "“苹果”接“果汁”",
            ),
            snapshot.toLanguageGameEntryUiModel().lines,
        )
        assertTrue(sender.sentTexts.isEmpty())
    }

    @Test
    fun wordChainFinishesAfterFiveEffectiveRoundsAndReplayRotatesStartWord() {
        val viewModel = viewModel()
        viewModel.startWordChainGame()

        repeat(5) {
            val previous = requireNotNull(viewModel.uiState.value.languageGame?.wordChain?.previousWord)
            viewModel.sendText(previous.last().toString())
        }

        var snapshot = requireNotNull(viewModel.uiState.value.languageGame)
        assertEquals(WordChainGameState.Finished, snapshot.wordChain?.gameState)
        assertEquals(
            listOf(
                "我们已经接了好多小词",
                "先让它们排队休息一下",
            ),
            snapshot.toLanguageGameEntryUiModel().lines,
        )

        viewModel.restartWordChainGame()

        snapshot = requireNotNull(viewModel.uiState.value.languageGame)
        assertEquals(WordChainGameState.Start, snapshot.wordChain?.gameState)
        assertEquals("月亮", snapshot.wordChain?.previousWord)
    }

    @Test
    fun startRiddleShowsFirstQuestion() {
        val viewModel = viewModel()

        viewModel.startRiddleGame()

        val snapshot = requireNotNull(viewModel.uiState.value.languageGame)
        assertEquals(LanguageGameState.Riddle, snapshot.state)
        assertEquals(0, snapshot.riddle?.questionIndex)
        assertEquals(RiddleGameState.Question, snapshot.riddle?.gameState)
        assertEquals(
            listOf(
                "我们来猜一个小谜语",
                "小小房子圆又圆",
                "里面住着甜甜水",
            ),
            snapshot.toLanguageGameEntryUiModel().lines,
        )
    }

    @Test
    fun repeatedRiddleStartsRotateStartingQuestion() {
        val viewModel = viewModel()

        viewModel.startRiddleGame()
        val firstIndex = viewModel.uiState.value.languageGame?.riddle?.questionIndex

        viewModel.startRiddleGame()
        val secondIndex = viewModel.uiState.value.languageGame?.riddle?.questionIndex

        assertEquals(0, firstIndex)
        assertEquals(1, secondIndex)
    }

    @Test
    fun riddleVoiceAnswerDoesNotSendConversationWhenCorrect() {
        val sender = LanguageGameSender()
        val viewModel = viewModel(
            sender = sender,
            speech = FakeLanguageGameSpeechInputController(
                result = SpeechInputResult.Transcript("我猜是橘子"),
            ),
        )
        viewModel.startRiddleGame()

        viewModel.startVoiceRecording(tempDir())
        viewModel.stopVoiceRecordingAndUpload()

        val snapshot = requireNotNull(viewModel.uiState.value.languageGame)
        assertEquals(RiddleGameState.Correct, snapshot.riddle?.gameState)
        assertEquals(
            listOf(
                "猜到啦",
                "就是橘子",
                "小白狐把这个谜底轻轻收好",
            ),
            snapshot.toLanguageGameEntryUiModel().lines,
        )
        assertTrue(sender.sentTexts.isEmpty())
    }

    @Test
    fun riddleNonMatchingAnswerEntersHintAndHintCanThenBecomeCorrect() {
        val sender = LanguageGameSender()
        val viewModel = viewModel(sender = sender)
        viewModel.startRiddleGame()

        viewModel.sendText("水果")

        var snapshot = requireNotNull(viewModel.uiState.value.languageGame)
        assertEquals(RiddleGameState.Hint, snapshot.riddle?.gameState)
        assertEquals(
            listOf(
                "这个想法也挺像",
                "我再给你一点提示",
                "它是一种水果，剥开以后可以一瓣一瓣吃",
            ),
            snapshot.toLanguageGameEntryUiModel().lines,
        )
        assertTrue(sender.sentTexts.isEmpty())

        viewModel.sendText("橘子")

        snapshot = requireNotNull(viewModel.uiState.value.languageGame)
        assertEquals(RiddleGameState.Correct, snapshot.riddle?.gameState)
        assertTrue(sender.sentTexts.isEmpty())
    }

    @Test
    fun riddleHintRevealAndNextQuestionWorkLocally() {
        val viewModel = viewModel()
        viewModel.startRiddleGame()

        viewModel.requestRiddleHint()
        assertEquals(
            RiddleGameState.Hint,
            viewModel.uiState.value.languageGame?.riddle?.gameState,
        )

        viewModel.revealRiddleAnswer()
        assertEquals(
            RiddleGameState.Revealed,
            viewModel.uiState.value.languageGame?.riddle?.gameState,
        )

        viewModel.nextRiddleQuestion()
        assertEquals(1, viewModel.uiState.value.languageGame?.riddle?.questionIndex)
        assertEquals(
            RiddleGameState.Question,
            viewModel.uiState.value.languageGame?.riddle?.gameState,
        )
    }

    @Test
    fun fifthRiddleNextLoopsBackToFirst() {
        val viewModel = viewModel()
        viewModel.startRiddleGame()

        repeat(5) {
            viewModel.nextRiddleQuestion()
        }

        assertEquals(0, viewModel.uiState.value.languageGame?.riddle?.questionIndex)
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
    fun casualChatTextDuringGameExitsAndSendsConversation() {
        val sender = LanguageGameSender()
        val viewModel = viewModel(sender = sender)

        viewModel.startRiddleGame()
        viewModel.sendText("聊变形金刚")

        assertNull(viewModel.uiState.value.languageGame)
        assertEquals(listOf("聊变形金刚"), sender.sentTexts)
    }

    @Test
    fun storyRequestDuringGameExitsAndSendsConversation() {
        val sender = LanguageGameSender()
        val viewModel = viewModel(sender = sender)

        viewModel.startRiddleGame()
        viewModel.sendText("你给我讲个故事")

        assertNull(viewModel.uiState.value.languageGame)
        assertEquals(listOf("你给我讲个故事"), sender.sentTexts)
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

        assertEquals(LanguageGameState.WordChain, thirdViewModel.uiState.value.languageGame?.state)
        assertEquals("苹果", thirdViewModel.uiState.value.languageGame?.wordChain?.previousWord)
        assertTrue(sender.sentTexts.isEmpty())

        val fourthViewModel = viewModel(sender = sender)
        fourthViewModel.sendText("接龙")

        assertEquals(LanguageGameState.WordChain, fourthViewModel.uiState.value.languageGame?.state)
        assertTrue(sender.sentTexts.isEmpty())

        val fifthViewModel = viewModel(sender = sender)
        fifthViewModel.sendText("猜谜语")

        assertEquals(LanguageGameState.Riddle, fifthViewModel.uiState.value.languageGame?.state)
        assertEquals(0, fifthViewModel.uiState.value.languageGame?.riddle?.questionIndex)
        assertTrue(sender.sentTexts.isEmpty())

        val sixthViewModel = viewModel(sender = sender)
        sixthViewModel.sendText("谜语")

        assertEquals(LanguageGameState.Riddle, sixthViewModel.uiState.value.languageGame?.state)
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

        val secondSender = LanguageGameSender()
        val secondViewModel = viewModel(sender = secondSender)
        secondViewModel.activateStrangeDoorDemo()
        secondViewModel.sendText("词语接龙")

        assertNull(secondViewModel.uiState.value.languageGame)
        assertEquals(listOf("词语接龙"), secondSender.sentTexts)

        val thirdSender = LanguageGameSender()
        val thirdViewModel = viewModel(sender = thirdSender)
        thirdViewModel.activateStrangeDoorDemo()
        thirdViewModel.sendText("猜谜语")

        assertNull(thirdViewModel.uiState.value.languageGame)
        assertEquals(listOf("猜谜语"), thirdSender.sentTexts)
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
            nowMillis = { 0L },
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
