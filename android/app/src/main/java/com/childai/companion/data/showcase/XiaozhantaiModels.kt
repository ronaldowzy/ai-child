package com.childai.companion.data.showcase

data class XiaozhantaiItem(
    val id: String,
    val photoUri: String,
    val name: String,
    val foxQuote: String,
    val createdAt: Long,
    val source: String = SOURCE_CHILD_CAMERA,
    val isDeleted: Boolean = false,
)

const val SOURCE_CHILD_CAMERA = "child_camera"

fun XiaozhantaiItem.isVisibleStandItem(): Boolean {
    return !isDeleted && id.isNotBlank() && photoUri.isNotBlank() && name.isNotBlank()
}

fun visibleXiaozhantaiItems(items: List<XiaozhantaiItem>): List<XiaozhantaiItem> {
    return items
        .filter { it.isVisibleStandItem() }
        .sortedByDescending { it.createdAt }
}

fun xiaozhantaiDisplayName(name: String, maxLength: Int = 12): String {
    val compact = name.trim().replace(Regex("\\s+"), " ")
    if (compact.length <= maxLength) return compact
    return compact.take(maxLength.coerceAtLeast(2) - 1) + "…"
}
