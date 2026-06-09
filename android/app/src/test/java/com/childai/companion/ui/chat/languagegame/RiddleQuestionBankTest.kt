package com.childai.companion.ui.chat.languagegame

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class RiddleQuestionBankTest {
    @Test
    fun questionBankOnlyContainsApprovedFiveRiddles() {
        assertEquals(
            listOf(
                RiddleQuestion(
                    lines = listOf(
                        "小小房子圆又圆",
                        "里面住着甜甜水",
                    ),
                    answer = "橘子",
                    hint = "它是一种水果，剥开以后可以一瓣一瓣吃",
                ),
                RiddleQuestion(
                    lines = listOf(
                        "白白一片天上走",
                        "有时像羊有时像狗",
                    ),
                    answer = "云",
                    hint = "它在天上，会慢慢变形",
                ),
                RiddleQuestion(
                    lines = listOf(
                        "肚子大大装书本",
                        "每天跟你一起出门",
                    ),
                    answer = "书包",
                    hint = "上学或出门时，常常背在身上",
                ),
                RiddleQuestion(
                    lines = listOf(
                        "一根小棍黑又尖",
                        "走到纸上留下线",
                    ),
                    answer = "铅笔",
                    hint = "它可以在纸上画画写字",
                ),
                RiddleQuestion(
                    lines = listOf(
                        "晚上出来眨眼睛",
                        "天一亮就躲起来",
                    ),
                    answer = "星星",
                    hint = "它常常在夜晚的天上",
                ),
            ),
            RiddleQuestionBank.questions,
        )
    }

    @Test
    fun nextIndexLoopsAfterFifthQuestion() {
        assertEquals(0, RiddleQuestionBank.nextIndex(4))
        assertEquals(1, RiddleQuestionBank.nextIndex(0))
    }

    @Test
    fun approvedRiddleCopyDoesNotContainForbiddenWords() {
        val forbidden = listOf(
            "答错了",
            "不对",
            "错误",
            "正确答案",
            "你不会",
            "再认真一点",
            "分数",
            "等级",
            "奖励",
            "连续答对",
            "排行榜",
            "通关",
            "任务",
            "学习入口",
            "考试",
        )

        RiddleQuestionBank.approvedChildFacingCopy().forEach { copy ->
            forbidden.forEach { marker ->
                assertFalse("$copy should not contain $marker", copy.contains(marker))
            }
        }
    }
}
