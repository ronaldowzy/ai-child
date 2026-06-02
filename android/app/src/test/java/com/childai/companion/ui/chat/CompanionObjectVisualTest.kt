package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.CompanionObjectMeta
import androidx.compose.ui.Alignment
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
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
    fun coCreateUsesStrongerVisualEmphasisThanSeed() {
        val seed = CompanionObjectMeta(
            id = "seed_001",
            name = "",
            objectType = "star",
            lightLocation = "窗边",
            state = "seed",
            action = "name_seed",
        )
        val created = CompanionObjectMeta(
            id = "co_123",
            name = "小棉花",
            objectType = "star",
            lightLocation = "窗边",
            state = "active",
            action = "co_create",
        )

        val seedEmphasis = seed.visualEmphasis()
        val createdEmphasis = created.visualEmphasis()

        assertTrue(createdEmphasis.foregroundAlphaMultiplier > seedEmphasis.foregroundAlphaMultiplier)
        assertTrue(createdEmphasis.glowScale > seedEmphasis.glowScale)
        assertTrue(createdEmphasis.foregroundGlowAlpha > seedEmphasis.foregroundGlowAlpha)
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
    fun starVisualKindMapsToStar() {
        assertEquals(CompanionVisualType.Star, "star".toCompanionVisualType())
    }

    @Test
    fun cloudVisualKindMapsToCloud() {
        assertEquals(CompanionVisualType.Cloud, "cloud".toCompanionVisualType())
    }

    @Test
    fun paperBoatVisualKindMapsToPaperBoat() {
        assertEquals(CompanionVisualType.PaperBoat, "paper_boat".toCompanionVisualType())
    }

    @Test
    fun tinyDoorVisualKindMapsToTinyDoor() {
        assertEquals(CompanionVisualType.TinyDoor, "tiny_door".toCompanionVisualType())
    }

    @Test
    fun dinoShadowVisualKindMapsToDinoShadow() {
        assertEquals(CompanionVisualType.DinoShadow, "dino_shadow".toCompanionVisualType())
    }

    @Test
    fun blockLightVisualKindMapsToBlockLight() {
        assertEquals(CompanionVisualType.BlockLight, "block_light".toCompanionVisualType())
    }

    @Test
    fun legacyStarFallbackMapsToStar() {
        assertEquals(CompanionVisualType.Star, "小星星".toCompanionVisualType())
    }

    @Test
    fun legacyCloudFallbackMapsToCloud() {
        assertEquals(CompanionVisualType.Cloud, "小云朵".toCompanionVisualType())
    }

    @Test
    fun legacyDinoFallbackMapsToDinoShadow() {
        assertEquals(CompanionVisualType.DinoShadow, "小恐龙".toCompanionVisualType())
    }

    @Test
    fun legacyUnknownDefaultsToStar() {
        assertEquals(CompanionVisualType.Star, "未知类型".toCompanionVisualType())
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

    @Test
    fun windowSidePlacementMovesAwayFromTopBubbleRegion() {
        val portrait = CompanionLocation.WindowSide.placementForViewport(
            CompanionRoomViewportClass.Portrait,
        )
        val portraitExpanded = CompanionLocation.WindowSide.placementForViewport(
            CompanionRoomViewportClass.PortraitExpanded,
        )

        assertEquals(Alignment.CenterStart, portrait.alignment)
        assertEquals(Alignment.CenterStart, portraitExpanded.alignment)
        assertTrue(portrait.offset.y < 0f)
        assertTrue(portraitExpanded.offset.y < 0f)
        assertNotEquals(0f, portrait.offset.x)
    }
}
