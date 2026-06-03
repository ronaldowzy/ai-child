package com.childai.companion.ui.chat

import com.childai.companion.data.attachment.AttachmentCreateResponse
import com.childai.companion.data.attachment.AttachmentRepository
import com.childai.companion.data.attachment.PhotoUploadPayload
import com.childai.companion.data.attachment.RecognizedContent
import com.childai.companion.data.conversation.CompanionObjectMeta
import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.showcase.XiaozhantaiItem
import com.childai.companion.data.showcase.XiaozhantaiRepository
import com.childai.companion.data.showcase.XiaozhantaiSaveRequest
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.coroutines.Continuation
import kotlin.coroutines.resume
import kotlin.coroutines.suspendCoroutine

class ChatViewModelImageAttachmentTest {
    @Test
    fun submitCapturedPhotoAppendsChildMessageWithPreviewMetadata() {
        val repository = HoldingAttachmentRepository()
        val viewModel = viewModel(repository)
        val payload = photoPayload(
            bytes = byteArrayOf(1, 2, 3, 4),
            previewBytes = byteArrayOf(9, 8, 7),
        )

        viewModel.submitCapturedPhoto(payload)

        val state = viewModel.uiState.value
        val childMessage = state.messages.last()
        val preview = state.imagePreviewCards[childMessage.id]
        assertEquals(MessageAuthor.Child, childMessage.author)
        assertEquals("我给小白狐看了一张图", childMessage.text)
        assertEquals(ChildTurnUiPhase.ImageProcessing, state.interactionPresentation.phase)
        assertNotNull(preview)
        assertEquals(LocalImagePreviewStatus.Uploading, preview!!.status)
        assertEquals("正在给小白狐看看", localImagePreviewStatusText(preview.status))
        assertEquals("JPEG", preview.displayMimeType)
        assertEquals(4, preview.sizeBytes)
        assertArrayEquals(byteArrayOf(9, 8, 7), preview.previewBytes!!)

        repository.resumeSuccess(attachmentResponse())
        assertEquals(
            LocalImagePreviewStatus.Sent,
            viewModel.uiState.value.imagePreviewCards.getValue(childMessage.id).status,
        )
        assertEquals(
            "小白狐正在看",
            localImagePreviewStatusText(
                viewModel.uiState.value.imagePreviewCards.getValue(childMessage.id).status,
            ),
        )
        assertFalse(viewModel.uiState.value.isSending)
    }

    @Test
    fun submitCapturedPhotoFailureKeepsGentleMessageAndFailedPreview() {
        val repository = ThrowingAttachmentRepository()
        val viewModel = viewModel(repository)

        viewModel.submitCapturedPhoto(photoPayload())

        val state = viewModel.uiState.value
        val childMessage = state.messages.first { it.author == MessageAuthor.Child }
        assertTrue(state.messages.any { it.text.contains("这张图刚才没弄好") })
        assertEquals(
            LocalImagePreviewStatus.Failed,
            state.imagePreviewCards.getValue(childMessage.id).status,
        )
        assertEquals(
            "这张图还没看到",
            localImagePreviewStatusText(state.imagePreviewCards.getValue(childMessage.id).status),
        )
        assertEquals(ChildTurnUiPhase.ServiceError, state.interactionPresentation.phase)
        assertFalse(state.isSending)
    }

    @Test
    fun submitCapturedPhotoDoesNotPassRawLocalPathAsUploadFileName() {
        val repository = HoldingAttachmentRepository()
        val viewModel = viewModel(repository)

        viewModel.submitCapturedPhoto(
            photoPayload(fileName = "/private/tmp/child-real-photo.jpg"),
        )

        assertEquals("child-real-photo.jpg", repository.capturedFileName)
        assertFalse(repository.capturedFileName.orEmpty().contains("/private/tmp"))
        assertArrayEquals(byteArrayOf(1, 2, 3), repository.capturedBytes!!)

        repository.resumeSuccess(attachmentResponse())
    }

    @Test
    fun localPreviewCardCanRenderWithoutBitmapBytes() {
        val card = LocalImagePreviewCardUiState.fromPayload(
            messageId = "child-photo-1",
            payload = photoPayload(previewBytes = null),
        )

        assertNull(card.previewBytes)
        assertEquals("JPEG", card.displayMimeType)
        assertEquals("1 KB", card.displaySize)
    }

