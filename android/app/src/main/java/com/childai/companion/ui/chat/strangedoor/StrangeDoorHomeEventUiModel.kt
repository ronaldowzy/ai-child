package com.childai.companion.ui.chat.strangedoor

enum class StrangeDoorHomeEventActionId {
    ChoosePhoto,
    ChooseRiddle,
    OpenPhotoCapture,
    OpenShowcasePicker,
    SwitchMethod,
    FindAnother,
    SaveToShowcase,
    RetryRiddle,
    ReplayDemo,
    OpenShowcase,
    ExitDemo,
}

data class StrangeDoorHomeEventAction(
    val id: StrangeDoorHomeEventActionId,
    val label: String,
    val enabled: Boolean = true,
)

enum class StrangeDoorHomeEventPanel {
    SpeechBubble,
    ToolCard,
    Riddle,
}

data class StrangeDoorHomeEventUiModel(
    val title: String,
    val panel: StrangeDoorHomeEventPanel,
    val bubbleLines: List<String>,
    val question: String? = null,
    val actions: List<StrangeDoorHomeEventAction>,
    val doorAssetKey: StrangeDoorAssetKey,
    val showNormalInputBar: Boolean = false,
    val showRiddleVoiceControl: Boolean = false,
    val showPhotoResultCard: Boolean = false,
    val showDoorSuccessGlow: Boolean = false,
    val showHomeIntroVisual: Boolean = false,
)

object StrangeDoorHomeEventCopy {
    const val title = "奇怪小门挡住了小白狐"

    const val riddleQuestion = "什么东西越洗越脏？"
    const val choosePhotoLabel = "找东西帮忙"
    const val chooseRiddleLabel = "动脑试试"
    const val openPhotoCaptureLabel = "拍给小白狐看"
    const val openShowcasePickerLabel = "用小展台里的"
    const val switchMethodLabel = "先换个办法"
    const val replayDemoLabel = "再玩一次"
    const val findAnotherLabel = "再找一个"
    const val saveToShowcaseLabel = "放进小展台"
    const val openShowcaseLabel = "去小展台看看"
    const val exitDemoLabel = "先聊别的"
    const val showcaseSavedSuffix = "，放好啦"
    const val showcaseSavedSecondLine = "以后可以在小展台里看到它"
    val completedLines = listOf(
        "开啦",
        "你真的帮到我了",
        "",
        "门后面有一点暖暖的风",
        "我们先看到这里",
    )

    fun choosingBubbleLines(mechanismType: StrangeDoorMechanismType): List<String> {
        return listOf(
            "你来得正好",
            "我被这扇奇怪小门挡住了",
            "它说：",
            "找一个${mechanismType.doorNeedLabel()}的东西",
            "或者答对一个怪问题",
        )
    }

    fun photoPromptLines(mechanismType: StrangeDoorMechanismType): List<String> {
        return when (mechanismType) {
            StrangeDoorMechanismType.Round -> listOf(
                "找一个有点圆的东西就行",
                "瓶盖、杯子、球、纽扣都可以",
                "奇怪一点也可以",
            )
            StrangeDoorMechanismType.Soft -> listOf(
                "找一个软软的东西就行",
                "毛巾、抱枕、布娃娃、纸巾都可以",
                "奇怪一点也可以",
            )
            StrangeDoorMechanismType.Shiny -> listOf(
                "找一个有点亮的东西就行",
                "勺子、杯盖、小灯、亮亮的贴纸都可以",
                "奇怪一点也可以",
            )
        }
    }

    fun approvedChildFacingCopy(): List<String> {
        val mechanismCopy = StrangeDoorMechanismType.entries.flatMap { mechanismType ->
            choosingBubbleLines(mechanismType) + photoPromptLines(mechanismType)
        }
        return listOf(
            title,
            riddleQuestion,
            choosePhotoLabel,
            chooseRiddleLabel,
            openPhotoCaptureLabel,
            openShowcasePickerLabel,
            switchMethodLabel,
            replayDemoLabel,
            findAnotherLabel,
            saveToShowcaseLabel,
            openShowcaseLabel,
            exitDemoLabel,
            showcaseSavedSuffix,
            showcaseSavedSecondLine,
        ) + mechanismCopy + completedLines
    }

