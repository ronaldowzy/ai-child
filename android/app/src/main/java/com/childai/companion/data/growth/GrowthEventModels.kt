package com.childai.companion.data.growth

import org.json.JSONObject

const val GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED = "showcase_item_saved"
const val GROWTH_EVENT_SOURCE_XIAOZHANTAI = "xiaozhantai"
const val GROWTH_EVENT_SHOWCASE_TITLE = "留下了一个小发现"

data class GrowthEvent(
    val id: String,
    val childId: String,
    val type: String,
    val title: String,
    val summary: String,
    val relatedItemId: String?,
    val relatedPhotoUri: String?,
    val createdAt: Long,
    val source: String,
    val isDeleted: Boolean = false,
)

fun GrowthEvent.isVisibleGrowthEvent(): Boolean {
    return !isDeleted &&
        id.isNotBlank() &&
        childId.isNotBlank() &&
        type.isNotBlank() &&
        title.isNotBlank() &&
        summary.isNotBlank() &&
        source.isNotBlank()
}

fun visibleGrowthEvents(events: List<GrowthEvent>): List<GrowthEvent> {
    return events
        .filter { it.isVisibleGrowthEvent() }
        .sortedByDescending { it.createdAt }
}

fun showcaseItemSavedGrowthSummary(
    name: String?,
    foxQuote: String?,
): String {
    val compactName = name
        ?.replace(Regex("[\\r\\n\\t]+"), " ")
        ?.replace(Regex("\\s+"), " ")
        ?.trim()
        .orEmpty()
    val compactQuote = foxQuote
        ?.lineSequence()
        ?.map { it.trim() }
        ?.firstOrNull { it.isNotBlank() }
        .orEmpty()
        .take(80)

    if (compactName.isBlank()) {
        return "孩子把一个小发现放进了小展台。"
    }
    return if (compactQuote.isBlank()) {
        "孩子把「${compactName.take(24)}」放进了小展台。"
    } else {
        "孩子把「${compactName.take(24)}」放进了小展台。小白狐当时说：$compactQuote"
    }
}

internal fun GrowthEvent.toJson(): JSONObject {
    return JSONObject()
        .put("id", id)
        .put("childId", childId)
        .put("type", type)
        .put("title", title)
        .put("summary", summary)
        .put("relatedItemId", relatedItemId)
        .put("relatedPhotoUri", relatedPhotoUri)
        .put("createdAt", createdAt)
        .put("source", source)
        .put("isDeleted", isDeleted)
}

internal fun growthEventFromJson(json: JSONObject): GrowthEvent? {
    val id = json.optString("id").takeIf { it.isNotBlank() } ?: return null
    val childId = json.optString("childId").takeIf { it.isNotBlank() } ?: return null
    val type = json.optString("type").takeIf { it.isNotBlank() } ?: return null
    val source = json.optString("source").takeIf { it.isNotBlank() } ?: return null
    val title = json.optString("title").ifBlank { GROWTH_EVENT_SHOWCASE_TITLE }
    val summary = json.optString("summary").takeIf { it.isNotBlank() } ?: return null
    return GrowthEvent(
        id = id,
        childId = childId,
        type = type,
        title = title,
        summary = summary,
        relatedItemId = json.optNullableString("relatedItemId"),
        relatedPhotoUri = json.optNullableString("relatedPhotoUri"),
        createdAt = json.optLong("createdAt", 0L),
        source = source,
        isDeleted = json.optBoolean("isDeleted", false),
    )
}

private fun JSONObject.optNullableString(name: String): String? {
    if (!has(name) || isNull(name)) return null
    return optString(name).takeIf { it.isNotBlank() }
}
