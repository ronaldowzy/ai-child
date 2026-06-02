package com.childai.companion.ui.chat

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.childai.companion.config.DevSettings
import com.childai.companion.voice.TtsUiState

@Composable
fun InputBar(
    onSend: (String) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    voice: VoiceUiState = VoiceUiState(),
    tts: TtsUiState = TtsUiState(),
    presentation: ChildInteractionPresentation = childInteractionPresentation(
        voice = voice,
        tts = tts,
        isSending = !enabled,
    ),
    onStopTts: () -> Unit = {},
    onToggleTtsMuted: () -> Unit = {},
    onOpenTtsSettings: () -> Unit = {},
    onInstallTtsData: () -> Unit = {},
    onOpenImageInput: (String) -> Unit = {},
    playfulControls: Boolean = false,
    playfulCompactControls: Boolean = false,
) {
    val context = LocalContext.current
    var draft by rememberSaveable { mutableStateOf("") }
    val trimmedDraft = draft.trim()
    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission(),
    ) { isGranted ->
        if (isGranted) {
            voice.actions.onStartRecording(context.cacheDir)
        } else {
            voice.actions.onPermissionDenied()
        }
    }
    fun startVoiceRecordingWithPermission() {
        val isGranted = ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.RECORD_AUDIO,
        ) == PackageManager.PERMISSION_GRANTED
        if (isGranted) {
            voice.actions.onStartRecording(context.cacheDir)
        } else {
            permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
        }
    }

    fun sendDraft() {
        if (enabled && !voice.hasPendingTranscript && trimmedDraft.isNotEmpty()) {
            onSend(trimmedDraft)
            draft = ""
        }
    }

    val useChildVoiceFirstInput = inputBarUsesChildVoiceFirstInput()
    val interactionPresentation = presentation
    val shouldAutoSendPendingTranscript = inputBarShouldAutoSendHiddenPendingTranscript(
        useChildVoiceFirstInput = useChildVoiceFirstInput,
        enabled = enabled,
        hasPendingTranscript = voice.hasPendingTranscript,
        pendingTranscript = voice.pendingTranscript,
    )

    LaunchedEffect(shouldAutoSendPendingTranscript, voice.pendingTranscript) {
        if (shouldAutoSendPendingTranscript) {
            voice.actions.onSendPendingTranscript()
        }
    }

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        if (inputBarShouldShowPendingTranscriptPanel(useChildVoiceFirstInput, voice.hasPendingTranscript)) {
            PendingVoiceTranscriptPanel(
                transcript = voice.pendingTranscript,
                errorMessage = voice.errorMessage,
                enabled = enabled,
                onTranscriptChange = voice.actions.onPendingTranscriptChange,
                onSend = voice.actions.onSendPendingTranscript,
                onResay = { startVoiceRecordingWithPermission() },
                onCancel = voice.actions.onCancelVoiceInput,
            )
        }
        if (useChildVoiceFirstInput) {
            if (playfulControls) {
                PlayfulVoiceFirstControls(
                    primaryText = inputBarPrimaryVoiceButtonText(interactionPresentation),
                    primaryEnabled = enabled && interactionPresentation.primaryButtonEnabled,
                    onPrimaryClick = {
                        if (voice.isRecording) {
                            voice.actions.onStopRecordingAndUpload()
                        } else {
                            startVoiceRecordingWithPermission()
                        }
                    },
                    imageAction = InputBarPlayfulAction(
                        text = "给小白狐看看",
                        icon = InputBarPlayfulIcon.Camera,
                        enabled = interactionPresentation.showImageInput &&
                            enabled &&
                            !voice.isRecording &&
                            !voice.isUploading,
                        visible = interactionPresentation.showImageInput,
                        onClick = { onOpenImageInput(IMAGE_PURPOSE_SHARE) },
                    ),
                    topicAction = InputBarPlayfulAction(
                        text = "换个话题",
                        icon = InputBarPlayfulIcon.Umbrella,
                        enabled = inputBarShouldShowTopicShift(useChildVoiceFirstInput, interactionPresentation) &&
                            enabled &&
                            !voice.isRecording &&
                            !voice.isUploading,
                        visible = inputBarShouldShowTopicShift(useChildVoiceFirstInput, interactionPresentation),
                        onClick = { onSend("换个话题") },
                    ),
                    stopAction = InputBarPlayfulAction(
                        text = "停一下",
                        icon = InputBarPlayfulIcon.Rest,
                        enabled = interactionPresentation.showStopSpeaking && enabled,
                        visible = true,
                        onClick = onStopTts,
                    ),
                    muteAction = InputBarPlayfulAction(
                        text = inputBarMuteToggleText(tts),
                        icon = InputBarPlayfulIcon.Rest,
                        enabled = inputBarShouldShowMuteToggle(useChildVoiceFirstInput, interactionPresentation) &&
                            enabled,
                        visible = inputBarShouldShowMuteToggle(useChildVoiceFirstInput, interactionPresentation),
                        onClick = onToggleTtsMuted,
                    ),
                    forceCompact = playfulCompactControls,
                )
            } else {
                Button(
                    onClick = {
                        if (voice.isRecording) {
                            voice.actions.onStopRecordingAndUpload()
                        } else {
                            startVoiceRecordingWithPermission()
                        }
                    },
                    enabled = enabled && interactionPresentation.primaryButtonEnabled,
                    shape = RoundedCornerShape(28.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF89BDF4),
                        contentColor = Color.White,
                        disabledContainerColor = Color(0xFFBFD7FF).copy(alpha = 0.56f),
                        disabledContentColor = Color.White.copy(alpha = 0.76f),
                    ),
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(min = 64.dp),
                ) {
                    Text(
                        text = inputBarPrimaryVoiceButtonText(interactionPresentation),
                        style = MaterialTheme.typography.titleMedium,
                    )
                }
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    if (interactionPresentation.showImageInput) {
                        InputBarSecondaryButton(
                            onClick = { onOpenImageInput(IMAGE_PURPOSE_SHARE) },
                            enabled = enabled && !voice.isRecording && !voice.isUploading,
                            text = "给小白狐看看",
                        )
                    }
                    if (inputBarShouldShowTopicShift(useChildVoiceFirstInput, interactionPresentation)) {
                        InputBarSecondaryButton(
                            onClick = { onSend("换个话题") },
                            enabled = enabled && !voice.isRecording && !voice.isUploading,
                            text = "换个话题",
                        )
                    }
                    if (interactionPresentation.showStopSpeaking) {
                        InputBarSecondaryButton(
                            onClick = onStopTts,
                            enabled = enabled,
                            text = "停一下",
                        )
                    }
                    if (inputBarShouldShowMuteToggle(useChildVoiceFirstInput, interactionPresentation)) {
                        InputBarSecondaryButton(
                            onClick = onToggleTtsMuted,
                            enabled = enabled,
                            text = inputBarMuteToggleText(tts),
                        )
                    }
                }
            }
        } else {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                OutlinedTextField(
                    value = draft,
                    onValueChange = { draft = it },
                    enabled = enabled && !voice.hasPendingTranscript,
                    modifier = Modifier.weight(1f),
                    placeholder = {
                        Text(text = "想说什么都可以")
                    },
                    textStyle = MaterialTheme.typography.bodyLarge,
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                    keyboardActions = KeyboardActions(onSend = { sendDraft() }),
                )
                TextButton(
                    onClick = {
                        if (voice.isRecording) {
                            voice.actions.onStopRecordingAndUpload()
                        } else {
                            startVoiceRecordingWithPermission()
                        }
                    },
                    enabled = enabled && !voice.isUploading,
                    modifier = Modifier.widthIn(min = 64.dp),
                ) {
                    Text(text = if (voice.isRecording) "说完了" else "语音说")
                }
                Button(
                    onClick = { sendDraft() },
                    enabled = enabled && !voice.hasPendingTranscript && trimmedDraft.isNotEmpty(),
                    modifier = Modifier.widthIn(min = 88.dp),
                ) {
                    Text(text = if (enabled) "发送" else "发送中…")
                }
            }
        }
        if (!useChildVoiceFirstInput) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = interactionPresentation.statusText,
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.weight(1f),
                )
                if (interactionPresentation.showStopSpeaking) {
                    TextButton(onClick = onStopTts) {
                        Text(text = "停一下")
                    }
                }
                if (inputBarShouldShowResayAction(useChildVoiceFirstInput, voice.inputMode)) {
                    TextButton(
                        onClick = { startVoiceRecordingWithPermission() },
                        enabled = enabled && !voice.isUploading,
                    ) {
                        Text(text = "重新说")
                    }
                }
                if (inputBarShouldShowCancelAction(useChildVoiceFirstInput, voice.inputMode)) {
                    TextButton(onClick = voice.actions.onCancelVoiceInput) {
                        Text(text = "先不发")
                    }
                }
                if (inputBarShouldShowMuteToggle(useChildVoiceFirstInput, interactionPresentation)) {
                    TextButton(onClick = onToggleTtsMuted) {
                        Text(text = inputBarMuteToggleText(tts))
                    }
                }
            }
            if (tts.needsSystemSetup) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    TextButton(onClick = onOpenTtsSettings) {
                        Text(text = "检查声音设置")
                    }
                    TextButton(onClick = onInstallTtsData) {
                        Text(text = "安装声音数据")
                    }
                }
            }
            if (DevSettings.SHOW_TTS_DIAGNOSTICS && tts.diagnosticText.isNotBlank()) {
                Text(
                    text = "朗读诊断：${tts.diagnosticText}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 2,
                )
            }
        }
    }
}

