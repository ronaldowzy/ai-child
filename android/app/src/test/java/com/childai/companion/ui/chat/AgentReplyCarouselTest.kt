package com.childai.companion.ui.chat

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class AgentReplyCarouselTest {
    @Test
    fun splitsLongAgentReplyIntoReadableSegments() {
        val segments = agentReplyCarouselSegments(
            text = "晚上好呀，今天过得怎么样？你今天有没有遇到什么想跟我说的小事？我们可以慢慢聊。",
            maxChars = 24,
        )

        assertTrue(segments.size > 1)
        assertTrue(segments.all { it.length <= 24 })
        assertEquals("晚上好呀，今天过得怎么样？", segments.first())
    }

    @Test
    fun blankReplyReturnsNoSegments() {
        assertEquals(emptyList<String>(), agentReplyCarouselSegments("   "))
    }

    @Test
    fun stateChipLabelsStayShortAndChildFacing() {
        assertEquals("准备好了", childUiPolishStateLabel(ChildTurnUiPhase.Ready))
        assertEquals("正在听", childUiPolishStateLabel(ChildTurnUiPhase.Listening))
        assertEquals("正在说", childUiPolishStateLabel(ChildTurnUiPhase.Speaking))
        assertEquals("正在看图", childUiPolishStateLabel(ChildTurnUiPhase.ImageProcessing))
        assertEquals("请大人检查", childUiPolishStateLabel(ChildTurnUiPhase.ServiceError))
    }

    @Test
    fun topicShiftChipsAreBackendDrivenOnly() {
        val state = ChatUiState(
            messages = initialChatMessages() + ChatMessage(
                id = "agent-after-turn",
                author = MessageAuthor.Agent,
                text = "我们可以换个轻松点的话题。",
            ),
        )

        val actions = topicShiftChipActions(state)

        assertTrue(actions.isEmpty())
    }

    @Test
    fun topicShiftChipsDoNotHideBackendActionsOrActiveTurns() {
        val withBackendActions = ChatUiState(
            messages = initialChatMessages() + ChatMessage(
                id = "agent-after-turn",
                author = MessageAuthor.Agent,
                text = "可以拍给我看。",
            ),
            quickActions = listOf(QuickActionUi(id = "take_photo", label = "拍给小白狐看")),
        )
        val activeTurn = withBackendActions.copy(
            quickActions = emptyList(),
            isSending = true,
        )

        assertTrue(topicShiftChipActions(withBackendActions).isEmpty())
        assertTrue(topicShiftChipActions(activeTurn).isEmpty())
    }
}
