package com.childai.companion.data.asr

import org.json.JSONObject

data class AsrAudioPayload(
    val data: String,
    val format: String = "wav",
    val sampleRateHz: Int = 16_000,
    val channelCount: Int = 1,
    val durationMs: Int,
) {
    fun toJson(): JSONObject {
        return JSONObject()
            .put("data", data)
            .put("format", format)
            .put("sampleRateHz", sampleRateHz)
            .put("channelCount", channelCount)
            .put("durationMs", durationMs)
    }
}

data class AsrClientContext(
    val deviceTime: String,
    val timezone: String,
    val appMode: String = "child",
) {
    fun toJson(): JSONObject {
        return JSONObject()
            .put("deviceTime", deviceTime)
            .put("timezone", timezone)
            .put("appMode", appMode)
    }
}

data class AsrTranscriptionRequest(
    val childId: String,
    val sessionId: String,
    val audio: AsrAudioPayload,
    val language: String = "zh-CN",
    val mode: String = "confirm_before_send",
    val clientContext: AsrClientContext,
) {
    fun toJsonString(): String {
        return JSONObject()
            .put("childId", childId)
            .put("sessionId", sessionId)
            .put("audio", audio.toJson())
            .put("language", language)
            .put("mode", mode)
            .put("clientContext", clientContext.toJson())
            .toString()
    }
}

data class AsrTranscriptionResponse(
    val status: String,
    val transcript: String?,
    val requiresConfirmation: Boolean,
    val provider: String,
    val model: String,
    val language: String,
    val durationMs: Int?,
    val confidence: Double?,
    val errorCode: String?,
    val fallbackAction: String?,
) {
    companion object {
        fun fromJsonString(rawJson: String): AsrTranscriptionResponse {
            val root = JSONObject(rawJson)
            return AsrTranscriptionResponse(
                status = root.getString("status"),
                transcript = root.optNullableString("transcript"),
                requiresConfirmation = root.optBoolean("requiresConfirmation", true),
                provider = root.optString("provider", "mock"),
                model = root.optString("model", ""),
                language = root.optString("language", "zh-CN"),
                durationMs = root.optNullableInt("durationMs"),
                confidence = root.optNullableDouble("confidence"),
                errorCode = root.optNullableString("errorCode"),
                fallbackAction = root.optNullableString("fallbackAction"),
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

private fun JSONObject.optNullableDouble(name: String): Double? {
    if (!has(name) || isNull(name)) return null
    return optDouble(name)
}
