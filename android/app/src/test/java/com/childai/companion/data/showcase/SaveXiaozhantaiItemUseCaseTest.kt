package com.childai.companion.data.showcase

import com.childai.companion.data.growth.GROWTH_EVENT_SHOWCASE_TITLE
import com.childai.companion.data.growth.GROWTH_EVENT_SOURCE_XIAOZHANTAI
import com.childai.companion.data.growth.GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED
import com.childai.companion.data.growth.LocalGrowthEventRepository
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class SaveXiaozhantaiItemUseCaseTest {
    @get:Rule
    val temporaryFolder = TemporaryFolder()

    @Test
    fun saveCapturedPhotoRecordsGrowthEventWithRelatedItemAndPhoto() = runTest {
        val xiaozhantaiRepository = LocalXiaozhantaiRepository(
            rootDirectory = temporaryFolder.newFolder("xiaozhantai"),
            clock = { 1760000000000L },
        )
        val growthEventRepository = LocalGrowthEventRepository(
            temporaryFolder.newFolder("growth_events"),
        )
        val useCase = SaveXiaozhantaiItemUseCase(
            xiaozhantaiRepository = xiaozhantaiRepository,
            growthEventRepository = growthEventRepository,
        )

        val item = useCase.saveCapturedPhoto(
            XiaozhantaiSaveRequest(
                childId = "child_001",
                photoBytes = byteArrayOf(1, 2, 3),
                name = "小石头",
                foxQuote = "它看起来像一颗安静的小星球。",
            ),
        )
        val event = growthEventRepository.observeEvents("child_001").first().single()

        assertEquals("growth_event_${item.id}", event.id)
        assertEquals("child_001", event.childId)
        assertEquals(GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED, event.type)
        assertEquals(GROWTH_EVENT_SHOWCASE_TITLE, event.title)
        assertEquals(GROWTH_EVENT_SOURCE_XIAOZHANTAI, event.source)
        assertEquals(item.id, event.relatedItemId)
        assertEquals(item.photoUri, event.relatedPhotoUri)
        assertEquals(item.createdAt, event.createdAt)
        assertEquals(
            "孩子把「小石头」放进了小展台。小白狐当时说：它看起来像一颗安静的小星球。",
            event.summary,
        )
        assertNotNull(xiaozhantaiRepository.itemById("child_001", item.id))
    }

    @Test
    fun saveCapturedPhotoRecordsFallbackGrowthSummaryForBlankNameAndQuote() = runTest {
        val growthEventRepository = LocalGrowthEventRepository(
            temporaryFolder.newFolder("growth_events_blank"),
        )
        val useCase = SaveXiaozhantaiItemUseCase(
            xiaozhantaiRepository = LocalXiaozhantaiRepository(
                rootDirectory = temporaryFolder.newFolder("xiaozhantai_blank"),
                clock = { 1760000000000L },
            ),
            growthEventRepository = growthEventRepository,
        )

        useCase.saveCapturedPhoto(
            XiaozhantaiSaveRequest(
                childId = "child_002",
                photoBytes = byteArrayOf(4, 5, 6),
                name = "",
                foxQuote = "",
            ),
        )
        val event = growthEventRepository.observeEvents("child_002").first().single()

        assertEquals("孩子把一个小发现放进了小展台。", event.summary)
    }
}
