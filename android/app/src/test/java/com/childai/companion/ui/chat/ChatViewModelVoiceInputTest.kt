package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.voice.SpeechInputController
import com.childai.companion.voice.SpeechInputResult
import java.io.File
import java.nio.file.Files
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatViewModelVoiceInputTest {
    @Test
    fun transcriptAutoSendsWhenConfirmationDisabled() {
        val sender = RecordingConversationSender()
        val speech = FakeSpeechInputController(
            result = SpeechInputResult.Transcript("我想聊恐龙。"),
        )
        val viewModel = viewModel(sender = sender, speech = speech)

        viewModel.startVoiceRecording(tempDir())
        assertEquals(VoiceInputMode.Listening, viewModel.uiState.value.voice.inputMode)
        assertTrue(speech.started)

        viewModel.stopVoiceRecordingAndUpload()

        assertEquals(listOf("我想聊恐龙。"), sender.sentTexts)
        assertEquals(VoiceInputMode.Idle, viewModel.uiState.value.voice.inputMode)
        assertFalse(viewModel.uiState.value.isSending)
    }

    @Test
    fun transcriptCanRemainPendingWhenConfirmationEnabledForDebug() {
        val sender = RecordingConversationSender()
        val viewModel = viewModel(
            sender = sender,
            speech = FakeSpeechInputController(
                result = SpeechInputResult.Transcript("我想聊恐龙。"),
            ),
            voiceConfirmBeforeSend = true,
        )

        viewModel.startVoiceRecording(tempDir())
        viewModel.stopVoiceRecordingAndUpload()

        assertEquals(VoiceInputMode.PendingTranscript, viewModel.uiState.value.voice.inputMode)
        assertEquals("我想聊恐龙。", viewModel.uiState.value.voice.pendingTranscript)
        assertTrue(sender.sentTexts.isEmpty())

        viewModel.sendPendingVoiceTranscript()
        assertEquals(listOf("我想聊恐龙。"), sender.sentTexts)
    }

    @Test
    fun cancelPendingTranscriptDoesNotSend() {
        val sender = RecordingConversationSender()
        val viewModel = viewModel(
            sender = sender,
            speech = FakeSpeechInputController(
                result = SpeechInputResult.Transcript("这句不要发。"),
            ),
            voiceConfirmBeforeSend = true,
        )

        viewModel.startVoiceRecording(tempDir())
        viewModel.stopVoiceRecordingAndUpload()
        viewModel.cancelVoiceInput()

        assertTrue(sender.sentTexts.isEmpty())
        assertEquals(VoiceInputMode.Idle, viewModel.uiState.value.voice.inputMode)
        assertEquals("", viewModel.uiState.value.voice.pendingTranscript)
    }

    @Test
    fun policyBlockedShowsTextFallbackAndDoesNotSend() {
        val sender = RecordingConversationSender()
        val message = "我现在还不能用云端听写，我们可以先打字。"
        val viewModel = viewModel(
            sender = sender,
            speech = FakeSpeechInputController(
                result = SpeechInputResult.PolicyBlocked(message),
            ),
        )

        viewModel.startVoiceRecording(tempDir())
        viewModel.stopVoiceRecordingAndUpload()

        assertTrue(sender.sentTexts.isEmpty())
        assertEquals(VoiceInputMode.Failed, viewModel.uiState.value.voice.inputMode)
        assertEquals(message, viewModel.uiState.value.voice.errorMessage)
        assertEquals(MessageAuthor.Agent, viewModel.uiState.value.messages.last().author)
        assertEquals(message, viewModel.uiState.value.messages.last().text)
    }

    @Test
    fun needsRetryShowsRetryPromptWithoutSending() {
        val sender = RecordingConversationSender()
        val message = "我刚才没听清，可以再说一次，也可以直接打字。"
        val viewModel = viewModel(
            sender = sender,
            speech = FakeSpeechInputController(
                result = SpeechInputResult.NeedsRetry(message),
            ),
        )

        viewModel.startVoiceRecording(tempDir())
        viewModel.stopVoiceRecordingAndUpload()

        assertTrue(sender.sentTexts.isEmpty())
        assertEquals(VoiceInputMode.NeedsRetry, viewModel.uiState.value.voice.inputMode)
        assertEquals(message, viewModel.uiState.value.voice.errorMessage)
        assertEquals(MessageAuthor.Agent, viewModel.uiState.value.messages.last().author)
        assertEquals(message, viewModel.uiState.value.messages.last().text)
    }

    @Test
    fun permissionDeniedKeepsTypingFallback() {
        val sender = RecordingConversationSender()
        val viewModel = viewModel(sender = sender)

        viewModel.onVoicePermissionDenied()

        assertTrue(sender.sentTexts.isEmpty())
        assertEquals(VoiceInputMode.PermissionDenied, viewModel.uiState.value.voice.inputMode)
        assertEquals("没有麦克风权限，我们可以请大人打开。", viewModel.uiState.value.voice.statusText)
    }

    private fun viewModel(
        sender: RecordingConversationSender,
        speech: SpeechInputController = FakeSpeechInputController(),
        voiceConfirmBeforeSend: Boolean = false,
    ): ChatViewModel {
        return ChatViewModel(
            conversationSender = sender,
            speechInputController = speech,
            sendDispatcher = Dispatchers.Unconfined,
            voiceConfirmBeforeSend = voiceConfirmBeforeSend,
        )
    }

    private fun tempDir(): File {
        return Files.createTempDirectory("voice-input-test").toFile()
    }
}

private class FakeSpeechInputController(
    private val result: SpeechInputResult = SpeechInputResult.Transcript("测试语音。"),
) : SpeechInputController {
    var started = false
    var canceled = false

    override suspend fun startRecording() {
        started = true
    }

    override suspend fun stopAndTranscribe(
        childId: String,
        sessionId: String,
        timezone: String,
    ): SpeechInputResult {
        return result
    }

    override suspend fun cancel() {
        canceled = true
    }

    override fun shutdown() = Unit
}

private class RecordingConversationSender : ConversationMessageSender {
    val sentTexts = mutableListOf<String>()

    override suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        timezone: String,
    ): ConversationMessageResponse {
        sentTexts += text
        return ConversationMessageResponse(
            reply = ConversationReply(
                type = "agent_message",
                text = "收到。",
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
