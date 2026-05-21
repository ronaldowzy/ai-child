package com.childai.companion.ui.chat

enum class MessageAuthor {
    Agent,
    Child,
}

data class ChatMessage(
    val id: String,
    val author: MessageAuthor,
    val text: String,
)

fun initialChatMessages(): List<ChatMessage> = listOf(
    ChatMessage(
        id = "agent-welcome",
        author = MessageAuthor.Agent,
        text = "我准备好啦。",
    ),
)
