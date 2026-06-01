package com.childai.companion.ui.chat

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.scaleIn
import androidx.compose.animation.scaleOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.blur
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.childai.companion.data.conversation.CompanionObjectMeta
import com.childai.companion.mascot.MascotState

/**
 * Companion stage for the Little White Fox.
 *
 * Wraps background gradient, state glow, animated fox, and state bubble
 * into a single visual unit. Does NOT own business logic, voice recording,
 * prompt, or parent report logic.
 */
@Composable
internal fun XiaobaohuCompanionStage(
    agent: FoxAgentUiState,
    mascotState: MascotState,
    compactLandscape: Boolean,
    viewportClass: CompanionRoomViewportClass = CompanionRoomViewportClass.Portrait,
    companionObject: CompanionObjectMeta? = null,
    modifier: Modifier = Modifier,
    debugMascotState: MascotState? = null,
) {
    val glowColor by animateColorAsState(
        targetValue = mascotState.glowColor(),
        animationSpec = tween(durationMillis = 600),
        label = "stageGlowColor",
    )

    BoxWithConstraints(modifier = modifier) {
        val mascotMaxSize = mascotMaxSizeForViewport(
            maxWidth = maxWidth,
            maxHeight = maxHeight,
            viewportClass = viewportClass,
        )
        val baseMascotOffsetY = mascotOffsetYForViewport(viewportClass)
        val stateGroundOffsetY = mascotGroundOffsetYForViewport(
            viewportClass = viewportClass,
            mascotState = mascotState,
        )
        val mascotOffsetY = baseMascotOffsetY + stateGroundOffsetY
        val visualScaleMultiplier = mascotVisualScaleMultiplier(viewportClass)
        val bubbleOffset = mascotStateBubbleOffset(viewportClass)

        Box(modifier = Modifier.fillMaxSize()) {
            // Companion object light point - rendered before fox so it stays behind
            CompanionLightPoint(
                companionObject = companionObject,
                viewportClass = viewportClass,
            )

            Box(
                modifier = Modifier
                    .align(Alignment.Center)
                    .offset(y = mascotOffsetY)
                    .size(
                        width = mascotMaxSize * 0.86f,
                        height = mascotMaxSize * 0.58f,
                    )
                    .blur(radius = if (compactLandscape) 42.dp else 48.dp)
                    .background(
                        Brush.radialGradient(
                            colors = listOf(
                                glowColor.copy(alpha = 0.34f),
                                Color.White.copy(alpha = 0.16f),
                                glowColor.copy(alpha = 0.0f),
                            ),
                        ),
                        shape = CircleShape,
                    ),
            )

            CartoonAgentView(
                agent = agent,
                debugMascotState = debugMascotState,
                visualScaleMultiplier = visualScaleMultiplier,
                modifier = Modifier
                    .align(Alignment.Center)
                    .offset(y = mascotOffsetY)
                    .sizeIn(
                        maxWidth = mascotMaxSize,
                        maxHeight = mascotMaxSize,
                    ),
            )

            val bubbleText = mascotStateBubbleText(mascotState)
            var renderedBubbleText by remember { mutableStateOf(bubbleText) }
            LaunchedEffect(bubbleText) {
                if (bubbleText != null) {
                    renderedBubbleText = bubbleText
                }
            }
            AnimatedVisibility(
                visible = bubbleText != null,
                enter = fadeIn(animationSpec = tween(durationMillis = 220)) +
                    slideInVertically(animationSpec = tween(durationMillis = 220)) { it / 6 } +
                    scaleIn(animationSpec = tween(durationMillis = 220), initialScale = 0.96f),
                exit = fadeOut(animationSpec = tween(durationMillis = 200)) +
                    slideOutVertically(animationSpec = tween(durationMillis = 200)) { it / 6 } +
                    scaleOut(animationSpec = tween(durationMillis = 200), targetScale = 0.96f),
                modifier = Modifier
                    .align(Alignment.CenterEnd)
                    .offset(
                        x = bubbleOffset.x,
                        y = bubbleOffset.y + stateGroundOffsetY,
                    ),
            ) {
                renderedBubbleText?.let { text ->
                    XiaobaohuStateBubble(
                        text = text,
                        compactLandscape = compactLandscape,
                    )
                }
            }
        }
    }
}

private data class MascotBubbleOffset(
    val x: Dp,
    val y: Dp,
)

