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

class ChatViewModelNaturalSpeakingTest {
    @Test
    fun ttsQueueDrainAutoStartsRecordingInWaitingMode() {
        val sender = NaturalSpeakingSender()
        val speech = NaturalSpeakingSpeechController()
        val tts = NaturalSpeakingTtsController(autoComplete = true)
        val viewModel = viewModel(
            sender = sender,
            speech = speech,
            ttsController = tts,
        )
        val dir = tempDir()

        // First establish cache directory via a manual recording
        viewModel.startVoiceRecording(dir)
        viewModel.cancelVoiceInput()
        speech.started = false

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

        assertTrue("Recording should start after TTS queue drains", speech.started)
        assertEquals(
            VoiceInputMode.WaitingForChild,
            viewModel.uiState.value.voice.inputMode,
        )
        assertTrue("isRecording should be true", viewModel.uiState.value.voice.isRecording)
        assertEquals(
            ChildTurnUiPhase.WaitingChild,
            viewModel.uiState.value.interactionPresentation.phase,
        )
    }

    @Test
    fun naturalSpeakingDisabledDoesNotAutoStartRecording() {
        val sender = NaturalSpeakingSender()
        val speech = NaturalSpeakingSpeechController()
        val tts = NaturalSpeakingTtsController(autoComplete = true)
        val viewModel = viewModel(
            sender = sender,
            speech = speech,
            ttsController = tts,
            naturalSpeakingEnabled = false,
        )
        val dir = tempDir()

        viewModel.startVoiceRecording(dir)
        viewModel.cancelVoiceInput()
        speech.started = false

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
        val sender = NaturalSpeakingSender()
        val speech = NaturalSpeakingSpeechController()
        val tts = NaturalSpeakingTtsController(autoComplete = true)
        val viewModel = viewModel(
            sender = sender,
            speech = speech,
            ttsController = tts,
        )
        val dir = tempDir()

        viewModel.startVoiceRecording(dir)
        viewModel.cancelVoiceInput()
        speech.started = false

        viewModel.renderAgentReply(
            response = agentReplyWithAudio(),
        )

        assertEquals(VoiceInputMode.WaitingForChild, viewModel.uiState.value.voice.inputMode)
        assertTrue(speech.started)

        viewModel.cancelVoiceInput()

        assertEquals(VoiceInputMode.Idle, viewModel.uiState.value.voice.inputMode)
        assertFalse(viewModel.uiState.value.voice.isRecording)
    }

    @Test
    fun waitingForChildIsConsideredRecording() {
        val voice = VoiceUiState(inputMode = VoiceInputMode.WaitingForChild)
        assertTrue(voice.isRecording)
    }

    @Test
    fun waitingForChildShowsCorrectStatusText() {
        val voice = VoiceUiState(inputMode = VoiceInputMode.WaitingForChild)
        assertEquals("我在听。", voice.statusText)
    }

    @Test
    fun waitingForChildPhaseResolvesToListening() {
        val presentation = childInteractionPresentation(
            voice = VoiceUiState(inputMode = VoiceInputMode.WaitingForChild),
            tts = TtsUiState(),
        )
        assertEquals(ChildTurnUiPhase.WaitingChild, presentation.phase)
        assertEquals("按一下开始说", presentation.primaryButtonText)
        assertTrue(presentation.primaryButtonEnabled)
    }

    @Test
    fun startVoiceRecordingDuringWaitingIsBlockedByIsRecording() {
        val sender = NaturalSpeakingSender()
        val speech = NaturalSpeakingSpeechController()
        val tts = NaturalSpeakingTtsController(autoComplete = true)
        val viewModel = viewModel(
            sender = sender,
            speech = speech,
            ttsController = tts,
        )
        val dir = tempDir()

        viewModel.startVoiceRecording(dir)
        viewModel.cancelVoiceInput()
        speech.started = false

        viewModel.renderAgentReply(
            response = agentReplyWithAudio(),
        )

        assertEquals(VoiceInputMode.WaitingForChild, viewModel.uiState.value.voice.inputMode)

        // isRecording is true, so startVoiceRecording should be blocked
        viewModel.startVoiceRecording(dir)

        // Should still be in WaitingForChild
        assertEquals(VoiceInputMode.WaitingForChild, viewModel.uiState.value.voice.inputMode)
    }

    @Test
    fun noAudioReplyDoesNotTriggerWaiting() {
        val sender = NaturalSpeakingSender()
        val speech = NaturalSpeakingSpeechController()
        val tts = NaturalSpeakingTtsController(autoComplete = true)
        val viewModel = viewModel(
            sender = sender,
            speech = speech,
            ttsController = tts,
        )
        val dir = tempDir()

        viewModel.startVoiceRecording(dir)
        viewModel.cancelVoiceInput()
        speech.started = false

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
        sender: NaturalSpeakingSender,
        speech: SpeechInputController = NaturalSpeakingSpeechController(),
        ttsController: TtsController = NaturalSpeakingTtsController(autoComplete = true),
        feedbackTts: XiaobaohuTtsAudioGenerator = NaturalSpeakingFeedbackTts(),
        naturalSpeakingEnabled: Boolean = true,
    ): ChatViewModel {
        return ChatViewModel(
            conversationSender = sender,
            speechInputController = speech,
            feedbackTtsAudioGenerator = feedbackTts,
            ttsController = ttsController,
            sendDispatcher = Dispatchers.Unconfined,
            naturalSpeakingEnabled = naturalSpeakingEnabled,
            naturalSpeakingTimeoutMs = 5_000L,
        )
    }

    private fun tempDir(): File {
        return Files.createTempDirectory("natural-speaking-test").toFile()
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

private class NaturalSpeakingSpeechController(
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

private class NaturalSpeakingTtsController(
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

private class NaturalSpeakingSender : ConversationMessageSender {
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

private class NaturalSpeakingFeedbackTts : XiaobaohuTtsAudioGenerator {
    override suspend fun generateAudioUrl(text: String, emotion: String): String? {
        return "/media/tts/feedback.wav"
    }
}
