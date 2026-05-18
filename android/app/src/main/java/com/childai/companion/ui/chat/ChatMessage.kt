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
        text = "放学回来啦。你可以先说一件今天印象最深的小事。",
    ),
    ChatMessage(
        id = "child-sample",
        author = MessageAuthor.Child,
        text = "我想先说作业。",
    ),
    ChatMessage(
        id = "agent-learning",
        author = MessageAuthor.Agent,
        text = "可以。我们先看看题目在问什么，再一起想第一步。",
    ),
)
