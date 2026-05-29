package com.childai.companion.ui.chat

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateColorAsState
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
import androidx.compose.ui.draw.blur
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.childai.companion.mascot.MascotState

/**
 * Companion stage for the Little White Fox.
 *
 * Wraps background gradient, state glow, animated fox, and state bubble
 * into a single visual unit. Does NOT own business logic, voice recording,
 * prompt, or parent report logic.
 */
@Composable
fun XiaobaohuCompanionStage(
    agent: FoxAgentUiState,
    mascotState: MascotState,
    compactLandscape: Boolean,
    modifier: Modifier = Modifier,
    debugMascotState: MascotState? = null,
) {
    val glowColor by animateColorAsState(
        targetValue = mascotState.glowColor(),
        animationSpec = tween(durationMillis = 600),
        label = "stageGlowColor",
    )

    BoxWithConstraints(modifier = modifier) {
        val mascotMaxSize = minOf(
            maxWidth * if (compactLandscape) 0.94f else 0.98f,
            (maxHeight * if (compactLandscape) 0.86f else 0.80f).coerceAtLeast(190.dp),
            if (compactLandscape) 560.dp else 520.dp,
        )
        val mascotOffsetY = if (compactLandscape) 34.dp else 42.dp
        val visualScaleMultiplier = if (compactLandscape) 1.38f else 1.20f

        Box(modifier = Modifier.fillMaxSize()) {
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
                        x = if (compactLandscape) (-20).dp else (-14).dp,
                        y = if (compactLandscape) (-84).dp else (-72).dp,
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
