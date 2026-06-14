package com.childai.companion.ui.chat.languagegame

import com.childai.companion.ui.chat.localanswer.LocalAnswerMatcher

data class BrainTeaserEvaluation(
    val isCorrect: Boolean,
)

object BrainTeaserEvaluator {
    fun evaluate(
        transcript: String,
        question: BrainTeaserQuestion,
    ): BrainTeaserEvaluation {
        return BrainTeaserEvaluation(
            isCorrect = LocalAnswerMatcher.containsAnswer(
                transcript = transcript,
                answer = question.answer,
                aliases = answerAliases[question.answer].orEmpty(),
            ),
        )
    }

    private val answerAliases = mapOf(
        "水" to setOf("shui"),
        "球门" to setOf("qiumen", "qiu men"),
        "路" to setOf("lu"),
        "傻瓜" to setOf("shagua", "sha gua"),
        "瀑布" to setOf("pubu", "pu bu"),
    )
}
