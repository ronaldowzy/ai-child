package com.childai.companion.mascot

data class MascotManifest(
    val mascot: String,
    val assetPackageVersion: String,
    val defaultFps: Int,
    val defaultState: MascotState,
    val states: Map<MascotState, MascotStateSpec>,
    val statePriority: List<MascotState>,
)

data class MascotStateSpec(
    val state: MascotState,
    val version: String,
    val animationType: MascotAnimationType,
    val fps: Int,
    val frameCount: Int,
    val width: Int,
    val height: Int,
    val path: String,
    val manifestPath: String,
    val framePattern: String,
    val spritesheet: String?,
)

data class MascotStateManifest(
    val state: MascotState,
    val displayName: String,
    val version: String,
    val sourceType: String,
    val fps: Int,
    val frameCount: Int,
    val loop: Boolean,
    val width: Int,
    val height: Int,
    val framePattern: String,
    val spritesheetFile: String?,
)
