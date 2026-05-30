package com.childai.companion.data.version

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

class VersionApiClient(private val baseUrl: String) {

    suspend fun checkVersion(): VersionCheckResult = withContext(Dispatchers.IO) {
        val url = URL("${baseUrl}api/v1/version/check")
        val conn = url.openConnection() as HttpURLConnection
        try {
            conn.requestMethod = "GET"
            conn.connectTimeout = 10_000
            conn.readTimeout = 10_000

            val responseCode = conn.responseCode
            if (responseCode != 200) {
                throw RuntimeException("版本检查失败: HTTP $responseCode")
            }

            val body = conn.inputStream.bufferedReader().readText()
            VersionCheckResult.fromJson(JSONObject(body))
        } finally {
            conn.disconnect()
        }
    }

    suspend fun downloadApk(downloadUrl: String, outputFile: File, onProgress: (Float) -> Unit = {}) =
        withContext(Dispatchers.IO) {
            val fullUrl = if (downloadUrl.startsWith("http")) {
                downloadUrl
            } else {
                "${baseUrl.trimEnd('/')}$downloadUrl"
            }

            val url = URL(fullUrl)
            val conn = url.openConnection() as HttpURLConnection
            try {
                conn.requestMethod = "GET"
                conn.connectTimeout = 30_000
                conn.readTimeout = 60_000
                conn.instanceFollowRedirects = true

                val responseCode = conn.responseCode
                if (responseCode != 200) {
                    throw RuntimeException("APK 下载失败: HTTP $responseCode")
                }

                val totalSize = conn.contentLength.toLong()
                var downloadedSize = 0L

                conn.inputStream.use { input ->
                    outputFile.outputStream().use { output ->
                        val buffer = ByteArray(8192)
                        var bytesRead: Int
                        while (input.read(buffer).also { bytesRead = it } != -1) {
                            output.write(buffer, 0, bytesRead)
                            downloadedSize += bytesRead
                            if (totalSize > 0) {
                                onProgress(downloadedSize.toFloat() / totalSize)
                            }
                        }
                    }
                }

                outputFile
            } finally {
                conn.disconnect()
            }
        }
}
