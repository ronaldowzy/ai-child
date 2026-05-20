package com.childai.companion.ui.chat

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import com.childai.companion.config.DevSettings
import com.childai.companion.mascot.AssetManifestLoader
import com.childai.companion.mascot.FrameBitmapCache
import com.childai.companion.mascot.FrameSequencePlayer
import com.childai.companion.mascot.MascotController
import com.childai.companion.mascot.MascotState

@Composable
fun CartoonAgentView(
    agent: FoxAgentUiState,
    modifier: Modifier = Modifier,
    debugMascotState: MascotState? = null,
) {
    val context = LocalContext.current
    val renderMode = DevSettings.FOX_RENDER_MODE.lowercase()
    val useAnimation = DevSettings.FOX_ANIMATION_ENABLED &&
        (renderMode == "animation_v1" || renderMode == "auto")
    val manifestLoader = remember(context) {
        AssetManifestLoader(context.assets)
    }
    val manifest = remember(manifestLoader) {
        manifestLoader.loadManifestOrNull()
    }
    val mascotController = remember(manifest) {
        MascotController(manifest)
    }
    var completedShortState by remember { mutableStateOf<MascotState?>(null) }
    val baseMascotState = debugMascotState ?: mascotController.stateFor(agent)
    val requestedMascotState = if (completedShortState == baseMascotState) {
        MascotState.Idle
    } else {
        baseMascotState
    }
    val frameSequence = remember(useAnimation, requestedMascotState, manifest) {
        if (useAnimation && manifest != null) {
            manifestLoader.loadFrameSequenceOrNull(requestedMascotState, manifest)
        } else {
            null
        }
    }
    val bitmapCache = remember(context) {
        FrameBitmapCache(
            assetManager = context.assets,
            sampleSize = if (DevSettings.FOX_ANIMATION_LOW_PERFORMANCE_MODE) {
                FrameBitmapCache.LOW_PERFORMANCE_SAMPLE_SIZE
            } else {
                FrameBitmapCache.DEFAULT_SAMPLE_SIZE
            },
        )
    }
    val lift by animateFloatAsState(
        targetValue = if (agent.motion == FoxMotion.CelebrateSmall) -10f else 0f,
        animationSpec = tween(durationMillis = 360),
        label = "foxLift",
    )
    Box(
        modifier = modifier
            .fillMaxWidth(0.88f)
            .sizeIn(minWidth = 160.dp, maxWidth = 420.dp)
            .aspectRatio(1f),
    ) {
        if (frameSequence != null) {
            FrameSequencePlayer(
                sequence = frameSequence,
                bitmapCache = bitmapCache,
                modifier = Modifier
                    .matchParentSize()
                    .graphicsLayer { translationY = lift },
                onAnimationFinished = { finishedState ->
                    completedShortState = finishedState
                },
                fallback = {
                    StaticFoxAgentView(
                        agent = agent,
                        lift = lift,
                        forceCanvas = renderMode == "canvas",
                    )
                },
            )
        } else {
            StaticFoxAgentView(
                agent = agent,
                lift = lift,
                forceCanvas = renderMode == "canvas",
            )
        }
    }
}

@Composable
private fun BoxScope.StaticFoxAgentView(
    agent: FoxAgentUiState,
    lift: Float,
    forceCanvas: Boolean,
) {
    val mode = if (forceCanvas) "canvas" else DevSettings.FOX_ASSET_MODE
    when (val asset = FoxAgentAssetMapper.resolve(agent, assetMode = mode)) {
        is FoxAgentAsset.Drawable -> {
            Image(
                painter = painterResource(id = asset.resId),
                contentDescription = "小白狐",
                contentScale = ContentScale.Fit,
                modifier = Modifier
                    .matchParentSize()
                    .graphicsLayer { translationY = lift },
            )
        }

        FoxAgentAsset.CanvasFallback -> {
            Canvas(modifier = Modifier.matchParentSize()) {
                drawFoxAgent(agent = agent, verticalOffset = lift)
            }
        }
    }
}

