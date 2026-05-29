package com.childai.companion.data

import com.childai.companion.mascot.MascotState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.io.FileOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

class FoxHdAssetManagerTest {

    @Test
    fun hdAssetStateNotStartedHasCorrectType() {
        val state = HdAssetState.NotStarted
        assertTrue(state is HdAssetState.NotStarted)
    }

    @Test
    fun hdAssetStateDownloadingTracksProgress() {
        val state = HdAssetState.Downloading(0.5f)
        assertTrue(state is HdAssetState.Downloading)
        assertEquals(0.5f, (state as HdAssetState.Downloading).progress, 0.001f)
    }

    @Test
    fun hdAssetStateReadyHoldsFramesDir() {
        val dir = File("/tmp/test_frames")
        val state = HdAssetState.Ready(dir)
        assertTrue(state is HdAssetState.Ready)
        assertEquals(dir, (state as HdAssetState.Ready).framesDir)
    }

    @Test
    fun hdAssetStateFailedHoldsReason() {
        val state = HdAssetState.Failed("network error")
        assertTrue(state is HdAssetState.Failed)
        assertEquals("network error", (state as HdAssetState.Failed).reason)
    }

    @Test
    fun mascotStatesHaveCorrectIds() {
        assertEquals("listening", MascotState.Listening.id)
        assertEquals("speaking", MascotState.Speaking.id)
        assertEquals("waiting_soft", MascotState.WaitingSoft.id)
        assertEquals("thinking", MascotState.Thinking.id)
        assertEquals("preparing_speech", MascotState.PreparingSpeech.id)
        assertEquals("image_viewing", MascotState.ImageViewing.id)
        assertEquals("co_create", MascotState.CoCreate.id)
        assertEquals("paused", MascotState.Paused.id)
        assertEquals("retry", MascotState.Retry.id)
    }

    @Test
    fun hdStatesExcludeIdle() {
        val hdStates = MascotState.entries.filter { it != MascotState.Idle }
        assertEquals(9, hdStates.size)
        assertFalse(hdStates.contains(MascotState.Idle))
    }

    @Test
    fun zipExtractionProducesExpectedStructure() {
        val tmpDir = createTempDir("hd_test")
        try {
            val zipFile = File(tmpDir, "test.zip")
            ZipOutputStream(FileOutputStream(zipFile)).use { zos ->
                zos.putNextEntry(ZipEntry("frames_webp/"))
                zos.closeEntry()
                zos.putNextEntry(ZipEntry("frames_webp/fox_listening_0001.webp"))
                zos.write(byteArrayOf(0x52, 0x49, 0x46, 0x46)) // RIFF header
                zos.closeEntry()
                zos.putNextEntry(ZipEntry("manifest.json"))
                zos.write("""{"state":"listening"}""".toByteArray())
                zos.closeEntry()
            }

            val extractDir = File(tmpDir, "extracted")
            extractDir.mkdirs()
            java.util.zip.ZipInputStream(zipFile.inputStream().buffered()).use { zis ->
                var entry = zis.nextEntry
                while (entry != null) {
                    if (entry.isDirectory) {
                        File(extractDir, entry.name).mkdirs()
                    } else {
                        val outFile = File(extractDir, entry.name)
                        outFile.parentFile?.mkdirs()
                        FileOutputStream(outFile).use { zis.copyTo(it) }
                    }
                    zis.closeEntry()
                    entry = zis.nextEntry
                }
            }

            assertTrue(File(extractDir, "frames_webp").exists())
            assertTrue(File(extractDir, "frames_webp/fox_listening_0001.webp").exists())
            assertTrue(File(extractDir, "manifest.json").exists())
        } finally {
            tmpDir.deleteRecursively()
        }
    }
}