private fun mascotMaxSizeForViewport(
    maxWidth: Dp,
    maxHeight: Dp,
    viewportClass: CompanionRoomViewportClass,
): Dp {
    return when (viewportClass) {
        CompanionRoomViewportClass.LandscapeWide -> minOf(
            maxWidth * 0.94f,
            (maxHeight * 0.82f).coerceAtLeast(190.dp),
            590.dp,
        )

        CompanionRoomViewportClass.LandscapeTablet -> minOf(
            maxWidth * 0.86f,
            (maxHeight * 0.74f).coerceAtLeast(240.dp),
            680.dp,
        )

        CompanionRoomViewportClass.LandscapeSquare -> minOf(
            maxWidth * 0.82f,
            (maxHeight * 0.70f).coerceAtLeast(240.dp),
            620.dp,
        )

        CompanionRoomViewportClass.Portrait -> minOf(
            maxWidth * 0.98f,
            (maxHeight * 0.80f).coerceAtLeast(190.dp),
            520.dp,
        )

        CompanionRoomViewportClass.PortraitExpanded -> minOf(
            maxWidth * 0.78f,
            (maxHeight * 0.68f).coerceAtLeast(250.dp),
            560.dp,
        )
    }
}

private fun mascotOffsetYForViewport(viewportClass: CompanionRoomViewportClass): Dp {
    return when (viewportClass) {
        CompanionRoomViewportClass.LandscapeWide -> (-8).dp
        CompanionRoomViewportClass.LandscapeTablet -> 6.dp
        CompanionRoomViewportClass.LandscapeSquare -> 12.dp
        CompanionRoomViewportClass.Portrait -> 28.dp
        CompanionRoomViewportClass.PortraitExpanded -> 82.dp
    }
}

private fun mascotGroundOffsetYForViewport(
    viewportClass: CompanionRoomViewportClass,
    mascotState: MascotState,
): Dp {
    if (viewportClass != CompanionRoomViewportClass.PortraitExpanded) {
        return 0.dp
    }

    return when (mascotState) {
        MascotState.Speaking -> 0.dp
        MascotState.Listening,
        MascotState.Thinking,
        MascotState.PreparingSpeech,
        MascotState.CoCreate,
        MascotState.Paused,
        MascotState.Retry -> 36.dp
        MascotState.ImageViewing -> 60.dp
        MascotState.Idle,
        MascotState.WaitingSoft -> 96.dp
    }
}

private fun mascotVisualScaleMultiplier(viewportClass: CompanionRoomViewportClass): Float {
    return when (viewportClass) {
        CompanionRoomViewportClass.LandscapeWide -> 1.30f
        CompanionRoomViewportClass.LandscapeTablet -> 1.16f
        CompanionRoomViewportClass.LandscapeSquare -> 1.08f
        CompanionRoomViewportClass.Portrait -> 1.18f
        CompanionRoomViewportClass.PortraitExpanded -> 1.02f
    }
}

private fun mascotStateBubbleOffset(viewportClass: CompanionRoomViewportClass): MascotBubbleOffset {
    return when (viewportClass) {
        CompanionRoomViewportClass.LandscapeWide -> MascotBubbleOffset(x = (-44).dp, y = (-90).dp)
        CompanionRoomViewportClass.LandscapeTablet -> MascotBubbleOffset(x = (-28).dp, y = (-78).dp)
        CompanionRoomViewportClass.LandscapeSquare -> MascotBubbleOffset(x = (-20).dp, y = (-68).dp)
        CompanionRoomViewportClass.Portrait -> MascotBubbleOffset(x = (-20).dp, y = (-72).dp)
        CompanionRoomViewportClass.PortraitExpanded -> MascotBubbleOffset(x = (-24).dp, y = (-16).dp)
    }
}

@Composable
private fun BubbleTail(
    color: Color,
    modifier: Modifier = Modifier,
) {
    Canvas(modifier = modifier.size(width = 18.dp, height = 12.dp)) {
        val path = Path().apply {
            moveTo(0f, 0f)
            lineTo(size.width, 0f)
            lineTo(size.width * 0.24f, size.height)
            close()
        }
        drawPath(path = path, color = color)
    }
}

/**
 * Small rounded bubble showing the current mascot state description.
 * Not a chat message — stays outside the message list.
 */
