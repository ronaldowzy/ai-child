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
        assertEquals("按一下开始说", inputBarPrimaryVoiceButtonText(VoiceInputMode.Idle))
        assertEquals("说完了", inputBarPrimaryVoiceButtonText(VoiceInputMode.Listening))
        assertEquals(
            "正在听懂你说的话",
            inputBarPrimaryVoiceButtonText(VoiceInputMode.Uploading),
        )
        assertEquals("再说一次", inputBarPrimaryVoiceButtonText(VoiceInputMode.NeedsRetry))
        assertEquals(
            "请大人检查后再说",
            inputBarPrimaryVoiceButtonText(VoiceInputMode.Failed),
        )
        assertEquals(
            "请大人检查后再说",
            inputBarPrimaryVoiceButtonText(VoiceInputMode.PermissionDenied),
        )
    }
}