    private fun StrangeDoorMechanismType.doorNeedLabel(): String {
        return when (this) {
            StrangeDoorMechanismType.Round -> "圆圆"
            StrangeDoorMechanismType.Soft -> "软软"
            StrangeDoorMechanismType.Shiny -> "亮亮"
        }
    }
}

fun StrangeDoorDemoSnapshot.toHomeEventUiModel(): StrangeDoorHomeEventUiModel {
    return when (demoState) {
        StrangeDoorDemoState.Completed -> completedUiModel()
        StrangeDoorDemoState.PhotoResult -> resultUiModelOrChoosingMethod()
        StrangeDoorDemoState.ShowcaseItemResult -> showcaseItemResultUiModelOrChoosingMethod()
        StrangeDoorDemoState.ShowcaseSaved -> showcaseSavedUiModelOrChoosingMethod()

        StrangeDoorDemoState.PhotoPrompt,
        StrangeDoorDemoState.PhotoUploading -> StrangeDoorHomeEventUiModel(
            title = StrangeDoorHomeEventCopy.title,
            panel = StrangeDoorHomeEventPanel.ToolCard,
            bubbleLines = StrangeDoorHomeEventCopy.photoPromptLines(mechanismType),
            actions = listOf(
                StrangeDoorHomeEventAction(
                    id = StrangeDoorHomeEventActionId.OpenPhotoCapture,
                    label = StrangeDoorHomeEventCopy.openPhotoCaptureLabel,
                    enabled = demoState != StrangeDoorDemoState.PhotoUploading,
                ),
                StrangeDoorHomeEventAction(
                    id = StrangeDoorHomeEventActionId.OpenShowcasePicker,
                    label = StrangeDoorHomeEventCopy.openShowcasePickerLabel,
                    enabled = demoState != StrangeDoorDemoState.PhotoUploading,
                ),
                StrangeDoorHomeEventAction(
                    id = StrangeDoorHomeEventActionId.SwitchMethod,
                    label = StrangeDoorHomeEventCopy.switchMethodLabel,
                ),
            ),
            doorAssetKey = doorState.toAssetKey(),
        )

        StrangeDoorDemoState.RiddlePrompt,
        StrangeDoorDemoState.RiddleHint -> if (demoState == StrangeDoorDemoState.RiddleHint) {
            val evaluation = lastRiddleEvaluation ?: StrangeDoorRiddleEvaluator.evaluate("")
            StrangeDoorHomeEventUiModel(
                title = StrangeDoorHomeEventCopy.title,
                panel = StrangeDoorHomeEventPanel.Riddle,
                bubbleLines = evaluation.feedbackLines,
                actions = listOf(
                    StrangeDoorHomeEventAction(
                        id = StrangeDoorHomeEventActionId.RetryRiddle,
                        label = StrangeDoorRiddleEvaluator.ACTION_RETRY,
                    ),
                    StrangeDoorHomeEventAction(
                        id = StrangeDoorHomeEventActionId.ChoosePhoto,
                        label = StrangeDoorRiddleEvaluator.ACTION_PHOTO,
                    ),
                ),
                doorAssetKey = doorState.toAssetKey(),
            )
        } else {
            StrangeDoorHomeEventUiModel(
                title = StrangeDoorHomeEventCopy.title,
                panel = StrangeDoorHomeEventPanel.Riddle,
                bubbleLines = emptyList(),
                question = StrangeDoorHomeEventCopy.riddleQuestion,
                actions = listOf(
                    StrangeDoorHomeEventAction(
                        id = StrangeDoorHomeEventActionId.ChoosePhoto,
                        label = StrangeDoorHomeEventCopy.choosePhotoLabel,
                    ),
                    StrangeDoorHomeEventAction(
                        id = StrangeDoorHomeEventActionId.SwitchMethod,
                        label = StrangeDoorHomeEventCopy.switchMethodLabel,
                    ),
                ),
                doorAssetKey = doorState.toAssetKey(),
                showRiddleVoiceControl = true,
            )
        }

        StrangeDoorDemoState.NotStarted,
        StrangeDoorDemoState.ChoosingMethod -> choosingMethodUiModel()
    }
}

