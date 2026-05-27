package com.childai.companion.ui.chat

import android.content.Intent
import android.graphics.BitmapFactory
import android.provider.Settings
import android.speech.tts.TextToSpeech
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.ime
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.draw.blur
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.childai.companion.config.DevSettings
import com.childai.companion.data.attachment.PhotoUploadPayload
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.mascot.MascotState
import com.childai.companion.ui.parent.ParentEntryCredentialDialog
import com.childai.companion.ui.parent.ParentEntryTarget
import com.childai.companion.ui.parent.ParentCredentialGate
import com.childai.companion.ui.theme.ChildAiCompanionTheme
import com.childai.companion.voice.MediaPlayerAudioUrlPlayer
import com.childai.companion.voice.NoOpTtsController
import com.childai.companion.voice.RemoteAudioTtsController
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

@Composable
fun ChildChatScreen(
    modifier: Modifier = Modifier,
    onOpenParentSettings: () -> Unit = {},
    onOpenParentReport: () -> Unit = {},
    viewModel: ChatViewModel = viewModel(),
    requireParentCredential: Boolean = false,
    verifyParentCredential: suspend (String) -> Boolean = { false },
) {
    val uiState by viewModel.uiState.collectAsState()
    val context = LocalContext.current
    val ttsController = remember {
        RemoteAudioTtsController(
            audioUrlPlayer = MediaPlayerAudioUrlPlayer(),
            fallbackController = NoOpTtsController,
            backendBaseUrl = DevSettings.conversationApiBaseUrl,
        )
    }

    fun openIntentWithFallback(primary: Intent, fallback: Intent = Intent(Settings.ACTION_SETTINGS)) {
        val primaryIntent = primary.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        val fallbackIntent = fallback.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        runCatching {
            context.startActivity(primaryIntent)
        }.onFailure {
            context.startActivity(fallbackIntent)
        }
    }

    DisposableEffect(viewModel, ttsController) {
        viewModel.attachTtsController(ttsController)
        onDispose {
            viewModel.shutdownTts()
        }
    }
    LaunchedEffect(viewModel) {
        viewModel.requestOpeningGreeting()
    }

    ChildChatScreenContent(
        uiState = uiState,
        onSend = viewModel::sendText,
        onQuickAction = viewModel::onQuickAction,
        onStopTts = viewModel::stopTtsPlayback,
        onToggleTtsMuted = viewModel::toggleTtsMuted,
        onOpenTtsSettings = {
            openIntentWithFallback(Intent(TTS_SETTINGS_ACTION))
        },
        onInstallTtsData = {
            openIntentWithFallback(Intent(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA))
        },
        onPhotoCaptured = viewModel::submitCapturedPhoto,
        onPhotoCaptureFailed = viewModel::onPhotoCaptureFailed,
        onOpenParentSettings = onOpenParentSettings,
        onOpenParentReport = onOpenParentReport,
        requireParentCredential = requireParentCredential,
        verifyParentCredential = verifyParentCredential,
        modifier = modifier,
    )
}

