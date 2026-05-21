package com.childai.companion.data.asr

import com.childai.companion.config.DevSettings
import com.childai.companion.data.conversation.readBody
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

class AsrApiClient(
    private val baseUrl: String = DevSettings.conversationApiBaseUrl,
    private val connectTimeoutMs: Int = 8_000,
    private val readTimeoutMs: Int = 45_000,
) {
    suspend fun transcribe(
        request: AsrTranscriptionRequest,
    ): AsrTranscriptionResponse = withContext(Dispatchers.IO) {
        val connection = openConnection()
        try {
            val requestBody = request.toJsonString().toByteArray(Charsets.UTF_8)
            connection.outputStream.use { output ->
                output.write(requestBody)
            }

            val statusCode = connection.responseCode
            val responseBody = connection.readBody(statusCode)
            if (statusCode !in 200..299) {
                throw AsrApiException(
                    message = "ASR API returned HTTP $statusCode",
                    statusCode = statusCode,
                    detail = responseBody.extractHttpDetail(),
                )
            }
            AsrTranscriptionResponse.fromJsonString(responseBody)
        } catch (exception: IOException) {
            throw AsrApiException("ASR API request failed", cause = exception)
        } finally {
            connection.disconnect()
        }
    }

    private fun openConnection(): HttpURLConnection {
        return (URL(transcribeEndpoint()).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = connectTimeoutMs
            readTimeout = readTimeoutMs
            doOutput = true
            setRequestProperty("Content-Type", "application/json; charset=utf-8")
            setRequestProperty("Accept", "application/json")
        }
    }

    private fun transcribeEndpoint(): String {
        return "${baseUrl.trimEnd('/')}/api/v1/asr/transcribe"
    }
}

class AsrApiException(
    message: String,
    val statusCode: Int? = null,
    val detail: String? = null,
    cause: Throwable? = null,
) : Exception(message, cause)

private fun String.extractHttpDetail(): String? {
    if (isBlank()) return null
    return runCatching {
        JSONObject(this).optString("detail").takeIf { it.isNotBlank() }
    }.getOrNull()
}
