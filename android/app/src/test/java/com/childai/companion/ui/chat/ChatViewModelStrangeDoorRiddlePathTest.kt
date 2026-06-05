package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoMethod
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoState
import com.childai.companion.ui.chat.strangedoor.StrangeDoorState
import com.childai.companion.voice.SpeechInputController
import com.childai.companion.voice.SpeechInputResult
import java.io.File
import java.nio.file.Files
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatViewModelStrangeDoorRiddlePathTest {
    @Test
    fun riddlePromptAsrTranscriptIsConsumedLocallyWithoutConversation() {
        val sender = RecordingRiddleConversationSender()
        val viewModel = viewModel(
            sender = sender,
            speech = RiddleSpeechInputController(SpeechInputResult.Transcript("答案是水")),
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorRiddleMethod()
        viewModel.startVoiceRecording(tempDir())
        viewModel.stopVoiceRecordingAndUpload()

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(0, sender.sendCalls)
        assertEquals(0, sender.streamCalls)
        assertEquals(StrangeDoorDemoState.Completed, snapshot.demoState)
        assertEquals(StrangeDoorState.Open, snapshot.doorState)
        assertTrue(requireNotNull(snapshot.lastRiddleEvaluation).isCorrect)
    }

    @Test
    fun answerContainingWaterOpensDoor() {
        val viewModel = viewModel(
            speech = RiddleSpeechInputController(SpeechInputResult.Transcript("我觉得是水吧")),
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorRiddleMethod()
        viewModel.startVoiceRecording(tempDir())
        viewModel.stopVoiceRecordingAndUpload()

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorState.Open, snapshot.doorState)
        assertEquals(StrangeDoorDemoState.Completed, snapshot.demoState)
        assertEquals(
            listOf(
                "对，是水",
                "",
                "小门被你说得愣住了",
                "它低头想了三秒",
                "然后咔哒一下打开了",
            ),
            requireNotNull(snapshot.lastRiddleEvaluation).feedbackLines,
        )
    }

    @Test
    fun nonWaterAnswerShowsHintWithoutOpeningDoor() {
        val viewModel = viewModel(
            speech = RiddleSpeechInputController(SpeechInputResult.Transcript("毛巾")),
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorRiddleMethod()
        viewModel.startVoiceRecording(tempDir())
        viewModel.stopVoiceRecordingAndUpload()

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        val evaluation = requireNotNull(snapshot.lastRiddleEvaluation)
        assertEquals(StrangeDoorDemoState.RiddleHint, snapshot.demoState)
        assertEquals(StrangeDoorState.Closed, snapshot.doorState)
        assertFalse(evaluation.isCorrect)
        assertEquals(
            listOf(
                "这个答案有点勇敢",
                "小门差点相信了",
                "",
                "我给你一个提示",
                "它常常在杯子里、河里、盆里",
            ),
            evaluation.feedbackLines,
        )
    }

    @Test
    fun retryRiddleReturnsToPrompt() {
        val viewModel = viewModel()

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorRiddleMethod()
        viewModel.answerStrangeDoorRiddle("毛巾")
        viewModel.retryStrangeDoorRiddle()

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorDemoState.RiddlePrompt, snapshot.demoState)
        assertEquals(StrangeDoorDemoMethod.Riddle, snapshot.lastMethod)
        assertEquals(null, snapshot.lastRiddleEvaluation)
    }

    @Test
    fun choosePhotoFromRiddleHintSwitchesToPhotoPrompt() {
        val viewModel = viewModel()

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorRiddleMethod()
        viewModel.answerStrangeDoorRiddle("毛巾")
        viewModel.chooseStrangeDoorPhotoMethod()

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorDemoState.PhotoPrompt, snapshot.demoState)
        assertEquals(StrangeDoorDemoMethod.Photo, snapshot.lastMethod)
        assertEquals(null, snapshot.lastRiddleEvaluation)
    }

    @Test
    fun debugTextAnswerInRiddlePromptDoesNotSendConversation() {
        val sender = RecordingRiddleConversationSender()
        val viewModel = viewModel(sender = sender)

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorRiddleMethod()
        viewModel.sendText("水")

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(0, sender.sendCalls)
        assertEquals(0, sender.streamCalls)
        assertEquals(StrangeDoorState.Open, snapshot.doorState)
    }

    private fun viewModel(
        sender: RecordingRiddleConversationSender = RecordingRiddleConversationSender(),
        speech: SpeechInputController = RiddleSpeechInputController(),
    ): ChatViewModel {
        return ChatViewModel(
            conversationSender = sender,
            speechInputController = speech,
            sendDispatcher = Dispatchers.Unconfined,
            requestOpeningOnInit = false,
        )
    }

    private fun tempDir(): File {
        return Files.createTempDirectory("strange-door-riddle-test").toFile()
    }
}

private class RiddleSpeechInputController(
    private val result: SpeechInputResult = SpeechInputResult.Transcript("测试语音"),
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

private class RecordingRiddleConversationSender : ConversationMessageSender {
    var sendCalls = 0
    var streamCalls = 0

    override suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        quickActionId: String?,
        timezone: String,
    ): ConversationMessageResponse {
        sendCalls += 1
        return riddleResponse()
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
    ) {
        streamCalls += 1
    }

    private fun riddleResponse(): ConversationMessageResponse {
        return ConversationMessageResponse(
            reply = ConversationReply(
                type = "agent_message",
                text = "不应被调用",
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
}
