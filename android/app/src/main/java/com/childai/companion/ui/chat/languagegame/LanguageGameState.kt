package com.childai.companion.ui.chat.languagegame

enum class LanguageGameState {
    EntryPrompt,
    GameMenu,
    BrainTeaser,
}

enum class LanguageGameType {
    BrainTeaser,
    WordChain,
    Riddle,
}

enum class BrainTeaserGameState {
    Question,
    Hint,
    Correct,
    Revealed,
}

data class BrainTeaserSnapshot(
    val questionIndex: Int = 0,
    val gameState: BrainTeaserGameState = BrainTeaserGameState.Question,
)

data class LanguageGameSnapshot(
    val state: LanguageGameState = LanguageGameState.EntryPrompt,
    val selectedType: LanguageGameType? = null,
    val brainTeaser: BrainTeaserSnapshot? = null,
    val autoPromptShown: Boolean = false,
    val dismissedForLifecycle: Boolean = false,
)

object LanguageGameReducer {
    fun entryPrompt(autoPromptShown: Boolean): LanguageGameSnapshot {
        return LanguageGameSnapshot(
            state = LanguageGameState.EntryPrompt,
            autoPromptShown = autoPromptShown,
        )
    }

    fun gameMenu(): LanguageGameSnapshot {
        return LanguageGameSnapshot(state = LanguageGameState.GameMenu)
    }

    fun startBrainTeaser(questionIndex: Int = 0): LanguageGameSnapshot {
        return LanguageGameSnapshot(
            state = LanguageGameState.BrainTeaser,
            selectedType = LanguageGameType.BrainTeaser,
            brainTeaser = BrainTeaserSnapshot(
                questionIndex = questionIndex.coerceInQuestionBank(),
                gameState = BrainTeaserGameState.Question,
            ),
        )
    }

    fun showBrainTeaserHint(snapshot: LanguageGameSnapshot): LanguageGameSnapshot {
        return snapshot.withBrainTeaserState(BrainTeaserGameState.Hint)
    }

    fun revealBrainTeaserAnswer(snapshot: LanguageGameSnapshot): LanguageGameSnapshot {
        return snapshot.withBrainTeaserState(BrainTeaserGameState.Revealed)
    }

    fun applyBrainTeaserAnswer(
        snapshot: LanguageGameSnapshot,
        transcript: String,
    ): LanguageGameSnapshot {
        val brainTeaser = snapshot.brainTeaser ?: return snapshot
        val question = BrainTeaserQuestionBank.questionAt(brainTeaser.questionIndex)
        val result = BrainTeaserEvaluator.evaluate(
            transcript = transcript,
            question = question,
        )
        return snapshot.withBrainTeaserState(
            if (result.isCorrect) BrainTeaserGameState.Correct else BrainTeaserGameState.Hint,
        )
    }

    fun nextBrainTeaserQuestion(snapshot: LanguageGameSnapshot): LanguageGameSnapshot {
        val brainTeaser = snapshot.brainTeaser ?: return startBrainTeaser()
        return startBrainTeaser(
            questionIndex = BrainTeaserQuestionBank.nextIndex(brainTeaser.questionIndex),
        )
    }

    private fun LanguageGameSnapshot.withBrainTeaserState(
        gameState: BrainTeaserGameState,
    ): LanguageGameSnapshot {
        val brainTeaser = brainTeaser ?: BrainTeaserSnapshot()
        return copy(
            state = LanguageGameState.BrainTeaser,
            selectedType = LanguageGameType.BrainTeaser,
            brainTeaser = brainTeaser.copy(gameState = gameState),
        )
    }

    private fun Int.coerceInQuestionBank(): Int {
        val size = BrainTeaserQuestionBank.questions.size
        return if (size == 0) 0 else floorMod(size)
    }

    private fun Int.floorMod(modulus: Int): Int {
        return ((this % modulus) + modulus) % modulus
    }
}