@Composable
private fun ChildChatScreenContent(
    uiState: ChatUiState,
    onSend: (String) -> Unit,
    onQuickAction: (QuickActionUi) -> Unit,
    onStopTts: () -> Unit,
    onToggleTtsMuted: () -> Unit,
    onOpenTtsSettings: () -> Unit,
    onInstallTtsData: () -> Unit,
    onPhotoCaptured: (PhotoUploadPayload, String) -> Unit,
    onPhotoCaptureFailed: (String) -> Unit,
    onOpenParentSettings: () -> Unit,
    onOpenParentReport: () -> Unit,
    requireParentCredential: Boolean,
    verifyParentCredential: suspend (String) -> Boolean,
    modifier: Modifier = Modifier,
) {
    val coroutineScope = rememberCoroutineScope()
    var pendingParentEntry by rememberSaveable { mutableStateOf<ParentEntryTarget?>(null) }
    var parentCredentialInput by rememberSaveable { mutableStateOf("") }
    var parentCredentialError by rememberSaveable { mutableStateOf<String?>(null) }
    var parentCredentialSubmitting by rememberSaveable { mutableStateOf(false) }
    var parentEntryHint by rememberSaveable { mutableStateOf<String?>(null) }
    var showParentEntryChoices by rememberSaveable { mutableStateOf(false) }

    fun resetParentGate() {
        pendingParentEntry = null
        parentCredentialInput = ""
        parentCredentialError = null
        parentCredentialSubmitting = false
    }

    fun openParentGate(target: ParentEntryTarget) {
        parentEntryHint = null
        showParentEntryChoices = false
        if (!requireParentCredential) {
            when (target) {
                ParentEntryTarget.Report -> onOpenParentReport()
                ParentEntryTarget.Settings -> onOpenParentSettings()
            }
            return
        }
        pendingParentEntry = target
        parentCredentialInput = ""
        parentCredentialError = null
        parentCredentialSubmitting = false
    }

    fun submitParentCredential() {
        val target = pendingParentEntry ?: return
        if (parentCredentialSubmitting) return
        parentCredentialSubmitting = true
        parentCredentialError = null
        val credential = parentCredentialInput
        coroutineScope.launch {
            val accepted = runCatching {
                verifyParentCredential(credential)
            }.getOrDefault(false)
            parentCredentialSubmitting = false
            if (accepted) {
                resetParentGate()
                when (target) {
                    ParentEntryTarget.Report -> onOpenParentReport()
                    ParentEntryTarget.Settings -> onOpenParentSettings()
                }
            } else {
                parentCredentialError = ParentCredentialGate.GENTLE_ERROR_MESSAGE
            }
        }
    }

    pendingParentEntry?.let { target ->
        ParentEntryCredentialDialog(
            target = target,
            credentialInput = parentCredentialInput,
            errorMessage = parentCredentialError,
            isSubmitting = parentCredentialSubmitting,
            onCredentialInputChange = {
                parentCredentialInput = it
                parentCredentialError = null
            },
            onConfirm = ::submitParentCredential,
            onDismiss = ::resetParentGate,
        )
    }
    if (showParentEntryChoices) {
        ParentEntryTargetDialog(
            onOpenTarget = ::openParentGate,
            onDismiss = { showParentEntryChoices = false },
        )
    }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = MaterialTheme.colorScheme.background,
    ) { innerPadding ->
        BoxWithConstraints(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
                .background(MaterialTheme.colorScheme.background),
        ) {
            val isLandscape = maxWidth > maxHeight
            val compactLandscape = maxHeight < 430.dp || maxWidth < 760.dp

            if (isLandscape) {
                // Landscape: fox on left, chat on right — fox is prominent
                val horizontalPadding = if (compactLandscape) 14.dp else 32.dp
                val verticalPadding = if (compactLandscape) 10.dp else 24.dp
                val columnGap = if (compactLandscape) 14.dp else 28.dp

                Row(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = horizontalPadding, vertical = verticalPadding),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    AgentPanel(
                        presentation = uiState.interactionPresentation,
                        compactLandscape = compactLandscape,
                        modifier = Modifier
                            .weight(0.50f)
                            .fillMaxHeight(),
                    )
                    Spacer(modifier = Modifier.width(columnGap))
                    ChatPanel(
                        uiState = uiState,
                        compactLandscape = compactLandscape,
                        parentEntryHint = parentEntryHint,
                        presentation = uiState.interactionPresentation,
                        onParentEntryTap = {
                            parentEntryHint = parentEntryTapHint()
                        },
                        onParentEntryLongPress = {
                            parentEntryHint = null
                            showParentEntryChoices = true
                        },
                        onSend = onSend,
                        onQuickAction = onQuickAction,
                        onStopTts = onStopTts,
                        onToggleTtsMuted = onToggleTtsMuted,
                        onOpenTtsSettings = onOpenTtsSettings,
                        onInstallTtsData = onInstallTtsData,
                        onPhotoCaptured = onPhotoCaptured,
                        onPhotoCaptureFailed = onPhotoCaptureFailed,
                        modifier = Modifier
                            .weight(0.50f)
                            .fillMaxHeight(),
                    )
                }
            } else {
                // Portrait: fox on top as hero, chat+input below
                val horizontalPadding = 20.dp
                val verticalPadding = 16.dp

                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = horizontalPadding, vertical = verticalPadding),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    ParentEntryHintBar(
                        parentEntryHint = parentEntryHint,
                        onParentEntryTap = {
                            parentEntryHint = parentEntryTapHint()
                        },
                        onParentEntryLongPress = {
                            parentEntryHint = null
                            showParentEntryChoices = true
                        },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    // Fox hero area — 55% of screen
                    AgentPanel(
                        presentation = uiState.interactionPresentation,
                        compactLandscape = false,
                        modifier = Modifier
                            .fillMaxWidth()
                            .weight(0.55f),
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    // Chat + input area — 45% of screen
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .weight(0.45f),
                    ) {
                        ChatConversationPanel(
                            uiState = uiState,
                            onQuickAction = onQuickAction,
                            modifier = Modifier.weight(1f),
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        InputBar(
                            modifier = Modifier
                                .fillMaxWidth()
                                .heightIn(min = 112.dp)
                                .background(MaterialTheme.colorScheme.surface)
                                .navigationBarsPadding()
                                .windowInsetsPadding(WindowInsets.ime)
                                .padding(horizontal = 18.dp, vertical = 14.dp),
                            onSend = onSend,
                            enabled = !uiState.isSending,
                            voice = uiState.voice,
                            tts = uiState.tts,
                            presentation = uiState.interactionPresentation,
                            onStopTts = onStopTts,
                            onToggleTtsMuted = onToggleTtsMuted,
                            onOpenTtsSettings = onOpenTtsSettings,
                            onInstallTtsData = onInstallTtsData,
                            onPhotoCaptured = onPhotoCaptured,
                            onPhotoCaptureFailed = onPhotoCaptureFailed,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun ChatConversationPanel(
    uiState: ChatUiState,
    onQuickAction: (QuickActionUi) -> Unit,
    modifier: Modifier = Modifier,
) {
    val visibleQuickActions = uiState.quickActions.filterNot { action ->
        action.id == "take_photo" || action.id == "share_photo"
    }
    Column(modifier = modifier) {
        ChatMessageListWithPreviews(
            messages = uiState.messages,
            imagePreviewCards = uiState.imagePreviewCards,
            modifier = Modifier.weight(1f),
        )
        if (visibleQuickActions.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            QuickActionsRow(
                actions = visibleQuickActions,
                enabled = !uiState.isSending,
                onQuickAction = onQuickAction,
            )
        } else {
            val topicShiftActions = topicShiftChipActions(uiState)
            if (topicShiftActions.isNotEmpty()) {
                Spacer(modifier = Modifier.height(12.dp))
                QuickActionsRow(
                    actions = topicShiftActions,
                    enabled = !uiState.isSending,
                    onQuickAction = onQuickAction,
                )
            }
        }
        if (DevSettings.SHOW_SESSION_STATE_DEBUG) uiState.sessionState?.let { sessionState ->
            Spacer(modifier = Modifier.height(10.dp))
            SessionStateStrip(sessionState = sessionState)
        }
    }
}

@Composable
private fun ChatMessageListWithPreviews(
    messages: List<ChatMessage>,
    imagePreviewCards: Map<String, LocalImagePreviewCardUiState>,
    modifier: Modifier = Modifier,
) {
    val listState = rememberLazyListState()
    val lastPreviewStatus = messages.lastOrNull()
        ?.id
        ?.let { imagePreviewCards[it]?.status }
    LaunchedEffect(messages.lastOrNull()?.id, messages.lastOrNull()?.text, lastPreviewStatus) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(messages.lastIndex)
        }
    }
    if (messages.isEmpty()) {
        Box(
            modifier = modifier.fillMaxWidth(),
            contentAlignment = Alignment.Center,
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text(
                    text = "小白狐在这里。",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Text(
                    text = "想说什么都可以慢慢说。",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                )
            }
        }
    } else {
        LazyColumn(
            modifier = modifier.fillMaxWidth(),
            state = listState,
            verticalArrangement = Arrangement.spacedBy(12.dp),
            contentPadding = PaddingValues(vertical = 8.dp),
        ) {
            items(
                items = messages,
                key = { message -> message.id },
            ) { message ->
                ChatMessageBubbleWithPreview(
                    message = message,
                    imagePreview = imagePreviewCards[message.id],
                )
            }
        }
    }
}

@Composable
private fun ChatMessageBubbleWithPreview(
    message: ChatMessage,
    imagePreview: LocalImagePreviewCardUiState?,
) {
    val isChild = message.author == MessageAuthor.Child
    val bubbleColor = if (isChild) {
        MaterialTheme.colorScheme.primary
    } else {
        MaterialTheme.colorScheme.surfaceVariant
    }
    val textColor = if (isChild) {
        MaterialTheme.colorScheme.onPrimary
    } else {
        MaterialTheme.colorScheme.onSurfaceVariant
    }
    val alignment = if (isChild) Alignment.CenterEnd else Alignment.CenterStart

    Box(
        modifier = Modifier.fillMaxWidth(),
        contentAlignment = alignment,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth(0.82f)
                .clip(RoundedCornerShape(8.dp))
                .background(bubbleColor)
                .padding(horizontal = 16.dp, vertical = 12.dp),
        ) {
            Text(
                text = if (isChild) "我" else "小白狐",
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.SemiBold,
                color = textColor.copy(alpha = 0.78f),
            )
            imagePreview?.let { preview ->
                LocalImagePreviewCard(
                    preview = preview,
                    childBubble = isChild,
                    modifier = Modifier.padding(top = 8.dp),
                )
            }
            Text(
                text = message.text,
                style = MaterialTheme.typography.bodyLarge,
                color = textColor,
                modifier = Modifier.padding(top = 4.dp),
            )
        }
    }
}

@Composable
private fun LocalImagePreviewCard(
    preview: LocalImagePreviewCardUiState,
    childBubble: Boolean,
    modifier: Modifier = Modifier,
) {
    val previewBitmap = remember(preview.previewBytes) {
        preview.previewBytes?.let { bytes ->
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.asImageBitmap()
        }
    }
    val contentColor = if (childBubble) {
        MaterialTheme.colorScheme.onPrimary
    } else {
        MaterialTheme.colorScheme.onSurfaceVariant
    }
    val statusText = when (preview.status) {
        LocalImagePreviewStatus.Uploading -> "图片正在给小白狐看"
        LocalImagePreviewStatus.Sent -> "图片已发送给小白狐"
        LocalImagePreviewStatus.Failed -> "图片没有传好"
    }
    val cardColor = if (childBubble) {
        MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.12f)
    } else {
        MaterialTheme.colorScheme.surface
    }

    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .background(cardColor)
            .border(
                width = 1.dp,
                color = contentColor.copy(alpha = 0.18f),
                shape = RoundedCornerShape(8.dp),
            )
            .padding(8.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        if (previewBitmap != null) {
            Image(
                bitmap = previewBitmap,
                contentDescription = "刚才发送的图片",
                contentScale = ContentScale.Crop,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(112.dp)
                    .clip(RoundedCornerShape(6.dp)),
            )
        }
        Text(
            text = "$statusText · ${preview.displayMimeType} · ${preview.displaySize}",
            style = MaterialTheme.typography.labelMedium,
            color = contentColor,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

@Composable
private fun ChatPanel(
    uiState: ChatUiState,
    compactLandscape: Boolean,
    parentEntryHint: String?,
    presentation: ChildInteractionPresentation,
    onParentEntryTap: () -> Unit,
    onParentEntryLongPress: () -> Unit,
    onSend: (String) -> Unit,
    onQuickAction: (QuickActionUi) -> Unit,
    onStopTts: () -> Unit,
    onToggleTtsMuted: () -> Unit,
    onOpenTtsSettings: () -> Unit,
    onInstallTtsData: () -> Unit,
    onPhotoCaptured: (PhotoUploadPayload, String) -> Unit,
    onPhotoCaptureFailed: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val panelGap = if (compactLandscape) 8.dp else 12.dp
    val inputHorizontalPadding = if (compactLandscape) 12.dp else 18.dp
    val inputVerticalPadding = if (compactLandscape) 10.dp else 14.dp

    Column(modifier = modifier) {
        AgentTopBar(
            parentEntryHint = parentEntryHint,
            statusText = presentation.statusText,
            compactLandscape = compactLandscape,
            onParentEntryTap = onParentEntryTap,
            onParentEntryLongPress = onParentEntryLongPress,
        )
        Spacer(modifier = Modifier.height(panelGap))
        ChatConversationPanel(
            uiState = uiState,
            onQuickAction = onQuickAction,
            modifier = Modifier.weight(1f),
        )
        Spacer(modifier = Modifier.height(panelGap))
        InputBar(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = if (compactLandscape) 96.dp else 112.dp)
                .background(MaterialTheme.colorScheme.surface)
                .navigationBarsPadding()
                .windowInsetsPadding(WindowInsets.ime)
                .padding(
                    horizontal = inputHorizontalPadding,
                    vertical = inputVerticalPadding,
                ),
            onSend = onSend,
            enabled = !uiState.isSending,
            voice = uiState.voice,
            tts = uiState.tts,
            presentation = presentation,
            onStopTts = onStopTts,
            onToggleTtsMuted = onToggleTtsMuted,
            onOpenTtsSettings = onOpenTtsSettings,
            onInstallTtsData = onInstallTtsData,
            onPhotoCaptured = onPhotoCaptured,
            onPhotoCaptureFailed = onPhotoCaptureFailed,
        )
    }
}

internal const val PARENT_ENTRY_COMPACT_LABEL = "大人"

internal fun parentEntryTapHint(): String = "这里给大人用。请大人长按进入。"

internal fun parentEntryDefaultHint(): String = "大人长按”大人”，输入家长账号密码后进入。"

internal fun parentEntryDefaultLabels(): List<String> = listOf(PARENT_ENTRY_COMPACT_LABEL)

internal fun parentEntryLongPressTargets(): List<ParentEntryTarget> =
    listOf(ParentEntryTarget.Report, ParentEntryTarget.Settings)

internal fun topicShiftChipActions(uiState: ChatUiState): List<QuickActionUi> {
    return emptyList()
}

@Composable
private fun QuickActionsRow(
    actions: List<QuickActionUi>,
    enabled: Boolean,
    onQuickAction: (QuickActionUi) -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        actions.forEach { action ->
            AssistChip(
                onClick = { onQuickAction(action) },
                enabled = enabled,
                label = {
                    Text(text = action.label)
                },
            )
        }
    }
}

@Composable
private fun SessionStateStrip(sessionState: ConversationSessionState) {
    Surface(
        color = MaterialTheme.colorScheme.surfaceVariant,
        shape = MaterialTheme.shapes.small,
    ) {
        Text(
            text = sessionState.toDisplayText(),
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
        )
    }
}

@Composable
private fun AgentTopBar(
    parentEntryHint: String?,
    statusText: String,
    compactLandscape: Boolean,
    onParentEntryTap: () -> Unit,
    onParentEntryLongPress: () -> Unit,
) {
    val horizontalPadding = if (compactLandscape) 16.dp else 24.dp
    val verticalPadding = if (compactLandscape) 10.dp else 18.dp
    Surface(
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 1.dp,
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = horizontalPadding, vertical = verticalPadding),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(
                    modifier = Modifier.weight(1f),
                ) {
                    Text(
                        text = "小白狐",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onSurface,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        text = statusText,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                ParentEntryButton(
                    label = PARENT_ENTRY_COMPACT_LABEL,
                    onTap = onParentEntryTap,
                    onLongPress = onParentEntryLongPress,
                )
            }
            Text(
                text = parentEntryHint ?: parentEntryDefaultHint(),
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(
                    start = horizontalPadding,
                    end = horizontalPadding,
                    bottom = if (compactLandscape) 8.dp else 10.dp,
                ),
            )
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun ParentEntryButton(
    label: String,
    onTap: () -> Unit,
    onLongPress: () -> Unit,
) {
    Surface(
        modifier = Modifier.combinedClickable(
            onClick = onTap,
            onLongClick = onLongPress,
            onLongClickLabel = "进入家长页面",
        ),
        shape = MaterialTheme.shapes.small,
        color = MaterialTheme.colorScheme.surface,
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.primary,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 7.dp),
        )
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun ParentEntryHintBar(
    parentEntryHint: String?,
    onParentEntryTap: () -> Unit,
    onParentEntryLongPress: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(
            text = parentEntryHint ?: parentEntryDefaultHint(),
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f),
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier.weight(1f),
        )
        ParentEntryButton(
            label = PARENT_ENTRY_COMPACT_LABEL,
            onTap = onParentEntryTap,
            onLongPress = onParentEntryLongPress,
        )
    }
}

@Composable
private fun ParentEntryTargetDialog(
    onOpenTarget: (ParentEntryTarget) -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(text = "给大人的角落")
        },
        text = {
            Text(
                text = "请选择要进入的家长页面。",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        },
        confirmButton = {
            TextButton(onClick = { onOpenTarget(ParentEntryTarget.Report) }) {
                Text(text = ParentEntryTarget.Report.label)
            }
        },
        dismissButton = {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                TextButton(onClick = { onOpenTarget(ParentEntryTarget.Settings) }) {
                    Text(text = ParentEntryTarget.Settings.label)
                }
                TextButton(onClick = onDismiss) {
                    Text(text = "取消")
                }
            }
        },
    )
}

