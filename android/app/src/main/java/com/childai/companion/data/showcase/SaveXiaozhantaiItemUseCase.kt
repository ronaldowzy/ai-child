package com.childai.companion.data.showcase

import com.childai.companion.data.growth.GROWTH_EVENT_SHOWCASE_TITLE
import com.childai.companion.data.growth.GROWTH_EVENT_SOURCE_XIAOZHANTAI
import com.childai.companion.data.growth.GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED
import com.childai.companion.data.growth.GrowthEvent
import com.childai.companion.data.growth.GrowthEventRepository
import com.childai.companion.data.growth.showcaseItemSavedGrowthSummary

class SaveXiaozhantaiItemUseCase(
    private val xiaozhantaiRepository: XiaozhantaiRepository,
    private val growthEventRepository: GrowthEventRepository? = null,
) {
    suspend fun saveCapturedPhoto(request: XiaozhantaiSaveRequest): XiaozhantaiItem {
        val item = xiaozhantaiRepository.saveCapturedPhoto(request)
        growthEventRepository?.append(
            GrowthEvent(
                id = "growth_event_${item.id}",
                childId = request.childId,
                type = GROWTH_EVENT_TYPE_SHOWCASE_ITEM_SAVED,
                title = GROWTH_EVENT_SHOWCASE_TITLE,
                summary = showcaseItemSavedGrowthSummary(
                    name = request.name,
                    foxQuote = request.foxQuote,
                ),
                relatedItemId = item.id,
                relatedPhotoUri = item.photoUri,
                createdAt = item.createdAt,
                source = GROWTH_EVENT_SOURCE_XIAOZHANTAI,
                isDeleted = false,
            ),
        )
        return item
    }
}
