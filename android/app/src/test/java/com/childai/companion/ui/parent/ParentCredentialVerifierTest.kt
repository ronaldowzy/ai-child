package com.childai.companion.ui.parent

import com.childai.companion.data.auth.AuthLoginRequest
import com.childai.companion.data.auth.AuthRegisterRequest
import com.childai.companion.data.auth.AuthSessionRepository
import com.childai.companion.data.auth.SavedAuthSession
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ParentCredentialVerifierTest {
    @Test
    fun verifiesAgainstSavedUsernameAndSubmittedPassword() = runBlocking {
        val repository = FakeAuthSessionRepository(
            initialSession = savedSession(username = "parent-one"),
        )
        val verifier = ParentCredentialVerifier(repository)

        assertTrue(verifier.verify("safe-password-123"))

        assertEquals(AuthLoginRequest("parent-one", "safe-password-123"), repository.loginRequests.single())
    }

    @Test
    fun rejectsBlankPasswordWithoutCallingLogin() = runBlocking {
        val repository = FakeAuthSessionRepository(
            initialSession = savedSession(username = "parent-one"),
        )
        val verifier = ParentCredentialVerifier(repository)

        assertFalse(verifier.verify(" "))

        assertTrue(repository.loginRequests.isEmpty())
    }

    @Test
    fun rejectsWhenBackendLoginFails() = runBlocking {
        val repository = FakeAuthSessionRepository(
            initialSession = savedSession(username = "parent-one"),
            loginFailure = IllegalStateException("invalid username or password"),
        )
        val verifier = ParentCredentialVerifier(repository)

        assertFalse(verifier.verify("wrong-password"))

        assertEquals(AuthLoginRequest("parent-one", "wrong-password"), repository.loginRequests.single())
    }
}

private class FakeAuthSessionRepository(
    initialSession: SavedAuthSession,
    private val loginFailure: Throwable? = null,
) : AuthSessionRepository {
    private var currentSession: SavedAuthSession = initialSession
    val loginRequests = mutableListOf<AuthLoginRequest>()

    override fun savedSession(): SavedAuthSession = currentSession

    override fun authToken(): String? = currentSession.token.takeIf { it.isNotBlank() }

    override fun childIdOrNull(): String? = currentSession.childId.takeIf { it.isNotBlank() }

    override suspend fun register(request: AuthRegisterRequest): SavedAuthSession = currentSession

    override suspend fun login(request: AuthLoginRequest): SavedAuthSession {
        loginRequests += request
        loginFailure?.let { throw it }
        currentSession = currentSession.copy(token = "refreshed-token")
        return currentSession
    }

    override suspend fun refreshAccount(): SavedAuthSession = currentSession

    override suspend fun logout() {
        currentSession = SavedAuthSession.Empty
    }
}

private fun savedSession(username: String): SavedAuthSession =
    SavedAuthSession(
        token = "token",
        childId = "child_1",
        username = username,
        expiresAt = "2026-06-24T00:00:00Z",
    )
