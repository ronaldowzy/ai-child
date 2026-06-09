package com.childai.companion.ui.chat.languagegame

data class RiddleEvaluation(
    val isCorrect: Boolean,
)

object RiddleEvaluator {
    fun evaluate(
        transcript: String,
        question: RiddleQuestion,
    ): RiddleEvaluation {
        val normalizedTranscript = transcript.normalizedForRiddle()
        val normalizedAnswer = question.answer.normalizedForRiddle()
        return RiddleEvaluation(
            isCorrect = normalizedAnswer.isNotBlank() &&
                normalizedTranscript.contains(normalizedAnswer),
        )
    }

    private fun String.normalizedForRiddle(): String {
        return filterNot { it.isWhitespace() || it.isCommonPunctuation() }
    }

    private fun Char.isCommonPunctuation(): Boolean {
        return this in listOf(
            '，',
            '。',
            '！',
            '？',
            '、',
            '；',
            '：',
            '“',
            '”',
            '‘',
            '’',
            ',',
            '.',
            '!',
            '?',
            ';',
            ':',
            '"',
            '\'',
        )
    }
}
