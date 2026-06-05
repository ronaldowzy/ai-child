package com.childai.companion.ui.chat.strangedoor

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class StrangeDoorPhotoTransformMapperTest {
    @Test
    fun roundObjectBecomesHighMatchOneStepTransform() {
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
        assertEquals(StrangeDoorDoorAdvanceSignal.AdvanceOneStep, transform.advanceSignal)
        assertTrue(transform.canSaveToShowcase)
        assertTrue(transform.isGoodMatch)
        assertEquals(
            listOf(
                "我看见了：蓝色瓶盖",
                "在小白狐的世界里",
                "它变成了：蓝盖盖转轮",
                "小白狐把它轻轻一转",
                "门上的圆锁轻轻转了一小下",
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
                "门边露出一条小小的缝",
                "小门歪着想了想，好像有点相信",
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
        assertEquals("这个小东西", transform.transformedName)
        assertEquals(StrangeDoorDoorAdvanceSignal.AdvanceOneStep, transform.advanceSignal)
    }

    @Test
    fun openDoorStateUsesApprovedOpenFeedbackPool() {
        val transform = StrangeDoorPhotoTransformMapper.map(
            StrangeDoorPhotoRecognition(
                recognizedType = "image_observation",
                recognizedText = "图片里有一个蓝色瓶盖",
                confidence = 0.91,
            ),
        )

        assertEquals(
            listOf(
                "我看见了：蓝色瓶盖",
                "在小白狐的世界里",
                "它变成了：蓝盖盖转轮",
                "小白狐把它轻轻一转",
                "小门终于咔哒一下打开了",
                "门后面有一点暖暖的风",
                "小白狐轻轻走过去，看见了一点光",
            ),
            StrangeDoorPhotoTransformMapper.feedbackLines(transform, doorState = StrangeDoorState.Open),
        )
    }

    @Test
    fun r1CopyPoolIsIncludedInApprovedChildFacingCopy() {
        val requiredR1Copy = listOf(
            "小月亮盾牌",
            "蓝盖盖转轮",
            "咕噜圆盘",
            "圆滚滚按钮",
            "眨眼门铃",
            "杯口小旋风",
            "纽扣小眼睛",
            "圆圆开门盘",
            "小饼干转轮",
            "月亮小按钮",
            "半圆冲撞器",
            "直直敲门棒",
            "弯弯撬门勺",
            "纸角小铲子",
            "软软开门垫",
            "歪歪小推板",
            "瘦长敲敲杆",
            "小斜坡垫子",
            "这个小东西",
            "迷糊开门垫",
            "软软试试看",
            "小小帮忙块",
            "糊糊门铃",
            "门上的圆锁轻轻转了一小下",
            "门缝里冒出一点暖风",
            "小门被它逗得晃了一下",
            "门边露出一条小小的缝",
            "圆锁像打哈欠一样松了一点",
            "小白狐往后退了一小步，又凑过去看",
            "小门没有完全打开",
            "但是它打了个喷嚏，露出一条小缝",
            "小门歪着想了想，好像有点相信",
            "这个东西有点奇怪，小门看了好久",
            "小白狐说：也许可以试试",
            "小门终于咔哒一下打开了",
            "门后面有一点暖暖的风",
            "小白狐轻轻走过去，看见了一点光",
        )

        assertTrue(StrangeDoorPhotoTransformMapper.approvedChildFacingCopy().containsAll(requiredR1Copy))
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

    @Test
    fun forbiddenTextSignalsDoNotBecomeDoorTools() {
        listOf("图片里有一道作业题目", "画面里有学校地址", "图片里有人脸和证件").forEach { text ->
            val transform = StrangeDoorPhotoTransformMapper.map(
                StrangeDoorPhotoRecognition(
                    recognizedType = "image_observation",
                    recognizedText = text,
                    confidence = 0.93,
                ),
            )

            assertEquals(StrangeDoorShapeHint.Blocked, transform.shapeHint)
            assertFalse(transform.isUsable)
            assertFalse(transform.canSaveToShowcase)
            assertEquals(StrangeDoorDoorAdvanceSignal.None, transform.advanceSignal)
        }
    }
}
