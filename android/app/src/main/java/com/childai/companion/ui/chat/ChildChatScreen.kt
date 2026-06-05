package com.childai.companion.ui.chat

import android.content.Intent
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Build
import android.provider.Settings
import android.speech.tts.TextToSpeech
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
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
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.aspectRatio
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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
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
import androidx.compose.ui.graphics.TransformOrigin
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.State
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.BiasAlignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.childai.companion.R
import androidx.lifecycle.viewmodel.compose.viewModel
import com.childai.companion.config.DevSettings
import com.childai.companion.data.attachment.PhotoUploadPayload
import com.childai.companion.data.conversation.CompanionObjectMeta
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.debug.HouseObjectDebugRepository
import com.childai.companion.mascot.MascotState
import com.childai.companion.ui.chat.strangedoor.StrangeDoorAndroidResources
import com.childai.companion.ui.chat.strangedoor.StrangeDoorAssetKey
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoSnapshot
import com.childai.companion.ui.chat.strangedoor.StrangeDoorHomeEventAction
import com.childai.companion.ui.chat.strangedoor.StrangeDoorHomeEventActionId
import com.childai.companion.ui.chat.strangedoor.StrangeDoorHomeEventPanel
import com.childai.companion.ui.chat.strangedoor.StrangeDoorHomeEventUiModel
import com.childai.companion.ui.chat.strangedoor.toHomeEventUiModel
import com.childai.companion.ui.parent.ParentEntryCredentialDialog
import com.childai.companion.ui.parent.ParentEntryTarget
import com.childai.companion.ui.parent.ParentCredentialGate
import com.childai.companion.ui.theme.ChildAiCompanionTheme
import com.childai.companion.voice.MediaPlayerAudioUrlPlayer
import com.childai.companion.voice.NoOpTtsController
import com.childai.companion.voice.RemoteAudioTtsController
import java.io.File
import java.net.URL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
fun ChildChatScreen(
    modifier: Modifier = Modifier,
    onOpenParentSettings: () -> Unit = {},
    onOpenParentReport: () -> Unit = {},
    onOpenXiaozhantai: () -> Unit = {},
    viewModel: ChatViewModel = viewModel(),
    requireParentCredential: Boolean = false,
    verifyParentCredential: suspend (String) -> Boolean = { false },
    houseObjectDebugRepository: HouseObjectDebugRepository? = null,
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
        viewModel.activateStrangeDoorDemo()
    }
    LaunchedEffect(uiState.xiaozhantaiSavedItemIdForNavigation) {
        val savedItemId = uiState.xiaozhantaiSavedItemIdForNavigation
        if (!savedItemId.isNullOrBlank()) {
            onOpenXiaozhantai()
            viewModel.consumeXiaozhantaiSaveNavigation()
        }
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
        onImageSaveToXiaozhantai = viewModel::requestSavePhotoToXiaozhantai,
        onXiaozhantaiSaveConfirm = viewModel::confirmXiaozhantaiSave,
        onXiaozhantaiSaveDismiss = viewModel::cancelXiaozhantaiSave,
        onOpenParentSettings = onOpenParentSettings,
        onOpenParentReport = onOpenParentReport,
        onOpenXiaozhantai = onOpenXiaozhantai,
        onStrangeDoorChoosePhoto = viewModel::chooseStrangeDoorPhotoMethod,
        onStrangeDoorChooseRiddle = viewModel::chooseStrangeDoorRiddleMethod,
        onStrangeDoorSwitchMethod = viewModel::returnToStrangeDoorMethodChoice,
        requireParentCredential = requireParentCredential,
        verifyParentCredential = verifyParentCredential,
        houseObjectDebugRepository = houseObjectDebugRepository,
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
    onImageSaveToXiaozhantai: (String) -> Unit = {},
    onXiaozhantaiSaveConfirm: () -> Unit = {},
    onXiaozhantaiSaveDismiss: () -> Unit = {},
    onOpenParentSettings: () -> Unit,
    onOpenParentReport: () -> Unit,
    onOpenXiaozhantai: () -> Unit,
    onStrangeDoorChoosePhoto: () -> Unit,
    onStrangeDoorChooseRiddle: () -> Unit,
    onStrangeDoorSwitchMethod: () -> Unit,
    requireParentCredential: Boolean,
    verifyParentCredential: suspend (String) -> Boolean,
    houseObjectDebugRepository: HouseObjectDebugRepository?,
    modifier: Modifier = Modifier,
) {
    val coroutineScope = rememberCoroutineScope()
    var pendingParentEntry by rememberSaveable { mutableStateOf<ParentEntryTarget?>(null) }
    var parentCredentialInput by rememberSaveable { mutableStateOf("") }
    var parentCredentialError by rememberSaveable { mutableStateOf<String?>(null) }
    var parentCredentialSubmitting by rememberSaveable { mutableStateOf(false) }
    var parentEntryHint by rememberSaveable { mutableStateOf<String?>(null) }
    var showParentEntryChoices by rememberSaveable { mutableStateOf(false) }
    var pendingImageSourcePurpose by rememberSaveable { mutableStateOf<String?>(null) }
    var showHouseObjectDebugPanel by rememberSaveable { mutableStateOf(false) }
    var houseObjectDebugVisualKind by rememberSaveable { mutableStateOf("star") }
    var houseObjectDebugState by rememberSaveable { mutableStateOf("co_create") }
    var houseObjectDebugLocation by rememberSaveable { mutableStateOf("窗边") }
    var houseObjectDebugStatus by rememberSaveable { mutableStateOf<String?>(null) }
    var houseObjectDebugBusy by rememberSaveable { mutableStateOf(false) }
    var houseObjectDebugPreview by remember { mutableStateOf<CompanionObjectMeta?>(null) }
    val showHouseObjectDebugEntry = DevSettings.houseObjectDebugToolsEnabled
    val imageInputLaunchers = rememberImageInputLaunchers(
        onCaptured = onPhotoCaptured,
        onFailed = onPhotoCaptureFailed,
    )
    val showGalleryEntry = remember {
        companionSupportsGalleryPicker()
    }

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
            showHouseObjectDebugEntry = showHouseObjectDebugEntry,
            onOpenHouseObjectDebug = {
                showParentEntryChoices = false
                showHouseObjectDebugPanel = true
            },
            onDismiss = { showParentEntryChoices = false },
        )
    }
    if (showHouseObjectDebugPanel) {
        HouseObjectDebugDialog(
            visualKind = houseObjectDebugVisualKind,
            state = houseObjectDebugState,
            lightLocation = houseObjectDebugLocation,
            statusText = houseObjectDebugStatus,
            isBusy = houseObjectDebugBusy,
            canUseRemoteDebug = houseObjectDebugRepository != null,
            onVisualKindChange = { houseObjectDebugVisualKind = it },
            onStateChange = { houseObjectDebugState = it },
            onLightLocationChange = { houseObjectDebugLocation = it },
            onPreview = {
                houseObjectDebugPreview = houseObjectDebugBuildPreviewMeta(
                    visualKind = houseObjectDebugVisualKind,
                    state = houseObjectDebugState,
                    lightLocation = houseObjectDebugLocation,
                )
                houseObjectDebugStatus = if (houseObjectDebugPreview == null) {
                    "本地预览已清空"
                } else {
                    "本地预览已更新，不写入数据库"
                }
            },
            onCreateRemote = {
                val repository = houseObjectDebugRepository
                if (
                    repository != null &&
                    houseObjectDebugCanPersist(houseObjectDebugState) &&
                    !houseObjectDebugBusy
                ) {
                    houseObjectDebugBusy = true
                    houseObjectDebugStatus = "正在创建测试小客人"
                    coroutineScope.launch {
                        runCatching {
                            repository.create(
                                visualKind = houseObjectDebugVisualKind,
                                state = houseObjectDebugState,
                                lightLocation = houseObjectDebugLocation,
                            )
                        }.onSuccess { response ->
                            houseObjectDebugPreview = response.companionObject
                            houseObjectDebugStatus = "已真实落库，并显示当前测试状态"
                        }.onFailure { error ->
                            houseObjectDebugStatus = "真实创建失败：${error.message.orEmpty().take(80)}"
                        }
                        houseObjectDebugBusy = false
                    }
                }
            },
            onResetRemote = {
                val repository = houseObjectDebugRepository
                if (repository != null && !houseObjectDebugBusy) {
                    houseObjectDebugBusy = true
                    houseObjectDebugStatus = "正在重置当前 child"
                    coroutineScope.launch {
                        runCatching {
                            repository.reset()
                        }.onSuccess { response ->
                            houseObjectDebugPreview = null
                            houseObjectDebugStatus = "已 retired ${response.retiredCount} 个小客人"
                        }.onFailure { error ->
                            houseObjectDebugStatus = "重置失败：${error.message.orEmpty().take(80)}"
                        }
                        houseObjectDebugBusy = false
                    }
                }
            },
            onDismiss = { showHouseObjectDebugPanel = false },
        )
    }
    uiState.xiaozhantaiSaveDraft?.let { draft ->
        XiaozhantaiSaveDialog(
            draft = draft,
            onConfirm = onXiaozhantaiSaveConfirm,
            onDismiss = onXiaozhantaiSaveDismiss,
        )
    }
    pendingImageSourcePurpose?.let { imagePurpose ->
        CompanionImageSourceDialog(
            showGalleryEntry = showGalleryEntry,
            onCapturePhoto = {
                pendingImageSourcePurpose = null
                imageInputLaunchers.capturePhoto(imagePurpose)
            },
            onPickFromGallery = {
                pendingImageSourcePurpose = null
                imageInputLaunchers.pickFromGallery(imagePurpose)
            },
            onDismiss = { pendingImageSourcePurpose = null },
        )
    }

    fun handleQuickAction(action: QuickActionUi) {
        when (action.id) {
            "companion_friend_image" -> pendingImageSourcePurpose = IMAGE_PURPOSE_SHARE
            else -> onQuickAction(action)
        }
    }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = MaterialTheme.colorScheme.background,
        contentWindowInsets = WindowInsets(0.dp),
    ) { innerPadding ->
        BoxWithConstraints(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
                .background(companionPageBackgroundBrush()),
        ) {
            val viewportClass = companionRoomViewportClass(maxWidth = maxWidth, maxHeight = maxHeight)
            val isLandscape = viewportClass.isLandscape
            val compactLandscape = companionLandscapeIsCompact(
                maxWidth = maxWidth,
                maxHeight = maxHeight,
                viewportClass = viewportClass,
            )
            val effectiveCompanionObject = houseObjectDebugPreview
                ?: uiState.sessionState?.companionObject

            CompanionRoomBackground(viewportClass = viewportClass)
            CompanionAmbientGlows(
                isLandscape = isLandscape,
                compactLandscape = compactLandscape,
            )

            val strangeDoorSnapshot = uiState.strangeDoorDemo
            if (strangeDoorSnapshot != null) {
                StrangeDoorHomeEventScreen(
                    snapshot = strangeDoorSnapshot,
                    viewportClass = viewportClass,
                    compactLandscape = compactLandscape,
                    parentEntryHint = parentEntryHint,
                    onParentEntryTap = {
                        parentEntryHint = parentEntryTapHint()
                    },
                    onParentEntryLongPress = {
                        parentEntryHint = null
                        showParentEntryChoices = true
                    },
                    onOpenXiaozhantai = onOpenXiaozhantai,
                    onChoosePhoto = onStrangeDoorChoosePhoto,
                    onChooseRiddle = onStrangeDoorChooseRiddle,
                    onSwitchMethod = onStrangeDoorSwitchMethod,
                    modifier = Modifier.fillMaxSize(),
                )
            } else if (isLandscape) {
                // Landscape: keep the room and mascot as the scene, with controls only as a light rail.
                val layoutWeights = companionLayoutWeights(viewportClass = viewportClass)
                val layoutMetrics = companionLandscapeLayoutMetrics(
                    viewportClass = viewportClass,
                    compactLandscape = compactLandscape,
                )

                val pinnedBubbleMessageId = companionPinnedBubbleMessageId(uiState)
                Row(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(
                            horizontal = layoutMetrics.horizontalPadding,
                            vertical = layoutMetrics.verticalPadding,
                        ),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    AgentPanel(
                        presentation = uiState.interactionPresentation,
                        messages = uiState.messages,
                        imagePreviewCards = uiState.imagePreviewCards,
                        xiaozhantaiSavePromptPreview = uiState.xiaozhantaiSavePromptPreview,
                        pinnedBubbleMessageId = pinnedBubbleMessageId,
                        viewportClass = viewportClass,
                        compactLandscape = compactLandscape,
                        companionObject = effectiveCompanionObject,
                        onImageRetry = onImageRetry,
                        onImageDismiss = onImageDismiss,
                        onImageSaveToXiaozhantai = onImageSaveToXiaozhantai,
                        modifier = Modifier
                            .weight(layoutWeights.agent)
                            .fillMaxHeight(),
                    )
                    Spacer(modifier = Modifier.width(layoutMetrics.columnGap))
                    LandscapeOperationPanel(
                        uiState = uiState,
                        compactLandscape = compactLandscape,
                        maxPanelWidth = layoutMetrics.operationPanelMaxWidth,
                        parentEntryHint = parentEntryHint,
                        presentation = uiState.interactionPresentation,
                        onParentEntryTap = {
                            parentEntryHint = parentEntryTapHint()
                        },
                        onParentEntryLongPress = {
                            parentEntryHint = null
                            showParentEntryChoices = true
                        },
                        onOpenXiaozhantai = onOpenXiaozhantai,
                        onSend = onSend,
                        onQuickAction = ::handleQuickAction,
                        onStopTts = onStopTts,
                        onToggleTtsMuted = onToggleTtsMuted,
                        onOpenTtsSettings = onOpenTtsSettings,
                        onInstallTtsData = onInstallTtsData,
                        onOpenImageInput = { pendingImageSourcePurpose = it },
                        viewportClass = viewportClass,
                        modifier = Modifier
                            .weight(layoutWeights.conversation)
                            .fillMaxHeight(),
                    )
                }
            } else {
                // Portrait: fox lives in the room; dialogue floats around it instead of sitting in a chat card.
                val portraitMetrics = companionPortraitLayoutMetrics(viewportClass = viewportClass)
                val horizontalPadding = portraitMetrics.horizontalPadding
                val verticalPadding = portraitMetrics.verticalPadding
                val inputWidth = minOf(
                    (maxWidth - horizontalPadding * 2f).coerceAtLeast(280.dp),
                    portraitMetrics.inputMaxWidth,
                )
                val visibleQuickActions = childCompanionVisibleQuickActions(uiState)
                val pinnedBubbleMessageId = companionPinnedBubbleMessageId(uiState)

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
                        onOpenXiaozhantai = onOpenXiaozhantai,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    // Fox hero area — 55% of screen
                    AgentPanel(
                        presentation = uiState.interactionPresentation,
                        messages = uiState.messages,
                        imagePreviewCards = uiState.imagePreviewCards,
                        xiaozhantaiSavePromptPreview = uiState.xiaozhantaiSavePromptPreview,
                        pinnedBubbleMessageId = pinnedBubbleMessageId,
                        viewportClass = viewportClass,
                        compactLandscape = false,
                        companionObject = effectiveCompanionObject,
                        onImageRetry = onImageRetry,
                        onImageDismiss = onImageDismiss,
                        onImageSaveToXiaozhantai = onImageSaveToXiaozhantai,
                        modifier = Modifier
                            .fillMaxWidth()
                            .weight(1f),
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    if (visibleQuickActions.isNotEmpty()) {
                        QuickActionsRow(
                            actions = visibleQuickActions,
                            enabled = !uiState.isSending,
                            onQuickAction = ::handleQuickAction,
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                    }
                    InputBar(
                        modifier = Modifier
                            .width(inputWidth)
                            .navigationBarsPadding()
                            .windowInsetsPadding(WindowInsets.ime)
                            .padding(bottom = 4.dp),
                        onSend = onSend,
                        enabled = !uiState.isSending,
                        voice = uiState.voice,
                        tts = uiState.tts,
                        presentation = uiState.interactionPresentation,
                        onStopTts = onStopTts,
                        onToggleTtsMuted = onToggleTtsMuted,
                        onOpenTtsSettings = onOpenTtsSettings,
                        onInstallTtsData = onInstallTtsData,
                        onOpenImageInput = { pendingImageSourcePurpose = it },
                        playfulControls = true,
                        playfulCompactControls = viewportClass == CompanionRoomViewportClass.PortraitExpanded,
                    )
                }
            }
        }
    }
}

