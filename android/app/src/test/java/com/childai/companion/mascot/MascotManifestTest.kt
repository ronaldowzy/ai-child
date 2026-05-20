package com.childai.companion.mascot

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class MascotManifestTest {
    @Test
    fun parsesAnimationManifestFromAndroidAssets() {
        val manifest = parseTestManifest()

        assertEquals("Little White Fox", manifest.mascot)
        assertEquals(MascotState.Idle, manifest.defaultState)
        assertEquals(11, manifest.states.size)
        assertTrue(manifest.states.containsKey(MascotState.Speaking))
        assertTrue(manifest.states.containsKey(MascotState.NetworkError))
        assertEquals(12, manifest.defaultFps)
    }

    @Test
    fun buildsFramePathsFromManifestPattern() {
        val manifest = parseTestManifest()
        val spec = manifest.states.getValue(MascotState.Speaking)

        val paths = AssetManifestLoader.buildFramePaths(
            rootPath = "mascot/xiaobaohu/v1/",
            statePath = spec.path,
            framePattern = spec.framePattern,
            frameCount = spec.frameCount,
        )

        assertEquals(24, paths.size)
        assertEquals(
            "mascot/xiaobaohu/v1/speaking/v0.1.0/frames/fox_speaking_0001.png",
            paths.first(),
        )
        assertEquals(
            "mascot/xiaobaohu/v1/speaking/v0.1.0/frames/fox_speaking_0024.png",
            paths.last(),
        )
    }

    @Test
    fun statePriorityKeepsSafetyAboveSpeaking() {
        val manifest = parseTestManifest()

        assertTrue(
            MascotStatePriority.rank(MascotState.SafetyConcern, manifest) <
                MascotStatePriority.rank(MascotState.PrivacyBoundary, manifest),
        )
        assertTrue(
            MascotStatePriority.rank(MascotState.PrivacyBoundary, manifest) <
                MascotStatePriority.rank(MascotState.NetworkError, manifest),
        )
        assertTrue(
            MascotStatePriority.rank(MascotState.NetworkError, manifest) <
                MascotStatePriority.rank(MascotState.Speaking, manifest),
        )
        assertTrue(
            MascotStatePriority.rank(MascotState.Speaking, manifest) <
                MascotStatePriority.rank(MascotState.Thinking, manifest),
        )
    }

    @Test
    fun controllerKeepsPrivacyBoundaryAboveSpeaking() {
        val controller = MascotController(parseTestManifest())

        assertEquals(
            MascotState.PrivacyBoundary,
            controller.higherPriority(MascotState.Speaking, MascotState.PrivacyBoundary),
        )
        assertTrue(controller.shouldReplace(MascotState.Speaking, MascotState.PrivacyBoundary))
    }

    @Test
    fun shortLoopReturnsToBaseStateAfterCompletion() {
        val controller = MascotController(parseTestManifest())

        assertEquals(
            MascotState.Idle,
            controller.stateAfterCompletion(
                completed = MascotState.JumpingHappy,
                baseState = MascotState.Idle,
            ),
        )
    }

    @Test
    fun unknownStateFallsBackToIdle() {
        assertEquals(MascotState.Idle, MascotState.fromId("not_in_manifest"))
    }

    private fun parseTestManifest(): MascotManifest {
        return AssetManifestLoader.parseMascotManifest(
            File(TEST_ASSET_ROOT, "mascot_manifest.json").readText(),
        )
    }

    private companion object {
        val TEST_ASSET_ROOT = File("src/main/assets/mascot/xiaobaohu/v1")
    }
}
