package com.childai.companion.data.auth

import com.childai.companion.config.DevSettings
import com.childai.companion.data.conversation.readBody
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class AuthApiClient(
    private val baseUrl: String = DevSettings.conversationApiBaseUrl,
    private val connectTimeoutMs: Int = 8_000,
    private val readTimeoutMs: Int = 12_000,
) {
    suspend fun register(request: AuthRegisterRequest): AuthSession =
        postJson("auth/register", request.toJsonString())

    suspend fun login(request: AuthLoginRequest): AuthSession =
        postJson("auth/login", request.toJsonString())

    suspend fun logout(token: String) = withContext(Dispatchers.IO) {
        val connection = openConnection(authEndpoint("auth/logout"), "POST").apply {
            setBearerToken(token)
            doOutput = true
        }
        try {
            connection.outputStream.use { it.write(ByteArray(0)) }
            val statusCode = connection.responseCode
            val responseBody = connection.readBody(statusCode)
            if (statusCode !in 200..299) {
                throw AuthApiException("Auth logout returned HTTP $statusCode: $responseBody")
            }
        } catch (exception: IOException) {
            throw AuthApiException("Auth logout request failed", exception)
        } finally {
            connection.disconnect()
        }
    }

    suspend fun me(token: String): AuthAccount = withContext(Dispatchers.IO) {
        val connection = openConnection(authEndpoint("auth/me"), "GET").apply {
            setBearerToken(token)
        }
        try {
            val statusCode = connection.responseCode
            val responseBody = connection.readBody(statusCode)
            if (statusCode !in 200..299) {
                throw AuthApiException("Auth me returned HTTP $statusCode: $responseBody")
            }
            AuthAccount.fromJson(org.json.JSONObject(responseBody).getJSONObject("account"))
        } catch (exception: IOException) {
            throw AuthApiException("Auth me request failed", exception)
        } finally {
            connection.disconnect()
        }
    }

    private suspend fun postJson(path: String, body: String): AuthSession =
        withContext(Dispatchers.IO) {
            val connection = openConnection(authEndpoint(path), "POST").apply {
                doOutput = true
            }
            try {
                val requestBody = body.toByteArray(Charsets.UTF_8)
                connection.outputStream.use { output ->
                    output.write(requestBody)
                }
                val statusCode = connection.responseCode
                val responseBody = connection.readBody(statusCode)
                if (statusCode !in 200..299) {
                    throw AuthApiException("Auth API returned HTTP $statusCode: $responseBody")
                }
                AuthSession.fromJsonString(responseBody)
            } catch (exception: IOException) {
                throw AuthApiException("Auth API request failed", exception)
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

    private fun authEndpoint(path: String): String {
        return "${baseUrl.trimEnd('/')}/api/v1/${path.trimStart('/')}"
    }
}

class AuthApiException(
    message: String,
    cause: Throwable? = null,
) : Exception(message, cause)

internal fun HttpURLConnection.setBearerToken(token: String?) {
    if (!token.isNullOrBlank()) {
        setRequestProperty("Authorization", "Bearer $token")
    }
}
