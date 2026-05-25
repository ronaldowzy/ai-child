package com.childai.companion.ui.auth

import com.childai.companion.data.auth.AuthLoginRequest
import com.childai.companion.data.auth.AuthRegisterRequest
import com.childai.companion.data.auth.AuthSessionRepository
import com.childai.companion.data.auth.SavedAuthSession
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AuthViewModelTest {
    @Test
    fun savedSessionRefreshKeepsLoginState() {
        val refreshed = savedSession(childId = "child_refreshed")
        val repository = FakeAuthSessionRepository(
            initialSession = savedSession(childId = "child_stale"),
            refreshedSession = refreshed,
        )

        val viewModel = AuthViewModel(repository, dispatcher = Dispatchers.Unconfined)

        assertTrue(viewModel.uiState.value.isLoggedIn)
        assertEquals(refreshed, viewModel.uiState.value.session)
        assertEquals(1, repository.refreshCalls)
        assertEquals(0, repository.logoutCalls)
    }

    @Test
    fun invalidSavedSessionLogsOutAndClearsState() {
        val repository = FakeAuthSessionRepository(
            initialSession = savedSession(childId = "child_expired"),
            refreshFailure = IllegalStateException("invalid or expired session"),
        )

        val viewModel = AuthViewModel(repository, dispatcher = Dispatchers.Unconfined)

        assertFalse(viewModel.uiState.value.isLoggedIn)
        assertEquals(SavedAuthSession.Empty, viewModel.uiState.value.session)
        assertEquals(1, repository.refreshCalls)
        assertEquals(1, repository.logoutCalls)
    }

    @Test
    fun logoutClearsSavedSession() {
        val repository = FakeAuthSessionRepository(
            initialSession = savedSession(childId = "child_logged_in"),
            refreshedSession = savedSession(childId = "child_logged_in"),
        )
        val viewModel = AuthViewModel(repository, dispatcher = Dispatchers.Unconfined)

        viewModel.logout()

        assertFalse(viewModel.uiState.value.isLoggedIn)
        assertEquals(SavedAuthSession.Empty, viewModel.uiState.value.session)
        assertEquals(1, repository.logoutCalls)
    }

    private fun savedSession(childId: String): SavedAuthSession {
        return SavedAuthSession(
            token = "token_$childId",
            childId = childId,
            username = "parent-one",
            expiresAt = "2026-06-24T00:00:00Z",
        )
    }
}

private class FakeAuthSessionRepository(
    initialSession: SavedAuthSession,
    private val refreshedSession: SavedAuthSession = initialSession,
    private val refreshFailure: Throwable? = null,
) : AuthSessionRepository {
    private var currentSession = initialSession
    var refreshCalls = 0
        private set
    var logoutCalls = 0
        private set

    override fun savedSession(): SavedAuthSession = currentSession

    override fun authToken(): String? = currentSession.token.takeIf { it.isNotBlank() }

    override fun childIdOrNull(): String? = currentSession.childId.takeIf { it.isNotBlank() }

    override suspend fun register(request: AuthRegisterRequest): SavedAuthSession {
        currentSession = refreshedSession
        return currentSession
    }

    override suspend fun login(request: AuthLoginRequest): SavedAuthSession {
        currentSession = refreshedSession
        return currentSession
    }

    override suspend fun refreshAccount(): SavedAuthSession {
        refreshCalls += 1
        refreshFailure?.let { throw it }
        currentSession = refreshedSession
        return currentSession
    }

    override suspend fun logout() {
        logoutCalls += 1
        currentSession = SavedAuthSession.Empty
    }
}
