package com.childai.companion.ui.chat.languagegame

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class LanguageGameEntryUiModelTest {
    @Test
    fun entryPromptUsesApprovedCopy() {
        val model = LanguageGameReducer.entryPrompt(autoPromptShown = true)
            .toLanguageGameEntryUiModel()

        assertEquals(
            listOf("我们随便聊聊天", "还是玩一个小游戏？"),
            model.lines,
        )
        assertEquals(
            listOf("随便聊聊", "玩个小游戏"),
            model.actions.map { it.label },
        )
    }

    @Test
    fun gameMenuShowsBrainTeaserWordChainAndExitThisRound() {
        val model = LanguageGameReducer.gameMenu().toLanguageGameEntryUiModel()

        assertEquals(listOf("想玩哪一个？"), model.lines)
        assertEquals(
            listOf("脑筋急转弯", "词语接龙", "先聊别的"),
            model.actions.map { it.label },
        )
        assertFalse(model.actions.any { it.label == "猜谜语" })
    }

    @Test
    fun wordChainStartUsesApprovedCopyAndButtons() {
        val model = LanguageGameReducer.startWordChain()
            .toLanguageGameEntryUiModel()

        assertEquals(
            listOf(
                "我们玩词语接龙",
                "我先说一个词",
                "苹果",
                "你接一个从“果”开始的词就行",
            ),
            model.lines,
        )
        assertEquals(
            listOf("我来接", "换个游戏", "先聊别的"),
            model.actions.map { it.label },
        )
    }

    @Test
    fun wordChainResultAndFinishedButtonsMatchApprovedOrder() {
        val correctModel = LanguageGameReducer.applyWordChainAnswer(
            snapshot = LanguageGameReducer.startWordChain(),
            transcript = "果汁",
        ).toLanguageGameEntryUiModel()

        assertEquals(
            listOf(
                "接上啦",
                "“苹果”接“果汁”",
                "这个小词跑得还挺快",
                "我来接一个",
                "“果汁”接“汁水”",
            ),
            correctModel.lines,
        )
        assertEquals(
            listOf("我来接", "换个游戏", "先聊别的"),
            correctModel.actions.map { it.label },
        )

        var snapshot = LanguageGameReducer.startWordChain()
        repeat(5) {
            snapshot = LanguageGameReducer.applyWordChainAnswer(
                snapshot = snapshot,
                transcript = snapshot.wordChain?.previousWord
                    ?.last()
                    ?.let { "$it" }
                    .orEmpty(),
            )
        }
        val finishedModel = snapshot.toLanguageGameEntryUiModel()

        assertEquals(
            listOf(
                "我们已经接了好多小词",
                "先让它们排队休息一下",
            ),
            finishedModel.lines,
        )
        assertEquals(
            listOf("再玩一次", "换个游戏", "先聊别的"),
            finishedModel.actions.map { it.label },
        )
    }

    @Test
    fun brainTeaserQuestionButtonsMatchApprovedOrder() {
        val model = LanguageGameReducer.startBrainTeaser()
            .toLanguageGameEntryUiModel()

        assertEquals(listOf("什么东西越洗越脏？"), model.lines)
        assertEquals(
            listOf("我来答", "给我提示", "换个游戏", "先聊别的"),
            model.actions.map { it.label },
        )
    }

    @Test
    fun hintRevealAndCorrectButtonsMatchApprovedOrder() {
        val hintModel = LanguageGameReducer.showBrainTeaserHint(
            LanguageGameReducer.startBrainTeaser(),
        ).toLanguageGameEntryUiModel()
        val correctModel = LanguageGameReducer.applyBrainTeaserAnswer(
            snapshot = LanguageGameReducer.startBrainTeaser(),
            transcript = "水",
        ).toLanguageGameEntryUiModel()
        val revealedModel = LanguageGameReducer.revealBrainTeaserAnswer(
            LanguageGameReducer.startBrainTeaser(),
        ).toLanguageGameEntryUiModel()

        assertEquals(
            listOf("我再猜", "告诉我答案", "换个游戏", "先聊别的"),
            hintModel.actions.map { it.label },
        )
        assertEquals(
            listOf("下一题", "换个游戏", "先聊别的"),
            correctModel.actions.map { it.label },
        )
        assertEquals(
            listOf("下一题", "换个游戏", "先聊别的"),
            revealedModel.actions.map { it.label },
        )
    }

    @Test
    fun approvedCopyDoesNotContainForbiddenWords() {
        val forbidden = listOf(
            "答错了",
            "不对",
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
            "考试",
            "错误",
            "闯关",
            "金币",
            "排名",
            "PK",
            "背诵",
            "默写",
            "纠错",
            "语法错误",
            "我没听懂",
        )

        LanguageGameApprovedCopy.approvedChildFacingCopy().forEach { copy ->
            forbidden.forEach { marker ->
                assertFalse("$copy should not contain $marker", copy.contains(marker))
            }
        }
        assertTrue(LanguageGameApprovedCopy.approvedChildFacingCopy().contains("答案是{answer}"))
    }
}
