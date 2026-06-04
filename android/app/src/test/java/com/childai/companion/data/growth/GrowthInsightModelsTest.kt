package com.childai.companion.data.growth

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class GrowthInsightModelsTest {
    private val now = 1760000000000L

    @Test
    fun recentSavedEventsBuildDiscoverySummary() {
        val insights = buildGrowthInsights(
            childId = "child_001",
            events = listOf(
                savedEvent(id = "saved_1", name = "小石头", createdAt = now - 1_000L),
                savedEvent(id = "saved_2", name = "小云朵", createdAt = now - 2_000L),
                savedEvent(id = "saved_3", name = "小纸船", createdAt = now - 3_000L),
            ),
            nowMillis = now,
        )

        val summary = insights.first { it.type == GROWTH_INSIGHT_TYPE_RECENT_DISCOVERY_SUMMARY }
        assertEquals("最近留下的小发现", summary.title)
        assertEquals(
            "孩子最近留下了 3 个小发现，比如「小石头」「小云朵」「小纸船」。",
            summary.summary,
        )
        assertEquals(listOf("saved_1", "saved_2", "saved_3"), summary.relatedEventIds)
    }

    @Test
    fun eventsOlderThanSevenDaysAreIgnored() {
        val insights = buildGrowthInsights(
            childId = "child_001",
            events = listOf(
                savedEvent(
                    id = "old_saved",
                    name = "小石头",
                    createdAt = now - 7L * 24L * 60L * 60L * 1000L - 1_000L,
                ),
            ),
            nowMillis = now,
        )

        assertTrue(insights.isEmpty())
    }

    @Test
    fun savedThenRecalledSameItemBuildsRecalledInterest() {
        val insights = buildGrowthInsights(
            childId = "child_001",
            events = listOf(
                savedEvent(
                    id = "saved_1",
                    itemId = "stand_item_001",
                    name = "小石头",
                    createdAt = now - 3_000L,
                ),
                recalledEvent(
                    id = "recalled_1",
                    itemId = "stand_item_001",
                    name = "小石头",
                    createdAt = now - 1_000L,
                ),
            ),
            nowMillis = now,
        )

        val recalled = insights.first { it.type == GROWTH_INSIGHT_TYPE_RECALLED_INTEREST }
        assertEquals("孩子又想起了一个小发现", recalled.title)
        assertEquals("孩子最近又和小白狐聊起了「小石头」。", recalled.summary)
        assertEquals(listOf("recalled_1", "saved_1"), recalled.relatedEventIds)
    }

    @Test
    fun repeatedRecallSameItemBuildsRecalledInterest() {
        val insights = buildGrowthInsights(
            childId = "child_001",
            events = listOf(
                recalledEvent(
                    id = "recalled_1",
                    itemId = "stand_item_001",
                    name = "小石头",
                    createdAt = now - 2_000L,
                ),
                recalledEvent(
                    id = "recalled_2",
                    itemId = "stand_item_001",
                    name = "小石头",
                    createdAt = now - 1_000L,
                ),
            ),
            nowMillis = now,
        )

        assertTrue(insights.any { it.type == GROWTH_INSIGHT_TYPE_RECALLED_INTEREST })
    }

    @Test
    fun noEventsBuildNoInsights() {
        assertTrue(
            buildGrowthInsights(
                childId = "child_001",
                events = emptyList(),
                nowMillis = now,
            ).isEmpty(),
        )
    }

    @Test
    fun insightCopyAvoidsRewardOrScoreLanguage() {
        val forbidden = listOf("分析结果", "能力评估", "兴趣诊断", "排名", "优秀", "落后", "任务完成", "奖励", "成就", "解锁")
        val insights = buildGrowthInsights(
            childId = "child_001",
            events = listOf(
                savedEvent(id = "saved_1", name = "小石头", createdAt = now - 2_000L),
                recalledEvent(id = "recalled_1", name = "小石头", createdAt = now - 1_000L),
            ),
            nowMillis = now,
        )
        val combinedCopy = insights.joinToString(separator = "\n") { "${it.title}\n${it.summary}" }

        assertTrue(forbidden.none { combinedCopy.contains(it) })
    }

    private fun savedEvent(
        id: String,
        itemId: String = id,
        name: String,
        createdAt: Long,
    ): GrowthEvent {
        return growthEvent(
            id = id,
            type = GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED,
            title = GROWTH_EVENT_SHOWCASE_TITLE,
            summary = "孩子把「$name」放进了小展台。",
            relatedItemId = itemId,
            createdAt = createdAt,
        )
    }

    private fun recalledEvent(
        id: String,
        itemId: String = "stand_item_001",
        name: String,
        createdAt: Long,
    ): GrowthEvent {
        return growthEvent(
            id = id,
            type = GROWTH_EVENT_TYPE_SHOWCASE_ITEM_RECALLED,
            title = GROWTH_EVENT_SHOWCASE_RECALL_TITLE,
            summary = "孩子又和小白狐聊起了「$name」。",
            relatedItemId = itemId,
            createdAt = createdAt,
        )
    }

    private fun growthEvent(
        id: String,
        type: String,
        title: String,
        summary: String,
        relatedItemId: String?,
        createdAt: Long,
    ): GrowthEvent {
        return GrowthEvent(
            id = id,
            childId = "child_001",
            type = type,
            title = title,
            summary = summary,
            relatedItemId = relatedItemId,
            relatedPhotoUri = "/tmp/photo.jpg",
            createdAt = createdAt,
            source = GROWTH_EVENT_SOURCE_XIAOZHANTAI,
        )
    }
}
