package com.childai.companion.ui.chat.languagegame

data class WordChainFoxStep(
    val promptWord: String,
    val foxWord: String,
    val startIndex: Int,
)

object WordChainWordBank {
    const val MaxRounds = 5

    val chains: List<List<String>> = listOf(
        listOf("苹果", "果汁", "汁水", "水池", "池塘", "塘边"),
        listOf("月亮", "亮光", "光点", "点心", "心愿", "愿望"),
        listOf("小猫", "猫毛", "毛笔", "笔盒", "盒饭", "饭团"),
        listOf("大树", "树枝", "枝条", "条纹", "纹路", "路灯"),
        listOf("水杯", "杯口", "口琴", "琴声", "声音", "音乐"),
    )

    val startWords: List<String> = chains.map { it.first() }

    fun startWordAt(index: Int): String {
        return chains[startIndexAt(index)].first()
    }

    fun nextStartIndex(index: Int): Int {
        return (startIndexAt(index) + 1).floorMod(chains.size)
    }

    fun firstStepForStartIndex(index: Int): WordChainFoxStep {
        val safeIndex = startIndexAt(index)
        val chain = chains[safeIndex]
        return WordChainFoxStep(
            promptWord = chain[0],
            foxWord = chain[1],
            startIndex = safeIndex,
        )
    }

    fun foxStepAfterChildWord(childWord: String, currentStartIndex: Int): WordChainFoxStep {
        val tail = childWord.lastEffectiveHanzi()
            ?: return firstStepForStartIndex(nextStartIndex(currentStartIndex))
        val matching = chains.withIndex().firstNotNullOfOrNull { indexed ->
            indexed.value.firstOrNull { word ->
                word.firstEffectiveHanzi() == tail && word != childWord
            }?.let { word ->
                WordChainFoxStep(
                    promptWord = childWord,
                    foxWord = word,
                    startIndex = indexed.index,
                )
            }
        }
        return matching ?: firstStepForStartIndex(nextStartIndex(currentStartIndex))
    }

    fun foxStepAfterPreviousWord(previousWord: String, currentStartIndex: Int): WordChainFoxStep {
        chains.withIndex().forEach { indexed ->
            val chain = indexed.value
            val position = chain.indexOf(previousWord)
            if (position >= 0 && position < chain.lastIndex) {
                return WordChainFoxStep(
                    promptWord = previousWord,
                    foxWord = chain[position + 1],
                    startIndex = indexed.index,
                )
            }
        }
        return firstStepForStartIndex(nextStartIndex(currentStartIndex))
    }

    fun lastCharOf(word: String): String {
        return word.lastEffectiveHanzi()?.toString().orEmpty()
    }

    fun approvedChildFacingCopy(): List<String> {
        return chains.flatten()
    }

    private fun startIndexAt(index: Int): Int {
        return index.floorMod(chains.size)
    }
}

internal fun String.firstEffectiveHanzi(): Char? {
    return firstOrNull { it.isCjkUnifiedIdeograph() && !it.isLeadingFillerHanzi() }
}

internal fun String.lastEffectiveHanzi(): Char? {
    return lastOrNull { it.isCjkUnifiedIdeograph() }
}

internal fun String.firstHanziSegment(): String {
    val builder = StringBuilder()
    var started = false
    for (char in this) {
        if (!started && char.isLeadingFillerHanzi()) {
            continue
        }
        if (char.isCjkUnifiedIdeograph()) {
            started = true
            builder.append(char)
        } else if (started) {
            break
        }
    }
    return builder.toString()
}

private fun Char.isCjkUnifiedIdeograph(): Boolean {
    return this in '\u4E00'..'\u9FFF'
}

private fun Char.isLeadingFillerHanzi(): Boolean {
    return this == '嗯' || this == '啊' || this == '呃' || this == '哦' || this == '唔' || this == '呀'
}

private fun Int.floorMod(modulus: Int): Int {
    return ((this % modulus) + modulus) % modulus
}
