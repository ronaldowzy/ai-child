package com.childai.companion.ui.parent

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childai.companion.config.DevSettings
import com.childai.companion.data.parent.ParentPolicyRepository
import com.childai.companion.data.parent.ParentPolicyResponse
import com.childai.companion.data.parent.ParentPolicyUpdateRequest
import com.childai.companion.data.parent.ParentSchedule
import com.childai.companion.data.parent.defaultParentSchedule
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class ParentPolicyViewModel(
    private val repository: ParentPolicyRepository = ParentPolicyRepository(),
) : ViewModel() {
    private var loadedPolicy: ParentPolicyResponse? = null

    private val _uiState = MutableStateFlow(ParentPolicyUiState())
    val uiState: StateFlow<ParentPolicyUiState> = _uiState

    init {
        loadPolicy()
    }

    fun loadPolicy() {
        if (_uiState.value.isLoading) return
        _uiState.update {
            it.copy(
                isLoading = true,
                errorMessage = null,
                statusMessage = null,
            )
        }
        viewModelScope.launch {
            runCatching {
                repository.getPolicy(DevSettings.CHILD_ID)
            }.onSuccess { policy ->
                loadedPolicy = policy
                _uiState.update {
                    it.copy(
                        form = policy.toFormState(),
                        isLoading = false,
                        errorMessage = null,
                    )
                }
            }.onFailure {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        errorMessage = "没有读到父亲设置，请检查后端是否启动。",
                    )
                }
            }
        }
    }

    fun updateGoalsText(value: String) {
        updateForm { it.copy(goalsText = value) }
    }

    fun updateOfferChoices(value: Boolean) {
        updateForm { it.copy(offerChoices = value) }
    }

    fun updateDoNotForceExpression(value: Boolean) {
        updateForm { it.copy(doNotForceExpression = value) }
    }

    fun updateAskThinkingBeforeAnswer(value: Boolean) {
        updateForm { it.copy(askThinkingBeforeAnswer = value) }
    }

    fun updateAfterSchoolStart(value: String) {
        updateForm { it.copy(afterSchoolStart = value) }
    }

    fun updateAfterSchoolEnd(value: String) {
        updateForm { it.copy(afterSchoolEnd = value) }
    }

    fun updateHomeworkStart(value: String) {
        updateForm { it.copy(homeworkStart = value) }
    }

    fun updateHomeworkEnd(value: String) {
        updateForm { it.copy(homeworkEnd = value) }
    }

    fun updateBedtimeStart(value: String) {
        updateForm { it.copy(bedtimeStart = value) }
    }

    fun updateBedtimeEnd(value: String) {
        updateForm { it.copy(bedtimeEnd = value) }
    }

    fun savePolicy() {
        val form = _uiState.value.form
        if (_uiState.value.isSaving) return
        if (!form.hasValidTimes()) {
            _uiState.update {
                it.copy(errorMessage = "作息时间请使用 HH:MM 格式。")
            }
            return
        }

        val basePolicy = loadedPolicy
        val schedule = (basePolicy?.schedule ?: defaultParentSchedule())
            .withEntryTimes(
                period = "after_school",
                start = form.afterSchoolStart,
                end = form.afterSchoolEnd,
            )
            .withEntryTimes(
                period = "homework_time",
                start = form.homeworkStart,
                end = form.homeworkEnd,
            )
            .withEntryTimes(
                period = "bedtime",
                start = form.bedtimeStart,
                end = form.bedtimeEnd,
            )
        val request = ParentPolicyUpdateRequest(
            childId = DevSettings.CHILD_ID,
            goals = form.goals(),
            communicationPreferences = form.communicationPreferences(
                basePolicy?.communicationPreferences.orEmpty(),
            ),
            schedule = schedule,
        )

        _uiState.update {
            it.copy(isSaving = true, errorMessage = null, statusMessage = null)
        }
        viewModelScope.launch {
            runCatching {
                repository.updatePolicy(request)
            }.onSuccess { policy ->
                loadedPolicy = policy
                _uiState.update {
                    it.copy(
                        form = policy.toFormState(),
                        isSaving = false,
                        statusMessage = "已保存，下一次对话会使用新的父亲设置。",
                    )
                }
            }.onFailure {
                _uiState.update {
                    it.copy(
                        isSaving = false,
                        errorMessage = "保存失败，请检查后端是否启动。",
                    )
                }
            }
        }
    }

    private fun updateForm(update: (ParentPolicyFormState) -> ParentPolicyFormState) {
        _uiState.update {
            it.copy(
                form = update(it.form),
                errorMessage = null,
                statusMessage = null,
            )
        }
    }
}

