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
    fun photoPromptUsesApprovedCopyAndEnabledPhotoEntry() {
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
        assertTrue(model.actions.first().enabled)
        assertEquals(StrangeDoorHomeEventActionId.OpenPhotoCapture, model.actions.first().id)
    }

    @Test
    fun photoResultShowsTransformFeedbackAndD3Actions() {
        val transform = StrangeDoorPhotoTransformMapper.map(
            StrangeDoorPhotoRecognition(
                recognizedType = "image_observation",
                recognizedText = "图片里有一个蓝色瓶盖",
                confidence = 0.92,
            ),
        )
        val snapshot = StrangeDoorDoorStateReducer.applyPhotoResult(
            snapshot = StrangeDoorDemoSnapshot(),
            transform = transform,
            photoMessageId = "child-photo-1",
        )
        val model = snapshot.toHomeEventUiModel()

        assertEquals(StrangeDoorHomeEventPanel.ToolCard, model.panel)
        assertEquals(StrangeDoorAssetKey.DoorOpen, model.doorAssetKey)
        assertEquals(
            listOf(
                "我看见了：蓝色瓶盖",
                "在小白狐的世界里",
                "它变成了：蓝盖盖转轮",
                "小白狐把它轻轻一转",
                "门上的圆锁咔哒一下松开了",
            ),
            model.bubbleLines,
        )
        assertEquals(
            listOf("再找一个", "放进小展台", "动脑试试"),
            model.actions.map { it.label },
        )
        assertTrue(model.actions.first { it.id == StrangeDoorHomeEventActionId.SaveToShowcase }.enabled)
    }

    @Test
    fun blockedPhotoResultKeepsSaveActionDisabled() {
        val transform = StrangeDoorPhotoTransformMapper.map(
            StrangeDoorPhotoRecognition(
                recognizedType = "privacy_sensitive",
                recognizedText = "图片里有学校地址",
                confidence = 0.92,
            ),
        )
        val snapshot = StrangeDoorDoorStateReducer.applyPhotoResult(
            snapshot = StrangeDoorDemoSnapshot(),
            transform = transform,
            photoMessageId = "child-photo-1",
        )
        val model = snapshot.toHomeEventUiModel()

        assertEquals(
            listOf(
                "这张图不太适合变成开门道具",
                "我们换一个小东西试试",
            ),
            model.bubbleLines,
        )
        assertFalse(model.actions.first { it.id == StrangeDoorHomeEventActionId.SaveToShowcase }.enabled)
    }

    @Test
    fun riddlePromptUsesFixedQuestionAndSwitchActions() {
        val model = StrangeDoorDemoSnapshot(
            demoState = StrangeDoorDemoState.RiddlePrompt,
        ).toHomeEventUiModel()

        assertEquals(StrangeDoorHomeEventPanel.Riddle, model.panel)
        assertEquals("什么东西越洗越脏？", model.question)
        assertTrue(model.showRiddleVoiceControl)
        assertEquals(
            listOf("找东西帮忙", "先换个办法"),
            model.actions.map { it.label },
        )
    }

    @Test
    fun wrongRiddleResultShowsHintAndD4Actions() {
        val snapshot = StrangeDoorDoorStateReducer.applyRiddleResult(
            snapshot = StrangeDoorDemoSnapshot(
                demoState = StrangeDoorDemoState.RiddlePrompt,
            ),
            evaluation = StrangeDoorRiddleEvaluator.evaluate("毛巾"),
        )
        val model = snapshot.toHomeEventUiModel()

        assertEquals(StrangeDoorHomeEventPanel.Riddle, model.panel)
        assertFalse(model.showRiddleVoiceControl)
        assertEquals(
            listOf(
                "这个答案有点勇敢",
                "小门差点相信了",
                "",
                "我给你一个提示",
                "它常常在杯子里、河里、盆里",
            ),
            model.bubbleLines,
        )
        assertEquals(
            listOf("再答一次", "找东西帮忙"),
            model.actions.map { it.label },
        )
        assertEquals(
            listOf(
                StrangeDoorHomeEventActionId.RetryRiddle,
                StrangeDoorHomeEventActionId.ChoosePhoto,
            ),
            model.actions.map { it.id },
        )
    }

    @Test
    fun correctRiddleResultShowsFeedbackAndOpenDoor() {
        val snapshot = StrangeDoorDoorStateReducer.applyRiddleResult(
            snapshot = StrangeDoorDemoSnapshot(
                demoState = StrangeDoorDemoState.RiddlePrompt,
            ),
            evaluation = StrangeDoorRiddleEvaluator.evaluate("水"),
        )
        val model = snapshot.toHomeEventUiModel()

        assertEquals(StrangeDoorHomeEventPanel.Riddle, model.panel)
        assertEquals(StrangeDoorAssetKey.DoorOpen, model.doorAssetKey)
        assertEquals(
            listOf(
                "对，是水",
                "",
                "小门被你说得愣住了",
                "它低头想了三秒",
                "然后咔哒一下打开了",
            ),
            model.bubbleLines,
        )
        assertEquals(
            listOf("再找一个", "先聊别的"),
            model.actions.map { it.label },
        )
    }

    @Test
    fun showcaseSavedStateUsesApprovedCompletionCopy() {
        val model = StrangeDoorDemoSnapshot(
            demoState = StrangeDoorDemoState.ShowcaseSaved,
            showcaseSavedName = "蓝盖盖转轮",
        ).toHomeEventUiModel()

        assertEquals(StrangeDoorHomeEventPanel.ToolCard, model.panel)
        assertEquals(
            listOf(
                "蓝盖盖转轮，放好啦",
                "以后可以在小展台里看到它",
            ),
            model.bubbleLines,
        )
        assertEquals(
            listOf("再找一个", "动脑试试", "先聊别的"),
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
