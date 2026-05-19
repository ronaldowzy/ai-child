package com.childai.companion.data.parent

import org.json.JSONObject

data class ParentReport(
    val childId: String,
    val date: String,
    val summary: String,
    val learningObservations: List<String>,
    val expressionObservations: List<String>,
    val emotionObservations: List<String>,
    val safetyAlerts: List<String>,
    val suggestedParentActions: List<String>,
) {
    companion object {
        fun fromJsonString(rawJson: String): ParentReport {
            val root = JSONObject(rawJson)
            return ParentReport(
                childId = root.getString("child_id"),
                date = root.getString("date"),
                summary = root.getString("summary"),
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
            )
        }
    }
}

private fun org.json.JSONArray?.toParentReportStringList(): List<String> {
    if (this == null) return emptyList()

    return buildList {
        for (index in 0 until length()) {
            add(getString(index))
        }
    }
}