private fun DrawScope.drawFoxAgent(
    agent: FoxAgentUiState,
    verticalOffset: Float,
) {
    val center = Offset(size.width / 2f, size.height / 2f + verticalOffset)
    val foxOrange = when (agent.mood) {
        FoxMood.Calm -> Color(0xFFD49A68)
        FoxMood.Thinking -> Color(0xFFD88945)
        FoxMood.Listening -> Color(0xFFE0964F)
        FoxMood.Encouraging -> Color(0xFFE28C3D)
        FoxMood.Warm -> Color(0xFFD88945)
        FoxMood.Sleepy -> Color(0xFFC68F72)
        FoxMood.SafetyConcern -> Color(0xFFC7835E)
        FoxMood.PrivacyBoundary -> Color(0xFFD09255)
        FoxMood.HomeworkFocus -> Color(0xFFD88945)
        FoxMood.NetworkError -> Color(0xFFC68F72)
    }
    val foxCream = Color(0xFFFFF1DD)
    val foxBrown = Color(0xFF604230)
    val leafGreen = when (agent.mood) {
        FoxMood.Calm -> Color(0xFF66816B)
        FoxMood.Thinking -> Color(0xFF536F77)
        FoxMood.Listening -> Color(0xFF5B7C5A)
        FoxMood.Encouraging -> Color(0xFF6D7F43)
        FoxMood.Warm -> Color(0xFF5B7C5A)
        FoxMood.Sleepy -> Color(0xFF6F7891)
        FoxMood.SafetyConcern -> Color(0xFF6C746A)
        FoxMood.PrivacyBoundary -> Color(0xFF536F77)
        FoxMood.HomeworkFocus -> Color(0xFF536F77)
        FoxMood.NetworkError -> Color(0xFF6F7891)
    }
    val softShadow = Color(0x263E4D39)
    val eyeHeight = if (agent.motion == FoxMotion.ThinkingBlink) {
        size.minDimension * 0.010f
    } else {
        size.minDimension * 0.026f
    }
    val mouthSweep = if (agent.mood == FoxMood.Calm) 96f else 132f
    val tailLift = if (agent.motion == FoxMotion.ListeningTail) -0.03f else 0f

    drawOval(
        color = softShadow,
        topLeft = Offset(size.width * 0.18f, size.height * 0.78f),
        size = Size(size.width * 0.64f, size.height * 0.10f),
    )

    drawCircle(
        color = foxOrange,
        radius = size.minDimension * 0.31f,
        center = Offset(center.x, size.height * 0.47f + verticalOffset),
    )

    drawEar(
        outerColor = foxOrange,
        innerColor = foxCream,
        points = listOf(
            Offset(size.width * 0.25f, size.height * 0.36f + verticalOffset),
            Offset(size.width * 0.33f, size.height * 0.12f + verticalOffset),
            Offset(size.width * 0.47f, size.height * 0.33f + verticalOffset),
        ),
    )
    drawEar(
        outerColor = foxOrange,
        innerColor = foxCream,
        points = listOf(
            Offset(size.width * 0.75f, size.height * 0.36f + verticalOffset),
            Offset(size.width * 0.67f, size.height * 0.12f + verticalOffset),
            Offset(size.width * 0.53f, size.height * 0.33f + verticalOffset),
        ),
    )

    drawOval(
        color = foxCream,
        topLeft = Offset(size.width * 0.31f, size.height * 0.45f + verticalOffset),
        size = Size(size.width * 0.38f, size.height * 0.28f),
    )

    drawOval(
        color = foxBrown,
        topLeft = Offset(
            size.width * 0.41f - size.minDimension * 0.026f,
            size.height * 0.44f - eyeHeight / 2f + verticalOffset,
        ),
        size = Size(size.minDimension * 0.052f, eyeHeight),
    )
    drawOval(
        color = foxBrown,
        topLeft = Offset(
            size.width * 0.59f - size.minDimension * 0.026f,
            size.height * 0.44f - eyeHeight / 2f + verticalOffset,
        ),
        size = Size(size.minDimension * 0.052f, eyeHeight),
    )

    drawCircle(
        color = foxBrown,
        radius = size.minDimension * 0.022f,
        center = Offset(size.width * 0.50f, size.height * 0.53f + verticalOffset),
    )
    drawArc(
        color = foxBrown,
        startAngle = 24f,
        sweepAngle = mouthSweep,
        useCenter = false,
        topLeft = Offset(size.width * 0.43f, size.height * 0.53f + verticalOffset),
        size = Size(size.width * 0.14f, size.height * 0.10f),
        style = Stroke(width = size.minDimension * 0.012f),
    )

    drawRoundRect(
        color = leafGreen,
        topLeft = Offset(size.width * 0.37f, size.height * (0.68f + tailLift) + verticalOffset),
        size = Size(size.width * 0.26f, size.height * 0.10f),
        cornerRadius = androidx.compose.ui.geometry.CornerRadius(
            x = size.minDimension * 0.04f,
            y = size.minDimension * 0.04f,
        ),
    )
}

private fun DrawScope.drawEar(
    outerColor: Color,
    innerColor: Color,
    points: List<Offset>,
) {
    val outerPath = Path().apply {
        moveTo(points[0].x, points[0].y)
        lineTo(points[1].x, points[1].y)
        lineTo(points[2].x, points[2].y)
        close()
    }
    drawPath(path = outerPath, color = outerColor)

    val innerPath = Path().apply {
        moveTo((points[0].x + points[1].x) / 2f, (points[0].y + points[1].y) / 2f)
        lineTo(points[1].x, points[1].y + size.height * 0.05f)
        lineTo((points[1].x + points[2].x) / 2f, (points[1].y + points[2].y) / 2f)
        close()
    }
    drawPath(path = innerPath, color = innerColor)
}
