package com.childai.companion.data.parent

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class ParentReportDtosTest {
    @Test
    fun parentReportDoesNotRequireTranscriptFields() {
        val report = ParentReport.fromJsonString(
            """
            {
              "child_id": "child_demo_001",
              "date": "2026-05-18",
              "summary": "今天记录了结构化观察，重点集中在学习支持。",
              "learning_observations": ["孩子在学习求助时需要先确认题意。"],
              "expression_observations": [],
              "emotion_observations": [],
              "safety_alerts": [],
              "suggested_parent_actions": ["请孩子先复述题目在问什么。"],
              "generation_status": "model_generated",
              "generated_by": "model",
              "generation_error_code": null,
              "created_at": "2026-05-18T00:00:00Z"
            }
            """.trimIndent(),
        )

        assertEquals("2026-05-18", report.date)
        assertEquals("model_generated", report.generationStatus)
        assertEquals("model", report.generatedBy)
        assertEquals(null, report.generationErrorCode)
        assertEquals(1, report.learningObservations.size)
        assertFalse(report.summary.contains("逐字聊天记录"))
    }
}
