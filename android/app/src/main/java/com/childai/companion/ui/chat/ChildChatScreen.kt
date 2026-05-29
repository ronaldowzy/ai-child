package com.childai.companion.ui.chat

import android.content.Intent
import android.graphics.BitmapFactory
import android.provider.Settings
import android.speech.tts.TextToSpeech
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.scaleIn
import androidx.compose.animation.scaleOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.clickable
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
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.childai.companion.R
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
        onImageRetry = viewModel::retryPhotoUpload,
        onImageDismiss = viewModel::dismissFailedPhoto,
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
    onImageRetry: (String) -> Unit = {},
    onImageDismiss: (String) -> Unit = {},
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
                .background(companionPageBackgroundBrush()),
        ) {
            val isLandscape = maxWidth > maxHeight
            val compactLandscape = maxHeight < 430.dp || maxWidth < 760.dp

            CompanionRoomBackground(isLandscape = isLandscape)
            CompanionAmbientGlows(
                isLandscape = isLandscape,
                compactLandscape = compactLandscape,
            )

            if (isLandscape) {
                // Landscape: keep the room and mascot as the scene, with controls only as a light rail.
                val layoutWeights = companionLayoutWeights(isLandscape = true)
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
                        messages = uiState.messages,
                        imagePreviewCards = uiState.imagePreviewCards,
                        isLandscape = true,
                        compactLandscape = compactLandscape,
                        onImageRetry = onImageRetry,
                        onImageDismiss = onImageDismiss,
                        modifier = Modifier
                            .weight(layoutWeights.agent)
                            .fillMaxHeight(),
                    )
                    Spacer(modifier = Modifier.width(columnGap))
                    LandscapeOperationPanel(
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
                            .weight(layoutWeights.conversation)
                            .fillMaxHeight(),
                    )
                }
            } else {
                // Portrait: fox lives in the room; dialogue floats around it instead of sitting in a chat card.
                val horizontalPadding = 20.dp
                val verticalPadding = 16.dp
                val visibleQuickActions = childCompanionVisibleQuickActions(uiState)

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
                        messages = uiState.messages,
                        imagePreviewCards = uiState.imagePreviewCards,
                        isLandscape = false,
                        compactLandscape = false,
                        onImageRetry = onImageRetry,
                        onImageDismiss = onImageDismiss,
                        modifier = Modifier
                            .fillMaxWidth()
                            .weight(1f),
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    if (visibleQuickActions.isNotEmpty()) {
                        QuickActionsRow(
                            actions = visibleQuickActions,
                            enabled = !uiState.isSending,
                            onQuickAction = onQuickAction,
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                    }
                    val inputTrayShape = companionInputTrayShape(compactLandscape = false)
                    InputBar(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = 112.dp)
                            .navigationBarsPadding()
                            .windowInsetsPadding(WindowInsets.ime)
                            .clip(inputTrayShape)
                            .background(companionInputTrayColor())
                            .border(
                                width = 1.dp,
                                color = companionSoftBorderColor(alpha = 0.48f),
                                shape = inputTrayShape,
                            )
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

@Composable
private fun ChatConversationPanel(
    uiState: ChatUiState,
    isLandscape: Boolean,
    onQuickAction: (QuickActionUi) -> Unit,
    onImageRetry: (String) -> Unit = {},
    onImageDismiss: (String) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val visibleQuickActions = childCompanionVisibleQuickActions(uiState)
    Column(modifier = modifier) {
        ChatMessageListWithPreviews(
            messages = uiState.messages,
            imagePreviewCards = uiState.imagePreviewCards,
            maxVisibleMessages = companionRecentMessageLimit(isLandscape),
            onImageRetry = onImageRetry,
            onImageDismiss = onImageDismiss,
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
    maxVisibleMessages: Int,
    onImageRetry: (String) -> Unit = {},
    onImageDismiss: (String) -> Unit = {},
    modifier: Modifier = Modifier,
) {
    val visibleMessages = remember(messages, maxVisibleMessages) {
        companionVisibleMessages(messages, maxVisibleMessages)
    }
    val listState = rememberLazyListState()
    val lastPreviewStatus = visibleMessages.lastOrNull()
        ?.id
        ?.let { imagePreviewCards[it]?.status }
    LaunchedEffect(visibleMessages.lastOrNull()?.id, visibleMessages.lastOrNull()?.text, lastPreviewStatus) {
        if (visibleMessages.isNotEmpty()) {
            listState.animateScrollToItem(visibleMessages.lastIndex)
        }
    }
    if (visibleMessages.isEmpty()) {
        // Empty state: stage bubble already shows status text,
        // so just leave a minimal spacer to maintain layout structure.
        Box(modifier = modifier.fillMaxWidth())
    } else {
        LazyColumn(
            modifier = modifier.fillMaxWidth(),
            state = listState,
            verticalArrangement = Arrangement.spacedBy(12.dp),
            contentPadding = PaddingValues(vertical = 8.dp),
        ) {
            items(
                items = visibleMessages,
                key = { message -> message.id },
            ) { message ->
                ChatMessageBubbleWithPreview(
                    message = message,
                    imagePreview = imagePreviewCards[message.id],
                    onImageRetry = onImageRetry,
                    onImageDismiss = onImageDismiss,
                )
            }
        }
    }
}

@Composable
private fun ChatMessageBubbleWithPreview(
    message: ChatMessage,
    imagePreview: LocalImagePreviewCardUiState?,
    onImageRetry: (String) -> Unit = {},
    onImageDismiss: (String) -> Unit = {},
) {
    val isChild = message.author == MessageAuthor.Child
    val bubbleShape = RoundedCornerShape(if (isChild) 20.dp else 22.dp)
    val bubbleColor = if (isChild) {
        Color(0xFFEAF4FF).copy(alpha = 0.72f)
    } else {
        Color.White.copy(alpha = 0.82f)
    }
    val textColor = if (isChild) {
        Color(0xFF3F4C5D)
    } else {
        Color(0xFF3F4A3F)
    }
    val alignment = if (isChild) Alignment.CenterEnd else Alignment.CenterStart
    val bubbleWidth = if (isChild) 0.70f else 0.82f

    Box(
        modifier = Modifier.fillMaxWidth(),
        contentAlignment = alignment,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth(bubbleWidth)
                .clip(bubbleShape)
                .background(bubbleColor)
                .border(
                    width = 1.dp,
                    color = if (isChild) {
                        Color(0xFFBFD7FF).copy(alpha = 0.28f)
                    } else {
                        companionSoftBorderColor(alpha = 0.50f)
                    },
                    shape = bubbleShape,
                )
                .padding(
                    horizontal = if (isChild) 14.dp else 16.dp,
                    vertical = if (isChild) 9.dp else 12.dp,
                ),
        ) {
            Text(
                text = if (isChild) "我" else "小白狐",
                style = if (isChild) MaterialTheme.typography.labelSmall else MaterialTheme.typography.labelMedium,
                fontWeight = if (isChild) FontWeight.Normal else FontWeight.SemiBold,
                color = textColor.copy(alpha = if (isChild) 0.6f else 0.78f),
            )
            imagePreview?.let { preview ->
                LocalImagePreviewCard(
                    preview = preview,
                    childBubble = isChild,
                    modifier = Modifier.padding(top = 8.dp),
                    onRetry = { onImageRetry(message.id) },
                    onDismiss = { onImageDismiss(message.id) },
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
private fun CompanionFloatingConversationBubbles(
    messages: List<ChatMessage>,
    imagePreviewCards: Map<String, LocalImagePreviewCardUiState>,
    isLandscape: Boolean,
    onImageRetry: (String) -> Unit,
    onImageDismiss: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val visibleMessages = remember(messages) {
        companionVisibleMessages(messages, maxVisibleMessages = 2)
    }
    val visibleSignature = visibleMessages.joinToString(separator = "|") { message ->
        val previewStatus = imagePreviewCards[message.id]?.status?.name.orEmpty()
        "${message.id}:${message.text}:$previewStatus"
    }
    var showBubbles by remember { mutableStateOf(false) }
    LaunchedEffect(visibleSignature) {
        showBubbles = visibleMessages.isNotEmpty()
        if (visibleMessages.isNotEmpty()) {
            delay(6_000)
            showBubbles = false
        }
    }

    Box(modifier = modifier.fillMaxSize()) {
        visibleMessages.forEachIndexed { index, message ->
            val childBubble = message.author == MessageAuthor.Child
            val alignment = when {
                childBubble -> Alignment.BottomEnd
                index == 0 -> Alignment.TopStart
                else -> Alignment.TopEnd
            }
            val horizontalPadding = if (isLandscape) 34.dp else 18.dp
            val verticalPadding = if (isLandscape) 46.dp else 36.dp
            val widthFraction = if (isLandscape) 0.46f else 0.62f
            AnimatedVisibility(
                visible = showBubbles,
                enter = fadeIn(animationSpec = tween(durationMillis = 220)) +
                    slideInVertically(animationSpec = tween(durationMillis = 220)) { it / 6 } +
                    scaleIn(animationSpec = tween(durationMillis = 220), initialScale = 0.97f),
                exit = fadeOut(animationSpec = tween(durationMillis = 220)) +
                    slideOutVertically(animationSpec = tween(durationMillis = 220)) { it / 6 } +
                    scaleOut(animationSpec = tween(durationMillis = 220), targetScale = 0.97f),
                modifier = Modifier
                    .align(alignment)
                    .padding(horizontal = horizontalPadding, vertical = verticalPadding)
                    .fillMaxWidth(widthFraction),
            ) {
                FloatingConversationBubble(
                    message = message,
                    imagePreview = imagePreviewCards[message.id],
                    onImageRetry = { onImageRetry(message.id) },
                    onImageDismiss = { onImageDismiss(message.id) },
                )
            }
        }
    }
}

@Composable
private fun FloatingConversationBubble(
    message: ChatMessage,
    imagePreview: LocalImagePreviewCardUiState?,
    onImageRetry: () -> Unit,
    onImageDismiss: () -> Unit,
) {
    val isChild = message.author == MessageAuthor.Child
    val bubbleShape = RoundedCornerShape(24.dp)
    val bubbleColor = if (isChild) {
        Color(0xFFEAF4FF).copy(alpha = 0.82f)
    } else {
        Color.White.copy(alpha = 0.86f)
    }
    val textColor = if (isChild) {
        Color(0xFF3F4C5D)
    } else {
        Color(0xFF3F4A3F)
    }
    Surface(
        shape = bubbleShape,
        color = bubbleColor,
        shadowElevation = 3.dp,
        border = BorderStroke(
            width = 1.dp,
            color = Color.White.copy(alpha = 0.58f),
        ),
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
        ) {
            Text(
                text = message.text,
                style = MaterialTheme.typography.bodyMedium,
                color = textColor,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
            imagePreview?.let { preview ->
                LocalImagePreviewCard(
                    preview = preview,
                    childBubble = isChild,
                    modifier = Modifier.padding(top = 8.dp),
                    onRetry = onImageRetry,
                    onDismiss = onImageDismiss,
                )
            }
        }
    }
}

@Composable
private fun LocalImagePreviewCard(
    preview: LocalImagePreviewCardUiState,
    childBubble: Boolean,
    modifier: Modifier = Modifier,
    onRetry: (() -> Unit)? = null,
    onDismiss: (() -> Unit)? = null,
) {
    val previewBitmap = remember(preview.previewBytes) {
        preview.previewBytes?.let { bytes ->
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.asImageBitmap()
        }
    }
    val contentColor = if (childBubble) {
        Color(0xFF3F4C5D)
    } else {
        Color(0xFF3F4A3F)
    }
    val statusText = localImagePreviewStatusText(preview.status)
    val cardShape = RoundedCornerShape(16.dp)
    val cardColor = when {
        preview.status == LocalImagePreviewStatus.Failed -> Color(0xFFFFF4E4).copy(alpha = 0.76f)
        childBubble -> Color.White.copy(alpha = 0.58f)
        else -> Color.White.copy(alpha = 0.72f)
    }

    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(cardShape)
            .background(cardColor)
            .border(
                width = 1.dp,
                color = if (preview.status == LocalImagePreviewStatus.Failed) {
                    Color(0xFFFFDDA8).copy(alpha = 0.50f)
                } else {
                    companionSoftBorderColor(alpha = 0.52f)
                },
                shape = cardShape,
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
                    .height(80.dp)
                    .clip(RoundedCornerShape(12.dp)),
            )
        }
        Text(
            text = statusText,
            style = MaterialTheme.typography.labelMedium,
            color = contentColor,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
        if (preview.status == LocalImagePreviewStatus.Failed) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                LocalImagePreviewActionButton(
                    text = "我们可以再试一次",
                    primary = true,
                    onClick = { onRetry?.invoke() },
                )
                LocalImagePreviewActionButton(
                    text = "先不看也可以",
                    primary = false,
                    onClick = { onDismiss?.invoke() },
                )
            }
        }
    }
}

@Composable
private fun LocalImagePreviewActionButton(
    text: String,
    primary: Boolean,
    onClick: () -> Unit,
) {
    val shape = RoundedCornerShape(14.dp)
    Surface(
        modifier = Modifier
            .clip(shape)
            .clickable { onClick() },
        shape = shape,
        color = if (primary) {
            Color.White.copy(alpha = 0.72f)
        } else {
            Color.White.copy(alpha = 0.48f)
        },
        border = BorderStroke(
            width = 1.dp,
            color = Color.White.copy(alpha = 0.58f),
        ),
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelSmall,
            color = if (primary) MaterialTheme.colorScheme.primary else Color(0xFF42546A).copy(alpha = 0.72f),
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 5.dp),
        )
    }
}

internal fun localImagePreviewStatusText(status: LocalImagePreviewStatus): String {
    return when (status) {
        LocalImagePreviewStatus.Uploading -> "正在给小白狐看看"
        LocalImagePreviewStatus.Sent -> "小白狐正在看"
        LocalImagePreviewStatus.Failed -> "这张图还没给小白狐看到"
    }
}

@Composable
private fun LandscapeOperationPanel(
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
    val visibleQuickActions = childCompanionVisibleQuickActions(uiState)

    Column(
        modifier = modifier
            .padding(if (compactLandscape) 4.dp else 8.dp),
        horizontalAlignment = Alignment.End,
    ) {
        ParentEntryHintBar(
            parentEntryHint = parentEntryHint,
            onParentEntryTap = onParentEntryTap,
            onParentEntryLongPress = onParentEntryLongPress,
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(modifier = Modifier.weight(1f))
        if (visibleQuickActions.isNotEmpty()) {
            QuickActionsRow(
                actions = visibleQuickActions,
                enabled = !uiState.isSending,
                onQuickAction = onQuickAction,
            )
            Spacer(modifier = Modifier.height(panelGap))
        }
        val inputTrayShape = companionInputTrayShape(compactLandscape = compactLandscape)
        InputBar(
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = if (compactLandscape) 96.dp else 112.dp)
                .navigationBarsPadding()
                .windowInsetsPadding(WindowInsets.ime)
                .clip(inputTrayShape)
                .background(companionInputTrayColor())
                .border(
                    width = 1.dp,
                    color = companionSoftBorderColor(alpha = 0.48f),
                    shape = inputTrayShape,
                )
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

internal const val PARENT_ENTRY_COMPACT_LABEL = "家长入口"

internal fun parentEntryTapHint(): String = ""

internal fun parentEntryDefaultHint(): String = ""

internal fun parentEntryDefaultLabels(): List<String> = listOf(PARENT_ENTRY_COMPACT_LABEL)

internal fun parentEntryLongPressTargets(): List<ParentEntryTarget> =
    listOf(ParentEntryTarget.Report, ParentEntryTarget.Settings)

internal fun topicShiftChipActions(uiState: ChatUiState): List<QuickActionUi> {
    return emptyList()
}

@Composable
private fun CompanionRoomBackground(isLandscape: Boolean) {
    Image(
        painter = painterResource(id = R.drawable.companion_room_background),
        contentDescription = null,
        contentScale = ContentScale.Crop,
        alignment = if (isLandscape) Alignment.Center else Alignment.Center,
        modifier = Modifier.fillMaxSize(),
    )
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(companionRoomScrimBrush(isLandscape = isLandscape)),
    )
}

@Composable
private fun companionPageBackgroundBrush(): Brush {
    return Brush.verticalGradient(
        colors = companionPageBackgroundColors(),
    )
}

internal fun companionPageBackgroundColors(): List<Color> {
    return listOf(
        Color(0xFFEDF4FF),
        Color(0xFFFFFDF8),
        Color(0xFFFFF2D8),
    )
}

private fun companionRoomScrimBrush(isLandscape: Boolean): Brush {
    return if (isLandscape) {
        Brush.verticalGradient(
            colors = listOf(
                Color.White.copy(alpha = 0.14f),
                Color.White.copy(alpha = 0.05f),
                Color(0xFFFFF1D6).copy(alpha = 0.16f),
            ),
        )
    } else {
        Brush.verticalGradient(
            colors = listOf(
                Color.White.copy(alpha = 0.20f),
                Color.White.copy(alpha = 0.04f),
                Color(0xFFFFE2B5).copy(alpha = 0.22f),
            ),
        )
    }
}

@Composable
private fun CompanionAmbientGlows(
    isLandscape: Boolean,
    compactLandscape: Boolean,
) {
    Box(modifier = Modifier.fillMaxSize()) {
        val topGlowWidth = if (isLandscape) 560.dp else 320.dp
        val topGlowHeight = if (isLandscape) 360.dp else 300.dp
        val warmGlowWidth = if (isLandscape) 520.dp else 340.dp
        val warmGlowHeight = if (isLandscape) 300.dp else 260.dp
        val blurRadius = if (compactLandscape) 42.dp else 56.dp

        Box(
            modifier = Modifier
                .align(Alignment.TopStart)
                .offset(x = (-96).dp, y = (-76).dp)
                .width(topGlowWidth)
                .height(topGlowHeight)
                .blur(blurRadius)
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            Color(0xFFBFD7FF).copy(alpha = 0.36f),
                            Color.Transparent,
                        ),
                    ),
                    shape = CircleShape,
                ),
        )
        Box(
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .offset(x = 90.dp, y = 66.dp)
                .width(warmGlowWidth)
                .height(warmGlowHeight)
                .blur(blurRadius)
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            Color(0xFFFFE3A8).copy(alpha = 0.30f),
                            Color.Transparent,
                        ),
                    ),
                    shape = CircleShape,
                ),
        )
    }
}

