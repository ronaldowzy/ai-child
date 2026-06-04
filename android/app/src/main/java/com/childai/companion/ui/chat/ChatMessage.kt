package com.childai.companion.ui.chat

import com.childai.companion.data.showcase.XiaozhantaiItem
import com.childai.companion.data.showcase.xiaozhantaiNormalizeFoxQuote
import com.childai.companion.data.showcase.xiaozhantaiNormalizeName

enum class MessageAuthor {
    Agent,
    Child,
}

data class ChatMessage(
    val id: String,
    val author: MessageAuthor,
    val text: String,
    val xiaozhantaiRecallCard: XiaozhantaiRecallCardUiState? = null,
)

fun initialChatMessages(): List<ChatMessage> = listOf(
    ChatMessage(
        id = "agent-welcome",
        author = MessageAuthor.Agent,
        text = "我在这里。",
    ),
)

data class XiaozhantaiRecallContext(
    val itemId: String,
    val name: String,
    val photoUri: String,
    val foxQuote: String,
    val createdAt: Long,
)

data class XiaozhantaiRecallCardUiState(
    val itemId: String,
    val name: String,
    val photoUri: String,
    val createdAt: Long,
)

fun XiaozhantaiItem.toRecallContext(): XiaozhantaiRecallContext {
    return XiaozhantaiRecallContext(
        itemId = id,
        name = name,
        photoUri = photoUri,
        foxQuote = foxQuote,
        createdAt = createdAt,
    )
}

fun XiaozhantaiRecallContext.normalized(): XiaozhantaiRecallContext {
    return copy(
        name = xiaozhantaiNormalizeName(name),
        foxQuote = xiaozhantaiNormalizeFoxQuote(foxQuote),
    )
}

fun xiaozhantaiRecallMessageText(context: XiaozhantaiRecallContext): String {
    val normalized = context.normalized()
    return "我们又看到「${normalized.name}」啦。还记得它当时被放进小展台的时候，小白狐说：${normalized.foxQuote}"
}

fun xiaozhantaiRecallRequestText(
    context: XiaozhantaiRecallContext,
    childText: String,
): String {
    val normalized = context.normalized()
    return "孩子正在回看小展台里的「${normalized.name}」。小白狐当时说：${normalized.foxQuote}\n孩子刚才说：${childText.trim()}"
}

fun XiaozhantaiRecallContext.toRecallCardUiState(): XiaozhantaiRecallCardUiState {
    val normalized = normalized()
    return XiaozhantaiRecallCardUiState(
        itemId = normalized.itemId,
        name = normalized.name,
        photoUri = normalized.photoUri,
        createdAt = normalized.createdAt,
    )
}
