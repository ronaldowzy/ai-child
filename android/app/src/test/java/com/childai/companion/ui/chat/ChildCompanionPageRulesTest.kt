package com.childai.companion.ui.chat

import org.junit.Assert.assertFalse
import org.junit.Test

class ChildCompanionPageRulesTest {
    @Test
    fun visibleCompanionCopyAvoidsForbiddenDirections() {
        val visibleCopy = listOf(
            childInteractionPresentation().statusText,
            childInteractionPresentation(
                voice = VoiceUiState(inputMode = VoiceInputMode.WaitingForChild),
            ).statusText,
            childInteractionPresentation(
                phaseHint = ChildTurnUiPhase.ImageProcessing,
            ).statusText,
            localImagePreviewStatusText(LocalImagePreviewStatus.Uploading),
            localImagePreviewStatusText(LocalImagePreviewStatus.Sent),
            parentEntryDefaultHint(),
            inputBarPrimaryVoiceButtonText(childInteractionPresentation()),
            childUiPolishStateLabel(ChildTurnUiPhase.Ready),
            childUiPolishStateLabel(ChildTurnUiPhase.Listening),
            childUiPolishStateLabel(ChildTurnUiPhase.ImageProcessing),
        )
        val forbidden = listOf(
            "上传文件",
            "立即开始",
            "完成任务",
            "今日挑战",
            "连续创作",
            "作品库",
            "故事库",
            "成长档案",
            "学习计划",
            "你怎么不说话",
            "明天继续",
            "轮到你了",
            "快说",
            "倒计时",
        )

        visibleCopy.forEach { copy ->
            forbidden.forEach { marker ->
                assertFalse("$copy should not contain $marker", copy.contains(marker))
            }
        }
    }
}
