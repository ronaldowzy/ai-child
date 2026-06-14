package com.childai.companion.ui.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childai.companion.config.DevSettings
import com.childai.companion.data.attachment.AttachmentCreateResponse
import com.childai.companion.data.attachment.AttachmentRepository
import com.childai.companion.data.attachment.PhotoUploadPayload
import com.childai.companion.data.conversation.CompanionObjectMeta
import com.childai.companion.data.conversation.ConversationMessageResponse
import com.childai.companion.data.conversation.ConversationRepository
import com.childai.companion.data.conversation.ConversationReply
import com.childai.companion.data.conversation.ConversationSessionState
import com.childai.companion.data.conversation.ConversationStreamEvent
import com.childai.companion.data.conversation.ConversationUiAction
import com.childai.companion.data.growth.GROWTH_EVENT_SHOWCASE_RECALL_TITLE
import com.childai.companion.data.growth.GROWTH_EVENT_SOURCE_XIAOZHANTAI
import com.childai.companion.data.growth.GROWTH_EVENT_TYPE_SHOWCASE_ITEM_RECALLED
import com.childai.companion.data.growth.GrowthEvent
import com.childai.companion.data.growth.GrowthEventRepository
import com.childai.companion.data.showcase.SaveXiaozhantaiItemUseCase
import com.childai.companion.data.showcase.XiaozhantaiItem
import com.childai.companion.data.showcase.XiaozhantaiRepository
import com.childai.companion.data.showcase.XiaozhantaiSaveRequest
import com.childai.companion.data.showcase.suggestedXiaozhantaiItemName
import com.childai.companion.data.showcase.xiaozhantaiFoxQuoteFromReply
import com.childai.companion.data.showcase.xiaozhantaiNormalizeFoxQuote
import com.childai.companion.data.showcase.xiaozhantaiNormalizeName
import com.childai.companion.data.growth.showcaseItemRecalledGrowthSummary
import com.childai.companion.data.tts.XiaobaohuTtsAudioGenerator
import com.childai.companion.data.tts.XiaobaohuTtsRepository
import com.childai.companion.data.attachment.RecognizedContent
import com.childai.companion.ui.chat.languagegame.BrainTeaserGameState
import com.childai.companion.ui.chat.languagegame.BrainTeaserQuestionBank
import com.childai.companion.ui.chat.languagegame.LanguageGameReducer
import com.childai.companion.ui.chat.languagegame.LanguageGameSnapshot
import com.childai.companion.ui.chat.languagegame.LanguageGameState
import com.childai.companion.ui.chat.languagegame.RiddleGameState
import com.childai.companion.ui.chat.languagegame.RiddleQuestionBank
import com.childai.companion.ui.chat.languagegame.WordChainGameState
import com.childai.companion.ui.chat.languagegame.WordChainWordBank
import com.childai.companion.ui.chat.languagegame.toLanguageGameEntryUiModel
import com.childai.companion.ui.chat.lightmemory.LightMemoryCopyMapper
import com.childai.companion.ui.chat.lightmemory.LightMemoryReducer
import com.childai.companion.ui.chat.lightmemory.LightMemorySnapshot
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoMethod
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoSnapshot
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoState
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDoorStateReducer
import com.childai.companion.ui.chat.strangedoor.StrangeDoorPhotoRecognition
import com.childai.companion.ui.chat.strangedoor.StrangeDoorPhotoTransform
import com.childai.companion.ui.chat.strangedoor.StrangeDoorPhotoTransformMapper
import com.childai.companion.ui.chat.strangedoor.StrangeDoorRiddleEvaluator
import com.childai.companion.ui.chat.strangedoor.StrangeDoorShowcaseAssistMapper
import com.childai.companion.ui.chat.strangedoor.StrangeDoorState
import com.childai.companion.ui.chat.strangedoor.toHomeEventUiModel
import com.childai.companion.voice.AudioSegment
import com.childai.companion.voice.AudioSegmentQueueCallbacks
import com.childai.companion.voice.AudioSegmentQueuePlayer
import com.childai.companion.voice.AndroidWavAudioRecorder
import com.childai.companion.voice.BackendSpeechInputController
import com.childai.companion.voice.NoOpTtsController
import com.childai.companion.voice.SpeechInputController
import com.childai.companion.voice.SpeechInputResult
import com.childai.companion.voice.TtsCallbacks
import com.childai.companion.voice.TtsController
import com.childai.companion.voice.TtsRequest
import com.childai.companion.voice.TtsUiState
import com.childai.companion.voice.VoiceProfile
import com.childai.companion.voice.previewForDiagnostics
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import android.util.Log
import java.io.File
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject

private const val TAG = "ChatViewModel"
private const val XIAOZHANTAI_RECALL_EVENT_DEDUPE_MS = 10_000L
private const val VOICE_RECORD_TTS_STOP_SETTLE_MS = 280L
private const val LANGUAGE_GAME_START_ROTATION_MS = 1000L

private val SCENES_NO_WAITING = setOf(
    "daily.bedtime_reflection",
    "learning.homework_help",
    "safety.guardian",
    "safety.gentle_checkin",
    "privacy.boundary",
)

