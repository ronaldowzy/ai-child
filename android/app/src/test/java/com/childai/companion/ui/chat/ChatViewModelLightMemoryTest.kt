package com.childai.companion.ui.chat

import com.childai.companion.data.attachment.AttachmentCreateResponse
import com.childai.companion.data.attachment.AttachmentRepository
import com.childai.companion.data.attachment.PhotoUploadPayload
import com.childai.companion.data.attachment.RecognizedContent
import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.data.showcase.XiaozhantaiItem
import com.childai.companion.data.showcase.XiaozhantaiRepository
import com.childai.companion.data.showcase.XiaozhantaiSaveRequest
import com.childai.companion.ui.chat.lightmemory.LightMemorySource
import com.childai.companion.ui.chat.lightmemory.LightMemoryStatus
import com.childai.companion.ui.chat.strangedoor.StrangeDoorMechanismType
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatViewModelLightMemoryTest {
    @Test
    fun resetStartsWithEmptyLightMemorySnapshot() {
        val viewModel = viewModel()

        val lightMemory = viewModel.uiState.value.lightMemory
        assertTrue(lightMemory.candidates.isEmpty())
        assertTrue(lightMemory.activeCandidates.isEmpty())
        assertNull(lightMemory.recentMechanismType)
        assertNull(lightMemory.recentToolName)
        assertFalse(lightMemory.recalledInCurrentLifecycle)
        assertFalse(lightMemory.mutedForCurrentLifecycle)
    }

    @Test
    fun strangeDoorRiddleCompletedCreatesCompletedCandidateWithoutChildAnswer() {
        val viewModel = viewModel()

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorRiddleMethod()
        viewModel.answerStrangeDoorRiddle("水")

        val lightMemory = viewModel.uiState.value.lightMemory
        assertEquals(StrangeDoorMechanismType.Round, lightMemory.recentMechanismType)
        assertTrue(
            lightMemory.activeCandidates.any {
                it.source == LightMemorySource.StrangeDoorCompleted &&
                    it.mechanismType == StrangeDoorMechanismType.Round
            },
        )
        assertTrue(lightMemory.activeCandidates.none { it.displayName == "水" })
    }

    @Test
    fun safePhotoProgressRecordsRecentMechanismAndToolName() {
        val viewModel = viewModel(
            attachmentRepository = ImmediateLightMemoryAttachmentRepository(
                response = attachmentResponse(
                    recognizedText = "图片里有一个蓝色瓶盖",
                ),
            ),
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()
        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)

        val lightMemory = viewModel.uiState.value.lightMemory
        assertEquals(StrangeDoorMechanismType.Round, lightMemory.recentMechanismType)
        assertEquals("蓝盖盖转轮", lightMemory.recentToolName)
        assertTrue(
            lightMemory.activeCandidates.any {
                it.source == LightMemorySource.StrangeDoorTool &&
                    it.toolName == "蓝盖盖转轮"
            },
        )
    }

    @Test
    fun blockedPrivacyAndHomeworkPhotoDoesNotCreateActiveLightMemory() {
        val blockedCases = listOf(
            "privacy_sensitive" to "图片里有学校地址",
            "homework_problem" to "图片里有一道作业题目",
            "unsafe_unknown" to "图片里有隐私内容",
        )

        blockedCases.forEach { (type, text) ->
            val viewModel = viewModel(
                attachmentRepository = ImmediateLightMemoryAttachmentRepository(
                    response = attachmentResponse(
                        recognizedType = type,
                        recognizedText = text,
                    ),
                ),
            )

            viewModel.activateStrangeDoorDemo()
            viewModel.chooseStrangeDoorPhotoMethod()
            viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)

            assertTrue(viewModel.uiState.value.lightMemory.activeCandidates.isEmpty())
        }
    }

    @Test
    fun showcaseAssistReadsAllowedFieldsAndMarksAssistedDoor() {
        val viewModel = viewModel()
        val item = showcaseItem(
            id = "stand_item_assist",
            name = "蓝盖盖转轮",
            foxQuote = "门上的圆锁轻轻转了一小下",
            createdAt = 123L,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()
        viewModel.useXiaozhantaiItemForStrangeDoor(item)

        val candidate = viewModel.uiState.value.lightMemory.activeCandidates
            .single { it.source == LightMemorySource.ShowcaseAssist }
        assertEquals("stand_item_assist", candidate.showcaseItemId)
        assertEquals("蓝盖盖转轮", candidate.showcaseItemName)
        assertEquals(123L, candidate.showcaseCreatedAtMillis)
        assertEquals("门上的圆锁轻轻转了一小下", candidate.showcaseFoxQuote)
        assertTrue(candidate.assistedDoorInCurrentLifecycle)
    }

    @Test
    fun riskyFoxQuoteFromSavedShowcaseItemIsFiltered() {
        val showcaseRepository = CapturingLightMemoryShowcaseRepository(
            savedItemFoxQuote = "这里有学校地址",
        )
        val viewModel = viewModel(
            attachmentRepository = ImmediateLightMemoryAttachmentRepository(
                response = attachmentResponse(recognizedText = "图片里有一个小石头"),
            ),
            showcaseRepository = showcaseRepository,
        )

        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)
        val messageId = viewModel.uiState.value.imagePreviewCards.keys.single()
        viewModel.requestSavePhotoToXiaozhantai(messageId)
        viewModel.updateXiaozhantaiSaveName("小石头")
        viewModel.confirmXiaozhantaiSave()

        assertTrue(showcaseRepository.savedRequests.isNotEmpty())
        assertTrue(viewModel.uiState.value.lightMemory.activeCandidates.isEmpty())
    }

    @Test
    fun ordinaryChatOnlyUsesLightMemoryWhenChildMentionsApprovedKeyword() {
        val sender = CapturingLightMemoryConversationSender()
        val showcaseRepository = CapturingLightMemoryShowcaseRepository()
        val viewModel = viewModel(
            attachmentRepository = ImmediateLightMemoryAttachmentRepository(
                response = attachmentResponse(recognizedText = "图片里有一个小石头"),
            ),
            showcaseRepository = showcaseRepository,
            conversationSender = sender,
        )

        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)
        val messageId = viewModel.uiState.value.imagePreviewCards.keys.single()
        viewModel.requestSavePhotoToXiaozhantai(messageId)
        viewModel.updateXiaozhantaiSaveName("小石头")
        viewModel.confirmXiaozhantaiSave()

        val candidateId = viewModel.uiState.value.lightMemory.activeCandidates.single().id

        viewModel.sendText("今天想画画")
        assertNull(viewModel.uiState.value.lightMemory.relatedChatCandidateId)

        viewModel.sendText("我放进去的小发现还在吗")
        assertEquals(candidateId, viewModel.uiState.value.lightMemory.relatedChatCandidateId)
        assertTrue(sender.sentTexts.contains("今天想画画"))
        assertTrue(sender.sentTexts.contains("我放进去的小发现还在吗"))
    }

    @Test
    fun openingRecallIsLifecycleLocalAndCanBeMuted() {
        val viewModel = viewModel(
            attachmentRepository = ImmediateLightMemoryAttachmentRepository(
                response = attachmentResponse(recognizedText = "图片里有一个小石头"),
            ),
            showcaseRepository = CapturingLightMemoryShowcaseRepository(),
            conversationSender = CapturingLightMemoryConversationSender(),
        )

        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)
        val messageId = viewModel.uiState.value.imagePreviewCards.keys.single()
        viewModel.requestSavePhotoToXiaozhantai(messageId)
        viewModel.updateXiaozhantaiSaveName("小石头")
        viewModel.confirmXiaozhantaiSave()
        viewModel.requestOpeningGreeting()

        assertTrue(viewModel.uiState.value.lightMemory.openingRecallCandidateId != null)

        viewModel.markLightMemoryOpeningRecalled()
        assertTrue(viewModel.uiState.value.lightMemory.recalledInCurrentLifecycle)
        assertNull(viewModel.uiState.value.lightMemory.openingRecallCandidateId)

        viewModel.muteLightMemoryForLifecycle()
        val lightMemory = viewModel.uiState.value.lightMemory
        assertTrue(lightMemory.mutedForCurrentLifecycle)
        assertTrue(lightMemory.candidates.all { it.status != LightMemoryStatus.Active })
    }

    @Test
    fun languageGameDoesNotWriteLightMemorySnapshot() {
        val viewModel = viewModel()

        viewModel.startBrainTeaserGame()
        viewModel.sendText("水")

        assertTrue(viewModel.uiState.value.lightMemory.candidates.isEmpty())
    }

    private fun viewModel(
        attachmentRepository: AttachmentRepository = ImmediateLightMemoryAttachmentRepository(
            response = attachmentResponse(),
        ),
        showcaseRepository: XiaozhantaiRepository? = null,
        conversationSender: ConversationMessageSender = CapturingLightMemoryConversationSender(),
    ): ChatViewModel {
        return ChatViewModel(
            conversationSender = conversationSender,
            attachmentRepository = attachmentRepository,
            xiaozhantaiRepository = showcaseRepository,
            sendDispatcher = Dispatchers.Unconfined,
            requestOpeningOnInit = false,
            nowMillis = { 1_700_000_000L },
        )
    }

    private fun photoPayload(): PhotoUploadPayload {
        return PhotoUploadPayload(
            bytes = byteArrayOf(1, 2, 3),
            mimeType = "image/jpeg",
            fileName = "light-memory-test.jpg",
            previewBytes = byteArrayOf(4, 5),
        )
    }

    private fun showcaseItem(
        id: String = "stand_item",
        name: String = "小发现",
        foxQuote: String = "小白狐看见了这个小发现。",
        createdAt: Long = 1_700_000_000L,
    ): XiaozhantaiItem {
        return XiaozhantaiItem(
            id = id,
            photoUri = "/tmp/light-memory-showcase.jpg",
            name = name,
            foxQuote = foxQuote,
            createdAt = createdAt,
            source = "test",
            isDeleted = false,
        )
    }

    private fun attachmentResponse(
        recognizedType: String = "image_observation",
        recognizedText: String = "图片里有一个蓝色瓶盖",
        confidence: Double = 0.92,
    ): AttachmentCreateResponse {
        return AttachmentCreateResponse(
            attachmentId = "att_light_memory",
            recognizedContent = RecognizedContent(
                type = recognizedType,
                text = recognizedText,
                confidence = confidence,
                providerName = "fake",
                fallbackAction = null,
                imagePurpose = IMAGE_PURPOSE_SHARE,
                childCaption = "我给小白狐看了一张图",
            ),
            reply = ConversationReply(
                type = "agent_message",
                text = "这是一条测试回复",
                voiceEnabled = false,
                audioUrl = null,
                emotion = "encourage",
                agentMotion = "listening_tail",
            ),
            uiActions = emptyList(),
            sessionState = ConversationSessionState(
                baseScene = "conversation.open",
                activeScene = "conversation.open",
                needsInput = null,
                requiresParentAttention = false,
            ),
            mimeType = "image/jpeg",
            sizeBytes = 3,
        )
    }
}

