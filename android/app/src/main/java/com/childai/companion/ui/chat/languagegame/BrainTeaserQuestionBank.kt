package com.childai.companion.ui.chat.languagegame

data class BrainTeaserQuestion(
    val question: String,
    val answer: String,
    val hint: String,
)

object BrainTeaserQuestionBank {
    val questions: List<BrainTeaserQuestion> = listOf(
        BrainTeaserQuestion(
            question = "什么东西越洗越脏？",
            answer = "水",
            hint = "它常常在杯子里、河里、盆里",
        ),
        BrainTeaserQuestion(
            question = "什么门永远关不上？",
            answer = "球门",
            hint = "它常常在操场上",
        ),
        BrainTeaserQuestion(
            question = "什么东西越走越少？",
            answer = "路",
            hint = "你走过以后，它就被你走掉了一点点",
        ),
        BrainTeaserQuestion(
            question = "什么瓜不能吃？",
            answer = "傻瓜",
            hint = "它不是一种真的瓜",
        ),
        BrainTeaserQuestion(
            question = "什么布剪不断？",
            answer = "瀑布",
            hint = "它不是用来做衣服的布",
        ),
    )

    fun questionAt(index: Int): BrainTeaserQuestion {
        return questions[index.floorMod(questions.size)]
    }

    fun nextIndex(index: Int): Int {
        return (index + 1).floorMod(questions.size)
    }

    fun approvedChildFacingCopy(): List<String> {
        return questions.flatMap { question ->
            listOf(question.question, question.answer, question.hint)
        }
    }

    private fun Int.floorMod(modulus: Int): Int {
        return ((this % modulus) + modulus) % modulus
    }
}
