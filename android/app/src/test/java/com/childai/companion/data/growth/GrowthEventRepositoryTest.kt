package com.childai.companion.data.growth

import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class GrowthEventRepositoryTest {
    @get:Rule
    val temporaryFolder = TemporaryFolder()

    @Test
    fun visibleEventsAreNewestFirstAndChildScoped() {
        val older = growthEvent(
            id = "older",
            childId = "child_001",
            createdAt = 100L,
        )
        val newer = older.copy(id = "newer", createdAt = 300L)
        val otherChild = older.copy(id = "other", childId = "child_002", createdAt = 500L)

        val result = visibleGrowthEvents(listOf(older, newer, otherChild))
            .filter { it.childId == "child_001" }

        assertEquals(listOf(newer, older), result)
        assertTrue(newer.isVisibleGrowthEvent())
        assertFalse(newer.copy(isDeleted = true).isVisibleGrowthEvent())
    }

    @Test
    fun showcaseSummaryUsesGentleFallbacks() {
        assertEquals(
            "孩子把「小石头」放进了小展台。小白狐当时说：它看起来像一颗安静的小星球。",
            showcaseItemSavedGrowthSummary("小石头", "它看起来像一颗安静的小星球。"),
        )
        assertEquals(
            "孩子把「小石头」放进了小展台。",
            showcaseItemSavedGrowthSummary("小石头", ""),
        )
        assertEquals(
            "孩子把一个小发现放进了小展台。",
            showcaseItemSavedGrowthSummary("", ""),
        )
    }

    @Test
    fun localRepositoryRestoresEventsAfterRestart() = runTest {
        val root = temporaryFolder.newFolder("growth_events")
        val repository = LocalGrowthEventRepository(root)
        val event = growthEvent(
            id = "growth_event_001",
            childId = "child_001",
            createdAt = 1760000000000L,
        )

        repository.append(event)

        val restartedRepository = LocalGrowthEventRepository(root)
        val restored = restartedRepository.observeEvents("child_001").first().single()

        assertEquals(event.id, restored.id)
        assertEquals(event.relatedItemId, restored.relatedItemId)
        assertEquals(event.relatedPhotoUri, restored.relatedPhotoUri)
        assertEquals(event.summary, restored.summary)
    }

    @Test
    fun softDeleteHidesEventFromObserveEvents() = runTest {
        val repository = LocalGrowthEventRepository(
            temporaryFolder.newFolder("growth_events_delete"),
        )
        val event = growthEvent(id = "growth_event_delete", childId = "child_001")

        repository.append(event)
        repository.softDelete("child_001", event.id)

        assertTrue(repository.observeEvents("child_001").first().isEmpty())
    }

    private fun growthEvent(
        id: String = "growth_event_001",
        childId: String = "child_001",
        createdAt: Long = 1760000000000L,
    ): GrowthEvent {
        return GrowthEvent(
            id = id,
            childId = childId,
            type = GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED,
            title = GROWTH_EVENT_SHOWCASE_TITLE,
            summary = "孩子把「小石头」放进了小展台。",
            relatedItemId = "stand_item_001",
            relatedPhotoUri = "/tmp/photo.jpg",
            createdAt = createdAt,
            source = GROWTH_EVENT_SOURCE_XIAOZHANTAI,
        )
    }
}
