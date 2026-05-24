package com.childai.companion.ui.parent

import com.childai.companion.data.parent.ParentPolicyResponse
import com.childai.companion.data.parent.ParentSchedule
import com.childai.companion.data.parent.ParentPolicyUpdateRequest
import com.childai.companion.data.parent.defaultParentSchedule
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class ParentPolicyViewModelTest {
    @Test
    fun loadPolicyMapsChildNamesIntoForm() {
        val viewModel = ParentPolicyViewModel(
            policyReader = {
                policyResponse(
                    childNickname = "豆豆",
                    childDisplayName = "王小明",
                )
            },
            policyWriter = { policyResponse() },
            dispatcher = Dispatchers.Unconfined,
        )

        val form = viewModel.uiState.value.form
        assertEquals("豆豆", form.childNickname)
        assertEquals("王小明", form.childDisplayName)
    }

    @Test
    fun savePolicySubmitsTrimmedChildNamesWithoutDroppingExistingFields() {
        var savedRequest: ParentPolicyUpdateRequest? = null
        val viewModel = ParentPolicyViewModel(
            policyReader = {
                policyResponse(
                    childNickname = "旧小名",
                    childDisplayName = "旧显示名",
                    parentMessageRaw = "原来的父母寄语",
                    goals = listOf("保留目标"),
                    communicationPreferences = mapOf(
                        "custom_preference" to "kept",
                        "offer_choices_before_open_questions" to true,
                    ),
                )
            },
            policyWriter = { request ->
                savedRequest = request
                policyResponse(
                    childNickname = request.childNickname,
                    childDisplayName = request.childDisplayName,
                    parentMessageRaw = request.parentMessageRaw,
                    goals = request.goals,
                    communicationPreferences = request.communicationPreferences,
                    schedule = request.schedule,
                )
            },
            dispatcher = Dispatchers.Unconfined,
        )

        viewModel.updateChildNickname("  豆豆  ")
        viewModel.updateChildDisplayName("  王小明  ")
        viewModel.savePolicy()

        val request = savedRequest
        assertNotNull(request)
        requireNotNull(request)
        assertEquals("豆豆", request.childNickname)
        assertEquals("王小明", request.childDisplayName)
        assertEquals("原来的父母寄语", request.parentMessageRaw)
        assertEquals(listOf("保留目标"), request.goals)
        assertEquals("kept", request.communicationPreferences["custom_preference"])
        assertEquals(
            "15:30",
            request.schedule.entry("after_school")?.start,
        )
    }

    @Test
    fun loadAndSavePolicyMapsSimplifiedChildProfilePreferences() {
        var savedRequest: ParentPolicyUpdateRequest? = null
        val viewModel = ParentPolicyViewModel(
            policyReader = {
                policyResponse(
                    communicationPreferences = mapOf(
                        "child_age" to 8,
                        "child_grade" to "二年级",
                        "child_call_preference" to "叫小名",
                        "child_interests" to listOf("恐龙", "画画"),
                        "topic_boundaries" to listOf("不要连续追问学校"),
                    ),
                )
            },
            policyWriter = { request ->
                savedRequest = request
                policyResponse(communicationPreferences = request.communicationPreferences)
            },
            dispatcher = Dispatchers.Unconfined,
        )

        val loadedForm = viewModel.uiState.value.form
        assertEquals("8", loadedForm.childAge)
        assertEquals("二年级", loadedForm.childGrade)
        assertEquals("叫小名", loadedForm.childCallPreference)
        assertEquals("恐龙\n画画", loadedForm.childInterestsText)
        assertEquals("不要连续追问学校", loadedForm.topicBoundariesText)

        viewModel.updateChildAge("9")
        viewModel.updateChildInterestsText("跑步比赛\n积木")
        viewModel.updateTopicBoundariesText("学校细节，比赛成绩")
        viewModel.savePolicy()

        val request = savedRequest
        assertNotNull(request)
        requireNotNull(request)
        assertEquals(9, request.communicationPreferences["child_age"])
        assertEquals(listOf("跑步比赛", "积木"), request.communicationPreferences["child_interests"])
        assertEquals(
            listOf("学校细节", "比赛成绩"),
            request.communicationPreferences["topic_boundaries"],
        )
        assertEquals(true, request.communicationPreferences["visible_schedule_deprecated_v0_1"])
    }

    @Test
    fun savePolicyAllowsBlankAge() {
        var savedRequest: ParentPolicyUpdateRequest? = null
        val viewModel = ParentPolicyViewModel(
            policyReader = { policyResponse() },
            policyWriter = { request ->
                savedRequest = request
                policyResponse(communicationPreferences = request.communicationPreferences)
            },
            dispatcher = Dispatchers.Unconfined,
        )

        viewModel.updateChildAge("   ")
        viewModel.savePolicy()

        val request = savedRequest
        assertNotNull(request)
        requireNotNull(request)
        assertEquals("", request.communicationPreferences["child_age"])
        assertNull(viewModel.uiState.value.errorMessage)
    }

    @Test
    fun savePolicyRejectsInvalidAgeWithoutCallingWriter() {
        var saveAttempts = 0
        val viewModel = ParentPolicyViewModel(
            policyReader = { policyResponse() },
            policyWriter = { request ->
                saveAttempts += 1
                policyResponse(communicationPreferences = request.communicationPreferences)
            },
            dispatcher = Dispatchers.Unconfined,
        )

        viewModel.updateChildAge("11")
        viewModel.savePolicy()

        assertEquals(0, saveAttempts)
        assertEquals("年龄请填写 5-10 之间的数字，或先留空。", viewModel.uiState.value.errorMessage)
    }

    @Test
    fun savePolicyPreservesLoadedScheduleAndDoesNotValidateHiddenTimes() {
        val existingSchedule = defaultParentSchedule()
            .withEntryTimes("after_school", "16:05", "17:15")
            .withEntryTimes("homework_time", "18:35", "19:10")
            .withEntryTimes("bedtime", "21:00", "21:20")
        var savedRequest: ParentPolicyUpdateRequest? = null
        val viewModel = ParentPolicyViewModel(
            policyReader = { policyResponse(schedule = existingSchedule) },
            policyWriter = { request ->
                savedRequest = request
                policyResponse(schedule = request.schedule)
            },
            dispatcher = Dispatchers.Unconfined,
        )

        viewModel.updateAfterSchoolStart("not-a-time")
        viewModel.updateHomeworkEnd("also-bad")
        viewModel.updateChildAge("8")
        viewModel.savePolicy()

        val request = savedRequest
        assertNotNull(request)
        requireNotNull(request)
        assertEquals("16:05", request.schedule.entry("after_school")?.start)
        assertEquals("17:15", request.schedule.entry("after_school")?.end)
        assertEquals("18:35", request.schedule.entry("homework_time")?.start)
        assertEquals("19:10", request.schedule.entry("homework_time")?.end)
        assertEquals("21:00", request.schedule.entry("bedtime")?.start)
        assertEquals("21:20", request.schedule.entry("bedtime")?.end)
        assertNull(viewModel.uiState.value.errorMessage)
    }

    @Test
    fun savePolicySubmitsBlankChildNamesAsEmptyValues() {
        var savedRequest: ParentPolicyUpdateRequest? = null
        val viewModel = ParentPolicyViewModel(
            policyReader = {
                policyResponse(
                    childNickname = "豆豆",
                    childDisplayName = "王小明",
                )
            },
            policyWriter = { request ->
                savedRequest = request
                policyResponse(
                    childNickname = request.childNickname,
                    childDisplayName = request.childDisplayName,
                )
            },
            dispatcher = Dispatchers.Unconfined,
        )

        viewModel.updateChildNickname("   ")
        viewModel.updateChildDisplayName("")
        viewModel.savePolicy()

        val request = savedRequest
        assertNotNull(request)
        requireNotNull(request)
        assertEquals("", request.childNickname)
        assertEquals("", request.childDisplayName)
    }
}

private fun policyResponse(
    childNickname: String? = null,
    childDisplayName: String? = null,
    parentMessageRaw: String? = "",
    goals: List<String> = listOf("保留目标"),
    communicationPreferences: Map<String, Any> = mapOf(
        "offer_choices_before_open_questions" to true,
    ),
    schedule: ParentSchedule = defaultParentSchedule(),
): ParentPolicyResponse {
    return ParentPolicyResponse(
        childId = "child_demo_001",
        childNickname = childNickname,
        childDisplayName = childDisplayName,
        parentMessageRaw = parentMessageRaw,
        goals = goals,
        communicationPreferences = communicationPreferences,
        safetyRules = emptyMap(),
        schedule = schedule,
        version = 1,
    )
}
