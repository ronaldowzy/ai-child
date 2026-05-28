package com.childai.companion.ui.chat

import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.voice.TtsCallbacks
import com.childai.companion.voice.TtsController
import com.childai.companion.voice.TtsRequest
import com.childai.companion.voice.TtsUiState
import com.childai.companion.voice.VoiceProfile
import com.childai.companion.voice.VoiceDiagnostics
import com.childai.companion.voice.AudioUrlPlayer
import com.childai.companion.voice.AudioUrlPlayerCallbacks
import com.childai.companion.voice.RemoteAudioTtsController
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.json.JSONObject

class ChatTtsViewModelTest {
    @Before
    fun setup() {
        Dispatchers.setMain(Dispatchers.Unconfined)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }
    @Test
    fun doesNotSpeakWhenReplyVoiceIsDisabled() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.renderAgentReply(response(reply(voiceEnabled = false)))

        assertTrue(fakeTts.requests.isEmpty())
        assertFalse(viewModel.uiState.value.tts.isSpeaking)
    }

    @Test
    fun doesNotSpeakWhenAutoReadIsDisabled() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(
            ttsController = fakeTts,
            initialTtsUiState = TtsUiState(isAutoReadEnabled = false),
        )

        viewModel.renderAgentReply(response(reply()))

        assertTrue(fakeTts.requests.isEmpty())
        assertFalse(viewModel.uiState.value.tts.isSpeaking)
    }

    @Test
    fun autoReadsAgentReplyAndSwitchesFoxToSpeaking() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.renderAgentReply(response(reply()))

        assertEquals(listOf("我在这里。"), fakeTts.requests.map { it.text })
        assertTrue(viewModel.uiState.value.tts.isSpeaking)
        assertEquals(FoxMotion.Speaking, viewModel.uiState.value.agent.motion)
    }

    @Test
    fun passesReplyAudioUrlToTtsController() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.renderAgentReply(response(reply(audioUrl = "/media/tts/fox.wav")))

        assertEquals("/media/tts/fox.wav", fakeTts.requests.single().audioUrl)
    }

    @Test
    fun acceptedTtsRequestShowsSpeakingPendingBeforePlatformStart() {
        val fakeTts = FakeTtsController(autoStart = false)
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.renderAgentReply(response(reply()))

        assertEquals(listOf("我在这里。"), fakeTts.requests.map { it.text })
        assertFalse(viewModel.uiState.value.tts.isSpeaking)
        assertTrue(viewModel.uiState.value.tts.isSpeakingPending)
        assertEquals(
            ChildTurnUiPhase.SpeakingPending,
            viewModel.uiState.value.interactionPresentation.phase,
        )
        assertTrue(viewModel.uiState.value.interactionPresentation.showStopSpeaking)
        assertEquals(FoxMotion.Speaking, viewModel.uiState.value.agent.motion)
        assertEquals("我在这里。", viewModel.uiState.value.tts.lastRequestedTextPreview)
    }

    @Test
    fun childMessageDoesNotTriggerTts() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.recordChildMessage("我想聊恐龙")

        assertTrue(fakeTts.requests.isEmpty())
        assertFalse(viewModel.uiState.value.tts.isSpeaking)
    }

    @Test
    fun mutedStatePreventsAutoRead() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.toggleTtsMuted()
        viewModel.renderAgentReply(response(reply(audioUrl = "/media/tts/fox.wav")))

        assertTrue(fakeTts.requests.isEmpty())
        assertTrue(viewModel.uiState.value.tts.isMuted)
        assertFalse(viewModel.uiState.value.tts.isSpeaking)
    }

    @Test
    fun newAgentReplyStopsPreviousPlaybackBeforeSpeaking() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.renderAgentReply(response(reply()))
        val stopCountAfterFirstReply = fakeTts.stopCount
        viewModel.renderAgentReply(response(reply(text = "新的回复。")))

        assertEquals(stopCountAfterFirstReply + 1, fakeTts.stopCount)
        assertEquals(listOf("我在这里。", "新的回复。"), fakeTts.requests.map { it.text })
        assertTrue(viewModel.uiState.value.tts.isSpeaking)
    }

    @Test
    fun stopRestoresBaseFoxState() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.renderAgentReply(
            response(
                reply(
                    emotion = "thinking",
                    agentMotion = "thinking_blink",
                ),
            ),
        )
        assertEquals(FoxMotion.Speaking, viewModel.uiState.value.agent.motion)
        val stopCountAfterAutoStart = fakeTts.stopCount

        viewModel.stopTtsPlayback()

        assertEquals(stopCountAfterAutoStart + 1, fakeTts.stopCount)
        assertFalse(viewModel.uiState.value.tts.isSpeaking)
        assertEquals(FoxMood.Thinking, viewModel.uiState.value.agent.mood)
        assertEquals(FoxMotion.ThinkingBlink, viewModel.uiState.value.agent.motion)
    }

    @Test
    fun finishRestoresBaseFoxState() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(
            ttsController = fakeTts,
            naturalWaitingEnabled = false,
        )

        viewModel.renderAgentReply(
            response(
                reply(
                    emotion = "encouraging",
                    agentMotion = "celebrate_small",
                ),
            ),
        )
        fakeTts.finish()

        assertFalse(viewModel.uiState.value.tts.isSpeaking)
        assertEquals(FoxMood.Encouraging, viewModel.uiState.value.agent.mood)
        assertEquals(FoxMotion.CelebrateSmall, viewModel.uiState.value.agent.motion)
    }

    @Test
    fun ttsUnavailableDoesNotCrashAndShowsGentleError() {
        val fakeTts = FakeTtsController(isAvailable = false)
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.renderAgentReply(response(reply()))

        assertFalse(viewModel.uiState.value.tts.isSpeaking)
        assertFalse(viewModel.uiState.value.tts.isAvailable)
        assertEquals(
            TtsController.UNAVAILABLE_MESSAGE,
            viewModel.uiState.value.tts.errorMessage,
        )
        assertEquals(
            "Fake TTS unavailable",
            viewModel.uiState.value.tts.lastFailureReason,
        )
    }

    @Test
    fun speakReturningFalseRestoresBaseStateAndRecordsFailureReason() {
        val fakeTts = FakeTtsController(acceptRequest = false)
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.renderAgentReply(
            response(
                reply(
                    emotion = "thinking",
                    agentMotion = "thinking_blink",
                ),
            ),
        )

        assertFalse(viewModel.uiState.value.tts.isSpeaking)
        assertFalse(viewModel.uiState.value.tts.isSpeakingPending)
        assertEquals(FoxMotion.ThinkingBlink, viewModel.uiState.value.agent.motion)
        assertEquals("Fake speak returned ERROR", viewModel.uiState.value.tts.lastFailureReason)
    }

    @Test
    fun voiceProfileDefaultUsesGentleChineseSettings() {
        val profile = VoiceProfile.default()

        assertEquals("zh-CN", profile.locale.toLanguageTag())
        assertTrue(profile.speechRate in 0.88f..0.95f)
        assertTrue(profile.pitch in 1.05f..1.15f)
        assertEquals(null, profile.preferredVoiceName)
    }

    @Test
    fun ttsUiStateExposesReadableDiagnostics() {
        val state = TtsUiState().withDiagnostics(
            VoiceDiagnostics(
                isAvailable = true,
                isInitialized = true,
                lastRequestedTextPreview = "我在这里。",
                selectedLocale = "zh-CN",
                selectedVoiceName = "fake-zh-cn",
                setLanguageResult = "LANG_COUNTRY_AVAILABLE",
                setVoiceResult = "SUCCESS",
                lastSpeakResult = "ERROR",
                enginePackageName = "fake.tts",
                lastFailureReason = "Fake failure",
                playbackSource = "remote_audio",
                audioUrl = "/media/tts/fox.wav",
            ),
        )

        assertTrue(state.diagnosticText.contains("engine=fake.tts"))
        assertTrue(state.diagnosticText.contains("speak=ERROR"))
        assertTrue(state.diagnosticText.contains("source=remote_audio"))
        assertTrue(state.diagnosticText.contains("audio=/media/tts/fox.wav"))
        assertEquals("Fake failure", state.lastFailureReason)
    }

    @Test
    fun ttsUiStateMarksSystemSetupWhenPlatformTtsIsUnavailable() {
        val state = TtsUiState().withDiagnostics(
            VoiceDiagnostics(
                isAvailable = false,
                isInitialized = false,
                lastSpeakResult = "SKIPPED_UNAVAILABLE",
                lastFailureReason = "TextToSpeech is unavailable",
            ),
        )

        assertTrue(state.needsSystemSetup)
        assertEquals(TtsController.UNAVAILABLE_MESSAGE, state.statusText)
    }

    @Test
    fun remoteAudioControllerPrefersAudioUrlOverSystemTts() {
        val fakePlayer = FakeAudioUrlPlayer()
        val fallbackTts = FakeTtsController()
        val controller = RemoteAudioTtsController(
            audioUrlPlayer = fakePlayer,
            fallbackController = fallbackTts,
            backendBaseUrl = "http://127.0.0.1:8000/",
        )
        var didStart = false

        val accepted = controller.speak(
            TtsRequest(text = "我在这里。", audioUrl = "/media/tts/fox.wav"),
            TtsCallbacks(onStart = { didStart = true }),
        )

        assertTrue(accepted)
        assertEquals(listOf("http://127.0.0.1:8000/media/tts/fox.wav"), fakePlayer.urls)
        assertTrue(fallbackTts.requests.isEmpty())
        assertTrue(didStart)
    }

    @Test
    fun remoteAudioControllerDoesNotFallbackToSystemTtsWhenPlaybackFails() {
        val fakePlayer = FakeAudioUrlPlayer(acceptRequest = false)
        val fallbackTts = FakeTtsController()
        val controller = RemoteAudioTtsController(
            audioUrlPlayer = fakePlayer,
            fallbackController = fallbackTts,
            backendBaseUrl = "http://127.0.0.1:8000/",
        )

        val accepted = controller.speak(
            TtsRequest(text = "我在这里。", audioUrl = "/media/tts/missing.wav"),
            TtsCallbacks(),
        )

        assertFalse(accepted)
        assertTrue(fallbackTts.requests.isEmpty())
    }

    @Test
    fun remoteAudioControllerDoesNotFallbackToSystemTtsWhenAudioUrlMissing() {
        val fakePlayer = FakeAudioUrlPlayer()
        val fallbackTts = FakeTtsController()
        val controller = RemoteAudioTtsController(
            audioUrlPlayer = fakePlayer,
            fallbackController = fallbackTts,
            backendBaseUrl = "http://127.0.0.1:8000/",
        )

        val accepted = controller.speak(
            TtsRequest(text = "我在这里。", audioUrl = null),
            TtsCallbacks(),
        )

        assertFalse(accepted)
        assertTrue(fakePlayer.urls.isEmpty())
        assertTrue(fallbackTts.requests.isEmpty())
    }

    @Test
    fun remoteAndSystemFailureKeepsGentleAudioPlaybackError() {
        val fakePlayer = FakeAudioUrlPlayer(acceptRequest = false)
        val controller = RemoteAudioTtsController(
            audioUrlPlayer = fakePlayer,
            fallbackController = FakeTtsController(isAvailable = false),
            backendBaseUrl = "http://127.0.0.1:8000/",
        )
        val viewModel = ChatViewModel(ttsController = controller)

        viewModel.renderAgentReply(response(reply(audioUrl = "/media/tts/missing.wav")))

        assertFalse(viewModel.uiState.value.tts.isSpeaking)
        assertEquals(
            TtsController.AUDIO_PLAYBACK_UNAVAILABLE_MESSAGE,
            viewModel.uiState.value.tts.errorMessage,
        )
    }

    @Test
    fun streamTtsErrorDoesNotUseSystemVoiceFallbackForSegment() {
        val fakeTts = FakeTtsController()
        val viewModel = ChatViewModel(ttsController = fakeTts)

        viewModel.applyStreamEvent(
            ConversationStreamEvent(
                type = "text_delta",
                payload = JSONObject().put("delta", "我看到这张图里有一个蓝色盒子。"),
            ),
        )
        viewModel.applyStreamEvent(
            ConversationStreamEvent(
                type = "error",
                payload = JSONObject()
                    .put("stage", "tts")
                    .put("text", "我看到这张图里有一个蓝色盒子。")
                    .put("safe_message", "这段朗读没有接上，文字还在这里。"),
            ),
        )

        assertTrue(fakeTts.requests.isEmpty())
        assertEquals(
            "这段朗读没有接上，文字还在这里。",
            viewModel.uiState.value.tts.errorMessage,
        )
    }

    @Test
    fun stopStopsRemoteAudioAndRestoresFoxState() {
        val fakePlayer = FakeAudioUrlPlayer()
        val controller = RemoteAudioTtsController(
            audioUrlPlayer = fakePlayer,
            fallbackController = FakeTtsController(),
            backendBaseUrl = "http://127.0.0.1:8000/",
        )
        val viewModel = ChatViewModel(ttsController = controller)

        viewModel.renderAgentReply(
            response(
                reply(
                    audioUrl = "/media/tts/fox.wav",
                    emotion = "thinking",
                    agentMotion = "thinking_blink",
                ),
            ),
        )
        val stopCountAfterRender = fakePlayer.stopCount
        viewModel.stopTtsPlayback()

        assertEquals(stopCountAfterRender + 1, fakePlayer.stopCount)
        assertFalse(viewModel.uiState.value.tts.isSpeaking)
        assertEquals(FoxMotion.ThinkingBlink, viewModel.uiState.value.agent.motion)
    }

    @Test
    fun relativeAudioUrlResolvesAgainstBackendBaseUrl() {
        assertEquals(
            "http://phone.local:8000/media/tts/fox.wav",
            RemoteAudioTtsController.resolveAudioUrl(
                audioUrl = "/media/tts/fox.wav",
                backendBaseUrl = "http://phone.local:8000/",
            ),
        )
        assertEquals(
            "https://cdn.example.test/audio.wav",
            RemoteAudioTtsController.resolveAudioUrl(
                audioUrl = "https://cdn.example.test/audio.wav",
                backendBaseUrl = "http://phone.local:8000/",
            ),
        )
    }

    private fun response(reply: ConversationReply): ConversationMessageResponse {
        return ConversationMessageResponse(
            reply = reply,
            uiActions = emptyList(),
            sessionState = ConversationSessionState(
                baseScene = "daily.after_school_checkin",
                activeScene = "daily.after_school_checkin",
                needsInput = null,
                requiresParentAttention = false,
            ),
        )
    }

    private fun reply(
        voiceEnabled: Boolean = true,
        text: String = "我在这里。",
        audioUrl: String? = null,
        emotion: String = "warm",
        agentMotion: String = "gentle_idle",
    ): ConversationReply {
        return ConversationReply(
            type = "agent_message",
            text = text,
            voiceEnabled = voiceEnabled,
            audioUrl = audioUrl,
            emotion = emotion,
            agentMotion = agentMotion,
        )
    }

    private class FakeTtsController(
        private val isAvailable: Boolean = true,
        private val autoStart: Boolean = true,
        private val acceptRequest: Boolean = true,
    ) : TtsController {
        val requests = mutableListOf<TtsRequest>()
        var stopCount = 0
        private var callbacks: TtsCallbacks? = null

        override fun speak(request: TtsRequest, callbacks: TtsCallbacks): Boolean {
            if (!isAvailable) {
                callbacks.onDiagnostics(
                    VoiceDiagnostics(
                        isAvailable = false,
                        isInitialized = false,
                        lastRequestedTextPreview = request.text,
                        lastFailureReason = "Fake TTS unavailable",
                        lastSpeakResult = "SKIPPED_UNAVAILABLE",
                    ),
                )
                callbacks.onError(TtsController.UNAVAILABLE_MESSAGE)
                return false
            }
            if (!acceptRequest) {
                callbacks.onDiagnostics(
                    VoiceDiagnostics(
                        isAvailable = true,
                        isInitialized = true,
                        lastRequestedTextPreview = request.text,
                        lastFailureReason = "Fake speak returned ERROR",
                        lastSpeakResult = "ERROR",
                    ),
                )
                callbacks.onError(TtsController.UNAVAILABLE_MESSAGE)
                return false
            }
            requests += request
            this.callbacks = callbacks
            callbacks.onDiagnostics(
                VoiceDiagnostics(
                    isAvailable = true,
                    isInitialized = true,
                    lastRequestedTextPreview = request.text,
                    selectedLocale = request.voiceProfile.locale.toLanguageTag(),
                    selectedVoiceName = "fake-zh-cn",
                    setLanguageResult = "LANG_COUNTRY_AVAILABLE",
                    setVoiceResult = "SUCCESS",
                    lastSpeakResult = "SUCCESS",
                    enginePackageName = "fake.tts",
                ),
            )
            if (autoStart) {
                callbacks.onStart()
            }
            return true
        }

        override fun stop() {
            stopCount += 1
            callbacks = null
        }

        override fun shutdown() {
            callbacks = null
        }

        fun finish() {
            callbacks?.onDone()
        }
    }

    private class FakeAudioUrlPlayer(
        private val acceptRequest: Boolean = true,
        private val autoStart: Boolean = true,
    ) : AudioUrlPlayer {
        val urls = mutableListOf<String>()
        var stopCount = 0
        private var callbacks: AudioUrlPlayerCallbacks? = null

        override fun play(url: String, callbacks: AudioUrlPlayerCallbacks): Boolean {
            urls += url
            if (!acceptRequest) {
                callbacks.onError("fake_remote_audio_failed")
                return false
            }
            this.callbacks = callbacks
            if (autoStart) {
                callbacks.onStart()
            }
            return true
        }

        override fun stop() {
            stopCount += 1
            callbacks = null
        }

        override fun release() {
            callbacks = null
        }
    }
}
