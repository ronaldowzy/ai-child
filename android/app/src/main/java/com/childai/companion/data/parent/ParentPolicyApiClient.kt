package com.childai.companion.data.parent

import android.util.Log
import com.childai.companion.config.DevSettings
import com.childai.companion.data.auth.setBearerToken
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

private const val TAG = "ParentPolicyApi"

class ParentPolicyApiClient(
    private val baseUrl: String = DevSettings.conversationApiBaseUrl,
    private val connectTimeoutMs: Int = 8_000,
    private val readTimeoutMs: Int = 12_000,
    private val authTokenProvider: () -> String? = { null },
) {
    suspend fun getPolicy(childId: String): ParentPolicyResponse =
        withContext(Dispatchers.IO) {
            val endpoint = policyEndpoint(childId)
            Log.d(TAG, "getPolicy: endpoint=$endpoint, childId=$childId")
            val connection = openConnection(endpoint, method = "GET")
            try {
                val statusCode = connection.responseCode
                val responseBody = connection.readBody(statusCode)
                Log.d(TAG, "getPolicy: status=$statusCode, bodyLength=${responseBody.length}, body=${responseBody.take(200)}")
                if (statusCode !in 200..299) {
                    Log.e(TAG, "getPolicy: error body=$responseBody")
                    throw ParentPolicyApiException(
                        "Parent policy API returned HTTP $statusCode: $responseBody",
                    )
                }
                val result = ParentPolicyResponse.fromJsonString(responseBody)
                Log.d(TAG, "getPolicy: parsed childAge=${result.communicationPreferences["child_age"]}, childGender=${result.communicationPreferences["child_gender"]}")
                result
            } catch (exception: IOException) {
                Log.e(TAG, "getPolicy: network error", exception)
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
        Log.d(TAG, "updatePolicy: childId=${request.childId}")
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
            Log.d(TAG, "updatePolicy: status=$statusCode, bodyLength=${responseBody.length}")
            if (statusCode !in 200..299) {
                Log.e(TAG, "updatePolicy: error body=$responseBody")
                throw ParentPolicyApiException(
                    "Parent policy API returned HTTP $statusCode: $responseBody",
                )
            }
            ParentPolicyResponse.fromJsonString(responseBody)
        } catch (exception: IOException) {
            Log.e(TAG, "updatePolicy: network error", exception)
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
            setBearerToken(authTokenProvider())
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
