package com.childai.companion.ui.chat

import androidx.compose.ui.graphics.Color
import com.childai.companion.mascot.MascotState
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoSnapshot
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
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
        assertEquals("我在这儿", mascotStateBubbleText(MascotState.Idle))
        assertEquals("想说再说", mascotStateBubbleText(MascotState.WaitingSoft))
        assertEquals("我在听", mascotStateBubbleText(MascotState.Listening))
        assertEquals("我想想", mascotStateBubbleText(MascotState.Thinking))
        assertEquals("我准备说", mascotStateBubbleText(MascotState.PreparingSpeech))
        assertNull(mascotStateBubbleText(MascotState.Speaking))
        assertEquals("我在看", mascotStateBubbleText(MascotState.ImageViewing))
        assertEquals("一起想想", mascotStateBubbleText(MascotState.CoCreate))
        assertEquals("先停一下", mascotStateBubbleText(MascotState.Paused))
        assertEquals("再试一次", mascotStateBubbleText(MascotState.Retry))

        MascotState.entries
            .mapNotNull { mascotStateBubbleText(it) }
            .forEach { copy ->
                assertFalse(copy.contains("。"))
            }
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

    @Test
    fun galleryPickerIsHiddenOnlyForKnownHonorPadFallback() {
        assertFalse(
            companionSupportsGalleryPicker(
                manufacturer = "HONOR",
                brand = "HONOR",
                model = "JDN2-W09HN",
            ),
        )
        assertFalse(
            companionSupportsGalleryPicker(
                manufacturer = "HONOR",
                brand = "HONOR",
                model = "Honor Pad 5",
            ),
        )
        assertEquals(
            true,
            companionSupportsGalleryPicker(
                manufacturer = "Xiaomi",
                brand = "Redmi",
                model = "Redmi K60",
            ),
        )
        assertEquals(
            true,
            companionSupportsGalleryPicker(
                manufacturer = "Google",
                brand = "google",
                model = "Pixel",
            ),
        )
    }

    @Test
    fun strangeDoorDemoDeemphasizesNormalInputBar() {
        assertTrue(strangeDoorShouldShowNormalInputBar(ChatUiState()))
        assertFalse(
            strangeDoorShouldShowNormalInputBar(
                ChatUiState(strangeDoorDemo = StrangeDoorDemoSnapshot()),
            ),
        )
    }

    @Test
    fun strangeDoorPhotoEntryUsesExistingShareImagePurpose() {
        assertEquals(IMAGE_PURPOSE_SHARE, strangeDoorPhotoCaptureImagePurpose())
        assertFalse(strangeDoorPhotoCaptureImagePurpose().contains("strange_door"))
    }
}
