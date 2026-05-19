package com.childai.companion.ui.chat

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import com.childai.companion.voice.TtsUiState

@Composable
fun InputBar(
    onSend: (String) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    voice: VoiceUiState = VoiceUiState(),
    tts: TtsUiState = TtsUiState(),
    onStopTts: () -> Unit = {},
    onToggleTtsMuted: () -> Unit = {},
) {
    var draft by rememberSaveable { mutableStateOf("") }
    val trimmedDraft = draft.trim()

    fun sendDraft() {
        if (enabled && trimmedDraft.isNotEmpty()) {
            onSend(trimmedDraft)
            draft = ""
        }
    }

    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            OutlinedTextField(
                value = draft,
                onValueChange = { draft = it },
                enabled = enabled,
                modifier = Modifier.weight(1f),
                placeholder = {
                    Text(text = "说点什么")
                },
                textStyle = MaterialTheme.typography.bodyLarge,
                singleLine = true,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                keyboardActions = KeyboardActions(onSend = { sendDraft() }),
            )
            TextButton(
                onClick = {},
                enabled = false,
                modifier = Modifier.widthIn(min = 64.dp),
            ) {
                Text(text = "语音")
            }
            Button(
                onClick = { sendDraft() },
                enabled = enabled && trimmedDraft.isNotEmpty(),
                modifier = Modifier.widthIn(min = 88.dp),
            ) {
                Text(text = if (enabled) "发送" else "发送中")
            }
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = "${voice.statusText} · ${tts.statusText}",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.weight(1f),
            )
            if (tts.isSpeaking) {
                TextButton(onClick = onStopTts) {
                    Text(text = "停止")
                }
            }
            TextButton(onClick = onToggleTtsMuted) {
                Text(text = if (tts.isMuted) "打开朗读" else "静音")
            }
        }
    }
}
