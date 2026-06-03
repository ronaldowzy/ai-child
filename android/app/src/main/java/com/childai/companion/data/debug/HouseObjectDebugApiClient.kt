package com.childai.companion.data.debug

import android.util.Log
import com.childai.companion.config.DevSettings
import com.childai.companion.data.auth.setBearerToken
import com.childai.companion.data.conversation.CompanionObjectMeta
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

private const val TAG = "HouseObjectDebugApi"

class HouseObjectDebugApiClient(
    private val baseUrl: String = DevSettings.conversationApiBaseUrl,
    private val connectTimeoutMs: Int = 8_000,
    private val readTimeoutMs: Int = 12_000,
    private val authTokenProvider: () -> String? = { null },
    private val debugTokenProvider: () -> String = { DevSettings.debugToolsToken },
) {
    suspend fun create(
        visualKind: String,
        state: String,
        lightLocation: String,
    ): HouseObjectDebugCreateResponse = withContext(Dispatchers.IO) {
        val body = JSONObject()
            .put("visual_kind", visualKind)
            .put("state", state)
            .put("light_location", lightLocation)
            .toString()
        val connection = openConnection(createEndpoint())
        try {
            connection.outputStream.use { output ->
                output.write(body.toByteArray(Charsets.UTF_8))
            }
            val statusCode = connection.responseCode
            val responseBody = connection.readDebugBody(statusCode)
            Log.d(TAG, "create: status=$statusCode, bodyLength=${responseBody.length}")
            if (statusCode !in 200..299) {
                throw HouseObjectDebugApiException(
                    "House object debug create returned HTTP $statusCode: $responseBody",
                )
            }
            HouseObjectDebugCreateResponse.fromJsonString(responseBody)
        } catch (exception: IOException) {
            Log.e(TAG, "create: network error", exception)
            throw HouseObjectDebugApiException("House object debug create failed", exception)
        } finally {
            connection.disconnect()
        }
    }

    suspend fun reset(): HouseObjectDebugResetResponse = withContext(Dispatchers.IO) {
        val connection = openConnection(resetEndpoint())
        try {
            connection.outputStream.use { output ->
                output.write("{}".toByteArray(Charsets.UTF_8))
            }
            val statusCode = connection.responseCode
            val responseBody = connection.readDebugBody(statusCode)
            Log.d(TAG, "reset: status=$statusCode, bodyLength=${responseBody.length}")
            if (statusCode !in 200..299) {
                throw HouseObjectDebugApiException(
                    "House object debug reset returned HTTP $statusCode: $responseBody",
                )
            }
            HouseObjectDebugResetResponse.fromJsonString(responseBody)
        } catch (exception: IOException) {
            Log.e(TAG, "reset: network error", exception)
            throw HouseObjectDebugApiException("House object debug reset failed", exception)
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
            setRequestProperty("X-Child-AI-Debug-Token", debugTokenProvider())
            setBearerToken(authTokenProvider())
        }
    }

    private fun createEndpoint(): String {
        return "${baseUrl.trimEnd('/')}/api/v1/debug/house-object/create"
    }

    private fun resetEndpoint(): String {
        return "${baseUrl.trimEnd('/')}/api/v1/debug/house-object/reset"
    }
}

data class HouseObjectDebugCreateResponse(
    val companionObject: CompanionObjectMeta,
) {
    companion object {
        fun fromJsonString(rawJson: String): HouseObjectDebugCreateResponse {
            val root = JSONObject(rawJson)
            return HouseObjectDebugCreateResponse(
                companionObject = CompanionObjectMeta.fromJson(
                    root.getJSONObject("companion_object"),
                ),
            )
        }
    }
}

data class HouseObjectDebugResetResponse(
    val retiredCount: Int,
) {
    companion object {
        fun fromJsonString(rawJson: String): HouseObjectDebugResetResponse {
            val root = JSONObject(rawJson)
            return HouseObjectDebugResetResponse(
                retiredCount = root.optInt("retired_count", 0),
            )
        }
    }
}

class HouseObjectDebugApiException(
    message: String,
    cause: Throwable? = null,
) : Exception(message, cause)

private fun HttpURLConnection.readDebugBody(statusCode: Int): String {
    val stream = if (statusCode in 200..299) inputStream else errorStream
    return stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
}
