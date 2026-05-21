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
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.data.conversation.ConversationUiAction
import com.childai.companion.voice.AudioSegment
import com.childai.companion.voice.AudioSegmentQueueCallbacks
import com.childai.companion.voice.AudioSegmentQueuePlayer
import com.childai.companion.voice.NoOpTtsController
import com.childai.companion.voice.TtsCallbacks
import com.childai.companion.voice.TtsController
import com.childai.companion.voice.TtsRequest
import com.childai.companion.voice.TtsUiState
import com.childai.companion.voice.VoiceProfile
import com.childai.companion.voice.previewForDiagnostics
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
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
    private val sendDispatcher: CoroutineDispatcher = Dispatchers.Main.immediate,
) : ViewModel() {
    private val sessionId = "android-${UUID.randomUUID()}"
    private var nextMessageIndex = 0
    private var baseAgentState = FoxAgentUiState()
    private var ttsToken = 0
    private var streamingAgentMessageId: String? = null

    private val _uiState = MutableStateFlow(
        ChatUiState(
            messages = initialChatMessages(),
            tts = initialTtsUiState,
        ),
    )
    val uiState: StateFlow<ChatUiState> = _uiState
    private val audioSegmentQueuePlayer = AudioSegmentQueuePlayer(
        ttsController = ttsController,
        backendBaseUrl = DevSettings.conversationApiBaseUrl,
        isMuted = { _uiState.value.tts.isMuted },
        callbacks = AudioSegmentQueueCallbacks(
            onDiagnostics = { diagnostics ->
                _uiState.update { state ->
                    state.copy(tts = state.tts.withDiagnostics(diagnostics))
                }
            },
            onStart = {
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
            },
            onQueueDrained = {
                _uiState.update { state ->
                    state.copy(
                        agent = baseAgentState,
                        tts = state.tts.copy(
                            isSpeaking = false,
                            isSpeakingPending = false,
                        ),
                    )
                }
            },
            onError = { message ->
                _uiState.update { state ->
                    state.copy(
                        agent = baseAgentState,
                        tts = state.tts.copy(
                            isSpeaking = false,
                            isSpeakingPending = false,
                            errorMessage = message.ifBlank {
                                TtsController.AUDIO_PLAYBACK_UNAVAILABLE_MESSAGE
                            },
                        ),
                    )
                }
            },
        ),
    )

    fun sendText(text: String) {
        val trimmedText = text.trim()
        if (trimmedText.isEmpty() || _uiState.value.isSending) return

        sendTextWithAttachments(trimmedText, emptyList())
    }

    private fun sendTextWithAttachments(text: String, attachments: List<String>) {
        if (_uiState.value.isSending) return

        recordChildMessage(text)
        _uiState.update {
            it.copy(
                isSending = true,
                quickActions = emptyList(),
            )
        }

        viewModelScope.launch(sendDispatcher) {
            if (DevSettings.USE_STREAMING_CONVERSATION) {
                val streamed = runCatching {
                    streamTextWithAttachments(text = text, attachments = attachments)
                }.getOrDefault(false)
                if (streamed) return@launch
            }

            runCatching {
                conversationSender.sendTextMessage(
                    childId = DevSettings.CHILD_ID,
                    sessionId = sessionId,
                    text = text,
                    attachments = attachments,
                )
            }.onSuccess { response ->
                renderAgentReply(
                    response = response,
                    replaceMessageId = streamingAgentMessageId,
                )
            }.onFailure {
                appendMessage(
                    ChatMessage(
                        id = nextMessageId("agent-error"),
                        author = MessageAuthor.Agent,
                        text = followupFailureMessage(attachments),
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
            "talk_about_image", "make_story", "ask_what_is_this" ->
                continuePendingImageConversation(action)
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

        viewModelScope.launch(sendDispatcher) {
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
                    uploadFailureMessage(mockPhoto.imagePurpose),
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
                pendingImageContext = attachmentResponse.toPendingImageContext(),
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
                    pendingImageContext = null,
                )
            }
        }
    }

    private fun continuePendingImageConversation(action: QuickActionUi) {
        val context = _uiState.value.pendingImageContext
        if (context == null) {
            sendText(action.label)
            return
        }
        val text = when (action.id) {
            "make_story" -> "请根据刚才那张图片编一个小故事：${context.summary}"
            "ask_what_is_this" -> "我想问刚才那张图片里这是什么：${context.summary}"
            else -> "我们继续聊刚才那张图片：${context.summary}"
        }
        sendTextWithAttachments(text, listOf(context.attachmentId))
    }

    fun attachTtsController(controller: TtsController) {
        if (ttsController === controller) return
        ttsController.stop()
        ttsController = controller
        audioSegmentQueuePlayer.updateController(controller)
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
        replaceMessageId: String? = null,
    ) {
        renderAgentReply(
            reply = response.reply,
            uiActions = response.uiActions,
            sessionState = response.sessionState,
            mockPhoto = mockPhoto,
            pendingImageContext = _uiState.value.pendingImageContext,
            replaceMessageId = replaceMessageId,
        )
    }

    internal fun renderAgentReply(
        reply: ConversationReply,
        uiActions: List<ConversationUiAction>,
        sessionState: ConversationSessionState,
        mockPhoto: MockPhotoUiState? = _uiState.value.mockPhoto,
        pendingImageContext: PendingImageContextUiState? = _uiState.value.pendingImageContext,
        replaceMessageId: String? = null,
    ) {
        if (replaceMessageId.isNullOrBlank()) {
            appendAgentMessage(reply.text)
        } else {
            replaceMessageText(replaceMessageId, reply.text)
        }
        streamingAgentMessageId = null
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
                pendingImageContext = pendingImageContext,
            )
        }
        maybeAutoReadReply(reply)
    }

    private suspend fun streamTextWithAttachments(
        text: String,
        attachments: List<String>,
    ): Boolean {
        var doneReceived = false
        conversationSender.streamTextMessage(
            childId = DevSettings.CHILD_ID,
            sessionId = sessionId,
            text = text,
            attachments = attachments,
            includeTts = _uiState.value.tts.isAutoReadEnabled && !_uiState.value.tts.isMuted,
            onEvent = { event ->
                applyStreamEvent(event)
                if (event.type == "done") {
                    doneReceived = true
                }
            },
        )
        return doneReceived
    }

    internal fun applyStreamEvent(event: ConversationStreamEvent) {
        when (event.type) {
            "session_started" -> {
                stopCurrentTts(restoreBaseAgent = false)
                _uiState.update { state ->
                    state.copy(
                        isSending = true,
                        agent = FoxAgentUiState(
                            mood = FoxMood.Thinking,
                            motion = FoxMotion.ThinkingBlink,
                            statusText = "我先想一想。",
                        ),
                    )
                }
            }
            "route_decision" -> applyStreamRoute(event)
            "text_delta" -> appendToStreamingAgentBubble(event.delta)
            "sentence_ready" -> Unit
            "audio_ready" -> enqueueStreamAudio(event)
            "text_final" -> event.finalText?.let(::replaceStreamingAgentText)
            "done" -> {
                streamingAgentMessageId = null
                _uiState.update { state ->
                    state.copy(isSending = false)
                }
            }
            "error" -> applyStreamError(event)
        }
    }

    private fun applyStreamRoute(event: ConversationStreamEvent) {
        val activeScene = event.activeScene ?: "conversation.open"
        val sessionState = ConversationSessionState(
            baseScene = event.payload.optString("baseScene", event.payload.optString("base_scene", activeScene)),
            activeScene = activeScene,
            needsInput = null,
            requiresParentAttention = event.requiresParentAttention,
        )
        val nextAgentState = ConversationReply(
            type = "agent_message",
            text = "",
            voiceEnabled = true,
            audioUrl = null,
            emotion = event.emotion,
            agentMotion = event.agentMotion,
        ).toFoxAgentUiState()
        baseAgentState = nextAgentState
        _uiState.update { state ->
            state.copy(
                sessionState = sessionState,
                agent = nextAgentState,
            )
        }
    }

    private fun appendToStreamingAgentBubble(delta: String) {
        if (delta.isBlank()) return
        val messageId = streamingAgentMessageId
        if (messageId == null) {
            val newMessage = ChatMessage(
                id = nextMessageId("agent-stream"),
                author = MessageAuthor.Agent,
                text = delta,
            )
            streamingAgentMessageId = newMessage.id
            appendMessage(newMessage)
            return
        }
        _uiState.update { state ->
            state.copy(
                messages = state.messages.map { message ->
                    if (message.id == messageId) {
                        message.copy(text = message.text + delta)
                    } else {
                        message
                    }
                },
            )
        }
    }

    private fun replaceStreamingAgentText(text: String) {
        val messageId = streamingAgentMessageId
        if (messageId == null) {
            appendToStreamingAgentBubble(text)
        } else {
            replaceMessageText(messageId, text)
        }
    }

    private fun enqueueStreamAudio(event: ConversationStreamEvent) {
        val audioUrl = event.audioUrl ?: return
        if (_uiState.value.tts.isMuted) return
        audioSegmentQueuePlayer.enqueue(
            AudioSegment(
                audioUrl = audioUrl,
                text = event.audioText,
                index = event.payload.optInt("index", 0),
            ),
        )
        _uiState.update { state ->
            state.copy(
                tts = state.tts.copy(
                    isSpeakingPending = !state.tts.isSpeaking,
                    isAvailable = true,
                    errorMessage = null,
                ),
            )
        }
    }

    private fun applyStreamError(event: ConversationStreamEvent) {
        val message = event.safeMessage
            ?: "小白狐这次没有接稳，但已经显示的文字还在这里。"
        val hasPartialText = streamingAgentMessageId != null
        if (!hasPartialText) {
            appendAgentMessage(message)
        }
        _uiState.update { state ->
            state.copy(
                tts = state.tts.copy(errorMessage = message),
                agent = if (hasPartialText) state.agent else FoxAgentUiState(
                    mood = FoxMood.NetworkError,
                    motion = FoxMotion.NetworkError,
                    statusText = "我们先等大人检查网络。",
                ),
            )
        }
    }

    private fun uploadFailureMessage(imagePurpose: String): String {
        return if (imagePurpose == IMAGE_PURPOSE_HOMEWORK) {
            "这道题目暂时没有传到后端。我们先停一下，请大人检查网络后再试。"
        } else {
            "这张图片暂时没有传到后端。我们先停一下，请大人检查网络后再试。"
        }
    }

    private fun followupFailureMessage(attachments: List<String>): String {
        val context = _uiState.value.pendingImageContext
        if (attachments.isEmpty() || context == null) {
            return "小白狐现在没有连上后端。我们先停一下，请大人检查网络后再试。"
        }
        return if (context.imagePurpose == IMAGE_PURPOSE_HOMEWORK) {
            "题目已经识别到了，但还没有连上后端继续引导。请大人检查网络后再试。"
        } else {
            "图片已经识别到了，但还没有连上后端继续聊。请大人检查网络后再试。"
        }
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

    private fun replaceMessageText(messageId: String, text: String) {
        _uiState.update { state ->
            state.copy(
                messages = state.messages.map { message ->
                    if (message.id == messageId) {
                        message.copy(text = text)
                    } else {
                        message
                    }
                },
            )
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
        audioSegmentQueuePlayer.stopAndClear()
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
    val pendingImageContext: PendingImageContextUiState? = null,
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

data class PendingImageContextUiState(
    val attachmentId: String,
    val summary: String,
    val imagePurpose: String?,
    val recognizedType: String,
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

private fun AttachmentCreateResponse.toPendingImageContext(): PendingImageContextUiState? {
    if (
        recognizedContent.type == "homework_problem" ||
        recognizedContent.imagePurpose == IMAGE_PURPOSE_HOMEWORK
    ) {
        return null
    }
    val summary = recognizedContent.text
        ?: recognizedContent.childCaption
        ?: return null
    return PendingImageContextUiState(
        attachmentId = attachmentId,
        summary = summary,
        imagePurpose = recognizedContent.imagePurpose,
        recognizedType = recognizedContent.type,
    )
}

interface ConversationMessageSender {
    suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String> = emptyList(),
        timezone: String = DevSettings.TIMEZONE,
    ): ConversationMessageResponse

    suspend fun streamTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String> = emptyList(),
        timezone: String = DevSettings.TIMEZONE,
        includeTts: Boolean = true,
        onEvent: (ConversationStreamEvent) -> Unit,
    )
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

    override suspend fun streamTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        timezone: String,
        includeTts: Boolean,
        onEvent: (ConversationStreamEvent) -> Unit,
    ) {
        repository.streamTextMessage(
            childId = childId,
            sessionId = sessionId,
            text = text,
            attachments = attachments,
            timezone = timezone,
            includeTts = includeTts,
            onEvent = onEvent,
        )
    }
}