private fun companionInputTrayShape(compactLandscape: Boolean): RoundedCornerShape {
    return RoundedCornerShape(if (compactLandscape) 22.dp else 28.dp)
}

private fun companionInputTrayColor(): Color {
    return Color.White.copy(alpha = 0.58f)
}

private fun companionLandscapePanelShape(compactLandscape: Boolean): RoundedCornerShape {
    return RoundedCornerShape(if (compactLandscape) 24.dp else 32.dp)
}

private fun companionLandscapePanelColor(): Color {
    return Color.White.copy(alpha = 0.36f)
}

private fun companionSoftBorderColor(alpha: Float = 0.42f): Color {
    return Color.White.copy(alpha = alpha)
}

internal data class CompanionLayoutWeights(
    val agent: Float,
    val conversation: Float,
)

internal fun companionLayoutWeights(isLandscape: Boolean): CompanionLayoutWeights {
    return if (isLandscape) {
        CompanionLayoutWeights(agent = 0.68f, conversation = 0.32f)
    } else {
        CompanionLayoutWeights(agent = 0.72f, conversation = 0.28f)
    }
}

internal fun companionRecentMessageLimit(isLandscape: Boolean): Int {
    return if (isLandscape) 2 else 1
}

internal fun companionVisibleMessages(
    messages: List<ChatMessage>,
    maxVisibleMessages: Int,
): List<ChatMessage> {
    return messages
        .filterNot(::isStageOnlyStatusMessage)
        .takeLast(maxVisibleMessages.coerceAtLeast(1))
}

