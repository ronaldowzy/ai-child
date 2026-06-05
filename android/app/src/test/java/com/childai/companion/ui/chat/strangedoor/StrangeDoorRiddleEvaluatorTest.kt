package com.childai.companion.ui.chat.strangedoor

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class StrangeDoorRiddleEvaluatorTest {
    @Test
    fun waterAnswerOpensDoor() {
        val result = StrangeDoorRiddleEvaluator.evaluate("我觉得是水呀")

        assertTrue(result.isCorrect)
        assertEquals(StrangeDoorDemoState.Completed, result.nextDemoState)
        assertEquals(StrangeDoorDoorAdvanceSignal.Open, result.advanceSignal)
        assertEquals(
            listOf(
                "对，是水",
                "",
                "小门被你说得愣住了",
                "它低头想了三秒",
                "然后咔哒一下打开了",
            ),
            result.feedbackLines,
        )
    }

    @Test
    fun wrongAnswerReturnsHintWithoutDoorAdvance() {
        val result = StrangeDoorRiddleEvaluator.evaluate("毛巾")

        assertFalse(result.isCorrect)
        assertEquals(StrangeDoorDemoState.RiddleHint, result.nextDemoState)
        assertEquals(StrangeDoorDoorAdvanceSignal.None, result.advanceSignal)
        assertEquals(listOf("再答一次", "找东西帮忙"), result.actionLabels)
        assertEquals(
            listOf(
                "这个答案有点勇敢",
                "小门差点相信了",
                "",
                "我给你一个提示",
                "它常常在杯子里、河里、盆里",
            ),
            result.feedbackLines,
        )
    }

    @Test
    fun riddleResultUpdatesSnapshot() {
        val result = StrangeDoorRiddleEvaluator.evaluate("水")

        val next = StrangeDoorDoorStateReducer.applyRiddleResult(
            snapshot = StrangeDoorDemoSnapshot(
                demoState = StrangeDoorDemoState.RiddlePrompt,
            ),
            evaluation = result,
        )

        assertEquals(StrangeDoorDemoState.Completed, next.demoState)
        assertEquals(StrangeDoorState.Open, next.doorState)
        assertEquals(1, next.riddleAttempts)
        assertEquals(StrangeDoorDemoMethod.Riddle, next.lastMethod)
    }
}
