package com.childai.companion.data.version

import android.content.Context
import java.io.File

class VersionRepository(private val context: Context, baseUrl: String) {

    private val apiClient = VersionApiClient(baseUrl)

    suspend fun checkForUpdate(currentVersionCode: Int): VersionCheckResult? {
        return try {
            val result = apiClient.checkVersion()
            if (result.versionCode > currentVersionCode) {
                result
            } else {
                null
            }
        } catch (e: Exception) {
            // 版本检查失败不影响正常使用
            null
        }
    }

    suspend fun downloadApk(downloadUrl: String, onProgress: (Float) -> Unit = {}): File {
        val apkDir = File(context.cacheDir, "updates")
        apkDir.mkdirs()
        val apkFile = File(apkDir, "update.apk")

        // 删除旧的下载文件
        if (apkFile.exists()) {
            apkFile.delete()
        }

        return apiClient.downloadApk(downloadUrl, apkFile, onProgress)
    }
}
