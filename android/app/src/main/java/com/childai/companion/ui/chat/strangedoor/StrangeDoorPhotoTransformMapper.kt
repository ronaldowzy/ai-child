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
    private const val DOOR_EFFECT_LIGHT_TURN = "门上的圆锁轻轻转了一小下"
    private const val DOOR_EFFECT_WARM_WIND = "门缝里冒出一点暖风"
    private const val DOOR_EFFECT_WOBBLE = "小门被它逗得晃了一下"
    private const val DOOR_EFFECT_TINY_GAP = "门边露出一条小小的缝"
    private const val DOOR_EFFECT_YAWN = "圆锁像打哈欠一样松了一点"
    private const val DOOR_EFFECT_FOX_LOOK = "小白狐往后退了一小步，又凑过去看"
    private const val DOOR_EFFECT_NOT_FULLY_OPEN = "小门没有完全打开"
    private const val DOOR_EFFECT_SNEEZE = "但是它打了个喷嚏，露出一条小缝"
    private const val DOOR_EFFECT_THINK = "小门歪着想了想，好像有点相信"
    private const val DOOR_EFFECT_ODD = "这个东西有点奇怪，小门看了好久"
    private const val DOOR_EFFECT_FOX_TRY = "小白狐说：也许可以试试"
    private const val DOOR_EFFECT_OPEN_CLICK = "小门终于咔哒一下打开了"
    private const val DOOR_EFFECT_OPEN_WIND = "门后面有一点暖暖的风"
    private const val DOOR_EFFECT_OPEN_LIGHT = "小白狐轻轻走过去，看见了一点光"

    private val blockedTypes = setOf(
        "privacy_sensitive",
        "unsafe_unknown",
        "homework_problem",
    )
    private val blockedTextKeywords = listOf(
        "人脸",
        "学校",
        "地址",
        "证件",
        "隐私",
        "医疗",
        "暴力",
        "惊吓",
        "作业",
        "题目",
        "学习",
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
        "勺",
        "纸",
        "垫",
        "杆",
        "棒",
        "弯弯",
        "半圆",
        "直直",
    )
    private val roundToolNames = listOf(
        "小月亮盾牌",
        "蓝盖盖转轮",
        "咕噜圆盘",
        "圆滚滚按钮",
        "眨眼门铃",
        "杯口小旋风",
        "纽扣小眼睛",
        "圆圆开门盘",
        "小饼干转轮",
        "月亮小按钮",
    )
    private val partialToolNames = listOf(
        "半圆冲撞器",
        "直直敲门棒",
        "弯弯撬门勺",
        "纸角小铲子",
        "软软开门垫",
        "歪歪小推板",
        "瘦长敲敲杆",
        "小斜坡垫子",
    )
    private val unknownToolNames = listOf(
        "这个小东西",
        "迷糊开门垫",
        "软软试试看",
        "小小帮忙块",
        "糊糊门铃",
    )
    private val lightDoorEffects = listOf(
        DOOR_EFFECT_LIGHT_TURN,
        DOOR_EFFECT_WARM_WIND,
        DOOR_EFFECT_WOBBLE,
        DOOR_EFFECT_TINY_GAP,
        DOOR_EFFECT_YAWN,
        DOOR_EFFECT_FOX_LOOK,
    )
    private val oddDoorEffects = listOf(
        DOOR_EFFECT_NOT_FULLY_OPEN,
        DOOR_EFFECT_SNEEZE,
        DOOR_EFFECT_THINK,
        DOOR_EFFECT_ODD,
        DOOR_EFFECT_FOX_TRY,
    )
    private val openDoorEffects = listOf(
        DOOR_EFFECT_OPEN_CLICK,
        DOOR_EFFECT_OPEN_WIND,
        DOOR_EFFECT_OPEN_LIGHT,
    )

    fun map(recognition: StrangeDoorPhotoRecognition): StrangeDoorPhotoTransform {
        val type = recognition.recognizedType.trim().lowercase()
        val text = recognition.recognizedText.orEmpty()
        if (type in blockedTypes || blockedTextKeywords.any(text::contains)) {
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

    fun feedbackLines(
        transform: StrangeDoorPhotoTransform,
        doorState: StrangeDoorState? = null,
    ): List<String> {
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
        val doorEffect = if (doorState == StrangeDoorState.Open) {
            openDoorEffects.joinToString(separator = "\n")
        } else {
            transform.doorEffect
        }
        doorEffect
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
            TRANSFORM_ACTION_TURN,
            FOX_ACTION_TURN,
        ) + roundToolNames + partialToolNames + unknownToolNames + lightDoorEffects + oddDoorEffects + openDoorEffects
    }

    private fun roundTransform(
        objectName: String,
        canSaveToShowcase: Boolean,
    ): StrangeDoorPhotoTransform {
        val transformedName = when {
            objectName.contains("瓶盖") || objectName.contains("盖子") -> "蓝盖盖转轮"
            objectName.contains("杯") -> "杯口小旋风"
            objectName.contains("球") -> "咕噜圆盘"
            objectName.contains("纽扣") -> "纽扣小眼睛"
            objectName.contains("饼干") -> "小饼干转轮"
            objectName.contains("圆盘") || objectName.contains("圆形") -> "圆圆开门盘"
            else -> "小月亮盾牌"
        }
        return StrangeDoorPhotoTransform(
            objectName = objectName,
            shapeHint = StrangeDoorShapeHint.Round,
            isUsable = true,
            transformedName = transformedName,
            transformedAction = TRANSFORM_ACTION_TURN,
            doorEffect = DOOR_EFFECT_LIGHT_TURN,
            canSaveToShowcase = canSaveToShowcase,
            advanceSignal = StrangeDoorDoorAdvanceSignal.AdvanceOneStep,
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
            transformedName = partialToolNameFor(objectName),
            transformedAction = null,
            doorEffect = "$DOOR_EFFECT_TINY_GAP\n$DOOR_EFFECT_THINK",
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
            transformedName = if (objectName == DEFAULT_OBJECT_NAME) {
                DEFAULT_OBJECT_NAME
            } else {
                pickFrom(unknownToolNames, objectName)
            },
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

    private fun partialToolNameFor(objectName: String): String {
        return when {
            objectName.contains("铅笔") || objectName.contains("直直") || objectName.contains("棒") -> "直直敲门棒"
            objectName.contains("弯弯") || objectName.contains("勺") -> "弯弯撬门勺"
            objectName.contains("纸") -> "纸角小铲子"
            objectName.contains("垫") -> "软软开门垫"
            objectName.contains("杆") -> "瘦长敲敲杆"
            objectName.contains("半圆") -> "半圆冲撞器"
            else -> pickFrom(partialToolNames, objectName)
        }
    }

    private fun pickFrom(pool: List<String>, seed: String): String {
        val index = seed.hashCode().floorMod(pool.size)
        return pool[index]
    }

    private fun Int.floorMod(divisor: Int): Int {
        return ((this % divisor) + divisor) % divisor
    }
}
