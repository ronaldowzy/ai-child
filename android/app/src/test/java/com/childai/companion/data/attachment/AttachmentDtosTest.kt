package com.childai.companion.data.attachment

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.json.JSONObject
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
    fun requestCanSendCameraImageDataUriWithoutOriginalStorage() {
        val json = AttachmentCreateRequest(
            childId = "child_demo_001",
            sessionId = "session_001",
            imagePurpose = "share",
            imageDataUri = "data:image/jpeg;base64,ZmFrZV9pbWFnZQ==",
            childCaption = "我拍了一张图片给小白狐看。",
        ).toJsonString()

        assertTrue(json.contains("\"image_data_uri\":\"data:image/jpeg;base64,ZmFrZV9pbWFnZQ==\""))
        assertTrue(json.contains("\"source\":\"android_camera_capture\""))
        assertTrue(json.contains("\"stores_original_image\":false"))
        assertTrue(JSONObject(json).isNull("file_id"))
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
