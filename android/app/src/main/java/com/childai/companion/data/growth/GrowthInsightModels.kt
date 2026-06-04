package com.childai.companion.data.growth

const val GROWTH_INSIGHT_TYPE_RECENT_DISCOVERY_SUMMARY = "recent_discovery_summary"
const val GROWTH_INSIGHT_TYPE_RECALLED_INTEREST = "recalled_interest"

private const val GROWTH_INSIGHT_WINDOW_MS = 7L * 24L * 60L * 60L * 1000L
private const val GROWTH_INSIGHT_NAME_LIMIT = 3
private const val GROWTH_INSIGHT_RECALLED_LIMIT = 3

data class GrowthInsight(
    val id: String,
    val childId: String,
    val title: String,
    val summary: String,
    val relatedEventIds: List<String>,
    val createdAt: Long,
    val type: String,
)

fun buildGrowthInsights(
    childId: String,
    events: List<GrowthEvent>,
    nowMillis: Long,
): List<GrowthInsight> {
    if (childId.isBlank()) return emptyList()
    val earliestCreatedAt = nowMillis - GROWTH_INSIGHT_WINDOW_MS
    val recentEvents = events
        .asSequence()
        .filter {
            it.childId == childId &&
                !it.isDeleted &&
                it.source == GROWTH_EVENT_SOURCE_XIAOZHANTAI &&
                it.createdAt >= earliestCreatedAt &&
                it.type in setOf(
                    GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED,
                    GROWTH_EVENT_TYPE_SHOWCASE_ITEM_RECALLED,
                )
        }
        .sortedByDescending { it.createdAt }
        .toList()
    if (recentEvents.isEmpty()) return emptyList()

    return buildList {
        buildRecentDiscoverySummary(childId, recentEvents)?.let(::add)
        addAll(buildRecalledInterestInsights(childId, recentEvents))
    }.sortedByDescending { it.createdAt }
}

private fun buildRecentDiscoverySummary(
    childId: String,
    recentEvents: List<GrowthEvent>,
): GrowthInsight? {
    val savedEvents = recentEvents
        .filter { it.type == GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED }
        .sortedByDescending { it.createdAt }
    if (savedEvents.isEmpty()) return null

    val names = savedEvents
        .mapNotNull { it.showcaseNameFromEvent() }
        .distinct()
        .take(GROWTH_INSIGHT_NAME_LIMIT)
    val count = savedEvents.size
    val summary = if (names.isEmpty()) {
        "孩子最近留下了 $count 个小发现。"
    } else {
        "孩子最近留下了 $count 个小发现，比如${names.joinToString(separator = "") { "「$it」" }}。"
    }
    val createdAt = savedEvents.maxOf { it.createdAt }
    return GrowthInsight(
        id = "growth_insight_recent_discovery_summary_${childId}_$createdAt",
        childId = childId,
        title = "最近留下的小发现",
        summary = summary,
        relatedEventIds = savedEvents.map { it.id },
        createdAt = createdAt,
        type = GROWTH_INSIGHT_TYPE_RECENT_DISCOVERY_SUMMARY,
    )
}

private fun buildRecalledInterestInsights(
    childId: String,
    recentEvents: List<GrowthEvent>,
): List<GrowthInsight> {
    return recentEvents
        .filter { !it.relatedItemId.isNullOrBlank() }
        .groupBy { it.relatedItemId.orEmpty() }
        .values
        .asSequence()
        .mapNotNull { eventsForItem ->
            val savedCount = eventsForItem.count { it.type == GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED }
            val recalledEvents = eventsForItem
                .filter { it.type == GROWTH_EVENT_TYPE_SHOWCASE_ITEM_RECALLED }
                .sortedByDescending { it.createdAt }
            val shouldShow = recalledEvents.size >= 2 || (savedCount > 0 && recalledEvents.isNotEmpty())
            if (!shouldShow) return@mapNotNull null
            val latestEvent = recalledEvents.firstOrNull() ?: eventsForItem.maxBy { it.createdAt }
            val name = eventsForItem
                .sortedByDescending { it.createdAt }
                .mapNotNull { it.showcaseNameFromEvent() }
                .firstOrNull()
                ?: "这个小发现"
            GrowthInsight(
                id = "growth_insight_recalled_interest_${childId}_${latestEvent.relatedItemId}_${latestEvent.createdAt}",
                childId = childId,
                title = "孩子又想起了一个小发现",
                summary = "孩子最近又和小白狐聊起了「$name」。",
                relatedEventIds = eventsForItem
                    .sortedByDescending { it.createdAt }
                    .map { it.id },
                createdAt = latestEvent.createdAt,
                type = GROWTH_INSIGHT_TYPE_RECALLED_INTEREST,
            )
        }
        .sortedByDescending { it.createdAt }
        .take(GROWTH_INSIGHT_RECALLED_LIMIT)
        .toList()
}

private fun GrowthEvent.showcaseNameFromEvent(): String? {
    val quotedName = Regex("「([^」]{1,24})」")
        .find(summary)
        ?.groupValues
        ?.getOrNull(1)
        ?.trim()
    return quotedName?.takeIf { it.isNotBlank() }
}