@Composable
private fun InputBarSecondaryButton(
    text: String,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    OutlinedButton(
        onClick = onClick,
        enabled = enabled,
        shape = RoundedCornerShape(22.dp),
        colors = ButtonDefaults.outlinedButtonColors(
            containerColor = Color.White.copy(alpha = 0.66f),
            contentColor = Color(0xFF42546A),
            disabledContainerColor = Color.White.copy(alpha = 0.36f),
            disabledContentColor = Color(0xFF42546A).copy(alpha = 0.45f),
        ),
        border = BorderStroke(
            width = 1.dp,
            color = Color.White.copy(alpha = 0.62f),
        ),
        modifier = Modifier.heightIn(min = 44.dp),
    ) {
        Text(text = text)
    }
}

private data class InputBarPlayfulAction(
    val text: String,
    val icon: InputBarPlayfulIcon,
    val enabled: Boolean,
    val visible: Boolean,
    val onClick: () -> Unit,
)

private enum class InputBarPlayfulIcon {
    Microphone,
    Camera,
    Umbrella,
    Rest,
}

@Composable
private fun PlayfulVoiceFirstControls(
    primaryText: String,
    primaryEnabled: Boolean,
    onPrimaryClick: () -> Unit,
    imageAction: InputBarPlayfulAction,
    topicAction: InputBarPlayfulAction,
    stopAction: InputBarPlayfulAction,
    muteAction: InputBarPlayfulAction,
    forceCompact: Boolean = false,
) {
    val visibleImage = imageAction.takeIf { it.visible }
    val visibleTopic = topicAction.takeIf { it.visible }
    val visibleStop = stopAction.takeIf { it.visible }
    val visibleMute = muteAction.takeIf { it.visible }
    val topAction = if (visibleStop != null && visibleImage != null) visibleImage else null
    val leftAction = visibleTopic ?: visibleImage.takeUnless { it == topAction }
    val rightAction = visibleStop
        ?: visibleImage.takeUnless { it == topAction || it == leftAction }
        ?: visibleMute.takeUnless { it == leftAction }

    BoxWithConstraints(modifier = Modifier.fillMaxWidth()) {
        val compact = forceCompact || maxWidth < 350.dp
        val extraCompact = maxWidth < 330.dp || (forceCompact && maxWidth < 380.dp)
        val primarySize = when {
            extraCompact -> 92.dp
            compact -> 102.dp
            else -> 116.dp
        }
        val secondarySize = when {
            extraCompact -> 76.dp
            compact -> 84.dp
            else -> 96.dp
        }
        val secondaryIconSize = when {
            extraCompact -> 32.dp
            compact -> 36.dp
            else -> 42.dp
        }
        val cameraMinWidth = when {
            extraCompact -> 128.dp
            compact -> 142.dp
            else -> 168.dp
        }
        val cameraIconSize = when {
            extraCompact -> 36.dp
            compact -> 40.dp
            else -> 46.dp
        }
        val rowGap = when {
            extraCompact -> 6.dp
            compact -> 8.dp
            else -> 12.dp
        }

        Column(
            modifier = Modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            if (topAction != null) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End,
                ) {
                    PlayfulCameraPill(
                        action = topAction,
                        minWidth = cameraMinWidth,
                        iconSize = cameraIconSize,
                    )
                }
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.Bottom,
            ) {
                PlayfulSecondaryControlButton(
                    action = leftAction,
                    buttonSize = secondarySize,
                    iconSize = secondaryIconSize,
                    modifier = Modifier.weight(1f),
                )
                Spacer(modifier = Modifier.width(rowGap))
                PlayfulPrimaryVoiceButton(
                    text = primaryText,
                    enabled = primaryEnabled,
                    size = primarySize,
                    iconSize = when {
                        extraCompact -> 44.dp
                        compact -> 48.dp
                        else -> 54.dp
                    },
                    onClick = onPrimaryClick,
                )
                Spacer(modifier = Modifier.width(rowGap))
                PlayfulSecondaryControlButton(
                    action = rightAction,
                    buttonSize = secondarySize,
                    iconSize = secondaryIconSize,
                    modifier = Modifier.weight(1f),
                )
            }
        }
    }
}

