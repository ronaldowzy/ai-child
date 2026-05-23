package com.childai.companion.data.attachment

import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationUiAction
import org.json.JSONArray
import org.json.JSONObject

data class AttachmentCreateRequest(
    val childId: String,
    val sessionId: String,
    val attachmentType: String = "image",
    val imagePurpose: String = "share",
    val fileId: String? = null,
    val imageDataUri: String? = null,
    val mockOcrText: String? = null,
    val mockVisionText: String? = null,
    val childCaption: String? = null,
    val mockConfidence: Double = 0.94,
) {
    fun toJsonString(): String {
        return JSONObject()
            .put("child_id", childId)
            .put("session_id", sessionId)
            .put("attachment_type", attachmentType)
            .put("image_purpose", imagePurpose)
            .put("file_id", fileId)
            .put("image_data_uri", imageDataUri)
            .put("mock_ocr_text", mockOcrText)
            .put("mock_vision_text", mockVisionText)
            .put("child_caption", childCaption)
            .put("mock_confidence", mockConfidence)
            .put(
                "metadata",
                JSONObject()
                    .put(
                        "source",
                        if (imageDataUri == null) {
                            "android_text_photo_flow"
                        } else {
                            "android_camera_capture"
                        },
                    )
                    .put("stores_original_image", false),
            )
            .toString()
    }
}

data class AttachmentCreateResponse(
    val attachmentId: String,
    val recognizedContent: RecognizedContent,
    val reply: ConversationReply,
    val uiActions: List<ConversationUiAction>,
    val sessionState: ConversationSessionState,
    val mimeType: String? = null,
    val sizeBytes: Int? = null,
) {
    val hasReadyHomeworkText: Boolean
        get() = !recognizedContent.text.isNullOrBlank() &&
            recognizedContent.type == "homework_problem" &&
            recognizedContent.imagePurpose == "learning_homework" &&
            recognizedContent.confidence >= HOMEWORK_READY_CONFIDENCE

    companion object {
        private const val HOMEWORK_READY_CONFIDENCE = 0.75

        fun fromJsonString(rawJson: String): AttachmentCreateResponse {
            val root = JSONObject(rawJson)
            return AttachmentCreateResponse(
                attachmentId = root.getString("attachment_id"),
                recognizedContent = RecognizedContent.fromJson(
                    root.getJSONObject("recognized_content"),
                ),
                reply = ConversationReply.fromJson(root.getJSONObject("reply")),
                uiActions = root.optJSONArray("ui_actions").toAttachmentUiActions(),
                sessionState = ConversationSessionState.fromJson(
                    root.getJSONObject("session_state"),
                ),
                mimeType = root.optNullableString("mime_type"),
                sizeBytes = root.optNullableInt("size_bytes"),
            )
        }
    }
}

data class RecognizedContent(
    val type: String,
    val text: String?,
    val confidence: Double,
    val providerName: String,
    val fallbackAction: String?,
    val imagePurpose: String?,
    val childCaption: String?,
) {
    companion object {
        fun fromJson(json: JSONObject): RecognizedContent {
            return RecognizedContent(
                type = json.optString("type", "homework_problem"),
                text = json.optNullableString("text"),
                confidence = json.getDouble("confidence"),
                providerName = json.optString("provider_name"),
                fallbackAction = json.optNullableString("fallback_action"),
                imagePurpose = json.optNullableString("image_purpose"),
                childCaption = json.optNullableString("child_caption"),
            )
        }
    }
}

private fun JSONArray?.toAttachmentUiActions(): List<ConversationUiAction> {
    if (this == null) return emptyList()

    return buildList {
        for (index in 0 until length()) {
            val item = getJSONObject(index)
            add(
                ConversationUiAction(
                    type = item.optString("type", "show_quick_actions"),
                    actions = item.optJSONArray("actions").toAttachmentQuickActions(),
                ),
            )
        }
    }
}

private fun JSONArray?.toAttachmentQuickActions(): List<com.childai.companion.data.conversation.ConversationQuickAction> {
    if (this == null) return emptyList()

    return buildList {
        for (index in 0 until length()) {
            val item = getJSONObject(index)
            add(
                com.childai.companion.data.conversation.ConversationQuickAction(
                    id = item.getString("id"),
                    label = item.getString("label"),
                ),
            )
        }
    }
}

private fun JSONObject.optNullableString(name: String): String? {
    if (!has(name) || isNull(name)) return null
    return optString(name).takeIf { it.isNotBlank() }
}

private fun JSONObject.optNullableInt(name: String): Int? {
    if (!has(name) || isNull(name)) return null
    return optInt(name)
}
