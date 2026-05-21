package com.childai.companion.ui.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childai.companion.config.DevSettings
import com.childai.companion.data.attachment.AttachmentCreateResponse
import com.childai.companion.data.attachment.AttachmentRepository
import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationRepository
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationUiAction
import com.childai.companion.voice.NoOpTtsController
import com.childai.companion.voice.TtsCallbacks
import com.childai.companion.voice.TtsController
import com.childai.companion.voice.TtsRequest
import com.childai.companion.voice.TtsUiState
import com.childai.companion.voice.VoiceProfile
import com.childai.companion.voice.previewForDiagnostics
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID

class ChatViewModel(
    private val conversationSender: ConversationMessageSender =
        ConversationRepositoryMessageSender(),
    private val attachmentRepository: AttachmentRepository = AttachmentRepository(),
    private var ttsController: TtsController = NoOpTtsController,
    initialTtsUiState: TtsUiState = TtsUiState(),
) : ViewModel() {
    private val sessionId = "android-${UUID.randomUUID()}"
    private var nextMessageIndex = 0
    private var baseAgentState = FoxAgentUiState()
    private var ttsToken = 0

    private val _uiState = MutableStateFlow(
        ChatUiState(
            messages = initialChatMessages(),
            tts = initialTtsUiState,
        ),
    )
    val uiState: StateFlow<ChatUiState> = _uiState

    fun sendText(text: String) {
        val trimmedText = text.trim()
        if (trimmedText.isEmpty() || _uiState.value.isSending) return

        recordChildMessage(trimmedText)
        _uiState.update {
            it.copy(
                isSending = true,
                quickActions = emptyList(),
            )
        }

        viewModelScope.launch {
            runCatching {
                conversationSender.sendTextMessage(
                    childId = DevSettings.CHILD_ID,
                    sessionId = sessionId,
                    text = trimmedText,
                )
            }.onSuccess { response ->
                renderAgentReply(response)
            }.onFailure {
                appendMessage(
                    ChatMessage(
                        id = nextMessageId("agent-error"),
                        author = MessageAuthor.Agent,
                        text = "小白狐现在没有连上后端。我们先停一下，请大人检查网络后再试。",
                    ),
                )
                _uiState.update {
                    it.copy(
                        quickActions = emptyList(),
                        agent = FoxAgentUiState(
                            mood = FoxMood.NetworkError,
                            motion = FoxMotion.NetworkError,
                            statusText = "我们先等大人检查网络。",
                        ),
                        voice = VoiceUiState(isVoiceInputReserved = true),
                        isSending = false,
                    )
                }
            }
        }
    }

    fun onQuickAction(action: QuickActionUi) {
        when (action.id) {
            "take_photo" -> showMockPhotoCapture(imagePurpose = IMAGE_PURPOSE_HOMEWORK)
            "share_photo" -> showMockPhotoCapture(imagePurpose = IMAGE_PURPOSE_SHARE)
            else -> sendText(action.label)
        }
    }

    fun updateMockProblemText(text: String) {
        _uiState.update { state ->
            val current = state.mockPhoto ?: return@update state
            state.copy(mockPhoto = current.copy(problemText = text, errorMessage = null))
        }
    }

    fun updateMockImagePurpose(imagePurpose: String) {
        _uiState.update { state ->
            val current = state.mockPhoto ?: return@update state
            state.copy(
                mockPhoto = current.copy(
                    imagePurpose = imagePurpose,
                    problemText = if (imagePurpose == IMAGE_PURPOSE_HOMEWORK) {
                        DEFAULT_MOCK_HOMEWORK_TEXT
                    } else {
                        DEFAULT_MOCK_IMAGE_SHARE_TEXT
                    },
                    errorMessage = null,
                ),
            )
        }
    }

    fun dismissMockPhotoCapture() {
        if (_uiState.value.mockPhoto?.isSubmitting == true) return
        _uiState.update { it.copy(mockPhoto = null) }
    }

    fun submitMockPhotoCapture() {
        val mockPhoto = _uiState.value.mockPhoto ?: return
        val problemText = mockPhoto.problemText.trim()
        if (problemText.isEmpty() || _uiState.value.isSending) {
            _uiState.update { state ->
                state.copy(
                    mockPhoto = mockPhoto.copy(
                        errorMessage = "请先写一点这张图片里有什么，再发送给小白狐。",
                    ),
                )
            }
            return
        }

        appendMessage(
            ChatMessage(
                id = nextMessageId("child-photo"),
                author = MessageAuthor.Child,
                text = if (mockPhoto.imagePurpose == IMAGE_PURPOSE_HOMEWORK) {
                    "我拍了一道题目。"
                } else {
                    "我拍了一张图片给小白狐看。"
                },
            ),
        )
        _uiState.update {
            it.copy(
                isSending = true,
                quickActions = emptyList(),
                mockPhoto = mockPhoto.copy(isSubmitting = true, errorMessage = null),
            )
        }

        viewModelScope.launch {
            runCatching {
                if (mockPhoto.imagePurpose == IMAGE_PURPOSE_HOMEWORK) {
                    attachmentRepository.createMockHomeworkPhoto(
                        childId = DevSettings.CHILD_ID,
                        sessionId = sessionId,
                        mockOcrText = problemText,
                    )
                } else {
                    attachmentRepository.createMockImageShare(
                        childId = DevSettings.CHILD_ID,
                        sessionId = sessionId,
                        mockVisionText = problemText,
                        imagePurpose = mockPhoto.imagePurpose,
                        childCaption = problemText,
                    )
                }
            }.onSuccess { attachmentResponse ->
                handleAttachmentResponse(attachmentResponse)
            }.onFailure {
                appendAgentMessage(
                    "这张题目暂时没有传到后端。我们先停一下，请大人检查网络后再试。",
                )
                _uiState.update {
                    it.copy(
                        isSending = false,
                        quickActions = emptyList(),
                        mockPhoto = null,
                    )
                }
            }
        }
    }

    private fun showMockPhotoCapture(imagePurpose: String = IMAGE_PURPOSE_SHARE) {
        if (_uiState.value.isSending) return
        _uiState.update {
            it.copy(
                mockPhoto = MockPhotoUiState(
                    imagePurpose = imagePurpose,
                    problemText = if (imagePurpose == IMAGE_PURPOSE_HOMEWORK) {
                        DEFAULT_MOCK_HOMEWORK_TEXT
                    } else {
                        DEFAULT_MOCK_IMAGE_SHARE_TEXT
                    },
                ),
                quickActions = emptyList(),
            )
        }
    }

    private suspend fun handleAttachmentResponse(
        attachmentResponse: AttachmentCreateResponse,
    ) {
        if (!attachmentResponse.hasReadyHomeworkText) {
            renderAgentReply(
                reply = attachmentResponse.reply,
                uiActions = attachmentResponse.uiActions,
                sessionState = attachmentResponse.sessionState,
                mockPhoto = null,
            )
            return
        }

        runCatching {
            conversationSender.sendTextMessage(
                childId = DevSettings.CHILD_ID,
                sessionId = sessionId,
                text = "这是刚才拍的题目",
                attachments = listOf(attachmentResponse.attachmentId),
            )
        }.onSuccess { response ->
            renderAgentReply(response, mockPhoto = null)
        }.onFailure {
            appendAgentMessage(
                "题目已经识别到了，但还没有连上后端继续引导。请大人检查网络后再试。",
            )
            _uiState.update {
                it.copy(
                    quickActions = emptyList(),
                    sessionState = attachmentResponse.sessionState,
                    agent = FoxAgentUiState(
                        mood = FoxMood.NetworkError,
                        motion = FoxMotion.NetworkError,
                        statusText = "题目在这里，我们等后端恢复。",
                    ),
                    voice = VoiceUiState(isVoiceInputReserved = true),
                    isSending = false,
                    mockPhoto = null,
                )
            }
        }
    }

    fun attachTtsController(controller: TtsController) {
        if (ttsController === controller) return
        ttsController.stop()
        ttsController = controller
        _uiState.update { state ->
            state.copy(
                tts = state.tts.copy(
                    isAvailable = true,
                    isInitializing = false,
                    isInitialized = false,
                    isSpeaking = false,
                    isSpeakingPending = false,
                    errorMessage = null,
                ),
            )
        }
    }

    fun stopTtsPlayback() {
        stopCurrentTts(restoreBaseAgent = true)
    }

    fun toggleTtsMuted() {
        val willMute = !_uiState.value.tts.isMuted
        if (willMute) {
            stopCurrentTts(restoreBaseAgent = true)
        }
        _uiState.update { state ->
            state.copy(
                tts = state.tts.copy(
                    isMuted = willMute,
                    isSpeaking = if (willMute) false else state.tts.isSpeaking,
                    isSpeakingPending = if (willMute) {
                        false
                    } else {
                        state.tts.isSpeakingPending
                    },
                    errorMessage = null,
                ),
            )
        }
    }

    fun shutdownTts() {
        stopCurrentTts(restoreBaseAgent = true)
        ttsController.shutdown()
        ttsController = NoOpTtsController
    }

    override fun onCleared() {
        shutdownTts()
        super.onCleared()
    }

    internal fun recordChildMessage(text: String) {
        appendMessage(
            ChatMessage(
                id = nextMessageId("child"),
                author = MessageAuthor.Child,
                text = text,
            ),
        )
    }

    internal fun renderAgentReply(
        response: ConversationMessageResponse,
        mockPhoto: MockPhotoUiState? = _uiState.value.mockPhoto,
    ) {
        renderAgentReply(
            reply = response.reply,
            uiActions = response.uiActions,
            sessionState = response.sessionState,
            mockPhoto = mockPhoto,
        )
    }

    internal fun renderAgentReply(
        reply: ConversationReply,
        uiActions: List<ConversationUiAction>,
        sessionState: ConversationSessionState,
        mockPhoto: MockPhotoUiState? = _uiState.value.mockPhoto,
    ) {
        appendAgentMessage(reply.text)
        stopCurrentTts(restoreBaseAgent = false)

        val nextAgentState = reply.toFoxAgentUiState()
        baseAgentState = nextAgentState
        _uiState.update { state ->
            state.copy(
                quickActions = uiActions.toQuickActionUi(),
                sessionState = sessionState,
                agent = nextAgentState,
                voice = reply.toVoiceUiState(),
                tts = state.tts.copy(
                    isSpeaking = false,
                    isSpeakingPending = false,
                    isAvailable = true,
                    errorMessage = null,
                    lastFailureReason = null,
                ),
                isSending = false,
                mockPhoto = mockPhoto,
            )
        }
        maybeAutoReadReply(reply)
    }

    private fun appendAgentMessage(text: String) {
        appendMessage(
            ChatMessage(
                id = nextMessageId("agent"),
                author = MessageAuthor.Agent,
                text = text,
            ),
        )
    }

    private fun appendMessage(message: ChatMessage) {
        _uiState.update { state ->
            state.copy(messages = state.messages + message)
        }
    }

    private fun nextMessageId(prefix: String): String {
        nextMessageIndex += 1
        return "$prefix-$nextMessageIndex"
    }

    private fun maybeAutoReadReply(reply: ConversationReply) {
        val currentTts = _uiState.value.tts
        if (
            !reply.voiceEnabled ||
            reply.text.isBlank() ||
            !currentTts.isAutoReadEnabled ||
            currentTts.isMuted
        ) {
            return
        }

        val token = nextTtsToken()
        val accepted = ttsController.speak(
            request = TtsRequest(
                text = reply.text,
                voiceProfile = VoiceProfile.default(),
                audioUrl = reply.audioUrl,
                backendBaseUrl = DevSettings.conversationApiBaseUrl,
            ),
            callbacks = TtsCallbacks(
                onDiagnostics = { diagnostics ->
                    if (token == ttsToken) {
                        _uiState.update { state ->
                            state.copy(tts = state.tts.withDiagnostics(diagnostics))
                        }
                    }
                },
                onStart = {
                    if (token == ttsToken) {
                        _uiState.update { state ->
                            state.copy(
                                agent = baseAgentState.asSpeaking(),
                                tts = state.tts.copy(
                                    isSpeaking = true,
                                    isSpeakingPending = false,
                                    isAvailable = true,
                                    errorMessage = null,
                                ),
                            )
                        }
                    }
                },
                onDone = {
                    if (token == ttsToken) {
                        _uiState.update { state ->
                            state.copy(
                                agent = baseAgentState,
                                tts = state.tts.copy(
                                    isSpeaking = false,
                                    isSpeakingPending = false,
                                ),
                            )
                        }
                    }
                },
                onError = { message ->
                    if (token == ttsToken) {
                        _uiState.update { state ->
                            state.copy(
                                agent = baseAgentState,
                                tts = state.tts.copy(
                                    isSpeaking = false,
                                    isSpeakingPending = false,
                                    isAvailable = state.tts.isAvailable,
                                    errorMessage = message.ifBlank {
                                        TtsController.UNAVAILABLE_MESSAGE
                                    },
                                ),
                            )
                        }
                    }
                },
            ),
        )

        if (!accepted) {
            _uiState.update { state ->
                state.copy(
                    agent = baseAgentState,
                    tts = state.tts.copy(
                        isSpeaking = false,
                        isSpeakingPending = false,
                        isAvailable = false,
                        errorMessage = state.tts.errorMessage
                            ?: TtsController.UNAVAILABLE_MESSAGE,
                        lastFailureReason = state.tts.lastFailureReason
                            ?: "TtsController.speak returned false",
                    ),
                )
            }
            return
        }

        _uiState.update { state ->
            state.copy(
                agent = baseAgentState.asSpeakingPending(),
                tts = state.tts.copy(
                    isSpeaking = state.tts.isSpeaking,
                    isSpeakingPending = !state.tts.isSpeaking,
                    isAvailable = true,
                    errorMessage = null,
                    lastRequestedTextPreview = reply.text.previewForDiagnostics(),
                    lastFailureReason = null,
                ),
            )
        }
    }

    private fun stopCurrentTts(restoreBaseAgent: Boolean) {
        nextTtsToken()
        ttsController.stop()
        _uiState.update { state ->
            state.copy(
                agent = if (restoreBaseAgent) baseAgentState else state.agent,
                tts = state.tts.copy(
                    isSpeaking = false,
                    isSpeakingPending = false,
                ),
            )
        }
    }

    private fun nextTtsToken(): Int {
        ttsToken += 1
        return ttsToken
    }
}

