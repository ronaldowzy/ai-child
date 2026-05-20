package com.childai.companion.mascot

data class FrameSequenceUiState(
    val state: MascotState,
    val animationType: MascotAnimationType,
    val fps: Int,
    val width: Int,
    val height: Int,
    val framePaths: List<String>,
    val assetVersion: String,
) {
    val key: String
        get() = "${assetVersion}:${state.id}:${framePaths.size}:${fps}:${animationType.name}"

    val aspectRatio: Float
        get() = if (height > 0) width.toFloat() / height.toFloat() else 1f
}