@Composable
private fun PlayfulPrimaryVoiceButton(
    text: String,
    enabled: Boolean,
    size: Dp,
    iconSize: Dp,
    onClick: () -> Unit,
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Button(
            onClick = onClick,
            enabled = enabled,
            shape = CircleShape,
            colors = ButtonDefaults.buttonColors(
                containerColor = Color(0xFF7DB5F4),
                contentColor = Color.White,
                disabledContainerColor = Color(0xFFBFD7FF).copy(alpha = 0.58f),
                disabledContentColor = Color.White.copy(alpha = 0.78f),
            ),
            elevation = ButtonDefaults.buttonElevation(
                defaultElevation = 8.dp,
                pressedElevation = 3.dp,
                disabledElevation = 0.dp,
            ),
            border = BorderStroke(
                width = 7.dp,
                color = Color.White.copy(alpha = 0.72f),
            ),
            contentPadding = PaddingValues(0.dp),
            modifier = Modifier.size(size),
        ) {
            InputBarControlIcon(
                icon = InputBarPlayfulIcon.Microphone,
                color = Color.White,
                modifier = Modifier.size(iconSize),
            )
        }
        Text(
            text = text,
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.SemiBold,
            color = Color(0xFF5B5560).copy(alpha = 0.86f),
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(top = 6.dp),
        )
    }
}

