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
              "topic_overview": [
                {
                  "topic": "学习求助",
                  "child_intent": "想解决题目卡点",
                  "summary": "今天出现学习求助线索，但不输出逐字聊天记录。",
                  "emotion_tone": "需要低压力分步支持",
                  "parent_bridge": "今晚可以先听孩子说题目在问什么。"
                }
              ],
              "conversation_summary": "今天主要聊了学习求助，父亲可看内容主线，不看原文。",
              "learning_observations": ["孩子在学习求助时需要先确认题意。"],
              "expression_observations": [],
              "emotion_observations": [],
              "safety_alerts": [],
              "suggested_parent_actions": ["请孩子先复述题目在问什么。"],
              "tonight_parent_bridge": "今晚可以轻轻说：如果有题卡住，我们先听你说题目在问什么。如果孩子不想说，就先休息。",
              "avoid_followup": ["不要直接追问最终答案。"],
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
        assertEquals(
            "今晚可以轻轻说：如果有题卡住，我们先听你说题目在问什么。如果孩子不想说，就先休息。",
            report.tonightParentBridge,
        )
        assertEquals(report.tonightParentBridge, report.bridgeText)
        assertEquals("今天主要聊了学习求助，父亲可看内容主线，不看原文。", report.conversationSummary)
        assertEquals(1, report.topicOverview.size)
        assertEquals("学习求助", report.topicOverview.first().topic)
        assertEquals("不要直接追问最终答案。", report.avoidFollowup.first())
        assertEquals(1, report.learningObservations.size)
        assertFalse(report.summary.contains("逐字聊天记录"))
    }

    @Test
    fun parentReportBridgeFallsBackToFirstActionForOldResponses() {
        val report = ParentReport.fromJsonString(
            """
            {
              "child_id": "child_demo_001",
              "date": "2026-05-18",
              "summary": "今天暂无可汇总的结构化会话素材。",
              "learning_observations": [],
              "expression_observations": [],
              "emotion_observations": [],
              "safety_alerts": [],
              "suggested_parent_actions": ["今晚轻轻问一个小细节，不要追问过多。"],
              "generation_status": "model_generated",
              "generated_by": "model",
              "created_at": "2026-05-18T00:00:00Z"
            }
            """.trimIndent(),
        )

        assertEquals(null, report.tonightParentBridge)
        assertEquals("今晚轻轻问一个小细节，不要追问过多。", report.bridgeText)
    }
}
