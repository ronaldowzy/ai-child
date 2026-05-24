package com.childai.companion.data.parent

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ParentPolicyDtosTest {
    @Test
    fun parentPolicyUpdateSerializesBackendScheduleShape() {
        val request = ParentPolicyUpdateRequest(
            childId = "child_demo_001",
            childNickname = "豆豆",
            childDisplayName = "王小明",
            parentMessageRaw = "小名叫豆豆，最近喜欢恐龙。",
            goals = listOf("数学题先复述题意"),
            communicationPreferences = mapOf(
                "offer_choices_before_open_questions" to true,
                "do_not_force_expression" to true,
                "ask_thinking_before_learning_answer" to true,
                "avoid_labels" to true,
                "child_age" to 8,
                "child_grade" to "二年级",
                "child_call_preference" to "叫小名",
                "child_interests" to listOf("恐龙", "画画"),
                "topic_boundaries" to listOf("不要连续追问学校"),
            ),
            schedule = defaultParentSchedule()
                .withEntryTimes("after_school", "15:30", "18:00")
                .withEntryTimes("bedtime", "20:20", "21:30"),
        )

        val json = request.toJsonString()

        assertTrue(json.contains("\"daily_schedule\""))
        assertTrue(json.contains("\"child_nickname\":\"豆豆\""))
        assertTrue(json.contains("\"child_display_name\":\"王小明\""))
        assertTrue(json.contains("\"parent_message_raw\":\"小名叫豆豆"))
        assertTrue(json.contains("\"child_age\":8"))
        assertTrue(json.contains("\"child_interests\""))
        assertTrue(json.contains("\"topic_boundaries\""))
        assertTrue(json.contains("\"period\":\"after_school\""))
        assertTrue(json.contains("\"period\":\"bedtime\""))
        assertFalse(json.contains("\"safety_rules\""))
    }

    @Test
    fun parentPolicyResponseParsesGoalsAndSchedule() {
        val response = ParentPolicyResponse.fromJsonString(
            """
            {
              "child_id": "child_demo_001",
              "child_nickname": "豆豆",
              "child_display_name": "王小明",
              "parent_message_raw": "小名叫豆豆，最近喜欢恐龙。",
              "goals": ["数学题先复述题意"],
              "communication_preferences": {
                "offer_choices_before_open_questions": true,
                "child_age": 8,
                "child_grade": "二年级",
                "child_call_preference": "叫小名",
                "child_interests": ["恐龙", "画画"],
                "topic_boundaries": ["不要连续追问学校"]
              },
              "safety_rules": {
                "homework_answer_policy": "scaffold_not_direct_answer"
              },
              "schedule": {
                "daily_schedule": [
                  {
                    "period": "after_school",
                    "start": "15:30",
                    "end": "18:00",
                    "goal": "情绪缓冲",
                    "preferred_interactions": ["状态选择"],
                    "avoid": ["连续追问"]
                  }
                ]
              },
              "version": 2,
              "created_at": "2026-05-18T00:00:00Z",
              "updated_at": "2026-05-18T00:00:00Z"
            }
            """.trimIndent(),
        )

        assertEquals(listOf("数学题先复述题意"), response.goals)
        assertEquals("豆豆", response.childNickname)
        assertEquals("王小明", response.childDisplayName)
        assertEquals("小名叫豆豆，最近喜欢恐龙。", response.parentMessageRaw)
        assertEquals("15:30", response.schedule.entry("after_school")?.start)
        assertEquals(2, response.version)
    }

    @Test
    fun parentPolicyResponseHandlesMissingChildNames() {
        val response = ParentPolicyResponse.fromJsonString(
            """
            {
              "child_id": "child_demo_001",
              "parent_message_raw": null,
              "goals": [],
              "communication_preferences": {},
              "safety_rules": {},
              "schedule": {
                "daily_schedule": []
              },
              "version": 1
            }
            """.trimIndent(),
        )

        assertEquals(null, response.childNickname)
        assertEquals(null, response.childDisplayName)
        assertEquals("", response.parentMessageRaw.orEmpty())
    }

    @Test
    fun parentPolicyUpdateSerializesNullChildNames() {
        val request = ParentPolicyUpdateRequest(
            childId = "child_demo_001",
            childNickname = null,
            childDisplayName = null,
            parentMessageRaw = null,
            goals = emptyList(),
            communicationPreferences = emptyMap(),
            schedule = defaultParentSchedule(),
        )

        val json = org.json.JSONObject(request.toJsonString())

        assertTrue(json.has("child_nickname"))
        assertTrue(json.isNull("child_nickname"))
        assertTrue(json.has("child_display_name"))
        assertTrue(json.isNull("child_display_name"))
    }
}
