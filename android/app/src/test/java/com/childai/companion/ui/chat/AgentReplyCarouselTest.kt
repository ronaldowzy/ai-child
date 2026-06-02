package com.childai.companion.ui.chat

import androidx.compose.ui.unit.dp
import com.childai.companion.data.conversation.CompanionObjectMeta
import com.childai.companion.data.conversation.ConversationSessionState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

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
        assertEquals("我在这里", childUiPolishStateLabel(ChildTurnUiPhase.Ready))
        assertEquals("我在听", childUiPolishStateLabel(ChildTurnUiPhase.Listening))
        assertEquals("在说给你听", childUiPolishStateLabel(ChildTurnUiPhase.Speaking))
        assertEquals("小白狐正在看", childUiPolishStateLabel(ChildTurnUiPhase.ImageProcessing))
        assertEquals("请家长帮忙看看", childUiPolishStateLabel(ChildTurnUiPhase.ServiceError))
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

    @Test
    fun portraitAndLandscapeKeepFoxAsPrimaryArea() {
        val portrait = companionLayoutWeights(isLandscape = false)
        val landscape = companionLayoutWeights(isLandscape = true)

        assertTrue(portrait.agent > portrait.conversation)
        assertTrue(landscape.agent > landscape.conversation)
        assertTrue(landscape.agent >= 0.50f)
    }

    @Test
    fun landscapeViewportClassSeparatesWidePhonesAndTablets() {
        assertEquals(
            CompanionRoomViewportClass.LandscapeWide,
            companionRoomViewportClass(maxWidth = 2712.dp, maxHeight = 1220.dp),
        )
        assertEquals(
            CompanionRoomViewportClass.LandscapeTablet,
            companionRoomViewportClass(maxWidth = 1280.dp, maxHeight = 800.dp),
        )
        assertEquals(
            CompanionRoomViewportClass.LandscapeSquare,
            companionRoomViewportClass(maxWidth = 1024.dp, maxHeight = 768.dp),
        )
        assertEquals(
            CompanionRoomViewportClass.Portrait,
            companionRoomViewportClass(maxWidth = 390.dp, maxHeight = 844.dp),
        )
        assertEquals(
            CompanionRoomViewportClass.PortraitExpanded,
            companionRoomViewportClass(maxWidth = 533.dp, maxHeight = 853.dp),
        )
    }

    @Test
    fun tabletLandscapeKeepsMascotPrimaryWhileGivingButtonsMoreRoom() {
        val wide = companionLayoutWeights(CompanionRoomViewportClass.LandscapeWide)
        val tablet = companionLayoutWeights(CompanionRoomViewportClass.LandscapeTablet)
        val tabletMetrics = companionLandscapeLayoutMetrics(
            viewportClass = CompanionRoomViewportClass.LandscapeTablet,
            compactLandscape = false,
        )

        assertTrue(tablet.agent > tablet.conversation)
        assertTrue(tablet.conversation > wide.conversation)
        assertEquals(720.dp, tabletMetrics.operationPanelMaxWidth)
    }

    @Test
    fun recentMessagesAreLightweightInsteadOfFullHistory() {
        val messages = (1..5).map { index ->
            ChatMessage(
                id = "m$index",
                author = if (index % 2 == 0) MessageAuthor.Child else MessageAuthor.Agent,
                text = "消息$index",
            )
        }

        val portraitMessages = companionVisibleMessages(messages, companionRecentMessageLimit(false))
        val landscapeMessages = companionVisibleMessages(messages, companionRecentMessageLimit(true))

        assertEquals(listOf("m5"), portraitMessages.map { it.id })
        assertEquals(listOf("m4", "m5"), landscapeMessages.map { it.id })
    }

    @Test
    fun defaultStageStatusMessageDoesNotEnterRecentMessageCards() {
        assertEquals(
            emptyList<ChatMessage>(),
            companionVisibleMessages(initialChatMessages(), companionRecentMessageLimit(false)),
        )

        val realOpening = initialChatMessages().map { message ->
            message.copy(text = "今天想说点什么呀？")
        }

        assertEquals(
            listOf("今天想说点什么呀？"),
            companionVisibleMessages(realOpening, companionRecentMessageLimit(false)).map { it.text },
        )
    }

    @Test
    fun openingBubbleDropsOutAsSoonAsChildStartsTalking() {
        val messages = listOf(
            ChatMessage(id = "agent-welcome", author = MessageAuthor.Agent, text = "窗边这颗小星星还没有名字"),
            ChatMessage(id = "child-1", author = MessageAuthor.Child, text = "那就叫亮亮"),
        )

        assertEquals(
            listOf("那就叫亮亮"),
            companionVisibleMessages(messages, companionRecentMessageLimit(true)).map { it.text },
        )
    }

    @Test
    fun imageContextShowsOnlyOneLowPressureCoCreationEntry() {
        val state = ChatUiState(
            pendingImageContext = PendingImageContextUiState(
                attachmentId = "att_image",
                summary = "一个作品",
                imagePurpose = IMAGE_PURPOSE_SHARE,
                recognizedType = "image_observation",
            ),
            quickActions = listOf(
                QuickActionUi(id = "companion_name", label = "起个名字"),
                QuickActionUi(id = "tell_story", label = "讲个故事"),
                QuickActionUi(id = "say_what_happened", label = "说说看"),
            ),
        )

        val actions = childCompanionVisibleQuickActions(state)

        assertEquals(1, actions.size)
        assertEquals("companion_name", actions.single().id)
        assertEquals("起个名字", actions.single().label)
    }

    @Test
    fun legacyImageStoryActionsAreHiddenFromVisibleQuickActions() {
        val state = ChatUiState(
            pendingImageContext = PendingImageContextUiState(
                attachmentId = "att_image",
                summary = "一个作品",
                imagePurpose = IMAGE_PURPOSE_SHARE,
                recognizedType = "image_observation",
            ),
            quickActions = listOf(
                QuickActionUi(id = "tell_story", label = "讲个故事"),
                QuickActionUi(id = "say_what_happened", label = "说说看"),
            ),
        )

        val actions = childCompanionVisibleQuickActions(state)

        assertTrue(actions.isEmpty())
    }

    @Test
    fun imageContextActionsAreHiddenWhenImageContextIsGone() {
        val state = ChatUiState(
            pendingImageContext = null,
            quickActions = listOf(
                QuickActionUi(id = "companion_name", label = "起个名字"),
                QuickActionUi(id = "topic_choice_1", label = "小车"),
            ),
        )

        assertEquals(
            listOf("小车"),
            childCompanionVisibleQuickActions(state).map { it.label },
        )
    }

    @Test
    fun legacyGiveNameActionNormalizesToCompanionName() {
        val state = ChatUiState(
            pendingImageContext = PendingImageContextUiState(
                attachmentId = "att_image",
                summary = "一个作品",
                imagePurpose = IMAGE_PURPOSE_SHARE,
                recognizedType = "image_observation",
            ),
            quickActions = listOf(
                QuickActionUi(id = "give_name", label = "起个名字"),
            ),
        )

        val action = childCompanionVisibleQuickActions(state).single()

        assertEquals("companion_name", action.id)
        assertEquals("起个名字", action.label)
    }

    @Test
    fun coCreateGuidanceKeepsSkipActionVisible() {
        val state = ChatUiState(
            quickActions = listOf(
                QuickActionUi(id = "companion_friend_name", label = "说个名字"),
                QuickActionUi(id = "companion_friend_image", label = "给小白狐看看"),
                QuickActionUi(id = "companion_skip", label = "先聊别的"),
            ),
            sessionState = ConversationSessionState(
                baseScene = "conversation.open",
                activeScene = "conversation.open",
                needsInput = null,
                requiresParentAttention = false,
                companionObject = CompanionObjectMeta(
                    id = "companion_1",
                    name = "宝石",
                    objectType = "star",
                    lightLocation = "窗边",
                    state = "active",
                    action = "co_create",
                    visualKind = "star",
                ),
            ),
        )

        assertEquals(
            listOf("说个名字", "给小白狐看看", "先聊别的"),
            childCompanionVisibleQuickActions(state).map { it.label },
        )
    }

    @Test
    fun startVoiceQuickActionIsHiddenBecauseVoiceButtonIsPrimary() {
        val state = ChatUiState(
            quickActions = listOf(
                QuickActionUi(id = "start_voice", label = "我想说话"),
                QuickActionUi(id = "topic_choice_1", label = "恐龙"),
            ),
        )

        assertEquals(
            listOf("恐龙"),
            childCompanionVisibleQuickActions(state).map { it.label },
        )
    }

    @Test
    fun openingQuickActionsKeepWelcomeBubblePinnedBeforeChildSpeaks() {
        val state = ChatUiState(
            messages = listOf(
                ChatMessage(id = "agent-welcome", author = MessageAuthor.Agent, text = "窗边这颗小星星还没有名字"),
            ),
            quickActions = listOf(
                QuickActionUi(id = "companion_name", label = "起个名字"),
                QuickActionUi(id = "companion_skip", label = "先看看"),
            ),
            sessionState = ConversationSessionState(
                baseScene = "conversation.open",
                activeScene = "conversation.open",
                needsInput = null,
                requiresParentAttention = false,
                companionObject = CompanionObjectMeta(
                    id = "star_seed",
                    name = "小星星",
                    objectType = "star",
                    lightLocation = "窗边",
                    state = "seed",
                    action = "name_seed",
                ),
            ),
        )

        assertEquals("agent-welcome", companionPinnedBubbleMessageId(state))
        assertEquals(listOf("起个名字", "先看看"), childCompanionVisibleQuickActions(state).map { it.label })
    }

    @Test
    fun nonOpeningCompanionNameActionIsHiddenInNormalChat() {
        val state = ChatUiState(
            messages = listOf(
                ChatMessage(id = "child-1", author = MessageAuthor.Child, text = "这个像飞船"),
                ChatMessage(id = "agent-1", author = MessageAuthor.Agent, text = "我也觉得像飞船"),
            ),
            quickActions = listOf(
                QuickActionUi(id = "companion_name", label = "起个名字"),
                QuickActionUi(id = "topic_choice_1", label = "恐龙"),
            ),
            sessionState = ConversationSessionState(
                baseScene = "conversation.open",
                activeScene = "conversation.open",
                needsInput = null,
                requiresParentAttention = false,
            ),
        )

        assertNull(companionPinnedBubbleMessageId(state))
        assertEquals(listOf("恐龙"), childCompanionVisibleQuickActions(state).map { it.label })
    }

    @Test
    fun hdFramePathsUseFramesDirectoryWithoutDuplicatingPrefix() {
        val rootDir = createTempDir(prefix = "hd_frames_test")
        try {
            val framesDir = File(rootDir, "frames_webp").apply { mkdirs() }
            File(framesDir, "fox_speaking_0001.webp").writeBytes(byteArrayOf(1, 2, 3))

            assertEquals(
                listOf(File(framesDir, "fox_speaking_0001.webp").absolutePath),
                buildHdFramePaths(
                    framesDir = framesDir,
                    framePattern = "frames_webp/fox_speaking_%04d.webp",
                    frameCount = 1,
                ),
            )
        } finally {
            rootDir.deleteRecursively()
        }
    }
}
