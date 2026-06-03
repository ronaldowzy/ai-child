package com.childai.companion.data.showcase

import java.io.File
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class LocalXiaozhantaiRepositoryTest {
    @get:Rule
    val temporaryFolder = TemporaryFolder()

    @Test
    fun saveCapturedPhotoPersistsMetadataPhotoAndFoxQuote() = runTest {
        val root = temporaryFolder.newFolder("xiaozhantai")
        val repository = LocalXiaozhantaiRepository(
            rootDirectory = root,
            clock = { 1760000000000L },
        )

        val item = repository.saveCapturedPhoto(
            XiaozhantaiSaveRequest(
                childId = "child_001",
                photoBytes = byteArrayOf(1, 2, 3, 4),
                name = "小石头",
                foxQuote = "它看起来像一颗安静的小星球。",
            ),
        )

        assertEquals("小石头", item.name)
        assertEquals("它看起来像一颗安静的小星球。", item.foxQuote)
        assertEquals(1760000000000L, item.createdAt)
        assertTrue(File(item.photoUri).isFile)
        assertEquals(listOf(item), repository.observeItems("child_001").first())

        val restartedRepository = LocalXiaozhantaiRepository(
            rootDirectory = root,
            clock = { 1760000005000L },
        )
        val restored = restartedRepository.observeItems("child_001").first().single()
        assertEquals(item.id, restored.id)
        assertEquals("小石头", restored.name)
        assertEquals("它看起来像一颗安静的小星球。", restored.foxQuote)
        assertTrue(File(restored.photoUri).isFile)
    }

    @Test
    fun softDeleteHidesLastItemSoListReturnsEmpty() = runTest {
        val repository = LocalXiaozhantaiRepository(
            rootDirectory = temporaryFolder.newFolder("xiaozhantai-delete"),
            clock = { 1760000000000L },
        )
        val item = repository.saveCapturedPhoto(
            XiaozhantaiSaveRequest(
                childId = "child_002",
                photoBytes = byteArrayOf(7, 8, 9),
                name = "小云朵",
                foxQuote = "它像轻轻飘过来的云。",
            ),
        )

        repository.softDelete("child_002", item.id)

        assertFalse(repository.observeItems("child_002").first().any())
    }
}
