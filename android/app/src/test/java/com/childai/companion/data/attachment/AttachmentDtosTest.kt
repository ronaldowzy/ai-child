package com.childai.companion.data.attachment

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AttachmentDtosTest {
    @Test
    fun requestUsesMockHomeworkPhotoWithoutOriginalImageStorage() {
        val json = AttachmentCreateRequest(
            childId = "child_demo_001",
            sessionId = "session_001",
            mockOcrText = "小明有24个苹果，平均分给6个同学，每人几个？",
        ).toJsonString()

        assertTrue(json.contains("\"attachment_type\":\"homework_photo\""))
        assertTrue(json.contains("\"mock_ocr_text\""))
        assertTrue(json.contains("\"stores_original_image\":false"))
        assertFalse(json.contains("CameraX"))
    }

    @Test
    fun responseMarksHighConfidenceHomeworkTextReady() {
        val response = AttachmentCreateResponse.fromJsonString(
            """
            {
              "attachment_id": "att_001",
              "recognized_content": {
                "type": "homework_problem",
                "text": "小明有24个苹果，平均分给6个同学，每人几个？",
                "confidence": 0.94,
                "provider_name": "mock_ocr"
              },
              "reply": {
                "type": "agent_message",
                "text": "我看清楚了。我们先不急着算。你能告诉我：这道题是在问什么吗？",
                "voice_enabled": true,
                "emotion": "warm"
              },
              "ui_actions": [],
              "session_state": {
                "base_scene": "daily.after_school_checkin",
                "active_scene": "learning.homework_help",
                "needs_input": "problem_understanding"
              }
            }
            """.trimIndent(),
        )

        assertEquals("att_001", response.attachmentId)
        assertTrue(response.hasReadyHomeworkText)
        assertFalse(response.reply.text.contains("答案是"))
    }
}
