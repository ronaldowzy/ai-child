package com.childai.companion.ui.chat

import com.childai.companion.voice.TtsUiState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class InputBarVoiceFirstTest {
    @Test
    fun childVoiceFirstDefaultsHideTextInputPath() {
        assertTrue(
            inputBarUsesChildVoiceFirstInput(
                childVoiceFirstMode = true,
                showTextInputForChild = false,
                voiceConfirmBeforeSend = false,
            ),
        )
    }

    @Test
    fun devTextInputOrConfirmModeKeepsLegacyInputPath() {
        assertFalse(
            inputBarUsesChildVoiceFirstInput(
                childVoiceFirstMode = true,
                showTextInputForChild = true,
                voiceConfirmBeforeSend = false,
            ),
        )
        assertFalse(
            inputBarUsesChildVoiceFirstInput(
                childVoiceFirstMode = true,
                showTextInputForChild = false,
                voiceConfirmBeforeSend = true,
            ),
        )
    }

    @Test
    fun pendingTranscriptPanelIsHiddenInVoiceFirstMode() {
        assertFalse(
            inputBarShouldShowPendingTranscriptPanel(
                useChildVoiceFirstInput = true,
                hasPendingTranscript = true,
            ),
        )
        assertTrue(
            inputBarShouldShowPendingTranscriptPanel(
                useChildVoiceFirstInput = false,
                hasPendingTranscript = true,
            ),
        )
    }

    @Test
    fun primaryVoiceButtonLabelsMatchRecordingState() {
        assertEquals(
            "按一下开始说",
            inputBarPrimaryVoiceButtonText(childInteractionPresentation()),
        )
        assertEquals(
            "说完了",
            inputBarPrimaryVoiceButtonText(
                childInteractionPresentation(
                    voice = VoiceUiState(inputMode = VoiceInputMode.Listening),
                ),
            ),
        )
        assertEquals(
            "正在听懂",
            inputBarPrimaryVoiceButtonText(
                childInteractionPresentation(
                    voice = VoiceUiState(inputMode = VoiceInputMode.Uploading),
                ),
            ),
        )
        assertEquals(
            "再说一次",
            inputBarPrimaryVoiceButtonText(
                childInteractionPresentation(
                    voice = VoiceUiState(inputMode = VoiceInputMode.NeedsRetry),
                ),
            ),
        )
        assertEquals(
            "请大人帮忙看看",
            inputBarPrimaryVoiceButtonText(
                childInteractionPresentation(
                    voice = VoiceUiState(inputMode = VoiceInputMode.PermissionDenied),
                ),
            ),
        )
    }

    @Test
    fun ttsSpeakingPresentationShowsStopSpeaking() {
        val presentation = childInteractionPresentation(
            tts = TtsUiState(isSpeaking = true),
        )

        assertTrue(presentation.showStopSpeaking)
        assertTrue(presentation.showMuteToggle)
        assertEquals("按一下开始说", inputBarPrimaryVoiceButtonText(presentation))
        assertTrue(inputBarShouldShowMuteToggle(useChildVoiceFirstInput = true, presentation))
        assertEquals("静音", inputBarMuteToggleText(TtsUiState(isSpeaking = true)))
        assertEquals("打开朗读", inputBarMuteToggleText(TtsUiState(isMuted = true)))
    }

    @Test
    fun voiceFirstReadyDoesNotShowMuteToggle() {
        val presentation = childInteractionPresentation()

        assertFalse(inputBarShouldShowMuteToggle(useChildVoiceFirstInput = true, presentation))
    }
}
