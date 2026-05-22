package com.childai.companion.data.attachment

class AttachmentRepository(
    private val apiClient: AttachmentApiClient = AttachmentApiClient(),
) {
    suspend fun createCapturedImage(
        childId: String,
        sessionId: String,
        imageDataUri: String,
        imagePurpose: String = "share",
        childCaption: String = "我拍了一张图片给小白狐看。",
    ): AttachmentCreateResponse {
        return apiClient.createAttachment(
            AttachmentCreateRequest(
                childId = childId,
                sessionId = sessionId,
                imagePurpose = imagePurpose,
                imageDataUri = imageDataUri,
                childCaption = childCaption,
            ),
        )
    }

    suspend fun createMockHomeworkPhoto(
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

    suspend fun createMockImageShare(
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
