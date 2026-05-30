package com.childai.companion.data.version

import org.json.JSONObject

data class VersionCheckResult(
    val versionName: String,
    val versionCode: Int,
    val title: String,
    val content: String,
    val forceUpdate: Boolean,
    val downloadUrl: String,
) {
    companion object {
        fun fromJson(json: JSONObject): VersionCheckResult = VersionCheckResult(
            versionName = json.getString("versionName"),
            versionCode = json.getInt("versionCode"),
            title = json.getString("title"),
            content = json.getString("content"),
            forceUpdate = json.getBoolean("forceUpdate"),
            downloadUrl = json.getString("downloadUrl"),
        )
    }
}