@Composable
private fun AgentPanel(
    presentation: ChildInteractionPresentation,
    compactLandscape: Boolean,
    modifier: Modifier = Modifier,
) {
    var debugMascotStateId by rememberSaveable { mutableStateOf<String?>(null) }
    val debugMascotState = debugMascotStateId?.let(MascotState::fromId)
    BoxWithConstraints(modifier = modifier) {
        val statusReserve = if (compactLandscape) 64.dp else 86.dp
        val mascotMaxSize = minOf(
            maxWidth,
            (maxHeight - statusReserve).coerceAtLeast(160.dp),
            if (compactLandscape) 340.dp else 470.dp,
        )
        val foxGlowColor = foxGlowColorForPhase(presentation.phase)
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.42f),
            shape = RoundedCornerShape(16.dp),
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(if (compactLandscape) 8.dp else 14.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                FoxStateIndicator(
                    phase = presentation.phase,
                    compactLandscape = compactLandscape,
                )
                Spacer(modifier = Modifier.height(if (compactLandscape) 4.dp else 8.dp))
                Box(
                    contentAlignment = Alignment.Center,
                ) {
                    // Glow effect behind fox
                    Box(
                        modifier = Modifier
                            .sizeIn(
                                maxWidth = mascotMaxSize * 0.7f,
                                maxHeight = mascotMaxSize * 0.7f,
                            )
                            .blur(radius = 32.dp)
                            .background(
                                Brush.radialGradient(
                                    colors = listOf(
                                        foxGlowColor.copy(alpha = 0.35f),
                                        foxGlowColor.copy(alpha = 0.0f),
                                    ),
                                ),
                                shape = CircleShape,
                            ),
                    )
                    CartoonAgentView(
                        agent = presentation.agent,
                        debugMascotState = debugMascotState,
                        modifier = Modifier.sizeIn(
                            maxWidth = mascotMaxSize,
                            maxHeight = mascotMaxSize,
                        ),
                    )
                }
                Spacer(modifier = Modifier.height(if (compactLandscape) 6.dp else 10.dp))
                AgentReplyCarouselText(
                    text = presentation.statusText,
                    compactLandscape = compactLandscape,
                )
                if (presentation.phase == ChildTurnUiPhase.Ready || presentation.phase == ChildTurnUiPhase.Resting) {
                    Spacer(modifier = Modifier.height(if (compactLandscape) 2.dp else 4.dp))
                    Text(
                        text = "可以聊一件小事，也可以拍给我看。",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f),
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                if (DevSettings.SHOW_MASCOT_DEBUG_SWITCHER) {
                    Spacer(modifier = Modifier.height(10.dp))
                    MascotDebugSwitcher(
                        selectedStateId = debugMascotStateId,
                        onStateSelected = { debugMascotStateId = it },
                    )
                }
            }
        }
    }
}

