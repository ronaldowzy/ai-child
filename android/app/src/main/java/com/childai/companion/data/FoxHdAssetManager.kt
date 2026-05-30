package com.childai.companion.data

import android.content.Context
import android.util.Log
import com.childai.companion.config.DevSettings
import com.childai.companion.mascot.MascotState
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.ConcurrentHashMap
import java.util.zip.ZipInputStream

internal fun buildFoxHdAssetUrl(baseUrl: String, state: MascotState): URL {
    return URL("${baseUrl.trimEnd('/')}/api/v1/assets/fox/hd/${state.id}")
}

/**
 * Manages on-demand download and local caching of HD (1024px) mascot state assets.
 *
 * - HD assets are zip files hosted on the backend
 * - Downloaded lazily when a state is first requested
 * - Cached in app internal storage: `filesDir/mascot_hd/{state}/`
 * - Falls back to bundled 512px assets if download fails
 */
class FoxHdAssetManager(
    private val context: Context,
    private val baseUrl: String,
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val mutex = Mutex()
    private val downloadJobs = ConcurrentHashMap<MascotState, MutableStateFlow<HdAssetState>>()

    private val hdRootDir: File
        get() = File(context.filesDir, "mascot_hd")

    /**
     * Get the current HD asset state for a state. Returns null if never requested.
     */
    fun hdStateFlow(state: MascotState): StateFlow<HdAssetState>? {
        return downloadJobs[state]?.asStateFlow()
    }

    /**
     * Check if HD frames are available locally for the given state.
     */
    fun isHdCached(state: MascotState): Boolean {
        val stateDir = hdStateDir(state)
        if (!stateDir.exists()) return false
        val framesDir = File(stateDir, "frames_webp")
        return framesDir.exists() && framesDir.listFiles()?.isNotEmpty() == true
    }

    /**
     * Get the local path to HD frames directory, or null if not cached.
     */
    fun hdFramesDir(state: MascotState): File? {
        val framesDir = File(hdStateDir(state), "frames_webp")
        return if (framesDir.exists() && framesDir.listFiles()?.isNotEmpty() == true) {
            framesDir
        } else {
            null
        }
    }

    /**
     * Ensure HD asset is available. Triggers async download if not cached.
     * Returns immediately with current state.
     */
    fun ensureHdAvailable(state: MascotState): StateFlow<HdAssetState> {
        val existing = downloadJobs[state]
        if (existing != null) {
            val current = existing.value
            if (current is HdAssetState.Ready || current is HdAssetState.Downloading) {
                return existing.asStateFlow()
            }
            // If failed, allow retry
        }

        val stateFlow = MutableStateFlow<HdAssetState>(HdAssetState.NotStarted)
        downloadJobs[state] = stateFlow

        if (isHdCached(state)) {
            stateFlow.value = HdAssetState.Ready(hdFramesDir(state)!!)
            return stateFlow.asStateFlow()
        }

        stateFlow.value = HdAssetState.Downloading(0f)
        scope.launch {
            downloadAndExtract(state, stateFlow)
        }
        return stateFlow.asStateFlow()
    }

    private suspend fun downloadAndExtract(state: MascotState, stateFlow: MutableStateFlow<HdAssetState>) {
        mutex.withLock {
            // Double-check after acquiring lock
            if (isHdCached(state)) {
                stateFlow.value = HdAssetState.Ready(hdFramesDir(state)!!)
                return
            }

            val stateDir = hdStateDir(state)
            val tmpZip = File(context.cacheDir, "${state.id}_hd.zip")

            try {
                // Step 1: Download zip
                val url = buildHdAssetUrl(state)
                val connection = url.openConnection() as HttpURLConnection
                connection.connectTimeout = 15_000
                connection.readTimeout = 30_000
                connection.setRequestProperty("Accept", "application/zip")

                if (connection.responseCode != 200) {
                    Log.w(TAG, "HD download failed for ${state.id}: HTTP ${connection.responseCode}")
                    stateFlow.value = HdAssetState.Failed("HTTP ${connection.responseCode}")
                    return
                }

                val totalBytes = connection.contentLength.toLong()
                var downloadedBytes = 0L

                connection.inputStream.use { input ->
                    FileOutputStream(tmpZip).use { output ->
                        val buffer = ByteArray(8192)
                        var bytesRead: Int
                        while (input.read(buffer).also { bytesRead = it } != -1) {
                            output.write(buffer, 0, bytesRead)
                            downloadedBytes += bytesRead
                            if (totalBytes > 0) {
                                stateFlow.value = HdAssetState.Downloading(
                                    downloadedBytes.toFloat() / totalBytes
                                )
                            }
                        }
                    }
                }

                // Step 2: Extract zip
                stateDir.mkdirs()
                extractZip(tmpZip, stateDir)

                // Step 3: Verify extraction
                val framesDir = File(stateDir, "frames_webp")
                if (!framesDir.exists() || framesDir.listFiles()?.isEmpty() != false) {
                    stateFlow.value = HdAssetState.Failed("No frames extracted")
                    stateDir.deleteRecursively()
                    return
                }

                tmpZip.delete()
                stateFlow.value = HdAssetState.Ready(framesDir)
                Log.i(TAG, "HD asset ready for ${state.id}: ${framesDir.listFiles()?.size} frames")

            } catch (e: Exception) {
                Log.w(TAG, "HD download failed for ${state.id}", e)
                stateFlow.value = HdAssetState.Failed(e.message ?: "Unknown error")
                tmpZip.delete()
                // Don't delete stateDir on failure - partial extract is OK, will retry
            }
        }
    }

    private fun extractZip(zipFile: File, targetDir: File) {
        ZipInputStream(zipFile.inputStream().buffered()).use { zis ->
            var entry = zis.nextEntry
            while (entry != null) {
                if (entry.isDirectory) {
                    File(targetDir, entry.name).mkdirs()
                } else {
                    val outFile = File(targetDir, entry.name)
                    outFile.parentFile?.mkdirs()
                    FileOutputStream(outFile).use { fos ->
                        zis.copyTo(fos)
                    }
                }
                zis.closeEntry()
                entry = zis.nextEntry
            }
        }
    }

    private fun hdStateDir(state: MascotState): File {
        return File(hdRootDir, state.id)
    }

    internal fun buildHdAssetUrl(state: MascotState): URL {
        return buildFoxHdAssetUrl(baseUrl, state)
    }

    /**
     * Clear all cached HD assets.
     */
    fun clearAll() {
        hdRootDir.deleteRecursively()
        downloadJobs.clear()
    }

    /**
     * Clear cached HD asset for a specific state.
     */
    fun clear(state: MascotState) {
        hdStateDir(state).deleteRecursively()
        downloadJobs.remove(state)
    }

    companion object {
        private const val TAG = "FoxHdAssetManager"
        @Volatile
        private var instance: FoxHdAssetManager? = null

        fun getInstance(context: Context): FoxHdAssetManager {
            return instance ?: synchronized(this) {
                instance ?: FoxHdAssetManager(context.applicationContext, DevSettings.conversationApiBaseUrl).also {
                    instance = it
                }
            }
        }
    }
}

/**
 * Represents the state of an HD asset download/cache.
 */
sealed class HdAssetState {
    /** Not started yet */
    data object NotStarted : HdAssetState()

    /** Downloading with progress 0.0-1.0 */
    data class Downloading(val progress: Float) : HdAssetState()

    /** HD frames are ready to use */
    data class Ready(val framesDir: File) : HdAssetState()

    /** Download failed */
    data class Failed(val reason: String) : HdAssetState()
}
