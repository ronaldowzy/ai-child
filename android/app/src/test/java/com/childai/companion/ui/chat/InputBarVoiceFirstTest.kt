package com.childai.companion.ui.chat

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
            "请大人检查后再说",
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
            tts = com.childai.companion.voice.TtsUiState(isSpeaking = true),
        )

        assertTrue(presentation.showStopSpeaking)
        assertEquals("小白狐在说", inputBarPrimaryVoiceButtonText(presentation))
    }
}
