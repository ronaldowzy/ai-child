package com.childai.companion.ui.chat.languagegame

import com.childai.companion.ui.chat.localanswer.LocalAnswerMatcher

data class WordChainEvaluation(
    val isConnected: Boolean,
    val expectedChar: String,
    val childWord: String,
)

object WordChainEvaluator {
    fun evaluate(
        transcript: String,
        previousWord: String,
    ): WordChainEvaluation {
        val expected = previousWord.lastEffectiveHanzi()
        val actual = transcript.firstEffectiveHanzi()
            ?: LocalAnswerMatcher.firstHanziOrAlias(transcript, firstCharAliases)
        return WordChainEvaluation(
            isConnected = expected != null && actual != null && expected == actual,
            expectedChar = expected?.toString().orEmpty(),
            childWord = transcript.firstHanziSegment().ifBlank {
                transcript.trim().take(12)
            },
        )
    }

    private val firstCharAliases = mapOf(
        '果' to setOf("guo"),
        '汁' to setOf("zhi"),
        '水' to setOf("shui"),
        '池' to setOf("chi"),
        '塘' to setOf("tang"),
        '亮' to setOf("liang"),
        '光' to setOf("guang"),
        '点' to setOf("dian"),
        '心' to setOf("xin"),
        '愿' to setOf("yuan"),
        '猫' to setOf("mao"),
        '毛' to setOf("mao"),
        '笔' to setOf("bi"),
        '盒' to setOf("he"),
        '饭' to setOf("fan"),
        '树' to setOf("shu"),
        '枝' to setOf("zhi"),
        '条' to setOf("tiao"),
        '纹' to setOf("wen"),
        '路' to setOf("lu"),
        '杯' to setOf("bei"),
        '口' to setOf("kou"),
        '琴' to setOf("qin"),
        '声' to setOf("sheng"),
        '音' to setOf("yin"),
    )
}
