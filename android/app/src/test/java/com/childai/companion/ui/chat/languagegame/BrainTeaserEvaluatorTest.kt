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
    fun pinyinScriptForApprovedAnswerIsCorrect() {
        val result = BrainTeaserEvaluator.evaluate(
            transcript = "Shui。",
            question = BrainTeaserQuestionBank.questions.first(),
        )

        assertTrue(result.isCorrect)
    }

    @Test
    fun pinyinScriptForTwoCharacterApprovedAnswerIsCorrect() {
        val result = BrainTeaserEvaluator.evaluate(
            transcript = "qiumen",
            question = BrainTeaserQuestionBank.questions[1],
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
