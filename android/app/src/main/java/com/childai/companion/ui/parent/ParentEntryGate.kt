package com.childai.companion.ui.parent

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp

enum class ParentEntryTarget(val label: String) {
    Report("家长日报"),
    Settings("家长设置"),
}

object ParentCredentialGate {
    const val GENTLE_ERROR_MESSAGE = "密码没有通过，请家长再试一次。"

    fun isLocalCredentialAccepted(input: String, expectedCredential: String): Boolean =
        expectedCredential.isNotBlank() && input.trim() == expectedCredential
}

@Composable
fun ParentEntryCredentialDialog(
    target: ParentEntryTarget,
    credentialInput: String,
    errorMessage: String?,
    isSubmitting: Boolean,
    onCredentialInputChange: (String) -> Unit,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(text = "进入${target.label}")
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text(
                    text = "请家长输入当前账号密码后继续。",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                OutlinedTextField(
                    value = credentialInput,
                    onValueChange = onCredentialInputChange,
                    singleLine = true,
                    label = {
                        Text(text = "账号密码")
                    },
                    visualTransformation = PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(
                        keyboardType = KeyboardType.Password,
                        imeAction = ImeAction.Done,
                    ),
                    keyboardActions = KeyboardActions(
                        onDone = {
                            onConfirm()
                        },
                    ),
                )
                errorMessage?.let { message ->
                    Text(
                        text = message,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.error,
                    )
                }
            }
        },
        confirmButton = {
            Button(
                onClick = onConfirm,
                enabled = !isSubmitting && credentialInput.isNotBlank(),
            ) {
                Text(text = if (isSubmitting) "验证中" else "进入")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text(text = "取消")
            }
        },
    )
}