@Composable
private fun FoxStateIndicator(
    phase: ChildTurnUiPhase,
    compactLandscape: Boolean,
) {
    val (label, emoji) = foxStateDisplayForPhase(phase)
    Surface(
        color = foxStateChipColor(phase),
        shape = MaterialTheme.shapes.medium,
        tonalElevation = 1.dp,
    ) {
        Text(
            text = "$emoji $label",
            style = if (compactLandscape) {
                MaterialTheme.typography.labelMedium
            } else {
                MaterialTheme.typography.titleSmall
            },
            color = MaterialTheme.colorScheme.onSurface,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
        )
    }
}

private fun foxStateDisplayForPhase(phase: ChildTurnUiPhase): Pair<String, String> {
    return when (phase) {
        ChildTurnUiPhase.Ready,
        ChildTurnUiPhase.Resting -> "小白狐在这里" to "🦊"
        ChildTurnUiPhase.Listening -> "在听你说" to "👀"
        ChildTurnUiPhase.Recognizing -> "在听懂你的话" to "🤔"
        ChildTurnUiPhase.Sending,
        ChildTurnUiPhase.Thinking -> "在想一想" to "🤔"
        ChildTurnUiPhase.SpeakingPending,
        ChildTurnUiPhase.Speaking -> "在说给你听" to "🐻‍💬"
        ChildTurnUiPhase.ImageProcessing -> "在看这张图" to "👁️"
        ChildTurnUiPhase.NeedsRetry -> "可以再说一次" to "👂"
        ChildTurnUiPhase.PermissionNeeded -> "需要大人帮忙" to "🙏"
        ChildTurnUiPhase.ServiceError -> "先请大人看看" to "⚠️"
    }
}

