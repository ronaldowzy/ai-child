package com.childai.companion.data.parent

import org.json.JSONArray
import org.json.JSONObject

data class ParentPolicyResponse(
    val childId: String,
    val childNickname: String?,
    val childDisplayName: String?,
    val parentMessageRaw: String?,
    val goals: List<String>,
    val communicationPreferences: Map<String, Any>,
    val safetyRules: Map<String, Any>,
    val schedule: ParentSchedule,
    val version: Int,
) {
    companion object {
        fun fromJsonString(rawJson: String): ParentPolicyResponse {
            val root = JSONObject(rawJson)
            return ParentPolicyResponse(
                childId = root.getString("child_id"),
                childNickname = root.optNullableString("child_nickname"),
                childDisplayName = root.optNullableString("child_display_name"),
                parentMessageRaw = root.optNullableString("parent_message_raw"),
                goals = root.optJSONArray("goals").toStringList(),
                communicationPreferences = parseNestedMap(root, "communication_preferences"),
                safetyRules = parseNestedMap(root, "safety_rules"),
                schedule = ParentSchedule.fromJson(root.getJSONObject("schedule")),
                version = root.optInt("version", 1),
            )
        }
    }
}

data class ParentPolicyUpdateRequest(
    val childId: String,
    val childNickname: String?,
    val childDisplayName: String?,
    val parentMessageRaw: String?,
    val goals: List<String>,
    val communicationPreferences: Map<String, Any>,
    val schedule: ParentSchedule,
) {
    fun toJsonString(): String {
        return JSONObject()
            .put("child_id", childId)
            .putNullable("child_nickname", childNickname)
            .putNullable("child_display_name", childDisplayName)
            .put("parent_message_raw", parentMessageRaw)
            .put("goals", JSONArray(goals))
            .put("communication_preferences", communicationPreferences.toJsonObject())
            .put("schedule", schedule.toJsonObject())
            .toString()
    }
}

data class ParentSchedule(
    val dailySchedule: List<TimeScheduleEntry>,
) {
    fun entry(period: String): TimeScheduleEntry? {
        return dailySchedule.firstOrNull { it.period == period }
    }

    fun withEntryTimes(period: String, start: String, end: String): ParentSchedule {
        val updatedEntries = dailySchedule.map { entry ->
            if (entry.period == period) {
                entry.copy(start = start, end = end)
            } else {
                entry
            }
        }
        if (updatedEntries.any { it.period == period }) {
            return copy(dailySchedule = updatedEntries)
        }
        return copy(
            dailySchedule = dailySchedule + TimeScheduleEntry(
                period = period,
                start = start,
                end = end,
                goal = defaultGoalForPeriod(period),
                preferredInteractions = emptyList(),
                avoid = emptyList(),
            ),
        )
    }

    fun toJsonObject(): JSONObject {
        return JSONObject()
            .put(
                "daily_schedule",
                JSONArray(dailySchedule.map { it.toJsonObject() }),
            )
    }

    companion object {
        fun fromJson(json: JSONObject): ParentSchedule {
            val entries = json.optJSONArray("daily_schedule").toScheduleEntries()
            return ParentSchedule(dailySchedule = entries)
        }
    }
}

data class TimeScheduleEntry(
    val period: String,
    val start: String,
    val end: String,
    val goal: String,
    val preferredInteractions: List<String>,
    val avoid: List<String>,
) {
    fun toJsonObject(): JSONObject {
        return JSONObject()
            .put("period", period)
            .put("start", start)
            .put("end", end)
            .put("goal", goal)
            .put("preferred_interactions", JSONArray(preferredInteractions))
            .put("avoid", JSONArray(avoid))
    }

    companion object {
        fun fromJson(json: JSONObject): TimeScheduleEntry {
            val period = json.getString("period")
            return TimeScheduleEntry(
                period = period,
                start = json.getString("start"),
                end = json.getString("end"),
                goal = json.optString("goal", defaultGoalForPeriod(period)),
                preferredInteractions = json.optJSONArray(
                    "preferred_interactions",
                ).toStringList(),
                avoid = json.optJSONArray("avoid").toStringList(),
            )
        }
    }
}

