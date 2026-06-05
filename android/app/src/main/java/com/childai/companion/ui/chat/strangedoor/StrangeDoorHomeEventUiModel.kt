package com.childai.companion.ui.chat.strangedoor

enum class StrangeDoorHomeEventActionId {
    ChoosePhoto,
    ChooseRiddle,
    OpenPhotoCapture,
    SwitchMethod,
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
)

object StrangeDoorHomeEventCopy {
    const val title = "奇怪小门挡住了小白狐"

    val choosingBubbleLines = listOf(
        "你来得正好",
        "我被这扇奇怪小门挡住了",
        "它说：",
        "找一个圆圆的东西",
        "或者答对一个怪问题",
    )

    val photoPromptLines = listOf(
        "找一个有点圆的东西就行",
        "瓶盖、杯子、球、纽扣都可以",
        "奇怪一点也可以",
    )

    const val riddleQuestion = "什么东西越洗越脏？"
    const val choosePhotoLabel = "找东西帮忙"
    const val chooseRiddleLabel = "动脑试试"
    const val openPhotoCaptureLabel = "拍给小白狐看"
    const val switchMethodLabel = "先换个办法"

    fun approvedChildFacingCopy(): List<String> {
        return listOf(
            title,
            riddleQuestion,
            choosePhotoLabel,
            chooseRiddleLabel,
            openPhotoCaptureLabel,
            switchMethodLabel,
        ) + choosingBubbleLines + photoPromptLines
    }
}

fun StrangeDoorDemoSnapshot.toHomeEventUiModel(): StrangeDoorHomeEventUiModel {
    return when (demoState) {
        StrangeDoorDemoState.PhotoPrompt,
        StrangeDoorDemoState.PhotoUploading,
        StrangeDoorDemoState.PhotoResult -> StrangeDoorHomeEventUiModel(
            title = StrangeDoorHomeEventCopy.title,
            panel = StrangeDoorHomeEventPanel.ToolCard,
            bubbleLines = StrangeDoorHomeEventCopy.photoPromptLines,
            actions = listOf(
                StrangeDoorHomeEventAction(
                    id = StrangeDoorHomeEventActionId.OpenPhotoCapture,
                    label = StrangeDoorHomeEventCopy.openPhotoCaptureLabel,
                    enabled = false,
                ),
                StrangeDoorHomeEventAction(
                    id = StrangeDoorHomeEventActionId.SwitchMethod,
                    label = StrangeDoorHomeEventCopy.switchMethodLabel,
                ),
            ),
            doorAssetKey = doorState.toAssetKey(),
        )

        StrangeDoorDemoState.RiddlePrompt,
        StrangeDoorDemoState.RiddleHint -> StrangeDoorHomeEventUiModel(
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
        )

        StrangeDoorDemoState.NotStarted,
        StrangeDoorDemoState.ChoosingMethod,
        StrangeDoorDemoState.Completed -> StrangeDoorHomeEventUiModel(
            title = StrangeDoorHomeEventCopy.title,
            panel = StrangeDoorHomeEventPanel.SpeechBubble,
            bubbleLines = StrangeDoorHomeEventCopy.choosingBubbleLines,
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
        )
    }
}

fun StrangeDoorState.toAssetKey(): StrangeDoorAssetKey {
    return when (this) {
        StrangeDoorState.Closed -> StrangeDoorAssetKey.DoorClosed
        StrangeDoorState.Cracked -> StrangeDoorAssetKey.DoorCracked
        StrangeDoorState.AlmostOpen -> StrangeDoorAssetKey.DoorAlmostOpen
        StrangeDoorState.Open -> StrangeDoorAssetKey.DoorOpen
    }
}
