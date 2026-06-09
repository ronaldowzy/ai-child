package com.childai.companion.ui.chat.languagegame

enum class LanguageGameActionId {
    CasualChat,
    OpenGameMenu,
    StartBrainTeaser,
    StartWordChain,
    StartVoiceAnswer,
    ShowHint,
    ChangeGame,
    ExitToChat,
    NextQuestion,
    GuessAgain,
    RevealAnswer,
    RestartWordChain,
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
                    id = LanguageGameActionId.StartWordChain,
                    label = "词语接龙",
                ),
                LanguageGameAction(
                    id = LanguageGameActionId.ExitToChat,
                    label = "先聊别的",
                ),
            ),
        )
        LanguageGameState.BrainTeaser -> brainTeaserUiModel(this)
        LanguageGameState.WordChain -> wordChainUiModel(this)
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
            "词语接龙",
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
            "我们玩词语接龙",
            "我先说一个词",
            "你接一个从“{lastChar}”开始的词就行",
            "接上啦",
            "“{previous}”接“{childWord}”",
            "这个小词跑得还挺快",
            "这个词也可以玩",
            "不过这次要从“{lastChar}”开始",
            "我给你换个容易的",
            "我来接一个",
            "“{previous}”接“{foxWord}”",
            "我们已经接了好多小词",
            "先让它们排队休息一下",
            "我来接",
            "再玩一次",
        ) + BrainTeaserQuestionBank.approvedChildFacingCopy() +
            WordChainWordBank.approvedChildFacingCopy()
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

private fun wordChainUiModel(snapshot: LanguageGameSnapshot): LanguageGameEntryUiModel {
    val wordChain = snapshot.wordChain ?: WordChainSnapshot()
    return when (wordChain.gameState) {
        WordChainGameState.Start,
        WordChainGameState.ChildTurn -> LanguageGameEntryUiModel(
            lines = wordChainStartLines(wordChain.previousWord),
            actions = wordChainAnswerActions(),
        )
        WordChainGameState.Correct,
        WordChainGameState.FoxTurn -> LanguageGameEntryUiModel(
            lines = wordChainCorrectLines(wordChain),
            actions = wordChainAnswerActions(),
        )
        WordChainGameState.Hint -> LanguageGameEntryUiModel(
            lines = wordChainHintLines(wordChain),
            actions = wordChainAnswerActions(),
        )
        WordChainGameState.Finished -> LanguageGameEntryUiModel(
            lines = listOf(
                "我们已经接了好多小词",
                "先让它们排队休息一下",
            ),
            actions = listOf(
                LanguageGameAction(
                    id = LanguageGameActionId.RestartWordChain,
                    label = "再玩一次",
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

private fun wordChainStartLines(previousWord: String): List<String> {
    return listOf(
        "我们玩词语接龙",
        "我先说一个词",
        previousWord,
        "你接一个从“${WordChainWordBank.lastCharOf(previousWord)}”开始的词就行",
    )
}

private fun wordChainCorrectLines(wordChain: WordChainSnapshot): List<String> {
    val promptWord = wordChain.promptWord ?: wordChain.previousWord
    val childWord = wordChain.childWord.orEmpty()
    return listOf(
        "接上啦",
        "“$promptWord”接“$childWord”",
        "这个小词跑得还挺快",
    ) + wordChainFoxLines(wordChain)
}

private fun wordChainHintLines(wordChain: WordChainSnapshot): List<String> {
    val promptWord = wordChain.promptWord ?: wordChain.previousWord
    return listOf(
        "这个词也可以玩",
        "不过这次要从“${WordChainWordBank.lastCharOf(promptWord)}”开始",
        "我给你换个容易的",
    ) + wordChainFoxLines(wordChain)
}

private fun wordChainFoxLines(wordChain: WordChainSnapshot): List<String> {
    val promptWord = wordChain.foxPromptWord ?: return emptyList()
    val foxWord = wordChain.foxWord ?: return emptyList()
    return listOf(
        "我来接一个",
        "“$promptWord”接“$foxWord”",
    )
}

private fun wordChainAnswerActions(): List<LanguageGameAction> {
    return listOf(
        LanguageGameAction(
            id = LanguageGameActionId.StartVoiceAnswer,
            label = "我来接",
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
    )
}