data class ChatUiState(
    val messages: List<ChatMessage> = emptyList(),
    val quickActions: List<QuickActionUi> = emptyList(),
    val sessionState: ConversationSessionState? = null,
    val agent: FoxAgentUiState = FoxAgentUiState(),
    val voice: VoiceUiState = VoiceUiState(),
    val tts: TtsUiState = TtsUiState(),
    val isSending: Boolean = false,
    val mockPhoto: MockPhotoUiState? = null,
)

data class QuickActionUi(
    val id: String,
    val label: String,
)

data class MockPhotoUiState(
    val problemText: String = DEFAULT_MOCK_IMAGE_SHARE_TEXT,
    val imagePurpose: String = IMAGE_PURPOSE_SHARE,
    val isSubmitting: Boolean = false,
    val errorMessage: String? = null,
)

const val IMAGE_PURPOSE_SHARE = "share"
const val IMAGE_PURPOSE_HOMEWORK = "learning_homework"
const val DEFAULT_MOCK_IMAGE_SHARE_TEXT = "我搭了一个积木城堡，想给小白狐看看。"
const val DEFAULT_MOCK_HOMEWORK_TEXT = "小明有24个苹果，平均分给6个同学，每人几个？"

private fun List<ConversationUiAction>.toQuickActionUi(): List<QuickActionUi> {
    return flatMap { action ->
        action.actions.map { quickAction ->
            QuickActionUi(
                id = quickAction.id,
                label = quickAction.label,
            )
        }
    }
}

interface ConversationMessageSender {
    suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String> = emptyList(),
        timezone: String = DevSettings.TIMEZONE,
    ): ConversationMessageResponse
}

private class ConversationRepositoryMessageSender(
    private val repository: ConversationRepository = ConversationRepository(),
) : ConversationMessageSender {
    override suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        timezone: String,
    ): ConversationMessageResponse {
        return repository.sendTextMessage(
            childId = childId,
            sessionId = sessionId,
            text = text,
            attachments = attachments,
            timezone = timezone,
        )
    }
}