@Composable
private fun foxStateChipColor(phase: ChildTurnUiPhase): Color {
    return when (phase) {
        ChildTurnUiPhase.Ready,
        ChildTurnUiPhase.Resting -> MaterialTheme.colorScheme.primaryContainer
        ChildTurnUiPhase.Listening -> MaterialTheme.colorScheme.tertiaryContainer
        ChildTurnUiPhase.Recognizing,
        ChildTurnUiPhase.Thinking,
        ChildTurnUiPhase.Sending -> MaterialTheme.colorScheme.secondaryContainer
        ChildTurnUiPhase.SpeakingPending,
        ChildTurnUiPhase.Speaking -> MaterialTheme.colorScheme.primaryContainer
        ChildTurnUiPhase.ImageProcessing -> MaterialTheme.colorScheme.secondaryContainer
        ChildTurnUiPhase.NeedsRetry -> MaterialTheme.colorScheme.surfaceVariant
        ChildTurnUiPhase.PermissionNeeded,
        ChildTurnUiPhase.ServiceError -> MaterialTheme.colorScheme.errorContainer
    }
}

private fun foxGlowColorForPhase(phase: ChildTurnUiPhase): Color {
    return when (phase) {
        ChildTurnUiPhase.Ready,
        ChildTurnUiPhase.Resting -> Color(0xFF81C784)       // soft green
        ChildTurnUiPhase.Listening -> Color(0xFF4FC3F7)     // sky blue
        ChildTurnUiPhase.Recognizing,
        ChildTurnUiPhase.Thinking,
        ChildTurnUiPhase.Sending -> Color(0xFFFFB74D)       // warm amber
        ChildTurnUiPhase.SpeakingPending,
        ChildTurnUiPhase.Speaking -> Color(0xFFFF8A65)      // warm orange
        ChildTurnUiPhase.ImageProcessing -> Color(0xFFBA68C8) // soft purple
        ChildTurnUiPhase.NeedsRetry -> Color(0xFFFFF176)    // soft yellow
        ChildTurnUiPhase.PermissionNeeded,
        ChildTurnUiPhase.ServiceError -> Color(0xFFEF9A9A)  // soft red
    }
}

