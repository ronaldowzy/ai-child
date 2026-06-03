package com.childai.companion.data.growth

import android.content.Context
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext
import org.json.JSONArray

open class GrowthEventRepository(
    initialEvents: List<GrowthEvent> = emptyList(),
) {
    protected val events = MutableStateFlow(visibleGrowthEvents(initialEvents))

    open fun observeEvents(childId: String): Flow<List<GrowthEvent>> {
        return events.map { current ->
            visibleGrowthEvents(current.filter { it.childId == childId })
        }
    }

    open suspend fun append(event: GrowthEvent): GrowthEvent {
        events.value = visibleGrowthEvents(
            events.value.filterNot { it.id == event.id } + event,
        )
        return event
    }

    open suspend fun softDelete(childId: String, eventId: String) {
        events.value = visibleGrowthEvents(
            events.value.map { event ->
                if (event.childId == childId && event.id == eventId) {
                    event.copy(isDeleted = true)
                } else {
                    event
                }
            },
        )
    }
}

class LocalGrowthEventRepository(
    private val rootDirectory: File,
) : GrowthEventRepository() {
    constructor(context: Context) : this(
        rootDirectory = File(context.filesDir, "growth_events"),
    )

    override fun observeEvents(childId: String): Flow<List<GrowthEvent>> {
        ensureLoaded(childId)
        return super.observeEvents(childId)
    }

    override suspend fun append(event: GrowthEvent): GrowthEvent {
        return withContext(Dispatchers.IO) {
            ensureLoaded(event.childId)
            val allEvents = readAllEvents(event.childId)
                .filterNot { it.id == event.id } + event
            writeAllEvents(event.childId, allEvents)
            events.value = visibleGrowthEvents(allEvents)
            event
        }
    }

    override suspend fun softDelete(childId: String, eventId: String) {
        withContext(Dispatchers.IO) {
            ensureLoaded(childId)
            val allEvents = readAllEvents(childId).map { event ->
                if (event.id == eventId) event.copy(isDeleted = true) else event
            }
            writeAllEvents(childId, allEvents)
            events.value = visibleGrowthEvents(allEvents)
        }
    }

    private fun ensureLoaded(childId: String) {
        events.value = visibleGrowthEvents(readAllEvents(childId))
    }

    private fun readAllEvents(childId: String): List<GrowthEvent> {
        val metadataFile = metadataFile(childId)
        if (!metadataFile.isFile) return emptyList()
        return runCatching {
            val array = JSONArray(metadataFile.readText())
            buildList {
                for (index in 0 until array.length()) {
                    val event = array.optJSONObject(index)?.let(::growthEventFromJson)
                    if (event != null) add(event)
                }
            }
        }.getOrDefault(emptyList())
    }

    private fun writeAllEvents(childId: String, nextEvents: List<GrowthEvent>) {
        val metadataFile = metadataFile(childId)
        metadataFile.parentFile?.mkdirs()
        val array = JSONArray()
        nextEvents.forEach { event -> array.put(event.toJson()) }
        val tempFile = File(metadataFile.parentFile, "${metadataFile.name}.tmp")
        tempFile.writeText(array.toString())
        if (!tempFile.renameTo(metadataFile)) {
            metadataFile.writeText(array.toString())
            tempFile.delete()
        }
    }

    private fun metadataFile(childId: String): File {
        return File(childDirectory(childId), "events.json")
    }

    private fun childDirectory(childId: String): File {
        return File(rootDirectory, childId.safePathSegment())
    }
}

private fun String.safePathSegment(): String {
    return replace(Regex("[^A-Za-z0-9_.-]"), "_").ifBlank { "child" }
}
