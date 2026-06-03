package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.CompanionObjectMeta

internal data class HouseObjectDebugOption(
    val id: String,
    val label: String,
)

internal val houseObjectDebugVisualKinds = listOf(
    HouseObjectDebugOption("star", "星星"),
    HouseObjectDebugOption("cloud", "云朵"),
    HouseObjectDebugOption("paper_boat", "纸船"),
    HouseObjectDebugOption("tiny_door", "小门"),
    HouseObjectDebugOption("dino_shadow", "恐龙影子"),
    HouseObjectDebugOption("block_light", "积木光"),
)

internal val houseObjectDebugStates = listOf(
    HouseObjectDebugOption("seed", "seed"),
    HouseObjectDebugOption("co_create", "co_create"),
    HouseObjectDebugOption("recall", "recall"),
    HouseObjectDebugOption("none", "none"),
)

internal val houseObjectDebugLocations = listOf(
    HouseObjectDebugOption("窗边", "窗边"),
    HouseObjectDebugOption("地毯边", "地毯边"),
    HouseObjectDebugOption("小白狐旁边", "小白狐旁边"),
    HouseObjectDebugOption("窗外", "窗外"),
)

internal fun houseObjectDebugBuildPreviewMeta(
    visualKind: String,
    state: String,
    lightLocation: String,
): CompanionObjectMeta? {
    val stateAction = houseObjectDebugStateAction(state) ?: return null
    return CompanionObjectMeta(
        id = "debug-preview-$visualKind-$state-$lightLocation",
        name = "调试小客人",
        objectType = houseObjectDebugObjectType(visualKind),
        lightLocation = lightLocation,
        state = stateAction.first,
        action = stateAction.second,
        visualKind = visualKind,
    )
}

internal fun houseObjectDebugStateAction(state: String): Pair<String, String>? {
    return when (state) {
        "seed" -> "seed" to "name_seed"
        "co_create" -> "active" to "co_create"
        "recall" -> "active" to "recall"
        "none" -> null
        else -> null
    }
}

internal fun houseObjectDebugObjectType(visualKind: String): String {
    return when (visualKind) {
        "star" -> "star"
        "cloud" -> "cloud"
        "paper_boat" -> "paper_boat"
        "tiny_door" -> "story_gate"
        "dino_shadow" -> "drawing_character"
        "block_light" -> "block_monster"
        else -> "star"
    }
}

internal fun houseObjectDebugCanPersist(state: String): Boolean {
    return state in setOf("seed", "co_create", "recall")
}

internal fun houseObjectDebugToolsVisible(
    debugBuild: Boolean,
    devSettingEnabled: Boolean,
): Boolean = debugBuild && devSettingEnabled