internal fun childUiPolishStateLabel(phase: ChildTurnUiPhase): String {
    return when (phase) {
        ChildTurnUiPhase.Ready,
        ChildTurnUiPhase.Resting -> "小白狐在这里"
        ChildTurnUiPhase.Listening -> "在听你说"
        ChildTurnUiPhase.Recognizing -> "在听懂你的话"
        ChildTurnUiPhase.Sending,
        ChildTurnUiPhase.Thinking -> "在想一想"
        ChildTurnUiPhase.SpeakingPending,
        ChildTurnUiPhase.Speaking -> "在说给你听"
        ChildTurnUiPhase.ImageProcessing -> "在看这张图"
        ChildTurnUiPhase.NeedsRetry -> "可以再说一次"
        ChildTurnUiPhase.PermissionNeeded -> "需要大人帮忙"
        ChildTurnUiPhase.ServiceError -> "先请大人看看"
    }
}

@Composable
private fun AgentReplyCarouselText(
    text: String,
    compactLandscape: Boolean,
) {
    val segments = remember(text, compactLandscape) {
        agentReplyCarouselSegments(
            text = text,
            maxChars = if (compactLandscape) 34 else 52,
        )
    }
    var currentIndex by remember(text, compactLandscape) { mutableStateOf(0) }
    LaunchedEffect(segments) {
        currentIndex = 0
        while (segments.size > 1) {
            delay(3_200)
            currentIndex = (currentIndex + 1) % segments.size
        }
    }
    Surface(
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 1.dp,
        shape = MaterialTheme.shapes.medium,
        modifier = Modifier.fillMaxWidth(0.92f),
    ) {
        Text(
            text = segments.getOrElse(currentIndex) { text },
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface,
            maxLines = if (compactLandscape) 2 else 3,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
        )
    }
}