private fun StrangeDoorDemoSnapshot.showcaseItemResultUiModelOrChoosingMethod(): StrangeDoorHomeEventUiModel {
    val result = lastShowcaseAssistResult ?: return choosingMethodUiModel()
    return StrangeDoorHomeEventUiModel(
        title = StrangeDoorHomeEventCopy.title,
        panel = StrangeDoorHomeEventPanel.ToolCard,
        bubbleLines = StrangeDoorShowcaseAssistMapper.feedbackLines(result),
        actions = listOf(
            StrangeDoorHomeEventAction(
                id = StrangeDoorHomeEventActionId.FindAnother,
                label = StrangeDoorHomeEventCopy.findAnotherLabel,
            ),
            StrangeDoorHomeEventAction(
                id = StrangeDoorHomeEventActionId.ChooseRiddle,
                label = StrangeDoorHomeEventCopy.chooseRiddleLabel,
            ),
        ),
        doorAssetKey = doorState.toAssetKey(),
        showDoorSuccessGlow = doorState != StrangeDoorState.Closed,
    )
}

private fun StrangeDoorDemoSnapshot.showcaseSavedUiModelOrChoosingMethod(): StrangeDoorHomeEventUiModel {
    val savedName = showcaseSavedName?.takeIf { it.isNotBlank() } ?: return resultUiModelOrChoosingMethod()
    return StrangeDoorHomeEventUiModel(
        title = StrangeDoorHomeEventCopy.title,
        panel = StrangeDoorHomeEventPanel.ToolCard,
        bubbleLines = listOf(
            savedName + StrangeDoorHomeEventCopy.showcaseSavedSuffix,
            StrangeDoorHomeEventCopy.showcaseSavedSecondLine,
        ),
        actions = listOf(
            StrangeDoorHomeEventAction(
                id = StrangeDoorHomeEventActionId.OpenShowcase,
                label = StrangeDoorHomeEventCopy.openShowcaseLabel,
            ),
            StrangeDoorHomeEventAction(
                id = StrangeDoorHomeEventActionId.FindAnother,
                label = StrangeDoorHomeEventCopy.findAnotherLabel,
            ),
            StrangeDoorHomeEventAction(
                id = StrangeDoorHomeEventActionId.ExitDemo,
                label = StrangeDoorHomeEventCopy.exitDemoLabel,
            ),
        ),
        doorAssetKey = doorState.toAssetKey(),
    )
}

private fun StrangeDoorDemoSnapshot.completedUiModel(): StrangeDoorHomeEventUiModel {
    return StrangeDoorHomeEventUiModel(
        title = StrangeDoorHomeEventCopy.title,
        panel = StrangeDoorHomeEventPanel.ToolCard,
        bubbleLines = StrangeDoorHomeEventCopy.completedLines,
        actions = listOf(
            StrangeDoorHomeEventAction(
                id = StrangeDoorHomeEventActionId.ReplayDemo,
                label = StrangeDoorHomeEventCopy.replayDemoLabel,
            ),
            StrangeDoorHomeEventAction(
                id = StrangeDoorHomeEventActionId.FindAnother,
                label = StrangeDoorHomeEventCopy.findAnotherLabel,
            ),
            StrangeDoorHomeEventAction(
                id = StrangeDoorHomeEventActionId.OpenShowcase,
                label = StrangeDoorHomeEventCopy.openShowcaseLabel,
            ),
            StrangeDoorHomeEventAction(
                id = StrangeDoorHomeEventActionId.ExitDemo,
                label = StrangeDoorHomeEventCopy.exitDemoLabel,
            ),
        ),
        doorAssetKey = StrangeDoorState.Open.toAssetKey(),
    )
}

