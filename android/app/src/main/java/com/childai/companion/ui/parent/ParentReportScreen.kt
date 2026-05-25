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
import androidx.compose.material3.Surface
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
import com.childai.companion.data.parent.ParentReportTopicOverview
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
                    Text(text = if (uiState.isLoading) "读取中" else "读取日报")
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
                if (report.isGeneratedSuccessfully) {
                    ReportBody(report = report)
                } else {
                    ReportGenerationStatus(report = report)
                }
            }
        }
    }
}

@Composable
private fun ReportGenerationStatus(report: ParentReport) {
    ReportSection(title = "日报生成状态") {
        Text(
            text = PARENT_REPORT_LOAD_FAILURE_MESSAGE,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.error,
        )
        Text(
            text = report.bridgeText,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun ReportBody(report: ParentReport) {
    ReportSection(title = PARENT_REPORT_BRIDGE_SECTION_TITLE) {
        Text(
            text = report.bridgeText,
            style = MaterialTheme.typography.bodyLarge,
        )
    }
    ReportSection(title = PARENT_REPORT_TOPIC_SECTION_TITLE) {
        report.conversationSummary?.let { summary ->
            Text(
                text = summary,
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
        if (report.topicOverview.isEmpty()) {
            Text(
                text = "今天还没有足够的结构化话题摘要。",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                report.topicOverview.forEach { topic ->
                    TopicOverviewCard(topic = topic)
                }
            }
        }
    }
    ReportSection(title = "今日整体摘要") {
        Text(
            text = report.summary,
            style = MaterialTheme.typography.bodyLarge,
        )
    }
    ReportSection(
        title = "学习观察",
        items = report.learningObservations,
    )
    ReportSection(
        title = "表达观察",
        items = report.expressionObservations,
    )
    ReportSection(
        title = "情绪/社交观察",
        items = report.emotionObservations,
    )
    ReportSection(
        title = "建议家长动作",
        items = report.suggestedParentActions,
    )
    ReportSection(
        title = "今晚先不追问",
        items = report.avoidFollowup,
        emptyText = "避免连续追问，先轻松陪孩子做一件现实里的小事。",
    )
    ReportSection(
        title = "需要关注事项",
        items = report.safetyAlerts,
        emptyText = "暂无需要关注事项。",
    )
}

@Composable
private fun TopicOverviewCard(topic: ParentReportTopicOverview) {
    Surface(
        color = MaterialTheme.colorScheme.surfaceVariant,
        shape = MaterialTheme.shapes.small,
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(
                text = topic.topic,
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            if (topic.summary.isNotBlank()) {
                Text(
                    text = topic.summary,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            if (topic.parentBridge.isNotBlank()) {
                Text(
                    text = topic.parentBridge,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun ReportSection(
    title: String,
    items: List<String>,
    emptyText: String = "暂无结构化观察。",
) {
    ReportSection(title = title) {
        if (items.isEmpty()) {
            Text(
                text = emptyText,
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items.forEach { item ->
                    Row {
                        Text(text = "·", style = MaterialTheme.typography.bodyLarge)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = item,
                            style = MaterialTheme.typography.bodyLarge,
                            modifier = Modifier.weight(1f),
                        )
                    }
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
                    summary = "今天暂无可汇总的结构化会话素材。建议保持轻量观察，不做额外判断。",
                    learningObservations = emptyList(),
                    expressionObservations = emptyList(),
                    emotionObservations = emptyList(),
                    safetyAlerts = emptyList(),
                    suggestedParentActions = listOf(
                        "今晚用一个具体问题轻轻收尾，不要追问过多。",
                    ),
                    topicOverview = listOf(
                        ParentReportTopicOverview(
                            topic = "图片分享",
                            childIntent = "想分享给小白狐看",
                            summary = "孩子今天把图片作为表达入口，适合先问最想看哪里。",
                            emotionTone = "好奇",
                            parentBridge = "今晚可以轻轻问那张图最想让我看哪里。",
                        ),
                    ),
                    conversationSummary = "今天主要聊了图片分享，没有输出逐字聊天记录。",
                    tonightParentBridge = "今晚可以轻轻问：“今天有没有一件还不错的小事？”如果孩子不想说，就换轻松方式。",
                    avoidFollowup = listOf("不要追问孩子在小白狐里逐字聊了什么。"),
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

internal const val PARENT_REPORT_BRIDGE_SECTION_TITLE = "今晚可以怎么接一句"
internal const val PARENT_REPORT_TOPIC_SECTION_TITLE = "今日聊了什么"
