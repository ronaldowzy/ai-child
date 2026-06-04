package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.data.showcase.XiaozhantaiItem
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.json.JSONObject

class ChatViewModelXiaozhantaiRecallTest {
    @Test
    fun showcaseItemBuildsRecallContextForChatNavigation() {
        val item = showcaseItem(
            id = "stand_item_001",
            name = "小石头",
            photoUri = "/tmp/photo.jpg",
            foxQuote = "它看起来像一颗安静的小星球。",
            createdAt = 1760000000000L,
        )

        val context = item.toRecallContext()

        assertEquals("stand_item_001", context.itemId)
        assertEquals("小石头", context.name)
        assertEquals("/tmp/photo.jpg", context.photoUri)
        assertEquals("它看起来像一颗安静的小星球。", context.foxQuote)
        assertEquals(1760000000000L, context.createdAt)
    }

    @Test
    fun recallContextAddsAgentMessageAndCard() {
        val viewModel = viewModel()

        viewModel.recallXiaozhantaiItem(
            XiaozhantaiRecallContext(
                itemId = "stand_item_001",
                name = "小石头",
                photoUri = "/tmp/photo.jpg",
                foxQuote = "它看起来像一颗安静的小星球。",
                createdAt = 1760000000000L,
            ),
        )

        val state = viewModel.uiState.value
        val message = state.messages.last()
        assertEquals(MessageAuthor.Agent, message.author)
        assertTrue(message.text.contains("我们又看到「小石头」啦"))
        assertTrue(message.text.contains("小白狐说：它看起来像一颗安静的小星球。"))
        assertEquals(message.text, state.agentReplyText)
        assertNotNull(message.xiaozhantaiRecallCard)
        assertEquals("stand_item_001", message.xiaozhantaiRecallCard!!.itemId)
        assertEquals("小石头", message.xiaozhantaiRecallCard!!.name)
        assertEquals("/tmp/photo.jpg", message.xiaozhantaiRecallCard!!.photoUri)
    }

    @Test
    fun recallContextUsesGentleFallbacksForBlankNameAndQuote() {
        val viewModel = viewModel()

        viewModel.recallXiaozhantaiItem(
            XiaozhantaiRecallContext(
                itemId = "stand_item_blank",
                name = "  \n ",
                photoUri = "/tmp/missing.jpg",
                foxQuote = "",
                createdAt = 1760000000001L,
            ),
        )

        val message = viewModel.uiState.value.messages.last()
        assertTrue(message.text.contains("我们又看到「小发现」啦"))
        assertTrue(message.text.contains("小白狐说：小白狐看见了这个小发现。"))
        assertEquals("小发现", message.xiaozhantaiRecallCard!!.name)
    }

    @Test
    fun duplicateRecallDoesNotAppendConsecutiveDuplicateMessage() {
        val viewModel = viewModel()
        val context = XiaozhantaiRecallContext(
            itemId = "stand_item_001",
            name = "小石头",
            photoUri = "/tmp/photo.jpg",
            foxQuote = "它看起来像一颗安静的小星球。",
            createdAt = 1760000000000L,
        )

        viewModel.recallXiaozhantaiItem(context)
        val sizeAfterFirstRecall = viewModel.uiState.value.messages.size
        viewModel.recallXiaozhantaiItem(context)

        assertEquals(sizeAfterFirstRecall, viewModel.uiState.value.messages.size)
    }

    @Test
    fun nextChildMessageSendsRecallContextToBackendButKeepsVisibleTextClean() {
        val sender = CapturingConversationSender()
        val viewModel = viewModel(sender)
        viewModel.recallXiaozhantaiItem(
            XiaozhantaiRecallContext(
                itemId = "stand_item_001",
                name = "小石头",
                photoUri = "/private/app/photo.jpg",
                foxQuote = "它看起来像一颗安静的小星球。",
                createdAt = 1760000000000L,
            ),
        )

        viewModel.sendText("我还记得它")

        val childMessage = viewModel.uiState.value.messages.first { it.text == "我还记得它" }
        assertEquals(MessageAuthor.Child, childMessage.author)
        assertTrue(sender.sentText!!.contains("孩子正在回看小展台里的「小石头」"))
        assertTrue(sender.sentText!!.contains("小白狐当时说：它看起来像一颗安静的小星球。"))
        assertTrue(sender.sentText!!.contains("孩子刚才说：我还记得它"))
        assertTrue(!sender.sentText!!.contains("/private/app/photo.jpg"))
    }

    private fun viewModel(
        conversationSender: ConversationMessageSender = CapturingConversationSender(),
    ): ChatViewModel {
        return ChatViewModel(
            conversationSender = conversationSender,
            sendDispatcher = Dispatchers.Unconfined,
            requestOpeningOnInit = false,
        )
    }

    private fun showcaseItem(
        id: String,
        name: String,
        photoUri: String,
        foxQuote: String,
        createdAt: Long,
    ): XiaozhantaiItem {
        return XiaozhantaiItem(
            id = id,
            photoUri = photoUri,
            name = name,
            foxQuote = foxQuote,
            createdAt = createdAt,
        )
    }
}

private class CapturingConversationSender : ConversationMessageSender {
    var sentText: String? = null

    override suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        quickActionId: String?,
        timezone: String,
    ): ConversationMessageResponse {
        sentText = text
        return response()
    }

    override suspend fun streamTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        quickActionId: String?,
        timezone: String,
        includeTts: Boolean,
        onEvent: (ConversationStreamEvent) -> Unit,
    ) {
        sentText = text
        onEvent(
            ConversationStreamEvent(
                type = "text_delta",
                payload = JSONObject().put("delta", "我们可以继续慢慢看它"),
            ),
        )
        onEvent(
            ConversationStreamEvent(
                type = "done",
                payload = JSONObject(),
            ),
        )
    }

    private fun response(): ConversationMessageResponse {
        return ConversationMessageResponse(
            reply = ConversationReply(
                type = "agent_message",
                text = "我们可以继续慢慢看它",
                voiceEnabled = false,
                audioUrl = null,
                emotion = "calm",
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
