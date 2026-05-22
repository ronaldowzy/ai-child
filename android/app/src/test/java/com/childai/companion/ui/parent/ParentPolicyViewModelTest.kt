package com.childai.companion.ui.parent

import com.childai.companion.data.parent.ParentPolicyResponse
import com.childai.companion.data.parent.ParentSchedule
import com.childai.companion.data.parent.ParentPolicyUpdateRequest
import com.childai.companion.data.parent.defaultParentSchedule
import kotlinx.coroutines.Dispatchers
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
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
