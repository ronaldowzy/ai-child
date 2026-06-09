package com.childai.companion.ui.chat.languagegame

enum class LanguageGameState {
    EntryPrompt,
    GameMenu,
    BrainTeaser,
    WordChain,
    Riddle,
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

enum class WordChainGameState {
    Start,
    ChildTurn,
    Correct,
    Hint,
    FoxTurn,
    Finished,
}

enum class RiddleGameState {
    Question,
    Hint,
    Correct,
    Revealed,
}

data class BrainTeaserSnapshot(
    val questionIndex: Int = 0,
    val gameState: BrainTeaserGameState = BrainTeaserGameState.Question,
)

data class WordChainSnapshot(
    val startIndex: Int = 0,
    val previousWord: String = WordChainWordBank.startWordAt(startIndex),
    val roundIndex: Int = 0,
    val missCount: Int = 0,
    val gameState: WordChainGameState = WordChainGameState.Start,
    val promptWord: String? = null,
    val childWord: String? = null,
    val foxPromptWord: String? = null,
    val foxWord: String? = null,
)

data class RiddleSnapshot(
    val questionIndex: Int = 0,
    val gameState: RiddleGameState = RiddleGameState.Question,
)

data class LanguageGameSnapshot(
    val state: LanguageGameState = LanguageGameState.EntryPrompt,
    val selectedType: LanguageGameType? = null,
    val brainTeaser: BrainTeaserSnapshot? = null,
    val wordChain: WordChainSnapshot? = null,
    val riddle: RiddleSnapshot? = null,
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

    fun startWordChain(startIndex: Int = 0): LanguageGameSnapshot {
        val safeStartIndex = startIndex.coerceInWordChainBank()
        return LanguageGameSnapshot(
            state = LanguageGameState.WordChain,
            selectedType = LanguageGameType.WordChain,
            wordChain = WordChainSnapshot(
                startIndex = safeStartIndex,
                previousWord = WordChainWordBank.startWordAt(safeStartIndex),
                roundIndex = 0,
                missCount = 0,
                gameState = WordChainGameState.Start,
            ),
        )
    }

    fun startRiddle(questionIndex: Int = 0): LanguageGameSnapshot {
        return LanguageGameSnapshot(
            state = LanguageGameState.Riddle,
            selectedType = LanguageGameType.Riddle,
            riddle = RiddleSnapshot(
                questionIndex = questionIndex.coerceInRiddleBank(),
                gameState = RiddleGameState.Question,
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

    fun applyRiddleAnswer(
        snapshot: LanguageGameSnapshot,
        transcript: String,
    ): LanguageGameSnapshot {
        val riddle = snapshot.riddle ?: return snapshot
        val question = RiddleQuestionBank.questionAt(riddle.questionIndex)
        val result = RiddleEvaluator.evaluate(
            transcript = transcript,
            question = question,
        )
        return snapshot.withRiddleState(
            if (result.isCorrect) RiddleGameState.Correct else RiddleGameState.Hint,
        )
    }

    fun nextBrainTeaserQuestion(snapshot: LanguageGameSnapshot): LanguageGameSnapshot {
        val brainTeaser = snapshot.brainTeaser ?: return startBrainTeaser()
        return startBrainTeaser(
            questionIndex = BrainTeaserQuestionBank.nextIndex(brainTeaser.questionIndex),
        )
    }

    fun restartWordChain(snapshot: LanguageGameSnapshot): LanguageGameSnapshot {
        val wordChain = snapshot.wordChain ?: return startWordChain()
        return startWordChain(
            startIndex = WordChainWordBank.nextStartIndex(wordChain.startIndex),
        )
    }

    fun showRiddleHint(snapshot: LanguageGameSnapshot): LanguageGameSnapshot {
        return snapshot.withRiddleState(RiddleGameState.Hint)
    }

    fun revealRiddleAnswer(snapshot: LanguageGameSnapshot): LanguageGameSnapshot {
        return snapshot.withRiddleState(RiddleGameState.Revealed)
    }

    fun nextRiddleQuestion(snapshot: LanguageGameSnapshot): LanguageGameSnapshot {
        val riddle = snapshot.riddle ?: return startRiddle()
        return startRiddle(
            questionIndex = RiddleQuestionBank.nextIndex(riddle.questionIndex),
        )
    }

    fun applyWordChainAnswer(
        snapshot: LanguageGameSnapshot,
        transcript: String,
    ): LanguageGameSnapshot {
        val wordChain = snapshot.wordChain ?: return snapshot
        if (wordChain.gameState == WordChainGameState.Finished) return snapshot
        val evaluation = WordChainEvaluator.evaluate(
            transcript = transcript,
            previousWord = wordChain.previousWord,
        )
        return if (evaluation.isConnected) {
            snapshot.advanceWordChain(
                wordChain = wordChain,
                childWord = evaluation.childWord,
                foxStep = WordChainWordBank.foxStepAfterChildWord(
                    childWord = evaluation.childWord,
                    currentStartIndex = wordChain.startIndex,
                ),
                nextState = WordChainGameState.Correct,
            )
        } else {
            snapshot.handleWordChainMiss(
                wordChain = wordChain,
                childWord = evaluation.childWord,
            )
        }
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

    private fun LanguageGameSnapshot.withRiddleState(
        gameState: RiddleGameState,
    ): LanguageGameSnapshot {
        val riddle = riddle ?: RiddleSnapshot()
        return copy(
            state = LanguageGameState.Riddle,
            selectedType = LanguageGameType.Riddle,
            riddle = riddle.copy(gameState = gameState),
        )
    }

    private fun LanguageGameSnapshot.handleWordChainMiss(
        wordChain: WordChainSnapshot,
        childWord: String,
    ): LanguageGameSnapshot {
        val nextMissCount = wordChain.missCount + 1
        if (nextMissCount < 2) {
            return copy(
                state = LanguageGameState.WordChain,
                selectedType = LanguageGameType.WordChain,
                wordChain = wordChain.copy(
                    gameState = WordChainGameState.Hint,
                    missCount = nextMissCount,
                    promptWord = wordChain.previousWord,
                    childWord = childWord,
                    foxPromptWord = null,
                    foxWord = null,
                ),
            )
        }
        return advanceWordChain(
            wordChain = wordChain,
            childWord = childWord,
            foxStep = WordChainWordBank.foxStepAfterPreviousWord(
                previousWord = wordChain.previousWord,
                currentStartIndex = wordChain.startIndex,
            ),
            nextState = WordChainGameState.Hint,
        )
    }

    private fun LanguageGameSnapshot.advanceWordChain(
        wordChain: WordChainSnapshot,
        childWord: String,
        foxStep: WordChainFoxStep,
        nextState: WordChainGameState,
    ): LanguageGameSnapshot {
        val nextRoundIndex = wordChain.roundIndex + 1
        val nextWordChain = if (nextRoundIndex >= WordChainWordBank.MaxRounds) {
            wordChain.copy(
                startIndex = foxStep.startIndex,
                previousWord = foxStep.foxWord,
                roundIndex = nextRoundIndex,
                missCount = 0,
                gameState = WordChainGameState.Finished,
                promptWord = wordChain.previousWord,
                childWord = childWord,
                foxPromptWord = foxStep.promptWord,
                foxWord = foxStep.foxWord,
            )
        } else {
            wordChain.copy(
                startIndex = foxStep.startIndex,
                previousWord = foxStep.foxWord,
                roundIndex = nextRoundIndex,
                missCount = 0,
                gameState = nextState,
                promptWord = wordChain.previousWord,
                childWord = childWord,
                foxPromptWord = foxStep.promptWord,
                foxWord = foxStep.foxWord,
            )
        }
        return copy(
            state = LanguageGameState.WordChain,
            selectedType = LanguageGameType.WordChain,
            wordChain = nextWordChain,
        )
    }

    private fun Int.coerceInQuestionBank(): Int {
        val size = BrainTeaserQuestionBank.questions.size
        return if (size == 0) 0 else floorMod(size)
    }

    private fun Int.coerceInWordChainBank(): Int {
        val size = WordChainWordBank.chains.size
        return if (size == 0) 0 else floorMod(size)
    }

    private fun Int.coerceInRiddleBank(): Int {
        val size = RiddleQuestionBank.questions.size
        return if (size == 0) 0 else floorMod(size)
    }

    private fun Int.floorMod(modulus: Int): Int {
        return ((this % modulus) + modulus) % modulus
    }
}
