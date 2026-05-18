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
        text = "我在这里。你可以慢慢说，一次说一件小事就好。",
    ),
)
