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
    fun doorReducerOpensForHighMatchInput() {
        assertEquals(
            StrangeDoorState.Open,
            StrangeDoorDoorStateReducer.nextDoorState(
                current = StrangeDoorState.Closed,
                signal = StrangeDoorDoorAdvanceSignal.Open,
            ),
        )
    }

    @Test
    fun photoResultUpdatesSnapshotWithoutPersistingProgressContract() {
        val transform = StrangeDoorPhotoTransformMapper.map(
            StrangeDoorPhotoRecognition(
                recognizedType = "image_observation",
                recognizedText = "图片里有一个蓝色瓶盖",
                confidence = 0.92,
            ),
        )

        val next = StrangeDoorDoorStateReducer.applyPhotoResult(
            snapshot = StrangeDoorDemoSnapshot(),
            transform = transform,
            photoMessageId = "child-photo-1",
        )

        assertTrue(next.isCompleted)
        assertEquals(StrangeDoorDemoState.Completed, next.demoState)
        assertEquals(StrangeDoorState.Open, next.doorState)
        assertEquals(1, next.attemptsCount)
        assertEquals(StrangeDoorDemoMethod.Photo, next.lastMethod)
        assertEquals("蓝色瓶盖", next.lastObjectName)
        assertEquals("蓝盖盖转轮", next.lastTransformedName)
        assertEquals("child-photo-1", next.lastPhotoMessageId)
    }

    @Test
    fun resetReturnsDefaultLocalDemoState() {
        val reset = StrangeDoorDoorStateReducer.reset()

        assertFalse(reset.isCompleted)
        assertEquals(StrangeDoorDemoState.ChoosingMethod, reset.demoState)
        assertEquals(StrangeDoorState.Closed, reset.doorState)
        assertEquals(0, reset.attemptsCount)
    }
}
