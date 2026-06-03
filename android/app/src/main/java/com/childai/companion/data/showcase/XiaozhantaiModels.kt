package com.childai.companion.data.showcase

import org.json.JSONObject

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

data class XiaozhantaiSaveRequest(
    val childId: String,
    val photoBytes: ByteArray,
    val name: String,
    val foxQuote: String,
    val source: String = SOURCE_CHILD_CAMERA,
    val createdAt: Long? = null,
)

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

fun suggestedXiaozhantaiItemName(summary: String?): String {
    val compact = summary
        ?.replace(Regex("[\\r\\n\\t]+"), " ")
        ?.replace(Regex("\\s+"), " ")
        ?.trim()
        .orEmpty()
        .replace(
            Regex("^(我看到|看到)?(这张图|图片里|图里|画面里)?(有|像是|像)?(一个|一张|一只|一颗)?"),
            "",
        )
        .trim(' ', '。', '，', ',', '.', '啦')
    val keyword = Regex("[\\p{IsHan}A-Za-z0-9]{2,8}")
        .findAll(compact)
        .map { it.value }
        .firstOrNull { token ->
            token !in setOf("我看到", "看到", "这张图", "图片里", "图里", "一个", "一张", "像是")
        }
    return keyword?.take(8) ?: "小发现"
}

fun xiaozhantaiFoxQuoteFromReply(replyText: String): String {
    val compact = replyText
        .lineSequence()
        .map { it.trim() }
        .firstOrNull { it.isNotBlank() }
        .orEmpty()
        .ifBlank { "小白狐看见了这个小发现。" }
    return compact.take(80)
}

internal fun XiaozhantaiItem.toJson(): JSONObject {
    return JSONObject()
        .put("id", id)
        .put("photoUri", photoUri)
        .put("name", name)
        .put("foxQuote", foxQuote)
        .put("createdAt", createdAt)
        .put("source", source)
        .put("isDeleted", isDeleted)
}

internal fun xiaozhantaiItemFromJson(json: JSONObject): XiaozhantaiItem? {
    val id = json.optString("id").takeIf { it.isNotBlank() } ?: return null
    val photoUri = json.optString("photoUri").takeIf { it.isNotBlank() } ?: return null
    val name = json.optString("name").takeIf { it.isNotBlank() } ?: return null
    return XiaozhantaiItem(
        id = id,
        photoUri = photoUri,
        name = name,
        foxQuote = json.optString("foxQuote"),
        createdAt = json.optLong("createdAt", 0L),
        source = json.optString("source").ifBlank { SOURCE_CHILD_CAMERA },
        isDeleted = json.optBoolean("isDeleted", false),
    )
}
