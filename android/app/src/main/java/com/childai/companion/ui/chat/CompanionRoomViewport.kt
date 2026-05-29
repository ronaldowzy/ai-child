package com.childai.companion.ui.chat

import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

internal enum class CompanionRoomViewportClass {
    Portrait,
    PortraitExpanded,
    LandscapeWide,
    LandscapeTablet,
    LandscapeSquare,
}

internal val CompanionRoomViewportClass.isLandscape: Boolean
    get() = when (this) {
        CompanionRoomViewportClass.LandscapeWide,
        CompanionRoomViewportClass.LandscapeTablet,
        CompanionRoomViewportClass.LandscapeSquare -> true
        CompanionRoomViewportClass.Portrait,
        CompanionRoomViewportClass.PortraitExpanded -> false
    }

internal fun companionRoomViewportClass(
    maxWidth: Dp,
    maxHeight: Dp,
): CompanionRoomViewportClass {
    if (maxWidth <= maxHeight) {
        return if (maxWidth >= 600.dp || (maxWidth >= 500.dp && maxHeight >= 800.dp)) {
            CompanionRoomViewportClass.PortraitExpanded
        } else {
            CompanionRoomViewportClass.Portrait
        }
    }

    val aspectRatio = maxWidth.value / maxHeight.value.coerceAtLeast(1f)
    return when {
        aspectRatio >= 1.90f -> CompanionRoomViewportClass.LandscapeWide
        aspectRatio >= 1.45f -> CompanionRoomViewportClass.LandscapeTablet
        else -> CompanionRoomViewportClass.LandscapeSquare
    }
}

internal fun companionLandscapeIsCompact(
    maxWidth: Dp,
    maxHeight: Dp,
    viewportClass: CompanionRoomViewportClass,
): Boolean {
    return viewportClass.isLandscape && (maxHeight < 430.dp || maxWidth < 760.dp)
}

internal data class CompanionLandscapeLayoutMetrics(
    val horizontalPadding: Dp,
    val verticalPadding: Dp,
    val columnGap: Dp,
    val operationPanelMaxWidth: Dp,
)

internal data class CompanionPortraitLayoutMetrics(
    val horizontalPadding: Dp,
    val verticalPadding: Dp,
    val inputMaxWidth: Dp,
)

internal fun companionPortraitLayoutMetrics(
    viewportClass: CompanionRoomViewportClass,
): CompanionPortraitLayoutMetrics {
    return if (viewportClass == CompanionRoomViewportClass.PortraitExpanded) {
        CompanionPortraitLayoutMetrics(
            horizontalPadding = 44.dp,
            verticalPadding = 24.dp,
            inputMaxWidth = 680.dp,
        )
    } else {
        CompanionPortraitLayoutMetrics(
            horizontalPadding = 20.dp,
            verticalPadding = 16.dp,
            inputMaxWidth = 620.dp,
        )
    }
}

internal fun companionLandscapeLayoutMetrics(
    viewportClass: CompanionRoomViewportClass,
    compactLandscape: Boolean,
): CompanionLandscapeLayoutMetrics {
    if (compactLandscape) {
        return CompanionLandscapeLayoutMetrics(
            horizontalPadding = 14.dp,
            verticalPadding = 10.dp,
            columnGap = 14.dp,
            operationPanelMaxWidth = 560.dp,
        )
    }

    return when (viewportClass) {
        CompanionRoomViewportClass.LandscapeWide -> CompanionLandscapeLayoutMetrics(
            horizontalPadding = 32.dp,
            verticalPadding = 24.dp,
            columnGap = 28.dp,
            operationPanelMaxWidth = 820.dp,
        )

        CompanionRoomViewportClass.LandscapeTablet -> CompanionLandscapeLayoutMetrics(
            horizontalPadding = 20.dp,
            verticalPadding = 18.dp,
            columnGap = 12.dp,
            operationPanelMaxWidth = 720.dp,
        )

        CompanionRoomViewportClass.LandscapeSquare -> CompanionLandscapeLayoutMetrics(
            horizontalPadding = 30.dp,
            verticalPadding = 24.dp,
            columnGap = 18.dp,
            operationPanelMaxWidth = 620.dp,
        )

        CompanionRoomViewportClass.Portrait,
        CompanionRoomViewportClass.PortraitExpanded -> CompanionLandscapeLayoutMetrics(
            horizontalPadding = 20.dp,
            verticalPadding = 16.dp,
            columnGap = 0.dp,
            operationPanelMaxWidth = 620.dp,
        )
    }
}
