package com.childai.companion.data.attachment

open class AttachmentRepository(
    private val apiClient: AttachmentApiClient = AttachmentApiClient(),
) {
    open suspend fun createCapturedImage(
        childId: String,
        sessionId: String,
        imageBytes: ByteArray,
        mimeType: String,
        fileName: String,
        imagePurpose: String = "share",
        childCaption: String = "我拍了一张图片给小白狐看。",
    ): AttachmentCreateResponse {
        return apiClient.uploadImage(
            childId = childId,
            sessionId = sessionId,
            imageBytes = imageBytes,
            mimeType = mimeType,
            fileName = fileName,
            imagePurpose = imagePurpose,
            childCaption = childCaption,
        )
    }

    open suspend fun createMockHomeworkPhoto(
        childId: String,
        sessionId: String,
        mockOcrText: String,
    ): AttachmentCreateResponse {
        return apiClient.createAttachment(
            AttachmentCreateRequest(
                childId = childId,
                sessionId = sessionId,
                imagePurpose = "learning_homework",
                fileId = "android_mock_homework_photo",
                mockOcrText = mockOcrText,
                mockVisionText = mockOcrText,
                childCaption = "这是作业题",
            ),
        )
    }

    open suspend fun createMockImageShare(
        childId: String,
        sessionId: String,
        mockVisionText: String,
        imagePurpose: String,
        childCaption: String,
    ): AttachmentCreateResponse {
        return apiClient.createAttachment(
            AttachmentCreateRequest(
                childId = childId,
                sessionId = sessionId,
                imagePurpose = imagePurpose,
                mockVisionText = mockVisionText,
                childCaption = childCaption,
            ),
        )
    }
}
