package com.childai.companion.ui.chat.languagegame

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class BrainTeaserEvaluatorTest {
    @Test
    fun containsExactAnswerKeywordIsCorrect() {
        val question = BrainTeaserQuestionBank.questions.first()

        val result = BrainTeaserEvaluator.evaluate(
            transcript = "我觉得是水。",
            question = question,
        )

        assertTrue(result.isCorrect)
    }

    @Test
    fun nonMatchingAnswerIsNotCorrect() {
        val question = BrainTeaserQuestionBank.questions.first()

        val result = BrainTeaserEvaluator.evaluate(
            transcript = "毛巾",
            question = question,
        )

        assertFalse(result.isCorrect)
    }
}
