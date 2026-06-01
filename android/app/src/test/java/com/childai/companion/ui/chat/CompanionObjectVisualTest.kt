package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.CompanionObjectMeta
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CompanionObjectVisualTest {

    @Test
    fun seedStateShouldShowVisual() {
        val companion = CompanionObjectMeta(
            id = "seed_001",
            name = "",
            objectType = "小星星",
            lightLocation = "窗边",
            state = "seed",
            action = "name_seed",
        )
        assertTrue(companion.shouldShowVisual())
    }

    @Test
    fun activeRecallShouldShowVisual() {
        val companion = CompanionObjectMeta(
            id = "co_123",
            name = "小棉花",
            objectType = "小星星",
            lightLocation = "窗边",
            state = "active",
            action = "recall",
        )
        assertTrue(companion.shouldShowVisual())
    }

    @Test
    fun activeCoCreateShouldShowVisual() {
        val companion = CompanionObjectMeta(
            id = "co_123",
            name = "小棉花",
            objectType = "star",
            lightLocation = "窗边",
            state = "active",
            action = "co_create",
        )
        assertTrue(companion.shouldShowVisual())
    }

    @Test
    fun pausedStateShouldNotShowVisual() {
        val companion = CompanionObjectMeta(
            id = "co_123",
            name = "小棉花",
            objectType = "小星星",
            lightLocation = "窗边",
            state = "paused",
            action = "recall",
        )
        assertFalse(companion.shouldShowVisual())
    }

    @Test
    fun activeWithNoneActionShouldNotShowVisual() {
        val companion = CompanionObjectMeta(
            id = "co_123",
            name = "小棉花",
            objectType = "小星星",
            lightLocation = "窗边",
            state = "active",
            action = "none",
        )
        assertFalse(companion.shouldShowVisual())
    }

    @Test
    fun starObjectTypeMapsToStarPoint() {
        assertEquals(
            CompanionVisualType.StarPoint,
            "小星星".toCompanionVisualType(),
        )
    }

    @Test
    fun backendStarEnumMapsToStarPoint() {
        assertEquals(
            CompanionVisualType.StarPoint,
            "star".toCompanionVisualType(),
        )
    }

    @Test
    fun cloudObjectTypeMapsToCloudShadow() {
        assertEquals(
            CompanionVisualType.CloudShadow,
            "小云朵".toCompanionVisualType(),
        )
    }

    @Test
    fun lightObjectTypeMapsToLightSpot() {
        assertEquals(
            CompanionVisualType.LightSpot,
            "小光影".toCompanionVisualType(),
        )
    }

    @Test
    fun unknownObjectTypeMapsToSoftOutline() {
        assertEquals(
            CompanionVisualType.SoftOutline,
            "小恐龙".toCompanionVisualType(),
        )
    }

    @Test
    fun windowSideLocationParsed() {
        assertEquals(
            CompanionLocation.WindowSide,
            "窗边".toCompanionLocation(),
        )
    }

    @Test
    fun carpetEdgeLocationParsed() {
        assertEquals(
            CompanionLocation.CarpetEdge,
            "地毯边".toCompanionLocation(),
        )
    }

    @Test
    fun nearFoxLocationParsed() {
        assertEquals(
            CompanionLocation.NearFox,
            "小白狐旁边".toCompanionLocation(),
        )
    }

    @Test
    fun outsideWindowLocationParsed() {
        assertEquals(
            CompanionLocation.OutsideWindow,
            "窗外".toCompanionLocation(),
        )
    }

    @Test
    fun unknownLocationDefaultsToWindowSide() {
        assertEquals(
            CompanionLocation.WindowSide,
            "未知位置".toCompanionLocation(),
        )
    }
}
