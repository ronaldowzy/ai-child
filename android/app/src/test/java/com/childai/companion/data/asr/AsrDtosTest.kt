package com.childai.companion.data.asr

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class AsrDtosTest {
    @Test
    fun requestUsesBackendAsrContractAndConfirmBeforeSendMode() {
        val request = AsrTranscriptionRequest(
            childId = "child_demo_001",
            sessionId = "android-session",
            audio = AsrAudioPayload(
                data = "data:audio/wav;base64,UklGRg==",
                sampleRateHz = 16000,
                channelCount = 1,
                durationMs = 1200,
            ),
            clientContext = AsrClientContext(
                deviceTime = "2026-05-21T20:00:00+08:00",
                timezone = "Asia/Shanghai",
            ),
        )

        val json = JSONObject(request.toJsonString())

        assertEquals("child_demo_001", json.getString("childId"))
        assertEquals("android-session", json.getString("sessionId"))
        assertEquals("confirm_before_send", json.getString("mode"))
        assertEquals("zh-CN", json.getString("language"))
        assertEquals("wav", json.getJSONObject("audio").getString("format"))
        assertEquals(16000, json.getJSONObject("audio").getInt("sampleRateHz"))
        assertEquals(1, json.getJSONObject("audio").getInt("channelCount"))
        assertEquals(1200, json.getJSONObject("audio").getInt("durationMs"))
    }

    @Test
    fun parsesOkTranscriptResponse() {
        val response = AsrTranscriptionResponse.fromJsonString(
            """
            {
              "status": "ok",
              "transcript": "我想聊恐龙。",
              "requiresConfirmation": true,
              "provider": "mock",
              "model": "mock-asr-v0",
              "language": "zh-CN",
              "durationMs": 1200,
              "confidence": null,
              "errorCode": null,
              "fallbackAction": null
            }
            """.trimIndent(),
        )

        assertEquals("ok", response.status)
        assertEquals("我想聊恐龙。", response.transcript)
        assertTrue(response.requiresConfirmation)
        assertEquals("mock", response.provider)
        assertEquals("mock-asr-v0", response.model)
        assertEquals(1200, response.durationMs)
        assertNull(response.errorCode)
    }

    @Test
    fun parsesNeedsRetryWithoutTranscript() {
        val response = AsrTranscriptionResponse.fromJsonString(
            """
            {
              "status": "needs_retry",
              "transcript": null,
              "requiresConfirmation": true,
              "provider": "mock",
              "model": "mock-asr-v0",
              "language": "zh-CN",
              "durationMs": 900,
              "errorCode": "empty_transcript",
              "fallbackAction": "retry_or_type"
            }
            """.trimIndent(),
        )

        assertEquals("needs_retry", response.status)
        assertNull(response.transcript)
        assertEquals("empty_transcript", response.errorCode)
        assertEquals("retry_or_type", response.fallbackAction)
    }
}
