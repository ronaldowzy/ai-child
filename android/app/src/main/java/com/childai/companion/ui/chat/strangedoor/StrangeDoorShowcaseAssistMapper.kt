package com.childai.companion.ui.chat.strangedoor

import com.childai.companion.data.showcase.XiaozhantaiItem
import com.childai.companion.data.showcase.xiaozhantaiDisplayName

data class StrangeDoorShowcaseAssistResult(
    val itemName: String,
    val doorEffect: String,
)

object StrangeDoorShowcaseAssistMapper {
    private const val AGAIN_SUFFIX = "又来帮忙啦"
    private const val FOX_PLACE_LINE = "小白狐把它轻轻放到门前"

    private val lightDoorEffects = listOf(
        "门上的圆锁轻轻转了一小下",
        "门缝里冒出一点暖风",
        "小门被它逗得晃了一下",
        "门边露出一条小小的缝",
        "圆锁像打哈欠一样松了一点",
        "小白狐往后退了一小步，又凑过去看",
    )

    fun map(item: XiaozhantaiItem): StrangeDoorShowcaseAssistResult {
        val itemName = xiaozhantaiDisplayName(item.name)
        return StrangeDoorShowcaseAssistResult(
            itemName = itemName,
            doorEffect = pickDoorEffect(seed = "${item.id}|$itemName"),
        )
    }

    fun feedbackLines(result: StrangeDoorShowcaseAssistResult): List<String> {
        return listOf(
            "${result.itemName} $AGAIN_SUFFIX",
            "",
            FOX_PLACE_LINE,
            result.doorEffect,
        )
    }

    fun approvedChildFacingCopy(): List<String> {
        return listOf(
            AGAIN_SUFFIX,
            FOX_PLACE_LINE,
        ) + lightDoorEffects
    }

    private fun pickDoorEffect(seed: String): String {
        val index = Math.floorMod(seed.hashCode(), lightDoorEffects.size)
        return lightDoorEffects[index]
    }
}
