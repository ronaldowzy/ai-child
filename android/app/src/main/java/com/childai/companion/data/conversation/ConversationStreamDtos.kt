package com.childai.companion.data.conversation

import org.json.JSONObject

data class ConversationStreamOptions(
    val protocolVersion: String = "stream.v0.1",
    val textGranularity: String = "sentence",
    val includeTts: Boolean = true,
    val audioDelivery: String = "url",
    val clientTurnId: String? = null,
) {
    fun toJson(): JSONObject {
        return JSONObject()
            .put("protocol_version", protocolVersion)
            .put("text_granularity", textGranularity)
            .put("include_tts", includeTts)
            .put("audio_delivery", audioDelivery)
            .put("client_turn_id", clientTurnId)
    }
}

data class ConversationStreamEvent(
    val type: String,
    val payload: JSONObject,
    val seq: Int? = null,
    val requestId: String? = null,
) {
    val delta: String
        get() = payload.optString("delta", "")

    val finalText: String?
        get() = payload.optNullableString("text")

    val audioUrl: String?
        get() = payload.optNullableString("audioUrl")
            ?: payload.optNullableString("audio_url")

    val audioText: String
        get() = payload.optString("text", "")

    val activeScene: String?
        get() = payload.optNullableString("activeScene")
            ?: payload.optNullableString("active_scene")

    val riskLevel: String?
        get() = payload.optNullableString("riskLevel")
            ?: payload.optNullableString("risk_level")

    val requiresParentAttention: Boolean
        get() = payload.optBoolean("requiresParentAttention")
            || payload.optBoolean("requires_parent_attention")

    val emotion: String
        get() = payload.optString("emotion", "thinking")

    val agentMotion: String
        get() = payload.optString("agentMotion", payload.optString("agent_motion", "thinking_blink"))

    val safeMessage: String?
        get() = payload.optNullableString("safe_message")
            ?: payload.optNullableString("message")

    companion object {
        fun fromJsonLine(line: String): ConversationStreamEvent {
            val root = JSONObject(line)
            return ConversationStreamEvent(
                type = root.getString("type"),
                payload = root.optJSONObject("payload") ?: JSONObject(),
                seq = if (root.has("seq") && !root.isNull("seq")) {
                    root.optInt("seq")
                } else {
                    null
                },
                requestId = root.optNullableString("request_id"),
            )
        }

        fun parseNdjson(rawNdjson: String): List<ConversationStreamEvent> {
            return rawNdjson
                .lineSequence()
                .map { it.trim() }
                .filter { it.isNotEmpty() }
                .map(::fromJsonLine)
                .toList()
        }
    }
}

fun ConversationMessageRequest.toStreamJsonString(
    streamOptions: ConversationStreamOptions,
): String {
    return JSONObject(toJsonString())
        .put("stream_options", streamOptions.toJson())
        .toString()
}

private fun JSONObject.optNullableString(name: String): String? {
    if (!has(name) || isNull(name)) return null
    return optString(name).takeIf { it.isNotBlank() }
}
