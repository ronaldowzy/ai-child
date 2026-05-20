package com.childai.companion.mascot

import android.content.res.AssetManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap

class FrameBitmapCache(
    private val assetManager: AssetManager,
    private val maxEntries: Int = DEFAULT_MAX_ENTRIES,
    private val sampleSize: Int = DEFAULT_SAMPLE_SIZE,
) {
    private val cache = object : LinkedHashMap<String, ImageBitmap>(maxEntries, 0.75f, true) {
        override fun removeEldestEntry(
            eldest: MutableMap.MutableEntry<String, ImageBitmap>?,
        ): Boolean = size > maxEntries
    }

    fun load(path: String): ImageBitmap? {
        cache[path]?.let { return it }
        val decoded = runCatching {
            assetManager.open(path).use { stream ->
                BitmapFactory.decodeStream(
                    stream,
                    null,
                    BitmapFactory.Options().apply {
                        inPreferredConfig = Bitmap.Config.ARGB_8888
                        inSampleSize = sampleSize.coerceAtLeast(1)
                    },
                )?.asImageBitmap()
            }
        }.getOrNull() ?: return null
        cache[path] = decoded
        return decoded
    }

    fun clear() {
        cache.clear()
    }

    companion object {
        const val DEFAULT_MAX_ENTRIES = 36
        const val DEFAULT_SAMPLE_SIZE = 2
        const val LOW_PERFORMANCE_SAMPLE_SIZE = 4
    }
}
