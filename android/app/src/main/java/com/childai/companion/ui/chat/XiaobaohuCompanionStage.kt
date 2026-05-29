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
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.sizeIn
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
        val statusReserve = if (compactLandscape) 64.dp else 86.dp
        val stageShape = RoundedCornerShape(if (compactLandscape) 24.dp else 32.dp)
        val mascotMaxSize = minOf(
            maxWidth,
            (maxHeight - statusReserve).coerceAtLeast(160.dp),
            if (compactLandscape) 340.dp else 470.dp,
        )

        Surface(
            modifier = Modifier.fillMaxSize(),
            color = Color.Transparent,
            shape = stageShape,
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(
                        Brush.verticalGradient(
                            colors = listOf(
                                Color.White.copy(alpha = 0.18f),
                                Color(0xFFFFFDF8).copy(alpha = 0.28f),
                                Color(0xFFFFF2D8).copy(alpha = 0.22f),
                            ),
                        ),
                        shape = stageShape,
                    )
                    .border(
                        width = 1.dp,
                        color = Color.White.copy(alpha = 0.28f),
                        shape = stageShape,
                    ),
            )

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(if (compactLandscape) 8.dp else 14.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Box(contentAlignment = Alignment.Center) {
                    // Glow effect behind fox
                    Box(
                        modifier = Modifier
                            .sizeIn(
                                maxWidth = mascotMaxSize * 0.75f,
                                maxHeight = mascotMaxSize * 0.75f,
                            )
                            .blur(radius = 36.dp)
                            .background(
                                Brush.radialGradient(
                                    colors = listOf(
                                        glowColor.copy(alpha = 0.30f),
                                        glowColor.copy(alpha = 0.0f),
                                    ),
                                ),
                                shape = CircleShape,
                            ),
                    )
                    // Fox animation
                    CartoonAgentView(
                        agent = agent,
                        debugMascotState = debugMascotState,
                        modifier = Modifier.sizeIn(
                            maxWidth = mascotMaxSize,
                            maxHeight = mascotMaxSize,
                        ),
                    )
                }

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
                        slideInVertically(animationSpec = tween(durationMillis = 220)) { it / 5 } +
                        scaleIn(animationSpec = tween(durationMillis = 220), initialScale = 0.96f),
                    exit = fadeOut(animationSpec = tween(durationMillis = 180)) +
                        slideOutVertically(animationSpec = tween(durationMillis = 180)) { it / 5 } +
                        scaleOut(animationSpec = tween(durationMillis = 180), targetScale = 0.96f),
                ) {
                    renderedBubbleText?.let { text ->
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                        ) {
                            Spacer(modifier = Modifier.height(if (compactLandscape) 6.dp else 10.dp))
                            XiaobaohuStateBubble(
                                text = text,
                                compactLandscape = compactLandscape,
                            )
                        }
                    }
                }
            }
        }
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
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(18.dp),
        color = Color.White.copy(alpha = 0.84f),
        shadowElevation = 1.dp,
        border = BorderStroke(
            width = 1.dp,
            color = Color.White.copy(alpha = 0.54f),
        ),
    ) {
        Text(
            text = text,
            modifier = Modifier.padding(
                horizontal = if (compactLandscape) 8.dp else 12.dp,
                vertical = if (compactLandscape) 4.dp else 6.dp,
            ),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.8f),
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            textAlign = TextAlign.Center,
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
        MascotState.Idle -> "我在这里。"
        MascotState.WaitingSoft -> "想说的时候再说。"
        MascotState.Listening -> "我在听。"
        MascotState.Thinking -> "我想一想。"
        MascotState.PreparingSpeech -> "我准备说。"
        MascotState.Speaking -> null
        MascotState.ImageViewing -> "我正在看。"
        MascotState.CoCreate -> "我们一起想想。"
        MascotState.Paused -> "好，我们先停一下。"
        MascotState.Retry -> "这次没弄好，可以再试一次。"
    }
}
