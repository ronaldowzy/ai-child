package com.childai.companion.ui.auth

import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.childai.companion.ui.theme.ChildAiCompanionTheme

private val genderOptions = listOf(
    "" to "不填写",
    "boy" to "男孩",
    "girl" to "女孩",
    "prefer_not_to_say" to "不填写",
)

@Composable
fun AuthScreen(
    viewModel: AuthViewModel,
    modifier: Modifier = Modifier,
) {
    val uiState by viewModel.uiState.collectAsState()
    AuthScreenContent(
        uiState = uiState,
        onModeChange = viewModel::updateMode,
        onUsernameChange = viewModel::updateUsername,
        onPasswordChange = viewModel::updatePassword,
        onChildNicknameChange = viewModel::updateChildNickname,
        onChildAgeChange = viewModel::updateChildAge,
        onChildGradeChange = viewModel::updateChildGrade,
        onChildGenderChange = viewModel::updateChildGender,
        onChildInterestsChange = viewModel::updateChildInterests,
        onSubmit = viewModel::submit,
        modifier = modifier,
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun AuthScreenContent(
    uiState: AuthUiState,
    onModeChange: (AuthMode) -> Unit,
    onUsernameChange: (String) -> Unit,
    onPasswordChange: (String) -> Unit,
    onChildNicknameChange: (String) -> Unit,
    onChildAgeChange: (String) -> Unit,
    onChildGradeChange: (String) -> Unit,
    onChildGenderChange: (String) -> Unit,
    onChildInterestsChange: (String) -> Unit,
    onSubmit: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.safeDrawing),
        color = MaterialTheme.colorScheme.background,
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .imePadding()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 28.dp, vertical = 26.dp),
            verticalArrangement = Arrangement.Top,
        ) {
            Text(
                text = if (uiState.mode == AuthMode.Register) {
                    "创建孩子账号"
                } else {
                    "家长登录"
                },
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.onBackground,
            )
            Text(
                text = "账号由家长创建和管理，孩子进入后不会看到密码设置。",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 8.dp, bottom = 18.dp),
            )
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = uiState.username,
                    onValueChange = onUsernameChange,
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    label = { Text("账号") },
                    enabled = !uiState.isSubmitting,
                )
                OutlinedTextField(
                    value = uiState.password,
                    onValueChange = onPasswordChange,
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    label = { Text("密码") },
                    visualTransformation = PasswordVisualTransformation(),
                    enabled = !uiState.isSubmitting,
                )
                if (uiState.mode == AuthMode.Register) {
                    OutlinedTextField(
                        value = uiState.childNickname,
                        onValueChange = onChildNicknameChange,
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        label = { Text("孩子常用称呼") },
                        enabled = !uiState.isSubmitting,
                    )
                    OutlinedTextField(
                        value = uiState.childAge,
                        onValueChange = onChildAgeChange,
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        label = { Text("年龄（可选，5-10）") },
                        enabled = !uiState.isSubmitting,
                    )
                    OutlinedTextField(
                        value = uiState.childGrade,
                        onValueChange = onChildGradeChange,
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        label = { Text("年级（可选）") },
                        enabled = !uiState.isSubmitting,
                    )
                    GenderDropdown(
                        selected = uiState.childGender,
                        onSelect = onChildGenderChange,
                        enabled = !uiState.isSubmitting,
                    )
                    OutlinedTextField(
                        value = uiState.childInterestsText,
                        onValueChange = onChildInterestsChange,
                        modifier = Modifier.fillMaxWidth(),
                        minLines = 2,
                        maxLines = 4,
                        label = { Text("最近愿意聊的兴趣（可选）") },
                        enabled = !uiState.isSubmitting,
                    )
                }
                uiState.errorMessage?.let { error ->
                    Text(
                        text = error,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.error,
                    )
                }
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Button(
                        onClick = onSubmit,
                        enabled = !uiState.isSubmitting,
                    ) {
                        Text(
                            text = if (uiState.isSubmitting) {
                                "请稍等"
                            } else if (uiState.mode == AuthMode.Register) {
                                "创建并登录"
                            } else {
                                "登录"
                            },
                        )
                    }
                    Spacer(modifier = Modifier.width(12.dp))
                    TextButton(
                        onClick = {
                            onModeChange(
                                if (uiState.mode == AuthMode.Register) {
                                    AuthMode.Login
                                } else {
                                    AuthMode.Register
                                },
                            )
                        },
                        enabled = !uiState.isSubmitting,
                    ) {
                        Text(
                            text = if (uiState.mode == AuthMode.Register) {
                                "已有账号"
                            } else {
                                "创建账号"
                            },
                        )
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun GenderDropdown(
    selected: String,
    onSelect: (String) -> Unit,
    enabled: Boolean,
) {
    var expanded by remember { mutableStateOf(false) }
    val selectedLabel = genderOptions.firstOrNull { it.first == selected }?.second ?: "不填写"

    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { if (enabled) expanded = !expanded },
    ) {
        OutlinedTextField(
            value = selectedLabel,
            onValueChange = {},
            modifier = Modifier
                .fillMaxWidth()
                .menuAnchor(),
            readOnly = true,
            singleLine = true,
            label = { Text("性别（可选）") },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            enabled = enabled,
        )
        ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
        ) {
            genderOptions.forEach { (value, label) ->
                DropdownMenuItem(
                    text = { Text(label) },
                    onClick = {
                        onSelect(value)
                        expanded = false
                    },
                )
            }
        }
    }
}

@Preview(showBackground = true, widthDp = 420, heightDp = 720)
@Composable
private fun AuthScreenPreview() {
    ChildAiCompanionTheme {
        AuthScreenContent(
            uiState = AuthUiState(mode = AuthMode.Register),
            onModeChange = {},
            onUsernameChange = {},
            onPasswordChange = {},
            onChildNicknameChange = {},
            onChildAgeChange = {},
            onChildGradeChange = {},
            onChildGenderChange = {},
            onChildInterestsChange = {},
            onSubmit = {},
        )
    }
}

@Preview(showBackground = true, widthDp = 900, heightDp = 360)
@Composable
private fun AuthScreenLandscapePreview() {
    ChildAiCompanionTheme {
        AuthScreenContent(
            uiState = AuthUiState(mode = AuthMode.Register),
            onModeChange = {},
            onUsernameChange = {},
            onPasswordChange = {},
            onChildNicknameChange = {},
            onChildAgeChange = {},
            onChildGradeChange = {},
            onChildGenderChange = {},
            onChildInterestsChange = {},
            onSubmit = {},
        )
    }
}
