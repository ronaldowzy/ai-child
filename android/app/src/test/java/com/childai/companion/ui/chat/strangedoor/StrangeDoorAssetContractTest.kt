package com.childai.companion.ui.chat.strangedoor

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class StrangeDoorAssetContractTest {
    @Test
    fun assetContractContainsTenRequiredFilesFromS1Plan() {
        assertEquals(10, StrangeDoorAssetContract.requiredAssets.size)
        assertEquals(
            setOf(
                "strange_door_closed.webp",
                "strange_door_cracked.webp",
                "strange_door_almost_open.webp",
                "strange_door_open.webp",
                "strange_door_round_lock.webp",
                "strange_door_transform_glow.webp",
                "strange_door_success_glow.webp",
                "strange_door_riddle_panel.webp",
                "strange_door_tool_card_panel.webp",
                "strange_door_ground_shadow.webp",
            ),
            StrangeDoorAssetContract.requiredFileNames,
        )
    }

    @Test
    fun assetMapperReportsMissingAssetsUntilS1ProvidesFiles() {
        val mapper = StrangeDoorAssetMapper()

        assertFalse(mapper.allAssetsReady())
        assertFalse(mapper.resolve(StrangeDoorAssetKey.DoorClosed).isReady)
    }

    @Test
    fun assetMapperReportsReadyOnlyWhenAllContractFilesExist() {
        val mapper = StrangeDoorAssetMapper(
            availableFileNames = StrangeDoorAssetContract.requiredFileNames,
        )

        assertTrue(mapper.allAssetsReady())
        assertTrue(mapper.resolve(StrangeDoorAssetKey.DoorOpen).isReady)
    }
}
