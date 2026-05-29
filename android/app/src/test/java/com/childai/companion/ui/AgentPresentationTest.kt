package com.childai.companion.ui

import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.R
import com.childai.companion.ui.chat.FoxAgentAsset
import com.childai.companion.ui.chat.FoxAgentAssetMapper
import com.childai.companion.ui.chat.FoxAgentUiState
import com.childai.companion.ui.chat.FoxMood
import com.childai.companion.ui.chat.FoxMotion
import com.childai.companion.ui.chat.toFoxAgentUiState
import com.childai.companion.ui.chat.toVoiceUiState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AgentPresentationTest {
    @Test
    fun mapsReplyEmotionAndMotionToFoxState() {
        val reply = ConversationReply(
            type = "agent_message",
            text = "我在听。",
            voiceEnabled = true,
            audioUrl = null,
            emotion = "thinking",
            agentMotion = "thinking_blink",
        )

        val agent = reply.toFoxAgentUiState()

        assertEquals(FoxMood.Thinking, agent.mood)
        assertEquals(FoxMotion.ThinkingBlink, agent.motion)
        assertEquals("我想想", agent.statusText)
    }

    @Test
    fun keepsVoiceAsReservedWhenBackendHasNoAudioUrl() {
        val reply = ConversationReply(
            type = "agent_message",
            text = "我在听。",
            voiceEnabled = true,
            audioUrl = null,
            emotion = "warm",
            agentMotion = "gentle_idle",
        )

        val voice = reply.toVoiceUiState()

        assertTrue(voice.isVoiceInputReserved)
        assertFalse(voice.isTtsAvailable)
        assertEquals("按一下开始说", voice.statusText)
    }

    @Test
    fun marksTtsAvailableOnlyWhenAudioUrlIsPresent() {
        val reply = ConversationReply(
            type = "agent_message",
            text = "我在听。",
            voiceEnabled = true,
            audioUrl = "https://example.test/audio.mp3",
            emotion = "warm",
            agentMotion = "gentle_idle",
        )

        val voice = reply.toVoiceUiState()

        assertTrue(voice.isTtsAvailable)
        assertEquals("https://example.test/audio.mp3", voice.audioUrl)
        assertEquals("声音马上来", voice.statusText)
    }

    @Test
    fun mapsFoxStateToCandidatePngResource() {
        val asset = FoxAgentAssetMapper.resolve(
            agent = FoxAgentUiState(
                mood = FoxMood.Listening,
                motion = FoxMotion.ListeningTail,
            ),
        )

        assertEquals(FoxAgentAsset.Drawable(R.drawable.fox_3d_listening), asset)
    }

    @Test
    fun mapsSpeakingStateToSpeakingPngResource() {
        val asset = FoxAgentAssetMapper.resolve(
            agent = FoxAgentUiState(
                mood = FoxMood.Warm,
                motion = FoxMotion.Speaking,
            ),
        )

        assertEquals(FoxAgentAsset.Drawable(R.drawable.fox_3d_speaking), asset)
    }

    @Test
    fun mapsNewSceneMotionsToDedicatedFoxResources() {
        assertEquals(
            FoxAgentAsset.Drawable(R.drawable.fox_3d_homework_focus),
            FoxAgentAssetMapper.resolve(
                FoxAgentUiState(
                    mood = FoxMood.HomeworkFocus,
                    motion = FoxMotion.HomeworkFocus,
                ),
            ),
        )
        assertEquals(
            FoxAgentAsset.Drawable(R.drawable.fox_3d_sleepy),
            FoxAgentAssetMapper.resolve(
                FoxAgentUiState(
                    mood = FoxMood.Sleepy,
                    motion = FoxMotion.SleepyBlink,
                ),
            ),
        )
        assertEquals(
            FoxAgentAsset.Drawable(R.drawable.fox_3d_safety_concern),
            FoxAgentAssetMapper.resolve(
                FoxAgentUiState(
                    mood = FoxMood.SafetyConcern,
                    motion = FoxMotion.ConcernedStill,
                ),
            ),
        )
        assertEquals(
            FoxAgentAsset.Drawable(R.drawable.fox_3d_privacy_boundary),
            FoxAgentAssetMapper.resolve(
                FoxAgentUiState(
                    mood = FoxMood.PrivacyBoundary,
                    motion = FoxMotion.SteadyBoundary,
                ),
            ),
        )
        assertEquals(
            FoxAgentAsset.Drawable(R.drawable.fox_3d_network_error),
            FoxAgentAssetMapper.resolve(
                FoxAgentUiState(
                    mood = FoxMood.NetworkError,
                    motion = FoxMotion.NetworkError,
                ),
            ),
        )
    }

    @Test
    fun canForceCanvasFallbackForLowPerformanceMode() {
        val asset = FoxAgentAssetMapper.resolve(
            agent = FoxAgentUiState(
                mood = FoxMood.Encouraging,
                motion = FoxMotion.CelebrateSmall,
            ),
            assetMode = "canvas",
        )

        assertEquals(FoxAgentAsset.CanvasFallback, asset)
    }
}
