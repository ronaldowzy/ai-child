package com.childai.companion.data.auth

import android.content.Context

interface AuthSessionStore {
    fun read(): SavedAuthSession
    fun save(session: SavedAuthSession)
    fun clear()
}

class SharedPreferencesAuthSessionStore(
    context: Context,
) : AuthSessionStore {
    private val preferences = context.getSharedPreferences(
        "xiaobaohu_auth_session",
        Context.MODE_PRIVATE,
    )

    override fun read(): SavedAuthSession {
        return SavedAuthSession(
            token = preferences.getString(KEY_TOKEN, "").orEmpty(),
            childId = preferences.getString(KEY_CHILD_ID, "").orEmpty(),
            username = preferences.getString(KEY_USERNAME, "").orEmpty(),
            expiresAt = preferences.getString(KEY_EXPIRES_AT, "").orEmpty(),
        )
    }

    override fun save(session: SavedAuthSession) {
        preferences.edit()
            .putString(KEY_TOKEN, session.token)
            .putString(KEY_CHILD_ID, session.childId)
            .putString(KEY_USERNAME, session.username)
            .putString(KEY_EXPIRES_AT, session.expiresAt)
            .apply()
    }

    override fun clear() {
        preferences.edit().clear().apply()
    }

    private companion object {
        const val KEY_TOKEN = "token"
        const val KEY_CHILD_ID = "child_id"
        const val KEY_USERNAME = "username"
        const val KEY_EXPIRES_AT = "expires_at"
    }
}

class InMemoryAuthSessionStore(
    initial: SavedAuthSession = SavedAuthSession.Empty,
) : AuthSessionStore {
    private var session: SavedAuthSession = initial

    override fun read(): SavedAuthSession = session

    override fun save(session: SavedAuthSession) {
        this.session = session
    }

    override fun clear() {
        session = SavedAuthSession.Empty
    }
}