@Composable
private fun PlayfulSecondaryControlButton(
    action: InputBarPlayfulAction?,
    buttonSize: Dp,
    iconSize: Dp,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier,
        contentAlignment = Alignment.Center,
    ) {
        if (action != null) {
            val contentColor = if (action.enabled) Color(0xFF42546A) else Color(0xFF42546A).copy(alpha = 0.48f)
            Box(
                modifier = Modifier
                    .size(buttonSize)
                    .clip(CircleShape)
                    .background(
                        if (action.enabled) {
                            Color(0xFFFFFEFA).copy(alpha = 0.97f)
                        } else {
                            Color(0xFFFFFEFA).copy(alpha = 0.78f)
                        },
                    )
                    .border(
                        width = 1.dp,
                        color = Color.White.copy(alpha = 0.88f),
                        shape = CircleShape,
                    )
                    .noRippleClick(
                        enabled = action.enabled,
                        onClick = action.onClick,
                    ),
                contentAlignment = Alignment.Center,
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                    modifier = Modifier.padding(horizontal = 6.dp),
                ) {
                    InputBarControlIcon(
                        icon = action.icon,
                        color = if (action.enabled) Color(0xFF6EADEB) else Color(0xFF9FB7CC),
                        modifier = Modifier.size(iconSize),
                    )
                    Text(
                        text = action.text,
                        style = MaterialTheme.typography.labelMedium,
                        color = contentColor,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.padding(top = 6.dp),
                    )
                }
            }
        }
    }
}

