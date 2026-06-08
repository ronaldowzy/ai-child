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
        assertTrue(model.showHomeIntroVisual)
        assertFalse(model.showPhotoResultCard)
        assertFalse(model.showDoorSuccessGlow)
    }

    @Test
    fun choosingMethodSwitchesDoorNeedForSoftAndShinyMechanisms() {
        val soft = StrangeDoorDemoSnapshot(
            mechanismType = StrangeDoorMechanismType.Soft,
        ).toHomeEventUiModel()
        val shiny = StrangeDoorDemoSnapshot(
            mechanismType = StrangeDoorMechanismType.Shiny,
        ).toHomeEventUiModel()

        assertEquals(
            listOf(
                "你来得正好",
                "我被这扇奇怪小门挡住了",
                "它说：",
                "找一个软软的东西",
                "或者答对一个怪问题",
            ),
            soft.bubbleLines,
        )
        assertEquals(
            listOf(
                "你来得正好",
                "我被这扇奇怪小门挡住了",
                "它说：",
                "找一个亮亮的东西",
                "或者答对一个怪问题",
            ),
            shiny.bubbleLines,
        )
    }

    @Test
    fun photoPromptUsesApprovedCopyAndEnabledPhotoEntry() {
        val model = StrangeDoorDemoSnapshot(
            demoState = StrangeDoorDemoState.PhotoPrompt,
        ).toHomeEventUiModel()

        assertEquals(StrangeDoorHomeEventPanel.ToolCard, model.panel)
        assertFalse(model.showHomeIntroVisual)
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
    fun photoPromptSwitchesPromptForSoftAndShinyMechanisms() {
        val soft = StrangeDoorDemoSnapshot(
            demoState = StrangeDoorDemoState.PhotoPrompt,
            mechanismType = StrangeDoorMechanismType.Soft,
        ).toHomeEventUiModel()
        val shiny = StrangeDoorDemoSnapshot(
            demoState = StrangeDoorDemoState.PhotoPrompt,
            mechanismType = StrangeDoorMechanismType.Shiny,
        ).toHomeEventUiModel()

        assertEquals(
            listOf(
                "找一个软软的东西就行",
                "毛巾、抱枕、布娃娃、纸巾都可以",
                "奇怪一点也可以",
            ),
            soft.bubbleLines,
        )
        assertEquals(
            listOf(
                "找一个有点亮的东西就行",
                "勺子、杯盖、小灯、亮亮的贴纸都可以",
                "奇怪一点也可以",
            ),
            shiny.bubbleLines,
        )
    }

    @Test
    fun photoResultShowsTransformFeedbackAndR1ActionOrder() {
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
        assertEquals(StrangeDoorAssetKey.DoorCracked, model.doorAssetKey)
        assertEquals(
            listOf(
                "我看见了：蓝色瓶盖",
                "在小白狐的世界里",
                "它变成了：蓝盖盖转轮",
                "小白狐把它轻轻一转",
                "门上的圆锁轻轻转了一小下",
            ),
            model.bubbleLines,
        )
        assertEquals(
            listOf("再找一个", "动脑试试", "放进小展台"),
            model.actions.map { it.label },
        )
        assertTrue(model.showPhotoResultCard)
        assertTrue(model.showDoorSuccessGlow)
        assertTrue(model.actions.first { it.id == StrangeDoorHomeEventActionId.SaveToShowcase }.enabled)
    }

    @Test
    fun photoResultAfterAlmostOpenUsesS3CompletedCopyAndActions() {
        val transform = StrangeDoorPhotoTransformMapper.map(
            StrangeDoorPhotoRecognition(
                recognizedType = "image_observation",
                recognizedText = "图片里有一个蓝色瓶盖",
                confidence = 0.92,
            ),
        )
        val snapshot = StrangeDoorDoorStateReducer.applyPhotoResult(
            snapshot = StrangeDoorDemoSnapshot(doorState = StrangeDoorState.AlmostOpen),
            transform = transform,
            photoMessageId = "child-photo-3",
        )
        val model = snapshot.toHomeEventUiModel()

        assertEquals(StrangeDoorAssetKey.DoorOpen, model.doorAssetKey)
        assertEquals(
            listOf(
                "开啦",
                "你真的帮到我了",
                "",
                "门后面有一点暖暖的风",
                "我们先看到这里",
            ),
            model.bubbleLines,
        )
        assertEquals(
            listOf("再玩一次", "再找一个", "去小展台看看", "先聊别的"),
            model.actions.map { it.label },
        )
        assertEquals(
            listOf(
                StrangeDoorHomeEventActionId.ReplayDemo,
                StrangeDoorHomeEventActionId.FindAnother,
                StrangeDoorHomeEventActionId.OpenShowcase,
                StrangeDoorHomeEventActionId.ExitDemo,
            ),
            model.actions.map { it.id },
        )
        assertFalse(model.showPhotoResultCard)
        assertFalse(model.showDoorSuccessGlow)
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
        assertFalse(model.showPhotoResultCard)
        assertFalse(model.showDoorSuccessGlow)
        assertFalse(model.actions.first { it.id == StrangeDoorHomeEventActionId.SaveToShowcase }.enabled)
    }

    @Test
    fun doorStateMapsToExpectedDoorAssetKey() {
        assertEquals(StrangeDoorAssetKey.DoorClosed, StrangeDoorState.Closed.toAssetKey())
        assertEquals(StrangeDoorAssetKey.DoorCracked, StrangeDoorState.Cracked.toAssetKey())
        assertEquals(StrangeDoorAssetKey.DoorAlmostOpen, StrangeDoorState.AlmostOpen.toAssetKey())
        assertEquals(StrangeDoorAssetKey.DoorOpen, StrangeDoorState.Open.toAssetKey())
    }

    @Test
    fun nonPhotoResultStatesDoNotShowPhotoGlow() {
        val choosing = StrangeDoorDemoSnapshot().toHomeEventUiModel()
        val photoPrompt = StrangeDoorDemoSnapshot(
            demoState = StrangeDoorDemoState.PhotoPrompt,
        ).toHomeEventUiModel()
        val riddleOpen = StrangeDoorDoorStateReducer.applyRiddleResult(
            snapshot = StrangeDoorDemoSnapshot(
                demoState = StrangeDoorDemoState.RiddlePrompt,
            ),
            evaluation = StrangeDoorRiddleEvaluator.evaluate("水"),
        ).toHomeEventUiModel()

        listOf(choosing, photoPrompt, riddleOpen).forEach { model ->
            assertFalse(model.showPhotoResultCard)
            assertFalse(model.showDoorSuccessGlow)
        }
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
    fun correctRiddleResultShowsS3CompletedCopyAndOpenDoor() {
        val snapshot = StrangeDoorDoorStateReducer.applyRiddleResult(
            snapshot = StrangeDoorDemoSnapshot(
                demoState = StrangeDoorDemoState.RiddlePrompt,
            ),
            evaluation = StrangeDoorRiddleEvaluator.evaluate("水"),
        )
        val model = snapshot.toHomeEventUiModel()

        assertEquals(StrangeDoorHomeEventPanel.ToolCard, model.panel)
        assertEquals(StrangeDoorAssetKey.DoorOpen, model.doorAssetKey)
        assertEquals(
            listOf(
                "开啦",
                "你真的帮到我了",
                "",
                "门后面有一点暖暖的风",
                "我们先看到这里",
            ),
            model.bubbleLines,
        )
        assertEquals(
            listOf("再玩一次", "再找一个", "去小展台看看", "先聊别的"),
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
            listOf("去小展台看看", "再找一个", "先聊别的"),
            model.actions.map { it.label },
        )
        assertEquals(
            listOf(
                StrangeDoorHomeEventActionId.OpenShowcase,
                StrangeDoorHomeEventActionId.FindAnother,
                StrangeDoorHomeEventActionId.ExitDemo,
            ),
            model.actions.map { it.id },
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
