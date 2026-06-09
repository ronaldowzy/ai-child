package com.childai.companion.ui.chat.languagegame

enum class LanguageGameActionId {
    CasualChat,
    OpenGameMenu,
    StartBrainTeaser,
    StartVoiceAnswer,
    ShowHint,
    ChangeGame,
    ExitToChat,
    NextQuestion,
    GuessAgain,
    RevealAnswer,
}

data class LanguageGameAction(
    val id: LanguageGameActionId,
    val label: String,
    val primary: Boolean = false,
)

data class LanguageGameEntryUiModel(
    val lines: List<String>,
    val actions: List<LanguageGameAction>,
)

fun LanguageGameSnapshot.toLanguageGameEntryUiModel(): LanguageGameEntryUiModel {
    return when (state) {
        LanguageGameState.EntryPrompt -> LanguageGameEntryUiModel(
            lines = listOf(
                "我们随便聊聊天",
                "还是玩一个小游戏？",
            ),
            actions = listOf(
                LanguageGameAction(
                    id = LanguageGameActionId.CasualChat,
                    label = "随便聊聊",
                ),
                LanguageGameAction(
                    id = LanguageGameActionId.OpenGameMenu,
                    label = "玩个小游戏",
                    primary = true,
                ),
            ),
        )
        LanguageGameState.GameMenu -> LanguageGameEntryUiModel(
            lines = listOf("想玩哪一个？"),
            actions = listOf(
                LanguageGameAction(
                    id = LanguageGameActionId.StartBrainTeaser,
                    label = "脑筋急转弯",
                    primary = true,
                ),
                LanguageGameAction(
                    id = LanguageGameActionId.ExitToChat,
                    label = "先聊别的",
                ),
            ),
        )
        LanguageGameState.BrainTeaser -> brainTeaserUiModel(this)
    }
}

object LanguageGameApprovedCopy {
    fun approvedChildFacingCopy(): List<String> {
        return listOf(
            "我们随便聊聊天",
            "还是玩一个小游戏？",
            "随便聊聊",
            "玩个小游戏",
            "想玩哪一个？",
            "脑筋急转弯",
            "先聊别的",
            "对，就是{answer}",
            "这个答案有点绕",
            "小白狐刚才也差点没绕出来",
            "这个答案也有点意思",
            "不过这题的小机关不是它",
            "我给你一个提示",
            "{hint}",
            "我偷偷告诉你",
            "答案是{answer}",
            "是不是有点拐弯？",
            "我来答",
            "给我提示",
            "换个游戏",
            "下一题",
            "我再猜",
            "告诉我答案",
        ) + BrainTeaserQuestionBank.approvedChildFacingCopy()
    }
}

private fun brainTeaserUiModel(snapshot: LanguageGameSnapshot): LanguageGameEntryUiModel {
    val brainTeaser = snapshot.brainTeaser ?: BrainTeaserSnapshot()
    val question = BrainTeaserQuestionBank.questionAt(brainTeaser.questionIndex)
    return when (brainTeaser.gameState) {
        BrainTeaserGameState.Question -> LanguageGameEntryUiModel(
            lines = listOf(question.question),
            actions = listOf(
                LanguageGameAction(
                    id = LanguageGameActionId.StartVoiceAnswer,
                    label = "我来答",
                    primary = true,
                ),
                LanguageGameAction(
                    id = LanguageGameActionId.ShowHint,
                    label = "给我提示",
                ),
                LanguageGameAction(
                    id = LanguageGameActionId.ChangeGame,
                    label = "换个游戏",
                ),
                LanguageGameAction(
                    id = LanguageGameActionId.ExitToChat,
                    label = "先聊别的",
                ),
            ),
        )
        BrainTeaserGameState.Hint -> LanguageGameEntryUiModel(
            lines = listOf(
                "这个答案也有点意思",
                "不过这题的小机关不是它",
                "我给你一个提示",
                question.hint,
            ),
            actions = listOf(
                LanguageGameAction(
                    id = LanguageGameActionId.StartVoiceAnswer,
                    label = "我再猜",
                    primary = true,
                ),
                LanguageGameAction(
                    id = LanguageGameActionId.RevealAnswer,
                    label = "告诉我答案",
                ),
                LanguageGameAction(
                    id = LanguageGameActionId.ChangeGame,
                    label = "换个游戏",
                ),
                LanguageGameAction(
                    id = LanguageGameActionId.ExitToChat,
                    label = "先聊别的",
                ),
            ),
        )
        BrainTeaserGameState.Correct -> LanguageGameEntryUiModel(
            lines = listOf(
                "对，就是${question.answer}",
                "这个答案有点绕",
                "小白狐刚才也差点没绕出来",
            ),
            actions = listOf(
                LanguageGameAction(
                    id = LanguageGameActionId.NextQuestion,
                    label = "下一题",
                    primary = true,
                ),
                LanguageGameAction(
                    id = LanguageGameActionId.ChangeGame,
                    label = "换个游戏",
                ),
                LanguageGameAction(
                    id = LanguageGameActionId.ExitToChat,
                    label = "先聊别的",
                ),
            ),
        )
        BrainTeaserGameState.Revealed -> LanguageGameEntryUiModel(
            lines = listOf(
                "我偷偷告诉你",
                "答案是${question.answer}",
                "是不是有点拐弯？",
            ),
            actions = listOf(
                LanguageGameAction(
                    id = LanguageGameActionId.NextQuestion,
                    label = "下一题",
                    primary = true,
                ),
                LanguageGameAction(
                    id = LanguageGameActionId.ChangeGame,
                    label = "换个游戏",
                ),
                LanguageGameAction(
                    id = LanguageGameActionId.ExitToChat,
                    label = "先聊别的",
                ),
            ),
        )
    }
}