@Composable
private fun PlayfulCameraPill(action: InputBarPlayfulAction) {
    PlayfulCameraPill(
        action = action,
        minWidth = 168.dp,
        iconSize = 46.dp,
    )
}

@Composable
private fun PlayfulCameraPill(
    action: InputBarPlayfulAction,
    minWidth: Dp,
    iconSize: Dp,
) {
    val shape = RoundedCornerShape(38.dp)
    Box(
        modifier = Modifier
            .clip(shape)
            .background(
                if (action.enabled) {
                    Color(0xFFFFFEFA).copy(alpha = 0.97f)
                } else {
                    Color(0xFFFFFEFA).copy(alpha = 0.78f)
                },
            )
            .border(
                width = 1.dp,
                color = Color.White.copy(alpha = 0.76f),
                shape = shape,
            )
            .noRippleClick(
                enabled = action.enabled,
                onClick = action.onClick,
            ),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            modifier = Modifier
                .widthIn(min = minWidth)
                .padding(horizontal = 18.dp, vertical = 12.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            InputBarControlIcon(
                icon = action.icon,
                color = Color(0xFF6EADEB),
                modifier = Modifier.size(iconSize),
            )
            Text(
                text = action.text,
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.SemiBold,
                color = if (action.enabled) Color(0xFF42546A) else Color(0xFF42546A).copy(alpha = 0.48f),
                modifier = Modifier.padding(top = 4.dp),
            )
        }
    }
}

@Composable
private fun Modifier.noRippleClick(
    enabled: Boolean,
    onClick: () -> Unit,
): Modifier {
    val interactionSource = remember { MutableInteractionSource() }
    return clickable(
        enabled = enabled,
        interactionSource = interactionSource,
        indication = null,
        onClick = onClick,
    )
}

private fun ovalPath(
    center: Offset,
    radiusX: Float,
    radiusY: Float,
): Path {
    return Path().apply {
        val c = 0.55228475f
        moveTo(center.x + radiusX, center.y)
        cubicTo(
            center.x + radiusX,
            center.y + radiusY * c,
            center.x + radiusX * c,
            center.y + radiusY,
            center.x,
            center.y + radiusY,
        )
        cubicTo(
            center.x - radiusX * c,
            center.y + radiusY,
            center.x - radiusX,
            center.y + radiusY * c,
            center.x - radiusX,
            center.y,
        )
        cubicTo(
            center.x - radiusX,
            center.y - radiusY * c,
            center.x - radiusX * c,
            center.y - radiusY,
            center.x,
            center.y - radiusY,
        )
        cubicTo(
            center.x + radiusX * c,
            center.y - radiusY,
            center.x + radiusX,
            center.y - radiusY * c,
            center.x + radiusX,
            center.y,
        )
        close()
    }
}

