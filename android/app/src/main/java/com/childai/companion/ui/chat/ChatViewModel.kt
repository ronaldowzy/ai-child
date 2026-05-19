package com.childai.companion.ui.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childai.companion.config.DevSettings
import com.childai.companion.data.attachment.AttachmentCreateResponse
import com.childai.companion.data.attachment.AttachmentRepository
import com.childai.companion.data.conversation.ConversationRepository
import com.childai.companion.data.conversation.ConversationUiAction
import com.childai.companion.data.conversation.ConversationSessionState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID

class ChatViewModel(
    private val repository: ConversationRepository = ConversationRepository(),
    private val attachmentRepository: AttachmentRepository = AttachmentRepository(),
) : ViewModel() {
    private val sessionId = "android-${UUID.randomUUID()}"
    private var nextMessageIndex = 0

    private val _uiState = MutableStateFlow(
        ChatUiState(
            messages = initialChatMessages(),
        ),
    )
    val uiState: StateFlow<ChatUiState> = _uiState

    fun sendText(text: String) {
        val trimmedText = text.trim()
        if (trimmedText.isEmpty() || _uiState.value.isSending) return

        appendMessage(
            ChatMessage(
                id = nextMessageId("child"),
                author = MessageAuthor.Child,
                text = trimmedText,
            ),
        )
        _uiState.update {
            it.copy(
                isSending = true,
                quickActions = emptyList(),
            )
        }

        viewModelScope.launch {
            runCatching {
                repository.sendTextMessage(
                    childId = DevSettings.CHILD_ID,
                    sessionId = sessionId,
                    text = trimmedText,
                )
            }.onSuccess { response ->
                appendAgentMessage(response.reply.text)
                _uiState.update {
                    it.copy(
                        quickActions = response.uiActions.toQuickActionUi(),
                        sessionState = response.sessionState,
                        isSending = false,
                    )
                }
            }.onFailure {
                appendMessage(
                    ChatMessage(
                        id = nextMessageId("agent-error"),
                        author = MessageAuthor.Agent,
                        text = "小狐狸现在没有连上后端。我们先停一下，请大人检查网络后再试。",
                    ),
                )
                _uiState.update {
                    it.copy(
                        quickActions = emptyList(),
                        isSending = false,
                    )
                }
            }
        }
    }

    fun onQuickAction(action: QuickActionUi) {
        when (action.id) {
            "take_photo" -> showMockPhotoCapture()
            else -> sendText(action.label)
        }
    }

    fun updateMockProblemText(text: String) {
        _uiState.update { state ->
            val current = state.mockPhoto ?: return@update state
            state.copy(mockPhoto = current.copy(problemText = text, errorMessage = null))
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
                        errorMessage = "请先保留题目文字，再发送给小狐狸。",
                    ),
                )
            }
            return
        }

        appendMessage(
            ChatMessage(
                id = nextMessageId("child-photo"),
                author = MessageAuthor.Child,
                text = "我拍了一道题目。",
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
                attachmentRepository.createMockHomeworkPhoto(
                    childId = DevSettings.CHILD_ID,
                    sessionId = sessionId,
                    mockOcrText = problemText,
                )
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

    private fun showMockPhotoCapture() {
        if (_uiState.value.isSending) return
        _uiState.update {
            it.copy(
                mockPhoto = MockPhotoUiState(),
                quickActions = emptyList(),
            )
        }
    }

    private suspend fun handleAttachmentResponse(
        attachmentResponse: AttachmentCreateResponse,
    ) {
        if (!attachmentResponse.hasReadyHomeworkText) {
            appendAgentMessage(attachmentResponse.reply.text)
            _uiState.update {
                it.copy(
                    quickActions = attachmentResponse.uiActions.toQuickActionUi(),
                    sessionState = attachmentResponse.sessionState,
                    isSending = false,
                    mockPhoto = null,
                )
            }
            return
        }

        runCatching {
            repository.sendTextMessage(
                childId = DevSettings.CHILD_ID,
                sessionId = sessionId,
                text = "这是刚才拍的题目",
                attachments = listOf(attachmentResponse.attachmentId),
            )
        }.onSuccess { response ->
            appendAgentMessage(response.reply.text)
            _uiState.update {
                it.copy(
                    quickActions = response.uiActions.toQuickActionUi(),
                    sessionState = response.sessionState,
                    isSending = false,
                    mockPhoto = null,
                )
            }
        }.onFailure {
            appendAgentMessage(
                "题目已经识别到了，但还没有连上后端继续引导。请大人检查网络后再试。",
            )
            _uiState.update {
                it.copy(
                    quickActions = emptyList(),
                    sessionState = attachmentResponse.sessionState,
                    isSending = false,
                    mockPhoto = null,
                )
            }
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

    private fun nextMessageId(prefix: String): String {
        nextMessageIndex += 1
        return "$prefix-$nextMessageIndex"
    }
}

data class ChatUiState(
    val messages: List<ChatMessage> = emptyList(),
    val quickActions: List<QuickActionUi> = emptyList(),
    val sessionState: ConversationSessionState? = null,
    val isSending: Boolean = false,
    val mockPhoto: MockPhotoUiState? = null,
)

data class QuickActionUi(
    val id: String,
    val label: String,
)

data class MockPhotoUiState(
    val problemText: String = DEFAULT_MOCK_HOMEWORK_TEXT,
    val isSubmitting: Boolean = false,
    val errorMessage: String? = null,
)

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
