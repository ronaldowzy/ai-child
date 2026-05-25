package com.childai.companion.ui.parent

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childai.companion.config.DevSettings
import com.childai.companion.data.parent.ParentReport
import com.childai.companion.data.parent.ParentReportRepository
import java.time.LocalDate
import java.time.ZoneId
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class ParentReportViewModel(
    private val repository: ParentReportRepository = ParentReportRepository(),
    private val childId: String = DevSettings.CHILD_ID,
) : ViewModel() {
    private val _uiState = MutableStateFlow(
        ParentReportUiState(date = todayDateText()),
    )
    val uiState: StateFlow<ParentReportUiState> = _uiState

    init {
        loadReport()
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

        _uiState.update {
            it.copy(isLoading = true, errorMessage = null)
        }
        viewModelScope.launch {
            runCatching {
                repository.getReport(
                    childId = childId,
                    date = date,
                )
            }.onSuccess { report ->
                _uiState.update {
                    it.copy(
                        report = report,
                        isLoading = false,
                        errorMessage = null,
                    )
                }
            }.onFailure {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        errorMessage = PARENT_REPORT_LOAD_FAILURE_MESSAGE,
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
)

private fun todayDateText(): String {
    val zone = runCatching { ZoneId.of(DevSettings.TIMEZONE) }
        .getOrElse { ZoneId.systemDefault() }
    return LocalDate.now(zone).toString()
}

private val DATE_PATTERN = Regex("^\\d{4}-\\d{2}-\\d{2}$")

internal const val PARENT_REPORT_LOAD_FAILURE_MESSAGE = "今天的小结还没准备好，请稍后再试。"