@Composable
private fun InputBarControlIcon(
    icon: InputBarPlayfulIcon,
    color: Color,
    modifier: Modifier = Modifier,
) {
    Canvas(modifier = modifier) {
        val stroke = Stroke(width = size.minDimension * 0.10f, cap = StrokeCap.Round)
        when (icon) {
            InputBarPlayfulIcon.Microphone -> {
                drawRoundRect(
                    color = color,
                    topLeft = Offset(size.width * 0.36f, size.height * 0.12f),
                    size = Size(size.width * 0.28f, size.height * 0.48f),
                    cornerRadius = CornerRadius(size.width * 0.14f, size.width * 0.14f),
                    style = Stroke(width = size.minDimension * 0.09f),
                )
                drawLine(
                    color = color,
                    start = Offset(size.width * 0.24f, size.height * 0.48f),
                    end = Offset(size.width * 0.24f, size.height * 0.56f),
                    strokeWidth = size.minDimension * 0.09f,
                    cap = StrokeCap.Round,
                )
                drawLine(
                    color = color,
                    start = Offset(size.width * 0.76f, size.height * 0.48f),
                    end = Offset(size.width * 0.76f, size.height * 0.56f),
                    strokeWidth = size.minDimension * 0.09f,
                    cap = StrokeCap.Round,
                )
                drawLine(
                    color = color,
                    start = Offset(size.width * 0.50f, size.height * 0.66f),
                    end = Offset(size.width * 0.50f, size.height * 0.86f),
                    strokeWidth = size.minDimension * 0.09f,
                    cap = StrokeCap.Round,
                )
                drawLine(
                    color = color,
                    start = Offset(size.width * 0.32f, size.height * 0.86f),
                    end = Offset(size.width * 0.68f, size.height * 0.86f),
                    strokeWidth = size.minDimension * 0.09f,
                    cap = StrokeCap.Round,
                )
            }

            InputBarPlayfulIcon.Camera -> {
                drawRoundRect(
                    brush = Brush.linearGradient(
                        colors = listOf(Color(0xFFB9E5FF), Color(0xFF6FB8F4)),
                        start = Offset(size.width * 0.16f, size.height * 0.22f),
                        end = Offset(size.width * 0.84f, size.height * 0.82f),
                    ),
                    topLeft = Offset(size.width * 0.10f, size.height * 0.32f),
                    size = Size(size.width * 0.80f, size.height * 0.52f),
                    cornerRadius = CornerRadius(size.width * 0.15f, size.width * 0.15f),
                )
                drawRoundRect(
                    color = Color(0xFF5CA9EE),
                    topLeft = Offset(size.width * 0.10f, size.height * 0.50f),
                    size = Size(size.width * 0.80f, size.height * 0.34f),
                    cornerRadius = CornerRadius(size.width * 0.14f, size.width * 0.14f),
                )
                drawRoundRect(
                    color = Color(0xFFFFD56B),
                    topLeft = Offset(size.width * 0.34f, size.height * 0.18f),
                    size = Size(size.width * 0.30f, size.height * 0.16f),
                    cornerRadius = CornerRadius(size.width * 0.06f, size.width * 0.06f),
                )
                drawRoundRect(
                    color = Color(0xFF88CBFF),
                    topLeft = Offset(size.width * 0.19f, size.height * 0.24f),
                    size = Size(size.width * 0.22f, size.height * 0.14f),
                    cornerRadius = CornerRadius(size.width * 0.05f, size.width * 0.05f),
                )
                drawCircle(
                    color = Color.White.copy(alpha = 0.34f),
                    radius = size.minDimension * 0.12f,
                    center = Offset(size.width * 0.31f, size.height * 0.46f),
                )
                drawRoundRect(
                    color = color,
                    topLeft = Offset(size.width * 0.10f, size.height * 0.32f),
                    size = Size(size.width * 0.80f, size.height * 0.52f),
                    cornerRadius = CornerRadius(size.width * 0.15f, size.width * 0.15f),
                    style = Stroke(width = size.minDimension * 0.045f, cap = StrokeCap.Round),
                )
                drawCircle(
                    color = Color.White,
                    radius = size.minDimension * 0.22f,
                    center = Offset(size.width * 0.50f, size.height * 0.58f),
                )
                drawCircle(
                    brush = Brush.radialGradient(
                        colors = listOf(Color(0xFF9FD6FF), Color(0xFF4F96DE)),
                        center = Offset(size.width * 0.46f, size.height * 0.54f),
                        radius = size.minDimension * 0.22f,
                    ),
                    radius = size.minDimension * 0.155f,
                    center = Offset(size.width * 0.50f, size.height * 0.58f),
                )
                drawCircle(
                    color = Color.White.copy(alpha = 0.78f),
                    radius = size.minDimension * 0.045f,
                    center = Offset(size.width * 0.44f, size.height * 0.53f),
                )
            }

            InputBarPlayfulIcon.Umbrella -> {
                val canopy = Path().apply {
                    moveTo(size.width * 0.12f, size.height * 0.56f)
                    cubicTo(
                        size.width * 0.18f,
                        size.height * 0.22f,
                        size.width * 0.82f,
                        size.height * 0.22f,
                        size.width * 0.88f,
                        size.height * 0.56f,
                    )
                    cubicTo(
                        size.width * 0.74f,
                        size.height * 0.50f,
                        size.width * 0.68f,
                        size.height * 0.62f,
                        size.width * 0.58f,
                        size.height * 0.56f,
                    )
                    cubicTo(
                        size.width * 0.50f,
                        size.height * 0.49f,
                        size.width * 0.42f,
                        size.height * 0.62f,
                        size.width * 0.32f,
                        size.height * 0.56f,
                    )
                    cubicTo(
                        size.width * 0.24f,
                        size.height * 0.50f,
                        size.width * 0.20f,
                        size.height * 0.56f,
                        size.width * 0.12f,
                        size.height * 0.56f,
                    )
                    close()
                }
                drawPath(
                    path = canopy,
                    brush = Brush.linearGradient(
                        colors = listOf(Color(0xFFBFE8FF), Color(0xFF6DBCF4)),
                        start = Offset(size.width * 0.18f, size.height * 0.22f),
                        end = Offset(size.width * 0.84f, size.height * 0.66f),
                    ),
                )
                drawCircle(
                    color = Color.White.copy(alpha = 0.45f),
                    radius = size.minDimension * 0.12f,
                    center = Offset(size.width * 0.35f, size.height * 0.39f),
                )
                drawPath(
                    path = canopy,
                    color = color,
                    style = Stroke(width = size.minDimension * 0.055f, cap = StrokeCap.Round),
                )
                drawLine(
                    color = color,
                    start = Offset(size.width * 0.50f, size.height * 0.56f),
                    end = Offset(size.width * 0.50f, size.height * 0.88f),
                    strokeWidth = size.minDimension * 0.07f,
                    cap = StrokeCap.Round,
                )
                drawArc(
                    color = color,
                    startAngle = 62f,
                    sweepAngle = 190f,
                    useCenter = false,
                    topLeft = Offset(size.width * 0.39f, size.height * 0.72f),
                    size = Size(size.width * 0.28f, size.height * 0.24f),
                    style = Stroke(width = size.minDimension * 0.07f, cap = StrokeCap.Round),
                )
            }

            InputBarPlayfulIcon.Rest -> {
                drawPath(
                    path = ovalPath(
                        center = Offset(size.width * 0.46f, size.height * 0.56f),
                        radiusX = size.width * 0.30f,
                        radiusY = size.height * 0.24f,
                    ),
                    brush = Brush.linearGradient(
                        colors = listOf(Color(0xFFA8DFFF), Color(0xFF78C7F7)),
                        start = Offset(size.width * 0.22f, size.height * 0.32f),
                        end = Offset(size.width * 0.74f, size.height * 0.76f),
                    ),
                )
                drawPath(
                    path = ovalPath(
                        center = Offset(size.width * 0.66f, size.height * 0.61f),
                        radiusX = size.width * 0.22f,
                        radiusY = size.height * 0.20f,
                    ),
                    color = Color(0xFFE0F5FF),
                )
                drawPath(
                    path = ovalPath(
                        center = Offset(size.width * 0.77f, size.height * 0.42f),
                        radiusX = size.width * 0.12f,
                        radiusY = size.height * 0.12f,
                    ),
                    color = Color(0xFFFFDDE6),
                )
                drawPath(
                    path = ovalPath(
                        center = Offset(size.width * 0.26f, size.height * 0.36f),
                        radiusX = size.width * 0.11f,
                        radiusY = size.height * 0.11f,
                    ),
                    color = Color(0xFFFFE986),
                )
                drawLine(
                    color = color,
                    start = Offset(size.width * 0.39f, size.height * 0.58f),
                    end = Offset(size.width * 0.46f, size.height * 0.62f),
                    strokeWidth = size.minDimension * 0.04f,
                    cap = StrokeCap.Round,
                )
                drawLine(
                    color = color,
                    start = Offset(size.width * 0.58f, size.height * 0.58f),
                    end = Offset(size.width * 0.65f, size.height * 0.62f),
                    strokeWidth = size.minDimension * 0.04f,
                    cap = StrokeCap.Round,
                )
            }
        }
    }
}

