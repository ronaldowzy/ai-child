package com.childai.companion.data.attachment

import com.childai.companion.config.DevSettings
import com.childai.companion.data.auth.setBearerToken
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class AttachmentApiClient(
    private val baseUrl: String = DevSettings.conversationApiBaseUrl,
    private val connectTimeoutMs: Int = 8_000,
    private val readTimeoutMs: Int = 12_000,
    private val authTokenProvider: () -> String? = { null },
) {
    suspend fun uploadImage(
        childId: String,
        sessionId: String,
        imageBytes: ByteArray,
        mimeType: String,
        fileName: String,
        imagePurpose: String,
        childCaption: String,
    ): AttachmentCreateResponse = withContext(Dispatchers.IO) {
        val boundary = "XiaobaohuBoundary-${UUID.randomUUID()}"
        val connection = openMultipartConnection(boundary)
        try {
            connection.outputStream.use { output ->
                output.writeTextPart(boundary, "child_id", childId)
                output.writeTextPart(boundary, "session_id", sessionId)
                output.writeTextPart(boundary, "image_purpose", imagePurpose)
                output.writeTextPart(boundary, "child_caption", childCaption)
                output.writeFilePart(
                    boundary = boundary,
                    name = "file",
                    fileName = fileName.ifBlank { "xiaobaohu_photo.jpg" },
                    mimeType = mimeType.ifBlank { "image/jpeg" },
                    bytes = imageBytes,
                )
                output.write("--$boundary--\r\n".toByteArray(Charsets.UTF_8))
            }

            val statusCode = connection.responseCode
            val responseBody = connection.readBody(statusCode)
            if (statusCode !in 200..299) {
                throw AttachmentApiException(
                    "Image upload returned HTTP $statusCode: $responseBody",
                )
            }
            AttachmentCreateResponse.fromJsonString(responseBody)
        } catch (exception: IOException) {
            throw AttachmentApiException("Image upload request failed", exception)
        } finally {
            connection.disconnect()
        }
    }

    private fun openMultipartConnection(boundary: String): HttpURLConnection {
        return (URL(imageUploadEndpoint()).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = connectTimeoutMs
            readTimeout = readTimeoutMs
            doOutput = true
            setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
            setRequestProperty("Accept", "application/json")
            setBearerToken(authTokenProvider())
        }
    }

    private fun imageUploadEndpoint(): String {
        return "${baseUrl.trimEnd('/')}/api/v1/attachments/images"
    }
}

class AttachmentApiException(
    message: String,
    cause: Throwable? = null,
) : Exception(message, cause)

private fun HttpURLConnection.readBody(statusCode: Int): String {
    val stream = if (statusCode in 200..299) inputStream else errorStream
    return stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
}

private fun java.io.OutputStream.writeTextPart(
    boundary: String,
    name: String,
    value: String,
) {
    write("--$boundary\r\n".toByteArray(Charsets.UTF_8))
    write("Content-Disposition: form-data; name=\"$name\"\r\n\r\n".toByteArray(Charsets.UTF_8))
    write(value.toByteArray(Charsets.UTF_8))
    write("\r\n".toByteArray(Charsets.UTF_8))
}

private fun java.io.OutputStream.writeFilePart(
    boundary: String,
    name: String,
    fileName: String,
    mimeType: String,
    bytes: ByteArray,
) {
    write("--$boundary\r\n".toByteArray(Charsets.UTF_8))
    write(
        "Content-Disposition: form-data; name=\"$name\"; filename=\"$fileName\"\r\n"
            .toByteArray(Charsets.UTF_8),
    )
    write("Content-Type: $mimeType\r\n\r\n".toByteArray(Charsets.UTF_8))
    write(bytes)
    write("\r\n".toByteArray(Charsets.UTF_8))
}