    @Test
    fun savedShowcaseItemUsesCapturedPhotoAndCurrentFoxQuote() {
        val attachmentRepository = HoldingAttachmentRepository()
        val showcaseRepository = CapturingXiaozhantaiRepository()
        val viewModel = viewModel(
            repository = attachmentRepository,
            showcaseRepository = showcaseRepository,
        )
        val payload = photoPayload(
            bytes = byteArrayOf(11, 12, 13),
            previewBytes = byteArrayOf(3, 2, 1),
        )

        viewModel.submitCapturedPhoto(payload)
        val childMessage = viewModel.uiState.value.messages.last()
        attachmentRepository.resumeSuccess(
            attachmentResponse(
                replyText = "它看起来像一颗安静的小星球。",
            ),
        )

        val sentCard = viewModel.uiState.value.imagePreviewCards.getValue(childMessage.id)
        assertTrue(sentCard.canSaveToXiaozhantai)

        viewModel.requestSavePhotoToXiaozhantai(childMessage.id)
        viewModel.updateXiaozhantaiSaveName("小石头")
        viewModel.confirmXiaozhantaiSave()

        assertEquals("小石头", showcaseRepository.savedRequest!!.name)
        assertArrayEquals(byteArrayOf(11, 12, 13), showcaseRepository.savedRequest!!.photoBytes)
        assertEquals("它看起来像一颗安静的小星球。", showcaseRepository.savedRequest!!.foxQuote)
        assertTrue(
            viewModel.uiState.value.imagePreviewCards
                .getValue(childMessage.id)
                .savedToXiaozhantai,
        )
        assertEquals("stand_item_saved", viewModel.uiState.value.xiaozhantaiSavedItemIdForNavigation)
    }

    @Test
    fun savedShowcaseItemUsesChildNamedCompanionNameWhenAvailable() {
        val attachmentRepository = HoldingAttachmentRepository()
        val showcaseRepository = CapturingXiaozhantaiRepository()
        val viewModel = viewModel(
            repository = attachmentRepository,
            showcaseRepository = showcaseRepository,
        )
        val payload = photoPayload(
            bytes = byteArrayOf(21, 22, 23),
            previewBytes = byteArrayOf(7, 8, 9),
        )

        viewModel.submitCapturedPhoto(payload)
        val childMessage = viewModel.uiState.value.messages.last()
        attachmentRepository.resumeSuccess(
            attachmentResponse(
                replyText = "我看到小黄星啦\n像一盏小小的灯",
            ),
        )
        viewModel.renderAgentReply(
            ConversationMessageResponse(
                reply = ConversationReply(
                    type = "agent_message",
                    text = "小棉花，软软的名字\n它轻轻落到窗边啦",
                    voiceEnabled = false,
                    audioUrl = null,
                    emotion = "warm",
                    agentMotion = "gentle_idle",
                ),
                uiActions = emptyList(),
                sessionState = ConversationSessionState(
                    baseScene = "conversation.open",
                    activeScene = "conversation.open",
                    needsInput = null,
                    requiresParentAttention = false,
                    companionObject = CompanionObjectMeta(
                        id = "co_saved_name",
                        name = "小棉花",
                        objectType = "star",
                        lightLocation = "窗边",
                        state = "active",
                        action = "co_create",
                        visualKind = "star",
                    ),
                ),
            ),
        )

        viewModel.requestSavePhotoToXiaozhantai(childMessage.id)
        assertEquals("小棉花", viewModel.uiState.value.xiaozhantaiSaveDraft!!.name)

        viewModel.confirmXiaozhantaiSave()

        assertEquals("小棉花", showcaseRepository.savedRequest!!.name)
        assertArrayEquals(byteArrayOf(21, 22, 23), showcaseRepository.savedRequest!!.photoBytes)
        assertEquals("我看到小黄星啦", showcaseRepository.savedRequest!!.foxQuote)
    }

    @Test
    fun confirmShowcaseSaveIgnoresDuplicateClicksWhileSaving() {
        val attachmentRepository = HoldingAttachmentRepository()
        val showcaseRepository = HoldingXiaozhantaiRepository()
        val viewModel = viewModel(
            repository = attachmentRepository,
            showcaseRepository = showcaseRepository,
        )

        viewModel.submitCapturedPhoto(photoPayload())
        val childMessage = viewModel.uiState.value.messages.last()
        attachmentRepository.resumeSuccess(attachmentResponse())
        viewModel.requestSavePhotoToXiaozhantai(childMessage.id)

        viewModel.confirmXiaozhantaiSave()
        viewModel.confirmXiaozhantaiSave()

        assertEquals(1, showcaseRepository.saveCalls)
        assertTrue(viewModel.uiState.value.xiaozhantaiSaveDraft!!.isSaving)
        assertTrue(
            viewModel.uiState.value.imagePreviewCards
                .getValue(childMessage.id)
                .isSavingToXiaozhantai,
        )

        showcaseRepository.resumeSuccess()

        assertTrue(
            viewModel.uiState.value.imagePreviewCards
                .getValue(childMessage.id)
                .savedToXiaozhantai,
        )
    }

