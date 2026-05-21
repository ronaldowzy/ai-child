package com.childai.companion.data

import com.childai.companion.data.conversation.ConversationMessageRequest
import com.childai.companion.data.conversation.ConversationInput
import com.childai.companion.data.conversation.ClientContext
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.data.conversation.ConversationStreamOptions
import com.childai.companion.data.conversation.toStreamJsonString
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ConversationStreamDtosTest {
    @Test
    fun parsesNdjsonEvents() {
        val events = ConversationStreamEvent.parseNdjson(
            """
            {"seq":1,"type":"session_started","request_id":"req-1","payload":{"requestId":"req-1"}}
            {"seq":2,"type":"text_delta","payload":{"delta":"你好"}}
            {"seq":3,"type":"audio_ready","payload":{"index":0,"audioUrl":"/media/tts/a.wav","text":"你好"}}
            """.trimIndent(),
        )

        assertEquals(3, events.size)
        assertEquals("session_started", events[0].type)
        assertEquals("req-1", events[0].requestId)
        assertEquals("你好", events[1].delta)
        assertEquals("/media/tts/a.wav", events[2].audioUrl)
        assertEquals("你好", events[2].audioText)
    }

    @Test
    fun serializesStreamOptionsIntoConversationRequest() {
        val rawJson = ConversationMessageRequest(
            childId = "child_demo",
            sessionId = "session_demo",
            input = ConversationInput(text = "我想聊恐龙"),
            clientContext = ClientContext(
                deviceTime = "2026-05-21T20:00:00+08:00",
                timezone = "Asia/Shanghai",
            ),
        ).toStreamJsonString(
            ConversationStreamOptions(
                includeTts = false,
                clientTurnId = "turn-1",
            ),
        )

        val streamOptions = JSONObject(rawJson).getJSONObject("stream_options")
        assertEquals("stream.v0.1", streamOptions.getString("protocol_version"))
        assertFalse(streamOptions.getBoolean("include_tts"))
        assertEquals("turn-1", streamOptions.getString("client_turn_id"))
        assertTrue(JSONObject(rawJson).getJSONObject("input").has("attachments"))
    }
}
