package com.childai.companion.data

import com.childai.companion.data.conversation.CompanionObjectMeta
import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ClientContext
import com.childai.companion.data.conversation.ConversationOpeningRequest
import com.childai.companion.data.conversation.ConversationSessionState
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ConversationDtosTest {
    @Test
    fun parsesVoiceAndAgentMotionFieldsForFutureFoxAnimation() {
        val response = ConversationMessageResponse.fromJsonString(
            """
            {
              "reply": {
                "type": "agent_message",
                "text": "我在听。",
                "voice_enabled": true,
                "audio_url": null,
                "emotion": "warm",
                "agent_motion": "listening_tail"
              },
              "ui_actions": [],
              "session_state": {
                "base_scene": "daily.after_school_checkin",
                "active_scene": "daily.after_school_checkin",
                "needs_input": "child_choice"
              }
            }
            """.trimIndent(),
        )

        assertTrue(response.reply.voiceEnabled)
        assertNull(response.reply.audioUrl)
        assertEquals("warm", response.reply.emotion)
        assertEquals("listening_tail", response.reply.agentMotion)
    }

    @Test
    fun defaultsVoiceAndAgentMotionForOlderBackendResponses() {
        val response = ConversationMessageResponse.fromJsonString(
            """
            {
              "reply": {
                "type": "agent_message",
                "text": "我在听。",
                "emotion": "warm"
              },
              "ui_actions": [],
              "session_state": {
                "base_scene": "daily.after_school_checkin",
                "active_scene": "daily.after_school_checkin"
              }
            }
            """.trimIndent(),
        )

        assertTrue(response.reply.voiceEnabled)
        assertNull(response.reply.audioUrl)
        assertEquals("gentle_idle", response.reply.agentMotion)
    }

    @Test
    fun serializesOpeningRequest() {
        val rawJson = ConversationOpeningRequest(
            childId = "child_demo",
            sessionId = "session_demo",
            clientContext = ClientContext(
                deviceTime = "2026-05-21T18:30:00+08:00",
                timezone = "Asia/Shanghai",
            ),
        ).toJsonString()

        val root = JSONObject(rawJson)
        assertEquals("child_demo", root.getString("child_id"))
        assertEquals("session_demo", root.getString("session_id"))
        assertEquals(
            "child",
            root.getJSONObject("client_context").getString("app_mode"),
        )
    }

    @Test
    fun serializesQuickActionIdOnMessageRequest() {
        val rawJson = com.childai.companion.data.conversation.ConversationMessageRequest(
            childId = "child_demo",
            sessionId = "session_demo",
            input = com.childai.companion.data.conversation.ConversationInput(
                text = "起个名字",
                quickActionId = "companion_name",
            ),
            clientContext = ClientContext(
                deviceTime = "2026-05-21T18:30:00+08:00",
                timezone = "Asia/Shanghai",
            ),
        ).toJsonString()

        val root = JSONObject(rawJson)
        assertEquals(
            "companion_name",
            root.getJSONObject("input").getString("quick_action_id"),
        )
    }

    @Test
    fun sessionStateParsesCompanionObjectForRecall() {
        val json = JSONObject(
            """
            {
                "base_scene": "daily.after_school",
                "active_scene": "companion.recall",
                "companion_object": {
                    "id": "co_123",
                    "name": "小棉花",
                    "object_type": "小星星",
                    "light_location": "窗边",
                    "state": "active",
                    "action": "recall"
                }
            }
            """.trimIndent(),
        )
        val state = ConversationSessionState.fromJson(json)

        assertNotNull(state.companionObject)
        assertEquals("co_123", state.companionObject?.id)
        assertEquals("小棉花", state.companionObject?.name)
        assertEquals("小星星", state.companionObject?.objectType)
        assertEquals("窗边", state.companionObject?.lightLocation)
        assertEquals("active", state.companionObject?.state)
        assertEquals("recall", state.companionObject?.action)
    }

    @Test
    fun sessionStateParsesCompanionObjectForSeed() {
        val json = JSONObject(
            """
            {
                "base_scene": "daily.first_open",
                "active_scene": "companion.star_seed",
                "companion_object": {
                    "id": "seed_001",
                    "name": "",
                    "object_type": "小星星",
                    "light_location": "窗边",
                    "state": "seed",
                    "action": "name_seed"
                }
            }
            """.trimIndent(),
        )
        val state = ConversationSessionState.fromJson(json)

        assertNotNull(state.companionObject)
        assertEquals("seed", state.companionObject?.state)
        assertEquals("name_seed", state.companionObject?.action)
    }

    @Test
    fun sessionStateParsesBackendEnumObjectTypeForSeed() {
        val json = JSONObject(
            """
            {
                "base_scene": "conversation.open",
                "active_scene": "conversation.open",
                "companion_object": {
                    "id": "star_seed",
                    "name": "小星星",
                    "object_type": "star",
                    "light_location": "窗边",
                    "state": "seed",
                    "action": "name_seed"
                }
            }
            """.trimIndent(),
        )
        val state = ConversationSessionState.fromJson(json)

        assertEquals("star", state.companionObject?.objectType)
        assertEquals("小星星", state.companionObject?.name)
    }

    @Test
    fun sessionStateHandlesNullCompanionObject() {
        val json = JSONObject(
            """
            {
                "base_scene": "daily.after_school",
                "active_scene": "free_chat"
            }
            """.trimIndent(),
        )
        val state = ConversationSessionState.fromJson(json)

        assertNull(state.companionObject)
    }

    @Test
    fun sessionStateHandlesMissingCompanionObjectField() {
        val json = JSONObject(
            """
            {
                "base_scene": "daily.after_school",
                "active_scene": "free_chat",
                "needs_input": null,
                "requires_parent_attention": false
            }
            """.trimIndent(),
        )
        val state = ConversationSessionState.fromJson(json)

        assertNull(state.companionObject)
    }

    @Test
    fun sessionStateDisplayTextIncludesCompanionInfo() {
        val state = ConversationSessionState(
            baseScene = "daily.after_school",
            activeScene = "companion.recall",
            needsInput = null,
            requiresParentAttention = false,
            companionObject = CompanionObjectMeta(
                id = "co_123",
                name = "小棉花",
                objectType = "小星星",
                lightLocation = "窗边",
                state = "active",
                action = "recall",
            ),
        )

        val text = state.toDisplayText()
        assertTrue(text.contains("companion=active/recall"))
    }
}