@Composable
private fun StrangeDoorHomeEventScreen(
    snapshot: StrangeDoorDemoSnapshot,
    viewportClass: CompanionRoomViewportClass,
    compactLandscape: Boolean,
    parentEntryHint: String?,
    onParentEntryTap: () -> Unit,
    onParentEntryLongPress: () -> Unit,
    onOpenXiaozhantai: () -> Unit,
    onChoosePhoto: () -> Unit,
    onChooseRiddle: () -> Unit,
    onSwitchMethod: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val model = remember(snapshot) {
        snapshot.toHomeEventUiModel()
    }

    fun handleAction(action: StrangeDoorHomeEventAction) {
        when (action.id) {
            StrangeDoorHomeEventActionId.ChoosePhoto -> onChoosePhoto()
            StrangeDoorHomeEventActionId.ChooseRiddle -> onChooseRiddle()
            StrangeDoorHomeEventActionId.SwitchMethod -> onSwitchMethod()
            StrangeDoorHomeEventActionId.OpenPhotoCapture -> Unit
        }
    }

    if (!StrangeDoorAndroidResources.allRequiredResourcesReady()) {
        StrangeDoorAssetBlockedNotice(modifier = modifier)
        return
    }

    BoxWithConstraints(modifier = modifier) {
        val isLandscape = viewportClass.isLandscape
        val horizontalPadding = if (isLandscape) 28.dp else 18.dp
        val verticalPadding = if (isLandscape) 18.dp else 12.dp

        if (isLandscape) {
            Row(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = horizontalPadding, vertical = verticalPadding),
                horizontalArrangement = Arrangement.spacedBy(if (compactLandscape) 14.dp else 24.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(
                    modifier = Modifier
                        .weight(0.62f)
                        .fillMaxHeight(),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    StrangeDoorEventTitle(model.title, compact = compactLandscape)
                    Spacer(modifier = Modifier.height(if (compactLandscape) 6.dp else 10.dp))
                    StrangeDoorEventScene(
                        model = model,
                        viewportClass = viewportClass,
                        modifier = Modifier
                            .fillMaxWidth()
                            .weight(1f),
                    )
                }
                Column(
                    modifier = Modifier
                        .weight(0.38f)
                        .fillMaxHeight(),
                    horizontalAlignment = Alignment.End,
                ) {
                    ParentEntryHintBar(
                        parentEntryHint = parentEntryHint,
                        onParentEntryTap = onParentEntryTap,
                        onParentEntryLongPress = onParentEntryLongPress,
                        onOpenXiaozhantai = onOpenXiaozhantai,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Spacer(modifier = Modifier.weight(1f))
                    StrangeDoorPromptPanel(
                        model = model,
                        compact = compactLandscape,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Spacer(modifier = Modifier.height(if (compactLandscape) 10.dp else 14.dp))
                    StrangeDoorActionRow(
                        actions = model.actions,
                        compact = compactLandscape,
                        onAction = ::handleAction,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Spacer(modifier = Modifier.weight(1f))
                }
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = horizontalPadding, vertical = verticalPadding),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                ParentEntryHintBar(
                    parentEntryHint = parentEntryHint,
                    onParentEntryTap = onParentEntryTap,
                    onParentEntryLongPress = onParentEntryLongPress,
                    onOpenXiaozhantai = onOpenXiaozhantai,
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(modifier = Modifier.height(6.dp))
                StrangeDoorEventTitle(model.title, compact = false)
                Spacer(modifier = Modifier.height(8.dp))
                StrangeDoorEventScene(
                    model = model,
                    viewportClass = viewportClass,
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                )
                Spacer(modifier = Modifier.height(8.dp))
                StrangeDoorPromptPanel(
                    model = model,
                    compact = false,
                    modifier = Modifier
                        .fillMaxWidth()
                        .widthIn(max = 520.dp),
                )
                Spacer(modifier = Modifier.height(10.dp))
                StrangeDoorActionRow(
                    actions = model.actions,
                    compact = false,
                    onAction = ::handleAction,
                    modifier = Modifier
                        .fillMaxWidth()
                        .widthIn(max = 520.dp)
                        .navigationBarsPadding(),
                )
            }
        }
    }
}

@Composable
private fun StrangeDoorAssetBlockedNotice(
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier.padding(24.dp),
        contentAlignment = Alignment.Center,
    ) {
        Surface(
            shape = RoundedCornerShape(18.dp),
            color = Color(0xFFFFF7F2).copy(alpha = 0.92f),
            border = BorderStroke(1.dp, Color(0xFFE9A690).copy(alpha = 0.60f)),
        ) {
            Text(
                text = "开发期错误：奇怪小门素材缺失，D2 验收阻塞",
                style = MaterialTheme.typography.bodyLarge,
                color = Color(0xFF8A4A3A),
                modifier = Modifier.padding(horizontal = 18.dp, vertical = 14.dp),
            )
        }
    }
}

@Composable
private fun StrangeDoorEventTitle(
    title: String,
    compact: Boolean,
) {
    Text(
        text = title,
        style = if (compact) MaterialTheme.typography.titleLarge else MaterialTheme.typography.headlineSmall,
        fontWeight = FontWeight.SemiBold,
        color = Color(0xFF3F4A3F),
        textAlign = TextAlign.Center,
        maxLines = 2,
        overflow = TextOverflow.Ellipsis,
        modifier = Modifier.fillMaxWidth(),
    )
}

@Composable
private fun StrangeDoorEventScene(
    model: StrangeDoorHomeEventUiModel,
    viewportClass: CompanionRoomViewportClass,
    modifier: Modifier = Modifier,
) {
    BoxWithConstraints(modifier = modifier) {
        val isLandscape = viewportClass.isLandscape
        val doorSize = minOf(
            maxWidth * if (isLandscape) 0.48f else 0.58f,
            maxHeight * if (isLandscape) 0.86f else 0.72f,
        ).coerceIn(
            minimumValue = if (isLandscape) 190.dp else 170.dp,
            maximumValue = if (isLandscape) 430.dp else 360.dp,
        )
        val foxSize = minOf(
            maxWidth * if (isLandscape) 0.42f else 0.52f,
            maxHeight * if (isLandscape) 0.74f else 0.58f,
        ).coerceIn(
            minimumValue = if (isLandscape) 170.dp else 150.dp,
            maximumValue = if (isLandscape) 380.dp else 310.dp,
        )
        val doorAlignment = if (isLandscape) Alignment.BottomEnd else Alignment.BottomEnd
        val foxAlignment = if (isLandscape) Alignment.BottomStart else Alignment.BottomStart

        Box(modifier = Modifier.fillMaxSize()) {
            Image(
                painter = painterResource(
                    id = StrangeDoorAndroidResources.drawableResId(StrangeDoorAssetKey.GroundShadow),
                ),
                contentDescription = null,
                contentScale = ContentScale.Fit,
                modifier = Modifier
                    .align(doorAlignment)
                    .offset(y = 12.dp)
                    .size(width = doorSize * 0.92f, height = doorSize * 0.24f),
            )
            CartoonAgentView(
                agent = FoxAgentUiState(
                    mood = FoxMood.Warm,
                    motion = FoxMotion.GentleIdle,
                    statusText = "",
                ),
                debugMascotState = MascotState.Idle,
                visualScaleMultiplier = if (isLandscape) 1.04f else 0.96f,
                modifier = Modifier
                    .align(foxAlignment)
                    .offset(
                        x = if (isLandscape) 6.dp else (-8).dp,
                        y = if (isLandscape) 8.dp else 6.dp,
                    )
                    .size(foxSize),
            )
            Box(
                modifier = Modifier
                    .align(doorAlignment)
                    .size(doorSize),
            ) {
                Image(
                    painter = painterResource(
                        id = StrangeDoorAndroidResources.drawableResId(model.doorAssetKey),
                    ),
                    contentDescription = null,
                    contentScale = ContentScale.Fit,
                    modifier = Modifier.fillMaxSize(),
                )
                Image(
                    painter = painterResource(
                        id = StrangeDoorAndroidResources.drawableResId(StrangeDoorAssetKey.RoundLock),
                    ),
                    contentDescription = null,
                    contentScale = ContentScale.Fit,
                    modifier = Modifier
                        .align(Alignment.Center)
                        .offset(y = doorSize * 0.03f)
                        .size(doorSize * 0.22f),
                )
            }
        }
    }
}

@Composable
private fun StrangeDoorPromptPanel(
    model: StrangeDoorHomeEventUiModel,
    compact: Boolean,
    modifier: Modifier = Modifier,
) {
    when (model.panel) {
        StrangeDoorHomeEventPanel.SpeechBubble -> StrangeDoorSpeechBubble(
            lines = model.bubbleLines,
            compact = compact,
            modifier = modifier,
        )

        StrangeDoorHomeEventPanel.ToolCard -> StrangeDoorImagePanel(
            backgroundKey = StrangeDoorAssetKey.ToolCardPanel,
            text = model.bubbleLines.joinToString(separator = "\n"),
            compact = compact,
            aspectRatio = 4f / 3f,
            modifier = modifier,
        )

        StrangeDoorHomeEventPanel.Riddle -> StrangeDoorImagePanel(
            backgroundKey = StrangeDoorAssetKey.RiddlePanel,
            text = model.question.orEmpty(),
            compact = compact,
            aspectRatio = 2f,
            modifier = modifier,
        )
    }
}

@Composable
private fun StrangeDoorSpeechBubble(
    lines: List<String>,
    compact: Boolean,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(if (compact) 20.dp else 24.dp),
        color = Color.White.copy(alpha = 0.82f),
        shadowElevation = 2.dp,
        border = BorderStroke(1.dp, Color.White.copy(alpha = 0.64f)),
    ) {
        Text(
            text = lines.joinToString(separator = "\n"),
            style = if (compact) MaterialTheme.typography.bodyMedium else MaterialTheme.typography.bodyLarge,
            color = Color(0xFF3F4A3F),
            modifier = Modifier.padding(
                horizontal = if (compact) 14.dp else 18.dp,
                vertical = if (compact) 12.dp else 15.dp,
            ),
        )
    }
}

@Composable
private fun StrangeDoorImagePanel(
    backgroundKey: StrangeDoorAssetKey,
    text: String,
    compact: Boolean,
    aspectRatio: Float,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .aspectRatio(aspectRatio)
            .sizeIn(maxHeight = if (compact) 170.dp else 210.dp),
        contentAlignment = Alignment.Center,
    ) {
        Image(
            painter = painterResource(id = StrangeDoorAndroidResources.drawableResId(backgroundKey)),
            contentDescription = null,
            contentScale = ContentScale.Fit,
            modifier = Modifier.fillMaxSize(),
        )
        Text(
            text = text,
            style = if (compact) MaterialTheme.typography.bodyMedium else MaterialTheme.typography.bodyLarge,
            color = Color(0xFF3F4A3F),
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(horizontal = 22.dp, vertical = 16.dp),
        )
    }
}

