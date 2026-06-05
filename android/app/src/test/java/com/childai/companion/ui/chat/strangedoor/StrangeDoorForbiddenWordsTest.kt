package com.childai.companion.ui.chat.strangedoor

import org.junit.Assert.assertFalse
import org.junit.Test

class StrangeDoorForbiddenWordsTest {
    @Test
    fun approvedChildFacingCopyAvoidsTaskRewardAndRankingLanguage() {
        val forbiddenWords = listOf(
            "任务",
            "今日任务",
            "通关奖励",
            "获得道具",
            "装备",
            "战斗力",
            "稀有",
            "史诗",
            "S级",
            "抽卡",
            "宝箱",
            "排行榜",
            "积分",
            "连续打卡",
            "解锁奖励",
            "错了",
            "正确答案是",
            "这个很简单",
            "百宝箱",
            "图鉴",
            "背包",
            "通关",
        )
        val approvedCopy = StrangeDoorPhotoTransformMapper.approvedChildFacingCopy() +
            StrangeDoorRiddleEvaluator.approvedChildFacingCopy() +
            StrangeDoorHomeEventCopy.approvedChildFacingCopy()

        approvedCopy.forEach { line ->
            forbiddenWords.forEach { forbidden ->
                assertFalse(
                    "approved copy should not contain $forbidden: $line",
                    line.contains(forbidden),
                )
            }
        }
    }
}