private fun StrangeDoorDemoSnapshot.resultUiModelOrChoosingMethod(): StrangeDoorHomeEventUiModel {
    lastPhotoTransform?.let { transform ->
        val actions = mutableListOf(
            StrangeDoorHomeEventAction(
                id = StrangeDoorHomeEventActionId.FindAnother,
                label = StrangeDoorHomeEventCopy.findAnotherLabel,
            ),
            StrangeDoorHomeEventAction(
                id = StrangeDoorHomeEventActionId.ChooseRiddle,
                label = StrangeDoorHomeEventCopy.chooseRiddleLabel,
            ),
        )
        if (transform.canSaveToShowcase) {
            actions += StrangeDoorHomeEventAction(
                id = StrangeDoorHomeEventActionId.SaveToShowcase,
                label = StrangeDoorHomeEventCopy.saveToShowcaseLabel,
                enabled = !showcaseSaveIntentRequested,
            )
        }
        return StrangeDoorHomeEventUiModel(
            title = StrangeDoorHomeEventCopy.title,
            panel = StrangeDoorHomeEventPanel.ToolCard,
            bubbleLines = StrangeDoorPhotoTransformMapper.feedbackLines(transform, doorState = doorState),
            actions = actions,
            doorAssetKey = doorState.toAssetKey(),
            showPhotoResultCard = transform.isUsable,
            showDoorSuccessGlow = transform.isUsable && doorState != StrangeDoorState.Closed,
        )
    }
    lastRiddleEvaluation?.let { evaluation ->
        return StrangeDoorHomeEventUiModel(
            title = StrangeDoorHomeEventCopy.title,
            panel = StrangeDoorHomeEventPanel.Riddle,
            bubbleLines = evaluation.feedbackLines,
            actions = listOf(
                StrangeDoorHomeEventAction(
                    id = StrangeDoorHomeEventActionId.FindAnother,
                    label = StrangeDoorHomeEventCopy.findAnotherLabel,
                ),
                StrangeDoorHomeEventAction(
                    id = StrangeDoorHomeEventActionId.ExitDemo,
                    label = StrangeDoorHomeEventCopy.exitDemoLabel,
                ),
            ),
            doorAssetKey = doorState.toAssetKey(),
        )
    }
    return choosingMethodUiModel()
}

private fun StrangeDoorDemoSnapshot.choosingMethodUiModel(): StrangeDoorHomeEventUiModel {
    return StrangeDoorHomeEventUiModel(
        title = StrangeDoorHomeEventCopy.title,
        panel = StrangeDoorHomeEventPanel.SpeechBubble,
        bubbleLines = StrangeDoorHomeEventCopy.choosingBubbleLines(mechanismType),
        actions = listOf(
            StrangeDoorHomeEventAction(
                id = StrangeDoorHomeEventActionId.ChoosePhoto,
                label = StrangeDoorHomeEventCopy.choosePhotoLabel,
            ),
            StrangeDoorHomeEventAction(
                id = StrangeDoorHomeEventActionId.ChooseRiddle,
                label = StrangeDoorHomeEventCopy.chooseRiddleLabel,
            ),
        ),
        doorAssetKey = doorState.toAssetKey(),
        showHomeIntroVisual = true,
    )
}

fun StrangeDoorState.toAssetKey(): StrangeDoorAssetKey {
    return when (this) {
        StrangeDoorState.Closed -> StrangeDoorAssetKey.DoorClosed
        StrangeDoorState.Cracked -> StrangeDoorAssetKey.DoorCracked
        StrangeDoorState.AlmostOpen -> StrangeDoorAssetKey.DoorAlmostOpen
        StrangeDoorState.Open -> StrangeDoorAssetKey.DoorOpen
    }
}
