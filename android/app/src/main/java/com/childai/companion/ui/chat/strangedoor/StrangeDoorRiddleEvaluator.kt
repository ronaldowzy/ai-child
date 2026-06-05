package com.childai.companion.ui.chat.strangedoor

data class StrangeDoorRiddleEvaluation(
    val isCorrect: Boolean,
    val feedbackLines: List<String>,
    val actionLabels: List<String>,
    val nextDemoState: StrangeDoorDemoState,
    val advanceSignal: StrangeDoorDoorAdvanceSignal,
)

object StrangeDoorRiddleEvaluator {
    const val QUESTION = "什么东西越洗越脏？"
    const val ANSWER = "水"
    const val ACTION_RETRY = "再答一次"
    const val ACTION_PHOTO = "找东西帮忙"

    private val correctFeedbackLines = listOf(
        "对，是水",
        "",
        "小门被你说得愣住了",
        "它低头想了三秒",
        "然后咔哒一下打开了",
    )

    private val wrongFeedbackLines = listOf(
        "这个答案有点勇敢",
        "小门差点相信了",
        "",
        "我给你一个提示",
        "它常常在杯子里、河里、盆里",
    )

    fun evaluate(answerText: String): StrangeDoorRiddleEvaluation {
        return if (isCorrectAnswer(answerText)) {
            StrangeDoorRiddleEvaluation(
                isCorrect = true,
                feedbackLines = correctFeedbackLines,
                actionLabels = emptyList(),
                nextDemoState = StrangeDoorDemoState.Completed,
                advanceSignal = StrangeDoorDoorAdvanceSignal.Open,
            )
        } else {
            StrangeDoorRiddleEvaluation(
                isCorrect = false,
                feedbackLines = wrongFeedbackLines,
                actionLabels = listOf(ACTION_RETRY, ACTION_PHOTO),
                nextDemoState = StrangeDoorDemoState.RiddleHint,
                advanceSignal = StrangeDoorDoorAdvanceSignal.None,
            )
        }
    }

    fun approvedChildFacingCopy(): List<String> {
        return listOf(QUESTION, ANSWER, ACTION_RETRY, ACTION_PHOTO) +
            correctFeedbackLines +
            wrongFeedbackLines
    }

    private fun isCorrectAnswer(answerText: String): Boolean {
        val normalized = answerText
            .replace(Regex("[\\s，。！？、,.!?]+"), "")
            .trim()
        return normalized.contains(ANSWER)
    }
}
