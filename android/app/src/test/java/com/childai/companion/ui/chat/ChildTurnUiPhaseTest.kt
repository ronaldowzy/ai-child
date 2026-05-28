package com.childai.companion.ui.chat

import com.childai.companion.voice.TtsUiState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ChildTurnUiPhaseTest {
    @Test
    fun mapsReadyPhase() {
        val presentation = childInteractionPresentation()

        assertEquals(ChildTurnUiPhase.Ready, presentation.phase)
        assertEquals("小白狐在这里。", presentation.statusText)
        assertEquals("按一下开始说", presentation.primaryButtonText)
        assertTrue(presentation.primaryButtonEnabled)
    }

    @Test
    fun mapsListeningPhase() {
        val presentation = childInteractionPresentation(
            voice = VoiceUiState(inputMode = VoiceInputMode.Listening),
        )

        assertEquals(ChildTurnUiPhase.Listening, presentation.phase)
        assertEquals("我在听。", presentation.statusText)
        assertEquals("说完了", presentation.primaryButtonText)
        assertEquals(FoxMood.Listening, presentation.agent.mood)
    }

    @Test
    fun mapsWaitingForChildToLowPressureListeningCopy() {
        val presentation = childInteractionPresentation(
            voice = VoiceUiState(inputMode = VoiceInputMode.WaitingForChild),
        )

        assertEquals(ChildTurnUiPhase.Listening, presentation.phase)
        assertTrue(presentation.statusText.contains("我在听"))
        assertTrue(presentation.statusText.contains("想说的时候再说"))
        assertFalse(presentation.statusText.contains("轮到你了"))
        assertFalse(presentation.statusText.contains("快说"))
        assertFalse(presentation.statusText.contains("起个名字"))
        assertFalse(presentation.statusText.contains("小故事"))
    }

    @Test
    fun mapsRecognizingPhase() {
        val presentation = childInteractionPresentation(
            voice = VoiceUiState(inputMode = VoiceInputMode.Uploading),
            isSending = true,
        )

        assertEquals(ChildTurnUiPhase.Recognizing, presentation.phase)
        assertEquals("我在听懂刚才的话。", presentation.statusText)
        assertEquals("正在听懂", presentation.primaryButtonText)
        assertFalse(presentation.primaryButtonEnabled)
    }

    @Test
    fun mapsThinkingPhase() {
        val presentation = childInteractionPresentation(
            isSending = true,
        )

        assertEquals(ChildTurnUiPhase.Thinking, presentation.phase)
        assertEquals("我先想一想。", presentation.statusText)
        assertFalse(presentation.primaryButtonEnabled)
        assertEquals(FoxMood.Thinking, presentation.agent.mood)
    }

    @Test
    fun mapsSpeakingPhaseAndShowsStop() {
        val presentation = childInteractionPresentation(
            tts = TtsUiState(isSpeaking = true),
        )

        assertEquals(ChildTurnUiPhase.Speaking, presentation.phase)
        assertEquals("我在说给你听。", presentation.statusText)
        assertTrue(presentation.showStopSpeaking)
        assertTrue(presentation.showMuteToggle)
        assertEquals(FoxMotion.Speaking, presentation.agent.motion)
    }

    @Test
    fun mapsSpeakingPendingPhaseAndShowsStopAndMute() {
        val presentation = childInteractionPresentation(
            tts = TtsUiState(isSpeakingPending = true),
        )

        assertEquals(ChildTurnUiPhase.SpeakingPending, presentation.phase)
        assertEquals("小白狐在准备说。", presentation.statusText)
        assertTrue(presentation.showStopSpeaking)
        assertTrue(presentation.showMuteToggle)
        assertEquals("按一下开始说", presentation.primaryButtonText)
        assertTrue(presentation.primaryButtonEnabled)
    }

    @Test
    fun mapsImageProcessingPhaseToLookingStatus() {
        val presentation = childInteractionPresentation(
            phaseHint = ChildTurnUiPhase.ImageProcessing,
        )

        assertEquals(ChildTurnUiPhase.ImageProcessing, presentation.phase)
        assertEquals("小白狐正在看。", presentation.statusText)
        assertEquals(FoxMood.Thinking, presentation.agent.mood)
    }

    @Test
    fun mapsNeedsRetryPhase() {
        val presentation = childInteractionPresentation(
            voice = VoiceUiState(inputMode = VoiceInputMode.NeedsRetry),
        )

        assertEquals(ChildTurnUiPhase.NeedsRetry, presentation.phase)
        assertEquals("我刚才没听清，可以再说一次。", presentation.statusText)
        assertEquals("再说一次", presentation.primaryButtonText)
    }

    @Test
    fun mapsServiceErrorPhase() {
        val presentation = childInteractionPresentation(
            voice = VoiceUiState(inputMode = VoiceInputMode.Failed),
        )

        assertEquals(ChildTurnUiPhase.ServiceError, presentation.phase)
        assertEquals("我们先请大人检查一下。", presentation.statusText)
        assertEquals(FoxMood.NetworkError, presentation.agent.mood)
    }
}