internal fun inputBarUsesChildVoiceFirstInput(
    childVoiceFirstMode: Boolean = DevSettings.CHILD_VOICE_FIRST_MODE,
    showTextInputForChild: Boolean = DevSettings.SHOW_TEXT_INPUT_FOR_CHILD,
    voiceConfirmBeforeSend: Boolean = DevSettings.VOICE_CONFIRM_BEFORE_SEND,
): Boolean {
    return childVoiceFirstMode && !showTextInputForChild && !voiceConfirmBeforeSend
}

internal fun inputBarShouldShowPendingTranscriptPanel(
    useChildVoiceFirstInput: Boolean,
    hasPendingTranscript: Boolean,
): Boolean {
    return hasPendingTranscript && !useChildVoiceFirstInput
}

internal fun inputBarShouldAutoSendHiddenPendingTranscript(
    useChildVoiceFirstInput: Boolean,
    enabled: Boolean,
    hasPendingTranscript: Boolean,
    pendingTranscript: String,
): Boolean {
    return useChildVoiceFirstInput &&
        enabled &&
        hasPendingTranscript &&
        pendingTranscript.trim().isNotEmpty()
}

internal fun inputBarPrimaryVoiceButtonText(
    presentation: ChildInteractionPresentation,
): String {
    return presentation.primaryButtonText
}

