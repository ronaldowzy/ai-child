package com.childai.companion.data.auth

import org.json.JSONArray
import org.json.JSONObject

data class AuthAccount(
    val childAccountId: String,
    val childId: String,
    val username: String,
    val childNickname: String?,
    val childDisplayName: String?,
    val childAge: Int?,
    val childGrade: String?,
    val childCallPreference: String?,
    val childInterests: List<String>,
    val topicBoundaries: List<String>,
) {
    companion object {
        fun fromJson(json: JSONObject): AuthAccount {
            return AuthAccount(
                childAccountId = json.getString("child_account_id"),
                childId = json.getString("child_id"),
                username = json.getString("username"),
                childNickname = json.optNullableString("child_nickname"),
                childDisplayName = json.optNullableString("child_display_name"),
                childAge = if (json.has("child_age") && !json.isNull("child_age")) {
                    json.optInt("child_age")
                } else {
                    null
                },
                childGrade = json.optNullableString("child_grade"),
                childCallPreference = json.optNullableString("child_call_preference"),
                childInterests = json.optJSONArray("child_interests").toStringList(),
                topicBoundaries = json.optJSONArray("topic_boundaries").toStringList(),
            )
        }
    }
}

data class AuthSession(
    val token: String,
    val tokenType: String,
    val expiresAt: String,
    val account: AuthAccount,
) {
    companion object {
        fun fromJsonString(rawJson: String): AuthSession {
            val root = JSONObject(rawJson)
            return AuthSession(
                token = root.getString("token"),
                tokenType = root.optString("token_type", "bearer"),
                expiresAt = root.getString("expires_at"),
                account = AuthAccount.fromJson(root.getJSONObject("account")),
            )
        }
    }
}

data class AuthRegisterRequest(
    val username: String,
    val password: String,
    val childNickname: String = "",
    val childDisplayName: String = "",
    val childAge: Int? = null,
    val childGrade: String = "",
    val childCallPreference: String = "",
    val childInterests: List<String> = emptyList(),
    val topicBoundaries: List<String> = emptyList(),
) {
    fun toJsonString(): String {
        return JSONObject()
            .put("username", username)
            .put("password", password)
            .put("child_nickname", childNickname.ifBlank { JSONObject.NULL })
            .put("child_display_name", childDisplayName.ifBlank { JSONObject.NULL })
            .put("child_age", childAge ?: JSONObject.NULL)
            .put("child_grade", childGrade.ifBlank { JSONObject.NULL })
            .put("child_call_preference", childCallPreference.ifBlank { JSONObject.NULL })
            .put("child_interests", JSONArray(childInterests))
            .put("topic_boundaries", JSONArray(topicBoundaries))
            .toString()
    }
}

data class AuthLoginRequest(
    val username: String,
    val password: String,
) {
    fun toJsonString(): String {
        return JSONObject()
            .put("username", username)
            .put("password", password)
            .toString()
    }
}

data class SavedAuthSession(
    val token: String,
    val childId: String,
    val username: String,
    val expiresAt: String,
) {
    val isPresent: Boolean
        get() = token.isNotBlank() && childId.isNotBlank()

    companion object {
        val Empty = SavedAuthSession(
            token = "",
            childId = "",
            username = "",
            expiresAt = "",
        )
    }
}

private fun JSONArray?.toStringList(): List<String> {
    if (this == null) return emptyList()
    return buildList {
        for (index in 0 until length()) {
            val item = optString(index).trim()
            if (item.isNotEmpty()) add(item)
        }
    }
}

private fun JSONObject.optNullableString(name: String): String? {
    if (!has(name) || isNull(name)) return null
    return optString(name).takeIf { it.isNotBlank() }
}
