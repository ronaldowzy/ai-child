package com.childai.companion.ui.chat

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
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
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.childai.companion.config.DevSettings
import com.childai.companion.data.attachment.PhotoUploadPayload
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
    onPhotoCaptured: (PhotoUploadPayload, String) -> Unit = { _, _ -> },
    onPhotoCaptureFailed: (String) -> Unit = {},
) {
    val context = LocalContext.current
    var draft by rememberSaveable { mutableStateOf("") }
    var showImageSourceDialog by rememberSaveable { mutableStateOf(false) }
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
    val imageInputLaunchers = rememberImageInputLaunchers(
        onCaptured = onPhotoCaptured,
        onFailed = onPhotoCaptureFailed,
    )

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

    if (showImageSourceDialog) {
        AlertDialog(
            onDismissRequest = { showImageSourceDialog = false },
            title = {
                Text(text = "拍给小白狐看")
            },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Button(
                        onClick = {
                            showImageSourceDialog = false
                            imageInputLaunchers.capturePhoto(IMAGE_PURPOSE_SHARE)
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(text = "拍照")
                    }
                    OutlinedButton(
                        onClick = {
                            showImageSourceDialog = false
                            imageInputLaunchers.pickFromGallery(IMAGE_PURPOSE_SHARE)
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(text = "从相册选")
                    }
                }
            },
            confirmButton = {},
            dismissButton = {
                TextButton(onClick = { showImageSourceDialog = false }) {
                    Text(text = "取消")
                }
            },
        )
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
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Button(
                    onClick = {
                        if (voice.isRecording) {
                            voice.actions.onStopRecordingAndUpload()
                        } else {
                            startVoiceRecordingWithPermission()
                        }
                    },
                    enabled = enabled && interactionPresentation.primaryButtonEnabled,
                    modifier = Modifier
                        .weight(1f)
                        .heightIn(min = 58.dp),
                ) {
                    Text(
                        text = inputBarPrimaryVoiceButtonText(interactionPresentation),
                        style = MaterialTheme.typography.titleMedium,
                    )
                }
                if (interactionPresentation.showStopSpeaking) {
                    OutlinedButton(
                        onClick = onStopTts,
                        modifier = Modifier.heightIn(min = 58.dp),
                    ) {
                        Text(
                            text = "停一下",
                            style = MaterialTheme.typography.titleMedium,
                        )
                    }
                }
                if (inputBarShouldShowMuteToggle(useChildVoiceFirstInput, interactionPresentation)) {
                    OutlinedButton(
                        onClick = onToggleTtsMuted,
                        modifier = Modifier.heightIn(min = 58.dp),
                    ) {
                        Text(
                            text = inputBarMuteToggleText(tts),
                            style = MaterialTheme.typography.titleMedium,
                        )
                    }
                }
                if (interactionPresentation.showImageInput) {
                    OutlinedButton(
                        onClick = { showImageSourceDialog = true },
                        enabled = enabled && !voice.isRecording && !voice.isUploading,
                        modifier = Modifier.heightIn(min = 58.dp),
                    ) {
                        Text(
                            text = "拍给小白狐看",
                            style = MaterialTheme.typography.titleMedium,
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
                        Text(text = "说点什么")
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
                    Text(text = if (voice.isRecording) "说完了" else "语音")
                }
                Button(
                    onClick = { sendDraft() },
                    enabled = enabled && !voice.hasPendingTranscript && trimmedDraft.isNotEmpty(),
                    modifier = Modifier.widthIn(min = 88.dp),
                ) {
                    Text(text = if (enabled) "发送" else "发送中")
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
                        Text(text = "重说")
                    }
                }
                if (inputBarShouldShowCancelAction(useChildVoiceFirstInput, voice.inputMode)) {
                    TextButton(onClick = voice.actions.onCancelVoiceInput) {
                        Text(text = "取消语音")
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
                        Text(text = "检查朗读设置")
                    }
                    TextButton(onClick = onInstallTtsData) {
                        Text(text = "安装语音数据")
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
