package com.childai.companion.ui.parent

import com.childai.companion.data.growth.GROWTH_EVENT_SHOWCASE_TITLE
import com.childai.companion.data.growth.GROWTH_EVENT_SHOWCASE_RECALL_TITLE
import com.childai.companion.data.growth.GROWTH_EVENT_SOURCE_XIAOZHANTAI
import com.childai.companion.data.growth.GROWTH_EVENT_TYPE_SHOWCASE_ITEM_RECALLED
import com.childai.companion.data.growth.GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED
import com.childai.companion.data.growth.GrowthEvent
import com.childai.companion.data.growth.GrowthEventRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class ParentReportViewModelTest {
    private val now = 1760000000000L

    @Before
    fun setUp() {
        Dispatchers.setMain(Dispatchers.Unconfined)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun readsGrowthEventsForParentReport() {
        val viewModel = viewModel(
            events = listOf(
                growthEvent(
                    id = "growth_event_001",
                    summary = "孩子把「小石头」放进了小展台。",
                    createdAt = now - 1_000L,
                ),
            ),
        )

        val discoveries = viewModel.uiState.value.recentDiscoveries

        assertEquals(1, discoveries.size)
        assertEquals("growth_event_001", discoveries.single().id)
        assertEquals("留下了一个小发现", discoveries.single().title)
        assertEquals("孩子把「小石头」放进了小展台。", discoveries.single().summary)
    }

    @Test
    fun onlyShowsXiaozhantaiShowcaseEvents() {
        val viewModel = viewModel(
            events = listOf(
                growthEvent(id = "showcase", createdAt = now - 1_000L),
                growthEvent(
                    id = "recalled",
                    type = GROWTH_EVENT_TYPE_SHOWCASE_ITEM_RECALLED,
                    title = GROWTH_EVENT_SHOWCASE_RECALL_TITLE,
                    summary = "孩子又和小白狐聊起了「小石头」。",
                    createdAt = now - 2_000L,
                ),
                growthEvent(id = "other_type", type = "voice_chat", createdAt = now - 3_000L),
                growthEvent(id = "other_source", source = "other", createdAt = now - 4_000L),
                growthEvent(id = "deleted", isDeleted = true, createdAt = now - 5_000L),
            ),
        )

        assertEquals(
            listOf("showcase", "recalled"),
            viewModel.uiState.value.recentDiscoveries.map { it.id },
        )
    }

    @Test
    fun sortsRecentDiscoveriesByCreatedAtDescendingAndLimitsToTen() {
        val events = (0 until 12).map { index ->
            growthEvent(
                id = "event_$index",
                createdAt = now - index * 1_000L,
            )
        }

        val discoveries = viewModel(events = events).uiState.value.recentDiscoveries

        assertEquals(10, discoveries.size)
        assertEquals("event_0", discoveries.first().id)
        assertEquals("event_9", discoveries.last().id)
    }

    @Test
    fun sortsMixedShowcaseEventsByCreatedAtDescendingAndLimitsToTen() {
        val events = (0 until 12).map { index ->
            growthEvent(
                id = "event_$index",
                type = if (index % 2 == 0) {
                    GROWTH_EVENT_TYPE_SHOWCASE_ITEM_RECALLED
                } else {
                    GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED
                },
                title = if (index % 2 == 0) {
                    GROWTH_EVENT_SHOWCASE_RECALL_TITLE
                } else {
                    GROWTH_EVENT_SHOWCASE_TITLE
                },
                summary = if (index % 2 == 0) {
                    "孩子又和小白狐聊起了「小石头」。"
                } else {
                    "孩子把「小石头」放进了小展台。"
                },
                createdAt = now - index * 1_000L,
            )
        }

        val discoveries = viewModel(events = events).uiState.value.recentDiscoveries

        assertEquals(10, discoveries.size)
        assertEquals("event_0", discoveries.first().id)
        assertEquals(GROWTH_EVENT_SHOWCASE_RECALL_TITLE, discoveries.first().title)
        assertEquals("event_9", discoveries.last().id)
    }

    @Test
    fun emptyEventsKeepGentleEmptyStateAvailable() {
        val viewModel = viewModel(events = emptyList())

        assertTrue(viewModel.uiState.value.recentDiscoveries.isEmpty())
        assertEquals("这几天还没有新的小发现。", PARENT_REPORT_NO_RECENT_DISCOVERIES_MESSAGE)
    }

    @Test
    fun nullPhotoUriDoesNotBreakDiscoveryMapping() {
        val viewModel = viewModel(
            events = listOf(
                growthEvent(
                    id = "no_photo",
                    relatedPhotoUri = null,
                    createdAt = now - 1_000L,
                ),
            ),
        )

        val discovery = viewModel.uiState.value.recentDiscoveries.single()

        assertEquals("no_photo", discovery.id)
        assertNull(discovery.relatedPhotoUri)
    }

    @Test
    fun filtersEventsOutsideSevenDayWindow() {
        val viewModel = viewModel(
            events = listOf(
                growthEvent(id = "recent", createdAt = now - 2_000L),
                growthEvent(
                    id = "old",
                    createdAt = now - PARENT_REPORT_GROWTH_EVENT_WINDOW_MS - 1_000L,
                ),
            ),
        )

        assertEquals(
            listOf("recent"),
            viewModel.uiState.value.recentDiscoveries.map { it.id },
        )
    }

    private fun viewModel(events: List<GrowthEvent>): ParentReportViewModel {
        return ParentReportViewModel(
            growthEventRepository = GrowthEventRepository(initialEvents = events),
            childId = "child_001",
            nowMillis = { now },
            requestReportOnInit = false,
        )
    }

    private fun growthEvent(
        id: String = "growth_event_001",
        childId: String = "child_001",
        type: String = GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED,
        title: String = GROWTH_EVENT_SHOWCASE_TITLE,
        source: String = GROWTH_EVENT_SOURCE_XIAOZHANTAI,
        summary: String = "孩子把「小石头」放进了小展台。",
        relatedPhotoUri: String? = "/tmp/photo.jpg",
        createdAt: Long = now - 1_000L,
        isDeleted: Boolean = false,
    ): GrowthEvent {
        return GrowthEvent(
            id = id,
            childId = childId,
            type = type,
            title = title,
            summary = summary,
            relatedItemId = "stand_item_001",
            relatedPhotoUri = relatedPhotoUri,
            createdAt = createdAt,
            source = source,
            isDeleted = isDeleted,
        )
    }
}
