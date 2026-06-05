package com.childai.companion.ui.chat.strangedoor

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class StrangeDoorHomeEventUiModelTest {
    @Test
    fun choosingMethodShowsApprovedTitleBubbleAndTwoButtons() {
        val model = StrangeDoorDemoSnapshot().toHomeEventUiModel()

        assertEquals("奇怪小门挡住了小白狐", model.title)
        assertEquals(StrangeDoorHomeEventPanel.SpeechBubble, model.panel)
        assertEquals(
            listOf(
                "你来得正好",
                "我被这扇奇怪小门挡住了",
                "它说：",
                "找一个圆圆的东西",
                "或者答对一个怪问题",
            ),
            model.bubbleLines,
        )
        assertEquals(
            listOf("找东西帮忙", "动脑试试"),
            model.actions.map { it.label },
        )
        assertEquals(StrangeDoorAssetKey.DoorClosed, model.doorAssetKey)
        assertFalse(model.showNormalInputBar)
    }

    @Test
    fun photoPromptUsesApprovedCopyWithoutStartingRealPhotoFlow() {
        val model = StrangeDoorDemoSnapshot(
            demoState = StrangeDoorDemoState.PhotoPrompt,
        ).toHomeEventUiModel()

        assertEquals(StrangeDoorHomeEventPanel.ToolCard, model.panel)
        assertEquals(
            listOf(
                "找一个有点圆的东西就行",
                "瓶盖、杯子、球、纽扣都可以",
                "奇怪一点也可以",
            ),
            model.bubbleLines,
        )
        assertEquals(
            listOf("拍给小白狐看", "先换个办法"),
            model.actions.map { it.label },
        )
        assertFalse(model.actions.first().enabled)
    }

    @Test
    fun riddlePromptUsesFixedQuestionAndSwitchActions() {
        val model = StrangeDoorDemoSnapshot(
            demoState = StrangeDoorDemoState.RiddlePrompt,
        ).toHomeEventUiModel()

        assertEquals(StrangeDoorHomeEventPanel.Riddle, model.panel)
        assertEquals("什么东西越洗越脏？", model.question)
        assertEquals(
            listOf("找东西帮忙", "先换个办法"),
            model.actions.map { it.label },
        )
    }

    @Test
    fun allRequiredAndroidResourcesResolveToDrawableIds() {
        assertTrue(StrangeDoorAndroidResources.allRequiredResourcesReady())
        StrangeDoorAssetContract.requiredAssets.forEach { key ->
            assertTrue(
                "${key.name} should resolve to a drawable resource",
                StrangeDoorAndroidResources.drawableResId(key) != 0,
            )
        }
    }
}
