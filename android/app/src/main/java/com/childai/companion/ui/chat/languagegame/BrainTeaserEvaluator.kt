package com.childai.companion.ui.chat.languagegame

data class BrainTeaserEvaluation(
    val isCorrect: Boolean,
)

object BrainTeaserEvaluator {
    fun evaluate(
        transcript: String,
        question: BrainTeaserQuestion,
    ): BrainTeaserEvaluation {
        val normalizedTranscript = transcript.normalizedForBrainTeaser()
        val normalizedAnswer = question.answer.normalizedForBrainTeaser()
        return BrainTeaserEvaluation(
            isCorrect = normalizedAnswer.isNotBlank() &&
                normalizedTranscript.contains(normalizedAnswer),
        )
    }

    private fun String.normalizedForBrainTeaser(): String {
        return trim()
            .replace(Regex("[\\s，。！？、,.!?：:；;“”\"'（）()《》<>【】\\[\\]{}]"), "")
    }
}
