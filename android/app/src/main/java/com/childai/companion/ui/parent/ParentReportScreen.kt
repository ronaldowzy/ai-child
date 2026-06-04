package com.childai.companion.ui.parent

import android.graphics.BitmapFactory
import android.net.Uri
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
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
import androidx.compose.runtime.produceState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.childai.companion.data.parent.ParentReport
import com.childai.companion.ui.theme.ChildAiCompanionTheme
import java.io.File
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

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
            ReportRecentInsights(insights = uiState.recentInsights)
            ReportRecentDiscoveries(events = uiState.recentDiscoveries)
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
private fun ReportRecentInsights(insights: List<ParentReportGrowthInsightUi>) {
    if (insights.isEmpty()) return
    ReportSection(title = "最近成长线索") {
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            insights.forEach { insight ->
                ParentReportGrowthInsightCard(insight = insight)
            }
        }
    }
}

@Composable
private fun ParentReportGrowthInsightCard(insight: ParentReportGrowthInsightUi) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.medium,
        color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.34f),
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(5.dp),
        ) {
            Text(
                text = insight.title,
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.SemiBold,
            )
            Text(
                text = insight.summary,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun ReportRecentDiscoveries(events: List<ParentReportGrowthEventUi>) {
    ReportSection(title = "最近的小发现") {
        if (events.isEmpty()) {
            Text(
                text = PARENT_REPORT_NO_RECENT_DISCOVERIES_MESSAGE,
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                events.forEach { event ->
                    ParentReportGrowthEventCard(event = event)
                }
            }
        }
    }
}

@Composable
private fun ParentReportGrowthEventCard(event: ParentReportGrowthEventUi) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.medium,
        color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.42f),
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            event.relatedPhotoUri?.let { photoUri ->
                ParentReportGrowthEventThumbnail(photoUri = photoUri)
            }
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                Text(
                    text = event.title,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                )
                Text(
                    text = event.summary,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Text(
                    text = parentReportGrowthEventTimeLabel(event.createdAt),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.72f),
                )
            }
        }
    }
}

@Composable
private fun ParentReportGrowthEventThumbnail(photoUri: String) {
    val bitmap by rememberParentReportPhotoBitmap(photoUri)
    if (bitmap != null) {
        Image(
            bitmap = bitmap!!,
            contentDescription = null,
            contentScale = ContentScale.Crop,
            modifier = Modifier
                .size(58.dp)
                .clip(MaterialTheme.shapes.medium),
        )
    }
}

@Composable
private fun rememberParentReportPhotoBitmap(photoUri: String): androidx.compose.runtime.State<ImageBitmap?> {
    val context = LocalContext.current
    return produceState<ImageBitmap?>(initialValue = null, photoUri, context) {
        value = withContext(Dispatchers.IO) {
            runCatching {
                val uri = Uri.parse(photoUri)
                val bitmap = when (uri.scheme?.lowercase()) {
                    "content" -> context.contentResolver.openInputStream(uri)?.use(BitmapFactory::decodeStream)
                    "file" -> BitmapFactory.decodeFile(uri.path)
                    "http", "https" -> URL(photoUri).openStream().use(BitmapFactory::decodeStream)
                    else -> BitmapFactory.decodeFile(File(photoUri).absolutePath)
                }
                bitmap?.asImageBitmap()
            }.getOrNull()
        }
    }
}

private fun parentReportGrowthEventTimeLabel(createdAt: Long): String {
    if (createdAt <= 0L) return ""
    return SimpleDateFormat("MM-dd HH:mm", Locale.CHINA).format(Date(createdAt))
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
    report.companionSummary?.let { summary ->
        ReportSection(title = "轻共创") {
            Text(
                text = summary,
                style = MaterialTheme.typography.bodyLarge,
            )
        }
    }
    if (report.topicOverview.isNotEmpty()) {
        ReportSection(title = "孩子今天提到的内容") {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                report.topicOverview.forEach { topic ->
                    val displayText = topic.summary.takeIf { it.isNotBlank() } ?: topic.topic
                    Text(
                        text = "· $displayText",
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
                recentInsights = listOf(
                    ParentReportGrowthInsightUi(
                        id = "growth_insight_preview",
                        title = "最近留下的小发现",
                        summary = "孩子最近留下了 3 个小发现，比如「小石头」「小云朵」「小纸船」。",
                    ),
                ),
                recentDiscoveries = listOf(
                    ParentReportGrowthEventUi(
                        id = "growth_event_preview",
                        title = "留下了一个小发现",
                        summary = "孩子把「小石头」放进了小展台。小白狐当时说：它看起来像一颗安静的小星球。",
                        createdAt = 1760000000000L,
                        relatedPhotoUri = null,
                    ),
                ),
            ),
            onBack = {},
            onDateChange = {},
            onLoad = {},
        )
    }
}