internal fun agentReplyCarouselSegments(
    text: String,
    maxChars: Int = 52,
): List<String> {
    val normalized = text.trim().replace(Regex("\\s+"), " ")
    if (normalized.isBlank()) return emptyList()

    val limit = maxChars.coerceAtLeast(12)
    val sentenceParts = Regex("(?<=[。！？!?；;])")
        .split(normalized)
        .map { it.trim() }
        .filter { it.isNotEmpty() }
    val source = sentenceParts.ifEmpty { listOf(normalized) }
    val chunks = mutableListOf<String>()
    val current = StringBuilder()

    fun flushCurrent() {
        if (current.isNotEmpty()) {
            chunks += current.toString()
            current.clear()
        }
    }

    source.forEach { part ->
        if (part.length > limit) {
            flushCurrent()
            part.chunked(limit).forEach { chunk ->
                if (chunk.isNotBlank()) {
                    chunks += chunk
                }
            }
        } else if (current.isEmpty()) {
            current.append(part)
        } else if (current.length + part.length <= limit) {
            current.append(part)
        } else {
            flushCurrent()
            current.append(part)
        }
    }
    flushCurrent()
    return chunks
}

@Composable
private fun MascotDebugSwitcher(
    selectedStateId: String?,
    onStateSelected: (String?) -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        AssistChip(
            onClick = { onStateSelected(null) },
            label = { Text(if (selectedStateId == null) "auto*" else "auto") },
        )
        MascotState.entries.forEach { state ->
            AssistChip(
                onClick = { onStateSelected(state.id) },
                label = { Text(state.id) },
            )
        }
    }
}

