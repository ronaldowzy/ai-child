package com.childai.companion.data.auth

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class AuthDtosTest {
    @Test
    fun registerRequestSerializesParentOperatedChildProfile() {
        val request = AuthRegisterRequest(
            username = "parent-one",
            password = "safe-password",
            childNickname = "豆豆",
            childAge = 8,
            childInterests = listOf("恐龙", "画画"),
            topicBoundaries = listOf("比赛成绩"),
        )

        val json = request.toJsonString()

        assertTrue(json.contains("\"username\":\"parent-one\""))
        assertTrue(json.contains("\"password\":\"safe-password\""))
        assertTrue(json.contains("\"child_nickname\":\"豆豆\""))
        assertTrue(json.contains("\"child_interests\":[\"恐龙\",\"画画\"]"))
    }

    @Test
    fun authSessionParsesAccountChildIdAndToken() {
        val session = AuthSession.fromJsonString(
            """
            {
              "token": "token_123",
              "token_type": "bearer",
              "expires_at": "2026-06-24T00:00:00Z",
              "account": {
                "child_account_id": "acct_1",
                "child_id": "child_1",
                "username": "parent-one",
                "child_nickname": "豆豆",
                "child_display_name": null,
                "child_age": 8,
                "child_grade": "二年级",
                "child_call_preference": "叫小名",
                "child_interests": ["恐龙", "画画"],
                "topic_boundaries": ["比赛成绩"]
              }
            }
            """.trimIndent(),
        )

        assertEquals("token_123", session.token)
        assertEquals("child_1", session.account.childId)
        assertEquals("豆豆", session.account.childNickname)
        assertEquals(listOf("恐龙", "画画"), session.account.childInterests)
    }

    @Test
    fun inMemorySessionStoreKeepsAndClearsLogin() {
        val store = InMemoryAuthSessionStore()
        val session = SavedAuthSession(
            token = "token",
            childId = "child_1",
            username = "parent-one",
            expiresAt = "2026-06-24T00:00:00Z",
        )

        store.save(session)

        assertEquals(session, store.read())
        assertTrue(store.read().isPresent)

        store.clear()

        assertEquals(SavedAuthSession.Empty, store.read())
    }
}
