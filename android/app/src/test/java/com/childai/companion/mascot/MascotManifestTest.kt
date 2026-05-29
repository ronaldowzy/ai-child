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
        assertEquals(10, manifest.states.size)
        assertTrue(manifest.states.containsKey(MascotState.Speaking))
        assertTrue(manifest.states.containsKey(MascotState.Retry))
        assertEquals(12, manifest.defaultFps)
        assertEquals("0.3.0-hd-ondemand", manifest.assetPackageVersion)
        assertEquals(1024, manifest.states.getValue(MascotState.Idle).width)
        assertEquals(1024, manifest.states.getValue(MascotState.Idle).height)
    }

    @Test
    fun buildsFramePathsFromManifestPattern() {
        val manifest = parseTestManifest()
        val spec = manifest.states.getValue(MascotState.Speaking)

        val paths = AssetManifestLoader.buildFramePaths(
            rootPath = "mascot/xiaobaohu/v2/",
            statePath = spec.path,
            framePattern = spec.framePattern,
            frameCount = spec.frameCount,
        )

        assertEquals(48, paths.size)
        assertEquals(
            "mascot/xiaobaohu/v2/speaking/v2.0.0/frames_webp/fox_speaking_0001.webp",
            paths.first(),
        )
        assertEquals(
            "mascot/xiaobaohu/v2/speaking/v2.0.0/frames_webp/fox_speaking_0048.webp",
            paths.last(),
        )
        assertEquals(512, spec.width)
        assertEquals(512, spec.height)
    }

    @Test
    fun runtimeAssetsUseWebpFramesOnly() {
        val files = TEST_ASSET_ROOT.walkTopDown().filter { it.isFile }.toList()

        assertEquals(480, files.count { it.extension == "webp" })
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
    fun statePriorityKeepsRetryAbovePaused() {
        val manifest = parseTestManifest()

        assertTrue(
            MascotStatePriority.rank(MascotState.Retry, manifest) <
                MascotStatePriority.rank(MascotState.Paused, manifest),
        )
        assertTrue(
            MascotStatePriority.rank(MascotState.Paused, manifest) <
                MascotStatePriority.rank(MascotState.Speaking, manifest),
        )
        assertTrue(
            MascotStatePriority.rank(MascotState.Speaking, manifest) <
                MascotStatePriority.rank(MascotState.Thinking, manifest),
        )
    }

    @Test
    fun controllerKeepsPausedAboveSpeaking() {
        val controller = MascotController(parseTestManifest())

        assertEquals(
            MascotState.Paused,
            controller.higherPriority(MascotState.Speaking, MascotState.Paused),
        )
        assertTrue(controller.shouldReplace(MascotState.Speaking, MascotState.Paused))
    }

    @Test
    fun shortLoopReturnsToBaseStateAfterCompletion() {
        val controller = MascotController(parseTestManifest())

        assertEquals(
            MascotState.Idle,
            controller.stateAfterCompletion(
                completed = MascotState.CoCreate,
                baseState = MascotState.Idle,
            ),
        )
    }

    @Test
    fun unknownStateFallsBackToIdle() {
        assertEquals(MascotState.Idle, MascotState.fromId("not_in_manifest"))
    }

    @Test
    fun idleStateHasNoHdSpec() {
        val manifest = parseTestManifest()
        val idleSpec = manifest.states.getValue(MascotState.Idle)
        assertTrue("idle should have no hd spec", idleSpec.hd == null)
    }

    @Test
    fun nonIdleStatesHaveHdSpec() {
        val manifest = parseTestManifest()
        val nonIdleStates = MascotState.entries.filter { it != MascotState.Idle }
        nonIdleStates.forEach { state ->
            val spec = manifest.states.getValue(state)
            assertTrue("${state.id} should have hd spec", spec.hd != null)
            assertEquals(1024, spec.hd!!.width)
            assertEquals(1024, spec.hd!!.height)
            assertTrue("${state.id} hd framePattern should contain %04d", spec.hd!!.framePattern.contains("%04d"))
        }
    }

    private fun parseTestManifest(): MascotManifest {
        return AssetManifestLoader.parseMascotManifest(
            File(TEST_ASSET_ROOT, "mascot_manifest.json").readText(),
        )
    }

    private companion object {
        val TEST_ASSET_ROOT = File("src/main/assets/mascot/xiaobaohu/v2")
        val STATIC_FALLBACK_ROOT = File("src/main/res/drawable-nodpi")
    }
}
