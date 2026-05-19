package com.childai.companion.data.attachment

import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationUiAction
import org.json.JSONArray
import org.json.JSONObject

data class AttachmentCreateRequest(
    val childId: String,
    val sessionId: String,
    val attachmentType: String = "homework_photo",
    val fileId: String? = "android_mock_homework_photo",
    val mockOcrText: String,
    val mockConfidence: Double = 0.94,
) {
    fun toJsonString(): String {
        return JSONObject()
            .put("child_id", childId)
            .put("session_id", sessionId)
            .put("attachment_type", attachmentType)
            .put("file_id", fileId)
            .put("mock_ocr_text", mockOcrText)
            .put("mock_confidence", mockConfidence)
            .put(
                "metadata",
                JSONObject()
                    .put("source", "android_mock_photo_flow")
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
) {
    val hasReadyHomeworkText: Boolean
        get() = !recognizedContent.text.isNullOrBlank() &&
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
) {
    companion object {
        fun fromJson(json: JSONObject): RecognizedContent {
            return RecognizedContent(
                type = json.optString("type", "homework_problem"),
                text = json.optNullableString("text"),
                confidence = json.getDouble("confidence"),
                providerName = json.optString("provider_name"),
                fallbackAction = json.optNullableString("fallback_action"),
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
