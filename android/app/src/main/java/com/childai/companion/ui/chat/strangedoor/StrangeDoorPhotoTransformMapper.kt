package com.childai.companion.ui.chat.strangedoor

data class StrangeDoorPhotoRecognition(
    val recognizedType: String,
    val recognizedText: String?,
    val confidence: Double,
)

enum class StrangeDoorShapeHint {
    Round,
    Partial,
    Unknown,
    Blocked,
}

data class StrangeDoorPhotoTransform(
    val objectName: String,
    val shapeHint: StrangeDoorShapeHint,
    val isUsable: Boolean,
    val transformedName: String?,
    val transformedAction: String?,
    val doorEffect: String?,
    val canSaveToShowcase: Boolean,
    val advanceSignal: StrangeDoorDoorAdvanceSignal,
) {
    val isGoodMatch: Boolean
        get() = shapeHint == StrangeDoorShapeHint.Round && isUsable
}

object StrangeDoorPhotoTransformMapper {
    const val DEFAULT_OBJECT_NAME = "这个小东西"
    const val NOT_SUITABLE_LINE_1 = "这张图不太适合变成开门道具"
    const val NOT_SUITABLE_LINE_2 = "我们换一个小东西试试"

    private const val LINE_SEE = "我看见了："
    private const val LINE_WORLD = "在小白狐的世界里"
    private const val LINE_TRANSFORMED = "它变成了："
    private const val TRANSFORM_ACTION_TURN = "把它轻轻一转"
    private const val FOX_ACTION_TURN = "小白狐把它轻轻一转"
    private const val DOOR_EFFECT_ROUND = "门上的圆锁咔哒一下松开了"
    private const val DOOR_EFFECT_KNOCK = "小门被敲得愣了一下"
    private const val DOOR_EFFECT_GAP = "露出了一条小缝"
    private const val DOOR_EFFECT_NOT_FULLY_OPEN = "门没有完全打开"
    private const val DOOR_EFFECT_SNEEZE = "但是它打了个喷嚏，露出一条小缝"

    private val blockedTypes = setOf(
        "privacy_sensitive",
        "unsafe_unknown",
        "homework_problem",
    )
    private val unsaveableTypes = blockedTypes + setOf(
        "unclear",
        "low_confidence",
    )
    private val roundKeywords = listOf(
        "蓝色瓶盖",
        "瓶盖",
        "盖子",
        "杯子",
        "球",
        "纽扣",
        "圆盘",
        "圆形",
    )
    private val partialKeywords = listOf(
        "铅笔",
        "弯弯",
        "半圆",
        "直直",
    )

    fun map(recognition: StrangeDoorPhotoRecognition): StrangeDoorPhotoTransform {
        val type = recognition.recognizedType.trim().lowercase()
        if (type in blockedTypes) {
            return StrangeDoorPhotoTransform(
                objectName = DEFAULT_OBJECT_NAME,
                shapeHint = StrangeDoorShapeHint.Blocked,
                isUsable = false,
                transformedName = null,
                transformedAction = null,
                doorEffect = null,
                canSaveToShowcase = false,
                advanceSignal = StrangeDoorDoorAdvanceSignal.None,
            )
        }

        val text = recognition.recognizedText.orEmpty()
        val objectName = extractObjectName(text)
        val shapeHint = shapeHintFor(text)
        val canSaveToShowcase = type !in unsaveableTypes && recognition.confidence >= 0.5
        return when (shapeHint) {
            StrangeDoorShapeHint.Round -> roundTransform(
                objectName = objectName,
                canSaveToShowcase = canSaveToShowcase,
            )
            StrangeDoorShapeHint.Partial -> partialTransform(
                objectName = objectName,
                canSaveToShowcase = canSaveToShowcase,
            )
            StrangeDoorShapeHint.Unknown -> unknownTransform(
                objectName = objectName,
                canSaveToShowcase = canSaveToShowcase,
            )
            StrangeDoorShapeHint.Blocked -> error("Blocked type should return early.")
        }
    }

    fun feedbackLines(transform: StrangeDoorPhotoTransform): List<String> {
        if (!transform.isUsable) {
            return listOf(NOT_SUITABLE_LINE_1, NOT_SUITABLE_LINE_2)
        }
        val transformedName = transform.transformedName ?: return emptyList()
        val lines = mutableListOf(
            "$LINE_SEE${transform.objectName}",
            LINE_WORLD,
            "$LINE_TRANSFORMED$transformedName",
        )
        if (transform.transformedAction == TRANSFORM_ACTION_TURN) {
            lines += FOX_ACTION_TURN
        }
        transform.doorEffect
            ?.split('\n')
            ?.filter { it.isNotBlank() }
            ?.let(lines::addAll)
        return lines
    }

