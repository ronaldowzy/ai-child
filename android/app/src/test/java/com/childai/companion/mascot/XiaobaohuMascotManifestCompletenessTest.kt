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
        assertEquals(MascotState.NetworkError, manifest.statePriority[2])
        assertTrue(manifest.statePriority.indexOf(MascotState.NetworkError) < manifest.statePriority.indexOf(MascotState.Speaking))
        assertTrue(manifest.statePriority.indexOf(MascotState.SafetyConcern) < manifest.statePriority.indexOf(MascotState.Speaking))
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

    private companion object {
        private const val MASCOT_MANIFEST_JSON = """
            {
              "mascot": "Little White Fox",
              "assetPackageVersion": "0.1.1-runtime-webp",
              "format": "webp_frame_sequence_runtime",
              "defaultFps": 12,
              "defaultState": "idle",
              "dimensions": [
                {
                  "width": 512,
                  "height": 512
                },
                {
                  "width": 512,
                  "height": 341
                }
              ],
              "states": {
                "safety_concern": {
                  "version": "v0.1.0",
                  "type": "oneshot_hold",
                  "fps": 12,
                  "frameCount": 24,
                  "width": 512,
                  "height": 341,
                  "path": "safety_concern/v0.1.0/",
                  "manifest": "safety_concern/v0.1.0/manifest.json",
                  "framePattern": "frames_webp/fox_safety_concern_%04d.webp"
                },
                "privacy_boundary": {
                  "version": "v0.1.0",
                  "type": "oneshot_hold",
                  "fps": 12,
                  "frameCount": 24,
                  "width": 512,
                  "height": 341,
                  "path": "privacy_boundary/v0.1.0/",
                  "manifest": "privacy_boundary/v0.1.0/manifest.json",
                  "framePattern": "frames_webp/fox_privacy_boundary_%04d.webp"
                },
                "network_error": {
                  "version": "v0.1.0",
                  "type": "oneshot_hold",
                  "fps": 12,
                  "frameCount": 24,
                  "width": 512,
                  "height": 341,
                  "path": "network_error/v0.1.0/",
                  "manifest": "network_error/v0.1.0/manifest.json",
                  "framePattern": "frames_webp/fox_network_error_%04d.webp"
                },
                "speaking": {
                  "version": "v0.1.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 24,
                  "width": 512,
                  "height": 341,
                  "path": "speaking/v0.1.0/",
                  "manifest": "speaking/v0.1.0/manifest.json",
                  "framePattern": "frames_webp/fox_speaking_%04d.webp"
                },
                "thinking": {
                  "version": "v0.1.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 24,
                  "width": 512,
                  "height": 341,
                  "path": "thinking/v0.1.0/",
                  "manifest": "thinking/v0.1.0/manifest.json",
                  "framePattern": "frames_webp/fox_thinking_%04d.webp"
                },
                "listening": {
                  "version": "v0.1.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 24,
                  "width": 512,
                  "height": 341,
                  "path": "listening/v0.1.0/",
                  "manifest": "listening/v0.1.0/manifest.json",
                  "framePattern": "frames_webp/fox_listening_%04d.webp"
                },
                "homework_focus": {
                  "version": "v0.1.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 24,
                  "width": 512,
                  "height": 341,
                  "path": "homework_focus/v0.1.0/",
                  "manifest": "homework_focus/v0.1.0/manifest.json",
                  "framePattern": "frames_webp/fox_homework_focus_%04d.webp"
                },
                "calm": {
                  "version": "v0.1.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 24,
                  "width": 512,
                  "height": 341,
                  "path": "calm/v0.1.0/",
                  "manifest": "calm/v0.1.0/manifest.json",
                  "framePattern": "frames_webp/fox_calm_%04d.webp"
                },
                "sleepy": {
                  "version": "v0.1.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 24,
                  "width": 512,
                  "height": 341,
                  "path": "sleepy/v0.1.0/",
                  "manifest": "sleepy/v0.1.0/manifest.json",
                  "framePattern": "frames_webp/fox_sleepy_%04d.webp"
                },
                "jumping_happy": {
                  "version": "v0.1.0",
                  "type": "short_loop",
                  "fps": 12,
                  "frameCount": 24,
                  "width": 512,
                  "height": 512,
                  "path": "jumping_happy/v0.1.0/",
                  "manifest": "jumping_happy/v0.1.0/manifest.json",
                  "framePattern": "frames_webp/fox_jumping_happy_%04d.webp"
                },
                "idle": {
                  "version": "v0.2.0",
                  "type": "loop",
                  "fps": 12,
                  "frameCount": 24,
                  "width": 512,
                  "height": 512,
                  "path": "idle/v0.2.0/",
                  "manifest": "idle/v0.2.0/manifest.json",
                  "framePattern": "frames_webp/fox_idle_%04d.webp"
                }
              },
              "statePriority": [
                "safety_concern",
                "privacy_boundary",
                "network_error",
                "speaking",
                "thinking",
                "listening",
                "homework_focus",
                "calm",
                "sleepy",
                "jumping_happy",
                "idle"
              ],
              "notes": "Runtime-only Little White Fox mascot package: 512px WebP frame sequences, one asset format per state."
            }
        """
    }
}