@Composable
private fun XiaobaohuStateBubble(
    text: String,
    compactLandscape: Boolean,
    modifier: Modifier = Modifier,
) {
    val bubbleColor = Color.White.copy(alpha = 0.88f)
    Box(modifier = modifier) {
        Surface(
            modifier = Modifier.widthIn(max = if (compactLandscape) 156.dp else 180.dp),
            shape = RoundedCornerShape(24.dp),
            color = bubbleColor,
            shadowElevation = 3.dp,
            border = BorderStroke(
                width = 1.dp,
                color = Color.White.copy(alpha = 0.62f),
            ),
        ) {
            Text(
                text = text,
                modifier = Modifier.padding(
                    horizontal = if (compactLandscape) 12.dp else 15.dp,
                    vertical = if (compactLandscape) 7.dp else 9.dp,
                ),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.84f),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                textAlign = TextAlign.Center,
            )
        }
        BubbleTail(
            color = bubbleColor,
            modifier = Modifier
                .align(Alignment.BottomStart)
                .offset(x = 28.dp, y = 8.dp),
        )
    }
}

// --- State-to-color mapping ---

private fun MascotState.glowColor(): Color {
    return when (this) {
        MascotState.Idle -> Color(0xFFFFF3E0)           // warm cream
        MascotState.WaitingSoft -> Color(0xFFFFF8E1)    // soft warm white
        MascotState.Listening -> Color(0xFFB3E5FC)      // light blue
        MascotState.Thinking -> Color(0xFFFFF9C4)       // soft yellow
        MascotState.PreparingSpeech -> Color(0xFFFFF3E0) // warm white
        MascotState.Speaking -> Color(0xFFFFE0B2)       // light gold
        MascotState.ImageViewing -> Color(0xFFD1C4E9)   // soft lavender
        MascotState.CoCreate -> Color(0xFFFFF9C4)       // soft gold
        MascotState.Paused -> Color(0xFFF5F5F5)         // muted gray
        MascotState.Retry -> Color(0xFFFFF8E1)          // soft cream, no red
    }
}

// --- State-to-bubble-text mapping ---

internal fun mascotStateBubbleText(state: MascotState): String? {
    return when (state) {
        MascotState.Idle -> "我在这儿"
        MascotState.WaitingSoft -> "想说再说"
        MascotState.Listening -> "我在听"
        MascotState.Thinking -> "我想想"
        MascotState.PreparingSpeech -> "我准备说"
        MascotState.Speaking -> null
        MascotState.ImageViewing -> "我在看"
        MascotState.CoCreate -> "一起想想"
        MascotState.Paused -> "先停一下"
        MascotState.Retry -> "再试一次"
    }
}

// --- Companion object visual types ---

internal enum class CompanionLocation {
    WindowSide,
    CarpetEdge,
    NearFox,
    OutsideWindow,
}

internal enum class CompanionVisualType {
    StarPoint,
    CloudShadow,
    LightSpot,
    SoftOutline,
}

internal fun String.toCompanionLocation(): CompanionLocation {
    return when (this) {
        "窗边" -> CompanionLocation.WindowSide
        "地毯边" -> CompanionLocation.CarpetEdge
        "小白狐旁边" -> CompanionLocation.NearFox
        "窗外" -> CompanionLocation.OutsideWindow
        else -> CompanionLocation.WindowSide
    }
}

internal fun String.toCompanionVisualType(): CompanionVisualType {
    return when {
        contains("星") || equals("star", ignoreCase = true) -> CompanionVisualType.StarPoint
        contains("云") || equals("cloud", ignoreCase = true) -> CompanionVisualType.CloudShadow
        contains("光") || contains("影") -> CompanionVisualType.LightSpot
        else -> CompanionVisualType.SoftOutline
    }
}

internal fun CompanionObjectMeta.shouldShowVisual(): Boolean {
    // Only show for seed state (first-time star) or active+recall state
    // Do not show for paused state or action=none
    if (state == "paused") return false
    if (state == "seed" && action == "name_seed") return true
    if (state == "active" && action in setOf("recall", "co_create")) return true
    return false
}

private data class CompanionVisualConfig(
    val size: Dp,
    val midGlowSize: Dp,
    val coreSize: Dp,
    val blurRadius: Dp,
    val baseAlpha: Float,
    val colors: List<Color>,
    val midGlowColor: Color,
    val coreColor: Color,
    val animationType: CompanionAnimationType,
)

private enum class CompanionAnimationType {
    Breathing,
    Floating,
    Static,
}