internal fun inputBarPrimaryVoiceButtonEnabled(
    enabled: Boolean,
    presentation: ChildInteractionPresentation,
): Boolean {
    return enabled && presentation.primaryButtonEnabled
}

internal fun inputBarShouldShowResayAction(
    useChildVoiceFirstInput: Boolean,
    inputMode: VoiceInputMode,
): Boolean {
    if (!useChildVoiceFirstInput) return false
    return when (inputMode) {
        VoiceInputMode.PendingTranscript,
        VoiceInputMode.NeedsRetry,
        VoiceInputMode.PermissionDenied,
        VoiceInputMode.Failed -> true
        else -> false
    }
}

internal fun inputBarShouldShowCancelAction(
    useChildVoiceFirstInput: Boolean,
    inputMode: VoiceInputMode,
): Boolean {
    return inputMode == VoiceInputMode.Listening ||
        inputMode == VoiceInputMode.WaitingForChild ||
        (useChildVoiceFirstInput && inputMode == VoiceInputMode.PendingTranscript)
}

internal fun inputBarShouldShowMuteToggle(
    useChildVoiceFirstInput: Boolean,
    presentation: ChildInteractionPresentation,
): Boolean {
    return presentation.showMuteToggle || !useChildVoiceFirstInput
}

internal fun inputBarShouldShowTopicShift(
    useChildVoiceFirstInput: Boolean,
    presentation: ChildInteractionPresentation,
): Boolean {
    if (!useChildVoiceFirstInput) return false
    return presentation.phase in setOf(
        ChildTurnUiPhase.Ready,
        ChildTurnUiPhase.WaitingChild,
        ChildTurnUiPhase.NeedsRetry,
        ChildTurnUiPhase.PermissionNeeded,
        ChildTurnUiPhase.Resting,
        ChildTurnUiPhase.ServiceError,
    )
}

internal fun inputBarMuteToggleText(tts: TtsUiState): String {
    return if (tts.isMuted) "打开朗读" else "静音"
}

@Composable
private fun PendingVoiceTranscriptPanel(
    transcript: String,
    errorMessage: String?,
    enabled: Boolean,
    onTranscriptChange: (String) -> Unit,
    onSend: () -> Unit,
    onResay: () -> Unit,
    onCancel: () -> Unit,
) {
    Surface(
        color = MaterialTheme.colorScheme.surfaceVariant,
        shape = MaterialTheme.shapes.small,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            OutlinedTextField(
                value = transcript,
                onValueChange = onTranscriptChange,
                enabled = enabled,
                modifier = Modifier.fillMaxWidth(),
                label = {
                    Text(text = "确认识别到的话")
                },
                textStyle = MaterialTheme.typography.bodyLarge,
                minLines = 1,
                maxLines = 3,
            )
            errorMessage?.let { message ->
                Text(
                    text = message,
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.error,
                )
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Button(
                    onClick = onSend,
                    enabled = enabled && transcript.trim().isNotEmpty(),
                    modifier = Modifier.widthIn(min = 82.dp),
                ) {
                    Text(text = "发送")
                }
                TextButton(
                    onClick = onResay,
                    enabled = enabled,
                ) {
                    Text(text = "重说")
                }
                TextButton(
                    onClick = onCancel,
                    enabled = enabled,
                ) {
                    Text(text = "取消")
                }
            }
        }
    }
}
