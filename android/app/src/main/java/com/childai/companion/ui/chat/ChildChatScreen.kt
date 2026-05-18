package com.childai.companion.ui.chat

import androidx.compose.foundation.background
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
import androidx.compose.material3.AssistChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.ui.theme.ChildAiCompanionTheme

@Composable
fun ChildChatScreen(
    modifier: Modifier = Modifier,
    viewModel: ChatViewModel = viewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    ChildChatScreenContent(
        uiState = uiState,
        onSend = viewModel::sendText,
        onQuickAction = viewModel::onQuickAction,
        modifier = modifier,
    )
}

@Composable
private fun ChildChatScreenContent(
    uiState: ChatUiState,
    onSend: (String) -> Unit,
    onQuickAction: (QuickActionUi) -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            AgentTopBar()
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
                    AgentPanel(modifier = Modifier.fillMaxWidth())
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
        uiState.sessionState?.let { sessionState ->
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
private fun AgentTopBar() {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 1.dp,
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp, vertical = 18.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = "小狐狸",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Spacer(modifier = Modifier.width(12.dp))
            Text(
                text = "准备听你说",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun AgentPanel(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        CartoonAgentView()
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = "慢慢说，一次说一件事就好。",
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
            ),
            onSend = {},
            onQuickAction = {},
        )
    }
}
