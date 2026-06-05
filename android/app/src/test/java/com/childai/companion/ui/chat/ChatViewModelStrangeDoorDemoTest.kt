package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoMethod
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoState
import com.childai.companion.ui.chat.strangedoor.StrangeDoorState
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatViewModelStrangeDoorDemoTest {
    @Test
    fun openingGreetingIsDeferredWhileStrangeDoorDemoIsActive() {
        val sender = StrangeDoorDemoSender()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.requestOpeningGreeting()

        assertEquals(0, sender.openingCalls)
        assertNotNull(viewModel.uiState.value.strangeDoorDemo)

        viewModel.exitStrangeDoorDemoAndRequestOpening()

        assertEquals(1, sender.openingCalls)
        assertEquals("豆豆，回来啦。", viewModel.uiState.value.messages.first().text)
        assertEquals(null, viewModel.uiState.value.strangeDoorDemo)
    }

    @Test
    fun activatingDemoStartsAtChoosingMethodWithClosedDoor() {
        val viewModel = ChatViewModel(
            conversationSender = StrangeDoorDemoSender(),
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.activateStrangeDoorDemo()

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorDemoState.ChoosingMethod, snapshot.demoState)
        assertEquals(StrangeDoorState.Closed, snapshot.doorState)
        assertFalse(strangeDoorShouldShowNormalInputBar(viewModel.uiState.value))
    }

    @Test
    fun choosingPhotoAndRiddleUpdateOnlyLocalDemoState() {
        val sender = StrangeDoorDemoSender()
        val viewModel = ChatViewModel(
            conversationSender = sender,
            sendDispatcher = Dispatchers.Unconfined,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()

        val photoSnapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorDemoState.PhotoPrompt, photoSnapshot.demoState)
        assertEquals(StrangeDoorDemoMethod.Photo, photoSnapshot.lastMethod)
        assertEquals(0, sender.sentTexts.size)
        assertEquals(0, sender.openingCalls)

        viewModel.returnToStrangeDoorMethodChoice()
        viewModel.chooseStrangeDoorRiddleMethod()

        val riddleSnapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorDemoState.RiddlePrompt, riddleSnapshot.demoState)
        assertEquals(StrangeDoorDemoMethod.Riddle, riddleSnapshot.lastMethod)
        assertTrue(viewModel.uiState.value.quickActions.isEmpty())
    }
}

private class StrangeDoorDemoSender : ConversationMessageSender {
    var openingCalls = 0
    val sentTexts = mutableListOf<String>()

    override suspend fun requestOpening(
        childId: String,
        sessionId: String,
        timezone: String,
    ): ConversationMessageResponse {
        openingCalls += 1
        return strangeDoorDemoResponse("豆豆，回来啦。")
    }

    override suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        quickActionId: String?,
        timezone: String,
    ): ConversationMessageResponse {
        sentTexts += text
        return strangeDoorDemoResponse("收到。")
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
    ) = Unit
}

private fun strangeDoorDemoResponse(text: String): ConversationMessageResponse {
    return ConversationMessageResponse(
        reply = ConversationReply(
            type = "agent_message",
            text = text,
            voiceEnabled = false,
            audioUrl = null,
            emotion = "warm",
            agentMotion = "gentle_idle",
        ),
        sessionState = ConversationSessionState(
            baseScene = "conversation.open",
            activeScene = "conversation.open",
            needsInput = null,
            requiresParentAttention = false,
        ),
        uiActions = emptyList(),
    )
}