class ChatViewModel(
    private val conversationSender: ConversationMessageSender =
        ConversationRepositoryMessageSender(),
    private val attachmentRepository: AttachmentRepository = AttachmentRepository(),
    private val xiaozhantaiRepository: XiaozhantaiRepository? = null,
    private val growthEventRepository: GrowthEventRepository? = null,
    private var ttsController: TtsController = NoOpTtsController,
    private var speechInputController: SpeechInputController? = null,
    private val speechInputControllerFactory: (File) -> SpeechInputController = { cacheDirectory ->
        BackendSpeechInputController(
            recorder = AndroidWavAudioRecorder(cacheDirectory = cacheDirectory),
        )
    },
    private val feedbackTtsAudioGenerator: XiaobaohuTtsAudioGenerator = XiaobaohuTtsRepository(),
    initialTtsUiState: TtsUiState = TtsUiState(),
    private val sendDispatcher: CoroutineDispatcher = Dispatchers.Main.immediate,
    requestOpeningOnInit: Boolean = false,
    private val voiceConfirmBeforeSend: Boolean = DevSettings.VOICE_CONFIRM_BEFORE_SEND,
    private val childId: String = DevSettings.CHILD_ID,
    private val naturalWaitingEnabled: Boolean = DevSettings.NATURAL_WAITING_ENABLED,
    private val naturalWaitingTimeoutMs: Long = DevSettings.NATURAL_WAITING_TIMEOUT_MS,
    private val initialLightMemory: LightMemorySnapshot = LightMemorySnapshot(),
    private val nowMillis: () -> Long = System::currentTimeMillis,
) : ViewModel() {
    private val sessionId = "android-${UUID.randomUUID()}"
    private var nextMessageIndex = 0
    private var baseAgentState = FoxAgentUiState()
    private var ttsToken = 0
    private var streamingAgentMessageId: String? = null
    private var voiceRecordingAutoStopJob: Job? = null
    private var naturalWaitingTimeoutJob: Job? = null
    private var waitingAttemptedThisTurn = false
    private var ttsSlowHintJob: Job? = null
    private var openingRequested = false
    private var openingDeferredByStrangeDoor = false
    private var strangeDoorDemoDismissed = false
    private var lastStrangeDoorNarrationText: String? = null
    private var languageGameAutoPromptShown = false
    private var languageGameDismissedForLifecycle = false
    private var lastLanguageGameNarrationText: String? = null
    private var nextBrainTeaserStartIndex = languageGameStartIndexFor(BrainTeaserQuestionBank.questions.size)
    private var nextRiddleStartIndex = languageGameStartIndexFor(RiddleQuestionBank.questions.size)
    private var nextWordChainStartIndex = languageGameStartIndexFor(WordChainWordBank.startWords.size)
    private var childInteractionStarted = false
    private var lastCacheDirectory: File? = null
    private var lastRecorder: AndroidWavAudioRecorder? = null
    private val pendingUploadPayloads = mutableMapOf<String, Pair<PhotoUploadPayload, String>>()
    private val xiaozhantaiSaveCandidates = mutableMapOf<String, XiaozhantaiSaveCandidate>()
    private var latestXiaozhantaiSaveCandidateMessageId: String? = null
    private var pendingXiaozhantaiRecallContext: XiaozhantaiRecallContext? = null
    private val lastXiaozhantaiRecallEventAtByItemId = mutableMapOf<String, Long>()
    private val saveXiaozhantaiItemUseCase = xiaozhantaiRepository?.let {
        SaveXiaozhantaiItemUseCase(
            xiaozhantaiRepository = it,
            growthEventRepository = growthEventRepository,
        )
    }

    private val _uiState = MutableStateFlow(
        run {
            val initialMessages = initialChatMessages()
            ChatUiState(
                messages = initialMessages,
                agentReplyText = initialMessages.lastOrNull { it.author == MessageAuthor.Agent }
                    ?.text
                    .orEmpty(),
                lightMemory = initialLightMemory,
                voice = createVoiceUiState(),
                tts = initialTtsUiState,
            )
        },
    )
    val uiState: StateFlow<ChatUiState> = _uiState

    private fun languageGameStartIndexFor(size: Int): Int {
        if (size <= 0) return 0
        return ((nowMillis() / LANGUAGE_GAME_START_ROTATION_MS) % size).toInt()
    }

    private val audioSegmentQueuePlayer = AudioSegmentQueuePlayer(
        ttsController = ttsController,
        backendBaseUrl = DevSettings.conversationApiBaseUrl,
        isMuted = { _uiState.value.tts.isMuted },
        callbacks = AudioSegmentQueueCallbacks(
            onDiagnostics = { diagnostics ->
                _uiState.update { state ->
                    state.copy(tts = state.tts.withDiagnostics(diagnostics))
                }
            },
            onStart = {
                _uiState.update { state ->
                    state.copy(
                        agent = baseAgentState.asSpeaking(),
                        tts = state.tts.copy(
                            isSpeaking = true,
                            isSpeakingPending = false,
                            isAvailable = true,
                            errorMessage = null,
                        ),
                    )
                }
            },
            onQueueDrained = {
                _uiState.update { state ->
                    state.copy(
                        agent = baseAgentState,
                        tts = state.tts.copy(
                            isSpeaking = false,
                            isSpeakingPending = false,
                        ),
                    )
                }
                showWaitingForChildAfterTts()
            },
            onError = { message ->
                _uiState.update { state ->
                    state.copy(
                        agent = baseAgentState,
                        tts = state.tts.copy(
                            isSpeaking = false,
                            isSpeakingPending = false,
                            errorMessage = message.ifBlank {
                                TtsController.AUDIO_PLAYBACK_UNAVAILABLE_MESSAGE
                            },
                        ),
                    )
                }
            },
        ),
    )

    init {
        trace(
            "view_model_created",
            "requestOpeningOnInit" to requestOpeningOnInit,
            "voiceConfirmBeforeSend" to voiceConfirmBeforeSend,
        )
        if (requestOpeningOnInit) {
            requestOpeningGreeting()
        }
    }

    private fun trace(
        event: String,
        vararg fields: Pair<String, Any?>,
    ) {
        val state = _uiState.value
        InteractionTraceLogger.log(
            event,
            "sessionId" to sessionId,
            "isSending" to state.isSending,
            "voiceMode" to state.voice.inputMode,
            "strangeDoor" to state.strangeDoorDemo?.shortTrace(),
            "languageGame" to state.languageGame?.shortTrace(),
            *fields,
        )
    }

    fun activateStrangeDoorDemo() {
        if (_uiState.value.strangeDoorDemo != null) {
            trace("strange_door_activate_ignored", "reason" to "already_active")
            return
        }
        if (strangeDoorDemoDismissed) {
            trace("strange_door_activate_ignored", "reason" to "dismissed_for_lifecycle")
            return
        }
        openingDeferredByStrangeDoor = !openingRequested
        cancelNaturalWaitingTimeout()
        stopCurrentTts(restoreBaseAgent = true)
        val nextSnapshot = StrangeDoorDoorStateReducer.reset()
        _uiState.update { state ->
            state.copy(
                strangeDoorDemo = nextSnapshot,
                languageGame = null,
                lightMemory = LightMemoryReducer.withOpeningRecallEligibility(
                    snapshot = state.lightMemory,
                    strangeDoorActive = true,
                    languageGameActive = false,
                ),
                quickActions = emptyList(),
                childTurnPhaseHint = null,
                pendingImageContext = null,
                isSending = false,
                voice = state.voice.copy(
                    inputMode = VoiceInputMode.Idle,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
            )
        }
        trace(
            "strange_door_activated",
            "openingDeferred" to openingDeferredByStrangeDoor,
            "snapshot" to nextSnapshot.shortTrace(),
        )
        speakCurrentStrangeDoorState(force = true)
    }

    fun replayStrangeDoorDemo() {
        val snapshot = _uiState.value.strangeDoorDemo ?: return
        strangeDoorDemoDismissed = false
        openingDeferredByStrangeDoor = !openingRequested
        cancelNaturalWaitingTimeout()
        stopCurrentTts(restoreBaseAgent = true)
        val nextSnapshot = StrangeDoorDoorStateReducer.replay(snapshot)
        _uiState.update { state ->
            state.copy(
                strangeDoorDemo = nextSnapshot,
                quickActions = emptyList(),
                childTurnPhaseHint = null,
                pendingImageContext = null,
                isSending = false,
                xiaozhantaiSaveDraft = null,
                voice = state.voice.copy(
                    inputMode = VoiceInputMode.Idle,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
            )
        }
        lastStrangeDoorNarrationText = null
        trace(
            "strange_door_replay",
            "from" to snapshot.shortTrace(),
            "to" to nextSnapshot.shortTrace(),
        )
        speakStrangeDoorSnapshot(nextSnapshot, force = true)
    }

    fun chooseStrangeDoorPhotoMethod() {
        trace("strange_door_action", "action" to "choose_photo")
        updateStrangeDoorDemoState(
            demoState = StrangeDoorDemoState.PhotoPrompt,
            method = StrangeDoorDemoMethod.Photo,
        )
    }

    fun chooseStrangeDoorRiddleMethod() {
        trace("strange_door_action", "action" to "choose_riddle")
        updateStrangeDoorDemoState(
            demoState = StrangeDoorDemoState.RiddlePrompt,
            method = StrangeDoorDemoMethod.Riddle,
        )
    }

    fun retryStrangeDoorRiddle() {
        trace("strange_door_action", "action" to "retry_riddle")
        updateStrangeDoorDemoState(
            demoState = StrangeDoorDemoState.RiddlePrompt,
            method = StrangeDoorDemoMethod.Riddle,
        )
    }

    fun returnToStrangeDoorMethodChoice() {
        trace("strange_door_action", "action" to "return_to_method_choice")
        updateStrangeDoorDemoState(
            demoState = StrangeDoorDemoState.ChoosingMethod,
            method = null,
        )
    }

    fun requestAnotherStrangeDoorPhoto() {
        val snapshot = _uiState.value.strangeDoorDemo ?: return
        openingDeferredByStrangeDoor = !openingRequested
        cancelNaturalWaitingTimeout()
        stopCurrentTts(restoreBaseAgent = true)
        val nextSnapshot = StrangeDoorDoorStateReducer.requestAnotherPhoto(snapshot)
        _uiState.update { state ->
            state.copy(
                strangeDoorDemo = nextSnapshot,
                quickActions = emptyList(),
                childTurnPhaseHint = null,
                pendingImageContext = null,
                isSending = false,
                xiaozhantaiSaveDraft = null,
                voice = state.voice.copy(
                    inputMode = VoiceInputMode.Idle,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
            )
        }
        trace(
            "strange_door_request_another_photo",
            "from" to snapshot.shortTrace(),
            "to" to nextSnapshot.shortTrace(),
        )
        speakStrangeDoorSnapshot(nextSnapshot)
    }

    fun useXiaozhantaiItemForStrangeDoor(item: XiaozhantaiItem) {
        val snapshot = _uiState.value.strangeDoorDemo ?: return
        if (snapshot.doorState == StrangeDoorState.Open) return
        openingDeferredByStrangeDoor = !openingRequested
        childInteractionStarted = true
        cancelNaturalWaitingTimeout()
        stopCurrentTts(restoreBaseAgent = true)
        val result = StrangeDoorShowcaseAssistMapper.map(item)
        val nextSnapshot = StrangeDoorDoorStateReducer.applyShowcaseAssist(
            snapshot = snapshot,
            result = result,
        )
        _uiState.update { state ->
            state.copy(
                strangeDoorDemo = nextSnapshot,
                lightMemory = LightMemoryReducer.rememberShowcaseAssist(
                    snapshot = state.lightMemory,
                    item = item,
                    doorSnapshot = nextSnapshot,
                    nowMillis = nowMillis(),
                ),
                quickActions = emptyList(),
                childTurnPhaseHint = null,
                pendingImageContext = null,
                isSending = false,
                xiaozhantaiSaveDraft = null,
                voice = state.voice.copy(
                    inputMode = VoiceInputMode.Idle,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
            )
        }
        trace(
            "strange_door_showcase_assist",
            "itemId" to item.id,
            "itemName" to item.name,
            "from" to snapshot.shortTrace(),
            "to" to nextSnapshot.shortTrace(),
            "doorEffect" to result.doorEffect,
        )
        speakStrangeDoorSnapshot(nextSnapshot)
    }

    fun requestStrangeDoorShowcaseSaveIntent() {
        val snapshot = _uiState.value.strangeDoorDemo ?: return
        val transform = snapshot.lastPhotoTransform ?: return
        val messageId = snapshot.lastPhotoMessageId ?: return
        if (!transform.isUsable || !transform.canSaveToShowcase || snapshot.showcaseSaveIntentRequested) return
        val candidate = xiaozhantaiSaveCandidates[messageId]
        if (candidate == null ||
            saveXiaozhantaiItemUseCase == null
        ) {
            return
        }
        _uiState.update { state ->
            state.copy(
                strangeDoorDemo = snapshot.copy(showcaseSaveIntentRequested = true),
                xiaozhantaiSaveDraft = XiaozhantaiSaveDraftUiState(
                    messageId = messageId,
                    name = candidate.saveName,
                    defaultName = candidate.defaultName,
                    previewBytes = candidate.payload.previewBytes,
                    isSaving = false,
                    errorMessage = null,
                    stage = XiaozhantaiSaveDraftStage.Confirm,
                    source = XiaozhantaiSaveDraftSource.StrangeDoor,
                ),
            )
        }
        speakAgentFeedback("要不要把这个小发现放进小展台？")
    }

    fun answerStrangeDoorRiddle(answerText: String): Boolean {
        val transcript = answerText.trim()
        if (transcript.isBlank()) {
            trace("strange_door_riddle_not_consumed", "reason" to "blank_input")
            return false
        }
        val snapshot = _uiState.value.strangeDoorDemo
        if (snapshot == null) {
            trace(
                "strange_door_riddle_not_consumed",
                "reason" to "demo_inactive",
                "input" to transcript,
            )
            return false
        }
        if (snapshot.demoState != StrangeDoorDemoState.RiddlePrompt) {
            trace(
                "strange_door_riddle_not_consumed",
                "reason" to "state_not_riddle_prompt",
                "input" to transcript,
                "snapshot" to snapshot.shortTrace(),
            )
            return false
        }
        val evaluation = StrangeDoorRiddleEvaluator.evaluate(transcript)
        val nextSnapshot = StrangeDoorDoorStateReducer.applyRiddleResult(
            snapshot = snapshot,
            evaluation = evaluation,
        )
        val normalized = transcript.normalizedForStrangeDoorRiddleTrace()
        trace(
            "strange_door_riddle_answer",
            "input" to transcript,
            "normalized" to normalized,
            "containsWater" to StrangeDoorRiddleEvaluator.isCorrectAnswer(transcript),
            "isCorrect" to evaluation.isCorrect,
            "from" to snapshot.shortTrace(),
            "to" to nextSnapshot.shortTrace(),
            "feedback" to evaluation.feedbackLines,
        )
        childInteractionStarted = true
        cancelNaturalWaitingTimeout()
        stopCurrentTts(restoreBaseAgent = true)
        _uiState.update { state ->
            state.copy(
                strangeDoorDemo = nextSnapshot,
                lightMemory = LightMemoryReducer.rememberStrangeDoorCompleted(
                    snapshot = state.lightMemory,
                    doorSnapshot = nextSnapshot,
                    nowMillis = nowMillis(),
                ),
                quickActions = emptyList(),
                childTurnPhaseHint = null,
                isSending = false,
                voice = state.voice.copy(
                    inputMode = VoiceInputMode.Idle,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
            )
        }
        speakStrangeDoorSnapshot(nextSnapshot)
        return true
    }

    fun submitStrangeDoorShowcaseName(name: String): Boolean {
        val itemName = name.trim()
        if (itemName.isBlank()) return false
        val draft = _uiState.value.xiaozhantaiSaveDraft ?: return false
        if (draft.source != XiaozhantaiSaveDraftSource.StrangeDoor ||
            draft.stage != XiaozhantaiSaveDraftStage.Naming
        ) {
            return false
        }
        _uiState.update { state ->
            state.copy(
                isSending = false,
                childTurnPhaseHint = null,
                voice = state.voice.copy(
                    inputMode = VoiceInputMode.Idle,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
            )
        }
        updateXiaozhantaiSaveName(itemName)
        confirmXiaozhantaiSave()
        return true
    }

    fun exitStrangeDoorDemoAndRequestOpening() {
        if (_uiState.value.strangeDoorDemo == null) return
        strangeDoorDemoDismissed = true
        trace("strange_door_exit_to_chat")
        _uiState.update { state ->
            state.copy(
                strangeDoorDemo = null,
                xiaozhantaiSaveDraft = null,
                lightMemory = LightMemoryReducer.muteForCurrentLifecycle(state.lightMemory),
            )
        }
        lastStrangeDoorNarrationText = null
        if (openingDeferredByStrangeDoor || !openingRequested) {
            openingDeferredByStrangeDoor = false
            requestOpeningGreeting()
        }
    }

    fun markLightMemoryOpeningRecalled() {
        _uiState.update { state ->
            state.copy(
                lightMemory = LightMemoryReducer.markOpeningRecalled(state.lightMemory),
            )
        }
    }

    fun muteLightMemoryForLifecycle() {
        _uiState.update { state ->
            state.copy(
                lightMemory = LightMemoryReducer.muteForCurrentLifecycle(state.lightMemory),
            )
        }
    }

    fun dismissLanguageGameEntry() {
        trace("language_game_action", "action" to "casual_chat")
        languageGameDismissedForLifecycle = true
        lastLanguageGameNarrationText = null
        _uiState.update { state ->
            state.copy(
                languageGame = null,
                lightMemory = LightMemoryReducer.muteForCurrentLifecycle(state.lightMemory),
            )
        }
    }

    fun openLanguageGameMenu() {
        trace("language_game_action", "action" to "open_menu")
        showLanguageGameSnapshot(
            LanguageGameReducer.gameMenu(),
            forceSpeak = true,
        )
    }

    fun startBrainTeaserGame() {
        val startIndex = nextBrainTeaserStartIndex
        nextBrainTeaserStartIndex = BrainTeaserQuestionBank.nextIndex(startIndex)
        trace(
            "language_game_action",
            "action" to "start_brain_teaser",
            "startIndex" to startIndex,
            "nextStartIndex" to nextBrainTeaserStartIndex,
        )
        showLanguageGameSnapshot(
            LanguageGameReducer.startBrainTeaser(questionIndex = startIndex),
            forceSpeak = true,
        )
    }

    fun startWordChainGame() {
        val startIndex = nextWordChainStartIndex
        nextWordChainStartIndex = WordChainWordBank.nextStartIndex(startIndex)
        trace(
            "language_game_action",
            "action" to "start_word_chain",
            "startIndex" to startIndex,
            "nextStartIndex" to nextWordChainStartIndex,
        )
        showLanguageGameSnapshot(
            LanguageGameReducer.startWordChain(startIndex = startIndex),
            forceSpeak = true,
        )
    }

    fun startRiddleGame() {
        val startIndex = nextRiddleStartIndex
        nextRiddleStartIndex = RiddleQuestionBank.nextIndex(startIndex)
        trace(
            "language_game_action",
            "action" to "start_riddle",
            "startIndex" to startIndex,
            "nextStartIndex" to nextRiddleStartIndex,
        )
        showLanguageGameSnapshot(
            LanguageGameReducer.startRiddle(questionIndex = startIndex),
            forceSpeak = true,
        )
    }

    fun requestBrainTeaserHint() {
        val snapshot = _uiState.value.languageGame ?: return
        trace("language_game_action", "action" to "brain_teaser_hint", "from" to snapshot.shortTrace())
        showLanguageGameSnapshot(
            LanguageGameReducer.showBrainTeaserHint(snapshot),
            forceSpeak = true,
        )
    }

    fun requestRiddleHint() {
        val snapshot = _uiState.value.languageGame ?: return
        trace("language_game_action", "action" to "riddle_hint", "from" to snapshot.shortTrace())
        showLanguageGameSnapshot(
            LanguageGameReducer.showRiddleHint(snapshot),
            forceSpeak = true,
        )
    }

    fun revealBrainTeaserAnswer() {
        val snapshot = _uiState.value.languageGame ?: return
        trace("language_game_action", "action" to "brain_teaser_reveal", "from" to snapshot.shortTrace())
        showLanguageGameSnapshot(
            LanguageGameReducer.revealBrainTeaserAnswer(snapshot),
            forceSpeak = true,
        )
    }

    fun revealRiddleAnswer() {
        val snapshot = _uiState.value.languageGame ?: return
        trace("language_game_action", "action" to "riddle_reveal", "from" to snapshot.shortTrace())
        showLanguageGameSnapshot(
            LanguageGameReducer.revealRiddleAnswer(snapshot),
            forceSpeak = true,
        )
    }

    fun nextBrainTeaserQuestion() {
        val snapshot = _uiState.value.languageGame ?: return
        trace("language_game_action", "action" to "brain_teaser_next", "from" to snapshot.shortTrace())
        showLanguageGameSnapshot(
            LanguageGameReducer.nextBrainTeaserQuestion(snapshot),
            forceSpeak = true,
        )
    }

    fun nextRiddleQuestion() {
        val snapshot = _uiState.value.languageGame ?: return
        trace("language_game_action", "action" to "riddle_next", "from" to snapshot.shortTrace())
        showLanguageGameSnapshot(
            LanguageGameReducer.nextRiddleQuestion(snapshot),
            forceSpeak = true,
        )
    }

    fun restartWordChainGame() {
        val snapshot = _uiState.value.languageGame ?: return
        trace("language_game_action", "action" to "word_chain_restart", "from" to snapshot.shortTrace())
        showLanguageGameSnapshot(
            LanguageGameReducer.restartWordChain(snapshot),
            forceSpeak = true,
        )
    }

    fun returnToLanguageGameMenu() {
        trace("language_game_action", "action" to "return_to_menu")
        showLanguageGameSnapshot(
            LanguageGameReducer.gameMenu(),
            forceSpeak = true,
        )
    }

    fun exitLanguageGame() {
        trace("language_game_action", "action" to "exit_to_chat")
        languageGameDismissedForLifecycle = true
        lastLanguageGameNarrationText = null
        _uiState.update { state ->
            state.copy(
                languageGame = null,
                childTurnPhaseHint = null,
                isSending = false,
                lightMemory = LightMemoryReducer.muteForCurrentLifecycle(state.lightMemory),
                voice = state.voice.copy(
                    inputMode = VoiceInputMode.Idle,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
            )
        }
    }

    private fun updateStrangeDoorDemoState(
        demoState: StrangeDoorDemoState,
        method: StrangeDoorDemoMethod?,
    ) {
        val snapshot = _uiState.value.strangeDoorDemo ?: return
        openingDeferredByStrangeDoor = !openingRequested
        cancelNaturalWaitingTimeout()
        stopCurrentTts(restoreBaseAgent = true)
        _uiState.update { state ->
            state.copy(
                strangeDoorDemo = snapshot.copy(
                    demoState = demoState,
                    lastMethod = method,
                    lastPhotoTransform = if (method == StrangeDoorDemoMethod.Riddle) null else snapshot.lastPhotoTransform,
                    lastRiddleEvaluation = if (method == StrangeDoorDemoMethod.Photo ||
                        demoState == StrangeDoorDemoState.RiddlePrompt
                    ) {
                        null
                    } else {
                        snapshot.lastRiddleEvaluation
                    },
                    lastShowcaseAssistResult = null,
                    showcaseSavedName = null,
                    showcaseSaveIntentRequested = false,
                ),
                quickActions = emptyList(),
                childTurnPhaseHint = null,
                isSending = false,
                voice = state.voice.copy(
                    inputMode = VoiceInputMode.Idle,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
            )
        }
        speakCurrentStrangeDoorState()
    }

    fun sendText(text: String, quickActionId: String? = null) {
        val trimmedText = text.trim()
        if (trimmedText.isEmpty()) {
            trace("child_text_ignored", "reason" to "blank", "quickActionId" to quickActionId)
            return
        }
        if (_uiState.value.isSending) {
            trace(
                "child_text_ignored",
                "reason" to "is_sending",
                "text" to trimmedText,
                "quickActionId" to quickActionId,
            )
            return
        }
        trace(
            "child_text_received",
            "text" to trimmedText,
            "quickActionId" to quickActionId,
        )
        val routedBackToConversation = routeLocalExperienceToConversationIfNeeded(trimmedText)
        if (!routedBackToConversation) {
            if (submitStrangeDoorShowcaseName(trimmedText)) {
                trace("child_text_consumed", "consumer" to "strange_door_showcase_name", "text" to trimmedText)
                return
            }
            if (answerStrangeDoorRiddle(trimmedText)) {
                trace("child_text_consumed", "consumer" to "strange_door_riddle", "text" to trimmedText)
                return
            }
            if (handleLanguageGameText(trimmedText)) {
                trace("child_text_consumed", "consumer" to "language_game", "text" to trimmedText)
                return
            }
        }
        updateLightMemoryRelatedChatEligibility(trimmedText)

        val imageContext = _uiState.value.pendingImageContext
        if (imageContext != null) {
            Log.d(TAG, "sendText: with image attachment=${imageContext.attachmentId}, textLength=${trimmedText.length}")
            _uiState.update { it.copy(pendingImageContext = null) }
        } else {
            Log.d(TAG, "sendText: textLength=${trimmedText.length}")
        }
        sendTextWithAttachments(
            trimmedText,
            imageContext?.let { listOf(it.attachmentId) } ?: emptyList(),
            quickActionId = quickActionId,
        )
    }

    private fun routeLocalExperienceToConversationIfNeeded(text: String): Boolean {
        val state = _uiState.value
        if (state.strangeDoorDemo == null && state.languageGame == null) return false
        if (!looksLikeConversationResumeIntent(text)) return false

        trace(
            "local_experience_exit_to_conversation",
            "text" to text,
            "fromStrangeDoor" to state.strangeDoorDemo?.shortTrace(),
            "fromLanguageGame" to state.languageGame?.shortTrace(),
        )
        strangeDoorDemoDismissed = true
        languageGameDismissedForLifecycle = true
        openingDeferredByStrangeDoor = false
        lastStrangeDoorNarrationText = null
        lastLanguageGameNarrationText = null
        cancelNaturalWaitingTimeout()
        stopCurrentTts(restoreBaseAgent = true)
        _uiState.update { current ->
            current.copy(
                strangeDoorDemo = null,
                languageGame = null,
                xiaozhantaiSaveDraft = null,
                childTurnPhaseHint = null,
                pendingImageContext = current.pendingImageContext,
                isSending = false,
                lightMemory = LightMemoryReducer.muteForCurrentLifecycle(current.lightMemory),
                voice = current.voice.copy(
                    inputMode = VoiceInputMode.Idle,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
            )
        }
        return true
    }

    private fun looksLikeConversationResumeIntent(text: String): Boolean {
        val normalized = text
            .filterNot { it.isWhitespace() || it in "，。！？,.!?；;：:" }
        return normalized.contains("先聊别的") ||
            normalized.contains("随便聊聊") ||
            normalized.contains("不想玩") ||
            normalized.contains("不玩了") ||
            normalized.contains("不玩游戏") ||
            normalized.contains("不想猜") ||
            normalized.contains("不想答") ||
            normalized.contains("讲故事") ||
            normalized.contains("讲个故事") ||
            normalized.contains("讲一个故事") ||
            normalized.contains("说故事") ||
            normalized.contains("说个故事") ||
            normalized.contains("给我讲") ||
            normalized.contains("我想听") ||
            normalized.contains("想听") ||
            normalized.contains("故事") ||
            normalized.contains("聊")
    }

    private fun updateLightMemoryRelatedChatEligibility(text: String) {
        _uiState.update { state ->
            state.copy(
                lightMemory = LightMemoryReducer.withRelatedChatEligibility(
                    snapshot = state.lightMemory,
                    childText = text,
                    strangeDoorActive = state.strangeDoorDemo != null,
                    languageGameActive = state.languageGame != null,
                ),
            )
        }
    }

    fun recallXiaozhantaiItem(context: XiaozhantaiRecallContext) {
        val normalizedContext = context.normalized()
        if (normalizedContext.itemId.isBlank()) return
        val currentMessages = _uiState.value.messages
        if (currentMessages.lastOrNull()?.xiaozhantaiRecallCard?.itemId == normalizedContext.itemId) {
            return
        }

        childInteractionStarted = true
        cancelNaturalWaitingTimeout()
        cancelSlowHints()
        val recallText = xiaozhantaiRecallMessageText(normalizedContext)
        val recallMessage = ChatMessage(
            id = nextMessageId("agent-xzt-recall"),
            author = MessageAuthor.Agent,
            text = recallText,
            xiaozhantaiRecallCard = normalizedContext.toRecallCardUiState(),
        )
        pendingXiaozhantaiRecallContext = normalizedContext
        _uiState.update { state ->
            state.copy(
                messages = state.messages + recallMessage,
                agentReplyText = recallText,
                quickActions = emptyList(),
                isSending = false,
                childTurnPhaseHint = null,
            )
        }
        recordXiaozhantaiRecallGrowthEvent(
            rawContext = context,
            normalizedContext = normalizedContext,
        )
    }

    private fun recordXiaozhantaiRecallGrowthEvent(
        rawContext: XiaozhantaiRecallContext,
        normalizedContext: XiaozhantaiRecallContext,
    ) {
        val repository = growthEventRepository ?: return
        val createdAt = nowMillis()
        val lastCreatedAt = lastXiaozhantaiRecallEventAtByItemId[normalizedContext.itemId]
        if (lastCreatedAt != null && createdAt - lastCreatedAt in 0L until XIAOZHANTAI_RECALL_EVENT_DEDUPE_MS) {
            return
        }
        lastXiaozhantaiRecallEventAtByItemId[normalizedContext.itemId] = createdAt
        viewModelScope.launch(sendDispatcher) {
            runCatching {
                repository.append(
                    GrowthEvent(
                        id = "growth_event_recall_${normalizedContext.itemId}_$createdAt",
                        childId = childId,
                        type = GROWTH_EVENT_TYPE_SHOWCASE_ITEM_RECALLED,
                        title = GROWTH_EVENT_SHOWCASE_RECALL_TITLE,
                        summary = showcaseItemRecalledGrowthSummary(rawContext.name),
                        relatedItemId = normalizedContext.itemId,
                        relatedPhotoUri = normalizedContext.photoUri.takeIf { it.isNotBlank() },
                        createdAt = createdAt,
                        source = GROWTH_EVENT_SOURCE_XIAOZHANTAI,
                    ),
                )
            }.onFailure { error ->
                Log.w(TAG, "recordXiaozhantaiRecallGrowthEvent: failed", error)
            }
        }
    }

    fun startVoiceRecording(cacheDirectory: File) {
        val state = _uiState.value
        if (state.isSending || state.voice.isUploading || state.voice.isRecording) {
            trace(
                "voice_record_start_ignored",
                "reason" to "busy",
                "isSending" to state.isSending,
                "isUploading" to state.voice.isUploading,
                "isRecording" to state.voice.isRecording,
            )
            return
        }

        val wasSpeaking = state.tts.isSpeaking || state.tts.isSpeakingPending
        val wasAudiblySpeaking = state.tts.isSpeaking
        childInteractionStarted = true
        lastCacheDirectory = cacheDirectory
        lastRecorder?.onSilenceDetected = null
        cancelNaturalWaitingTimeout()
        if (wasSpeaking) {
            Log.d(TAG, "[LatencyTrace] stage=child_interrupt")
        }
        stopCurrentTts(restoreBaseAgent = true)
        if (wasSpeaking) {
            _uiState.update {
                it.copy(agent = baseAgentState.copy(statusText = "我听到啦"))
            }
        }
        Log.d(TAG, "[LatencyTrace] stage=asr_start")
        trace("voice_record_started", "interruptedTts" to wasSpeaking)
        _uiState.update {
            it.copy(
                quickActions = emptyList(),
                childTurnPhaseHint = ChildTurnUiPhase.Listening,
                voice = it.voice.copy(
                    inputMode = VoiceInputMode.Listening,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
                agent = childInteractionPresentation(
                    phaseHint = ChildTurnUiPhase.Listening,
                ).agent,
            )
        }

        viewModelScope.launch(sendDispatcher) {
            runCatching {
                if (wasAudiblySpeaking) {
                    trace(
                        "voice_record_start_wait_tts_stop",
                        "delayMs" to VOICE_RECORD_TTS_STOP_SETTLE_MS,
                    )
                    delay(VOICE_RECORD_TTS_STOP_SETTLE_MS)
                }
                activeSpeechInputController(cacheDirectory).startRecording()
                scheduleVoiceRecordingAutoStop()
            }.onFailure {
                trace(
                    "voice_record_start_failed",
                    "error" to it::class.simpleName,
                    "message" to it.message,
                )
                voiceRecordingAutoStopJob?.cancel()
                _uiState.update { current ->
                    current.copy(
                        childTurnPhaseHint = ChildTurnUiPhase.ServiceError,
                        voice = current.voice.copy(
                            inputMode = VoiceInputMode.Failed,
                            errorMessage = "没太听清，可以再说一次。",
                        ),
                        agent = childInteractionPresentation(
                            phaseHint = ChildTurnUiPhase.ServiceError,
                        ).agent,
                    )
                }
            }
        }
    }

    fun stopVoiceRecordingAndUpload() {
        if (!_uiState.value.voice.isRecording) {
            trace("voice_record_stop_ignored", "reason" to "not_recording")
            return
        }

        voiceRecordingAutoStopJob?.cancel()
        trace("voice_record_stop_upload_started")
        _uiState.update {
            it.copy(
                isSending = true,
                childTurnPhaseHint = ChildTurnUiPhase.Recognizing,
                voice = it.voice.copy(
                    inputMode = VoiceInputMode.Uploading,
                    errorMessage = null,
                ),
                agent = childInteractionPresentation(
                    phaseHint = ChildTurnUiPhase.Recognizing,
                ).agent,
            )
        }

        viewModelScope.launch(sendDispatcher) {
            val result = runCatching {
                requireNotNull(speechInputController) {
                    "Speech input controller is not ready"
                }.stopAndTranscribe(
                    childId = childId,
                    sessionId = sessionId,
                    timezone = DevSettings.TIMEZONE,
                )
            }.getOrElse {
                trace(
                    "asr_upload_failed_before_result",
                    "error" to it::class.simpleName,
                    "message" to it.message,
                )
                SpeechInputResult.Failed("刚才没听清。请家长帮忙看一下麦克风")
            }
            Log.d(TAG, "[LatencyTrace] stage=asr_done result=${result::class.simpleName}")
            applySpeechInputResult(result)
        }
    }

    fun onVoicePermissionDenied() {
        childInteractionStarted = true
        trace("voice_permission_denied")
        _uiState.update {
            it.copy(
                childTurnPhaseHint = ChildTurnUiPhase.PermissionNeeded,
                voice = it.voice.copy(
                    inputMode = VoiceInputMode.PermissionDenied,
                    errorMessage = null,
                    pendingTranscript = "",
                ),
            )
        }
    }

    fun updatePendingVoiceTranscript(text: String) {
        trace("pending_voice_transcript_updated", "text" to text)
        _uiState.update { state ->
            if (!state.voice.hasPendingTranscript) return@update state
            state.copy(
                voice = state.voice.copy(
                    pendingTranscript = text,
                    errorMessage = null,
                ),
            )
        }
    }

    fun sendPendingVoiceTranscript() {
        val transcript = _uiState.value.voice.pendingTranscript.trim()
        if (transcript.isBlank()) {
            trace("pending_voice_transcript_send_ignored", "reason" to "blank")
            _uiState.update {
                it.copy(
                    voice = it.voice.copy(
                        errorMessage = "先写一句话，再发给小白狐",
                    ),
                )
            }
            return
        }
        trace("pending_voice_transcript_send", "text" to transcript)
        if (routeLocalExperienceToConversationIfNeeded(transcript)) {
            clearVoiceInputState()
            sendText(transcript)
            return
        }
        if (submitStrangeDoorShowcaseName(transcript)) return
        if (answerStrangeDoorRiddle(transcript)) return
        if (handleLanguageGameText(transcript)) return
        clearVoiceInputState()
        sendText(transcript)
    }

    fun cancelVoiceInput() {
        val wasRecording = _uiState.value.voice.isRecording
        trace("voice_input_cancelled", "wasRecording" to wasRecording)
        voiceRecordingAutoStopJob?.cancel()
        cancelNaturalWaitingTimeout()
        _uiState.update {
            it.copy(
                childTurnPhaseHint = null,
                voice = it.voice.copy(
                    inputMode = VoiceInputMode.Idle,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
                agent = if (wasRecording) baseAgentState else it.agent,
            )
        }
        if (wasRecording) {
            viewModelScope.launch(sendDispatcher) {
                runCatching { speechInputController?.cancel() }
            }
        }
    }

    private fun sendTextWithAttachments(
        text: String,
        attachments: List<String>,
        quickActionId: String? = null,
    ) {
        if (_uiState.value.isSending) {
            trace(
                "conversation_request_ignored",
                "reason" to "is_sending",
                "text" to text,
                "attachmentsCount" to attachments.size,
                "quickActionId" to quickActionId,
            )
            return
        }

        Log.d(TAG, "[LatencyTrace] stage=request_send textLen=${text.length}")
        val requestText = consumeXiaozhantaiRecallRequestText(
            childText = text,
            attachments = attachments,
        )
        val wasSpeaking = _uiState.value.tts.isSpeaking || _uiState.value.tts.isSpeakingPending
        childInteractionStarted = true
        waitingAttemptedThisTurn = false
        stopCurrentTts(restoreBaseAgent = true)
        if (wasSpeaking) {
            _uiState.update {
                it.copy(agent = baseAgentState.copy(statusText = "好，我先停下"))
            }
        }
        trace(
            "conversation_request_send",
            "childText" to text,
            "requestText" to requestText,
            "attachmentsCount" to attachments.size,
            "quickActionId" to quickActionId,
            "useStreaming" to DevSettings.USE_STREAMING_CONVERSATION,
        )
        recordChildMessage(text)
        _uiState.update {
            it.copy(
                isSending = true,
                childTurnPhaseHint = ChildTurnUiPhase.Sending,
                quickActions = emptyList(),
            )
        }

        viewModelScope.launch(sendDispatcher) {
            if (DevSettings.USE_STREAMING_CONVERSATION) {
                val streamed = runCatching {
                    streamTextWithAttachments(
                        text = requestText,
                        attachments = attachments,
                        quickActionId = quickActionId,
                    )
                }.getOrDefault(false)
                if (streamed) return@launch
            }

            runCatching {
                conversationSender.sendTextMessage(
                    childId = childId,
                    sessionId = sessionId,
                    text = requestText,
                    attachments = attachments,
                    quickActionId = quickActionId,
                )
            }.onSuccess { response ->
                Log.d(TAG, "sendTextWithAttachments: success, replyLength=${response.reply.text.length}")
                trace(
                    "conversation_response_received",
                    "replyText" to response.reply.text,
                    "activeScene" to response.sessionState.activeScene,
                    "quickActions" to response.uiActions.flatMap { group -> group.actions.map { it.label } },
                    "streamingFallback" to true,
                )
                renderAgentReply(
                    response = response,
                    replaceMessageId = streamingAgentMessageId,
                )
            }.onFailure { error ->
                Log.e(TAG, "sendTextWithAttachments: failed", error)
                trace(
                    "conversation_request_failed",
                    "error" to error::class.simpleName,
                    "message" to error.message,
                )
                appendMessage(
                    ChatMessage(
                        id = nextMessageId("agent-error"),
                        author = MessageAuthor.Agent,
                        text = followupFailureMessage(attachments),
                    ),
                )
                _uiState.update {
                    it.copy(
                        quickActions = emptyList(),
                        childTurnPhaseHint = ChildTurnUiPhase.ServiceError,
                        agent = FoxAgentUiState(
                            mood = FoxMood.NetworkError,
                            motion = FoxMotion.NetworkError,
                            statusText = "请家长帮忙看看网络",
                        ),
                        voice = it.voice.copy(
                            inputMode = VoiceInputMode.Idle,
                            pendingTranscript = "",
                            errorMessage = null,
                        ),
                        isSending = false,
                    )
                }
            }
        }
    }

    private fun consumeXiaozhantaiRecallRequestText(
        childText: String,
        attachments: List<String>,
    ): String {
        val context = pendingXiaozhantaiRecallContext
        if (context == null) {
            return childText
        }
        if (attachments.isNotEmpty()) {
            pendingXiaozhantaiRecallContext = null
            return childText
        }
        pendingXiaozhantaiRecallContext = null
        return xiaozhantaiRecallRequestText(
            context = context,
            childText = childText,
        )
    }

    fun onQuickAction(action: QuickActionUi) {
        Log.d(TAG, "onQuickAction: id=${action.id}, label=${action.label}")
        trace("quick_action_clicked", "id" to action.id, "label" to action.label)
        when (action.id) {
            "take_photo", "share_photo" -> {
                stopCurrentTts(restoreBaseAgent = true)
                appendAgentMessage(
                    "点“给小白狐看看”，拍一张或选一张都可以",
                )
            }
            "talk_about_image",
            "make_story",
            "ask_what_is_this",
            "tell_story",
            "image_story",
            "say_what_happened" ->
                continuePendingImageConversation(action)
            "companion_name",
            "give_name",
            "image_naming",
            "companion_friend_name" -> {
                sendText(
                    action.label,
                    quickActionId = normalizedQuickActionId(action.id),
                )
            }
            else -> sendText(
                action.label,
                quickActionId = normalizedQuickActionId(action.id),
            )
        }
    }

    fun submitCapturedPhoto(
        payload: PhotoUploadPayload,
        imagePurpose: String = IMAGE_PURPOSE_SHARE,
    ) {
        if (_uiState.value.isSending || payload.bytes.isEmpty()) {
            trace(
                "photo_submit_ignored",
                "reason" to if (_uiState.value.isSending) "is_sending" else "empty_payload",
                "purpose" to imagePurpose,
                "sizeBytes" to payload.bytes.size,
            )
            return
        }
        Log.d(TAG, "[LatencyTrace] stage=image_local_selected purpose=$imagePurpose size=${payload.bytes.size}")
        Log.d(TAG, "submitCapturedPhoto: purpose=$imagePurpose, size=${payload.bytes.size}bytes, mime=${payload.mimeType}")
        pendingXiaozhantaiRecallContext = null
        stopCurrentTts(restoreBaseAgent = true)
        childInteractionStarted = true
        val childPhotoMessageId = nextMessageId("child-photo")
        appendMessage(
            ChatMessage(
                id = childPhotoMessageId,
                author = MessageAuthor.Child,
                text = "我给小白狐看了一张图",
            ),
        )
        pendingUploadPayloads[childPhotoMessageId] = payload to imagePurpose
        val isStrangeDoorPhoto = _uiState.value.strangeDoorDemo != null &&
            imagePurpose == IMAGE_PURPOSE_SHARE
        trace(
            "photo_submit_started",
            "purpose" to imagePurpose,
            "mimeType" to payload.mimeType,
            "sizeBytes" to payload.bytes.size,
            "isStrangeDoorPhoto" to isStrangeDoorPhoto,
            "messageId" to childPhotoMessageId,
        )
        _uiState.update {
            it.copy(
                isSending = true,
                childTurnPhaseHint = ChildTurnUiPhase.ImageProcessing,
                quickActions = emptyList(),
                strangeDoorDemo = if (isStrangeDoorPhoto) {
                    it.strangeDoorDemo?.copy(
                        demoState = StrangeDoorDemoState.PhotoUploading,
                        lastMethod = StrangeDoorDemoMethod.Photo,
                        lastPhotoMessageId = childPhotoMessageId,
                        lastShowcaseAssistResult = null,
                        showcaseSaveIntentRequested = false,
                    )
                } else {
                    it.strangeDoorDemo
                },
                imagePreviewCards = it.imagePreviewCards + (
                    childPhotoMessageId to LocalImagePreviewCardUiState.fromPayload(
                        messageId = childPhotoMessageId,
                        payload = payload,
                    )
                    ),
                agent = childInteractionPresentation(
                    phaseHint = ChildTurnUiPhase.ImageProcessing,
                ).agent,
                voice = it.voice.copy(
                    inputMode = VoiceInputMode.Idle,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
            )
        }
        if (isStrangeDoorPhoto) {
            speakAgentFeedback(localImagePreviewStatusText(LocalImagePreviewStatus.Uploading))
        }

        viewModelScope.launch(sendDispatcher) {
            Log.d(TAG, "[LatencyTrace] stage=image_upload_start")
            runCatching {
                attachmentRepository.createCapturedImage(
                    childId = childId,
                    sessionId = sessionId,
                    imageBytes = payload.bytes,
                    mimeType = payload.mimeType,
                    fileName = childSafeUploadFileName(payload.fileName),
                    imagePurpose = imagePurpose,
                    childCaption = "我给小白狐看了一张图",
                )
            }.onSuccess { attachmentResponse ->
                Log.d(TAG, "[LatencyTrace] stage=image_upload_done status=ok")
                trace(
                    "photo_upload_success",
                    "messageId" to childPhotoMessageId,
                    "attachmentId" to attachmentResponse.attachmentId,
                    "recognizedType" to attachmentResponse.recognizedContent.type,
                    "recognizedText" to attachmentResponse.recognizedContent.text,
                    "imagePurpose" to attachmentResponse.recognizedContent.imagePurpose,
                    "confidence" to attachmentResponse.recognizedContent.confidence,
                )
                pendingUploadPayloads.remove(childPhotoMessageId)
                if (handleStrangeDoorAttachmentResponseIfActive(
                        attachmentResponse = attachmentResponse,
                        photoMessageId = childPhotoMessageId,
                        payload = payload,
                    )
                ) {
                    updateImagePreviewStatus(
                        messageId = childPhotoMessageId,
                        status = LocalImagePreviewStatus.Sent,
                        canSaveToXiaozhantai = strangeDoorPhotoCanSaveToShowcase(childPhotoMessageId),
                        defaultShowcaseName = _uiState.value.strangeDoorDemo?.lastTransformedName,
                    )
                    return@onSuccess
                }
                val defaultItemName = suggestedXiaozhantaiItemName(
                    attachmentResponse.recognizedContent.text,
                )
                xiaozhantaiSaveCandidates[childPhotoMessageId] = XiaozhantaiSaveCandidate(
                    payload = payload,
                    defaultName = defaultItemName,
                    foxQuote = xiaozhantaiFoxQuoteFromReply(attachmentResponse.reply.text),
                )
                latestXiaozhantaiSaveCandidateMessageId = childPhotoMessageId
                handleAttachmentResponse(attachmentResponse)
                updateImagePreviewStatus(
                    messageId = childPhotoMessageId,
                    status = LocalImagePreviewStatus.Sent,
                    canSaveToXiaozhantai = xiaozhantaiRepository != null,
                    defaultShowcaseName = defaultItemName,
                )
                _uiState.update { state ->
                    state.copy(
                        xiaozhantaiSavePromptMessageId = childPhotoMessageId,
                    )
                }
            }.onFailure { error ->
                Log.d(TAG, "[LatencyTrace] stage=image_upload_failed error=${error::class.simpleName}")
                trace(
                    "photo_upload_failed",
                    "messageId" to childPhotoMessageId,
                    "error" to error::class.simpleName,
                    "message" to error.message,
                )
                appendAgentMessage(uploadFailureMessage(imagePurpose))
                _uiState.update {
                    it.copy(
                        isSending = false,
                        childTurnPhaseHint = ChildTurnUiPhase.ServiceError,
                        quickActions = emptyList(),
                        imagePreviewCards = it.imagePreviewCards + (
                            childPhotoMessageId to (
                                it.imagePreviewCards[childPhotoMessageId]
                                    ?: LocalImagePreviewCardUiState.fromPayload(
                                        messageId = childPhotoMessageId,
                                        payload = payload,
                                    )
                                ).copy(status = LocalImagePreviewStatus.Failed)
                            ),
                        agent = FoxAgentUiState(
                            mood = FoxMood.NetworkError,
                            motion = FoxMotion.NetworkError,
                            statusText = "这张图还没看到",
                        ),
                        strangeDoorDemo = if (isStrangeDoorPhoto) {
                            it.strangeDoorDemo?.copy(
                                demoState = StrangeDoorDemoState.PhotoPrompt,
                                showcaseSaveIntentRequested = false,
                            )
                        } else {
                            it.strangeDoorDemo
                        },
                    )
                }
            }
        }
    }

    fun retryPhotoUpload(messageId: String) {
        val (payload, imagePurpose) = pendingUploadPayloads[messageId] ?: return
        if (_uiState.value.isSending) return
        val isStrangeDoorPhoto = _uiState.value.strangeDoorDemo?.lastPhotoMessageId == messageId &&
            imagePurpose == IMAGE_PURPOSE_SHARE

        _uiState.update { state ->
            state.copy(
                isSending = true,
                childTurnPhaseHint = ChildTurnUiPhase.ImageProcessing,
                strangeDoorDemo = if (isStrangeDoorPhoto) {
                    state.strangeDoorDemo?.copy(
                        demoState = StrangeDoorDemoState.PhotoUploading,
                        lastShowcaseAssistResult = null,
                        showcaseSaveIntentRequested = false,
                    )
                } else {
                    state.strangeDoorDemo
                },
                imagePreviewCards = state.imagePreviewCards + (
                    messageId to (state.imagePreviewCards[messageId]?.copy(
                        status = LocalImagePreviewStatus.Uploading,
                    ) ?: return@update state)
                    ),
                agent = childInteractionPresentation(
                    phaseHint = ChildTurnUiPhase.ImageProcessing,
                ).agent,
            )
        }
        if (isStrangeDoorPhoto) {
            speakAgentFeedback(localImagePreviewStatusText(LocalImagePreviewStatus.Uploading))
        }

        viewModelScope.launch(sendDispatcher) {
            runCatching {
                attachmentRepository.createCapturedImage(
                    childId = childId,
                    sessionId = sessionId,
                    imageBytes = payload.bytes,
                    mimeType = payload.mimeType,
                    fileName = childSafeUploadFileName(payload.fileName),
                    imagePurpose = imagePurpose,
                    childCaption = "我给小白狐看了一张图",
                )
            }.onSuccess { attachmentResponse ->
                pendingUploadPayloads.remove(messageId)
                if (handleStrangeDoorAttachmentResponseIfActive(
                        attachmentResponse = attachmentResponse,
                        photoMessageId = messageId,
                        payload = payload,
                    )
                ) {
                    updateImagePreviewStatus(
                        messageId = messageId,
                        status = LocalImagePreviewStatus.Sent,
                        canSaveToXiaozhantai = strangeDoorPhotoCanSaveToShowcase(messageId),
                        defaultShowcaseName = _uiState.value.strangeDoorDemo?.lastTransformedName,
                    )
                    return@onSuccess
                }
                val defaultItemName = suggestedXiaozhantaiItemName(
                    attachmentResponse.recognizedContent.text,
                )
                xiaozhantaiSaveCandidates[messageId] = XiaozhantaiSaveCandidate(
                    payload = payload,
                    defaultName = defaultItemName,
                    foxQuote = xiaozhantaiFoxQuoteFromReply(attachmentResponse.reply.text),
                )
                latestXiaozhantaiSaveCandidateMessageId = messageId
                handleAttachmentResponse(attachmentResponse)
                updateImagePreviewStatus(
                    messageId = messageId,
                    status = LocalImagePreviewStatus.Sent,
                    canSaveToXiaozhantai = xiaozhantaiRepository != null,
                    defaultShowcaseName = defaultItemName,
                )
                _uiState.update { state ->
                    state.copy(
                        xiaozhantaiSavePromptMessageId = messageId,
                    )
                }
            }.onFailure {
                appendAgentMessage(uploadFailureMessage(imagePurpose))
                _uiState.update { state ->
                    val existingCard = state.imagePreviewCards[messageId]
                    if (existingCard != null) {
                        state.copy(
                            isSending = false,
                            childTurnPhaseHint = ChildTurnUiPhase.ServiceError,
                            imagePreviewCards = state.imagePreviewCards + (
                                messageId to existingCard.copy(status = LocalImagePreviewStatus.Failed)
                                ),
                            agent = FoxAgentUiState(
                                mood = FoxMood.NetworkError,
                                motion = FoxMotion.NetworkError,
                                statusText = "这张图还没看到",
                            ),
                            strangeDoorDemo = if (isStrangeDoorPhoto) {
                                state.strangeDoorDemo?.copy(
                                    demoState = StrangeDoorDemoState.PhotoPrompt,
                                    showcaseSaveIntentRequested = false,
                                )
                            } else {
                                state.strangeDoorDemo
                            },
                        )
                    } else state
                }
            }
        }
    }

    fun dismissFailedPhoto(messageId: String) {
        pendingUploadPayloads.remove(messageId)
        xiaozhantaiSaveCandidates.remove(messageId)
        clearLatestXiaozhantaiCandidateIfNeeded(messageId)
        _uiState.update { state ->
            state.copy(
                imagePreviewCards = state.imagePreviewCards - messageId,
                xiaozhantaiSavePromptMessageId = state.xiaozhantaiSavePromptMessageId
                    ?.takeUnless { it == messageId },
            )
        }
    }

    private fun updateImagePreviewStatus(
        messageId: String,
        status: LocalImagePreviewStatus,
        canSaveToXiaozhantai: Boolean? = null,
        defaultShowcaseName: String? = null,
    ) {
        _uiState.update { state ->
            val card = state.imagePreviewCards[messageId] ?: return@update state
            state.copy(
                imagePreviewCards = state.imagePreviewCards + (
                    messageId to card.copy(
                        status = status,
                        canSaveToXiaozhantai = canSaveToXiaozhantai ?: card.canSaveToXiaozhantai,
                        defaultShowcaseName = defaultShowcaseName ?: card.defaultShowcaseName,
                    )
                    ),
            )
        }
    }

    private fun rememberXiaozhantaiCompanionName(companionObject: CompanionObjectMeta?) {
        val companionName = companionObject
            ?.takeIf { it.state == "active" && it.action == "co_create" }
            ?.name
            ?.let(::xiaozhantaiNormalizeName)
            ?: return
        val messageId = latestXiaozhantaiSaveCandidateMessageId
            ?.takeIf { xiaozhantaiSaveCandidates.containsKey(it) }
            ?: xiaozhantaiSaveCandidates.keys.lastOrNull()
            ?: return
        val candidate = xiaozhantaiSaveCandidates[messageId] ?: return
        xiaozhantaiSaveCandidates[messageId] = candidate.copy(confirmedName = companionName)
        _uiState.update { state ->
            val card = state.imagePreviewCards[messageId] ?: return@update state
            state.copy(
                imagePreviewCards = state.imagePreviewCards + (
                    messageId to card.copy(defaultShowcaseName = companionName)
                    ),
            )
        }
    }

    private fun clearLatestXiaozhantaiCandidateIfNeeded(messageId: String) {
        if (latestXiaozhantaiSaveCandidateMessageId == messageId) {
            latestXiaozhantaiSaveCandidateMessageId = xiaozhantaiSaveCandidates.keys.lastOrNull()
        }
    }

    fun requestSavePhotoToXiaozhantai(messageId: String) {
        val candidate = xiaozhantaiSaveCandidates[messageId] ?: return
        val card = _uiState.value.imagePreviewCards[messageId] ?: return
        if (!card.canSaveToXiaozhantai || card.savedToXiaozhantai || card.isSavingToXiaozhantai) return
        _uiState.update { state ->
            state.copy(
                xiaozhantaiSaveDraft = XiaozhantaiSaveDraftUiState(
                    messageId = messageId,
                    name = candidate.saveName,
                    defaultName = candidate.defaultName,
                    previewBytes = candidate.payload.previewBytes,
                    isSaving = false,
                    errorMessage = null,
                ),
            )
        }
    }

    fun updateXiaozhantaiSaveName(name: String) {
        _uiState.update { state ->
            val draft = state.xiaozhantaiSaveDraft ?: return@update state
            state.copy(
                xiaozhantaiSaveDraft = draft.copy(
                    name = name.take(24),
                    errorMessage = null,
                ),
            )
        }
    }

    fun cancelXiaozhantaiSave() {
        val draft = _uiState.value.xiaozhantaiSaveDraft
        _uiState.update { state ->
            state.copy(
                xiaozhantaiSaveDraft = null,
                strangeDoorDemo = if (draft?.source == XiaozhantaiSaveDraftSource.StrangeDoor) {
                    state.strangeDoorDemo?.copy(showcaseSaveIntentRequested = false)
                } else {
                    state.strangeDoorDemo
                },
            )
        }
    }

    fun confirmXiaozhantaiSave() {
        val saveUseCase = saveXiaozhantaiItemUseCase ?: return
        val draft = _uiState.value.xiaozhantaiSaveDraft ?: return
        if (draft.isSaving) return
        if (draft.stage == XiaozhantaiSaveDraftStage.Confirm) {
            _uiState.update { state ->
                state.copy(
                    xiaozhantaiSaveDraft = draft.copy(
                        stage = XiaozhantaiSaveDraftStage.Naming,
                        errorMessage = null,
                    ),
                )
            }
            speakAgentFeedback("给它起个名字吧")
            return
        }
        val candidate = xiaozhantaiSaveCandidates[draft.messageId] ?: return
        val itemName = xiaozhantaiNormalizeName(draft.name.ifBlank { draft.defaultName })
        val foxQuote = xiaozhantaiNormalizeFoxQuote(
            candidate.foxQuote.ifBlank { _uiState.value.agentReplyText },
        )
        _uiState.update { state ->
            val updatedPreviewCards = state.imagePreviewCards[draft.messageId]?.let { card ->
                state.imagePreviewCards + (
                    draft.messageId to card.copy(
                        isSavingToXiaozhantai = true,
                        xiaozhantaiError = null,
                    )
                    )
            } ?: state.imagePreviewCards
            state.copy(
                xiaozhantaiSaveDraft = draft.copy(
                    name = itemName,
                    isSaving = true,
                    errorMessage = null,
                ),
                imagePreviewCards = updatedPreviewCards,
            )
        }
        viewModelScope.launch(sendDispatcher) {
            runCatching {
                saveUseCase.saveCapturedPhoto(
                    XiaozhantaiSaveRequest(
                        childId = childId,
                        photoBytes = candidate.payload.bytes,
                        name = itemName,
                        foxQuote = foxQuote,
                    ),
                )
            }.onSuccess { item ->
                xiaozhantaiSaveCandidates.remove(draft.messageId)
                clearLatestXiaozhantaiCandidateIfNeeded(draft.messageId)
                _uiState.update { state ->
                    val updatedPreviewCards = state.imagePreviewCards[draft.messageId]?.let { card ->
                        state.imagePreviewCards + (
                            draft.messageId to card.copy(
                                canSaveToXiaozhantai = false,
                                isSavingToXiaozhantai = false,
                                savedToXiaozhantai = true,
                                xiaozhantaiError = null,
                            )
                            )
                    } ?: state.imagePreviewCards
                    state.copy(
                        xiaozhantaiSaveDraft = null,
                        xiaozhantaiSavedItemIdForNavigation = if (draft.source == XiaozhantaiSaveDraftSource.StrangeDoor) {
                            null
                        } else {
                            item.id
                        },
                        strangeDoorDemo = if (draft.source == XiaozhantaiSaveDraftSource.StrangeDoor) {
                            state.strangeDoorDemo?.copy(
                                demoState = StrangeDoorDemoState.ShowcaseSaved,
                                showcaseSaveIntentRequested = false,
                                showcaseSavedName = itemName,
                            )
                        } else {
                            state.strangeDoorDemo
                        },
                        xiaozhantaiSavePromptMessageId = state.xiaozhantaiSavePromptMessageId
                            ?.takeUnless { it == draft.messageId },
                        imagePreviewCards = updatedPreviewCards,
                        lightMemory = LightMemoryReducer.rememberShowcaseItem(
                            snapshot = state.lightMemory,
                            item = item,
                            nowMillis = nowMillis(),
                        ),
                    )
                }
                if (draft.source == XiaozhantaiSaveDraftSource.StrangeDoor) {
                    speakCurrentStrangeDoorState(force = true)
                }
            }.onFailure {
                _uiState.update { state ->
                    state.copy(
                        xiaozhantaiSaveDraft = state.xiaozhantaiSaveDraft?.copy(
                            isSaving = false,
                            errorMessage = "刚才没有放好，我们可以等一下再试。",
                        ),
                        imagePreviewCards = state.imagePreviewCards + (
                            draft.messageId to (state.imagePreviewCards[draft.messageId]?.copy(
                                isSavingToXiaozhantai = false,
                                xiaozhantaiError = "刚才没有放好，我们可以等一下再试。",
                            ) ?: return@update state)
                            ),
                    )
                }
            }
        }
    }

    fun consumeXiaozhantaiSaveNavigation() {
        _uiState.update { state ->
            state.copy(xiaozhantaiSavedItemIdForNavigation = null)
        }
    }

    private fun childSafeUploadFileName(fileName: String): String {
        return fileName
            .substringAfterLast('/')
            .substringAfterLast('\\')
            .ifBlank { "xiaobaohu_photo.jpg" }
            .take(96)
    }

    fun onPhotoCaptureFailed(message: String) {
        appendAgentMessage(message)
        _uiState.update {
            it.copy(
                isSending = false,
                childTurnPhaseHint = ChildTurnUiPhase.ServiceError,
                strangeDoorDemo = it.strangeDoorDemo?.copy(
                    demoState = StrangeDoorDemoState.PhotoPrompt,
                    showcaseSaveIntentRequested = false,
                ),
                agent = FoxAgentUiState(
                    mood = FoxMood.NetworkError,
                    motion = FoxMotion.NetworkError,
                    statusText = "可以再拍一次",
                ),
            )
        }
    }

    private fun handleStrangeDoorAttachmentResponseIfActive(
        attachmentResponse: AttachmentCreateResponse,
        photoMessageId: String,
        payload: PhotoUploadPayload,
    ): Boolean {
        val snapshot = _uiState.value.strangeDoorDemo ?: return false
        if (attachmentResponse.recognizedContent.imagePurpose != IMAGE_PURPOSE_SHARE) {
            return false
        }
        val transform = StrangeDoorPhotoTransformMapper.map(
            attachmentResponse.recognizedContent.toStrangeDoorPhotoRecognition(),
            mechanismType = snapshot.mechanismType,
        )
        val nextSnapshot = StrangeDoorDoorStateReducer.applyPhotoResult(
            snapshot = snapshot,
            transform = transform,
            photoMessageId = photoMessageId,
        )
        trace(
            "strange_door_photo_transform",
            "photoMessageId" to photoMessageId,
            "recognizedType" to attachmentResponse.recognizedContent.type,
            "recognizedText" to attachmentResponse.recognizedContent.text,
            "confidence" to attachmentResponse.recognizedContent.confidence,
            "mechanism" to snapshot.mechanismType,
            "objectName" to transform.objectName,
            "shapeHint" to transform.shapeHint,
            "transformedName" to transform.transformedName,
            "advanceSignal" to transform.advanceSignal,
            "canSaveToShowcase" to transform.canSaveToShowcase,
            "isUsable" to transform.isUsable,
            "from" to snapshot.shortTrace(),
            "to" to nextSnapshot.shortTrace(),
        )
        registerStrangeDoorShowcaseCandidate(
            photoMessageId = photoMessageId,
            payload = payload,
            transform = transform,
            doorState = nextSnapshot.doorState,
        )
        _uiState.update { state ->
            state.copy(
                strangeDoorDemo = nextSnapshot,
                lightMemory = LightMemoryReducer.rememberStrangeDoorPhotoResult(
                    snapshot = state.lightMemory,
                    doorSnapshot = nextSnapshot,
                    transform = transform,
                    nowMillis = nowMillis(),
                ),
                isSending = false,
                childTurnPhaseHint = null,
                quickActions = emptyList(),
                pendingImageContext = null,
                xiaozhantaiSavePromptMessageId = state.xiaozhantaiSavePromptMessageId
                    ?.takeUnless { it == photoMessageId },
                voice = state.voice.copy(
                    inputMode = VoiceInputMode.Idle,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
            )
        }
        speakStrangeDoorSnapshot(nextSnapshot)
        return true
    }

    private fun registerStrangeDoorShowcaseCandidate(
        photoMessageId: String,
        payload: PhotoUploadPayload,
        transform: StrangeDoorPhotoTransform,
        doorState: StrangeDoorState,
    ) {
        if (!transform.isUsable || !transform.canSaveToShowcase || xiaozhantaiRepository == null) return
        xiaozhantaiSaveCandidates[photoMessageId] = XiaozhantaiSaveCandidate(
            payload = payload,
            defaultName = transform.transformedName ?: transform.objectName,
            foxQuote = strangeDoorShowcaseFoxQuote(transform, doorState),
        )
        latestXiaozhantaiSaveCandidateMessageId = photoMessageId
    }

    private fun strangeDoorPhotoCanSaveToShowcase(photoMessageId: String): Boolean {
        val snapshot = _uiState.value.strangeDoorDemo ?: return false
        return snapshot.lastPhotoMessageId == photoMessageId &&
            snapshot.lastPhotoTransform?.isUsable == true &&
            snapshot.lastPhotoTransform?.canSaveToShowcase == true &&
            xiaozhantaiRepository != null
    }

    private fun strangeDoorShowcaseFoxQuote(
        transform: StrangeDoorPhotoTransform,
        doorState: StrangeDoorState,
    ): String {
        return StrangeDoorPhotoTransformMapper.feedbackLines(transform, doorState = doorState)
            .drop(2)
            .joinToString(separator = " ")
    }

    private suspend fun handleAttachmentResponse(
        attachmentResponse: AttachmentCreateResponse,
    ) {
        Log.d(TAG, "handleAttachmentResponse: id=${attachmentResponse.attachmentId}, type=${attachmentResponse.recognizedContent.type}, purpose=${attachmentResponse.recognizedContent.imagePurpose}")
        if (!attachmentResponse.hasReadyHomeworkText) {
            val reply = attachmentResponse.reply.withGeneratedAudioForAttachment()
            renderAgentReply(
                reply = reply,
                uiActions = attachmentResponse.uiActions,
                sessionState = attachmentResponse.sessionState,
                pendingImageContext = attachmentResponse.toPendingImageContext(),
            )
            return
        }

        runCatching {
            conversationSender.sendTextMessage(
                childId = childId,
                sessionId = sessionId,
                text = "这是刚才拍的题目",
                attachments = listOf(attachmentResponse.attachmentId),
            )
        }.onSuccess { response ->
            renderAgentReply(response)
        }.onFailure {
            appendAgentMessage(
                "题目我看到了，但刚才有点卡住。请家长稍后再试",
            )
            _uiState.update {
                it.copy(
                    quickActions = emptyList(),
                    sessionState = attachmentResponse.sessionState,
                    childTurnPhaseHint = ChildTurnUiPhase.ServiceError,
                    agent = FoxAgentUiState(
                        mood = FoxMood.NetworkError,
                        motion = FoxMotion.NetworkError,
                        statusText = "题目我看到了，我们等一下再试",
                    ),
                    voice = it.voice.copy(
                        inputMode = VoiceInputMode.Idle,
                        pendingTranscript = "",
                        errorMessage = null,
                    ),
                    isSending = false,
                    pendingImageContext = null,
                )
            }
        }
    }

    private suspend fun ConversationReply.withGeneratedAudioForAttachment(): ConversationReply {
        if (
            !voiceEnabled ||
            !audioUrl.isNullOrBlank() ||
            !_uiState.value.tts.isAutoReadEnabled ||
            _uiState.value.tts.isMuted
        ) {
            return this
        }
        val generatedAudioUrl = runCatching {
            feedbackTtsAudioGenerator.generateAudioUrl(
                text = text,
                emotion = emotion.toXiaobaohuTtsEmotion(),
            )
        }.getOrNull()
        return if (generatedAudioUrl.isNullOrBlank()) {
            copy(voiceEnabled = false, audioUrl = null)
        } else {
            copy(audioUrl = generatedAudioUrl)
        }
    }

    private fun continuePendingImageConversation(action: QuickActionUi) {
        val context = _uiState.value.pendingImageContext
        Log.d(TAG, "continuePendingImageConversation: action=${action.id}, hasContext=${context != null}")
        if (context == null) {
            sendText(
                action.label,
                quickActionId = normalizedQuickActionId(action.id),
            )
            return
        }
        _uiState.update { it.copy(pendingImageContext = null) }
        val text = when (action.id) {
            "give_name", "image_naming" -> "起个名字"
            "tell_story", "make_story", "image_story" -> "编个小故事"
            "ask_what_is_this" -> "这是什么？"
            else -> "给小白狐看看"
        }
        sendTextWithAttachments(
            text,
            listOf(context.attachmentId),
            quickActionId = normalizedQuickActionId(action.id),
        )
    }

    private fun activeSpeechInputController(cacheDirectory: File): SpeechInputController {
        val existing = speechInputController
        if (existing != null) return existing
        return speechInputControllerFactory(cacheDirectory).also {
            speechInputController = it
            if (it is BackendSpeechInputController && it.recorder is AndroidWavAudioRecorder) {
                lastRecorder = it.recorder as AndroidWavAudioRecorder
            }
        }
    }

    private fun applySpeechInputResult(result: SpeechInputResult) {
        when (result) {
            is SpeechInputResult.Transcript -> {
                trace(
                    "asr_transcript_received",
                    "text" to result.text,
                    "trimmed" to result.text.trim(),
                    "voiceConfirmBeforeSend" to voiceConfirmBeforeSend,
                    "provider" to result.provider,
                    "model" to result.model,
                    "durationMs" to result.durationMs,
                )
                if (!voiceConfirmBeforeSend) {
                    val transcript = result.text.trim()
                    if (transcript.isNotEmpty()) {
                        if (routeLocalExperienceToConversationIfNeeded(transcript)) {
                            trace("asr_transcript_route", "route" to "conversation_after_local_exit", "text" to transcript)
                            _uiState.update { state ->
                                state.copy(
                                    isSending = false,
                                    childTurnPhaseHint = ChildTurnUiPhase.Sending,
                                    voice = state.voice.copy(
                                        inputMode = VoiceInputMode.Idle,
                                        pendingTranscript = "",
                                        errorMessage = null,
                                    ),
                                    agent = childInteractionPresentation(
                                        phaseHint = ChildTurnUiPhase.Sending,
                                    ).agent,
                                )
                            }
                            sendText(transcript)
                            return
                        }
                        if (submitStrangeDoorShowcaseName(transcript)) {
                            trace("asr_transcript_route", "route" to "strange_door_showcase_name", "text" to transcript)
                            return
                        }
                        if (answerStrangeDoorRiddle(transcript)) {
                            trace("asr_transcript_route", "route" to "strange_door_riddle", "text" to transcript)
                            return
                        }
                        if (handleLanguageGameText(transcript)) {
                            trace("asr_transcript_route", "route" to "language_game", "text" to transcript)
                            return
                        }
                        trace("asr_transcript_route", "route" to "conversation", "text" to transcript)
                        _uiState.update { state ->
                            state.copy(
                                isSending = false,
                                childTurnPhaseHint = ChildTurnUiPhase.Sending,
                                voice = state.voice.copy(
                                    inputMode = VoiceInputMode.Idle,
                                    pendingTranscript = "",
                                    errorMessage = null,
                                ),
                                agent = childInteractionPresentation(
                                    phaseHint = ChildTurnUiPhase.Sending,
                                ).agent,
                            )
                        }
                        sendText(transcript)
                        return
                    }
                    trace("asr_transcript_empty_after_trim", "raw" to result.text)
                }
                trace("asr_transcript_pending_confirmation", "text" to result.text)
                _uiState.update { state ->
                    state.copy(
                        isSending = false,
                        childTurnPhaseHint = null,
                        voice = state.voice.copy(
                            inputMode = VoiceInputMode.PendingTranscript,
                            pendingTranscript = result.text,
                            errorMessage = null,
                        ),
                        agent = FoxAgentUiState(
                            mood = FoxMood.Listening,
                            motion = FoxMotion.ListeningTail,
                            statusText = "我听到了，可以改一下再发",
                        ),
                    )
                }
            }
            is SpeechInputResult.NeedsRetry -> {
                trace("asr_needs_retry", "message" to result.message)
                appendAgentMessage(result.message)
                _uiState.update { state ->
                    state.copy(
                        isSending = false,
                        childTurnPhaseHint = ChildTurnUiPhase.NeedsRetry,
                        voice = state.voice.copy(
                            inputMode = VoiceInputMode.NeedsRetry,
                            pendingTranscript = "",
                            errorMessage = result.message,
                        ),
                        agent = childInteractionPresentation(
                            phaseHint = ChildTurnUiPhase.NeedsRetry,
                        ).agent,
                    )
                }
                speakAgentFeedback(result.message)
            }
            is SpeechInputResult.PolicyBlocked -> {
                trace("asr_policy_blocked", "message" to result.message)
                appendAgentMessage(result.message)
                _uiState.update { state ->
                    state.copy(
                        isSending = false,
                        childTurnPhaseHint = ChildTurnUiPhase.ServiceError,
                        voice = state.voice.copy(
                            inputMode = VoiceInputMode.Failed,
                            pendingTranscript = "",
                            errorMessage = result.message,
                        ),
                        agent = baseAgentState,
                    )
                }
            }
            is SpeechInputResult.Failed -> {
                trace("asr_failed", "message" to result.message)
                appendAgentMessage(result.message)
                _uiState.update { state ->
                    state.copy(
                        isSending = false,
                        childTurnPhaseHint = ChildTurnUiPhase.ServiceError,
                        voice = state.voice.copy(
                            inputMode = VoiceInputMode.Failed,
                            pendingTranscript = "",
                            errorMessage = result.message,
                        ),
                        agent = childInteractionPresentation(
                            phaseHint = ChildTurnUiPhase.ServiceError,
                        ).agent,
                    )
                }
            }
        }
    }

    fun attachTtsController(controller: TtsController) {
        if (ttsController === controller) return
        ttsController.stop()
        ttsController = controller
        audioSegmentQueuePlayer.updateController(controller)
        _uiState.update { state ->
            state.copy(
                tts = state.tts.copy(
                    isAvailable = true,
                    isInitializing = false,
                    isInitialized = false,
                    isSpeaking = false,
                    isSpeakingPending = false,
                    errorMessage = null,
                ),
            )
        }
        speakCurrentStrangeDoorState(force = true)
    }

    fun stopTtsPlayback() {
        stopCurrentTts(restoreBaseAgent = true)
    }

    fun toggleTtsMuted() {
        val willMute = !_uiState.value.tts.isMuted
        if (willMute) {
            stopCurrentTts(restoreBaseAgent = true)
        }
        _uiState.update { state ->
            state.copy(
                tts = state.tts.copy(
                    isMuted = willMute,
                    isSpeaking = if (willMute) false else state.tts.isSpeaking,
                    isSpeakingPending = if (willMute) {
                        false
                    } else {
                        state.tts.isSpeakingPending
                    },
                    errorMessage = null,
                ),
            )
        }
    }

    fun shutdownTts() {
        stopCurrentTts(restoreBaseAgent = true)
        ttsController.shutdown()
        ttsController = NoOpTtsController
    }

    override fun onCleared() {
        voiceRecordingAutoStopJob?.cancel()
        cancelNaturalWaitingTimeout()
        shutdownTts()
        speechInputController?.shutdown()
        super.onCleared()
    }

    internal fun recordChildMessage(text: String) {
        trace("child_message_recorded", "text" to text)
        appendMessage(
            ChatMessage(
                id = nextMessageId("child"),
                author = MessageAuthor.Child,
                text = text,
            ),
        )
    }

    internal fun renderAgentReply(
        response: ConversationMessageResponse,
        replaceMessageId: String? = null,
    ) {
        renderAgentReply(
            reply = response.reply,
            uiActions = response.uiActions,
            sessionState = response.sessionState,
            pendingImageContext = _uiState.value.pendingImageContext,
            replaceMessageId = replaceMessageId,
        )
    }

    internal fun renderAgentReply(
        reply: ConversationReply,
        uiActions: List<ConversationUiAction>,
        sessionState: ConversationSessionState,
        pendingImageContext: PendingImageContextUiState? = _uiState.value.pendingImageContext,
        replaceMessageId: String? = null,
    ) {
        trace(
            "agent_reply_render",
            "text" to reply.text,
            "voiceEnabled" to reply.voiceEnabled,
            "audioUrlPresent" to !reply.audioUrl.isNullOrBlank(),
            "emotion" to reply.emotion,
            "agentMotion" to reply.agentMotion,
            "activeScene" to sessionState.activeScene,
            "quickActions" to uiActions.flatMap { group -> group.actions.map { it.label } },
            "replaceMessageId" to replaceMessageId,
        )
        rememberXiaozhantaiCompanionName(sessionState.companionObject)
        if (replaceMessageId.isNullOrBlank()) {
            appendAgentMessage(reply.text)
        } else {
            replaceMessageText(replaceMessageId, reply.text)
        }
        streamingAgentMessageId = null
        stopCurrentTts(restoreBaseAgent = false)

        val nextAgentState = reply.toFoxAgentUiState()
        baseAgentState = nextAgentState
        val mergedSessionState = sessionState.mergeWith(_uiState.value.sessionState)
        _uiState.update { state ->
            state.copy(
                quickActions = uiActions.toQuickActionUi(),
                sessionState = mergedSessionState,
                agent = nextAgentState,
                childTurnPhaseHint = null,
                voice = state.voice.withReplyVoice(reply),
                tts = state.tts.copy(
                    isSpeaking = false,
                    isSpeakingPending = false,
                    isAvailable = true,
                    errorMessage = null,
                    lastFailureReason = null,
                ),
                isSending = false,
                pendingImageContext = pendingImageContext,
            )
        }
        maybeAutoReadReply(reply)
    }

    private suspend fun streamTextWithAttachments(
        text: String,
        attachments: List<String>,
        quickActionId: String? = null,
    ): Boolean {
        var doneReceived = false
        trace(
            "conversation_stream_start",
            "text" to text,
            "attachmentsCount" to attachments.size,
            "quickActionId" to quickActionId,
            "includeTts" to (_uiState.value.tts.isAutoReadEnabled && !_uiState.value.tts.isMuted),
        )
        conversationSender.streamTextMessage(
            childId = childId,
            sessionId = sessionId,
            text = text,
            attachments = attachments,
            quickActionId = quickActionId,
            includeTts = _uiState.value.tts.isAutoReadEnabled && !_uiState.value.tts.isMuted,
            onEvent = { event ->
                applyStreamEvent(event)
                if (event.type == "done") {
                    doneReceived = true
                }
            },
        )
        return doneReceived
    }

    private var slowHint5sJob: Job? = null
    private var slowHint8sJob: Job? = null

    internal fun applyStreamEvent(event: ConversationStreamEvent) {
        when (event.type) {
            "text_delta" -> Unit
            "audio_ready" -> trace(
                "conversation_stream_event",
                "type" to event.type,
                "requestId" to event.requestId,
                "seq" to event.seq,
                "audioText" to event.audioText,
                "audioUrlPresent" to !event.audioUrl.isNullOrBlank(),
            )
            "text_final" -> trace(
                "conversation_stream_event",
                "type" to event.type,
                "requestId" to event.requestId,
                "seq" to event.seq,
                "finalText" to event.finalText,
            )
            "route_decision" -> trace(
                "conversation_stream_event",
                "type" to event.type,
                "requestId" to event.requestId,
                "seq" to event.seq,
                "activeScene" to event.activeScene,
                "riskLevel" to event.riskLevel,
                "requiresParentAttention" to event.requiresParentAttention,
                "quickActions" to event.payload.toStreamQuickActionUi().map { it.label },
            )
            "error" -> trace(
                "conversation_stream_event",
                "type" to event.type,
                "requestId" to event.requestId,
                "seq" to event.seq,
                "safeMessage" to event.safeMessage,
            )
            else -> trace(
                "conversation_stream_event",
                "type" to event.type,
                "requestId" to event.requestId,
                "seq" to event.seq,
            )
        }
        when (event.type) {
            "session_started" -> {
                Log.d(TAG, "[LatencyTrace] stage=session_started request=${event.requestId}")
                stopCurrentTts(restoreBaseAgent = false)
                _uiState.update { state ->
                    state.copy(
                        isSending = true,
                        childTurnPhaseHint = ChildTurnUiPhase.Thinking,
                        agent = childInteractionPresentation(
                            phaseHint = ChildTurnUiPhase.Thinking,
                        ).agent,
                    )
                }
                // SLA: T0-5s 若仍无模型文本，显示 "小白狐还在想怎么说清楚"
                scheduleSlowHint5s()
            }
            "route_decision" -> applyStreamRoute(event)
            "text_delta" -> {
                cancelSlowHints()
                if (streamingAgentMessageId == null) {
                    Log.d(TAG, "[LatencyTrace] stage=text_visible")
                    scheduleTtsSlowHint()
                }
                appendToStreamingAgentBubble(event.delta)
            }
            "sentence_ready" -> Unit
            "audio_ready" -> {
                Log.d(TAG, "[LatencyTrace] stage=audio_ready index=${event.payload.optInt("index", 0)}")
                enqueueStreamAudio(event)
            }
            "text_final" -> event.finalText?.let(::replaceStreamingAgentText)
            "done" -> {
                cancelSlowHints()
                Log.d(TAG, "[LatencyTrace] stage=stream_done")
                streamingAgentMessageId = null
                _uiState.update { state ->
                    state.copy(
                        isSending = false,
                        childTurnPhaseHint = null,
                    )
                }
            }
            "error" -> applyStreamError(event)
        }
    }

    private fun applyStreamRoute(event: ConversationStreamEvent) {
        val activeScene = event.activeScene ?: "conversation.open"
        val routeSessionState = ConversationSessionState(
            baseScene = event.payload.optString("baseScene", event.payload.optString("base_scene", activeScene)),
            activeScene = activeScene,
            needsInput = event.payload.optString("needsInput").takeIf { it.isNotBlank() }
                ?: event.payload.optString("needs_input").takeIf { it.isNotBlank() },
            requiresParentAttention = event.requiresParentAttention,
            companionObject = event.payload.optJSONObject("companion_object")?.let {
                com.childai.companion.data.conversation.CompanionObjectMeta.fromJson(it)
            },
        )
        rememberXiaozhantaiCompanionName(routeSessionState.companionObject)
        val nextSessionState = routeSessionState.mergeWith(_uiState.value.sessionState)
        val nextAgentState = ConversationReply(
            type = "agent_message",
            text = "",
            voiceEnabled = true,
            audioUrl = null,
            emotion = event.emotion,
            agentMotion = event.agentMotion,
        ).toFoxAgentUiState()
        baseAgentState = nextAgentState
        _uiState.update { state ->
            state.copy(
                sessionState = nextSessionState,
                agent = nextAgentState,
                quickActions = event.payload.toStreamQuickActionUi(),
            )
        }
    }

    private fun appendToStreamingAgentBubble(delta: String) {
        if (delta.isBlank()) return
        val messageId = streamingAgentMessageId
        if (messageId == null) {
            val newMessage = ChatMessage(
                id = nextMessageId("agent-stream"),
                author = MessageAuthor.Agent,
                text = delta,
            )
            streamingAgentMessageId = newMessage.id
            appendMessage(newMessage)
            return
        }
        trace(
            "message_stream_delta_appended",
            "messageId" to messageId,
            "delta" to delta,
        )
        _uiState.update { state ->
            val nextAgentReplyText = state.messages
                .firstOrNull { it.id == messageId }
                ?.let { it.text + delta }
                ?: state.agentReplyText
            state.copy(
                messages = state.messages.map { message ->
                    if (message.id == messageId) {
                        message.copy(text = message.text + delta)
                    } else {
                        message
                    }
                },
                agentReplyText = nextAgentReplyText,
            )
        }
    }

    private fun replaceStreamingAgentText(text: String) {
        val messageId = streamingAgentMessageId
        if (messageId == null) {
            appendToStreamingAgentBubble(text)
        } else {
            replaceMessageText(messageId, text)
        }
    }

    private fun enqueueStreamAudio(event: ConversationStreamEvent) {
        val audioUrl = event.audioUrl ?: return
        if (!_uiState.value.tts.isAutoReadEnabled || _uiState.value.tts.isMuted) return
        ttsSlowHintJob?.cancel()
        _uiState.update { state ->
            state.copy(
                tts = state.tts.copy(
                    isSpeakingPending = !state.tts.isSpeaking,
                    isAvailable = true,
                    errorMessage = null,
                ),
            )
        }
        audioSegmentQueuePlayer.enqueue(
            AudioSegment(
                audioUrl = audioUrl,
                text = event.audioText,
                index = event.payload.optInt("index", 0),
                requestId = event.requestId,
                turnId = event.requestId,
            ),
        )
    }

    private fun applyStreamError(event: ConversationStreamEvent) {
        val message = event.safeMessage
            ?: "刚才有点卡住，字还在"
        val hasPartialText = streamingAgentMessageId != null
        if (!hasPartialText) {
            appendAgentMessage(message)
        }
        _uiState.update { state ->
            state.copy(
                tts = state.tts.copy(errorMessage = message),
                childTurnPhaseHint = if (hasPartialText) {
                    state.childTurnPhaseHint
                } else {
                    ChildTurnUiPhase.ServiceError
                },
                agent = if (hasPartialText) state.agent else FoxAgentUiState(
                    mood = FoxMood.NetworkError,
                    motion = FoxMotion.NetworkError,
                    statusText = "请家长帮忙看一下网络",
                ),
            )
        }
    }

    private fun uploadFailureMessage(imagePurpose: String): String {
        return if (imagePurpose == IMAGE_PURPOSE_HOMEWORK) {
            "这道题刚才没弄好。我们先停一下，请家长稍后再试"
        } else {
            "这张图刚才没弄好。我们先停一下，请家长稍后再试"
        }
    }

    private fun followupFailureMessage(attachments: List<String>): String {
        val context = _uiState.value.pendingImageContext
        if (attachments.isEmpty() || context == null) {
            return "小白狐刚才有点卡住。我们先停一下，请家长检查网络后再试"
        }
        return if (context.imagePurpose == IMAGE_PURPOSE_HOMEWORK) {
            "题目我看到了，但刚才有点卡住。请家长稍后再试"
        } else {
            "图片我看到了，但刚才有点卡住。请家长稍后再试"
        }
    }

    private fun appendAgentMessage(text: String) {
        trace("agent_message_recorded", "text" to text)
        appendMessage(
            ChatMessage(
                id = nextMessageId("agent"),
                author = MessageAuthor.Agent,
                text = text,
            ),
        )
    }

    private fun appendMessage(message: ChatMessage) {
        trace(
            "message_appended",
            "messageId" to message.id,
            "author" to message.author,
            "text" to message.text,
        )
        _uiState.update { state ->
            state.copy(
                messages = state.messages + message,
                agentReplyText = if (message.author == MessageAuthor.Agent) {
                    message.text
                } else {
                    state.agentReplyText
                },
            )
        }
    }

    private fun replaceMessageText(messageId: String, text: String) {
        trace(
            "message_replaced",
            "messageId" to messageId,
            "text" to text,
        )
        _uiState.update { state ->
            val replacedMessage = state.messages.firstOrNull { it.id == messageId }
            state.copy(
                messages = state.messages.map { message ->
                    if (message.id == messageId) {
                        message.copy(text = text)
                    } else {
                        message
                    }
                },
                agentReplyText = if (replacedMessage?.author == MessageAuthor.Agent) {
                    text
                } else {
                    state.agentReplyText
                },
            )
        }
    }

    private fun speakAgentFeedback(text: String) {
        val trimmedText = text.trim()
        val currentTts = _uiState.value.tts
        if (
            trimmedText.isBlank() ||
            !currentTts.isAutoReadEnabled ||
            currentTts.isMuted
        ) {
            trace(
                "local_tts_feedback_skipped",
                "reason" to when {
                    trimmedText.isBlank() -> "blank"
                    !currentTts.isAutoReadEnabled -> "auto_read_disabled"
                    currentTts.isMuted -> "muted"
                    else -> "unknown"
                },
                "text" to trimmedText,
            )
            return
        }
        trace("local_tts_feedback_request", "text" to trimmedText)
        viewModelScope.launch(sendDispatcher) {
            val audioUrl = generateFeedbackAudioUrlWithRetry(trimmedText)
            if (audioUrl.isNullOrBlank()) {
                Log.w(TAG, "speakAgentFeedback: audioUrl missing after retry")
                trace("local_tts_feedback_audio_missing", "text" to trimmedText)
                return@launch
            }
            trace(
                "local_tts_feedback_audio_ready",
                "text" to trimmedText,
                "audioUrlPresent" to true,
            )
            maybeAutoReadReply(
                ConversationReply(
                    type = "agent_message",
                    text = trimmedText,
                    voiceEnabled = true,
                    audioUrl = audioUrl,
                    emotion = "encourage",
                    agentMotion = "listening_tail",
                ),
            )
        }
    }

    private suspend fun generateFeedbackAudioUrlWithRetry(text: String): String? {
        repeat(2) { attemptIndex ->
            trace(
                "local_tts_feedback_generate_attempt",
                "attempt" to attemptIndex + 1,
                "text" to text,
            )
            val audioUrl = runCatching {
                feedbackTtsAudioGenerator.generateAudioUrl(
                    text = text,
                    emotion = "encourage",
                )
            }.onFailure { error ->
                Log.w(
                    TAG,
                    "generateFeedbackAudioUrl failed attempt=${attemptIndex + 1}",
                    error,
                )
                trace(
                    "local_tts_feedback_generate_failed",
                    "attempt" to attemptIndex + 1,
                    "error" to error::class.simpleName,
                    "message" to error.message,
                    "text" to text,
                )
            }.getOrNull()
            if (!audioUrl.isNullOrBlank()) return audioUrl
        }
        return null
    }

    private fun speakCurrentStrangeDoorState(force: Boolean = false) {
        val snapshot = _uiState.value.strangeDoorDemo ?: return
        speakStrangeDoorSnapshot(snapshot, force = force)
    }

    private fun speakStrangeDoorSnapshot(
        snapshot: StrangeDoorDemoSnapshot,
        force: Boolean = false,
    ) {
        val model = snapshot.toHomeEventUiModel()
        val lines = buildList {
            if (snapshot.demoState == StrangeDoorDemoState.ChoosingMethod) {
                add(model.title)
            }
            if (model.bubbleLines.isNotEmpty()) {
                addAll(model.bubbleLines)
            } else {
                model.question?.takeIf { it.isNotBlank() }?.let(::add)
            }
        }
        val text = lines.joinToString(separator = "\n").trim()
        if (text.isBlank()) return
        if (!force && lastStrangeDoorNarrationText == text) {
            trace(
                "strange_door_speak_skipped",
                "reason" to "duplicate",
                "snapshot" to snapshot.shortTrace(),
                "text" to text,
            )
            return
        }
        lastStrangeDoorNarrationText = text
        trace(
            "strange_door_speak",
            "force" to force,
            "snapshot" to snapshot.shortTrace(),
            "text" to text,
        )
        speakAgentFeedback(text)
    }

    private fun maybeShowLanguageGameEntryPromptAfterOpening() {
        if (!DevSettings.LANGUAGE_GAME_AUTO_PROMPT_ENABLED) {
            trace("language_game_auto_prompt_skipped", "reason" to "disabled")
            return
        }
        if (languageGameAutoPromptShown || languageGameDismissedForLifecycle) {
            trace(
                "language_game_auto_prompt_skipped",
                "reason" to if (languageGameAutoPromptShown) "already_shown" else "dismissed_for_lifecycle",
            )
            return
        }
        if (_uiState.value.strangeDoorDemo != null) {
            trace("language_game_auto_prompt_skipped", "reason" to "strange_door_active")
            return
        }
        if (_uiState.value.languageGame != null) {
            trace("language_game_auto_prompt_skipped", "reason" to "language_game_active")
            return
        }
        if (_uiState.value.messages.any { it.author == MessageAuthor.Child }) {
            trace("language_game_auto_prompt_skipped", "reason" to "child_already_spoke")
            return
        }
        languageGameAutoPromptShown = true
        trace("language_game_auto_prompt_show")
        _uiState.update { state ->
            state.copy(
                languageGame = LanguageGameReducer.entryPrompt(autoPromptShown = true),
                quickActions = emptyList(),
                lightMemory = LightMemoryReducer.withOpeningRecallEligibility(
                    snapshot = state.lightMemory,
                    strangeDoorActive = false,
                    languageGameActive = true,
                ),
            )
        }
    }

    private fun handleLanguageGameText(text: String): Boolean {
        val trimmed = text.trim()
        if (trimmed.isBlank()) {
            trace("language_game_text_not_consumed", "reason" to "blank_input")
            return false
        }
        if (_uiState.value.strangeDoorDemo != null) {
            trace("language_game_text_not_consumed", "reason" to "strange_door_active", "text" to trimmed)
            return false
        }
        val snapshot = _uiState.value.languageGame
        trace(
            "language_game_text_received",
            "text" to trimmed,
            "snapshot" to snapshot?.shortTrace(),
        )
        if (snapshot?.state == LanguageGameState.BrainTeaser) {
            val brainTeaser = snapshot.brainTeaser
            if (brainTeaser?.gameState == BrainTeaserGameState.Question ||
                brainTeaser?.gameState == BrainTeaserGameState.Hint
            ) {
                val nextSnapshot = LanguageGameReducer.applyBrainTeaserAnswer(
                    snapshot = snapshot,
                    transcript = trimmed,
                )
                trace(
                    "language_game_answer",
                    "game" to "BrainTeaser",
                    "input" to trimmed,
                    "from" to snapshot.shortTrace(),
                    "to" to nextSnapshot.shortTrace(),
                )
                showLanguageGameSnapshot(
                    nextSnapshot,
                    forceSpeak = true,
                )
                return true
            }
            if (handleLanguageGameCommand(trimmed)) return true
            return true
        }
        if (snapshot?.state == LanguageGameState.WordChain) {
            if (handleLanguageGameCommand(trimmed)) return true
            val wordChainState = snapshot.wordChain?.gameState
            if (wordChainState != WordChainGameState.Finished) {
                val nextSnapshot = LanguageGameReducer.applyWordChainAnswer(
                    snapshot = snapshot,
                    transcript = trimmed,
                )
                trace(
                    "language_game_answer",
                    "game" to "WordChain",
                    "input" to trimmed,
                    "from" to snapshot.shortTrace(),
                    "to" to nextSnapshot.shortTrace(),
                )
                showLanguageGameSnapshot(
                    nextSnapshot,
                    forceSpeak = true,
                )
            } else {
                trace(
                    "language_game_answer_ignored",
                    "reason" to "word_chain_finished",
                    "input" to trimmed,
                    "snapshot" to snapshot.shortTrace(),
                )
            }
            return true
        }
        if (snapshot?.state == LanguageGameState.Riddle) {
            val riddleState = snapshot.riddle?.gameState
            if (riddleState == RiddleGameState.Question ||
                riddleState == RiddleGameState.Hint
            ) {
                val nextSnapshot = LanguageGameReducer.applyRiddleAnswer(
                    snapshot = snapshot,
                    transcript = trimmed,
                )
                trace(
                    "language_game_answer",
                    "game" to "Riddle",
                    "input" to trimmed,
                    "from" to snapshot.shortTrace(),
                    "to" to nextSnapshot.shortTrace(),
                )
                showLanguageGameSnapshot(
                    nextSnapshot,
                    forceSpeak = true,
                )
                return true
            }
            if (handleLanguageGameCommand(trimmed)) return true
            return true
        }
        if (handleLanguageGameCommand(trimmed)) return true
        return false
    }

    private fun handleLanguageGameCommand(text: String): Boolean {
        return when {
            text.contains("脑筋急转弯") -> {
                trace("language_game_command", "command" to "start_brain_teaser", "text" to text)
                startBrainTeaserGame()
                true
            }
            text.contains("词语接龙") ||
                text.contains("接龙") -> {
                trace("language_game_command", "command" to "start_word_chain", "text" to text)
                startWordChainGame()
                true
            }
            text.contains("猜谜语") ||
                text.contains("谜语") -> {
                trace("language_game_command", "command" to "start_riddle", "text" to text)
                startRiddleGame()
                true
            }
            text.contains("玩游戏") -> {
                trace("language_game_command", "command" to "open_menu", "text" to text)
                openLanguageGameMenu()
                true
            }
            text.contains("随便聊聊") ||
                text.contains("先聊别的") -> {
                trace("language_game_command", "command" to "exit_to_chat", "text" to text)
                exitLanguageGame()
                true
            }
            text.contains("换个游戏") -> {
                trace("language_game_command", "command" to "change_game", "text" to text)
                returnToLanguageGameMenu()
                true
            }
            text.contains("下一题") -> {
                trace("language_game_command", "command" to "next_question", "text" to text)
                when (_uiState.value.languageGame?.state) {
                    LanguageGameState.BrainTeaser -> nextBrainTeaserQuestion()
                    LanguageGameState.Riddle -> nextRiddleQuestion()
                    else -> return false
                }
                true
            }
            text.contains("再玩一次") &&
                _uiState.value.languageGame?.state == LanguageGameState.WordChain -> {
                trace("language_game_command", "command" to "restart_word_chain", "text" to text)
                restartWordChainGame()
                true
            }
            text.contains("告诉我答案") -> {
                trace("language_game_command", "command" to "reveal_answer", "text" to text)
                when (_uiState.value.languageGame?.state) {
                    LanguageGameState.BrainTeaser -> revealBrainTeaserAnswer()
                    LanguageGameState.Riddle -> revealRiddleAnswer()
                    else -> return false
                }
                true
            }
            text.contains("给我提示") -> {
                trace("language_game_command", "command" to "show_hint", "text" to text)
                when (_uiState.value.languageGame?.state) {
                    LanguageGameState.BrainTeaser -> requestBrainTeaserHint()
                    LanguageGameState.Riddle -> requestRiddleHint()
                    else -> return false
                }
                true
            }
            else -> false
        }
    }

    private fun showLanguageGameSnapshot(
        snapshot: LanguageGameSnapshot,
        forceSpeak: Boolean = false,
    ) {
        if (_uiState.value.strangeDoorDemo != null) {
            trace(
                "language_game_show_ignored",
                "reason" to "strange_door_active",
                "target" to snapshot.shortTrace(),
            )
            return
        }
        trace(
            "language_game_show",
            "target" to snapshot.shortTrace(),
            "forceSpeak" to forceSpeak,
        )
        childInteractionStarted = true
        cancelNaturalWaitingTimeout()
        stopCurrentTts(restoreBaseAgent = true)
        _uiState.update { state ->
            state.copy(
                languageGame = snapshot,
                quickActions = emptyList(),
                childTurnPhaseHint = null,
                pendingImageContext = null,
                isSending = false,
                lightMemory = LightMemoryReducer.withOpeningRecallEligibility(
                    snapshot = state.lightMemory,
                    strangeDoorActive = state.strangeDoorDemo != null,
                    languageGameActive = true,
                ),
                voice = state.voice.copy(
                    inputMode = VoiceInputMode.Idle,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
            )
        }
        speakLanguageGameSnapshot(snapshot, force = forceSpeak)
    }

    private fun speakLanguageGameSnapshot(
        snapshot: LanguageGameSnapshot,
        force: Boolean = false,
    ) {
        val text = snapshot.toLanguageGameEntryUiModel()
            .lines
            .joinToString(separator = "\n")
            .trim()
        if (text.isBlank()) return
        if (!force && lastLanguageGameNarrationText == text) {
            trace(
                "language_game_speak_skipped",
                "reason" to "duplicate",
                "snapshot" to snapshot.shortTrace(),
                "text" to text,
            )
            return
        }
        lastLanguageGameNarrationText = text
        trace(
            "language_game_speak",
            "force" to force,
            "snapshot" to snapshot.shortTrace(),
            "text" to text,
        )
        speakAgentFeedback(text)
    }

    private fun nextMessageId(prefix: String): String {
        nextMessageIndex += 1
        return "$prefix-$nextMessageIndex"
    }

    private fun maybeAutoReadReply(reply: ConversationReply) {
        val currentTts = _uiState.value.tts
        if (
            !reply.voiceEnabled ||
            reply.text.isBlank() ||
            !currentTts.isAutoReadEnabled ||
            currentTts.isMuted
        ) {
            trace(
                "auto_tts_skipped",
                "reason" to when {
                    !reply.voiceEnabled -> "voice_disabled"
                    reply.text.isBlank() -> "blank_text"
                    !currentTts.isAutoReadEnabled -> "auto_read_disabled"
                    currentTts.isMuted -> "muted"
                    else -> "unknown"
                },
                "text" to reply.text,
                "audioUrlPresent" to !reply.audioUrl.isNullOrBlank(),
            )
            return
        }

        val token = nextTtsToken()
        trace(
            "auto_tts_speak_request",
            "turnId" to "local_tts_$token",
            "text" to reply.text,
            "audioUrlPresent" to !reply.audioUrl.isNullOrBlank(),
        )
        val accepted = ttsController.speak(
            request = TtsRequest(
                text = reply.text,
                voiceProfile = VoiceProfile.default(),
                audioUrl = reply.audioUrl,
                backendBaseUrl = DevSettings.conversationApiBaseUrl,
                turnId = "local_tts_$token",
            ),
            callbacks = TtsCallbacks(
                onDiagnostics = { diagnostics ->
                    if (token == ttsToken) {
                        _uiState.update { state ->
                            state.copy(tts = state.tts.withDiagnostics(diagnostics))
                        }
                    }
                },
                onStart = {
                    if (token == ttsToken) {
                        trace("auto_tts_playback_started", "turnId" to "local_tts_$token", "text" to reply.text)
                        _uiState.update { state ->
                            state.copy(
                                agent = baseAgentState.asSpeaking(),
                                tts = state.tts.copy(
                                    isSpeaking = true,
                                    isSpeakingPending = false,
                                    isAvailable = true,
                                    errorMessage = null,
                                ),
                            )
                        }
                    }
                },
                onDone = {
                    if (token == ttsToken) {
                        trace("auto_tts_playback_done", "turnId" to "local_tts_$token", "text" to reply.text)
                        _uiState.update { state ->
                            state.copy(
                                agent = baseAgentState,
                                tts = state.tts.copy(
                                    isSpeaking = false,
                                    isSpeakingPending = false,
                                ),
                            )
                        }
                        showWaitingForChildAfterTts()
                    }
                },
                onError = { message ->
                    if (token == ttsToken) {
                        trace(
                            "auto_tts_playback_error",
                            "turnId" to "local_tts_$token",
                            "text" to reply.text,
                            "message" to message,
                        )
                        _uiState.update { state ->
                            state.copy(
                                agent = baseAgentState,
                                tts = state.tts.copy(
                                    isSpeaking = false,
                                    isSpeakingPending = false,
                                    isAvailable = state.tts.isAvailable,
                                    errorMessage = message.ifBlank {
                                        TtsController.UNAVAILABLE_MESSAGE
                                    },
                                ),
                            )
                        }
                    }
                },
            ),
        )

        if (!accepted) {
            trace(
                "auto_tts_speak_rejected",
                "turnId" to "local_tts_$token",
                "text" to reply.text,
            )
            _uiState.update { state ->
                state.copy(
                    agent = baseAgentState,
                    tts = state.tts.copy(
                        isSpeaking = false,
                        isSpeakingPending = false,
                        isAvailable = false,
                        errorMessage = state.tts.errorMessage
                            ?: TtsController.UNAVAILABLE_MESSAGE,
                        lastFailureReason = state.tts.lastFailureReason
                            ?: "TtsController.speak returned false",
                    ),
                )
            }
            return
        }

        _uiState.update { state ->
            state.copy(
                agent = baseAgentState.asSpeakingPending(),
                tts = state.tts.copy(
                    isSpeaking = state.tts.isSpeaking,
                    isSpeakingPending = !state.tts.isSpeaking,
                    isAvailable = true,
                    errorMessage = null,
                    lastRequestedTextPreview = reply.text.previewForDiagnostics(),
                    lastFailureReason = null,
                ),
            )
        }
    }

    private fun stopCurrentTts(restoreBaseAgent: Boolean) {
        nextTtsToken()
        audioSegmentQueuePlayer.stopAndClear()
        _uiState.update { state ->
            state.copy(
                agent = if (restoreBaseAgent) baseAgentState else state.agent,
                childTurnPhaseHint = if (restoreBaseAgent) null else state.childTurnPhaseHint,
                tts = state.tts.copy(
                    isSpeaking = false,
                    isSpeakingPending = false,
                ),
            )
        }
    }

    private fun nextTtsToken(): Int {
        ttsToken += 1
        return ttsToken
    }

    private fun clearVoiceInputState() {
        _uiState.update {
            it.copy(
                childTurnPhaseHint = null,
                voice = it.voice.copy(
                    inputMode = VoiceInputMode.Idle,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
            )
        }
    }

    fun requestOpeningGreeting() {
        if (_uiState.value.strangeDoorDemo != null) {
            openingDeferredByStrangeDoor = true
            Log.d(TAG, "[LatencyTrace] stage=opening_deferred reason=strange_door_demo")
            trace("opening_deferred", "reason" to "strange_door_demo")
            return
        }
        if (openingRequested) {
            trace("opening_ignored", "reason" to "already_requested")
            return
        }
        openingRequested = true
        Log.d(TAG, "[LatencyTrace] stage=opening_start")
        trace("opening_request_start")
        // 0-1 秒：立即显示本地确定性状态 "我在这儿"
        _uiState.update { state ->
            state.copy(
                childTurnPhaseHint = null,
                lightMemory = LightMemoryReducer.withOpeningRecallEligibility(
                    snapshot = state.lightMemory,
                    strangeDoorActive = state.strangeDoorDemo != null,
                    languageGameActive = state.languageGame != null,
                ),
                agent = FoxAgentUiState(
                    mood = FoxMood.Warm,
                    motion = FoxMotion.GentleIdle,
                    statusText = "我在这儿",
                ),
            )
        }
        // 1-3 秒降级：若个性化 opening 未返回，显示本地短句
        val openingFallbackJob = viewModelScope.launch(sendDispatcher) {
            delay(1500)
            if (!childInteractionStarted && !_uiState.value.messages.any { it.author == MessageAuthor.Child }) {
                // 个性化 opening 尚未返回，且孩子未开始输入
                if (_uiState.value.agent.statusText == "我在这儿") {
                    trace("opening_local_fallback_status", "statusText" to "想聊什么都可以")
                    _uiState.update { state ->
                        state.copy(
                            agent = state.agent.copy(statusText = "想聊什么都可以"),
                        )
                    }
                }
            }
        }
        viewModelScope.launch(sendDispatcher) {
            runCatching {
                conversationSender.requestOpening(
                    childId = childId,
                    sessionId = sessionId,
                    timezone = DevSettings.TIMEZONE,
                )
            }.onSuccess { response ->
                openingFallbackJob.cancel()
                Log.d(TAG, "[LatencyTrace] stage=opening_model_done")
                trace(
                    "opening_response_received",
                    "replyText" to response.reply.text,
                    "activeScene" to response.sessionState.activeScene,
                )
                // 只有孩子尚未输入、仍处于 opening 状态时才展示个性化 opening
                if (childInteractionStarted || _uiState.value.messages.any { it.author == MessageAuthor.Child }) {
                    Log.d(TAG, "[LatencyTrace] stage=opening_discarded reason=child_already_interacted")
                    trace("opening_discarded", "reason" to "child_already_interacted")
                    return@onSuccess
                }
                renderAgentReply(
                    response = response,
                    replaceMessageId = "agent-welcome",
                )
                val lightMemoryShown = appendOpeningLightMemoryMessageIfAvailable()
                if (!lightMemoryShown) {
                    maybeShowLanguageGameEntryPromptAfterOpening()
                }
            }.onFailure {
                openingFallbackJob.cancel()
                Log.d(TAG, "[LatencyTrace] stage=opening_failed")
                trace("opening_failed", "error" to it::class.simpleName, "message" to it.message)
                // opening 失败：进入普通 ready 状态，不显示错误
                _uiState.update { state ->
                    state.copy(
                        agent = baseAgentState,
                        childTurnPhaseHint = null,
                        isSending = false,
                    )
                }
            }
        }
    }

    private fun appendOpeningLightMemoryMessageIfAvailable(): Boolean {
        val uiModel = LightMemoryCopyMapper.toOpeningUiModel(_uiState.value.lightMemory)
            ?: return false
        val message = ChatMessage(
            id = nextMessageId("light-memory"),
            author = MessageAuthor.Agent,
            text = uiModel.text,
        )
        var appended = false
        _uiState.update { state ->
            if (state.strangeDoorDemo != null || state.languageGame != null) {
                state
            } else {
                appended = true
                trace("opening_light_memory_appended", "text" to message.text)
                state.copy(
                    messages = state.messages + message,
                    agentReplyText = message.text,
                    lightMemory = LightMemoryReducer.markOpeningRecalled(state.lightMemory),
                )
            }
        }
        return appended
    }

    private fun scheduleVoiceRecordingAutoStop() {
        voiceRecordingAutoStopJob?.cancel()
        voiceRecordingAutoStopJob = viewModelScope.launch(sendDispatcher) {
            delay(AndroidWavAudioRecorder.MAX_DURATION_MS)
            if (_uiState.value.voice.isRecording) {
                stopVoiceRecordingAndUpload()
            }
        }
    }

    private fun cancelNaturalWaitingTimeout() {
        naturalWaitingTimeoutJob?.cancel()
        naturalWaitingTimeoutJob = null
    }

    private fun showWaitingForChildAfterTts() {
        if (!naturalWaitingEnabled) return
        if (waitingAttemptedThisTurn) return
        if (_uiState.value.voice.isRecording || _uiState.value.isSending) return
        val activeScene = _uiState.value.sessionState?.activeScene
        if (activeScene in SCENES_NO_WAITING) return
        waitingAttemptedThisTurn = true

        // 只设置视觉状态，不启动录音
        _uiState.update { state ->
            state.copy(
                childTurnPhaseHint = ChildTurnUiPhase.WaitingChild,
                voice = state.voice.copy(
                    inputMode = VoiceInputMode.WaitingForChild,
                    pendingTranscript = "",
                    errorMessage = null,
                ),
                agent = childInteractionPresentation(
                    phaseHint = ChildTurnUiPhase.WaitingChild,
                ).agent,
            )
        }
        scheduleNaturalWaitingTimeout()
    }

    private fun scheduleNaturalWaitingTimeout() {
        naturalWaitingTimeoutJob?.cancel()
        naturalWaitingTimeoutJob = viewModelScope.launch(sendDispatcher) {
            delay(naturalWaitingTimeoutMs)
            if (_uiState.value.voice.inputMode == VoiceInputMode.WaitingForChild) {
                _uiState.update { state ->
                    state.copy(
                        agent = baseAgentState.copy(statusText = "想说再说"),
                    )
                }
                delay(1500)
                cancelVoiceInput()
                Log.d(TAG, "naturalWaitingTimeout: waiting expired, returned to idle")
            }
        }
    }

    private fun scheduleTtsSlowHint() {
        ttsSlowHintJob?.cancel()
        ttsSlowHintJob = viewModelScope.launch(sendDispatcher) {
            delay(3000)
            if (_uiState.value.tts.isSpeakingPending && !_uiState.value.tts.isSpeaking) {
                Log.d(TAG, "[LatencyTrace] stage=tts_slow_hint_3s")
                _uiState.update { state ->
                    state.copy(
                        agent = state.agent.copy(statusText = "声音有点慢，你先看字"),
                    )
                }
            }
        }
    }

    // SLA: T0-5s 若仍无模型文本，显示 "我还在想怎么说"
    private fun scheduleSlowHint5s() {
        slowHint5sJob?.cancel()
        slowHint8sJob?.cancel()
        slowHint5sJob = viewModelScope.launch(sendDispatcher) {
            delay(5000)
            if (_uiState.value.isSending && streamingAgentMessageId == null) {
                Log.d(TAG, "[LatencyTrace] stage=slow_hint_5s")
                _uiState.update { state ->
                    state.copy(
                        agent = state.agent.copy(statusText = "我还在想怎么说"),
                    )
                }
                // SLA: T0-8s 允许显示低压出口
                slowHint8sJob = viewModelScope.launch(sendDispatcher) {
                    delay(3000)
                    if (_uiState.value.isSending && streamingAgentMessageId == null) {
                        Log.d(TAG, "[LatencyTrace] stage=slow_hint_8s")
                        _uiState.update { state ->
                            state.copy(
                                agent = state.agent.copy(statusText = "也可以换个话题，或者等我一下"),
                            )
                        }
                    }
                }
            }
        }
    }

    private fun cancelSlowHints() {
        slowHint5sJob?.cancel()
        slowHint5sJob = null
        slowHint8sJob?.cancel()
        slowHint8sJob = null
    }

    private fun createVoiceUiState(): VoiceUiState {
        return VoiceUiState(
            actions = VoiceInputActions(
                onStartRecording = ::startVoiceRecording,
                onStopRecordingAndUpload = ::stopVoiceRecordingAndUpload,
                onPermissionDenied = ::onVoicePermissionDenied,
                onPendingTranscriptChange = ::updatePendingVoiceTranscript,
                onSendPendingTranscript = ::sendPendingVoiceTranscript,
                onCancelVoiceInput = ::cancelVoiceInput,
            ),
        )
    }
}

private fun StrangeDoorDemoSnapshot.shortTrace(): String {
    return "state=$demoState door=$doorState mechanism=$mechanismType attempts=$attemptsCount " +
        "lastMethod=$lastMethod riddleAttempts=$riddleAttempts lastObject=$lastObjectName " +
        "lastTool=$lastTransformedName canSave=${lastPhotoTransform?.canSaveToShowcase} " +
        "photoMessageId=$lastPhotoMessageId"
}

private fun LanguageGameSnapshot.shortTrace(): String {
    return when (state) {
        LanguageGameState.EntryPrompt,
        LanguageGameState.GameMenu -> "state=$state"
        LanguageGameState.BrainTeaser -> {
            val game = brainTeaser
            "state=$state questionIndex=${game?.questionIndex} gameState=${game?.gameState}"
        }
        LanguageGameState.WordChain -> {
            val game = wordChain
            "state=$state startIndex=${game?.startIndex} previous=${game?.previousWord} " +
                "round=${game?.roundIndex} miss=${game?.missCount} gameState=${game?.gameState} " +
                "childWord=${game?.childWord} foxWord=${game?.foxWord}"
        }
        LanguageGameState.Riddle -> {
            val game = riddle
            "state=$state questionIndex=${game?.questionIndex} gameState=${game?.gameState}"
        }
    }
}

private fun String.normalizedForStrangeDoorRiddleTrace(): String {
    return replace(Regex("[\\s，。！？、,.!?]+"), "")
        .trim()
}

data class ChatUiState(
    val messages: List<ChatMessage> = emptyList(),
    val agentReplyText: String = "",
    val quickActions: List<QuickActionUi> = emptyList(),
    val sessionState: ConversationSessionState? = null,
    val agent: FoxAgentUiState = FoxAgentUiState(),
    val voice: VoiceUiState = VoiceUiState(),
    val tts: TtsUiState = TtsUiState(),
    val isSending: Boolean = false,
    val childTurnPhaseHint: ChildTurnUiPhase? = null,
    val pendingImageContext: PendingImageContextUiState? = null,
    val imagePreviewCards: Map<String, LocalImagePreviewCardUiState> = emptyMap(),
    val xiaozhantaiSavePromptMessageId: String? = null,
    val xiaozhantaiSaveDraft: XiaozhantaiSaveDraftUiState? = null,
    val xiaozhantaiSavedItemIdForNavigation: String? = null,
    val strangeDoorDemo: StrangeDoorDemoSnapshot? = null,
    val languageGame: LanguageGameSnapshot? = null,
    val lightMemory: LightMemorySnapshot = LightMemorySnapshot(),
) {
    val interactionPresentation: ChildInteractionPresentation
        get() = childInteractionPresentation(
            voice = voice,
            tts = tts,
            isSending = isSending,
            phaseHint = childTurnPhaseHint,
            fallbackAgent = agent,
        )

    val xiaozhantaiSavePromptPreview: LocalImagePreviewCardUiState?
        get() = xiaozhantaiSavePromptMessageId
            ?.let(imagePreviewCards::get)
            ?.takeIf {
                it.status == LocalImagePreviewStatus.Sent &&
                    it.canSaveToXiaozhantai &&
                    !it.savedToXiaozhantai &&
                    !it.isSavingToXiaozhantai
            }
}

data class XiaozhantaiSaveDraftUiState(
    val messageId: String,
    val name: String,
    val defaultName: String,
    val previewBytes: ByteArray?,
    val isSaving: Boolean,
    val errorMessage: String?,
    val stage: XiaozhantaiSaveDraftStage = XiaozhantaiSaveDraftStage.Naming,
    val source: XiaozhantaiSaveDraftSource = XiaozhantaiSaveDraftSource.StandardPhoto,
)

enum class XiaozhantaiSaveDraftStage {
    Confirm,
    Naming,
}

enum class XiaozhantaiSaveDraftSource {
    StandardPhoto,
    StrangeDoor,
}

data class QuickActionUi(
    val id: String,
    val label: String,
)

data class PendingImageContextUiState(
    val attachmentId: String,
    val summary: String,
    val imagePurpose: String?,
    val recognizedType: String,
)

private fun ConversationSessionState.mergeWith(
    previous: ConversationSessionState?,
): ConversationSessionState {
    return copy(
        companionObject = companionObject ?: previous?.companionObject,
    )
}

enum class LocalImagePreviewStatus {
    Uploading,
    Sent,
    Failed,
}

data class LocalImagePreviewCardUiState(
    val messageId: String,
    val mimeType: String,
    val sizeBytes: Int,
    val previewBytes: ByteArray?,
    val status: LocalImagePreviewStatus = LocalImagePreviewStatus.Uploading,
    val canSaveToXiaozhantai: Boolean = false,
    val isSavingToXiaozhantai: Boolean = false,
    val savedToXiaozhantai: Boolean = false,
    val defaultShowcaseName: String? = null,
    val xiaozhantaiError: String? = null,
) {
    val displayMimeType: String
        get() = when (mimeType.lowercase()) {
            "image/jpeg" -> "JPEG"
            "image/png" -> "PNG"
            "image/webp" -> "WebP"
            else -> "图片"
        }

    val displaySize: String
        get() = if (sizeBytes >= 1024 * 1024) {
            "${sizeBytes / (1024 * 1024)} MB"
        } else {
            "${(sizeBytes / 1024).coerceAtLeast(1)} KB"
        }

    companion object {
        fun fromPayload(
            messageId: String,
            payload: PhotoUploadPayload,
        ): LocalImagePreviewCardUiState {
            return LocalImagePreviewCardUiState(
                messageId = messageId,
                mimeType = payload.mimeType,
                sizeBytes = payload.bytes.size,
                previewBytes = payload.previewBytes,
            )
        }
    }
}

private data class XiaozhantaiSaveCandidate(
    val payload: PhotoUploadPayload,
    val defaultName: String,
    val foxQuote: String,
    val confirmedName: String? = null,
) {
    val saveName: String
        get() = confirmedName?.takeIf { it.isNotBlank() } ?: defaultName
}

const val IMAGE_PURPOSE_SHARE = "share"
const val IMAGE_PURPOSE_HOMEWORK = "learning_homework"

private fun normalizedQuickActionId(actionId: String): String {
    return when (actionId) {
        "give_name", "image_naming" -> "companion_name"
        else -> actionId
    }
}

private fun List<ConversationUiAction>.toQuickActionUi(): List<QuickActionUi> {
    return flatMap { action ->
        action.actions.map { quickAction ->
            QuickActionUi(
                id = quickAction.id,
                label = quickAction.label,
            )
        }
    }
}

private fun JSONObject.toStreamQuickActionUi(): List<QuickActionUi> {
    return optJSONArray("quick_actions").toQuickActionUiList()
}

private fun JSONArray?.toQuickActionUiList(): List<QuickActionUi> {
    if (this == null) return emptyList()
    return buildList {
        for (index in 0 until length()) {
            val item = optJSONObject(index) ?: continue
            val id = item.optString("id").takeIf { it.isNotBlank() } ?: continue
            val label = item.optString("label").takeIf { it.isNotBlank() } ?: continue
            add(QuickActionUi(id = id, label = label))
        }
    }
}

private fun AttachmentCreateResponse.toPendingImageContext(): PendingImageContextUiState? {
    if (recognizedContent.imagePurpose == IMAGE_PURPOSE_HOMEWORK) {
        return null
    }
    val summary = recognizedContent.text
        ?: recognizedContent.childCaption
        ?: return null
    return PendingImageContextUiState(
        attachmentId = attachmentId,
        summary = summary,
        imagePurpose = recognizedContent.imagePurpose,
        recognizedType = recognizedContent.type,
    )
}

private fun RecognizedContent.toStrangeDoorPhotoRecognition(): StrangeDoorPhotoRecognition {
    return StrangeDoorPhotoRecognition(
        recognizedType = type,
        recognizedText = text,
        confidence = confidence,
    )
}

private fun String?.toXiaobaohuTtsEmotion(): String {
    return when (this) {
        "encourage", "comfort", "hint", "explain", "happy", "calm", "safety", "privacy" -> this
        else -> "encourage"
    }
}

interface ConversationMessageSender {
    suspend fun requestOpening(
        childId: String,
        sessionId: String,
        timezone: String = DevSettings.TIMEZONE,
    ): ConversationMessageResponse {
        throw UnsupportedOperationException("Opening greeting is not implemented")
    }

    suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String> = emptyList(),
        quickActionId: String? = null,
        timezone: String = DevSettings.TIMEZONE,
    ): ConversationMessageResponse

    suspend fun streamTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String> = emptyList(),
        quickActionId: String? = null,
        timezone: String = DevSettings.TIMEZONE,
        includeTts: Boolean = true,
        onEvent: (ConversationStreamEvent) -> Unit,
    )
}

class ConversationRepositoryMessageSender(
    private val repository: ConversationRepository = ConversationRepository(),
) : ConversationMessageSender {
    override suspend fun requestOpening(
        childId: String,
        sessionId: String,
        timezone: String,
    ): ConversationMessageResponse {
        return repository.requestOpening(
            childId = childId,
            sessionId = sessionId,
            timezone = timezone,
        )
    }

    override suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        quickActionId: String?,
        timezone: String,
    ): ConversationMessageResponse {
        return repository.sendTextMessage(
            childId = childId,
            sessionId = sessionId,
            text = text,
            attachments = attachments,
            quickActionId = quickActionId,
            timezone = timezone,
        )
    }

    override suspend fun streamTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        quickActionId: String?,
        timezone: String,
        includeTts: Boolean,
        onEvent: (ConversationStreamEvent) -> Unit,
    ) {
        repository.streamTextMessage(
            childId = childId,
            sessionId = sessionId,
            text = text,
            attachments = attachments,
            quickActionId = quickActionId,
            timezone = timezone,
            includeTts = includeTts,
            onEvent = onEvent,
        )
    }
}
