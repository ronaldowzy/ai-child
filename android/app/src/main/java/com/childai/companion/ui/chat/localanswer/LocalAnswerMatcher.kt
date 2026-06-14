package com.childai.companion.ui.chat.localanswer

import java.util.Locale

object LocalAnswerMatcher {
    fun containsAnswer(
        transcript: String,
        answer: String,
        aliases: Set<String> = emptySet(),
    ): Boolean {
        val normalizedTranscript = transcript.normalizedForLocalAnswer()
        if (normalizedTranscript.isBlank()) return false
        val candidates = aliases + answer
        return candidates.any { candidate ->
            val normalizedCandidate = candidate.normalizedForLocalAnswer()
            normalizedCandidate.isNotBlank() &&
                normalizedTranscript.contains(normalizedCandidate)
        }
    }

    fun firstHanziOrAlias(
        transcript: String,
        aliasesByChar: Map<Char, Set<String>>,
    ): Char? {
        val direct = transcript.firstOrNull { it.isCjkUnifiedIdeograph() }
        if (direct != null) return direct
        val normalizedTranscript = transcript.normalizedForLocalAnswer()
        if (normalizedTranscript.isBlank()) return null
        return aliasesByChar.entries.firstOrNull { (_, aliases) ->
            aliases.any { alias ->
                val normalizedAlias = alias.normalizedForLocalAnswer()
                normalizedAlias.isNotBlank() &&
                    normalizedTranscript.startsWith(normalizedAlias)
            }
        }?.key
    }

    fun String.normalizedForLocalAnswer(): String {
        return lowercase(Locale.ROOT)
            .filterNot { it.isWhitespace() || it.isCommonPunctuation() }
    }

    private fun Char.isCommonPunctuation(): Boolean {
        return this in listOf(
            '，',
            '。',
            '！',
            '？',
            '、',
            '；',
            '：',
            '“',
            '”',
            '‘',
            '’',
            ',',
            '.',
            '!',
            '?',
            ';',
            ':',
            '"',
            '\'',
            '（',
            '）',
            '(',
            ')',
            '《',
            '》',
            '<',
            '>',
            '【',
            '】',
            '[',
            ']',
            '{',
            '}',
        )
    }

    private fun Char.isCjkUnifiedIdeograph(): Boolean {
        return this in '\u4E00'..'\u9FFF'
    }
}
