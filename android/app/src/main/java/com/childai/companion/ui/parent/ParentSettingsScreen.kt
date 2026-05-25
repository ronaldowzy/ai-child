package com.childai.companion.ui.parent

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.childai.companion.ui.theme.ChildAiCompanionTheme

@Composable
fun ParentSettingsScreen(
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ParentPolicyViewModel = viewModel(),
    onLogout: () -> Unit = {},
) {
    val uiState by viewModel.uiState.collectAsState()

    ParentSettingsScreenContent(
        uiState = uiState,
        onBack = onBack,
        onReload = viewModel::loadPolicy,
        onSave = viewModel::savePolicy,
        onChildNicknameChange = viewModel::updateChildNickname,
        onChildDisplayNameChange = viewModel::updateChildDisplayName,
        onChildAgeChange = viewModel::updateChildAge,
        onChildGradeChange = viewModel::updateChildGrade,
        onChildCallPreferenceChange = viewModel::updateChildCallPreference,
        onChildInterestsTextChange = viewModel::updateChildInterestsText,
        onTopicBoundariesTextChange = viewModel::updateTopicBoundariesText,
        onParentMessageChange = viewModel::updateParentMessageRaw,
        onGoalsTextChange = viewModel::updateGoalsText,
        onOfferChoicesChange = viewModel::updateOfferChoices,
        onDoNotForceExpressionChange = viewModel::updateDoNotForceExpression,
        onAskThinkingBeforeAnswerChange = viewModel::updateAskThinkingBeforeAnswer,
        onLogout = onLogout,
        modifier = modifier,
    )
}

@Composable
private fun ParentSettingsScreenContent(
    uiState: ParentPolicyUiState,
    onBack: () -> Unit,
    onReload: () -> Unit,
    onSave: () -> Unit,
    onChildNicknameChange: (String) -> Unit,
    onChildDisplayNameChange: (String) -> Unit,
    onChildAgeChange: (String) -> Unit,
    onChildGradeChange: (String) -> Unit,
    onChildCallPreferenceChange: (String) -> Unit,
    onChildInterestsTextChange: (String) -> Unit,
    onTopicBoundariesTextChange: (String) -> Unit,
    onParentMessageChange: (String) -> Unit,
    onGoalsTextChange: (String) -> Unit,
    onOfferChoicesChange: (Boolean) -> Unit,
    onDoNotForceExpressionChange: (Boolean) -> Unit,
    onAskThinkingBeforeAnswerChange: (Boolean) -> Unit,
    onLogout: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        modifier = modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.safeDrawing),
        topBar = {
            ParentTopBar(
                title = "家长设置",
                onBack = onBack,
                trailing = {
                    Row {
                        TextButton(
                            onClick = onReload,
                            enabled = !uiState.isLoading && !uiState.isSaving,
                        ) {
                            Text(text = "刷新")
                        }
                        TextButton(
                            onClick = onLogout,
                            enabled = !uiState.isSaving,
                        ) {
                            Text(text = "退出登录")
                        }
                    }
                },
            )
        },
        bottomBar = {
            SettingsBottomBar(
                isSaving = uiState.isSaving,
                onSave = onSave,
            )
        },
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 28.dp, vertical = 22.dp),
            verticalArrangement = Arrangement.spacedBy(22.dp),
        ) {
            if (uiState.isLoading) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    CircularProgressIndicator()
                    Text(text = "正在读取设置")
                }
            }
            SettingsSection(title = "孩子称呼") {
                OutlinedTextField(
                    value = uiState.form.childNickname,
                    onValueChange = onChildNicknameChange,
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    textStyle = MaterialTheme.typography.bodyLarge,
                    label = {
                        Text(text = "小名")
                    },
                    placeholder = {
                        Text(text = "可填小名或家里常用称呼，不强制填写")
                    },
                )
                OutlinedTextField(
                    value = uiState.form.childDisplayName,
                    onValueChange = onChildDisplayNameChange,
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    textStyle = MaterialTheme.typography.bodyLarge,
                    label = {
                        Text(text = "大名 / 显示名")
                    },
                    placeholder = {
                        Text(text = "没有小名时，小白狐会优先用这个称呼")
                    },
                )
                Text(
                    text = "用于小白狐开场白称呼孩子。可以只写家里常用称呼，不需要填写真实全名。",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            SettingsSection(title = "孩子画像") {
                OutlinedTextField(
                    value = uiState.form.childAge,
                    onValueChange = onChildAgeChange,
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    textStyle = MaterialTheme.typography.bodyLarge,
                    label = {
                        Text(text = "年龄")
                    },
                    placeholder = {
                        Text(text = "建议填写 5-10 岁，用来控制小白狐回复长度")
                    },
                )
                OutlinedTextField(
                    value = uiState.form.childGrade,
                    onValueChange = onChildGradeChange,
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    textStyle = MaterialTheme.typography.bodyLarge,
                    label = {
                        Text(text = "年级（可选）")
                    },
                    placeholder = {
                        Text(text = "例如 二年级；不确定可以留空")
                    },
                )
                OutlinedTextField(
                    value = uiState.form.childCallPreference,
                    onValueChange = onChildCallPreferenceChange,
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    textStyle = MaterialTheme.typography.bodyLarge,
                    label = {
                        Text(text = "称呼 / 代词偏好（可选）")
                    },
                    placeholder = {
                        Text(text = "例如 叫小名、叫哥哥、用“孩子”")
                    },
                )
                Text(
                    text = "这些只用于尊重称呼和调整回复节奏，不用于给孩子贴性格标签。",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            SettingsSection(title = "兴趣和不想聊的话题") {
                OutlinedTextField(
                    value = uiState.form.childInterestsText,
                    onValueChange = onChildInterestsTextChange,
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 2,
                    maxLines = 4,
                    textStyle = MaterialTheme.typography.bodyLarge,
                    label = {
                        Text(text = "孩子最近愿意聊的兴趣")
                    },
                    placeholder = {
                        Text(text = "一行一个，例如：恐龙、画画、跑步比赛")
                    },
                )
                OutlinedTextField(
                    value = uiState.form.topicBoundariesText,
                    onValueChange = onTopicBoundariesTextChange,
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 2,
                    maxLines = 4,
                    textStyle = MaterialTheme.typography.bodyLarge,
                    label = {
                        Text(text = "近期不想被追问的话题")
                    },
                    placeholder = {
                        Text(text = "一行一个，例如：学校细节、比赛成绩")
                    },
                )
            }
            SettingsSection(title = "家长寄语 / 小白狐了解孩子") {
                OutlinedTextField(
                    value = uiState.form.parentMessageRaw,
                    onValueChange = onParentMessageChange,
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 4,
                    maxLines = 8,
                    textStyle = MaterialTheme.typography.bodyLarge,
                    placeholder = {
                        Text(
                            text = "可以写孩子的小名、性格特点、最近状态、希望小白狐怎么陪他说话，以及哪些说法要避免。小白狐会把这些作为背景来理解孩子，不会机械复述给孩子。",
                        )
                    },
                )
            }
            SettingsSection(title = "本周目标") {
                OutlinedTextField(
                    value = uiState.form.goalsText,
                    onValueChange = onGoalsTextChange,
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 4,
                    maxLines = 7,
                    textStyle = MaterialTheme.typography.bodyLarge,
                )
            }
            SettingsSection(title = "沟通偏好") {
                PreferenceRow(
                    text = "先给选择，再开放提问",
                    checked = uiState.form.offerChoices,
                    onCheckedChange = onOfferChoicesChange,
                )
                PreferenceRow(
                    text = "不强迫孩子立刻表达",
                    checked = uiState.form.doNotForceExpression,
                    onCheckedChange = onDoNotForceExpressionChange,
                )
                PreferenceRow(
                    text = "学习问题先问思路",
                    checked = uiState.form.askThinkingBeforeAnswer,
                    onCheckedChange = onAskThinkingBeforeAnswerChange,
                )
            }
            uiState.errorMessage?.let { error ->
                Text(
                    text = error,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.error,
                )
            }
            uiState.statusMessage?.let { status ->
                Text(
                    text = status,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.primary,
                )
            }
        }
    }
}

@Composable
internal fun ParentTopBar(
    title: String,
    onBack: () -> Unit,
    trailing: @Composable () -> Unit = {},
) {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 1.dp,
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            TextButton(onClick = onBack) {
                Text(text = "返回")
            }
            Text(
                text = title,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.padding(start = 10.dp),
            )
            Spacer(modifier = Modifier.weight(1f))
            trailing()
        }
    }
}

