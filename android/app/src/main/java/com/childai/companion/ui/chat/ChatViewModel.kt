package com.childai.companion.ui.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childai.companion.config.DevSettings
import com.childai.companion.data.conversation.ConversationRepository
import com.childai.companion.data.conversation.ConversationSessionState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID

class ChatViewModel(
    private val repository: ConversationRepository = ConversationRepository(),
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
                appendMessage(
                    ChatMessage(
                        id = nextMessageId("agent"),
                        author = MessageAuthor.Agent,
                        text = response.reply.text,
                    ),
                )
                _uiState.update {
                    it.copy(
                        quickActions = response.uiActions.flatMap { action ->
                            action.actions.map { quickAction ->
                                QuickActionUi(
                                    id = quickAction.id,
                                    label = quickAction.label,
                                )
                            }
                        },
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
        sendText(action.label)
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
)

data class QuickActionUi(
    val id: String,
    val label: String,
)