    fun approvedChildFacingCopy(): List<String> {
        return listOf(
            DEFAULT_OBJECT_NAME,
            NOT_SUITABLE_LINE_1,
            NOT_SUITABLE_LINE_2,
            LINE_SEE,
            LINE_WORLD,
            LINE_TRANSFORMED,
            "小月亮盾牌",
            "半圆冲撞器",
            "咕噜圆盘",
            "蓝盖盖转轮",
            "软软开门垫",
            "星星小钥匙",
            "眨眼门铃",
            "圆滚滚按钮",
            "直直敲门棒",
            TRANSFORM_ACTION_TURN,
            FOX_ACTION_TURN,
            DOOR_EFFECT_ROUND,
            DOOR_EFFECT_KNOCK,
            DOOR_EFFECT_GAP,
            DOOR_EFFECT_NOT_FULLY_OPEN,
            DOOR_EFFECT_SNEEZE,
        )
    }

    private fun roundTransform(
        objectName: String,
        canSaveToShowcase: Boolean,
    ): StrangeDoorPhotoTransform {
        val transformedName = when {
            objectName.contains("瓶盖") || objectName.contains("盖子") -> "蓝盖盖转轮"
            objectName.contains("球") -> "圆滚滚按钮"
            objectName.contains("纽扣") -> "眨眼门铃"
            else -> "小月亮盾牌"
        }
        return StrangeDoorPhotoTransform(
            objectName = objectName,
            shapeHint = StrangeDoorShapeHint.Round,
            isUsable = true,
            transformedName = transformedName,
            transformedAction = TRANSFORM_ACTION_TURN,
            doorEffect = DOOR_EFFECT_ROUND,
            canSaveToShowcase = canSaveToShowcase,
            advanceSignal = StrangeDoorDoorAdvanceSignal.Open,
        )
    }

    private fun partialTransform(
        objectName: String,
        canSaveToShowcase: Boolean,
    ): StrangeDoorPhotoTransform {
        return StrangeDoorPhotoTransform(
            objectName = objectName,
            shapeHint = StrangeDoorShapeHint.Partial,
            isUsable = true,
            transformedName = if (objectName.contains("铅笔")) {
                "直直敲门棒"
            } else {
                "半圆冲撞器"
            },
            transformedAction = null,
            doorEffect = "$DOOR_EFFECT_KNOCK\n$DOOR_EFFECT_GAP",
            canSaveToShowcase = canSaveToShowcase,
            advanceSignal = StrangeDoorDoorAdvanceSignal.AdvanceOneStep,
        )
    }

    private fun unknownTransform(
        objectName: String,
        canSaveToShowcase: Boolean,
    ): StrangeDoorPhotoTransform {
        return StrangeDoorPhotoTransform(
            objectName = objectName,
            shapeHint = StrangeDoorShapeHint.Unknown,
            isUsable = true,
            transformedName = "软软开门垫",
            transformedAction = null,
            doorEffect = "$DOOR_EFFECT_NOT_FULLY_OPEN\n$DOOR_EFFECT_SNEEZE",
            canSaveToShowcase = canSaveToShowcase,
            advanceSignal = StrangeDoorDoorAdvanceSignal.AdvanceOneStep,
        )
    }

    private fun shapeHintFor(text: String): StrangeDoorShapeHint {
        val compact = text.trim()
        if (roundKeywords.any(compact::contains)) return StrangeDoorShapeHint.Round
        if (partialKeywords.any(compact::contains)) return StrangeDoorShapeHint.Partial
        return StrangeDoorShapeHint.Unknown
    }

    private fun extractObjectName(text: String): String {
        val compact = text
            .replace(Regex("[\\r\\n\\t]+"), " ")
            .replace(Regex("\\s+"), " ")
            .trim()
        if (compact.isBlank()) return DEFAULT_OBJECT_NAME

        roundKeywords.firstOrNull(compact::contains)?.let { keyword ->
            if (keyword == "蓝色瓶盖") return keyword
            if (keyword == "瓶盖" && compact.contains("蓝色瓶盖")) return "蓝色瓶盖"
            return keyword
        }
        partialKeywords.firstOrNull(compact::contains)?.let { keyword ->
            return if (keyword == "铅笔") "一支铅笔" else keyword
        }

        return compact
            .replace(
                Regex("^(我看到|看到)?(这张图|图片里|图里|画面里)?(有|像是|像)?(一个|一张|一只|一颗|一支)?"),
                "",
            )
            .trim(' ', '。', '，', ',', '.', '啦')
            .lineSequence()
            .firstOrNull()
            ?.take(12)
            ?.ifBlank { DEFAULT_OBJECT_NAME }
            ?: DEFAULT_OBJECT_NAME
    }
}