@Composable
private fun StrangeDoorActionRow(
    actions: List<StrangeDoorHomeEventAction>,
    compact: Boolean,
    onAction: (StrangeDoorHomeEventAction) -> Unit,
    modifier: Modifier = Modifier,
) {
    BoxWithConstraints(modifier = modifier) {
        val useColumn = maxWidth < 360.dp
        val gap = if (compact) 8.dp else 10.dp
        if (useColumn) {
            Column(verticalArrangement = Arrangement.spacedBy(gap)) {
                actions.forEachIndexed { index, action ->
                    StrangeDoorActionButton(
                        action = action,
                        primary = index == 0,
                        onClick = { onAction(action) },
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            }
        } else {
            Row(horizontalArrangement = Arrangement.spacedBy(gap)) {
                actions.forEachIndexed { index, action ->
                    StrangeDoorActionButton(
                        action = action,
                        primary = index == 0,
                        onClick = { onAction(action) },
                        modifier = Modifier.weight(1f),
                    )
                }
            }
        }
    }
}

@Composable
private fun StrangeDoorActionButton(
    action: StrangeDoorHomeEventAction,
    primary: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    if (primary) {
        Button(
            onClick = onClick,
            enabled = action.enabled,
            shape = RoundedCornerShape(26.dp),
            modifier = modifier.heightIn(min = 54.dp),
        ) {
            Text(
                text = action.label,
                style = MaterialTheme.typography.titleMedium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    } else {
        OutlinedButton(
            onClick = onClick,
            enabled = action.enabled,
            shape = RoundedCornerShape(26.dp),
            modifier = modifier.heightIn(min = 54.dp),
        ) {
            Text(
                text = action.label,
                style = MaterialTheme.typography.titleMedium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun CompanionImageSourceDialog(
    showGalleryEntry: Boolean,
    onCapturePhoto: () -> Unit,
    onPickFromGallery: () -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(text = "给小白狐看看")
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Button(
                    onClick = onCapturePhoto,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(text = "拍一张照片")
                }
                if (showGalleryEntry) {
                    OutlinedButton(
                        onClick = onPickFromGallery,
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(text = "从相册选")
                    }
                }
            }
        },
        confirmButton = {},
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text(text = "先不看")
            }
        },
    )
}

internal fun companionSupportsGalleryPicker(
    manufacturer: String = Build.MANUFACTURER,
    brand: String = Build.BRAND,
    model: String = Build.MODEL,
): Boolean {
    val fingerprint = listOf(manufacturer, brand, model)
        .joinToString(" ")
        .lowercase()
    if ("jdn2" in fingerprint) return false
    if ("honor" in fingerprint && "pad" in fingerprint) return false
    return true
}

@Composable
private fun ChatConversationPanel(
    uiState: ChatUiState,
    isLandscape: Boolean,
    onQuickAction: (QuickActionUi) -> Unit,
    onImageRetry: (String) -> Unit = {},
    onImageDismiss: (String) -> Unit = {},
    onImageSaveToXiaozhantai: (String) -> Unit = {},
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
            onImageSaveToXiaozhantai = onImageSaveToXiaozhantai,
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
    onImageSaveToXiaozhantai: (String) -> Unit = {},
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
                    onImageSaveToXiaozhantai = onImageSaveToXiaozhantai,
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
    onImageSaveToXiaozhantai: (String) -> Unit = {},
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
                    onSaveToXiaozhantai = { onImageSaveToXiaozhantai(message.id) },
                )
            }
            message.xiaozhantaiRecallCard?.let { recallCard ->
                XiaozhantaiRecallChatCard(
                    card = recallCard,
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
private fun CompanionFloatingConversationBubbles(
    messages: List<ChatMessage>,
    imagePreviewCards: Map<String, LocalImagePreviewCardUiState>,
    isLandscape: Boolean,
    pinnedMessageId: String?,
    onImageRetry: (String) -> Unit,
    onImageDismiss: (String) -> Unit,
    onImageSaveToXiaozhantai: (String) -> Unit,
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
    LaunchedEffect(visibleSignature, pinnedMessageId) {
        showBubbles = visibleMessages.isNotEmpty()
        val pinnedVisible = pinnedMessageId != null && visibleMessages.any { it.id == pinnedMessageId }
        if (visibleMessages.isNotEmpty() && !pinnedVisible) {
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
                    onImageSaveToXiaozhantai = { onImageSaveToXiaozhantai(message.id) },
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
    onImageSaveToXiaozhantai: () -> Unit,
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
                    onSaveToXiaozhantai = onImageSaveToXiaozhantai,
                )
            }
            message.xiaozhantaiRecallCard?.let { recallCard ->
                XiaozhantaiRecallChatCard(
                    card = recallCard,
                    compact = true,
                    modifier = Modifier.padding(top = 8.dp),
                )
            }
        }
    }
}

@Composable
private fun XiaozhantaiRecallChatCard(
    card: XiaozhantaiRecallCardUiState,
    modifier: Modifier = Modifier,
    compact: Boolean = false,
) {
    val bitmap by rememberXiaozhantaiRecallPhotoBitmap(card.photoUri)
    val shape = RoundedCornerShape(if (compact) 14.dp else 16.dp)
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = shape,
        color = Color(0xFFF7FBFF).copy(alpha = 0.78f),
        border = BorderStroke(1.dp, companionSoftBorderColor(alpha = 0.46f)),
        shadowElevation = 0.dp,
    ) {
        Row(
            modifier = Modifier.padding(if (compact) 8.dp else 10.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            XiaozhantaiRecallThumbnail(
                bitmap = bitmap,
                compact = compact,
            )
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(3.dp),
            ) {
                Text(
                    text = card.name,
                    style = if (compact) MaterialTheme.typography.labelLarge else MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    color = Color(0xFF4F6072),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    text = "来自小展台",
                    style = MaterialTheme.typography.labelSmall,
                    color = Color(0xFF6A7B88).copy(alpha = 0.78f),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

@Composable
private fun XiaozhantaiRecallThumbnail(
    bitmap: ImageBitmap?,
    compact: Boolean,
) {
    val shape = RoundedCornerShape(if (compact) 10.dp else 12.dp)
    val modifier = Modifier
        .size(if (compact) 46.dp else 58.dp)
        .clip(shape)
    if (bitmap != null) {
        Image(
            bitmap = bitmap,
            contentDescription = null,
            contentScale = ContentScale.Crop,
            modifier = modifier,
        )
    } else {
        Box(
            modifier = modifier.background(
                brush = Brush.linearGradient(
                    colors = listOf(
                        Color(0xFFFFF7E8),
                        Color(0xFFEAF5FF),
                    ),
                ),
            ),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = "照片",
                style = MaterialTheme.typography.labelSmall,
                color = Color(0xFF7A8998).copy(alpha = 0.76f),
            )
        }
    }
}

@Composable
private fun rememberXiaozhantaiRecallPhotoBitmap(photoUri: String): State<ImageBitmap?> {
    val context = LocalContext.current
    return produceState<ImageBitmap?>(initialValue = null, photoUri, context) {
        value = withContext(Dispatchers.IO) {
            runCatching {
                val uri = Uri.parse(photoUri)
                val bitmap = when (uri.scheme?.lowercase()) {
                    "content" -> context.contentResolver.openInputStream(uri)?.use(BitmapFactory::decodeStream)
                    "file" -> BitmapFactory.decodeFile(uri.path)
                    "http", "https" -> URL(photoUri).openStream().use(BitmapFactory::decodeStream)
                    else -> BitmapFactory.decodeFile(File(photoUri).absolutePath)
                }
                bitmap?.asImageBitmap()
            }.getOrNull()
        }
    }
}

@Composable
private fun XiaozhantaiSavePromptBubble(
    preview: LocalImagePreviewCardUiState?,
    isLandscape: Boolean,
    onSaveToXiaozhantai: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val card = preview ?: return
    val previewBitmap = remember(card.previewBytes) {
        card.previewBytes?.let { bytes ->
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.asImageBitmap()
        }
    }
    Box(modifier = modifier.fillMaxSize()) {
        Surface(
            modifier = Modifier
                .align(Alignment.BottomStart)
                .padding(
                    start = if (isLandscape) 32.dp else 26.dp,
                    bottom = if (isLandscape) 26.dp else 30.dp,
                )
                .sizeIn(maxWidth = if (isLandscape) 280.dp else 300.dp),
            shape = RoundedCornerShape(24.dp),
            color = Color.White.copy(alpha = 0.82f),
            shadowElevation = 3.dp,
            border = BorderStroke(
                width = 1.dp,
                color = Color.White.copy(alpha = 0.62f),
            ),
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                if (previewBitmap != null) {
                    Image(
                        bitmap = previewBitmap,
                        contentDescription = "可放入小展台的照片",
                        contentScale = ContentScale.Crop,
                        modifier = Modifier
                            .size(46.dp)
                            .clip(RoundedCornerShape(14.dp)),
                    )
                }
                Column(
                    modifier = Modifier.weight(1f, fill = false),
                    verticalArrangement = Arrangement.spacedBy(5.dp),
                ) {
                    Text(
                        text = "照片可以放进小展台",
                        style = MaterialTheme.typography.labelMedium,
                        color = Color(0xFF42546A),
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    LocalImagePreviewActionButton(
                        text = "放入小展台",
                        primary = true,
                        onClick = { onSaveToXiaozhantai(card.messageId) },
                    )
                }
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
    onSaveToXiaozhantai: (() -> Unit)? = null,
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
        if (preview.status == LocalImagePreviewStatus.Sent) {
            when {
                preview.savedToXiaozhantai -> Text(
                    text = "已放入小展台",
                    style = MaterialTheme.typography.labelMedium,
                    color = contentColor.copy(alpha = 0.72f),
                )
                preview.isSavingToXiaozhantai -> Text(
                    text = "正在轻轻放进去",
                    style = MaterialTheme.typography.labelMedium,
                    color = contentColor.copy(alpha = 0.72f),
                )
                preview.canSaveToXiaozhantai -> LocalImagePreviewActionButton(
                    text = "放入小展台",
                    primary = true,
                    onClick = { onSaveToXiaozhantai?.invoke() },
                )
            }
        }
        preview.xiaozhantaiError?.takeIf { it.isNotBlank() }?.let { message ->
            Text(
                text = message,
                style = MaterialTheme.typography.labelMedium,
                color = contentColor.copy(alpha = 0.72f),
            )
        }
    }
}

@Composable
private fun XiaozhantaiSaveDialog(
    draft: XiaozhantaiSaveDraftUiState,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
) {
    val previewBitmap = remember(draft.previewBytes) {
        draft.previewBytes?.let { bytes ->
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.asImageBitmap()
        }
    }
    AlertDialog(
        onDismissRequest = {
            if (!draft.isSaving) onDismiss()
        },
        title = { Text(text = "放进小展台") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                if (previewBitmap != null) {
                    Image(
                        bitmap = previewBitmap,
                        contentDescription = "准备放入小展台的图片",
                        contentScale = ContentScale.Crop,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(132.dp)
                            .clip(RoundedCornerShape(18.dp)),
                    )
                }
                Text(
                    text = "名字",
                    style = MaterialTheme.typography.labelMedium,
                    color = Color(0xFF52667B),
                )
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(18.dp),
                    color = Color.White.copy(alpha = 0.78f),
                    border = BorderStroke(
                        width = 1.dp,
                        color = Color.White.copy(alpha = 0.66f),
                    ),
                ) {
                    Text(
                        text = draft.name.ifBlank { draft.defaultName },
                        style = MaterialTheme.typography.titleMedium,
                        color = Color(0xFF40546A),
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp),
                    )
                }
                draft.errorMessage?.let { message ->
                    Text(
                        text = message,
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.error,
                    )
                }
            }
        },
        confirmButton = {
            Button(
                onClick = onConfirm,
                enabled = !draft.isSaving,
            ) {
                Text(text = if (draft.isSaving) "正在放好" else "留下")
            }
        },
        dismissButton = {
            TextButton(
                onClick = onDismiss,
                enabled = !draft.isSaving,
            ) {
                Text(text = "先不放")
            }
        },
    )
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
        LocalImagePreviewStatus.Failed -> "这张图还没看到"
    }
}

@Composable
private fun LandscapeOperationPanel(
    uiState: ChatUiState,
    compactLandscape: Boolean,
    maxPanelWidth: Dp,
    parentEntryHint: String?,
    presentation: ChildInteractionPresentation,
    onParentEntryTap: () -> Unit,
    onParentEntryLongPress: () -> Unit,
    onOpenXiaozhantai: () -> Unit,
    onSend: (String) -> Unit,
    onQuickAction: (QuickActionUi) -> Unit,
    onStopTts: () -> Unit,
    onToggleTtsMuted: () -> Unit,
    onOpenTtsSettings: () -> Unit,
    onInstallTtsData: () -> Unit,
    onOpenImageInput: (String) -> Unit,
    viewportClass: CompanionRoomViewportClass,
    modifier: Modifier = Modifier,
) {
    val tabletLandscape = viewportClass == CompanionRoomViewportClass.LandscapeTablet
    val panelGap = when {
        compactLandscape || tabletLandscape -> 8.dp
        else -> 12.dp
    }
    val inputHorizontalPadding = when {
        compactLandscape -> 12.dp
        tabletLandscape -> 0.dp
        else -> 18.dp
    }
    val inputVerticalPadding = when {
        compactLandscape -> 10.dp
        tabletLandscape -> 6.dp
        else -> 14.dp
    }
    val visibleQuickActions = childCompanionVisibleQuickActions(uiState)

    BoxWithConstraints(modifier = modifier) {
        val panelWidth = minOf(maxWidth, maxPanelWidth)
        Column(
            modifier = Modifier
                .align(Alignment.CenterEnd)
                .width(panelWidth)
                .fillMaxHeight()
                .padding(if (compactLandscape || tabletLandscape) 4.dp else 8.dp),
            horizontalAlignment = Alignment.End,
        ) {
            ParentEntryHintBar(
                parentEntryHint = parentEntryHint,
                onParentEntryTap = onParentEntryTap,
                onParentEntryLongPress = onParentEntryLongPress,
                onOpenXiaozhantai = onOpenXiaozhantai,
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
            InputBar(
                modifier = Modifier
                    .fillMaxWidth()
                    .navigationBarsPadding()
                    .windowInsetsPadding(WindowInsets.ime)
                    .padding(
                        horizontal = if (compactLandscape) 4.dp else inputHorizontalPadding,
                        vertical = if (compactLandscape) 6.dp else inputVerticalPadding,
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
                onOpenImageInput = onOpenImageInput,
                playfulControls = true,
                playfulCompactControls = viewportClass == CompanionRoomViewportClass.LandscapeTablet,
            )
        }
    }
}

internal const val PARENT_ENTRY_COMPACT_LABEL = "家长入口"

internal fun parentEntryTapHint(): String = "长按进入家长入口"

internal fun parentEntryDefaultHint(): String = ""

internal fun parentEntryDefaultLabels(): List<String> = listOf(PARENT_ENTRY_COMPACT_LABEL)

internal fun parentEntryLongPressTargets(): List<ParentEntryTarget> =
    listOf(ParentEntryTarget.Report, ParentEntryTarget.Settings)

internal fun topicShiftChipActions(uiState: ChatUiState): List<QuickActionUi> {
    return emptyList()
}

@Composable
private fun CompanionRoomBackground(viewportClass: CompanionRoomViewportClass) {
    when (viewportClass) {
        CompanionRoomViewportClass.LandscapeWide -> {
            Image(
                painter = painterResource(id = R.drawable.companion_room_background_land),
                contentDescription = null,
                contentScale = ContentScale.Crop,
                alignment = Alignment.Center,
                modifier = Modifier.fillMaxSize(),
            )
        }

        CompanionRoomViewportClass.LandscapeTablet -> {
            Image(
                painter = painterResource(id = R.drawable.companion_room_background_land),
                contentDescription = null,
                contentScale = ContentScale.Crop,
                alignment = Alignment.Center,
                modifier = Modifier.fillMaxSize(),
            )
        }

        CompanionRoomViewportClass.LandscapeSquare -> {
            Image(
                painter = painterResource(id = R.drawable.companion_room_background_land),
                contentDescription = null,
                contentScale = ContentScale.Crop,
                alignment = Alignment.Center,
                modifier = Modifier.fillMaxSize(),
            )
        }

        CompanionRoomViewportClass.PortraitExpanded -> {
            Image(
                painter = painterResource(id = R.drawable.companion_room_background_portrait),
                contentDescription = null,
                contentScale = ContentScale.Crop,
                alignment = BiasAlignment(horizontalBias = 0f, verticalBias = -0.1f),
                modifier = Modifier.fillMaxSize(),
            )
        }

        CompanionRoomViewportClass.Portrait -> {
            BoxWithConstraints(modifier = Modifier.fillMaxSize()) {
                Image(
                    painter = painterResource(id = R.drawable.companion_room_background_portrait),
                    contentDescription = null,
                    contentScale = ContentScale.Crop,
                    alignment = Alignment.TopCenter,
                    modifier = Modifier
                        .align(Alignment.TopCenter)
                        .width(maxWidth)
                        .height(maxHeight + 160.dp)
                        .graphicsLayer {
                            scaleY = 1f
                            transformOrigin = TransformOrigin(0.5f, 0f)
                        },
                )
            }
        }
    }
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(companionRoomScrimBrush(isLandscape = viewportClass.isLandscape)),
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
    return companionLayoutWeights(
        viewportClass = if (isLandscape) {
            CompanionRoomViewportClass.LandscapeWide
        } else {
            CompanionRoomViewportClass.Portrait
        },
    )
}

internal fun companionLayoutWeights(viewportClass: CompanionRoomViewportClass): CompanionLayoutWeights {
    return when (viewportClass) {
        CompanionRoomViewportClass.LandscapeWide -> CompanionLayoutWeights(
            agent = 0.58f,
            conversation = 0.42f,
        )

        CompanionRoomViewportClass.LandscapeTablet -> CompanionLayoutWeights(
            agent = 0.56f,
            conversation = 0.44f,
        )

        CompanionRoomViewportClass.LandscapeSquare -> CompanionLayoutWeights(
            agent = 0.70f,
            conversation = 0.30f,
        )

        CompanionRoomViewportClass.Portrait -> CompanionLayoutWeights(
            agent = 0.72f,
            conversation = 0.28f,
        )

        CompanionRoomViewportClass.PortraitExpanded -> CompanionLayoutWeights(
            agent = 0.70f,
            conversation = 0.30f,
        )
    }
}

internal fun companionRecentMessageLimit(isLandscape: Boolean): Int {
    return if (isLandscape) 2 else 1
}

internal fun companionVisibleMessages(
    messages: List<ChatMessage>,
    maxVisibleMessages: Int,
): List<ChatMessage> {
    val filteredMessages = messages.filterNot(::isStageOnlyStatusMessage)
    val hasChildMessage = filteredMessages.any { it.author == MessageAuthor.Child }
    return filteredMessages
        .filterNot { hasChildMessage && it.id == "agent-welcome" }
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
    "companion_name",
    "give_name",
    "image_naming",
)

private val openingQuickActionIds = setOf(
    "companion_name",
    "companion_skip",
    "companion_continue",
)

internal fun companionOpeningQuickActionsActive(uiState: ChatUiState): Boolean {
    val openingActionVisible = uiState.quickActions.any { it.id in openingQuickActionIds }
    if (!openingActionVisible) return false
    if (uiState.messages.any { it.author == MessageAuthor.Child }) return false
    return uiState.sessionState?.companionObject?.action in setOf("name_seed", "recall")
}

internal fun companionPinnedBubbleMessageId(uiState: ChatUiState): String? {
    val hasOpeningBubble = uiState.messages.any { it.id == "agent-welcome" && it.author == MessageAuthor.Agent }
    return if (hasOpeningBubble && companionOpeningQuickActionsActive(uiState)) {
        "agent-welcome"
    } else {
        null
    }
}

internal fun childCompanionVisibleQuickActions(uiState: ChatUiState): List<QuickActionUi> {
    val openingActionsActive = companionOpeningQuickActionsActive(uiState)
    val coCreateGuidanceActive =
        uiState.sessionState?.companionObject?.action == "co_create" &&
            uiState.quickActions.any { it.id == "companion_friend_name" || it.id == "companion_friend_image" }
    val baseActions = uiState.quickActions.filterNot { action ->
        action.id == "take_photo" ||
            action.id == "share_photo" ||
            action.id == "start_voice" ||
            action.label == "我想说话" ||
            (
                action.id in openingQuickActionIds &&
                    !openingActionsActive &&
                    !(coCreateGuidanceActive && action.id == "companion_skip") &&
                    !(uiState.pendingImageContext != null && action.id == "companion_name")
                )
    }
    if (uiState.pendingImageContext == null) {
        return baseActions.filterNot { it.id in imageContextActionIds }
    }
    return baseActions
        .firstOrNull { it.id in primaryImageCoCreationActionIds }
        ?.let { listOf(normalizeImageQuickAction(it)) }
        ?: emptyList()
}

internal fun strangeDoorShouldShowNormalInputBar(uiState: ChatUiState): Boolean {
    return uiState.strangeDoorDemo == null
}

private fun normalizeImageQuickAction(action: QuickActionUi): QuickActionUi {
    return when (action.id) {
        "give_name", "image_naming" -> action.copy(id = "companion_name", label = "起个名字")
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
    onOpenXiaozhantai: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.End,
    ) {
        XiaozhantaiEntranceButton(
            onClick = onOpenXiaozhantai,
            modifier = Modifier.padding(start = 24.dp, top = 12.dp),
        )
        Spacer(modifier = Modifier.width(8.dp))
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
private fun XiaozhantaiEntranceButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val interactionSource = remember { MutableInteractionSource() }
    val pressed by interactionSource.collectIsPressedAsState()
    val scale by animateFloatAsState(
        targetValue = if (pressed) 0.96f else 1f,
        animationSpec = tween(durationMillis = 160),
        label = "xiaozhantaiEntranceScale",
    )
    Surface(
        modifier = modifier
            .heightIn(min = 44.dp)
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
            }
            .clickable(
                interactionSource = interactionSource,
                indication = null,
                onClick = onClick,
            ),
        shape = RoundedCornerShape(22.dp),
        color = Color.White.copy(alpha = 0.66f),
        shadowElevation = 1.dp,
        border = BorderStroke(
            width = 1.dp,
            color = Color.White.copy(alpha = 0.60f),
        ),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Image(
                painter = painterResource(id = R.drawable.xzt_entrance_icon),
                contentDescription = "小展台",
                contentScale = ContentScale.Fit,
                modifier = Modifier.size(34.dp),
            )
            Text(
                text = "小展台",
                style = MaterialTheme.typography.labelMedium,
                color = Color(0xFF52667B),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun ParentEntryTargetDialog(
    onOpenTarget: (ParentEntryTarget) -> Unit,
    showHouseObjectDebugEntry: Boolean,
    onOpenHouseObjectDebug: () -> Unit,
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
                if (showHouseObjectDebugEntry) {
                    TextButton(onClick = onOpenHouseObjectDebug) {
                        Text(text = "开发调试")
                    }
                }
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
    xiaozhantaiSavePromptPreview: LocalImagePreviewCardUiState?,
    pinnedBubbleMessageId: String?,
    viewportClass: CompanionRoomViewportClass,
    compactLandscape: Boolean,
    companionObject: CompanionObjectMeta? = null,
    onImageRetry: (String) -> Unit,
    onImageDismiss: (String) -> Unit,
    onImageSaveToXiaozhantai: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    var debugMascotStateId by rememberSaveable { mutableStateOf<String?>(null) }
    val debugMascotState = debugMascotStateId?.let(MascotState::fromId)
    val resolvedMascotState = XiaobaohuVisualStateResolver.resolve(presentation.agent).mascotState
    val effectiveMascotState = debugMascotState ?: resolvedMascotState
    val isLandscape = viewportClass.isLandscape

    Box(modifier = modifier) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Box(modifier = Modifier.weight(1f)) {
                XiaobaohuCompanionStage(
                    agent = presentation.agent,
                    mascotState = effectiveMascotState,
                    compactLandscape = compactLandscape,
                    viewportClass = viewportClass,
                    companionObject = companionObject,
                    debugMascotState = debugMascotState,
                    modifier = Modifier.fillMaxSize(),
                )
                CompanionFloatingConversationBubbles(
                    messages = messages,
                    imagePreviewCards = imagePreviewCards,
                    isLandscape = isLandscape,
                    pinnedMessageId = pinnedBubbleMessageId,
                    onImageRetry = onImageRetry,
                    onImageDismiss = onImageDismiss,
                    onImageSaveToXiaozhantai = onImageSaveToXiaozhantai,
                    modifier = Modifier.matchParentSize(),
                )
                XiaozhantaiSavePromptBubble(
                    preview = xiaozhantaiSavePromptPreview,
                    isLandscape = isLandscape,
                    onSaveToXiaozhantai = onImageSaveToXiaozhantai,
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
        ChildTurnUiPhase.ServiceError -> "请家长帮忙看看"
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
            onOpenXiaozhantai = {},
            onStrangeDoorChoosePhoto = {},
            onStrangeDoorChooseRiddle = {},
            onStrangeDoorSwitchMethod = {},
            requireParentCredential = false,
            verifyParentCredential = { false },
            houseObjectDebugRepository = null,
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
            onOpenXiaozhantai = {},
            onStrangeDoorChoosePhoto = {},
            onStrangeDoorChooseRiddle = {},
            onStrangeDoorSwitchMethod = {},
            requireParentCredential = false,
            verifyParentCredential = { false },
            houseObjectDebugRepository = null,
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
            onOpenXiaozhantai = {},
            onStrangeDoorChoosePhoto = {},
            onStrangeDoorChooseRiddle = {},
            onStrangeDoorSwitchMethod = {},
            requireParentCredential = false,
            verifyParentCredential = { false },
            houseObjectDebugRepository = null,
        )
    }
}

private const val TTS_SETTINGS_ACTION = "com.android.settings.TTS_SETTINGS"
