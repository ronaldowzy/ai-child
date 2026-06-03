package com.childai.companion.ui.chat

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class HouseObjectDebugModelsTest {

    @Test
    fun debugToolsRequireDebugBuildAndDevSetting() {
        assertTrue(
            houseObjectDebugToolsVisible(
                debugBuild = true,
                devSettingEnabled = true,
            ),
        )
        assertFalse(
            houseObjectDebugToolsVisible(
                debugBuild = false,
                devSettingEnabled = true,
            ),
        )
        assertFalse(
            houseObjectDebugToolsVisible(
                debugBuild = true,
                devSettingEnabled = false,
            ),
        )
    }

    @Test
    fun noneStateBuildsNoPreviewMetaAndCannotPersist() {
        assertNull(
            houseObjectDebugBuildPreviewMeta(
                visualKind = "star",
                state = "none",
                lightLocation = "窗边",
            ),
        )
        assertFalse(houseObjectDebugCanPersist("none"))
    }

    @Test
    fun seedPreviewUsesNameSeedContract() {
        val meta = houseObjectDebugBuildPreviewMeta(
            visualKind = "star",
            state = "seed",
            lightLocation = "窗边",
        )

        requireNotNull(meta)
        assertEquals("seed", meta.state)
        assertEquals("name_seed", meta.action)
        assertTrue(meta.shouldShowVisual())
    }

    @Test
    fun coCreateAndRecallPreviewUseActiveState() {
        val coCreate = houseObjectDebugBuildPreviewMeta(
            visualKind = "cloud",
            state = "co_create",
            lightLocation = "地毯边",
        )
        val recall = houseObjectDebugBuildPreviewMeta(
            visualKind = "paper_boat",
            state = "recall",
            lightLocation = "窗外",
        )

        requireNotNull(coCreate)
        requireNotNull(recall)
        assertEquals("active", coCreate.state)
        assertEquals("co_create", coCreate.action)
        assertEquals("active", recall.state)
        assertEquals("recall", recall.action)
        assertTrue(coCreate.shouldShowVisual())
        assertTrue(recall.shouldShowVisual())
    }

    @Test
    fun allM2VisualKindsBuildVisibleCoCreatePreview() {
        houseObjectDebugVisualKinds.forEach { option ->
            val meta = houseObjectDebugBuildPreviewMeta(
                visualKind = option.id,
                state = "co_create",
                lightLocation = "窗边",
            )

            requireNotNull(meta)
            assertEquals(option.id, meta.visualKind)
            assertTrue(meta.shouldShowVisual())
        }
    }

    @Test
    fun objectTypeMappingMatchesBackendDebugMapping() {
        assertEquals("star", houseObjectDebugObjectType("star"))
        assertEquals("cloud", houseObjectDebugObjectType("cloud"))
        assertEquals("paper_boat", houseObjectDebugObjectType("paper_boat"))
        assertEquals("story_gate", houseObjectDebugObjectType("tiny_door"))
        assertEquals("drawing_character", houseObjectDebugObjectType("dino_shadow"))
        assertEquals("block_monster", houseObjectDebugObjectType("block_light"))
    }
}
