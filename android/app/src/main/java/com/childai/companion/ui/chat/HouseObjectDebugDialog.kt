package com.childai.companion.ui.chat

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

@Composable
internal fun HouseObjectDebugDialog(
    visualKind: String,
    state: String,
    lightLocation: String,
    statusText: String?,
    isBusy: Boolean,
    canUseRemoteDebug: Boolean,
    onVisualKindChange: (String) -> Unit,
    onStateChange: (String) -> Unit,
    onLightLocationChange: (String) -> Unit,
    onPreview: () -> Unit,
    onCreateRemote: () -> Unit,
    onResetRemote: () -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(text = "开发调试")
        },
        text = {
            Column(
                modifier = Modifier
                    .heightIn(max = 520.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                HouseObjectDebugSection(
                    title = "素材",
                    options = houseObjectDebugVisualKinds,
                    selectedId = visualKind,
                    onSelected = onVisualKindChange,
                )
                HouseObjectDebugSection(
                    title = "状态",
                    options = houseObjectDebugStates,
                    selectedId = state,
                    onSelected = onStateChange,
                )
                HouseObjectDebugSection(
                    title = "位置",
                    options = houseObjectDebugLocations,
                    selectedId = lightLocation,
                    onSelected = onLightLocationChange,
                )
                statusText?.let { text ->
                    Text(
                        text = text,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                Spacer(modifier = Modifier.height(2.dp))
                Button(
                    onClick = onPreview,
                    enabled = !isBusy,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(text = "仅本地预览")
                }
                OutlinedButton(
                    onClick = onCreateRemote,
                    enabled = !isBusy && canUseRemoteDebug && houseObjectDebugCanPersist(state),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(text = "真实落库创建")
                }
                OutlinedButton(
                    onClick = onResetRemote,
                    enabled = !isBusy && canUseRemoteDebug,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(text = "重置当前 child 小客人")
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text(text = "关闭")
            }
        },
    )
}

@Composable
private fun HouseObjectDebugSection(
    title: String,
    options: List<HouseObjectDebugOption>,
    selectedId: String,
    onSelected: (String) -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(
            text = title,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.SemiBold,
        )
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            options.forEach { option ->
                FilterChip(
                    selected = option.id == selectedId,
                    onClick = { onSelected(option.id) },
                    label = {
                        Text(text = option.label)
                    },
                )
            }
        }
    }
}
