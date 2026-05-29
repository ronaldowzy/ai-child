package com.childai.companion.mascot

import android.content.res.AssetManager
import org.json.JSONObject
import java.io.File

class AssetManifestLoader(
    private val assetManager: AssetManager,
    private val rootPath: String = DEFAULT_ROOT_PATH,
) {
    fun loadManifestOrNull(): MascotManifest? {
        return runCatching {
            parseMascotManifest(readText("$rootPath/mascot_manifest.json"))
        }.getOrNull()
    }

    fun loadFrameSequenceOrNull(state: MascotState): FrameSequenceUiState? {
        val manifest = loadManifestOrNull() ?: return null
        return loadFrameSequenceOrNull(state, manifest)
    }

    fun loadFrameSequenceOrNull(
        state: MascotState,
        manifest: MascotManifest,
    ): FrameSequenceUiState? {
        val spec = manifest.states[state] ?: manifest.states[manifest.defaultState] ?: return null
        val stateManifest = runCatching {
            parseStateManifest(readText("$rootPath/${spec.manifestPath}"))
        }.getOrNull()
        val fps = stateManifest?.fps ?: spec.fps
        val frameCount = stateManifest?.frameCount ?: spec.frameCount
        val width = stateManifest?.width ?: spec.width
        val height = stateManifest?.height ?: spec.height
        val framePattern = stateManifest?.framePattern ?: spec.framePattern
        return FrameSequenceUiState(
            state = spec.state,
            animationType = spec.animationType,
            fps = fps.coerceAtLeast(1),
            width = width,
            height = height,
            framePaths = buildFramePaths(
                rootPath = rootPath,
                statePath = spec.path,
                framePattern = framePattern,
                frameCount = frameCount,
            ),
            assetVersion = manifest.assetPackageVersion,
        )
    }

    private fun readText(path: String): String {
        return assetManager.open(path).bufferedReader().use { it.readText() }
    }

    companion object {
        const val DEFAULT_ROOT_PATH = "mascot/xiaobaohu/v2"

        fun parseMascotManifest(rawJson: String): MascotManifest {
            val root = JSONObject(rawJson)
            val statesObject = root.getJSONObject("states")
            val states = buildMap {
                for (key in statesObject.keys()) {
                    val state = MascotState.fromId(key)
                    val item = statesObject.getJSONObject(key)
                    val hdObj = item.optJSONObject("hd")
                    put(
                        state,
                        MascotStateSpec(
                            state = state,
                            version = item.optString("version", ""),
                            animationType = MascotAnimationType.fromRaw(
                                item.optString("type", "loop"),
                            ),
                            fps = item.optInt("fps", root.optInt("defaultFps", 12)),
                            frameCount = item.optInt("frameCount", 1).coerceAtLeast(1),
                            width = item.optInt("width", 1024),
                            height = item.optInt("height", 1024),
                            path = item.getString("path").trimSlashes(),
                            manifestPath = item.getString("manifest").trimSlashes(),
                            framePattern = item.getString("framePattern"),
                            spritesheet = item.optString("spritesheet").takeIf {
                                it.isNotBlank()
                            },
                            hd = hdObj?.let { h ->
                                HdSpec(
                                    width = h.optInt("width", 1024),
                                    height = h.optInt("height", 1024),
                                    framePattern = h.optString("framePattern", item.getString("framePattern")),
                                )
                            },
                        ),
                    )
                }
            }
            val priorities = root.optJSONArray("statePriority")?.let { array ->
                buildList {
                    for (index in 0 until array.length()) {
                        add(MascotState.fromId(array.getString(index)))
                    }
                }
            }.orEmpty()
            return MascotManifest(
                mascot = root.optString("mascot", "Little White Fox"),
                assetPackageVersion = root.optString("assetPackageVersion", "unknown"),
                defaultFps = root.optInt("defaultFps", 12),
                defaultState = MascotState.fromId(root.optString("defaultState", "idle")),
                states = states,
                statePriority = priorities.ifEmpty { MascotStatePriority.fallbackOrder },
            )
        }

        fun parseStateManifest(rawJson: String): MascotStateManifest {
            val root = JSONObject(rawJson)
            val spritesheet = root.optJSONObject("spritesheet")
            return MascotStateManifest(
                state = MascotState.fromId(root.optString("state", "idle")),
                displayName = root.optString("displayName", root.optString("state", "idle")),
                version = root.optString("version", ""),
                sourceType = root.optString("type", "frame_sequence"),
                fps = root.optInt("fps", 12).coerceAtLeast(1),
                frameCount = root.optInt("frameCount", 1).coerceAtLeast(1),
                loop = root.optBoolean("loop", true),
                width = root.optInt("width", 1024),
                height = root.optInt("height", 1024),
                framePattern = root.getString("framePattern"),
                spritesheetFile = spritesheet?.optString("file")?.takeIf { it.isNotBlank() },
            )
        }

        fun buildFramePaths(
            rootPath: String,
            statePath: String,
            framePattern: String,
            frameCount: Int,
        ): List<String> {
            return (1..frameCount.coerceAtLeast(1)).map { frameNumber ->
                val frameName = framePattern.replace(
                    "%04d",
                    frameNumber.toString().padStart(4, '0'),
                )
                "${rootPath.trimEnd('/')}/${statePath.trimSlashes()}/$frameName"
            }
        }
    }
}

private fun String.trimSlashes(): String {
    return trimStart('/').trimEnd('/')
}
