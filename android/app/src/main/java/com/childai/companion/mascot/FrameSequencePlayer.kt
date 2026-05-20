package com.childai.companion.mascot

import androidx.compose.foundation.Image
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import kotlinx.coroutines.delay

@Composable
fun FrameSequencePlayer(
    sequence: FrameSequenceUiState,
    bitmapCache: FrameBitmapCache,
    modifier: Modifier = Modifier,
    onAnimationFinished: (MascotState) -> Unit = {},
    fallback: @Composable () -> Unit = {},
) {
    if (sequence.framePaths.isEmpty()) {
        fallback()
        return
    }
    var frameIndex by remember(sequence.key) { mutableIntStateOf(0) }
    val frameDelayMs = (1000L / sequence.fps.coerceAtLeast(1)).coerceAtLeast(16L)

    LaunchedEffect(sequence.key) {
        frameIndex = 0
        var loopsCompleted = 0
        while (true) {
            delay(frameDelayMs)
            val nextFrame = frameIndex + 1
            if (nextFrame < sequence.framePaths.size) {
                frameIndex = nextFrame
                continue
            }

            when (sequence.animationType) {
                MascotAnimationType.Loop -> frameIndex = 0
                MascotAnimationType.OneShotHold -> {
                    frameIndex = sequence.framePaths.lastIndex
                    onAnimationFinished(sequence.state)
                    break
                }
                MascotAnimationType.ShortLoop -> {
                    loopsCompleted += 1
                    if (loopsCompleted >= SHORT_LOOP_COUNT) {
                        frameIndex = sequence.framePaths.lastIndex
                        onAnimationFinished(sequence.state)
                        break
                    } else {
                        frameIndex = 0
                    }
                }
            }
        }
    }

    val path = sequence.framePaths[frameIndex.coerceIn(sequence.framePaths.indices)]
    val image = remember(path) { bitmapCache.load(path) }
    if (image != null) {
        Image(
            bitmap = image,
            contentDescription = "小白狐",
            contentScale = ContentScale.Fit,
            modifier = modifier,
        )
    } else {
        fallback()
    }
}

private const val SHORT_LOOP_COUNT = 2
