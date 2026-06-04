package com.childai.companion.ui.parent

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childai.companion.config.DevSettings
import com.childai.companion.data.growth.GROWTH_EVENT_SOURCE_XIAOZHANTAI
import com.childai.companion.data.growth.GROWTH_EVENT_TYPE_SHOWCASE_ITEM_RECALLED
import com.childai.companion.data.growth.GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED
import com.childai.companion.data.growth.GrowthEvent
import com.childai.companion.data.growth.GrowthEventRepository
import com.childai.companion.data.parent.ParentReport
import com.childai.companion.data.parent.ParentReportRepository
import java.time.LocalDate
import java.time.ZoneId
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class ParentReportViewModel(
    repository: ParentReportRepository = ParentReportRepository(),
    private val growthEventRepository: GrowthEventRepository = GrowthEventRepository(),
    private val childId: String = DevSettings.CHILD_ID,
    private val nowMillis: () -> Long = System::currentTimeMillis,
    private val reportReader: suspend (String, String) -> ParentReport = repository::getReport,
    requestReportOnInit: Boolean = true,
) : ViewModel() {
    private val _uiState = MutableStateFlow(
        ParentReportUiState(date = todayDateText()),
    )
    val uiState: StateFlow<ParentReportUiState> = _uiState

    private var loadJob: Job? = null

    init {
        observeGrowthEvents()
        if (requestReportOnInit) {
            loadReport()
        }
    }

    fun updateDate(value: String) {
        _uiState.update {
            it.copy(date = value, errorMessage = null)
        }
    }

    fun loadReport() {
        val date = _uiState.value.date.trim()
        if (_uiState.value.isLoading) return
        if (!DATE_PATTERN.matches(date)) {
            _uiState.update {
                it.copy(errorMessage = "日期请使用 YYYY-MM-DD 格式。")
            }
            return
        }

        loadJob?.cancel()
        _uiState.update {
            it.copy(
                isLoading = true,
                report = null,
                errorMessage = null,
            )
        }
        loadJob = viewModelScope.launch {
            var report: ParentReport? = null
            var error: Exception? = null
            val apiJob = launch {
                try {
                    report = reportReader(childId, date)
                } catch (e: Exception) {
                    error = e
                }
            }
            delay(REPORT_TIMEOUT_MS)
            if (apiJob.isActive) {
                _uiState.update {
                    it.copy(isLoading = false, errorMessage = PARENT_REPORT_TIMEOUT_MESSAGE)
                }
            }
            apiJob.join()
            val finalReport = report
            val finalError = error
            if (finalReport != null) {
                _uiState.update {
                    it.copy(
                        report = finalReport,
                        isLoading = false,
                        errorMessage = null,
                    )
                }
            } else if (finalError != null) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        errorMessage = PARENT_REPORT_FAILED_MESSAGE,
                    )
                }
            }
        }
    }

    private fun observeGrowthEvents() {
        viewModelScope.launch {
            growthEventRepository.observeEvents(childId).collect { events ->
                _uiState.update {
                    it.copy(
                        recentDiscoveries = parentReportRecentDiscoveries(
                            events = events,
                            nowMillis = nowMillis(),
                        ),
                    )
                }
            }
        }
    }
}

data class ParentReportUiState(
    val date: String,
    val report: ParentReport? = null,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val recentDiscoveries: List<ParentReportGrowthEventUi> = emptyList(),
)

data class ParentReportGrowthEventUi(
    val id: String,
    val title: String,
    val summary: String,
    val createdAt: Long,
    val relatedPhotoUri: String?,
)

internal fun parentReportRecentDiscoveries(
    events: List<GrowthEvent>,
    nowMillis: Long,
    maxItems: Int = PARENT_REPORT_GROWTH_EVENT_LIMIT,
): List<ParentReportGrowthEventUi> {
    val earliestCreatedAt = nowMillis - PARENT_REPORT_GROWTH_EVENT_WINDOW_MS
    return events
        .asSequence()
        .filter {
            !it.isDeleted &&
                it.type in PARENT_REPORT_XIAOZHANTAI_EVENT_TYPES &&
                it.source == GROWTH_EVENT_SOURCE_XIAOZHANTAI &&
                it.createdAt >= earliestCreatedAt
        }
        .sortedByDescending { it.createdAt }
        .take(maxItems)
        .map { event ->
            ParentReportGrowthEventUi(
                id = event.id,
                title = event.title,
                summary = event.summary,
                createdAt = event.createdAt,
                relatedPhotoUri = event.relatedPhotoUri?.takeIf { it.isNotBlank() },
            )
        }
        .toList()
}

private fun todayDateText(): String {
    val zone = runCatching { ZoneId.of(DevSettings.TIMEZONE) }
        .getOrElse { ZoneId.systemDefault() }
    return LocalDate.now(zone).toString()
}

private val DATE_PATTERN = Regex("^\\d{4}-\\d{2}-\\d{2}$")
private val PARENT_REPORT_XIAOZHANTAI_EVENT_TYPES = setOf(
    GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED,
    GROWTH_EVENT_TYPE_SHOWCASE_ITEM_RECALLED,
)

internal const val REPORT_TIMEOUT_MS = 30_000L
internal const val PARENT_REPORT_TIMEOUT_MESSAGE = "今天的小结还没整理好，可以稍后再看。"
internal const val PARENT_REPORT_FAILED_MESSAGE = "这次没有整理成功，可以再试一次。"
internal const val PARENT_REPORT_INSUFFICIENT_MESSAGE = "今天聊得还不多，小结会短一点。"
internal const val PARENT_REPORT_NO_RECENT_DISCOVERIES_MESSAGE = "这几天还没有新的小发现。"
internal const val PARENT_REPORT_GROWTH_EVENT_LIMIT = 10
internal const val PARENT_REPORT_GROWTH_EVENT_WINDOW_MS = 7L * 24L * 60L * 60L * 1000L
