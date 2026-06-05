package com.childai.companion.ui.chat.strangedoor

import com.childai.companion.R

object StrangeDoorAndroidResources {
    fun drawableResId(key: StrangeDoorAssetKey): Int {
        return when (key) {
            StrangeDoorAssetKey.DoorClosed -> R.drawable.strange_door_closed
            StrangeDoorAssetKey.DoorCracked -> R.drawable.strange_door_cracked
            StrangeDoorAssetKey.DoorAlmostOpen -> R.drawable.strange_door_almost_open
            StrangeDoorAssetKey.DoorOpen -> R.drawable.strange_door_open
            StrangeDoorAssetKey.RoundLock -> R.drawable.strange_door_round_lock
            StrangeDoorAssetKey.TransformGlow -> R.drawable.strange_door_transform_glow
            StrangeDoorAssetKey.DoorSuccessGlow -> R.drawable.strange_door_success_glow
            StrangeDoorAssetKey.RiddlePanel -> R.drawable.strange_door_riddle_panel
            StrangeDoorAssetKey.ToolCardPanel -> R.drawable.strange_door_tool_card_panel
            StrangeDoorAssetKey.GroundShadow -> R.drawable.strange_door_ground_shadow
        }
    }

    fun allRequiredResourcesReady(): Boolean {
        return StrangeDoorAssetContract.requiredAssets.all { drawableResId(it) != 0 }
    }
}
