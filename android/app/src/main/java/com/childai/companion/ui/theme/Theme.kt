package com.childai.companion.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColorScheme = lightColorScheme(
    primary = ForestGreen,
    onPrimary = Color.White,
    primaryContainer = SoftLeaf,
    onPrimaryContainer = ForestGreenDark,
    secondary = ClayOrange,
    onSecondary = Color.White,
    background = WarmIvory,
    onBackground = InkBrown,
    surface = Color.White,
    onSurface = InkBrown,
    surfaceVariant = SoftLeaf,
    onSurfaceVariant = ForestGreenDark,
    outline = Color(0xFF87927F),
)

@Composable
fun ChildAiCompanionTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = LightColorScheme,
        typography = ChildAiTypography,
        content = content,
    )
}
