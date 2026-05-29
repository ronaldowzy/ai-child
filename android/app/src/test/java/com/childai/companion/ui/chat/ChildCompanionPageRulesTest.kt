package com.childai.companion.ui.chat

import androidx.compose.ui.graphics.Color
import com.childai.companion.mascot.MascotState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
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

    @Test
    fun companionBackgroundUsesSoftGeneratedPalette() {
        assertEquals(
            listOf(
                Color(0xFFEDF4FF),
                Color(0xFFFFFDF8),
                Color(0xFFFFF2D8),
            ),
            companionPageBackgroundColors(),
        )
    }

    @Test
    fun mascotStateBubbleCopyUsesSingleApprovedStatusLine() {
        assertEquals("我在这里。", mascotStateBubbleText(MascotState.Idle))
        assertEquals("想说的时候再说。", mascotStateBubbleText(MascotState.WaitingSoft))
        assertEquals("我在听。", mascotStateBubbleText(MascotState.Listening))
        assertEquals("我想一想。", mascotStateBubbleText(MascotState.Thinking))
        assertEquals("我准备说。", mascotStateBubbleText(MascotState.PreparingSpeech))
        assertNull(mascotStateBubbleText(MascotState.Speaking))
        assertEquals("我正在看。", mascotStateBubbleText(MascotState.ImageViewing))
        assertEquals("我们一起想想。", mascotStateBubbleText(MascotState.CoCreate))
        assertEquals("好，我们先停一下。", mascotStateBubbleText(MascotState.Paused))
        assertEquals("这次没弄好，可以再试一次。", mascotStateBubbleText(MascotState.Retry))
    }

    @Test
    fun waitingBubbleDoesNotContainPressureCountdownOrCoCreationPrompt() {
        val waitingCopy = mascotStateBubbleText(MascotState.WaitingSoft).orEmpty()

        listOf(
            "倒计时",
            "轮到你了",
            "快说",
            "起个名字",
            "小故事",
            "不说也没关系",
        ).forEach { marker ->
            assertFalse(waitingCopy.contains(marker))
        }
    }
}
