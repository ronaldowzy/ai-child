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
        assertEquals("0.1.1-runtime-webp", manifest.assetPackageVersion)
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
            "mascot/xiaobaohu/v1/speaking/v0.1.0/frames_webp/fox_speaking_0001.webp",
            paths.first(),
        )
        assertEquals(
            "mascot/xiaobaohu/v1/speaking/v0.1.0/frames_webp/fox_speaking_0024.webp",
            paths.last(),
        )
        assertEquals(512, spec.width)
        assertEquals(341, spec.height)
    }

    @Test
    fun runtimeAssetsUseWebpFramesOnly() {
        val files = TEST_ASSET_ROOT.walkTopDown().filter { it.isFile }.toList()

        assertEquals(264, files.count { it.extension == "webp" })
        assertEquals(0, files.count { it.extension == "png" })
        assertTrue(files.none { it.path.contains("/frames/") })
        assertTrue(files.all { !it.name.endsWith(".gif") && !it.name.endsWith(".html") })
    }

    @Test
    fun staticFallbackDrawablesUseWebpOnly() {
        val files = STATIC_FALLBACK_ROOT.listFiles()?.filter { it.isFile } ?: emptyList()

        assertEquals(12, files.count { it.extension == "webp" && it.name.startsWith("fox_3d_") })
        assertEquals(0, files.count { it.extension == "png" && it.name.startsWith("fox_3d_") })
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
        val STATIC_FALLBACK_ROOT = File("src/main/res/drawable-nodpi")
    }
}