private fun CompanionVisualType.config(): CompanionVisualConfig {
    return when (this) {
        CompanionVisualType.StarPoint -> CompanionVisualConfig(
            size = 38.dp,
            midGlowSize = 22.dp,
            coreSize = 9.dp,
            blurRadius = 16.dp,
            baseAlpha = 0.96f,
            colors = listOf(
                Color(0xFFFFF7CC).copy(alpha = 0.98f),
                Color(0xFFFFD86B).copy(alpha = 0.72f),
                Color(0xFFFFF8E1).copy(alpha = 0.0f),
            ),
            midGlowColor = Color(0xFFFFD45A),
            coreColor = Color(0xFFFFFCF0),
            animationType = CompanionAnimationType.Breathing,
        )
        CompanionVisualType.CloudShadow -> CompanionVisualConfig(
            size = 26.dp,
            midGlowSize = 16.dp,
            coreSize = 0.dp,
            blurRadius = 12.dp,
            baseAlpha = 0.62f,
            colors = listOf(
                Color(0xFFE8EAF6).copy(alpha = 0.8f),
                Color(0xFFC5CAE9).copy(alpha = 0.4f),
                Color(0xFFE8EAF6).copy(alpha = 0.0f),
            ),
            midGlowColor = Color.Transparent,
            coreColor = Color.Transparent,
            animationType = CompanionAnimationType.Floating,
        )
        CompanionVisualType.LightSpot -> CompanionVisualConfig(
            size = 24.dp,
            midGlowSize = 14.dp,
            coreSize = 0.dp,
            blurRadius = 12.dp,
            baseAlpha = 0.68f,
            colors = listOf(
                Color(0xFFFFF3E0).copy(alpha = 0.85f),
                Color(0xFFFFE0B2).copy(alpha = 0.45f),
                Color(0xFFFFF3E0).copy(alpha = 0.0f),
            ),
            midGlowColor = Color.Transparent,
            coreColor = Color.Transparent,
            animationType = CompanionAnimationType.Floating,
        )
        CompanionVisualType.SoftOutline -> CompanionVisualConfig(
            size = 22.dp,
            midGlowSize = 12.dp,
            coreSize = 0.dp,
            blurRadius = 11.dp,
            baseAlpha = 0.6f,
            colors = listOf(
                Color(0xFFF3E5F5).copy(alpha = 0.8f),
                Color(0xFFE1BEE7).copy(alpha = 0.4f),
                Color(0xFFF3E5F5).copy(alpha = 0.0f),
            ),
            midGlowColor = Color.Transparent,
            coreColor = Color.Transparent,
            animationType = CompanionAnimationType.Static,
        )
    }
}

private data class CompanionPlacement(
    val alignment: Alignment,
    val offset: Offset,
)

private fun CompanionLocation.placementForViewport(
    viewportClass: CompanionRoomViewportClass,
): CompanionPlacement {
    return when (this) {
        CompanionLocation.WindowSide -> CompanionPlacement(
            alignment = Alignment.TopStart,
            offset = when (viewportClass) {
                CompanionRoomViewportClass.Portrait -> Offset(92f, 118f)
                CompanionRoomViewportClass.PortraitExpanded -> Offset(118f, 140f)
                CompanionRoomViewportClass.LandscapeWide -> Offset(110f, 92f)
                CompanionRoomViewportClass.LandscapeTablet -> Offset(102f, 96f)
                CompanionRoomViewportClass.LandscapeSquare -> Offset(96f, 88f)
            },
        )
        CompanionLocation.CarpetEdge -> CompanionPlacement(
            alignment = Alignment.BottomCenter,
            offset = when (viewportClass) {
                CompanionRoomViewportClass.Portrait -> Offset(-96f, -86f)
                CompanionRoomViewportClass.PortraitExpanded -> Offset(-118f, -106f)
                CompanionRoomViewportClass.LandscapeWide -> Offset(-128f, -76f)
                CompanionRoomViewportClass.LandscapeTablet -> Offset(-112f, -84f)
                CompanionRoomViewportClass.LandscapeSquare -> Offset(-102f, -80f)
            },
        )
        CompanionLocation.NearFox -> CompanionPlacement(
            alignment = Alignment.Center,
            offset = when (viewportClass) {
                CompanionRoomViewportClass.Portrait -> Offset(96f, 38f)
                CompanionRoomViewportClass.PortraitExpanded -> Offset(118f, 52f)
                CompanionRoomViewportClass.LandscapeWide -> Offset(136f, 26f)
                CompanionRoomViewportClass.LandscapeTablet -> Offset(122f, 30f)
                CompanionRoomViewportClass.LandscapeSquare -> Offset(112f, 28f)
            },
        )
        CompanionLocation.OutsideWindow -> CompanionPlacement(
            alignment = Alignment.TopStart,
            offset = when (viewportClass) {
                CompanionRoomViewportClass.Portrait -> Offset(36f, 74f)
                CompanionRoomViewportClass.PortraitExpanded -> Offset(48f, 82f)
                CompanionRoomViewportClass.LandscapeWide -> Offset(42f, 62f)
                CompanionRoomViewportClass.LandscapeTablet -> Offset(40f, 66f)
                CompanionRoomViewportClass.LandscapeSquare -> Offset(38f, 60f)
            },
        )
    }
}

