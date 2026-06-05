package com.childai.companion.ui.chat

import com.childai.companion.data.attachment.AttachmentCreateResponse
import com.childai.companion.data.attachment.AttachmentRepository
import com.childai.companion.data.attachment.PhotoUploadPayload
import com.childai.companion.data.attachment.RecognizedContent
import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoState
import com.childai.companion.ui.chat.strangedoor.StrangeDoorShapeHint
import com.childai.companion.ui.chat.strangedoor.StrangeDoorState
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ChatViewModelStrangeDoorPhotoTransformTest {
    @Test
    fun strangeDoorPhotoUsesExistingShareAttachmentEntry() {
        val attachmentRepository = ImmediateStrangeDoorAttachmentRepository(
            response = attachmentResponse(
                recognizedText = "图片里有一个蓝色瓶盖",
            ),
        )
        val sender = CapturingStrangeDoorConversationSender()
        val viewModel = viewModel(
            attachmentRepository = attachmentRepository,
            conversationSender = sender,
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()
        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = strangeDoorPhotoCaptureImagePurpose())

        assertEquals(IMAGE_PURPOSE_SHARE, attachmentRepository.capturedImagePurpose)
        assertEquals(0, sender.sendCalls)
        assertEquals(0, sender.streamCalls)
    }

    @Test
    fun roundRecognizedContentGoesThroughMapperAndOpensDoor() {
        val viewModel = viewModel(
            attachmentRepository = ImmediateStrangeDoorAttachmentRepository(
                response = attachmentResponse(
                    recognizedType = "image_observation",
                    recognizedText = "图片里有一个蓝色瓶盖",
                    confidence = 0.92,
                ),
            ),
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()
        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        val transform = requireNotNull(snapshot.lastPhotoTransform)
        assertEquals(StrangeDoorDemoState.Completed, snapshot.demoState)
        assertEquals(StrangeDoorState.Open, snapshot.doorState)
        assertEquals(StrangeDoorShapeHint.Round, transform.shapeHint)
        assertEquals("蓝色瓶盖", transform.objectName)
        assertEquals("蓝盖盖转轮", transform.transformedName)
        assertTrue(transform.canSaveToShowcase)
        assertFalse(viewModel.uiState.value.isSending)
    }

    @Test
    fun partialAndUnknownObjectsAdvanceOneStepOnly() {
        val partialViewModel = viewModel(
            attachmentRepository = ImmediateStrangeDoorAttachmentRepository(
                response = attachmentResponse(recognizedText = "图片里有一支铅笔"),
            ),
        )
        partialViewModel.activateStrangeDoorDemo()
        partialViewModel.chooseStrangeDoorPhotoMethod()
        partialViewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)

        val partialSnapshot = requireNotNull(partialViewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorState.Cracked, partialSnapshot.doorState)
        assertEquals(StrangeDoorDemoState.PhotoResult, partialSnapshot.demoState)
        assertEquals(StrangeDoorShapeHint.Partial, partialSnapshot.lastPhotoTransform?.shapeHint)

        val unknownViewModel = viewModel(
            attachmentRepository = ImmediateStrangeDoorAttachmentRepository(
                response = attachmentResponse(recognizedText = "图片里有一个奇怪盒子"),
            ),
        )
        unknownViewModel.activateStrangeDoorDemo()
        unknownViewModel.chooseStrangeDoorPhotoMethod()
        unknownViewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)

        val unknownSnapshot = requireNotNull(unknownViewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorState.Cracked, unknownSnapshot.doorState)
        assertEquals(StrangeDoorDemoState.PhotoResult, unknownSnapshot.demoState)
        assertEquals(StrangeDoorShapeHint.Unknown, unknownSnapshot.lastPhotoTransform?.shapeHint)
    }

    @Test
    fun blockedContentDoesNotAdvanceDoorOrAllowShowcaseSave() {
        val viewModel = viewModel(
            attachmentRepository = ImmediateStrangeDoorAttachmentRepository(
                response = attachmentResponse(
                    recognizedType = "privacy_sensitive",
                    recognizedText = "图片里有学校地址",
                    confidence = 0.92,
                ),
            ),
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()
        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)
        viewModel.requestStrangeDoorShowcaseSaveIntent()

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        val transform = requireNotNull(snapshot.lastPhotoTransform)
        assertEquals(StrangeDoorState.Closed, snapshot.doorState)
        assertEquals(StrangeDoorDemoState.PhotoResult, snapshot.demoState)
        assertEquals(StrangeDoorShapeHint.Blocked, transform.shapeHint)
        assertFalse(transform.isUsable)
        assertFalse(transform.canSaveToShowcase)
        assertFalse(snapshot.showcaseSaveIntentRequested)
        assertNull(viewModel.uiState.value.xiaozhantaiSaveDraft)
    }

    @Test
    fun saveToShowcaseButtonOnlyRecordsLocalIntentInD3() {
        val viewModel = viewModel(
            attachmentRepository = ImmediateStrangeDoorAttachmentRepository(
                response = attachmentResponse(
                    recognizedText = "图片里有一个蓝色瓶盖",
                ),
            ),
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()
        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)
        viewModel.requestStrangeDoorShowcaseSaveIntent()

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertTrue(snapshot.showcaseSaveIntentRequested)
        assertNull(viewModel.uiState.value.xiaozhantaiSaveDraft)
        assertNull(viewModel.uiState.value.xiaozhantaiSavedItemIdForNavigation)
    }

    @Test
    fun failedImageUploadDoesNotPretendRecognitionSucceeded() {
        val viewModel = viewModel(
            attachmentRepository = ThrowingStrangeDoorAttachmentRepository(),
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()
        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorDemoState.PhotoPrompt, snapshot.demoState)
        assertEquals(StrangeDoorState.Closed, snapshot.doorState)
        assertNull(snapshot.lastPhotoTransform)
        assertTrue(viewModel.uiState.value.messages.none { it.text.startsWith("我看见了：") })
        assertTrue(
            viewModel.uiState.value.imagePreviewCards.values.any {
                it.status == LocalImagePreviewStatus.Failed
            },
        )
    }

    @Test
    fun textBlockedLearningContentIsNotConvertedIntoDoorTool() {
        val viewModel = viewModel(
            attachmentRepository = ImmediateStrangeDoorAttachmentRepository(
                response = attachmentResponse(
                    recognizedType = "image_observation",
                    recognizedText = "图片里有一道作业题目",
                    confidence = 0.92,
                ),
            ),
        )

        viewModel.activateStrangeDoorDemo()
        viewModel.chooseStrangeDoorPhotoMethod()
        viewModel.submitCapturedPhoto(photoPayload(), imagePurpose = IMAGE_PURPOSE_SHARE)

        val snapshot = requireNotNull(viewModel.uiState.value.strangeDoorDemo)
        assertEquals(StrangeDoorState.Closed, snapshot.doorState)
        assertEquals(StrangeDoorShapeHint.Blocked, snapshot.lastPhotoTransform?.shapeHint)
    }

    private fun viewModel(
        attachmentRepository: AttachmentRepository,
        conversationSender: ConversationMessageSender = CapturingStrangeDoorConversationSender(),
    ): ChatViewModel {
        return ChatViewModel(
            conversationSender = conversationSender,
            attachmentRepository = attachmentRepository,
            sendDispatcher = Dispatchers.Unconfined,
            requestOpeningOnInit = false,
        )
    }

    private fun photoPayload(): PhotoUploadPayload {
        return PhotoUploadPayload(
            bytes = byteArrayOf(1, 2, 3),
            mimeType = "image/jpeg",
            fileName = "strange-door-test.jpg",
            previewBytes = byteArrayOf(4, 5),
        )
    }

    private fun attachmentResponse(
        recognizedType: String = "image_observation",
        recognizedText: String = "图片里有一个蓝色瓶盖",
        confidence: Double = 0.92,
    ): AttachmentCreateResponse {
        return AttachmentCreateResponse(
            attachmentId = "att_strange_door",
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

private class ImmediateStrangeDoorAttachmentRepository(
    private val response: AttachmentCreateResponse,
) : AttachmentRepository() {
    var capturedImagePurpose: String? = null

    override suspend fun createCapturedImage(
        childId: String,
        sessionId: String,
        imageBytes: ByteArray,
        mimeType: String,
        fileName: String,
        imagePurpose: String,
        childCaption: String,
    ): AttachmentCreateResponse {
        capturedImagePurpose = imagePurpose
        return response
    }
}

private class ThrowingStrangeDoorAttachmentRepository : AttachmentRepository() {
    override suspend fun createCapturedImage(
        childId: String,
        sessionId: String,
        imageBytes: ByteArray,
        mimeType: String,
        fileName: String,
        imagePurpose: String,
        childCaption: String,
    ): AttachmentCreateResponse {
        throw RuntimeException("upload failed")
    }
}

private class CapturingStrangeDoorConversationSender : ConversationMessageSender {
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
}
