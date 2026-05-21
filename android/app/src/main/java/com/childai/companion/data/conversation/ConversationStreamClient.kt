package com.childai.companion.data.conversation

import com.childai.companion.config.DevSettings
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class ConversationStreamClient(
    private val baseUrl: String = DevSettings.conversationApiBaseUrl,
    private val connectTimeoutMs: Int = 8_000,
    private val readTimeoutMs: Int = 45_000,
) {
    suspend fun streamMessage(
        request: ConversationMessageRequest,
        streamOptions: ConversationStreamOptions,
        onEvent: (ConversationStreamEvent) -> Unit,
    ) = withContext(Dispatchers.IO) {
        val connection = openConnection()
        try {
            val requestBody = request
                .toStreamJsonString(streamOptions)
                .toByteArray(Charsets.UTF_8)
            connection.outputStream.use { output ->
                output.write(requestBody)
            }

            val statusCode = connection.responseCode
            if (statusCode !in 200..299) {
                val responseBody = connection.readBody(statusCode)
                throw ConversationApiException(
                    "Conversation stream returned HTTP $statusCode: $responseBody",
                )
            }

            connection.inputStream.bufferedReader(Charsets.UTF_8).useLines { lines ->
                lines
                    .map { it.trim() }
                    .filter { it.isNotEmpty() }
                    .forEach { line ->
                        onEvent(ConversationStreamEvent.fromJsonLine(line))
                    }
            }
        } catch (exception: IOException) {
            throw ConversationApiException("Conversation stream request failed", exception)
        } finally {
            connection.disconnect()
        }
    }

    private fun openConnection(): HttpURLConnection {
        return (URL(streamEndpoint()).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = connectTimeoutMs
            readTimeout = readTimeoutMs
            doOutput = true
            setRequestProperty("Content-Type", "application/json; charset=utf-8")
            setRequestProperty("Accept", "application/x-ndjson")
        }
    }

    private fun streamEndpoint(): String {
        return "${baseUrl.trimEnd('/')}/api/v1/conversation/stream"
    }
}
