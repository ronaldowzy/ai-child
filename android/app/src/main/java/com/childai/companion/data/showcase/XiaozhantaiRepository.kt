package com.childai.companion.data.showcase

import android.content.Context
import java.io.File
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext
import org.json.JSONArray

open class XiaozhantaiRepository(
    initialItems: List<XiaozhantaiItem> = emptyList(),
) {
    protected val items = MutableStateFlow(visibleXiaozhantaiItems(initialItems))

    open fun observeItems(childId: String): Flow<List<XiaozhantaiItem>> {
        return items.map(::visibleXiaozhantaiItems)
    }

    open suspend fun itemById(childId: String, itemId: String): XiaozhantaiItem? {
        return visibleXiaozhantaiItems(items.value).firstOrNull { it.id == itemId }
    }

    open suspend fun saveCapturedPhoto(request: XiaozhantaiSaveRequest): XiaozhantaiItem {
        val item = XiaozhantaiItem(
            id = "stand_item_${UUID.randomUUID()}",
            photoUri = "memory://${request.childId}/${UUID.randomUUID()}",
            name = xiaozhantaiNormalizeName(request.name),
            foxQuote = xiaozhantaiNormalizeFoxQuote(request.foxQuote),
            createdAt = request.createdAt ?: System.currentTimeMillis(),
            source = request.source,
            isDeleted = false,
        )
        items.value = visibleXiaozhantaiItems(items.value + item)
        return item
    }

    open suspend fun softDelete(childId: String, itemId: String) {
        items.value = items.value.map { item ->
            if (item.id == itemId) item.copy(isDeleted = true) else item
        }
    }
}

class LocalXiaozhantaiRepository(
    private val rootDirectory: File,
    private val clock: () -> Long = System::currentTimeMillis,
) : XiaozhantaiRepository() {
    constructor(
        context: Context,
        clock: () -> Long = System::currentTimeMillis,
    ) : this(
        rootDirectory = File(context.filesDir, "xiaozhantai"),
        clock = clock,
    )

    override fun observeItems(childId: String): Flow<List<XiaozhantaiItem>> {
        ensureLoaded(childId)
        return super.observeItems(childId)
    }

    override suspend fun itemById(childId: String, itemId: String): XiaozhantaiItem? {
        ensureLoaded(childId)
        return super.itemById(childId, itemId)
    }

    override suspend fun saveCapturedPhoto(request: XiaozhantaiSaveRequest): XiaozhantaiItem {
        return withContext(Dispatchers.IO) {
            ensureLoaded(request.childId)
            val createdAt = request.createdAt ?: clock()
            val itemId = "stand_item_${createdAt}_${UUID.randomUUID().toString().take(8)}"
            val childDirectory = childDirectory(request.childId).apply { mkdirs() }
            val photoDirectory = File(childDirectory, "photos").apply { mkdirs() }
            val photoFile = File(photoDirectory, "$itemId.jpg")
            photoFile.writeBytes(request.photoBytes)
            val item = XiaozhantaiItem(
                id = itemId,
                photoUri = photoFile.absolutePath,
                name = xiaozhantaiNormalizeName(request.name),
                foxQuote = xiaozhantaiNormalizeFoxQuote(request.foxQuote),
                createdAt = createdAt,
                source = request.source.ifBlank { SOURCE_CHILD_CAMERA },
                isDeleted = false,
            )
            val allItems = readAllItems(request.childId)
                .filterNot { it.id == item.id } + item
            writeAllItems(request.childId, allItems)
            items.value = visibleXiaozhantaiItems(allItems)
            item
        }
    }

    override suspend fun softDelete(childId: String, itemId: String) {
        withContext(Dispatchers.IO) {
            ensureLoaded(childId)
            val allItems = readAllItems(childId).map { item ->
                if (item.id == itemId) item.copy(isDeleted = true) else item
            }
            writeAllItems(childId, allItems)
            items.value = visibleXiaozhantaiItems(allItems)
        }
    }

    private fun ensureLoaded(childId: String) {
        items.value = visibleXiaozhantaiItems(readAllItems(childId))
    }

    private fun readAllItems(childId: String): List<XiaozhantaiItem> {
        val metadataFile = metadataFile(childId)
        if (!metadataFile.isFile) return emptyList()
        return runCatching {
            val array = JSONArray(metadataFile.readText())
            buildList {
                for (index in 0 until array.length()) {
                    val item = array.optJSONObject(index)?.let(::xiaozhantaiItemFromJson)
                    if (item != null) add(item)
                }
            }
        }.getOrDefault(emptyList())
    }

    private fun writeAllItems(childId: String, nextItems: List<XiaozhantaiItem>) {
        val metadataFile = metadataFile(childId)
        metadataFile.parentFile?.mkdirs()
        val array = JSONArray()
        nextItems.forEach { item -> array.put(item.toJson()) }
        val tempFile = File(metadataFile.parentFile, "${metadataFile.name}.tmp")
        tempFile.writeText(array.toString())
        if (!tempFile.renameTo(metadataFile)) {
            metadataFile.writeText(array.toString())
            tempFile.delete()
        }
    }

    private fun metadataFile(childId: String): File {
        return File(childDirectory(childId), "items.json")
    }

    private fun childDirectory(childId: String): File {
        return File(rootDirectory, childId.safePathSegment())
    }
}

private fun String.safePathSegment(): String {
    return replace(Regex("[^A-Za-z0-9_.-]"), "_").ifBlank { "child" }
}