@Composable
private fun SettingsBottomBar(
    isSaving: Boolean,
    onSave: () -> Unit,
) {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 1.dp,
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .navigationBarsPadding()
                .padding(horizontal = 28.dp, vertical = 14.dp),
            horizontalArrangement = Arrangement.End,
        ) {
            Button(
                onClick = onSave,
                enabled = !isSaving,
            ) {
                Text(text = if (isSaving) "保存中" else "保存设置")
            }
        }
    }
}

@Composable
private fun SettingsSection(
    title: String,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            color = MaterialTheme.colorScheme.onBackground,
        )
        content()
    }
}

@Composable
private fun PreferenceRow(
    text: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Checkbox(
            checked = checked,
            onCheckedChange = onCheckedChange,
        )
        Text(
            text = text,
            style = MaterialTheme.typography.bodyLarge,
            modifier = Modifier.padding(start = 8.dp),
        )
    }
}

@Preview(showBackground = true, widthDp = 900, heightDp = 700)
@Composable
private fun ParentSettingsScreenPreview() {
    ChildAiCompanionTheme {
        ParentSettingsScreenContent(
            uiState = ParentPolicyUiState(),
            onBack = {},
            onReload = {},
            onSave = {},
            onChildNicknameChange = {},
            onChildDisplayNameChange = {},
            onChildAgeChange = {},
            onChildGradeChange = {},
            onChildCallPreferenceChange = {},
            onChildInterestsTextChange = {},
            onTopicBoundariesTextChange = {},
            onParentMessageChange = {},
            onGoalsTextChange = {},
            onOfferChoicesChange = {},
            onDoNotForceExpressionChange = {},
            onAskThinkingBeforeAnswerChange = {},
            onLogout = {},
        )
    }
}