internal fun isStageOnlyStatusMessage(message: ChatMessage): Boolean {
    return message.id == "agent-welcome" && message.text in setOf(
        "小白狐在这里。",
        "我在这里。",
    )
}

private val imageContextActionIds = setOf(
    "give_name",
    "image_naming",
    "tell_story",
    "make_story",
    "image_story",
    "say_what_happened",
    "talk_about_image",
    "ask_what_is_this",
)

private val primaryImageCoCreationActionIds = setOf(
    "give_name",
    "image_naming",
    "tell_story",
    "make_story",
    "image_story",
)

internal fun childCompanionVisibleQuickActions(uiState: ChatUiState): List<QuickActionUi> {
    val baseActions = uiState.quickActions.filterNot { action ->
        action.id == "take_photo" ||
            action.id == "share_photo" ||
            action.id == "start_voice" ||
            action.label == "我想说话"
    }
    if (uiState.pendingImageContext == null) {
        return baseActions.filterNot { it.id in imageContextActionIds }
    }
    return baseActions
        .firstOrNull { it.id in primaryImageCoCreationActionIds }
        ?.let { listOf(normalizeImageQuickAction(it)) }
        ?: emptyList()
}

private fun normalizeImageQuickAction(action: QuickActionUi): QuickActionUi {
    return when (action.id) {
        "give_name", "image_naming" -> action.copy(label = "起个名字")
        "tell_story", "make_story", "image_story" -> action.copy(label = "讲一句小故事")
        else -> action
    }
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
            val shape = RoundedCornerShape(22.dp)
            Surface(
                modifier = Modifier
                    .heightIn(min = 44.dp)
                    .clip(shape)
                    .clickable(enabled = enabled) { onQuickAction(action) },
                shape = shape,
                color = Color.White.copy(alpha = if (enabled) 0.72f else 0.38f),
                shadowElevation = 2.dp,
                border = BorderStroke(
                    width = 1.dp,
                    color = Color.White.copy(alpha = 0.58f),
                ),
            ) {
                Text(
                    text = action.label,
                    style = MaterialTheme.typography.labelLarge,
                    color = Color(0xFF42546A).copy(alpha = if (enabled) 0.92f else 0.45f),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
                )
            }
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
    compactLandscape: Boolean,
    onParentEntryTap: () -> Unit,
    onParentEntryLongPress: () -> Unit,
) {
    val horizontalPadding = if (compactLandscape) 16.dp else 24.dp
    val verticalPadding = if (compactLandscape) 10.dp else 18.dp
    val topBarShape = RoundedCornerShape(if (compactLandscape) 18.dp else 24.dp)
    Surface(
        color = Color.White.copy(alpha = 0.56f),
        tonalElevation = 0.dp,
        shadowElevation = 0.dp,
        shape = topBarShape,
        border = BorderStroke(
            width = 1.dp,
            color = companionSoftBorderColor(alpha = 0.38f),
        ),
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
                }
                ParentEntryButton(
                    label = PARENT_ENTRY_COMPACT_LABEL,
                    onTap = onParentEntryTap,
                    onLongPress = onParentEntryLongPress,
                )
            }
            if (!parentEntryHint.isNullOrBlank()) {
                Text(
                    text = parentEntryHint,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.52f),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.padding(
                        start = horizontalPadding,
                        end = horizontalPadding,
                        bottom = if (compactLandscape) 8.dp else 10.dp,
                    ),
                )
            }
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
    val buttonShape = RoundedCornerShape(18.dp)
    Surface(
        modifier = Modifier.combinedClickable(
            onClick = onTap,
            onLongClick = onLongPress,
            onLongClickLabel = "进入家长页面",
        ),
        shape = buttonShape,
        color = Color.White.copy(alpha = 0.64f),
        shadowElevation = 1.dp,
        border = BorderStroke(
            width = 1.dp,
            color = Color.White.copy(alpha = 0.58f),
        ),
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.68f),
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
        horizontalArrangement = Arrangement.End,
    ) {
        if (!parentEntryHint.isNullOrBlank()) {
            Text(
                text = parentEntryHint,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.52f),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier
                    .weight(1f)
                    .padding(end = 8.dp),
            )
        } else {
            Spacer(modifier = Modifier.weight(1f))
        }
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
    messages: List<ChatMessage>,
    imagePreviewCards: Map<String, LocalImagePreviewCardUiState>,
    isLandscape: Boolean,
    compactLandscape: Boolean,
    onImageRetry: (String) -> Unit,
    onImageDismiss: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    var debugMascotStateId by rememberSaveable { mutableStateOf<String?>(null) }
    val debugMascotState = debugMascotStateId?.let(MascotState::fromId)
    val resolvedMascotState = XiaobaohuVisualStateResolver.resolve(presentation.agent).mascotState
    val effectiveMascotState = debugMascotState ?: resolvedMascotState

    Box(modifier = modifier) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Box(modifier = Modifier.weight(1f)) {
                XiaobaohuCompanionStage(
                    agent = presentation.agent,
                    mascotState = effectiveMascotState,
                    compactLandscape = compactLandscape,
                    debugMascotState = debugMascotState,
                    modifier = Modifier.fillMaxSize(),
                )
                CompanionFloatingConversationBubbles(
                    messages = messages,
                    imagePreviewCards = imagePreviewCards,
                    isLandscape = isLandscape,
                    onImageRetry = onImageRetry,
                    onImageDismiss = onImageDismiss,
                    modifier = Modifier.matchParentSize(),
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

private fun foxGlowColorForPhase(phase: ChildTurnUiPhase): Color {
    return when (phase) {
        ChildTurnUiPhase.Ready,
        ChildTurnUiPhase.Resting -> Color(0xFF81C784)       // soft green
        ChildTurnUiPhase.Listening,
        ChildTurnUiPhase.WaitingChild -> Color(0xFF4FC3F7)  // sky blue
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
        ChildTurnUiPhase.Resting -> "我在这里"
        ChildTurnUiPhase.Listening -> "我在听"
        ChildTurnUiPhase.WaitingChild -> "想说的时候再说"
        ChildTurnUiPhase.Recognizing -> "在听懂你的话"
        ChildTurnUiPhase.Sending,
        ChildTurnUiPhase.Thinking -> "在想一想"
        ChildTurnUiPhase.SpeakingPending,
        ChildTurnUiPhase.Speaking -> "在说给你听"
        ChildTurnUiPhase.ImageProcessing -> "小白狐正在看"
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
                    statusText = "我在这里。",
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
                    statusText = "我在听。",
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
                    statusText = "我在听。",
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