private class ImmediateLightMemoryAttachmentRepository(
    private val response: AttachmentCreateResponse,
) : AttachmentRepository() {
    override suspend fun createCapturedImage(
        childId: String,
        sessionId: String,
        imageBytes: ByteArray,
        mimeType: String,
        fileName: String,
        imagePurpose: String,
        childCaption: String,
    ): AttachmentCreateResponse {
        return response
    }
}

private class CapturingLightMemoryShowcaseRepository(
    private val savedItemFoxQuote: String? = null,
) : XiaozhantaiRepository() {
    val savedRequests = mutableListOf<XiaozhantaiSaveRequest>()

    override suspend fun saveCapturedPhoto(request: XiaozhantaiSaveRequest): XiaozhantaiItem {
        savedRequests += request
        return XiaozhantaiItem(
            id = "stand_item_light_memory",
            photoUri = "/tmp/stand_item_light_memory.jpg",
            name = request.name,
            foxQuote = savedItemFoxQuote ?: request.foxQuote,
            createdAt = request.createdAt ?: 1_700_000_000L,
            source = request.source,
            isDeleted = false,
        )
    }
}

private class CapturingLightMemoryConversationSender : ConversationMessageSender {
    val sentTexts = mutableListOf<String>()

    override suspend fun requestOpening(
        childId: String,
        sessionId: String,
        timezone: String,
    ): ConversationMessageResponse {
        return response("今天想聊什么都可以")
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
        return response("小白狐听见了")
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

    private fun response(text: String): ConversationMessageResponse {
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
}
