package com.childai.companion.ui.chat

import androidx.compose.foundation.background
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.ime
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.childai.companion.config.DevSettings
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.ui.parent.ParentEntryPinDialog
import com.childai.companion.ui.parent.ParentEntryTarget
import com.childai.companion.ui.parent.ParentPinGate
import com.childai.companion.ui.theme.ChildAiCompanionTheme

@Composable
fun ChildChatScreen(
    modifier: Modifier = Modifier,
    onOpenParentSettings: () -> Unit = {},
    onOpenParentReport: () -> Unit = {},
    viewModel: ChatViewModel = viewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    ChildChatScreenContent(
        uiState = uiState,
        onSend = viewModel::sendText,
        onQuickAction = viewModel::onQuickAction,
        onMockProblemTextChange = viewModel::updateMockProblemText,
        onDismissMockPhoto = viewModel::dismissMockPhotoCapture,
        onSubmitMockPhoto = viewModel::submitMockPhotoCapture,
        onOpenParentSettings = onOpenParentSettings,
        onOpenParentReport = onOpenParentReport,
        modifier = modifier,
    )
}

@Composable
private fun ChildChatScreenContent(
    uiState: ChatUiState,
    onSend: (String) -> Unit,
    onQuickAction: (QuickActionUi) -> Unit,
    onMockProblemTextChange: (String) -> Unit,
    onDismissMockPhoto: () -> Unit,
    onSubmitMockPhoto: () -> Unit,
    onOpenParentSettings: () -> Unit,
    onOpenParentReport: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var pendingParentEntry by rememberSaveable { mutableStateOf<ParentEntryTarget?>(null) }
    var parentPinInput by rememberSaveable { mutableStateOf("") }
    var parentPinError by rememberSaveable { mutableStateOf<String?>(null) }
    var parentEntryHint by rememberSaveable { mutableStateOf<String?>(null) }

    fun resetParentGate() {
        pendingParentEntry = null
        parentPinInput = ""
        parentPinError = null
    }

    fun openParentGate(target: ParentEntryTarget) {
        parentEntryHint = null
        pendingParentEntry = target
        parentPinInput = ""
        parentPinError = null
    }

    fun submitParentPin() {
        val target = pendingParentEntry ?: return
        if (ParentPinGate.isPinAccepted(parentPinInput, DevSettings.DEV_PARENT_PIN)) {
            resetParentGate()
            when (target) {
                ParentEntryTarget.Report -> onOpenParentReport()
                ParentEntryTarget.Settings -> onOpenParentSettings()
            }
        } else {
            parentPinError = ParentPinGate.GENTLE_ERROR_MESSAGE
        }
    }

    uiState.mockPhoto?.let { mockPhoto ->
        MockPhotoDialog(
            mockPhoto = mockPhoto,
            onProblemTextChange = onMockProblemTextChange,
            onDismiss = onDismissMockPhoto,
            onSubmit = onSubmitMockPhoto,
        )
    }
    pendingParentEntry?.let { target ->
        ParentEntryPinDialog(
            target = target,
            pinInput = parentPinInput,
            errorMessage = parentPinError,
            onPinInputChange = {
                parentPinInput = it
                parentPinError = null
            },
            onConfirm = ::submitParentPin,
            onDismiss = ::resetParentGate,
        )
    }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            AgentTopBar(
                parentEntryHint = parentEntryHint,
                onParentEntryTap = {
                    parentEntryHint = "请让大人长按父亲入口。"
                },
                onOpenParentSettings = {
                    openParentGate(ParentEntryTarget.Settings)
                },
                onOpenParentReport = {
                    openParentGate(ParentEntryTarget.Report)
                },
            )
        },
        bottomBar = {
            InputBar(
                modifier = Modifier
                    .background(MaterialTheme.colorScheme.surface)
                    .navigationBarsPadding()
                    .windowInsetsPadding(WindowInsets.ime)
                    .padding(horizontal = 24.dp, vertical = 16.dp),
                onSend = onSend,
                enabled = !uiState.isSending,
                voice = uiState.voice,
            )
        },
    ) { innerPadding ->
        BoxWithConstraints(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
                .background(MaterialTheme.colorScheme.background),
        ) {
            if (maxWidth >= 720.dp) {
                Row(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 32.dp, vertical = 24.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    AgentPanel(
                        agent = uiState.agent,
                        modifier = Modifier
                            .weight(0.42f)
                            .fillMaxWidth(),
                    )
                    Spacer(modifier = Modifier.width(28.dp))
                    ChatConversationPanel(
                        uiState = uiState,
                        onQuickAction = onQuickAction,
                        modifier = Modifier.weight(0.58f),
                    )
                }
            } else {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 20.dp, vertical = 18.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    AgentPanel(
                        agent = uiState.agent,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Spacer(modifier = Modifier.height(18.dp))
                    ChatConversationPanel(
                        uiState = uiState,
                        onQuickAction = onQuickAction,
                        modifier = Modifier.weight(1f),
                    )
                }
            }
        }
    }
}

