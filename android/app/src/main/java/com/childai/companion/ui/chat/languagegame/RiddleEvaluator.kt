package com.childai.companion.ui.chat.languagegame

import com.childai.companion.ui.chat.localanswer.LocalAnswerMatcher

data class RiddleEvaluation(
    val isCorrect: Boolean,
)

object RiddleEvaluator {
    fun evaluate(
        transcript: String,
        question: RiddleQuestion,
    ): RiddleEvaluation {
        return RiddleEvaluation(
            isCorrect = LocalAnswerMatcher.containsAnswer(
                transcript = transcript,
                answer = question.answer,
                aliases = answerAliases[question.answer].orEmpty(),
            ),
        )
    }

    private val answerAliases = mapOf(
        "橘子" to setOf("juzi", "ju zi"),
        "云" to setOf("yun"),
        "书包" to setOf("shubao", "shu bao"),
        "铅笔" to setOf("qianbi", "qian bi"),
        "星星" to setOf("xingxing", "xing xing"),
    )
}
