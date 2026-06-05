package com.childai.companion.ui.chat

import com.childai.companion.data.attachment.AttachmentCreateResponse
import com.childai.companion.data.attachment.AttachmentRepository
import com.childai.companion.data.attachment.PhotoUploadPayload
import com.childai.companion.data.attachment.RecognizedContent
import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.data.growth.GrowthEvent
import com.childai.companion.data.growth.GrowthEventRepository
import com.childai.companion.data.showcase.XiaozhantaiItem
import com.childai.companion.data.showcase.XiaozhantaiRepository
import com.childai.companion.data.showcase.XiaozhantaiSaveRequest
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoState
import com.childai.companion.ui.chat.strangedoor.StrangeDoorHomeEventActionId
import com.childai.companion.ui.chat.strangedoor.StrangeDoorShapeHint
import com.childai.companion.ui.chat.strangedoor.toHomeEventUiModel
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatViewModelStrangeDoorShowcaseTest {
    @Test
    fun cannotSaveBlockedTransformToShowcase() {
        val showcaseRepository = CapturingStrangeDoorShowcaseRepository()
        val viewModel = viewModel(
            attachmentRepository = ImmediateShowcaseAttachmentRepository(
                response = attachmentResponse(
                    recognizedType = "privacy_sensitive",
                    recognizedText = "图片里有学校地址",
                ),
            ),
            showcaseRepository = showcaseRepository,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()
        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)
        viewModel.requestStrangeDoorShowcaseSaveIntent()

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        val saveAction = snapshot.toHomeEventUiModel()
            .actions
            .first { it.id == StrangeDoorHomeEventActionId.SaveToShowcase }
        assertEquals(StrangeDoorShapeHint.Blocked, snapshot.lastPhotoTransform?.shapeHint)
        assertFalse(saveAction.enabled)
        assertNull(viewModel.uiState.value.xiaozhantaiSaveDraft)
        assertNull(showcaseRepository.savedRequest)
    }

    @Test
    fun saveIntentOpensConfirmThenNamingState() {
        val viewModel = saveablePhotoViewModel()

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()
        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)
        viewModel.requestStrangeDoorShowcaseSaveIntent()

        val confirmDraft = requireNotNull(viewModel.uiState.value.xiaozhantaiSaveDraft)
        assertEquals(XiaozhantaiSaveDraftStage.Confirm, confirmDraft.stage)
        assertEquals(XiaozhantaiSaveDraftSource.StrangeDoor, confirmDraft.source)
        assertEquals("蓝盖盖转轮", confirmDraft.defaultName)

        viewModel.confirmXiaozhantaiSave()

        val namingDraft = requireNotNull(viewModel.uiState.value.xiaozhantaiSaveDraft)
        assertEquals(XiaozhantaiSaveDraftStage.Naming, namingDraft.stage)
        assertEquals(XiaozhantaiSaveDraftSource.StrangeDoor, namingDraft.source)
        assertEquals("蓝盖盖转轮", namingDraft.name)
    }

    @Test
    fun namingThenConfirmUsesExistingShowcaseSaveUseCase() {
        val showcaseRepository = CapturingStrangeDoorShowcaseRepository()
        val growthRepository = CapturingStrangeDoorGrowthRepository()
        val viewModel = saveablePhotoViewModel(
            showcaseRepository = showcaseRepository,
            growthEventRepository = growthRepository,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()
        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)
        viewModel.requestStrangeDoorShowcaseSaveIntent()
        viewModel.confirmXiaozhantaiSave()
        viewModel.updateXiaozhantaiSaveName("蓝盖盖转轮")
        viewModel.confirmXiaozhantaiSave()

        val request = requireNotNull(showcaseRepository.savedRequest)
        assertEquals("蓝盖盖转轮", request.name)
        assertArrayEquals(byteArrayOf(1, 2, 3), request.photoBytes)
        assertTrue(request.foxQuote.contains("蓝盖盖转轮"))
        assertTrue(request.foxQuote.contains("小白狐把它轻轻一转"))
        assertTrue(request.foxQuote.contains("门上的圆锁咔哒一下松开了"))
        assertEquals("showcase_item_saved", growthRepository.appendedEvent?.type)
        assertEquals("xiaozhantai", growthRepository.appendedEvent?.source)
        assertNull(viewModel.uiState.value.xiaozhantaiSavedItemIdForNavigation)
    }

    @Test
    fun textNameInNamingStateSavesWithoutConversation() {
        val showcaseRepository = CapturingStrangeDoorShowcaseRepository()
        val sender = CapturingStrangeDoorShowcaseConversationSender()
        val viewModel = saveablePhotoViewModel(
            showcaseRepository = showcaseRepository,
            conversationSender = sender,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()
        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)
        viewModel.requestStrangeDoorShowcaseSaveIntent()
        viewModel.confirmXiaozhantaiSave()
        viewModel.sendText("蓝盖盖转轮")

        assertEquals("蓝盖盖转轮", showcaseRepository.savedRequest?.name)
        assertEquals(0, sender.sendCalls)
        assertEquals(0, sender.streamCalls)
    }

    @Test
    fun savedShowcaseFeedbackStaysOnDemoPage() {
        val showcaseRepository = CapturingStrangeDoorShowcaseRepository()
        val viewModel = saveablePhotoViewModel(showcaseRepository = showcaseRepository)

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()
        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)
        viewModel.requestStrangeDoorShowcaseSaveIntent()
        viewModel.confirmXiaozhantaiSave()
        viewModel.updateXiaozhantaiSaveName("蓝盖盖转轮")
        viewModel.confirmXiaozhantaiSave()

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        val model = snapshot.toHomeEventUiModel()
        assertEquals(StrangeDoorDemoState.ShowcaseSaved, snapshot.demoState)
        assertEquals(
            listOf(
                "蓝盖盖转轮，放好啦",
                "以后可以在小展台里看到它",
            ),
            model.bubbleLines,
        )
        assertEquals(
            listOf("再找一个", "动脑试试"),
            model.actions.map { it.label },
        )
        assertNull(viewModel.uiState.value.xiaozhantaiSaveDraft)
    }

    private fun saveablePhotoViewModel(
        showcaseRepository: XiaozhantaiRepository = CapturingStrangeDoorShowcaseRepository(),
        growthEventRepository: GrowthEventRepository? = null,
        conversationSender: ConversationMessageSender = CapturingStrangeDoorShowcaseConversationSender(),
    ): ChatViewModel {
        return viewModel(
            attachmentRepository = ImmediateShowcaseAttachmentRepository(
                response = attachmentResponse(),
            ),
            showcaseRepository = showcaseRepository,
            growthEventRepository = growthEventRepository,
            conversationSender = conversationSender,
        )
    }

    private fun viewModel(
        attachmentRepository: AttachmentRepository,
        showcaseRepository: XiaozhantaiRepository? = null,
        growthEventRepository: GrowthEventRepository? = null,
        conversationSender: ConversationMessageSender = CapturingStrangeDoorShowcaseConversationSender(),
    ): ChatViewModel {
        return ChatViewModel(
            conversationSender = conversationSender,
            attachmentRepository = attachmentRepository,
            xiaozhantaiRepository = showcaseRepository,
            growthEventRepository = growthEventRepository,
            sendDispatcher = Dispatchers.Unconfined,
            requestOpeningOnInit = false,
        )
    }

    private fun photoPayload(): PhotoUploadPayload {
        return PhotoUploadPayload(
            bytes = byteArrayOf(1, 2, 3),
            mimeType = "image/jpeg",
            fileName = "strange-door-showcase.jpg",
            previewBytes = byteArrayOf(4, 5),
        )
    }

    private fun attachmentResponse(
        recognizedType: String = "image_observation",
        recognizedText: String = "图片里有一个蓝色瓶盖",
        confidence: Double = 0.92,
    ): AttachmentCreateResponse {
        return AttachmentCreateResponse(
            attachmentId = "att_strange_door_showcase",
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
                text = "普通图片回复不应该在奇怪小门里渲染",
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

private class ImmediateShowcaseAttachmentRepository(
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

private class CapturingStrangeDoorShowcaseRepository : XiaozhantaiRepository() {
    var savedRequest: XiaozhantaiSaveRequest? = null

    override suspend fun saveCapturedPhoto(request: XiaozhantaiSaveRequest): XiaozhantaiItem {
        savedRequest = request
        return XiaozhantaiItem(
            id = "stand_item_strange_door",
            photoUri = "/tmp/stand_item_strange_door.jpg",
            name = request.name,
            foxQuote = request.foxQuote,
            createdAt = 1_700_000_000L,
            source = request.source,
            isDeleted = false,
        )
    }
}

private class CapturingStrangeDoorGrowthRepository : GrowthEventRepository() {
    var appendedEvent: GrowthEvent? = null

    override suspend fun append(event: GrowthEvent): GrowthEvent {
        appendedEvent = event
        return event
    }
}

private class CapturingStrangeDoorShowcaseConversationSender : ConversationMessageSender {
    var sendCalls = 0
    var streamCalls = 0

    override suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        quickActionId: String?,
        timezone: String,
    ): ConversationMessageResponse {
        sendCalls += 1
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
        streamCalls += 1
    }

    private fun response(): ConversationMessageResponse {
        return ConversationMessageResponse(
            reply = ConversationReply(
                type = "agent_message",
                text = "不应被调用",
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