@Composable
private fun MockPhotoDialog(
    mockPhoto: MockPhotoUiState,
    onProblemTextChange: (String) -> Unit,
    onDismiss: () -> Unit,
    onSubmit: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(text = "拍题目")
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(
                    value = mockPhoto.problemText,
                    onValueChange = onProblemTextChange,
                    enabled = !mockPhoto.isSubmitting,
                    label = {
                        Text(text = "题目文字")
                    },
                    minLines = 3,
                    maxLines = 5,
                    textStyle = MaterialTheme.typography.bodyLarge,
                )
                mockPhoto.errorMessage?.let { error ->
                    Text(
                        text = error,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.error,
                    )
                }
            }
        },
        confirmButton = {
            Button(
                onClick = onSubmit,
                enabled = !mockPhoto.isSubmitting,
            ) {
                Text(text = if (mockPhoto.isSubmitting) "发送中" else "发送题目")
            }
        },
        dismissButton = {
            TextButton(
                onClick = onDismiss,
                enabled = !mockPhoto.isSubmitting,
            ) {
                Text(text = "取消")
            }
        },
    )
}

@Composable
private fun ChatConversationPanel(
    uiState: ChatUiState,
    onQuickAction: (QuickActionUi) -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier) {
        MessageList(
            messages = uiState.messages,
            modifier = Modifier.weight(1f),
        )
        if (uiState.quickActions.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            QuickActionsRow(
                actions = uiState.quickActions,
                enabled = !uiState.isSending,
                onQuickAction = onQuickAction,
            )
        }
        if (DevSettings.SHOW_SESSION_STATE_DEBUG) uiState.sessionState?.let { sessionState ->
            Spacer(modifier = Modifier.height(10.dp))
            SessionStateStrip(sessionState = sessionState)
        }
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
    onParentEntryTap: () -> Unit,
    onOpenParentSettings: () -> Unit,
    onOpenParentReport: () -> Unit,
) {
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
                    .padding(horizontal = 24.dp, vertical = 18.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(
                    modifier = Modifier.weight(1f),
                ) {
                    Text(
                        text = "小狐狸",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onSurface,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        text = "准备听你说",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                ParentEntryButton(
                    label = "父亲日报",
                    onTap = onParentEntryTap,
                    onLongPress = onOpenParentReport,
                )
                Spacer(modifier = Modifier.width(8.dp))
                ParentEntryButton(
                    label = "父亲设置",
                    onTap = onParentEntryTap,
                    onLongPress = onOpenParentSettings,
                )
            }
            parentEntryHint?.let { hint ->
                Text(
                    text = hint,
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(start = 24.dp, end = 24.dp, bottom = 10.dp),
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
    Surface(
        modifier = Modifier.combinedClickable(
            onClick = onTap,
            onLongClick = onLongPress,
            onLongClickLabel = "输入 PIN",
        ),
        shape = MaterialTheme.shapes.small,
        color = MaterialTheme.colorScheme.surface,
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 9.dp),
        )
    }
}

@Composable
private fun AgentPanel(
    agent: FoxAgentUiState,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        CartoonAgentView(agent = agent)
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = agent.statusText,
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onBackground,
        )
    }
}

@Preview(showBackground = true, widthDp = 900, heightDp = 700)
@Composable
private fun ChildChatScreenPreview() {
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
            onMockProblemTextChange = {},
            onDismissMockPhoto = {},
            onSubmitMockPhoto = {},
            onOpenParentSettings = {},
            onOpenParentReport = {},
        )
    }
}
