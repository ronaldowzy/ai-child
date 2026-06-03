package com.childai.companion.ui.chat

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.EaseOut
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
import androidx.compose.foundation.Image
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
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.geometry.CornerRadius as GeoCornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
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
            // Companion object ambient glow stays behind the fox,
            // while the soft shape layer can still appear in front.
            CompanionLightPointBackdrop(
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

            CompanionLightPointForeground(
                companionObject = companionObject,
                viewportClass = viewportClass,
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

/** 6 种小物件影子类型，每种 visual_kind 对应独立渲染。 */
internal enum class CompanionVisualType {
    Star,
    Cloud,
    PaperBoat,
    TinyDoor,
    DinoShadow,
    BlockLight,
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

/**
 * 当 light_location 为空或未知时，按 visual_kind 给出兜底位置。
 * star / cloud / tiny_door 默认窗边；paper_boat / dino_shadow / block_light 默认地毯边。
 */
private fun String.defaultLocationForVisualKind(): CompanionLocation {
    return when (this) {
        "star", "cloud", "tiny_door" -> CompanionLocation.WindowSide
        "paper_boat", "dino_shadow", "block_light" -> CompanionLocation.CarpetEdge
        else -> CompanionLocation.WindowSide
    }
}

internal fun String.toCompanionVisualType(): CompanionVisualType {
    return when (this) {
        "star" -> CompanionVisualType.Star
        "cloud" -> CompanionVisualType.Cloud
        "paper_boat" -> CompanionVisualType.PaperBoat
        "tiny_door" -> CompanionVisualType.TinyDoor
        "dino_shadow" -> CompanionVisualType.DinoShadow
        "block_light" -> CompanionVisualType.BlockLight
        // legacy fallback: 从 objectType 模糊匹配（兼容旧后端）
        else -> when {
            contains("星") || equals("star", ignoreCase = true) -> CompanionVisualType.Star
            contains("云") || equals("cloud", ignoreCase = true) -> CompanionVisualType.Cloud
            contains("纸") || contains("船") -> CompanionVisualType.PaperBoat
            contains("门") -> CompanionVisualType.TinyDoor
            contains("恐") || contains("龙") -> CompanionVisualType.DinoShadow
            contains("积") || contains("木") -> CompanionVisualType.BlockLight
            contains("光") || contains("影") -> CompanionVisualType.BlockLight
            else -> CompanionVisualType.Star
        }
    }
}

internal fun CompanionObjectMeta.shouldShowVisual(): Boolean {
    if (state == "paused") return false
    if (state == "seed" && action == "name_seed") return true
    if (state == "active" && action in setOf("recall", "co_create")) return true
    return false
}

/** 小物件影子渲染配置：光晕层 + Canvas 形状层 + 入场/持续动效。 */
private data class CompanionVisualConfig(
    val glowSize: Dp,
    val glowBlurRadius: Dp,
    val glowAlpha: Float,
    val glowColors: List<Color>,
    val shapeSize: Dp,
    val shapeSizeV: Dp,
    val assetSize: Dp,
    val shapeFill: Color,
    val shapeStroke: Color,
    val animationType: CompanionAnimationType,
)

internal data class CompanionVisualEmphasis(
    val backdropAlphaMultiplier: Float,
    val foregroundAlphaMultiplier: Float,
    val glowScale: Float,
    val shapeScale: Float,
    val foregroundGlowAlpha: Float,
)

internal fun CompanionObjectMeta.visualEmphasis(): CompanionVisualEmphasis {
    return when {
        state == "active" && action == "co_create" -> CompanionVisualEmphasis(
            backdropAlphaMultiplier = 1.34f,
            foregroundAlphaMultiplier = 1.58f,
            glowScale = 1.22f,
            shapeScale = 1.14f,
            foregroundGlowAlpha = 0.38f,
        )
        state == "active" && action == "recall" -> CompanionVisualEmphasis(
            backdropAlphaMultiplier = 1.12f,
            foregroundAlphaMultiplier = 1.18f,
            glowScale = 1.08f,
            shapeScale = 1.06f,
            foregroundGlowAlpha = 0.24f,
        )
        state == "seed" && action == "name_seed" -> CompanionVisualEmphasis(
            backdropAlphaMultiplier = 1.08f,
            foregroundAlphaMultiplier = 1.10f,
            glowScale = 1.04f,
            shapeScale = 1.02f,
            foregroundGlowAlpha = 0.20f,
        )
        else -> CompanionVisualEmphasis(
            backdropAlphaMultiplier = 1f,
            foregroundAlphaMultiplier = 1f,
            glowScale = 1f,
            shapeScale = 1f,
            foregroundGlowAlpha = 0f,
        )
    }
}

private enum class CompanionAnimationType {
    Breathing,
    Floating,
}

private fun CompanionVisualType.config(): CompanionVisualConfig {
    return when (this) {
        CompanionVisualType.Star -> CompanionVisualConfig(
            glowSize = 42.dp,
            glowBlurRadius = 16.dp,
            glowAlpha = 0.45f,
            glowColors = listOf(
                Color(0xFFFFF8E1).copy(alpha = 0.72f),
                Color(0xFFFFECB3).copy(alpha = 0.36f),
                Color(0xFFFFF8E1).copy(alpha = 0.0f),
            ),
            shapeSize = 30.dp,
            shapeSizeV = 30.dp,
            assetSize = 48.dp,
            shapeFill = Color(0xFFFFE082).copy(alpha = 0.50f),
            shapeStroke = Color(0xFFFFCA28).copy(alpha = 0.30f),
            animationType = CompanionAnimationType.Breathing,
        )
        CompanionVisualType.Cloud -> CompanionVisualConfig(
            glowSize = 46.dp,
            glowBlurRadius = 14.dp,
            glowAlpha = 0.40f,
            glowColors = listOf(
                Color(0xFFF5F5F5).copy(alpha = 0.65f),
                Color(0xFFE8EAF6).copy(alpha = 0.30f),
                Color(0xFFF5F5F5).copy(alpha = 0.0f),
            ),
            shapeSize = 40.dp,
            shapeSizeV = 26.dp,
            assetSize = 52.dp,
            shapeFill = Color(0xFFE8EAF6).copy(alpha = 0.45f),
            shapeStroke = Color(0xFFC5CAE9).copy(alpha = 0.28f),
            animationType = CompanionAnimationType.Floating,
        )
        CompanionVisualType.PaperBoat -> CompanionVisualConfig(
            glowSize = 38.dp,
            glowBlurRadius = 13.dp,
            glowAlpha = 0.38f,
            glowColors = listOf(
                Color(0xFFFFF8E1).copy(alpha = 0.60f),
                Color(0xFFE1F5FE).copy(alpha = 0.28f),
                Color(0xFFFFF8E1).copy(alpha = 0.0f),
            ),
            shapeSize = 34.dp,
            shapeSizeV = 28.dp,
            assetSize = 50.dp,
            shapeFill = Color(0xFFFFF8E1).copy(alpha = 0.42f),
            shapeStroke = Color(0xFFE1F5FE).copy(alpha = 0.30f),
            animationType = CompanionAnimationType.Floating,
        )
        CompanionVisualType.TinyDoor -> CompanionVisualConfig(
            glowSize = 34.dp,
            glowBlurRadius = 13.dp,
            glowAlpha = 0.40f,
            glowColors = listOf(
                Color(0xFFFFF3E0).copy(alpha = 0.62f),
                Color(0xFFEFEBE9).copy(alpha = 0.30f),
                Color(0xFFFFF3E0).copy(alpha = 0.0f),
            ),
            shapeSize = 26.dp,
            shapeSizeV = 36.dp,
            assetSize = 50.dp,
            shapeFill = Color(0xFFFFF3E0).copy(alpha = 0.42f),
            shapeStroke = Color(0xFFD7CCC8).copy(alpha = 0.32f),
            animationType = CompanionAnimationType.Breathing,
        )
        CompanionVisualType.DinoShadow -> CompanionVisualConfig(
            glowSize = 40.dp,
            glowBlurRadius = 14.dp,
            glowAlpha = 0.38f,
            glowColors = listOf(
                Color(0xFFE8F5E9).copy(alpha = 0.60f),
                Color(0xFFC8E6C9).copy(alpha = 0.28f),
                Color(0xFFE8F5E9).copy(alpha = 0.0f),
            ),
            shapeSize = 36.dp,
            shapeSizeV = 30.dp,
            assetSize = 54.dp,
            shapeFill = Color(0xFFC8E6C9).copy(alpha = 0.40f),
            shapeStroke = Color(0xFFA5D6A7).copy(alpha = 0.28f),
            animationType = CompanionAnimationType.Floating,
        )
        CompanionVisualType.BlockLight -> CompanionVisualConfig(
            glowSize = 36.dp,
            glowBlurRadius = 13.dp,
            glowAlpha = 0.40f,
            glowColors = listOf(
                Color(0xFFFFE0B2).copy(alpha = 0.62f),
                Color(0xFFFFCC80).copy(alpha = 0.30f),
                Color(0xFFFFE0B2).copy(alpha = 0.0f),
            ),
            shapeSize = 28.dp,
            shapeSizeV = 28.dp,
            assetSize = 48.dp,
            shapeFill = Color(0xFFFFCC80).copy(alpha = 0.42f),
            shapeStroke = Color(0xFFFFB74D).copy(alpha = 0.30f),
            animationType = CompanionAnimationType.Breathing,
        )
    }
}

internal data class CompanionPlacement(
    val alignment: Alignment,
    val offset: Offset,
)

internal fun CompanionLocation.placementForViewport(
    viewportClass: CompanionRoomViewportClass,
): CompanionPlacement {
    return when (this) {
        CompanionLocation.WindowSide -> CompanionPlacement(
            alignment = Alignment.CenterStart,
            offset = when (viewportClass) {
                CompanionRoomViewportClass.Portrait -> Offset(84f, -84f)
                CompanionRoomViewportClass.PortraitExpanded -> Offset(92f, -82f)
                CompanionRoomViewportClass.LandscapeWide -> Offset(92f, -64f)
                CompanionRoomViewportClass.LandscapeTablet -> Offset(84f, -54f)
                CompanionRoomViewportClass.LandscapeSquare -> Offset(80f, -58f)
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
private fun CompanionLightPointBackdrop(
    companionObject: CompanionObjectMeta?,
    viewportClass: CompanionRoomViewportClass,
    modifier: Modifier = Modifier,
) {
    val renderState = rememberCompanionLightPointRenderState(
        companionObject = companionObject,
        viewportClass = viewportClass,
    ) ?: return
    val assetResId = renderState.assetResourceName?.let { companionObjectAssetResId(it) }
    if (assetResId != null) return

    val backdropAlpha = (renderState.alpha * renderState.emphasis.backdropAlphaMultiplier)
        .coerceIn(0f, 0.90f)

    Box(modifier = modifier.fillMaxSize()) {
        Box(
            modifier = Modifier
                .align(renderState.placement.alignment)
                .offset(
                    x = renderState.placement.offset.x.dp,
                    y = (renderState.placement.offset.y + renderState.offsetY).dp,
                )
                .graphicsLayer {
                    scaleX = renderState.scale
                    scaleY = renderState.scale
                }
                .size(
                    width = maxOf(
                        renderState.config.glowSize * renderState.emphasis.glowScale,
                        renderState.config.shapeSize * renderState.emphasis.shapeScale,
                        renderState.assetSize,
                    ),
                    height = maxOf(
                        renderState.config.glowSize * renderState.emphasis.glowScale,
                        renderState.config.shapeSizeV * renderState.emphasis.shapeScale,
                        renderState.assetSize,
                    ),
                ),
        ) {
            Box(
                modifier = Modifier
                    .align(Alignment.Center)
                    .size(renderState.config.glowSize * renderState.emphasis.glowScale)
                    .alpha(backdropAlpha)
                    .blur(radius = renderState.config.glowBlurRadius)
                    .background(
                        brush = Brush.radialGradient(colors = renderState.config.glowColors),
                        shape = CircleShape,
                    ),
            )
        }
    }
}

@Composable
private fun CompanionLightPointForeground(
    companionObject: CompanionObjectMeta?,
    viewportClass: CompanionRoomViewportClass,
    modifier: Modifier = Modifier,
) {
    val renderState = rememberCompanionLightPointRenderState(
        companionObject = companionObject,
        viewportClass = viewportClass,
    ) ?: return
    val foregroundAlpha = (renderState.alpha * renderState.emphasis.foregroundAlphaMultiplier)
        .coerceIn(0f, 0.94f)

    Box(modifier = modifier.fillMaxSize()) {
        val assetResId = renderState.assetResourceName?.let { companionObjectAssetResId(it) }
        Box(
            modifier = Modifier
                .align(renderState.placement.alignment)
                .offset(
                    x = renderState.placement.offset.x.dp,
                    y = (renderState.placement.offset.y + renderState.offsetY).dp,
                )
                .graphicsLayer {
                    scaleX = renderState.scale
                    scaleY = renderState.scale
                }
                .size(
                    width = maxOf(
                        renderState.config.glowSize * renderState.emphasis.glowScale,
                        renderState.config.shapeSize * renderState.emphasis.shapeScale,
                        renderState.assetSize,
                    ),
                    height = maxOf(
                        renderState.config.glowSize * renderState.emphasis.glowScale,
                        renderState.config.shapeSizeV * renderState.emphasis.shapeScale,
                        renderState.assetSize,
                    ),
                ),
        ) {
            if (assetResId != null) {
                Image(
                    painter = painterResource(id = assetResId),
                    contentDescription = null,
                    contentScale = ContentScale.Fit,
                    modifier = Modifier
                        .align(Alignment.Center)
                        .size(renderState.assetSize)
                        .alpha(renderState.assetAlpha),
                )
            } else {
                Box(
                    modifier = Modifier
                        .align(Alignment.Center)
                        .size(
                            renderState.config.shapeSize * renderState.emphasis.shapeScale * 1.18f,
                        )
                        .alpha(renderState.emphasis.foregroundGlowAlpha)
                        .blur(radius = (renderState.config.glowBlurRadius * 0.72f))
                        .background(
                            brush = Brush.radialGradient(colors = renderState.config.glowColors),
                            shape = CircleShape,
                        ),
                )
                Canvas(
                    modifier = Modifier
                        .align(Alignment.Center)
                        .size(
                            renderState.config.shapeSize * renderState.emphasis.shapeScale,
                            renderState.config.shapeSizeV * renderState.emphasis.shapeScale,
                        ),
                ) {
                    val w = size.width
                    val h = size.height
                    val fill = renderState.config.shapeFill.copy(
                        alpha = (renderState.config.shapeFill.alpha * foregroundAlpha / renderState.config.glowAlpha)
                            .coerceIn(0f, 0.88f),
                    )
                    val stroke = renderState.config.shapeStroke.copy(
                        alpha = (renderState.config.shapeStroke.alpha * foregroundAlpha / renderState.config.glowAlpha)
                            .coerceIn(0f, 0.82f),
                    )
                    drawCompanionShape(renderState.visualType, w, h, fill, stroke)
                }
            }
        }
    }
}

private data class CompanionLightPointRenderState(
    val placement: CompanionPlacement,
    val visualType: CompanionVisualType,
    val config: CompanionVisualConfig,
    val emphasis: CompanionVisualEmphasis,
    val assetResourceName: String?,
    val assetSize: Dp,
    val assetAlpha: Float,
    val alpha: Float,
    val offsetY: Float,
    val scale: Float,
)

@Composable
private fun rememberCompanionLightPointRenderState(
    companionObject: CompanionObjectMeta?,
    viewportClass: CompanionRoomViewportClass,
): CompanionLightPointRenderState? {
    if (companionObject == null || !companionObject.shouldShowVisual()) return null

    val location = if (companionObject.lightLocation.isBlank()) {
        companionObject.visualKind.defaultLocationForVisualKind()
    } else {
        companionObject.lightLocation.toCompanionLocation()
    }
    val visualType = companionObject.visualKind.toCompanionVisualType()
    val config = visualType.config()
    val placement = location.placementForViewport(viewportClass)
    val emphasis = companionObject.visualEmphasis()
    val assetResourceName = visualType.assetResourceName()

    var entranceDone by remember(companionObject.id, companionObject.action) { mutableStateOf(false) }
    val entranceProgress = remember(companionObject.id, companionObject.action) { Animatable(0f) }
    LaunchedEffect(companionObject.id, companionObject.action) {
        entranceDone = false
        entranceProgress.snapTo(0f)
        entranceProgress.animateTo(
            targetValue = 1f,
            animationSpec = tween(durationMillis = 1200, easing = EaseOut),
        )
        entranceDone = true
    }

    val alpha: Float
    val offsetY: Float

    if (!entranceDone) {
        alpha = entranceProgress.value * config.glowAlpha
        offsetY = 10f * (1f - entranceProgress.value)
    } else {
        when (config.animationType) {
            CompanionAnimationType.Breathing -> {
                val infiniteTransition = rememberInfiniteTransition(label = "companionBreathing")
                val animatedAlpha by infiniteTransition.animateFloat(
                    initialValue = config.glowAlpha - 0.08f,
                    targetValue = config.glowAlpha + 0.06f,
                    animationSpec = infiniteRepeatable(
                        animation = tween(3500),
                        repeatMode = RepeatMode.Reverse,
                    ),
                    label = "companionAlpha",
                )
                alpha = animatedAlpha
                offsetY = 0f
            }
            CompanionAnimationType.Floating -> {
                val infiniteTransition = rememberInfiniteTransition(label = "companionFloating")
                val animatedAlpha by infiniteTransition.animateFloat(
                    initialValue = config.glowAlpha - 0.06f,
                    targetValue = config.glowAlpha + 0.05f,
                    animationSpec = infiniteRepeatable(
                        animation = tween(5000),
                        repeatMode = RepeatMode.Reverse,
                    ),
                    label = "companionAlpha",
                )
                val animatedOffset by infiniteTransition.animateFloat(
                    initialValue = -3f,
                    targetValue = 3f,
                    animationSpec = infiniteRepeatable(
                        animation = tween(5000),
                        repeatMode = RepeatMode.Reverse,
                    ),
                    label = "companionOffsetY",
                )
                alpha = animatedAlpha
                offsetY = animatedOffset
            }
        }
    }

    val scale = if (!entranceDone) {
        0.82f + 0.18f * entranceProgress.value
    } else {
        1f
    }

    return CompanionLightPointRenderState(
        placement = placement,
        visualType = visualType,
        config = config,
        emphasis = emphasis,
        assetResourceName = assetResourceName,
        assetSize = config.assetSize * emphasis.shapeScale,
        assetAlpha = companionObject.assetAlpha(alpha = alpha, baseAlpha = config.glowAlpha),
        alpha = alpha,
        offsetY = offsetY,
        scale = scale,
    )
}

internal fun CompanionVisualType.assetResourceName(): String? {
    return when (this) {
        CompanionVisualType.Star -> "companion_object_star"
        CompanionVisualType.Cloud -> "companion_object_cloud"
        CompanionVisualType.PaperBoat -> "companion_object_paper_boat"
        CompanionVisualType.TinyDoor -> "companion_object_tiny_door"
        CompanionVisualType.DinoShadow -> "companion_object_dino_shadow"
        CompanionVisualType.BlockLight -> "companion_object_block_light"
    }
}

@Composable
private fun companionObjectAssetResId(resourceName: String): Int? {
    val context = LocalContext.current
    return remember(resourceName, context) {
        context.resources
            .getIdentifier(resourceName, "drawable", context.packageName)
            .takeIf { it != 0 }
    }
}

private fun CompanionObjectMeta.assetAlpha(alpha: Float, baseAlpha: Float): Float {
    val stateAlpha = when {
        state == "active" && action == "co_create" -> 0.98f
        state == "active" && action == "recall" -> 0.78f
        state == "seed" && action == "name_seed" -> 0.88f
        else -> 0.82f
    }
    val entranceAlpha = if (baseAlpha <= 0f) 1f else (alpha / baseAlpha).coerceIn(0f, 1.06f)
    return (stateAlpha * entranceAlpha).coerceIn(0f, 1f)
}

// --- Shape drawing functions ---

private fun DrawScope.drawCompanionShape(
    type: CompanionVisualType,
    w: Float,
    h: Float,
    fill: Color,
    stroke: Color,
) {
    when (type) {
        CompanionVisualType.Star -> drawStarShape(w, h, fill, stroke)
        CompanionVisualType.Cloud -> drawCloudShape(w, h, fill, stroke)
        CompanionVisualType.PaperBoat -> drawPaperBoatShape(w, h, fill, stroke)
        CompanionVisualType.TinyDoor -> drawTinyDoorShape(w, h, fill, stroke)
        CompanionVisualType.DinoShadow -> drawDinoShadowShape(w, h, fill, stroke)
        CompanionVisualType.BlockLight -> drawBlockLightShape(w, h, fill, stroke)
    }
}

/** 五角星：5 外顶点 + 5 内顶点，圆角软化。 */
private fun DrawScope.drawStarShape(w: Float, h: Float, fill: Color, stroke: Color) {
    val cx = w / 2f
    val cy = h / 2f
    val outerR = minOf(w, h) / 2f * 0.88f
    val innerR = outerR * 0.42f
    val path = Path()
    for (i in 0 until 5) {
        val outerAngle = Math.toRadians((i * 72 - 90).toDouble())
        val innerAngle = Math.toRadians((i * 72 + 36 - 90).toDouble())
        val ox = cx + outerR * kotlin.math.cos(outerAngle).toFloat()
        val oy = cy + outerR * kotlin.math.sin(outerAngle).toFloat()
        val ix = cx + innerR * kotlin.math.cos(innerAngle).toFloat()
        val iy = cy + innerR * kotlin.math.sin(innerAngle).toFloat()
        if (i == 0) path.moveTo(ox, oy) else path.lineTo(ox, oy)
        path.lineTo(ix, iy)
    }
    path.close()
    drawPath(path, color = fill)
    drawPath(path, color = stroke, style = Stroke(width = 1.dp.toPx()))
}

/** 云朵：3 个重叠椭圆。 */
private fun DrawScope.drawCloudShape(w: Float, h: Float, fill: Color, stroke: Color) {
    val mainW = w * 0.60f
    val mainH = h * 0.52f
    val mainLeft = (w - mainW) / 2f
    val mainTop = h * 0.42f
    drawOval(
        color = fill,
        topLeft = Offset(mainLeft, mainTop),
        size = Size(mainW, mainH),
    )
    drawOval(
        color = stroke,
        topLeft = Offset(mainLeft, mainTop),
        size = Size(mainW, mainH),
        style = Stroke(width = 1.dp.toPx()),
    )
    val leftW = w * 0.38f
    val leftH = h * 0.40f
    drawOval(
        color = fill,
        topLeft = Offset(w * 0.14f, h * 0.22f),
        size = Size(leftW, leftH),
    )
    val rightW = w * 0.34f
    val rightH = h * 0.36f
    drawOval(
        color = fill,
        topLeft = Offset(w * 0.50f, h * 0.18f),
        size = Size(rightW, rightH),
    )
}

/** 小纸船：倒梯形船身 + 三角帆。 */
private fun DrawScope.drawPaperBoatShape(w: Float, h: Float, fill: Color, stroke: Color) {
    val hull = Path().apply {
        moveTo(w * 0.15f, h * 0.58f)
        lineTo(w * 0.85f, h * 0.58f)
        lineTo(w * 0.92f, h * 0.82f)
        lineTo(w * 0.08f, h * 0.82f)
        close()
    }
    drawPath(hull, color = fill)
    drawPath(hull, color = stroke, style = Stroke(width = 1.dp.toPx()))
    val sail = Path().apply {
        moveTo(w * 0.50f, h * 0.12f)
        lineTo(w * 0.50f, h * 0.58f)
        lineTo(w * 0.72f, h * 0.42f)
        close()
    }
    val sailFill = fill.copy(alpha = fill.alpha * 0.8f)
    drawPath(sail, color = sailFill)
    drawPath(sail, color = stroke, style = Stroke(width = 1.dp.toPx()))
}

/** 小门：圆角矩形 + 半圆门顶 + 小门把手。 */
private fun DrawScope.drawTinyDoorShape(w: Float, h: Float, fill: Color, stroke: Color) {
    val doorW = w * 0.72f
    val doorH = h * 0.62f
    val doorLeft = (w - doorW) / 2f
    val doorTop = h * 0.30f
    val cornerPx = 5.dp.toPx()
    drawRoundRect(
        color = fill,
        topLeft = Offset(doorLeft, doorTop),
        size = Size(doorW, doorH),
        cornerRadius = GeoCornerRadius(cornerPx, cornerPx),
    )
    drawRoundRect(
        color = stroke,
        topLeft = Offset(doorLeft, doorTop),
        size = Size(doorW, doorH),
        cornerRadius = GeoCornerRadius(cornerPx, cornerPx),
        style = Stroke(width = 1.dp.toPx()),
    )
    val archR = doorW / 2f
    drawArc(
        color = fill,
        startAngle = 180f,
        sweepAngle = 180f,
        useCenter = true,
        topLeft = Offset(doorLeft, doorTop - archR),
        size = Size(doorW, archR * 2f),
    )
    drawArc(
        color = stroke,
        startAngle = 180f,
        sweepAngle = 180f,
        useCenter = false,
        topLeft = Offset(doorLeft, doorTop - archR),
        size = Size(doorW, archR * 2f),
        style = Stroke(width = 1.dp.toPx()),
    )
    val handleR = 1.5.dp.toPx()
    val handleCx = doorLeft + doorW * 0.76f
    val handleCy = doorTop + doorH * 0.52f
    drawCircle(
        color = stroke,
        radius = handleR,
        center = Offset(handleCx, handleCy),
    )
}

/** 小恐龙影子：极简圆润轮廓（身体 + 头 + 短尾巴），无眼睛、无表情、无背脊装饰。 */
private fun DrawScope.drawDinoShadowShape(w: Float, h: Float, fill: Color, stroke: Color) {
    val bodyW = w * 0.56f
    val bodyH = h * 0.50f
    val bodyLeft = w * 0.16f
    val bodyTop = h * 0.38f
    drawOval(
        color = fill,
        topLeft = Offset(bodyLeft, bodyTop),
        size = Size(bodyW, bodyH),
    )
    drawOval(
        color = stroke,
        topLeft = Offset(bodyLeft, bodyTop),
        size = Size(bodyW, bodyH),
        style = Stroke(width = 1.dp.toPx()),
    )
    val headR = w * 0.17f
    val headCx = w * 0.68f
    val headCy = h * 0.30f
    drawCircle(
        color = fill,
        radius = headR,
        center = Offset(headCx, headCy),
    )
    drawCircle(
        color = stroke,
        radius = headR,
        center = Offset(headCx, headCy),
        style = Stroke(width = 1.dp.toPx()),
    )
    val tail = Path().apply {
        moveTo(bodyLeft + bodyW * 0.08f, bodyTop + bodyH * 0.55f)
        cubicTo(
            w * 0.06f, h * 0.62f,
            w * 0.02f, h * 0.44f,
            w * 0.08f, h * 0.32f,
        )
    }
    drawPath(tail, color = stroke, style = Stroke(width = 1.5.dp.toPx()))
}

/** 小积木光点：圆角正方形。 */
private fun DrawScope.drawBlockLightShape(w: Float, h: Float, fill: Color, stroke: Color) {
    val blockW = w * 0.78f
    val blockH = h * 0.78f
    val left = (w - blockW) / 2f
    val top = (h - blockH) / 2f
    val cornerPx = 5.dp.toPx()
    drawRoundRect(
        color = fill,
        topLeft = Offset(left, top),
        size = Size(blockW, blockH),
        cornerRadius = GeoCornerRadius(cornerPx, cornerPx),
    )
    drawRoundRect(
        color = stroke,
        topLeft = Offset(left, top),
        size = Size(blockW, blockH),
        cornerRadius = GeoCornerRadius(cornerPx, cornerPx),
        style = Stroke(width = 1.dp.toPx()),
    )
    val nubW = blockW * 0.36f
    val nubH = 2.5.dp.toPx()
    val nubLeft = left + (blockW - nubW) / 2f
    val nubCornerPx = 1.5.dp.toPx()
    drawRoundRect(
        color = fill,
        topLeft = Offset(nubLeft, top - nubH - 1.dp.toPx()),
        size = Size(nubW, nubH),
        cornerRadius = GeoCornerRadius(nubCornerPx, nubCornerPx),
    )
}
