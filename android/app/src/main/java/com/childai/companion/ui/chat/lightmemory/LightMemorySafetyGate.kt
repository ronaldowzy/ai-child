package com.childai.companion.ui.chat.lightmemory

object LightMemorySafetyGate {
    val forbiddenFieldNames = setOf(
        "rawTranscript",
        "rawPhotoBytes",
        "recognizedText",
        "childAnswer",
        "score",
        "rank",
        "school",
        "address",
        "phone",
        "realName",
        "promptTrace",
    )

    private val blockedSourceTokens = listOf(
        "blocked",
        "privacy",
        "homework",
        "unsafe",
    )

    private val sensitiveContentKeywords = listOf(
        "隐私",
        "学习",
        "作业",
        "题目",
        "考试",
        "学校",
        "班级",
        "老师",
        "地址",
        "住址",
        "电话",
        "手机号",
        "手机号码",
        "真实姓名",
        "姓名",
        "身份证",
        "证件",
        "人脸",
        "脸",
        "医疗",
        "病历",
        "医院",
    )

    private val relatedChatKeywords = listOf(
        "小门",
        "奇怪小门",
        "小展台",
        "小发现",
        "刚才那个",
        "我放进去的",
        "帮小白狐",
    )

    fun acceptsCandidate(candidate: LightMemoryCandidate): Boolean {
        if (candidate.status == LightMemoryStatus.Blocked) return false
        if (blockedSourceTokens.any { candidate.safeLabel.contains(it, ignoreCase = true) }) return false
        return listOf(
            candidate.displayName,
            candidate.toolName,
            candidate.showcaseItemName,
            candidate.showcaseFoxQuote,
        ).none(::containsSensitiveContent)
    }

    fun safeTextOrNull(text: String?, maxLength: Int = 48): String? {
        val compact = text
            ?.replace(Regex("[\\r\\n\\t]+"), " ")
            ?.replace(Regex("\\s+"), " ")
            ?.trim()
            .orEmpty()
        if (compact.isBlank()) return null
        if (containsSensitiveContent(compact)) return null
        return compact.take(maxLength.coerceAtLeast(1))
    }

    fun containsSensitiveContent(text: String?): Boolean {
        val compact = text?.trim().orEmpty()
        if (compact.isBlank()) return false
        return sensitiveContentKeywords.any(compact::contains) ||
            forbiddenFieldNames.any { compact.contains(it, ignoreCase = true) }
    }

    fun isRelatedChatText(text: String): Boolean {
        return relatedChatKeywords.any(text::contains)
    }
}
