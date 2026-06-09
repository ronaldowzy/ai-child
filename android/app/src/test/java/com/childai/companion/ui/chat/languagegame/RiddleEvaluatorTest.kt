package com.childai.companion.ui.chat.languagegame

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class RiddleEvaluatorTest {
    @Test
    fun transcriptContainingAnswerIsCorrect() {
        val result = RiddleEvaluator.evaluate(
            transcript = "我猜是橘子",
            question = RiddleQuestionBank.questions[0],
        )

        assertTrue(result.isCorrect)
    }

    @Test
    fun punctuationAndWhitespaceDoNotBlockOriginalAnswerMatch() {
        val result = RiddleEvaluator.evaluate(
            transcript = "我猜是  橘，子！",
            question = RiddleQuestionBank.questions[0],
        )

        assertTrue(result.isCorrect)
    }

    @Test
    fun synonymOrFeatureWordDoesNotCountAsCorrect() {
        val result = RiddleEvaluator.evaluate(
            transcript = "我觉得是水果",
            question = RiddleQuestionBank.questions[0],
        )

        assertFalse(result.isCorrect)
    }

    @Test
    fun emptyTranscriptGoesToHintPath() {
        val result = RiddleEvaluator.evaluate(
            transcript = "",
            question = RiddleQuestionBank.questions[0],
        )

        assertFalse(result.isCorrect)
    }
}
