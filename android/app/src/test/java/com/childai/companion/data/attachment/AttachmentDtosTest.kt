package com.childai.companion.data.attachment

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AttachmentDtosTest {
    @Test
    fun requestUsesGenericImageWithoutOriginalImageStorage() {
        val json = AttachmentCreateRequest(
            childId = "child_demo_001",
            sessionId = "session_001",
            imagePurpose = "share",
            mockVisionText = "我搭了一个积木城堡",
        ).toJsonString()

        assertTrue(json.contains("\"attachment_type\":\"image\""))
        assertTrue(json.contains("\"image_purpose\":\"share\""))
        assertTrue(json.contains("\"mock_vision_text\""))
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
                "provider_name": "mock_ocr",
                "image_purpose": "learning_homework"
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

    @Test
    fun responseCanParseRealImageUploadMetadata() {
        val response = AttachmentCreateResponse.fromJsonString(
            """
            {
              "attachment_id": "att_real_001",
              "mime_type": "image/jpeg",
              "size_bytes": 1200,
              "recognized_content": {
                "type": "image_observation",
                "text": "图片里是一张测试图。",
                "confidence": 0.84,
                "provider_name": "mimo",
                "image_purpose": "share"
              },
              "reply": {
                "type": "agent_message",
                "text": "我看到这张图啦。你想让我陪你聊聊它，还是说说你想问哪里？",
                "voice_enabled": true,
                "emotion": "curious"
              },
              "ui_actions": [],
              "session_state": {
                "base_scene": "conversation.open",
                "active_scene": "conversation.open"
              }
            }
            """.trimIndent(),
        )

        assertEquals("att_real_001", response.attachmentId)
        assertEquals("image/jpeg", response.mimeType)
        assertEquals(1200, response.sizeBytes)
        assertEquals("mimo", response.recognizedContent.providerName)
    }

    @Test
    fun responseDoesNotTreatGenericImageAsHomework() {
        val response = AttachmentCreateResponse.fromJsonString(
            """
            {
              "attachment_id": "att_002",
              "recognized_content": {
                "type": "image_observation",
                "text": "孩子搭了一个积木城堡",
                "confidence": 0.9,
                "provider_name": "mock_ocr",
                "image_purpose": "share"
              },
              "reply": {
                "type": "agent_message",
                "text": "我看到你想分享的是：孩子搭了一个积木城堡。",
                "voice_enabled": true,
                "emotion": "curious"
              },
              "ui_actions": [],
              "session_state": {
                "base_scene": "conversation.open",
                "active_scene": "conversation.open"
              }
            }
            """.trimIndent(),
        )

        assertFalse(response.hasReadyHomeworkText)
        assertEquals("share", response.recognizedContent.imagePurpose)
    }

    @Test
    fun responseDoesNotAutoSendShareImageEvenWhenVisionTextLooksLikeHomework() {
        val response = AttachmentCreateResponse.fromJsonString(
            """
            {
              "attachment_id": "att_share_homework_like",
              "recognized_content": {
                "type": "homework_problem",
                "text": "图片里有一张纸，上面像是数学题目和一些数字。",
                "confidence": 0.93,
                "provider_name": "mimo",
                "image_purpose": "share"
              },
              "reply": {
                "type": "agent_message",
                "text": "我看到你想分享的是：图片里有一张纸，上面像是数学题目和一些数字。",
                "voice_enabled": true,
                "emotion": "curious"
              },
              "ui_actions": [],
              "session_state": {
                "base_scene": "conversation.open",
                "active_scene": "conversation.open"
              }
            }
            """.trimIndent(),
        )

        assertFalse(response.hasReadyHomeworkText)
        assertEquals("share", response.recognizedContent.imagePurpose)
    }

    @Test
    fun genericImageResponsePreservesCaptionForFollowupContext() {
        val response = AttachmentCreateResponse.fromJsonString(
            """
            {
              "attachment_id": "att_003",
              "recognized_content": {
                "type": "image_observation",
                "text": "孩子搭了一个积木城堡",
                "confidence": 0.9,
                "provider_name": "mock_ocr",
                "image_purpose": "share",
                "child_caption": "你看我搭的这个"
              },
              "reply": {
                "type": "agent_message",
                "text": "我看到你想分享的是：孩子搭了一个积木城堡。",
                "voice_enabled": true,
                "emotion": "curious"
              },
              "ui_actions": [],
              "session_state": {
                "base_scene": "conversation.open",
                "active_scene": "conversation.open"
              }
            }
            """.trimIndent(),
        )

        assertEquals("att_003", response.attachmentId)
        assertEquals("孩子搭了一个积木城堡", response.recognizedContent.text)
        assertEquals("你看我搭的这个", response.recognizedContent.childCaption)
        assertFalse(response.hasReadyHomeworkText)
    }
}
