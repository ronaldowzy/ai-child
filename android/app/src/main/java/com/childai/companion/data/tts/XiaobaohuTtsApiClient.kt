package com.childai.companion.data.tts

import com.childai.companion.config.DevSettings
import com.childai.companion.data.conversation.readBody
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

interface XiaobaohuTtsAudioGenerator {
    suspend fun generateAudioUrl(text: String, emotion: String = "encourage"): String?
}

class XiaobaohuTtsRepository(
    private val apiClient: XiaobaohuTtsApiClient = XiaobaohuTtsApiClient(),
) : XiaobaohuTtsAudioGenerator {
    override suspend fun generateAudioUrl(text: String, emotion: String): String? {
        return apiClient.generate(
            XiaobaohuTtsRequest(
                text = text,
                emotion = emotion,
            ),
        ).audioUrl
    }
}

class XiaobaohuTtsApiClient(
    private val baseUrl: String = DevSettings.conversationApiBaseUrl,
    private val connectTimeoutMs: Int = 8_000,
    private val readTimeoutMs: Int = 45_000,
) {
    suspend fun generate(request: XiaobaohuTtsRequest): XiaobaohuTtsResponse =
        withContext(Dispatchers.IO) {
            val connection = openConnection()
            try {
                val requestBody = request.toJsonString().toByteArray(Charsets.UTF_8)
                connection.outputStream.use { output ->
                    output.write(requestBody)
                }
                val statusCode = connection.responseCode
                val responseBody = connection.readBody(statusCode)
                if (statusCode !in 200..299) {
                    throw XiaobaohuTtsApiException("TTS API returned HTTP $statusCode")
                }
                XiaobaohuTtsResponse.fromJsonString(responseBody)
            } catch (exception: IOException) {
                throw XiaobaohuTtsApiException("TTS API request failed", exception)
            } finally {
                connection.disconnect()
            }
        }

    private fun openConnection(): HttpURLConnection {
        return (URL(ttsEndpoint()).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = connectTimeoutMs
            readTimeout = readTimeoutMs
            doOutput = true
            setRequestProperty("Content-Type", "application/json; charset=utf-8")
            setRequestProperty("Accept", "application/json")
        }
    }

    private fun ttsEndpoint(): String {
        return "${baseUrl.trimEnd('/')}/api/v1/tts/xiaobaohu"
    }
}

data class XiaobaohuTtsRequest(
    val text: String,
    val emotion: String = "encourage",
    val voiceVersion: String = "xiaobaohu_v01",
) {
    fun toJsonString(): String {
        return JSONObject()
            .put("text", text)
            .put("emotion", emotion)
            .put("voiceVersion", voiceVersion)
            .toString()
    }
}

data class XiaobaohuTtsResponse(
    val audioUrl: String?,
    val provider: String,
    val model: String,
) {
    companion object {
        fun fromJsonString(rawJson: String): XiaobaohuTtsResponse {
            val root = JSONObject(rawJson)
            return XiaobaohuTtsResponse(
                audioUrl = root.optString("audioUrl").takeIf { it.isNotBlank() },
                provider = root.optString("provider"),
                model = root.optString("model"),
            )
        }
    }
}

class XiaobaohuTtsApiException(
    message: String,
    cause: Throwable? = null,
) : Exception(message, cause)
