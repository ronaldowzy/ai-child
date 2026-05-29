package com.childai.companion.mascot

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class XiaobaohuMascotManifestCompletenessTest {
    @Test
    fun everyMascotStateHasManifestEntryAndEveryManifestStateIsKnown() {
        val manifest = AssetManifestLoader.parseMascotManifest(MASCOT_MANIFEST_JSON)
        val expectedStates = MascotState.entries.toSet()

        assertEquals(expectedStates, manifest.states.keys)
        assertEquals(MascotState.Idle, manifest.defaultState)

        val rawStateIds = JSONObject(MASCOT_MANIFEST_JSON)
            .getJSONObject("states")
            .keys()
            .asSequence()
            .toList()
        assertEquals(expectedStates.map { it.id }.toSet(), rawStateIds.toSet())
        rawStateIds.forEach { stateId ->
            assertEquals(stateId, MascotState.fromId(stateId).id)
        }
    }

    @Test
    fun statePriorityContainsEveryDeclaredStateOnce() {
        val manifest = AssetManifestLoader.parseMascotManifest(MASCOT_MANIFEST_JSON)

        assertEquals(MascotState.entries.size, manifest.statePriority.size)
        assertEquals(MascotState.entries.toSet(), manifest.statePriority.toSet())
        assertEquals(MascotState.Retry, manifest.statePriority[0])
        assertTrue(manifest.statePriority.indexOf(MascotState.Retry) < manifest.statePriority.indexOf(MascotState.Speaking))
        assertTrue(manifest.statePriority.indexOf(MascotState.Paused) < manifest.statePriority.indexOf(MascotState.Speaking))
    }

    @Test
    fun unknownOrMissingStateFallsBackToIdle() {
        assertEquals(MascotState.Idle, MascotState.fromId("missing_state"))
        assertEquals(MascotState.Idle, MascotState.fromId(null))
    }

    @Test
    fun manifestKeepsRuntimeFallbackSafe() {
        val manifest = AssetManifestLoader.parseMascotManifest(MASCOT_MANIFEST_JSON)

        MascotState.entries.forEach { state ->
            val spec = manifest.states[state]
            requireNotNull(spec) { "Missing spec for ${state.id}" }
            assertTrue("${state.id} frameCount", spec.frameCount > 0)
            assertTrue("${state.id} fps", spec.fps > 0)
            assertTrue("${state.id} path", spec.path.isNotBlank())
            assertTrue("${state.id} manifest", spec.manifestPath.endsWith("manifest.json"))
            assertTrue("${state.id} framePattern", spec.framePattern.contains("%04d"))
            assertFalse("${state.id} should not use png frames", spec.framePattern.endsWith(".png"))
        }
    }

    @Test
    fun nonIdleStatesHaveHdSpecWithValidDimensions() {
        val manifest = AssetManifestLoader.parseMascotManifest(MASCOT_MANIFEST_JSON)

        MascotState.entries.filter { it != MascotState.Idle }.forEach { state ->
            val spec = manifest.states[state]
            requireNotNull(spec) { "Missing spec for ${state.id}" }
            val hd = spec.hd
            requireNotNull(hd) { "${state.id} should have hd spec" }
            assertEquals("${state.id} hd width", 1024, hd.width)
            assertEquals("${state.id} hd height", 1024, hd.height)
            assertTrue("${state.id} hd framePattern", hd.framePattern.contains("%04d"))
        }
    }

    @Test
    fun idleStateHasNoHdSpec() {
        val manifest = AssetManifestLoader.parseMascotManifest(MASCOT_MANIFEST_JSON)
        val idleSpec = manifest.states[MascotState.Idle]
        requireNotNull(idleSpec)
        assertTrue("idle should have no hd spec", idleSpec.hd == null)
    }

    private companion object {
        private const val MASCOT_MANIFEST_JSON = """
            {
              "mascot": "Little White Fox",
              "assetPackageVersion": "0.2.0-v2-full",
              "format": "webp_frame_sequence_runtime",
              "defaultFps": 12,
              "defaultState": "idle",
              "dimensions": [
                {
                  "width": 512,
                  "height": 512
                }
              ],
              "states": {
                "idle": {
                  "version": "v2.0.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 48,
                  "width": 512,
                  "height": 512,
                  "path": "idle/v2.0.0/",
                  "manifest": "idle/v2.0.0/manifest.json",
                  "framePattern": "frames_webp/fox_idle_%04d.webp"
                },
                "listening": {
                  "version": "v2.0.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 48,
                  "width": 512,
                  "height": 512,
                  "path": "listening/v2.0.0/",
                  "manifest": "listening/v2.0.0/manifest.json",
                  "framePattern": "frames_webp/fox_listening_%04d.webp",
                  "hd": { "width": 1024, "height": 1024, "framePattern": "frames_webp/fox_listening_%04d.webp" }
                },
                "thinking": {
                  "version": "v2.0.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 48,
                  "width": 512,
                  "height": 512,
                  "path": "thinking/v2.0.0/",
                  "manifest": "thinking/v2.0.0/manifest.json",
                  "framePattern": "frames_webp/fox_thinking_%04d.webp",
                  "hd": { "width": 1024, "height": 1024, "framePattern": "frames_webp/fox_thinking_%04d.webp" }
                },
                "speaking": {
                  "version": "v2.0.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 48,
                  "width": 512,
                  "height": 512,
                  "path": "speaking/v2.0.0/",
                  "manifest": "speaking/v2.0.0/manifest.json",
                  "framePattern": "frames_webp/fox_speaking_%04d.webp",
                  "hd": { "width": 1024, "height": 1024, "framePattern": "frames_webp/fox_speaking_%04d.webp" }
                },
                "waiting_soft": {
                  "version": "v2.0.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 48,
                  "width": 512,
                  "height": 512,
                  "path": "waiting_soft/v2.0.0/",
                  "manifest": "waiting_soft/v2.0.0/manifest.json",
                  "framePattern": "frames_webp/fox_waiting_soft_%04d.webp",
                  "hd": { "width": 1024, "height": 1024, "framePattern": "frames_webp/fox_waiting_soft_%04d.webp" }
                },
                "preparing_speech": {
                  "version": "v2.0.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 48,
                  "width": 512,
                  "height": 512,
                  "path": "preparing_speech/v2.0.0/",
                  "manifest": "preparing_speech/v2.0.0/manifest.json",
                  "framePattern": "frames_webp/fox_preparing_speech_%04d.webp",
                  "hd": { "width": 1024, "height": 1024, "framePattern": "frames_webp/fox_preparing_speech_%04d.webp" }
                },
                "image_viewing": {
                  "version": "v2.0.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 48,
                  "width": 512,
                  "height": 512,
                  "path": "image_viewing/v2.0.0/",
                  "manifest": "image_viewing/v2.0.0/manifest.json",
                  "framePattern": "frames_webp/fox_image_viewing_%04d.webp",
                  "hd": { "width": 1024, "height": 1024, "framePattern": "frames_webp/fox_image_viewing_%04d.webp" }
                },
                "co_create": {
                  "version": "v2.0.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 48,
                  "width": 512,
                  "height": 512,
                  "path": "co_create/v2.0.0/",
                  "manifest": "co_create/v2.0.0/manifest.json",
                  "framePattern": "frames_webp/fox_co_create_%04d.webp",
                  "hd": { "width": 1024, "height": 1024, "framePattern": "frames_webp/fox_co_create_%04d.webp" }
                },
                "paused": {
                  "version": "v2.0.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 48,
                  "width": 512,
                  "height": 512,
                  "path": "paused/v2.0.0/",
                  "manifest": "paused/v2.0.0/manifest.json",
                  "framePattern": "frames_webp/fox_paused_%04d.webp",
                  "hd": { "width": 1024, "height": 1024, "framePattern": "frames_webp/fox_paused_%04d.webp" }
                },
                "retry": {
                  "version": "v2.0.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 48,
                  "width": 512,
                  "height": 512,
                  "path": "retry/v2.0.0/",
                  "manifest": "retry/v2.0.0/manifest.json",
                  "framePattern": "frames_webp/fox_retry_%04d.webp",
                  "hd": { "width": 1024, "height": 1024, "framePattern": "frames_webp/fox_retry_%04d.webp" }
                }
              },
              "statePriority": [
                "retry",
                "paused",
                "listening",
                "speaking",
                "preparing_speech",
                "thinking",
                "image_viewing",
                "co_create",
                "waiting_soft",
                "idle"
              ],
              "notes": "v2 mascot package: 512px WebP frame sequences, 10 states full mapping."
            }
        """
    }
}
