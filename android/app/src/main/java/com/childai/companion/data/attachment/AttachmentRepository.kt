package com.childai.companion.data.attachment

class AttachmentRepository(
    private val apiClient: AttachmentApiClient = AttachmentApiClient(),
) {
    suspend fun createMockHomeworkPhoto(
        childId: String,
        sessionId: String,
        mockOcrText: String,
    ): AttachmentCreateResponse {
        return apiClient.createAttachment(
            AttachmentCreateRequest(
                childId = childId,
                sessionId = sessionId,
                mockOcrText = mockOcrText,
            ),
        )
    }
}
