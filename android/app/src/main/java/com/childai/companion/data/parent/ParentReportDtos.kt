package com.childai.companion.data.parent

import org.json.JSONObject

data class ParentReportTopicOverview(
    val topic: String,
    val childIntent: String,
    val summary: String,
    val emotionTone: String,
    val parentBridge: String,
)

data class ParentReport(
    val childId: String,
    val date: String,
    val summary: String,
    val topicOverview: List<ParentReportTopicOverview> = emptyList(),
    val conversationSummary: String? = null,
    val learningObservations: List<String>,
    val expressionObservations: List<String>,
    val emotionObservations: List<String>,
    val safetyAlerts: List<String>,
    val suggestedParentActions: List<String>,
    val tonightParentBridge: String? = null,
    val avoidFollowup: List<String> = emptyList(),
    val generationStatus: String = "legacy",
    val generatedBy: String = "legacy",
    val generationErrorCode: String? = null,
) {
    val isGeneratedSuccessfully: Boolean
        get() = generationStatus == "model_generated"

    val bridgeText: String
        get() = tonightParentBridge
            ?: suggestedParentActions.firstOrNull { it.isNotBlank() }
            ?: "今晚先轻松陪孩子做一件日常小事，不追问孩子今天在小白狐里聊了什么。"

    companion object {
        fun fromJsonString(rawJson: String): ParentReport {
            val root = JSONObject(rawJson)
            return ParentReport(
                childId = root.getString("child_id"),
                date = root.getString("date"),
                summary = root.getString("summary"),
                topicOverview = root.optJSONArray("topic_overview")
                    .toParentReportTopicOverviewList(),
                conversationSummary = root.optNullableString("conversation_summary"),
                learningObservations = root.optJSONArray(
                    "learning_observations",
                ).toParentReportStringList(),
                expressionObservations = root.optJSONArray(
                    "expression_observations",
                ).toParentReportStringList(),
                emotionObservations = root.optJSONArray(
                    "emotion_observations",
                ).toParentReportStringList(),
                safetyAlerts = root.optJSONArray("safety_alerts")
                    .toParentReportStringList(),
                suggestedParentActions = root.optJSONArray(
                    "suggested_parent_actions",
                ).toParentReportStringList(),
                tonightParentBridge = root.optNullableString("tonight_parent_bridge"),
                avoidFollowup = root.optJSONArray("avoid_followup")
                    .toParentReportStringList(),
                generationStatus = root.optString("generation_status", "legacy"),
                generatedBy = root.optString("generated_by", "legacy"),
                generationErrorCode = root.optNullableString(
                    "generation_error_code",
                ),
            )
        }
    }
}

private fun org.json.JSONArray?.toParentReportTopicOverviewList(): List<ParentReportTopicOverview> {
    if (this == null) return emptyList()

    return buildList {
        for (index in 0 until length()) {
            val item = optJSONObject(index) ?: continue
            val topic = item.optString("topic").takeIf { it.isNotBlank() } ?: continue
            add(
                ParentReportTopicOverview(
                    topic = topic,
                    childIntent = item.optString("child_intent"),
                    summary = item.optString("summary"),
                    emotionTone = item.optString("emotion_tone"),
                    parentBridge = item.optString("parent_bridge"),
                ),
            )
        }
    }
}

private fun JSONObject.optNullableString(name: String): String? {
    if (!has(name) || isNull(name)) return null
    return optString(name).takeIf { it.isNotBlank() }
}

private fun org.json.JSONArray?.toParentReportStringList(): List<String> {
    if (this == null) return emptyList()

    return buildList {
        for (index in 0 until length()) {
            add(getString(index))
        }
    }
}