@Composable
private fun CompanionLightPoint(
    companionObject: CompanionObjectMeta?,
    viewportClass: CompanionRoomViewportClass,
    modifier: Modifier = Modifier,
) {
    if (companionObject == null || !companionObject.shouldShowVisual()) return

    val location = companionObject.lightLocation.toCompanionLocation()
    val visualType = companionObject.objectType.toCompanionVisualType()
    val config = visualType.config()
    val placement = location.placementForViewport(viewportClass)

    val alpha = when (config.animationType) {
        CompanionAnimationType.Breathing -> {
            val infiniteTransition = rememberInfiniteTransition(label = "companionBreathing")
            val animatedAlpha by infiniteTransition.animateFloat(
                initialValue = config.baseAlpha - 0.15f,
                targetValue = config.baseAlpha + 0.1f,
                animationSpec = infiniteRepeatable(
                    animation = tween(3000),
                    repeatMode = RepeatMode.Reverse,
                ),
                label = "companionAlpha",
            )
            animatedAlpha
        }
        CompanionAnimationType.Floating -> {
            val infiniteTransition = rememberInfiniteTransition(label = "companionFloating")
            val animatedAlpha by infiniteTransition.animateFloat(
                initialValue = config.baseAlpha - 0.1f,
                targetValue = config.baseAlpha + 0.08f,
                animationSpec = infiniteRepeatable(
                    animation = tween(4000),
                    repeatMode = RepeatMode.Reverse,
                ),
                label = "companionAlpha",
            )
            animatedAlpha
        }
        CompanionAnimationType.Static -> config.baseAlpha
    }

    // Floating offset animation for cloud/light types
    val offsetY = when (config.animationType) {
        CompanionAnimationType.Floating -> {
            val infiniteTransition = rememberInfiniteTransition(label = "companionOffsetY")
            val animatedOffset by infiniteTransition.animateFloat(
                initialValue = -2f,
                targetValue = 2f,
                animationSpec = infiniteRepeatable(
                    animation = tween(4000),
                    repeatMode = RepeatMode.Reverse,
                ),
                label = "companionOffsetY",
            )
            animatedOffset
        }
        else -> 0f
    }

    Box(modifier = modifier.fillMaxSize()) {
        Box(
            modifier = Modifier
                .align(placement.alignment)
                .offset(x = placement.offset.x.dp, y = (placement.offset.y + offsetY).dp)
                .size(config.size),
        ) {
            Box(
                modifier = Modifier
                    .align(Alignment.Center)
                    .size(config.size)
                    .alpha(alpha)
                    .blur(radius = config.blurRadius)
                    .background(
                        brush = Brush.radialGradient(
                            colors = config.colors,
                        ),
                        shape = CircleShape,
                    ),
            )
            if (config.midGlowColor != Color.Transparent) {
                Box(
                    modifier = Modifier
                        .align(Alignment.Center)
                        .size(config.midGlowSize)
                        .alpha((alpha * 0.82f).coerceAtMost(1f))
                        .background(
                            color = config.midGlowColor.copy(alpha = 0.66f),
                            shape = CircleShape,
                        ),
                )
            }
            if (config.coreColor != Color.Transparent && config.coreSize > 0.dp) {
                Box(
                    modifier = Modifier
                        .align(Alignment.Center)
                        .size(config.coreSize)
                        .background(
                            color = config.coreColor,
                            shape = CircleShape,
                        ),
                )
            }
        }
    }
}
