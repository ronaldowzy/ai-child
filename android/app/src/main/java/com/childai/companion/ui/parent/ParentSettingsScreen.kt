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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
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
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.childai.companion.ui.theme.ChildAiCompanionTheme

@Composable
fun ParentSettingsScreen(
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ParentPolicyViewModel = viewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    ParentSettingsScreenContent(
        uiState = uiState,
        onBack = onBack,
        onReload = viewModel::loadPolicy,
        onSave = viewModel::savePolicy,
        onChildNicknameChange = viewModel::updateChildNickname,
        onChildDisplayNameChange = viewModel::updateChildDisplayName,
        onParentMessageChange = viewModel::updateParentMessageRaw,
        onGoalsTextChange = viewModel::updateGoalsText,
        onOfferChoicesChange = viewModel::updateOfferChoices,
        onDoNotForceExpressionChange = viewModel::updateDoNotForceExpression,
        onAskThinkingBeforeAnswerChange = viewModel::updateAskThinkingBeforeAnswer,
        onAfterSchoolStartChange = viewModel::updateAfterSchoolStart,
        onAfterSchoolEndChange = viewModel::updateAfterSchoolEnd,
        onHomeworkStartChange = viewModel::updateHomeworkStart,
        onHomeworkEndChange = viewModel::updateHomeworkEnd,
        onBedtimeStartChange = viewModel::updateBedtimeStart,
        onBedtimeEndChange = viewModel::updateBedtimeEnd,
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
    onParentMessageChange: (String) -> Unit,
    onGoalsTextChange: (String) -> Unit,
    onOfferChoicesChange: (Boolean) -> Unit,
    onDoNotForceExpressionChange: (Boolean) -> Unit,
    onAskThinkingBeforeAnswerChange: (Boolean) -> Unit,
    onAfterSchoolStartChange: (String) -> Unit,
    onAfterSchoolEndChange: (String) -> Unit,
    onHomeworkStartChange: (String) -> Unit,
    onHomeworkEndChange: (String) -> Unit,
    onBedtimeStartChange: (String) -> Unit,
    onBedtimeEndChange: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        modifier = modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.safeDrawing),
        topBar = {
            ParentTopBar(
                title = "父亲设置",
                onBack = onBack,
                trailing = {
                    TextButton(
                        onClick = onReload,
                        enabled = !uiState.isLoading && !uiState.isSaving,
                    ) {
                        Text(text = "刷新")
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
            SettingsSection(title = "父母寄语 / 小白狐了解孩子") {
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
            SettingsSection(title = "作息时间") {
                TimeRangeRow(
                    label = "放学后",
                    start = uiState.form.afterSchoolStart,
                    end = uiState.form.afterSchoolEnd,
                    onStartChange = onAfterSchoolStartChange,
                    onEndChange = onAfterSchoolEndChange,
                )
                TimeRangeRow(
                    label = "作业时间",
                    start = uiState.form.homeworkStart,
                    end = uiState.form.homeworkEnd,
                    onStartChange = onHomeworkStartChange,
                    onEndChange = onHomeworkEndChange,
                )
                TimeRangeRow(
                    label = "睡前",
                    start = uiState.form.bedtimeStart,
                    end = uiState.form.bedtimeEnd,
                    onStartChange = onBedtimeStartChange,
                    onEndChange = onBedtimeEndChange,
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

@Composable
private fun TimeRangeRow(
    label: String,
    start: String,
    end: String,
    onStartChange: (String) -> Unit,
    onEndChange: (String) -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyLarge,
            modifier = Modifier.weight(1f),
        )
        TimeField(
            value = start,
            onValueChange = onStartChange,
        )
        Text(text = "到")
        TimeField(
            value = end,
            onValueChange = onEndChange,
        )
    }
}

@Composable
private fun TimeField(
    value: String,
    onValueChange: (String) -> Unit,
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        modifier = Modifier.width(96.dp),
        singleLine = true,
        textStyle = MaterialTheme.typography.bodyMedium,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Text),
    )
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
            onParentMessageChange = {},
            onGoalsTextChange = {},
            onOfferChoicesChange = {},
            onDoNotForceExpressionChange = {},
            onAskThinkingBeforeAnswerChange = {},
            onAfterSchoolStartChange = {},
            onAfterSchoolEndChange = {},
            onHomeworkStartChange = {},
            onHomeworkEndChange = {},
            onBedtimeStartChange = {},
            onBedtimeEndChange = {},
        )
    }
}
