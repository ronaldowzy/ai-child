package com.childai.companion.ui.chat.strangedoor

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class StrangeDoorPhotoTransformMapperTest {
    @Test
    fun roundObjectBecomesHighMatchDoorOpeningTransform() {
        val transform = StrangeDoorPhotoTransformMapper.map(
            StrangeDoorPhotoRecognition(
                recognizedType = "image_observation",
                recognizedText = "图片里有一个蓝色瓶盖",
                confidence = 0.91,
            ),
        )

        assertEquals("蓝色瓶盖", transform.objectName)
        assertEquals(StrangeDoorShapeHint.Round, transform.shapeHint)
        assertEquals("蓝盖盖转轮", transform.transformedName)
        assertEquals(StrangeDoorDoorAdvanceSignal.Open, transform.advanceSignal)
        assertTrue(transform.canSaveToShowcase)
        assertTrue(transform.isGoodMatch)
        assertEquals(
            listOf(
                "我看见了：蓝色瓶盖",
                "在小白狐的世界里",
                "它变成了：蓝盖盖转轮",
                "小白狐把它轻轻一转",
                "门上的圆锁咔哒一下松开了",
            ),
            StrangeDoorPhotoTransformMapper.feedbackLines(transform),
        )
    }

    @Test
    fun partialObjectAdvancesOneStepWithoutFailing() {
        val transform = StrangeDoorPhotoTransformMapper.map(
            StrangeDoorPhotoRecognition(
                recognizedType = "image_observation",
                recognizedText = "画面里有一支铅笔",
                confidence = 0.88,
            ),
        )

        assertEquals("一支铅笔", transform.objectName)
        assertEquals(StrangeDoorShapeHint.Partial, transform.shapeHint)
        assertEquals("直直敲门棒", transform.transformedName)
        assertEquals(StrangeDoorDoorAdvanceSignal.AdvanceOneStep, transform.advanceSignal)
        assertTrue(transform.isUsable)
        assertEquals(
            listOf(
                "我看见了：一支铅笔",
                "在小白狐的世界里",
                "它变成了：直直敲门棒",
                "小门被敲得愣了一下",
                "露出了一条小缝",
            ),
            StrangeDoorPhotoTransformMapper.feedbackLines(transform),
        )
    }

    @Test
    fun blankRecognitionUsesApprovedFallbackObjectName() {
        val transform = StrangeDoorPhotoTransformMapper.map(
            StrangeDoorPhotoRecognition(
                recognizedType = "image_observation",
                recognizedText = null,
                confidence = 0.66,
            ),
        )

        assertEquals("这个小东西", transform.objectName)
        assertEquals(StrangeDoorShapeHint.Unknown, transform.shapeHint)
        assertEquals("软软开门垫", transform.transformedName)
        assertEquals(StrangeDoorDoorAdvanceSignal.AdvanceOneStep, transform.advanceSignal)
    }

    @Test
    fun homeworkAndSensitiveImagesDoNotBecomeDoorTools() {
        listOf("homework_problem", "privacy_sensitive", "unsafe_unknown").forEach { type ->
            val transform = StrangeDoorPhotoTransformMapper.map(
                StrangeDoorPhotoRecognition(
                    recognizedType = type,
                    recognizedText = "图片里有一些文字",
                    confidence = 0.93,
                ),
            )

            assertEquals(StrangeDoorShapeHint.Blocked, transform.shapeHint)
            assertFalse(transform.isUsable)
            assertFalse(transform.canSaveToShowcase)
            assertEquals(StrangeDoorDoorAdvanceSignal.None, transform.advanceSignal)
            assertNull(transform.transformedName)
            assertEquals(
                listOf(
                    "这张图不太适合变成开门道具",
                    "我们换一个小东西试试",
                ),
                StrangeDoorPhotoTransformMapper.feedbackLines(transform),
            )
        }
    }
}
