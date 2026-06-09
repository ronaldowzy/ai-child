package com.childai.companion.ui.chat.languagegame

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
        return WordChainEvaluation(
            isConnected = expected != null && actual != null && expected == actual,
            expectedChar = expected?.toString().orEmpty(),
            childWord = transcript.firstHanziSegment(),
        )
    }
}
