package com.childai.companion.ui.parent

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
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
import com.childai.companion.data.parent.ParentReport
import com.childai.companion.ui.theme.ChildAiCompanionTheme

@Composable
fun ParentReportScreen(
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ParentReportViewModel = viewModel(),
) {
    val uiState by viewModel.uiState.collectAsState()

    ParentReportScreenContent(
        uiState = uiState,
        onBack = onBack,
        onDateChange = viewModel::updateDate,
        onLoad = viewModel::loadReport,
        modifier = modifier,
    )
}

@Composable
private fun ParentReportScreenContent(
    uiState: ParentReportUiState,
    onBack: () -> Unit,
    onDateChange: (String) -> Unit,
    onLoad: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        modifier = modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.safeDrawing),
        topBar = {
            ParentTopBar(
                title = "家长日报",
                onBack = onBack,
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
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                OutlinedTextField(
                    value = uiState.date,
                    onValueChange = onDateChange,
                    modifier = Modifier.width(170.dp),
                    singleLine = true,
                    label = {
                        Text(text = "日期")
                    },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Text),
                )
                Button(
                    onClick = onLoad,
                    enabled = !uiState.isLoading,
                ) {
                    Text(text = if (uiState.isLoading) "正在整理" else "查看今天小结")
                }
                if (uiState.isLoading) {
                    CircularProgressIndicator()
                }
            }
            uiState.errorMessage?.let { error ->
                Text(
                    text = error,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.error,
                )
            }
            uiState.report?.let { report ->
                when {
                    report.isGeneratedSuccessfully -> ReportBody(report = report)
                    report.isMaterialInsufficient -> ReportMaterialInsufficient()
                    else -> ReportFailed(onRetry = onLoad)
                }
            }
        }
    }
}

@Composable
private fun ReportMaterialInsufficient() {
    ReportSection(title = "今天的小结") {
        Text(
            text = PARENT_REPORT_INSUFFICIENT_MESSAGE,
            style = MaterialTheme.typography.bodyLarge,
        )
    }
}

@Composable
private fun ReportFailed(onRetry: () -> Unit) {
    ReportSection(title = "今天的小结") {
        Text(
            text = PARENT_REPORT_FAILED_MESSAGE,
            style = MaterialTheme.typography.bodyLarge,
        )
        Button(onClick = onRetry) {
            Text(text = "再试一次")
        }
    }
}

@Composable
private fun ReportBody(report: ParentReport) {
    ReportSection(title = "今天一句话") {
        Text(
            text = report.summary,
            style = MaterialTheme.typography.bodyLarge,
        )
    }
    if (report.topicOverview.isNotEmpty()) {
        ReportSection(title = "孩子今天提到的内容") {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                report.topicOverview.forEach { topic ->
                    Text(
                        text = "· ${topic.topic}",
                        style = MaterialTheme.typography.bodyLarge,
                    )
                }
            }
        }
    }
    if (report.safetyAlerts.isNotEmpty()) {
        ReportSection(title = "需要留意的地方") {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                report.safetyAlerts.forEach { alert ->
                    Text(
                        text = "· $alert",
                        style = MaterialTheme.typography.bodyLarge,
                    )
                }
            }
        }
    }
}

@Composable
private fun ReportSection(
    title: String,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(
        verticalArrangement = Arrangement.spacedBy(10.dp),
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

@Preview(showBackground = true, widthDp = 900, heightDp = 700)
@Composable
private fun ParentReportScreenPreview() {
    ChildAiCompanionTheme {
        ParentReportScreenContent(
            uiState = ParentReportUiState(
                date = "2026-05-18",
                report = ParentReport(
                    childId = "child_demo_001",
                    date = "2026-05-18",
                    summary = "今天聊了跳绳和游戏，孩子主动分享了运动后的感受，整体情绪比较轻松。",
                    topicOverview = emptyList(),
                    conversationSummary = null,
                    learningObservations = emptyList(),
                    expressionObservations = emptyList(),
                    emotionObservations = emptyList(),
                    safetyAlerts = emptyList(),
                    suggestedParentActions = emptyList(),
                    tonightParentBridge = null,
                    avoidFollowup = emptyList(),
                    generationStatus = "model_generated",
                    generatedBy = "model",
                ),
            ),
            onBack = {},
            onDateChange = {},
            onLoad = {},
        )
    }
}
