package com.childai.companion.ui.parent

import com.childai.companion.data.auth.AuthLoginRequest
import com.childai.companion.data.auth.AuthSessionRepository

class ParentCredentialVerifier(
    private val repository: AuthSessionRepository,
) {
    suspend fun verify(password: String): Boolean {
        val username = repository.savedSession().username.trim()
        if (username.isBlank() || password.isBlank()) return false
        return runCatching {
            repository.login(
                AuthLoginRequest(
                    username = username,
                    password = password,
                ),
            )
            true
        }.getOrDefault(false)
    }
}