    @Test
    fun failedShowcaseSaveRestoresRetryableStateWithGentleMessage() {
        val attachmentRepository = HoldingAttachmentRepository()
        val showcaseRepository = ThrowingXiaozhantaiRepository()
        val viewModel = viewModel(
            repository = attachmentRepository,
            showcaseRepository = showcaseRepository,
        )

        viewModel.submitCapturedPhoto(photoPayload())
        val childMessage = viewModel.uiState.value.messages.last()
        attachmentRepository.resumeSuccess(attachmentResponse())
        viewModel.requestSavePhotoToXiaozhantai(childMessage.id)
        viewModel.confirmXiaozhantaiSave()

        val draft = viewModel.uiState.value.xiaozhantaiSaveDraft
        val card = viewModel.uiState.value.imagePreviewCards.getValue(childMessage.id)
        assertNotNull(draft)
        assertFalse(draft!!.isSaving)
        assertEquals("刚才没有放好，我们可以等一下再试。", draft.errorMessage)
        assertFalse(card.isSavingToXiaozhantai)
        assertFalse(card.savedToXiaozhantai)
        assertEquals("刚才没有放好，我们可以等一下再试。", card.xiaozhantaiError)
    }

    private fun viewModel(
        repository: AttachmentRepository,
        showcaseRepository: XiaozhantaiRepository? = null,
    ): ChatViewModel {
        return ChatViewModel(
            attachmentRepository = repository,
            xiaozhantaiRepository = showcaseRepository,
            sendDispatcher = Dispatchers.Unconfined,
            requestOpeningOnInit = false,
        )
    }

    private fun photoPayload(
        bytes: ByteArray = byteArrayOf(1, 2, 3),
        previewBytes: ByteArray? = byteArrayOf(4, 5),
        fileName: String = "child-photo.jpg",
    ): PhotoUploadPayload {
        return PhotoUploadPayload(
            bytes = bytes,
            mimeType = "image/jpeg",
            fileName = fileName,
            previewBytes = previewBytes,
        )
    }

    private fun attachmentResponse(
        replyText: String = "我看到图里像是一个积木城堡。你想先讲讲它哪里最有意思吗？",
    ): AttachmentCreateResponse {
        return AttachmentCreateResponse(
            attachmentId = "att_image_test",
            recognizedContent = RecognizedContent(
                type = "image_observation",
                text = "图片里有一个积木城堡",
                confidence = 0.92,
                providerName = "mock_ocr",
                fallbackAction = null,
                imagePurpose = IMAGE_PURPOSE_SHARE,
                childCaption = "我拍了一张图片给小白狐看。",
            ),
            reply = ConversationReply(
                type = "agent_message",
                text = replyText,
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

private class HoldingAttachmentRepository : AttachmentRepository() {
    private var continuation: Continuation<AttachmentCreateResponse>? = null
    var capturedBytes: ByteArray? = null
    var capturedFileName: String? = null

    override suspend fun createCapturedImage(
        childId: String,
        sessionId: String,
        imageBytes: ByteArray,
        mimeType: String,
        fileName: String,
        imagePurpose: String,
        childCaption: String,
    ): AttachmentCreateResponse {
        capturedBytes = imageBytes
        capturedFileName = fileName
        return suspendCoroutine { nextContinuation ->
            continuation = nextContinuation
        }
    }

    fun resumeSuccess(response: AttachmentCreateResponse) {
        continuation?.resume(response)
        continuation = null
    }
}

private class ThrowingAttachmentRepository : AttachmentRepository() {
    override suspend fun createCapturedImage(
        childId: String,
        sessionId: String,
        imageBytes: ByteArray,
        mimeType: String,
        fileName: String,
        imagePurpose: String,
        childCaption: String,
    ): AttachmentCreateResponse {
        throw RuntimeException("network down")
    }
}

private class CapturingXiaozhantaiRepository : XiaozhantaiRepository() {
    var savedRequest: XiaozhantaiSaveRequest? = null

    override suspend fun saveCapturedPhoto(request: XiaozhantaiSaveRequest): XiaozhantaiItem {
        savedRequest = request
        return XiaozhantaiItem(
            id = "stand_item_saved",
            photoUri = "/tmp/stand_item_saved.jpg",
            name = request.name,
            foxQuote = request.foxQuote,
            createdAt = 1760000000000L,
            source = request.source,
            isDeleted = false,
        )
    }
}

private class HoldingXiaozhantaiRepository : XiaozhantaiRepository() {
    private var continuation: Continuation<XiaozhantaiItem>? = null
    var saveCalls = 0
    private var lastRequest: XiaozhantaiSaveRequest? = null

    override suspend fun saveCapturedPhoto(request: XiaozhantaiSaveRequest): XiaozhantaiItem {
        saveCalls += 1
        lastRequest = request
        return suspendCoroutine { nextContinuation ->
            continuation = nextContinuation
        }
    }

    fun resumeSuccess() {
        val request = lastRequest ?: return
        continuation?.resume(
            XiaozhantaiItem(
                id = "stand_item_saved",
                photoUri = "/tmp/stand_item_saved.jpg",
                name = request.name,
                foxQuote = request.foxQuote,
                createdAt = 1760000000000L,
                source = request.source,
                isDeleted = false,
            ),
        )
        continuation = null
    }
}

private class ThrowingXiaozhantaiRepository : XiaozhantaiRepository() {
    override suspend fun saveCapturedPhoto(request: XiaozhantaiSaveRequest): XiaozhantaiItem {
        throw RuntimeException("save failed")
    }
}
