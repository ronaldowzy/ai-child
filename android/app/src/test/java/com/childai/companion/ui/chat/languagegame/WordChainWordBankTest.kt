package com.childai.companion.ui.chat.languagegame

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class WordChainWordBankTest {
    @Test
    fun wordBankOnlyContainsApprovedChains() {
        assertEquals(
            listOf(
                listOf("苹果", "果汁", "汁水", "水池", "池塘", "塘边"),
                listOf("月亮", "亮光", "光点", "点心", "心愿", "愿望"),
                listOf("小猫", "猫毛", "毛笔", "笔盒", "盒饭", "饭团"),
                listOf("大树", "树枝", "枝条", "条纹", "纹路", "路灯"),
                listOf("水杯", "杯口", "口琴", "琴声", "声音", "音乐"),
            ),
            WordChainWordBank.chains,
        )
    }

    @Test
    fun startWordsRotateInApprovedOrder() {
        assertEquals("苹果", WordChainWordBank.startWordAt(0))
        assertEquals("月亮", WordChainWordBank.startWordAt(1))
        assertEquals("小猫", WordChainWordBank.startWordAt(2))
        assertEquals("大树", WordChainWordBank.startWordAt(3))
        assertEquals("水杯", WordChainWordBank.startWordAt(4))
        assertEquals("苹果", WordChainWordBank.startWordAt(5))
    }

    @Test
    fun foxStepUsesApprovedPoolAndFallsBackWithoutInventingWords() {
        val matching = WordChainWordBank.foxStepAfterChildWord(
            childWord = "果汁",
            currentStartIndex = 0,
        )
        assertEquals("果汁", matching.promptWord)
        assertEquals("汁水", matching.foxWord)

        val fallback = WordChainWordBank.foxStepAfterChildWord(
            childWord = "山山",
            currentStartIndex = 0,
        )
        assertEquals("月亮", fallback.promptWord)
        assertEquals("亮光", fallback.foxWord)
        assertEquals(1, fallback.startIndex)
    }

    @Test
    fun approvedWordChainCopyDoesNotContainForbiddenWords() {
        val forbidden = listOf(
            "答错了",
            "不对",
            "错误",
            "正确答案",
            "分数",
            "等级",
            "奖励",
            "连续答对",
            "排行榜",
            "通关",
            "任务",
            "学习入口",
            "你不会",
            "再认真一点",
        )

        WordChainWordBank.approvedChildFacingCopy().forEach { copy ->
            forbidden.forEach { marker ->
                assertFalse("$copy should not contain $marker", copy.contains(marker))
            }
        }
    }
}