fun defaultParentSchedule(): ParentSchedule {
    return ParentSchedule(
        dailySchedule = listOf(
            TimeScheduleEntry(
                period = "after_school",
                start = "15:30",
                end = "18:00",
                goal = "情绪缓冲、学校表达、作业衔接",
                preferredInteractions = listOf("状态选择", "学校小事", "学习卡点"),
                avoid = listOf("立刻连续追问"),
            ),
            TimeScheduleEntry(
                period = "homework_time",
                start = "18:00",
                end = "20:20",
                goal = "作业引导、错题分析、思路训练",
                preferredInteractions = listOf("拍照识题", "分级提示", "复述思路"),
                avoid = listOf("直接给答案", "替孩子完成作业"),
            ),
            TimeScheduleEntry(
                period = "bedtime",
                start = "20:20",
                end = "21:30",
                goal = "低刺激复盘、情绪安定、明日计划",
                preferredInteractions = listOf("三问复盘", "情绪总结", "晚安收尾"),
                avoid = listOf("强刺激话题", "长时间聊天"),
            ),
        ),
    )
}

private fun JSONArray?.toScheduleEntries(): List<TimeScheduleEntry> {
    if (this == null) return defaultParentSchedule().dailySchedule

    return buildList {
        for (index in 0 until length()) {
            add(TimeScheduleEntry.fromJson(getJSONObject(index)))
        }
    }
}

private fun JSONArray?.toStringList(): List<String> {
    if (this == null) return emptyList()

    return buildList {
        for (index in 0 until length()) {
            add(getString(index))
        }
    }
}

private fun JSONObject?.toMap(): Map<String, Any> {
    if (this == null) return emptyMap()

    return buildMap {
        val keyList = keys().asSequence().toList()
        for (key in keyList) {
            val value = opt(key)
            if (value != null && value != JSONObject.NULL) {
                put(key, valueToKotlin(value))
            }
        }
    }
}

private fun JSONObject.optNullableString(name: String): String? {
    if (!has(name) || isNull(name)) return null
    return optString(name).takeIf { it.isNotBlank() }
}

private fun JSONObject.putNullable(name: String, value: String?): JSONObject {
    return put(name, value ?: JSONObject.NULL)
}

private fun Map<String, Any>.toJsonObject(): JSONObject {
    val json = JSONObject()
    forEach { (key, value) ->
        json.put(key, value.toJsonValue())
    }
    return json
}

private fun Any.toJsonValue(): Any {
    return when (this) {
        is Map<*, *> -> {
            val json = JSONObject()
            forEach { (key, value) ->
                if (key is String && value != null) {
                    json.put(key, value.toJsonValue())
                }
            }
            json
        }
        is Iterable<*> -> JSONArray(mapNotNull { item -> item?.toJsonValue() })
        else -> this
    }
}

/**
 * Parse a nested JSON object by re-serializing and re-parsing.
 * Works around an Android org.json bug where JSONObject.get(key) returns null
 * even though toString() shows correct values.
 */
private fun parseNestedMap(root: JSONObject, key: String): Map<String, Any> {
    if (!root.has(key)) return emptyMap()
    val nestedJson = root.optJSONObject(key)
    if (nestedJson == null) return emptyMap()
    // Re-serialize and re-parse to work around get() returning null
    val reparsed = JSONObject(nestedJson.toString())
    val result = mutableMapOf<String, Any>()
    for (k in reparsed.keys()) {
        val value = reparsed.opt(k)
        if (value != null && value != JSONObject.NULL) {
            result[k] = valueToKotlin(value)
        }
    }
    return result
}

private fun valueToKotlin(value: Any): Any {
    return when (value) {
        is JSONObject -> value.toMap()
        is JSONArray -> buildList {
            for (index in 0 until value.length()) {
                add(valueToKotlin(value.get(index)))
            }
        }
        else -> value
    }
}

private fun defaultGoalForPeriod(period: String): String {
    return when (period) {
        "after_school" -> "情绪缓冲、学校表达、作业衔接"
        "homework_time" -> "作业引导、错题分析、思路训练"
        "bedtime" -> "低刺激复盘、情绪安定、明日计划"
        else -> "轻量支持"
    }
}