data class ParentPolicyUiState(
    val form: ParentPolicyFormState = ParentPolicyFormState(),
    val isLoading: Boolean = false,
    val isSaving: Boolean = false,
    val errorMessage: String? = null,
    val statusMessage: String? = null,
)

data class ParentPolicyFormState(
    val goalsText: String = "鼓励孩子每天说一件学校小事\n学习问题先引导思路，不直接给答案",
    val offerChoices: Boolean = true,
    val doNotForceExpression: Boolean = true,
    val askThinkingBeforeAnswer: Boolean = true,
    val afterSchoolStart: String = "15:30",
    val afterSchoolEnd: String = "18:00",
    val homeworkStart: String = "18:00",
    val homeworkEnd: String = "20:20",
    val bedtimeStart: String = "20:20",
    val bedtimeEnd: String = "21:30",
) {
    fun goals(): List<String> {
        return goalsText.lines()
            .map { it.trim() }
            .filter { it.isNotEmpty() }
    }

    fun communicationPreferences(
        existing: Map<String, Any>,
    ): Map<String, Any> {
        return existing + mapOf(
            "offer_choices_before_open_questions" to offerChoices,
            "do_not_force_expression" to doNotForceExpression,
            "ask_thinking_before_learning_answer" to askThinkingBeforeAnswer,
            "tone" to "warm_calm",
            "avoid_labels" to true,
        )
    }

    fun hasValidTimes(): Boolean {
        return listOf(
            afterSchoolStart,
            afterSchoolEnd,
            homeworkStart,
            homeworkEnd,
            bedtimeStart,
            bedtimeEnd,
        ).all { TIME_PATTERN.matches(it) }
    }
}

private fun ParentPolicyResponse.toFormState(): ParentPolicyFormState {
    val schedule = scheduleWithDefaults(schedule)
    return ParentPolicyFormState(
        goalsText = goals.joinToString(separator = "\n"),
        offerChoices = communicationPreferences.booleanValue(
            key = "offer_choices_before_open_questions",
            fallback = communicationPreferences["expression_support"] ==
                "offer_choices_before_open_questions",
        ),
        doNotForceExpression = communicationPreferences.booleanValue(
            key = "do_not_force_expression",
            fallback = true,
        ),
        askThinkingBeforeAnswer = communicationPreferences.booleanValue(
            key = "ask_thinking_before_learning_answer",
            fallback = true,
        ),
        afterSchoolStart = schedule.entry("after_school")?.start ?: "15:30",
        afterSchoolEnd = schedule.entry("after_school")?.end ?: "18:00",
        homeworkStart = schedule.entry("homework_time")?.start ?: "18:00",
        homeworkEnd = schedule.entry("homework_time")?.end ?: "20:20",
        bedtimeStart = schedule.entry("bedtime")?.start ?: "20:20",
        bedtimeEnd = schedule.entry("bedtime")?.end ?: "21:30",
    )
}

private fun scheduleWithDefaults(schedule: ParentSchedule): ParentSchedule {
    val defaults = defaultParentSchedule()
    return listOf("after_school", "homework_time", "bedtime").fold(schedule) { current, period ->
        current.entry(period)?.let { current }
            ?: current.withEntryTimes(
                period = period,
                start = defaults.entry(period)?.start ?: "18:00",
                end = defaults.entry(period)?.end ?: "20:00",
            )
    }
}

private fun Map<String, Any>.booleanValue(key: String, fallback: Boolean): Boolean {
    return when (val value = this[key]) {
        is Boolean -> value
        is String -> value == "true"
        else -> fallback
    }
}

private val TIME_PATTERN = Regex("^\\d{2}:\\d{2}$")
