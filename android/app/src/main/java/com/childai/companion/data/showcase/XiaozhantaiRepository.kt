package com.childai.companion.data.showcase

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.map

open class XiaozhantaiRepository(
    initialItems: List<XiaozhantaiItem> = emptyList(),
) {
    private val items = MutableStateFlow(initialItems)

    open fun observeItems(childId: String): Flow<List<XiaozhantaiItem>> {
        return items.map(::visibleXiaozhantaiItems)
    }

    open suspend fun itemById(childId: String, itemId: String): XiaozhantaiItem? {
        return visibleXiaozhantaiItems(items.value).firstOrNull { it.id == itemId }
    }
}
