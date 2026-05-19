package com.childai.companion.data.parent

import com.childai.companion.config.DevSettings
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class ParentReportApiClient(
    private val baseUrl: String = DevSettings.conversationApiBaseUrl,
    private val connectTimeoutMs: Int = 8_000,
    private val readTimeoutMs: Int = 12_000,
) {
    suspend fun getReport(childId: String, date: String): ParentReport =
        withContext(Dispatchers.IO) {
            val connection = openConnection(reportEndpoint(childId, date))
            try {
                val statusCode = connection.responseCode
                val responseBody = connection.readBody(statusCode)
                if (statusCode !in 200..299) {
                    throw ParentReportApiException(
                        "Parent report API returned HTTP $statusCode: $responseBody",
                    )
                }
                ParentReport.fromJsonString(responseBody)
            } catch (exception: IOException) {
                throw ParentReportApiException(
                    "Parent report API request failed",
                    exception,
                )
            } finally {
                connection.disconnect()
            }
        }

    private fun openConnection(endpoint: String): HttpURLConnection {
        return (URL(endpoint).openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = connectTimeoutMs
            readTimeout = readTimeoutMs
            setRequestProperty("Accept", "application/json")
        }
    }

    private fun reportEndpoint(childId: String, date: String): String {
        return "${baseUrl.trimEnd('/')}/api/v1/parent/reports/" +
            "${childId.urlEncode()}?date=${date.urlEncode()}"
    }
}

class ParentReportApiException(
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
