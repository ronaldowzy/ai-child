package com.childai.companion.ui.chat.languagegame

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class WordChainEvaluatorTest {
    @Test
    fun matchingFirstHanziConnects() {
        val result = WordChainEvaluator.evaluate(
            transcript = "果汁",
            previousWord = "苹果",
        )

        assertTrue(result.isConnected)
        assertEquals("果", result.expectedChar)
        assertEquals("果汁", result.childWord)
    }

    @Test
    fun transcriptUsesFirstEffectiveHanziOnly() {
        val result = WordChainEvaluator.evaluate(
            transcript = "嗯，果冻也可以",
            previousWord = "苹果",
        )

        assertTrue(result.isConnected)
        assertEquals("果冻也可以", result.childWord)
    }

    @Test
    fun nonMatchingFirstHanziEntersHintPath() {
        val result = WordChainEvaluator.evaluate(
            transcript = "毛巾",
            previousWord = "苹果",
        )

        assertFalse(result.isConnected)
        assertEquals("果", result.expectedChar)
        assertEquals("毛巾", result.childWord)
    }

    @Test
    fun doesNotValidateWhetherTranscriptIsARealWord() {
        val result = WordChainEvaluator.evaluate(
            transcript = "果果果",
            previousWord = "苹果",
        )

        assertTrue(result.isConnected)
        assertEquals("果果果", result.childWord)
    }
}
