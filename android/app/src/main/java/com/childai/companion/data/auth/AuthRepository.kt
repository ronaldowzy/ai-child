package com.childai.companion.data.auth

class AuthRepository(
    private val apiClient: AuthRemoteDataSource = AuthApiClient(),
    private val sessionStore: AuthSessionStore,
) : AuthSessionRepository {
    override fun savedSession(): SavedAuthSession = sessionStore.read()

    override fun authToken(): String? = sessionStore.read().token.takeIf { it.isNotBlank() }

    override fun childIdOrNull(): String? = sessionStore.read().childId.takeIf { it.isNotBlank() }

    override suspend fun register(request: AuthRegisterRequest): SavedAuthSession {
        return save(apiClient.register(request))
    }

    override suspend fun login(request: AuthLoginRequest): SavedAuthSession {
        return save(apiClient.login(request))
    }

    override suspend fun refreshAccount(): SavedAuthSession {
        val current = sessionStore.read()
        if (!current.isPresent) return SavedAuthSession.Empty
        val account = apiClient.me(current.token)
        val refreshed = current.copy(
            childId = account.childId,
            username = account.username,
        )
        sessionStore.save(refreshed)
        return refreshed
    }

    override suspend fun logout() {
        val token = sessionStore.read().token
        if (token.isNotBlank()) {
            runCatching { apiClient.logout(token) }
        }
        sessionStore.clear()
    }

    private fun save(session: AuthSession): SavedAuthSession {
        val saved = SavedAuthSession(
            token = session.token,
            childId = session.account.childId,
            username = session.account.username,
            expiresAt = session.expiresAt,
        )
        sessionStore.save(saved)
        return saved
    }
}
