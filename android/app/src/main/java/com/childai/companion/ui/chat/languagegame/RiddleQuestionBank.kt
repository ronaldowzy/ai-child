package com.childai.companion.ui.chat.languagegame

data class RiddleQuestion(
    val lines: List<String>,
    val answer: String,
    val hint: String,
)

object RiddleQuestionBank {
    val questions: List<RiddleQuestion> = listOf(
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
    )

    fun questionAt(index: Int): RiddleQuestion {
        return questions[index.floorMod(questions.size)]
    }

    fun nextIndex(index: Int): Int {
        return (index + 1).floorMod(questions.size)
    }

    fun approvedChildFacingCopy(): List<String> {
        return questions.flatMap { question ->
            question.lines + question.answer + question.hint
        }
    }

    private fun Int.floorMod(modulus: Int): Int {
        return ((this % modulus) + modulus) % modulus
    }
}