@Preview(showBackground = true, widthDp = 400, heightDp = 800, name = "Portrait - Ready")
@Composable
private fun ChildChatScreenPortraitPreview() {
    ChildAiCompanionTheme {
        ChildChatScreenContent(
            uiState = ChatUiState(
                messages = initialChatMessages(),
                agent = FoxAgentUiState(
                    mood = FoxMood.Warm,
                    motion = FoxMotion.GentleIdle,
                    statusText = "我准备好啦。",
                ),
            ),
            onSend = {},
            onQuickAction = {},
            onStopTts = {},
            onToggleTtsMuted = {},
            onOpenTtsSettings = {},
            onInstallTtsData = {},
            onPhotoCaptured = { _, _ -> },
            onPhotoCaptureFailed = {},
            onOpenParentSettings = {},
            onOpenParentReport = {},
            requireParentCredential = false,
            verifyParentCredential = { false },
        )
    }
}

@Preview(showBackground = true, widthDp = 400, heightDp = 800, name = "Portrait - Listening")
@Composable
private fun ChildChatScreenPortraitListeningPreview() {
    ChildAiCompanionTheme {
        ChildChatScreenContent(
            uiState = ChatUiState(
                messages = initialChatMessages() + ChatMessage(
                    id = "preview-child",
                    author = MessageAuthor.Child,
                    text = "今天学校有一件好玩的事",
                ),
                agent = FoxAgentUiState(
                    mood = FoxMood.Listening,
                    motion = FoxMotion.ListeningTail,
                    statusText = "我在听你说。",
                ),
                childTurnPhaseHint = ChildTurnUiPhase.Listening,
            ),
            onSend = {},
            onQuickAction = {},
            onStopTts = {},
            onToggleTtsMuted = {},
            onOpenTtsSettings = {},
            onInstallTtsData = {},
            onPhotoCaptured = { _, _ -> },
            onPhotoCaptureFailed = {},
            onOpenParentSettings = {},
            onOpenParentReport = {},
            requireParentCredential = false,
            verifyParentCredential = { false },
        )
    }
}

@Preview(showBackground = true, widthDp = 900, heightDp = 700, name = "Landscape - Listening")
@Composable
private fun ChildChatScreenLandscapePreview() {
    ChildAiCompanionTheme {
        ChildChatScreenContent(
            uiState = ChatUiState(
                messages = initialChatMessages() + ChatMessage(
                    id = "preview-child",
                    author = MessageAuthor.Child,
                    text = "我有一道题不会",
                ),
                quickActions = listOf(
                    QuickActionUi(id = "take_photo", label = "拍题目"),
                    QuickActionUi(id = "speak_problem", label = "读题目"),
                ),
                sessionState = ConversationSessionState(
                    baseScene = "daily.after_school_checkin",
                    activeScene = "learning.homework_help",
                    needsInput = "problem_content",
                    requiresParentAttention = false,
                ),
                agent = FoxAgentUiState(
                    mood = FoxMood.Listening,
                    motion = FoxMotion.ListeningTail,
                    statusText = "我在听你说。",
                ),
            ),
            onSend = {},
            onQuickAction = {},
            onStopTts = {},
            onToggleTtsMuted = {},
            onOpenTtsSettings = {},
            onInstallTtsData = {},
            onPhotoCaptured = { _, _ -> },
            onPhotoCaptureFailed = {},
            onOpenParentSettings = {},
            onOpenParentReport = {},
            requireParentCredential = false,
            verifyParentCredential = { false },
        )
    }
}

private const val TTS_SETTINGS_ACTION = "com.android.settings.TTS_SETTINGS"
