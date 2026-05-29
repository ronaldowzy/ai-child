package com.childai.companion.ui.chat

import com.childai.companion.data.attachment.AttachmentCreateResponse
import com.childai.companion.data.attachment.AttachmentRepository
import com.childai.companion.data.attachment.PhotoUploadPayload
import com.childai.companion.data.attachment.RecognizedContent
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
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
        assertEquals("我拍了一张图片给小白狐看。", childMessage.text)
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
        assertTrue(state.messages.any { it.text.contains("这张图片暂时没有处理好") })
        assertEquals(
            LocalImagePreviewStatus.Failed,
            state.imagePreviewCards.getValue(childMessage.id).status,
        )
        assertEquals(
            "这张图还没给小白狐看到",
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

    private fun viewModel(repository: AttachmentRepository): ChatViewModel {
        return ChatViewModel(
            attachmentRepository = repository,
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

    private fun attachmentResponse(): AttachmentCreateResponse {
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
                text = "我看到图里像是一个积木城堡。你想先讲讲它哪里最有意思吗？",
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
