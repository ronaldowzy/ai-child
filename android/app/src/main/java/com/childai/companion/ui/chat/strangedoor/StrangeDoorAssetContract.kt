package com.childai.companion.ui.chat.strangedoor

enum class StrangeDoorAssetKey(
    val fileName: String,
    val widthPx: Int,
    val heightPx: Int,
) {
    DoorClosed("strange_door_closed.webp", 1024, 1024),
    DoorCracked("strange_door_cracked.webp", 1024, 1024),
    DoorAlmostOpen("strange_door_almost_open.webp", 1024, 1024),
    DoorOpen("strange_door_open.webp", 1024, 1024),
    RoundLock("strange_door_round_lock.webp", 512, 512),
    TransformGlow("strange_door_transform_glow.webp", 512, 512),
    DoorSuccessGlow("strange_door_success_glow.webp", 512, 512),
    RiddlePanel("strange_door_riddle_panel.webp", 1024, 512),
    ToolCardPanel("strange_door_tool_card_panel.webp", 1024, 768),
    GroundShadow("strange_door_ground_shadow.webp", 1024, 512),
}

data class StrangeDoorAssetResolution(
    val key: StrangeDoorAssetKey,
    val fileName: String,
    val isReady: Boolean,
)

object StrangeDoorAssetContract {
    val requiredAssets: List<StrangeDoorAssetKey> = StrangeDoorAssetKey.values().toList()

    val requiredFileNames: Set<String> = requiredAssets.mapTo(sortedSetOf()) { it.fileName }
}

class StrangeDoorAssetMapper(
    private val availableFileNames: Set<String> = emptySet(),
) {
    fun resolve(key: StrangeDoorAssetKey): StrangeDoorAssetResolution {
        return StrangeDoorAssetResolution(
            key = key,
            fileName = key.fileName,
            isReady = key.fileName in availableFileNames,
        )
    }

    fun allAssetsReady(): Boolean {
        return StrangeDoorAssetContract.requiredFileNames.all { it in availableFileNames }
    }
}
