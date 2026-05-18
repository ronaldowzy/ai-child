package com.childai.companion.data.conversation

import org.json.JSONArray
import org.json.JSONObject

data class ConversationMessageRequest(
    val childId: String,
    val sessionId: String,
    val input: ConversationInput,
    val clientContext: ClientContext,
) {
    fun toJsonString(): String {
        return JSONObject()
            .put("child_id", childId)
            .put("session_id", sessionId)
            .put(
                "input",
                JSONObject()
                    .put("type", input.type)
                    .put("text", input.text)
                    .put("attachments", JSONArray(input.attachments)),
            )
            .put(
                "client_context",
                JSONObject()
                    .put("device_time", clientContext.deviceTime)
                    .put("timezone", clientContext.timezone)
                    .put("app_mode", clientContext.appMode),
            )
            .toString()
    }
}

data class ConversationInput(
    val text: String,
    val type: String = "text",
    val attachments: List<String> = emptyList(),
)

data class ClientContext(
    val deviceTime: String,
    val timezone: String,
    val appMode: String = "child",
)

data class ConversationMessageResponse(
    val reply: ConversationReply,
    val uiActions: List<ConversationUiAction>,
    val sessionState: ConversationSessionState,
) {
    companion object {
        fun fromJsonString(rawJson: String): ConversationMessageResponse {
            val root = JSONObject(rawJson)
            return ConversationMessageResponse(
                reply = ConversationReply.fromJson(root.getJSONObject("reply")),
                uiActions = root.optJSONArray("ui_actions").toUiActions(),
                sessionState = ConversationSessionState.fromJson(
                    root.getJSONObject("session_state"),
                ),
            )
        }
    }
}

data class ConversationReply(
    val type: String,
    val text: String,
    val voiceEnabled: Boolean,
    val emotion: String,
) {
    companion object {
        fun fromJson(json: JSONObject): ConversationReply {
            return ConversationReply(
                type = json.optString("type", "agent_message"),
                text = json.getString("text"),
                voiceEnabled = json.optBoolean("voice_enabled", true),
                emotion = json.optString("emotion", "warm"),
            )
        }
    }
}

data class ConversationUiAction(
    val type: String,
    val actions: List<ConversationQuickAction>,
)

data class ConversationQuickAction(
    val id: String,
    val label: String,
)

data class ConversationSessionState(
    val baseScene: String,
    val activeScene: String,
    val needsInput: String?,
    val requiresParentAttention: Boolean,
) {
    fun toDisplayText(): String {
        val parts = mutableListOf(
            "base=$baseScene",
            "active=$activeScene",
        )
        if (!needsInput.isNullOrBlank()) {
            parts.add("needs=$needsInput")
        }
        if (requiresParentAttention) {
            parts.add("parent_attention=true")
        }
        return parts.joinToString(separator = " | ")
    }

    companion object {
        fun fromJson(json: JSONObject): ConversationSessionState {
            return ConversationSessionState(
                baseScene = json.getString("base_scene"),
                activeScene = json.getString("active_scene"),
                needsInput = json.optNullableString("needs_input"),
                requiresParentAttention = json.optBoolean(
                    "requires_parent_attention",
                    false,
                ),
            )
        }
    }
}

private fun JSONArray?.toUiActions(): List<ConversationUiAction> {
    if (this == null) return emptyList()

    return buildList {
        for (index in 0 until length()) {
            val item = getJSONObject(index)
            add(
                ConversationUiAction(
                    type = item.optString("type", "show_quick_actions"),
                    actions = item.optJSONArray("actions").toQuickActions(),
                ),
            )
        }
    }
}

private fun JSONArray?.toQuickActions(): List<ConversationQuickAction> {
    if (this == null) return emptyList()

    return buildList {
        for (index in 0 until length()) {
            val item = getJSONObject(index)
            add(
                ConversationQuickAction(
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
