package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.data.tts.XiaobaohuTtsAudioGenerator
import com.childai.companion.voice.SpeechInputController
import com.childai.companion.voice.SpeechInputResult
import com.childai.companion.voice.TtsCallbacks
import com.childai.companion.voice.TtsController
import com.childai.companion.voice.TtsRequest
import com.childai.companion.voice.TtsUiState
import java.io.File
import java.nio.file.Files
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatViewModelNaturalWaitingTest {
    @Test
    fun ttsQueueDrainEntersWaitingVisualState() {
        val sender = NaturalWaitingSender()
        val speech = NaturalWaitingSpeechController()
        val tts = NaturalWaitingTtsController(autoComplete = true)
        val viewModel = viewModel(
            sender = sender,
            speech = speech,
            ttsController = tts,
        )

        // Simulate agent reply with audio
        viewModel.renderAgentReply(
            response = ConversationMessageResponse(
                reply = ConversationReply(
                    type = "agent_message",
                    text = "你好呀。",
                    voiceEnabled = true,
                    audioUrl = "/media/tts/hello.wav",
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
            ),
        )

        // Should enter waiting visual state
        assertEquals(
            VoiceInputMode.WaitingForChild,
            viewModel.uiState.value.voice.inputMode,
        )
        // WaitingForChild is NOT recording
        assertFalse("WaitingForChild should not be recording", viewModel.uiState.value.voice.isRecording)
        assertEquals(
            ChildTurnUiPhase.WaitingChild,
            viewModel.uiState.value.interactionPresentation.phase,
        )
        // Should NOT have started actual recording
        assertFalse("Should not start recording for visual waiting", speech.started)
    }

    @Test
    fun naturalWaitingDisabledDoesNotEnterWaitingState() {
        val sender = NaturalWaitingSender()
        val speech = NaturalWaitingSpeechController()
        val tts = NaturalWaitingTtsController(autoComplete = true)
        val viewModel = viewModel(
            sender = sender,
            speech = speech,
            ttsController = tts,
            naturalWaitingEnabled = false,
        )

        viewModel.renderAgentReply(
            response = ConversationMessageResponse(
                reply = ConversationReply(
                    type = "agent_message",
                    text = "你好呀。",
                    voiceEnabled = true,
                    audioUrl = "/media/tts/hello.wav",
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
            ),
        )

        assertFalse("Recording should not start when feature disabled", speech.started)
        assertEquals(
            VoiceInputMode.Idle,
            viewModel.uiState.value.voice.inputMode,
        )
    }

    @Test
    fun cancelVoiceInputDuringWaitingReturnsToIdle() {
        val sender = NaturalWaitingSender()
        val speech = NaturalWaitingSpeechController()
        val tts = NaturalWaitingTtsController(autoComplete = true)
        val viewModel = viewModel(
            sender = sender,
            speech = speech,
            ttsController = tts,
        )

        viewModel.renderAgentReply(
            response = agentReplyWithAudio(),
        )

        assertEquals(VoiceInputMode.WaitingForChild, viewModel.uiState.value.voice.inputMode)

        viewModel.cancelVoiceInput()

        assertEquals(VoiceInputMode.Idle, viewModel.uiState.value.voice.inputMode)
        assertFalse(viewModel.uiState.value.voice.isRecording)
    }

    @Test
    fun waitingForChildIsNotRecording() {
        val voice = VoiceUiState(inputMode = VoiceInputMode.WaitingForChild)
        assertFalse("WaitingForChild should not be considered recording", voice.isRecording)
    }

    @Test
    fun listeningIsRecording() {
        val voice = VoiceUiState(inputMode = VoiceInputMode.Listening)
        assertTrue("Listening should be considered recording", voice.isRecording)
    }

    @Test
    fun waitingForChildShowsCorrectStatusText() {
        val voice = VoiceUiState(inputMode = VoiceInputMode.WaitingForChild)
        assertEquals("想说再说", voice.statusText)
    }

    @Test
    fun waitingForChildPhaseResolvesToWaitingChild() {
        val presentation = childInteractionPresentation(
            voice = VoiceUiState(inputMode = VoiceInputMode.WaitingForChild),
            tts = TtsUiState(),
        )
        assertEquals(ChildTurnUiPhase.WaitingChild, presentation.phase)
        assertEquals("按一下开始说", presentation.primaryButtonText)
        assertTrue(presentation.primaryButtonEnabled)
    }

    @Test
    fun waitingForChildClickStartsRecording() {
        val sender = NaturalWaitingSender()
        val speech = NaturalWaitingSpeechController()
        val tts = NaturalWaitingTtsController(autoComplete = true)
        val viewModel = viewModel(
            sender = sender,
            speech = speech,
            ttsController = tts,
        )
        val dir = tempDir()

        viewModel.renderAgentReply(
            response = agentReplyWithAudio(),
        )

        assertEquals(VoiceInputMode.WaitingForChild, viewModel.uiState.value.voice.inputMode)
        assertFalse("WaitingForChild is not recording", viewModel.uiState.value.voice.isRecording)

        // Click start button should enter Listening
        viewModel.startVoiceRecording(dir)

        assertEquals(VoiceInputMode.Listening, viewModel.uiState.value.voice.inputMode)
        assertTrue("Listening should be recording", viewModel.uiState.value.voice.isRecording)
        assertTrue("Should have started actual recording", speech.started)
    }

    @Test
    fun noAudioReplyDoesNotTriggerWaiting() {
        val sender = NaturalWaitingSender()
        val speech = NaturalWaitingSpeechController()
        val tts = NaturalWaitingTtsController(autoComplete = true)
        val viewModel = viewModel(
            sender = sender,
            speech = speech,
            ttsController = tts,
        )

        // Reply without audio - should NOT trigger waiting
        viewModel.renderAgentReply(
            response = ConversationMessageResponse(
                reply = ConversationReply(
                    type = "agent_message",
                    text = "好的。",
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
            ),
        )

        assertFalse("No recording when reply has no audio", speech.started)
        assertEquals(VoiceInputMode.Idle, viewModel.uiState.value.voice.inputMode)
    }

    @Test
    fun waitingCancelButtonShowsInWaitingState() {
        val shouldShow = inputBarShouldShowCancelAction(
            useChildVoiceFirstInput = true,
            inputMode = VoiceInputMode.WaitingForChild,
        )
        assertTrue("Cancel should show during waiting", shouldShow)
    }

    private fun viewModel(
        sender: NaturalWaitingSender,
        speech: SpeechInputController = NaturalWaitingSpeechController(),
        ttsController: TtsController = NaturalWaitingTtsController(autoComplete = true),
        feedbackTts: XiaobaohuTtsAudioGenerator = NaturalWaitingFeedbackTts(),
        naturalWaitingEnabled: Boolean = true,
    ): ChatViewModel {
        return ChatViewModel(
            conversationSender = sender,
            speechInputController = speech,
            feedbackTtsAudioGenerator = feedbackTts,
            ttsController = ttsController,
            sendDispatcher = Dispatchers.Unconfined,
            naturalWaitingEnabled = naturalWaitingEnabled,
            naturalWaitingTimeoutMs = 5_000L,
        )
    }

    private fun tempDir(): File {
        return Files.createTempDirectory("natural-waiting-test").toFile()
    }

    private fun agentReplyWithAudio(): ConversationMessageResponse {
        return ConversationMessageResponse(
            reply = ConversationReply(
                type = "agent_message",
                text = "你好呀。",
                voiceEnabled = true,
                audioUrl = "/media/tts/hello.wav",
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
}

private class NaturalWaitingSpeechController(
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

private class NaturalWaitingTtsController(
    private val autoComplete: Boolean,
) : TtsController {
    override fun speak(request: TtsRequest, callbacks: TtsCallbacks): Boolean {
        callbacks.onStart()
        if (autoComplete) {
            callbacks.onDone()
        }
        return true
    }

    override fun stop() = Unit
    override fun shutdown() = Unit
}

private class NaturalWaitingSender : ConversationMessageSender {
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

private class NaturalWaitingFeedbackTts : XiaobaohuTtsAudioGenerator {
    override suspend fun generateAudioUrl(text: String, emotion: String): String? {
        return "/media/tts/feedback.wav"
    }
}
