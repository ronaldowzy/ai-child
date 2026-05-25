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
}
