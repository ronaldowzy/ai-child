package com.childai.companion.data.conversation

import com.childai.companion.config.DevSettings
import com.childai.companion.data.auth.setBearerToken
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class ConversationApiClient(
    private val baseUrl: String = DevSettings.conversationApiBaseUrl,
    private val connectTimeoutMs: Int = 8_000,
    private val readTimeoutMs: Int = 45_000,
    private val authTokenProvider: () -> String? = { null },
) {
    suspend fun sendMessage(
        request: ConversationMessageRequest,
    ): ConversationMessageResponse = withContext(Dispatchers.IO) {
        val connection = openConnection(messageEndpoint())
        try {
            val requestBody = request.toJsonString().toByteArray(Charsets.UTF_8)
            connection.outputStream.use { output ->
                output.write(requestBody)
            }

            val statusCode = connection.responseCode
            val responseBody = connection.readBody(statusCode)
            if (statusCode !in 200..299) {
                throw ConversationApiException(
                    "Conversation API returned HTTP $statusCode: $responseBody",
                )
            }
            ConversationMessageResponse.fromJsonString(responseBody)
        } catch (exception: IOException) {
            throw ConversationApiException("Conversation API request failed", exception)
        } finally {
            connection.disconnect()
        }
    }

    suspend fun requestOpening(
        request: ConversationOpeningRequest,
    ): ConversationMessageResponse = withContext(Dispatchers.IO) {
        val connection = openConnection(openingEndpoint())
        try {
            val requestBody = request.toJsonString().toByteArray(Charsets.UTF_8)
            connection.outputStream.use { output ->
                output.write(requestBody)
            }

            val statusCode = connection.responseCode
            val responseBody = connection.readBody(statusCode)
            if (statusCode !in 200..299) {
                throw ConversationApiException(
                    "Conversation opening API returned HTTP $statusCode: $responseBody",
                )
            }
            ConversationMessageResponse.fromJsonString(responseBody)
        } catch (exception: IOException) {
            throw ConversationApiException("Conversation opening request failed", exception)
        } finally {
            connection.disconnect()
        }
    }

    private fun openConnection(endpoint: String): HttpURLConnection {
        return (URL(endpoint).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = connectTimeoutMs
            readTimeout = readTimeoutMs
            doOutput = true
            setRequestProperty("Content-Type", "application/json; charset=utf-8")
            setRequestProperty("Accept", "application/json")
            setBearerToken(authTokenProvider())
        }
    }

    private fun messageEndpoint(): String {
        return "${baseUrl.trimEnd('/')}/api/v1/conversation/message"
    }

    private fun openingEndpoint(): String {
        return "${baseUrl.trimEnd('/')}/api/v1/conversation/opening"
    }
}

class ConversationApiException(
    message: String,
    cause: Throwable? = null,
) : Exception(message, cause)

internal fun HttpURLConnection.readBody(statusCode: Int): String {
    val stream = if (statusCode in 200..299) inputStream else errorStream
    return stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
}
