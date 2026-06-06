package com.childai.companion.ui.chat.strangedoor

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class StrangeDoorStateContractTest {
    @Test
    fun doorReducerAdvancesOneStepAtATime() {
        assertEquals(
            StrangeDoorState.Cracked,
            StrangeDoorDoorStateReducer.nextDoorState(
                current = StrangeDoorState.Closed,
                signal = StrangeDoorDoorAdvanceSignal.AdvanceOneStep,
            ),
        )
        assertEquals(
            StrangeDoorState.AlmostOpen,
            StrangeDoorDoorStateReducer.nextDoorState(
                current = StrangeDoorState.Cracked,
                signal = StrangeDoorDoorAdvanceSignal.AdvanceOneStep,
            ),
        )
        assertEquals(
            StrangeDoorState.Open,
            StrangeDoorDoorStateReducer.nextDoorState(
                current = StrangeDoorState.AlmostOpen,
                signal = StrangeDoorDoorAdvanceSignal.AdvanceOneStep,
            ),
        )
    }

    @Test
    fun doorReducerKeepsBlockedInputFromAdvancing() {
        assertEquals(
            StrangeDoorState.Cracked,
            StrangeDoorDoorStateReducer.nextDoorState(
                current = StrangeDoorState.Cracked,
                signal = StrangeDoorDoorAdvanceSignal.None,
            ),
        )
    }

    @Test
    fun doorReducerOpensForExplicitOpenSignal() {
        assertEquals(
            StrangeDoorState.Open,
            StrangeDoorDoorStateReducer.nextDoorState(
                current = StrangeDoorState.Closed,
                signal = StrangeDoorDoorAdvanceSignal.Open,
            ),
        )
    }

    @Test
    fun roundPhotoResultAdvancesFromClosedToCrackedOnly() {
        val transform = StrangeDoorPhotoTransformMapper.map(
            StrangeDoorPhotoRecognition(
                recognizedType = "image_observation",
                recognizedText = "图片里有一个蓝色瓶盖",
                confidence = 0.92,
            ),
        )

        assertEquals(StrangeDoorDoorAdvanceSignal.AdvanceOneStep, transform.advanceSignal)
        val next = StrangeDoorDoorStateReducer.applyPhotoResult(
            snapshot = StrangeDoorDemoSnapshot(),
            transform = transform,
            photoMessageId = "child-photo-1",
        )

        assertFalse(next.isCompleted)
        assertEquals(StrangeDoorDemoState.PhotoResult, next.demoState)
        assertEquals(StrangeDoorState.Cracked, next.doorState)
        assertEquals(1, next.attemptsCount)
        assertEquals(StrangeDoorDemoMethod.Photo, next.lastMethod)
        assertEquals("蓝色瓶盖", next.lastObjectName)
        assertEquals("蓝盖盖转轮", next.lastTransformedName)
        assertEquals("child-photo-1", next.lastPhotoMessageId)
    }

    @Test
    fun repeatedValidPhotosAdvanceToAlmostOpenThenOpen() {
        val transform = StrangeDoorPhotoTransformMapper.map(
            StrangeDoorPhotoRecognition(
                recognizedType = "image_observation",
                recognizedText = "图片里有一个蓝色瓶盖",
                confidence = 0.92,
            ),
        )

        val first = StrangeDoorDoorStateReducer.applyPhotoResult(
            snapshot = StrangeDoorDemoSnapshot(),
            transform = transform,
            photoMessageId = "child-photo-1",
        )
        val second = StrangeDoorDoorStateReducer.applyPhotoResult(
            snapshot = first,
            transform = transform,
            photoMessageId = "child-photo-2",
        )
        val third = StrangeDoorDoorStateReducer.applyPhotoResult(
            snapshot = second,
            transform = transform,
            photoMessageId = "child-photo-3",
        )

        assertEquals(StrangeDoorState.Cracked, first.doorState)
        assertEquals(StrangeDoorDemoState.PhotoResult, first.demoState)
        assertEquals(StrangeDoorState.AlmostOpen, second.doorState)
        assertEquals(StrangeDoorDemoState.PhotoResult, second.demoState)
        assertEquals(StrangeDoorState.Open, third.doorState)
        assertEquals(StrangeDoorDemoState.Completed, third.demoState)
        assertTrue(third.isCompleted)
    }

    @Test
    fun resetReturnsDefaultLocalDemoState() {
        val reset = StrangeDoorDoorStateReducer.reset()

        assertFalse(reset.isCompleted)
        assertEquals(StrangeDoorDemoState.ChoosingMethod, reset.demoState)
        assertEquals(StrangeDoorState.Closed, reset.doorState)
        assertEquals(0, reset.attemptsCount)
    }

    @Test
    fun requestAnotherPhotoKeepsNonOpenDoorState() {
        val snapshot = StrangeDoorDemoSnapshot(
            demoState = StrangeDoorDemoState.PhotoResult,
            doorState = StrangeDoorState.AlmostOpen,
            attemptsCount = 2,
        )

        val next = StrangeDoorDoorStateReducer.requestAnotherPhoto(snapshot)

        assertEquals(StrangeDoorDemoState.PhotoPrompt, next.demoState)
        assertEquals(StrangeDoorState.AlmostOpen, next.doorState)
        assertEquals(2, next.attemptsCount)
        assertEquals(StrangeDoorDemoMethod.Photo, next.lastMethod)
    }

    @Test
    fun requestAnotherPhotoAfterOpenRestartsFromClosed() {
        val snapshot = StrangeDoorDemoSnapshot(
            demoState = StrangeDoorDemoState.Completed,
            doorState = StrangeDoorState.Open,
            attemptsCount = 3,
            lastPhotoMessageId = "child-photo-3",
        )

        val next = StrangeDoorDoorStateReducer.requestAnotherPhoto(snapshot)

        assertEquals(StrangeDoorDemoState.PhotoPrompt, next.demoState)
        assertEquals(StrangeDoorState.Closed, next.doorState)
        assertEquals(0, next.attemptsCount)
        assertEquals(StrangeDoorDemoMethod.Photo, next.lastMethod)
        assertEquals(null, next.lastPhotoMessageId)
    }
}
