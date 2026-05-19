package com.childai.companion.data.parent

import com.childai.companion.config.DevSettings
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class ParentPolicyApiClient(
    private val baseUrl: String = DevSettings.conversationApiBaseUrl,
    private val connectTimeoutMs: Int = 8_000,
    private val readTimeoutMs: Int = 12_000,
) {
    suspend fun getPolicy(childId: String): ParentPolicyResponse =
        withContext(Dispatchers.IO) {
            val connection = openConnection(policyEndpoint(childId), method = "GET")
            try {
                val statusCode = connection.responseCode
                val responseBody = connection.readBody(statusCode)
                if (statusCode !in 200..299) {
                    throw ParentPolicyApiException(
                        "Parent policy API returned HTTP $statusCode: $responseBody",
                    )
                }
                ParentPolicyResponse.fromJsonString(responseBody)
            } catch (exception: IOException) {
                throw ParentPolicyApiException(
                    "Parent policy API request failed",
                    exception,
                )
            } finally {
                connection.disconnect()
            }
        }

    suspend fun updatePolicy(
        request: ParentPolicyUpdateRequest,
    ): ParentPolicyResponse = withContext(Dispatchers.IO) {
        val connection = openConnection(updateEndpoint(), method = "POST").apply {
            doOutput = true
        }
        try {
            val requestBody = request.toJsonString().toByteArray(Charsets.UTF_8)
            connection.outputStream.use { output ->
                output.write(requestBody)
            }

            val statusCode = connection.responseCode
            val responseBody = connection.readBody(statusCode)
            if (statusCode !in 200..299) {
                throw ParentPolicyApiException(
                    "Parent policy API returned HTTP $statusCode: $responseBody",
                )
            }
            ParentPolicyResponse.fromJsonString(responseBody)
        } catch (exception: IOException) {
            throw ParentPolicyApiException("Parent policy API request failed", exception)
        } finally {
            connection.disconnect()
        }
    }

    private fun openConnection(endpoint: String, method: String): HttpURLConnection {
        return (URL(endpoint).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = connectTimeoutMs
            readTimeout = readTimeoutMs
            setRequestProperty("Content-Type", "application/json; charset=utf-8")
            setRequestProperty("Accept", "application/json")
        }
    }

    private fun policyEndpoint(childId: String): String {
        return "${baseUrl.trimEnd('/')}/api/v1/parent/policy/${childId.urlEncode()}"
    }

    private fun updateEndpoint(): String {
        return "${baseUrl.trimEnd('/')}/api/v1/parent/policy"
    }
}

class ParentPolicyApiException(
    message: String,
    cause: Throwable? = null,
) : Exception(message, cause)

private fun String.urlEncode(): String {
    return URLEncoder.encode(this, Charsets.UTF_8.name())
}

private fun HttpURLConnection.readBody(statusCode: Int): String {
    val stream = if (statusCode in 200..299) inputStream else errorStream
    return stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
}
