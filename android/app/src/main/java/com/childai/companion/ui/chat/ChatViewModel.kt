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
import com.childai.companion.ui.chat.languagegame.LanguageGameReducer
import com.childai.companion.ui.chat.languagegame.LanguageGameSnapshot
import com.childai.companion.ui.chat.languagegame.LanguageGameState
import com.childai.companion.ui.chat.languagegame.WordChainGameState
import com.childai.companion.ui.chat.languagegame.toLanguageGameEntryUiModel
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
                voice = createVoiceUiState(),
                tts = initialTtsUiState,
            )
        },
    )
    val uiState: StateFlow<ChatUiState> = _uiState
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
        if (requestOpeningOnInit) {
            requestOpeningGreeting()
        }
    }

    fun activateStrangeDoorDemo() {
        if (_uiState.value.strangeDoorDemo != null) return
        if (strangeDoorDemoDismissed) return
        openingDeferredByStrangeDoor = !openingRequested
        cancelNaturalWaitingTimeout()
        stopCurrentTts(restoreBaseAgent = true)
        _uiState.update { state ->
            state.copy(
                strangeDoorDemo = StrangeDoorDoorStateReducer.reset(),
                languageGame = null,
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
        speakStrangeDoorSnapshot(nextSnapshot, force = true)
    }

    fun chooseStrangeDoorPhotoMethod() {
        updateStrangeDoorDemoState(
            demoState = StrangeDoorDemoState.PhotoPrompt,
            method = StrangeDoorDemoMethod.Photo,
        )
    }

    fun chooseStrangeDoorRiddleMethod() {
        updateStrangeDoorDemoState(
            demoState = StrangeDoorDemoState.RiddlePrompt,
            method = StrangeDoorDemoMethod.Riddle,
        )
    }

    fun retryStrangeDoorRiddle() {
        updateStrangeDoorDemoState(
            demoState = StrangeDoorDemoState.RiddlePrompt,
            method = StrangeDoorDemoMethod.Riddle,
        )
    }

    fun returnToStrangeDoorMethodChoice() {
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
        speakStrangeDoorSnapshot(nextSnapshot)
    }

    fun requestStrangeDoorShowcaseSaveIntent() {
        val snapshot = _uiState.value.strangeDoorDemo ?: return
        val transform = snapshot.lastPhotoTransform ?: return
        val messageId = snapshot.lastPhotoMessageId ?: return
        if (!transform.canSaveToShowcase || snapshot.showcaseSaveIntentRequested) return
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
        if (transcript.isBlank()) return false
        val snapshot = _uiState.value.strangeDoorDemo ?: return false
        if (snapshot.demoState != StrangeDoorDemoState.RiddlePrompt) return false
        val evaluation = StrangeDoorRiddleEvaluator.evaluate(transcript)
        val nextSnapshot = StrangeDoorDoorStateReducer.applyRiddleResult(
            snapshot = snapshot,
            evaluation = evaluation,
        )
        childInteractionStarted = true
        cancelNaturalWaitingTimeout()
        stopCurrentTts(restoreBaseAgent = true)
        _uiState.update { state ->
            state.copy(
                strangeDoorDemo = nextSnapshot,
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
        _uiState.update { state ->
            state.copy(
                strangeDoorDemo = null,
                xiaozhantaiSaveDraft = null,
            )
        }
        lastStrangeDoorNarrationText = null
        if (openingDeferredByStrangeDoor || !openingRequested) {
            openingDeferredByStrangeDoor = false
            requestOpeningGreeting()
        }
    }

    fun dismissLanguageGameEntry() {
        languageGameDismissedForLifecycle = true
        lastLanguageGameNarrationText = null
        _uiState.update { state ->
            state.copy(languageGame = null)
        }
    }

    fun openLanguageGameMenu() {
        showLanguageGameSnapshot(
            LanguageGameReducer.gameMenu(),
            forceSpeak = true,
        )
    }

    fun startBrainTeaserGame() {
        showLanguageGameSnapshot(
            LanguageGameReducer.startBrainTeaser(),
            forceSpeak = true,
        )
    }

    fun startWordChainGame() {
        showLanguageGameSnapshot(
            LanguageGameReducer.startWordChain(),
            forceSpeak = true,
        )
    }

    fun requestBrainTeaserHint() {
        val snapshot = _uiState.value.languageGame ?: return
        showLanguageGameSnapshot(
            LanguageGameReducer.showBrainTeaserHint(snapshot),
            forceSpeak = true,
        )
    }

    fun revealBrainTeaserAnswer() {
        val snapshot = _uiState.value.languageGame ?: return
        showLanguageGameSnapshot(
            LanguageGameReducer.revealBrainTeaserAnswer(snapshot),
            forceSpeak = true,
        )
    }

    fun nextBrainTeaserQuestion() {
        val snapshot = _uiState.value.languageGame ?: return
        showLanguageGameSnapshot(
            LanguageGameReducer.nextBrainTeaserQuestion(snapshot),
            forceSpeak = true,
        )
    }

    fun restartWordChainGame() {
        val snapshot = _uiState.value.languageGame ?: return
        showLanguageGameSnapshot(
            LanguageGameReducer.restartWordChain(snapshot),
            forceSpeak = true,
        )
    }

    fun returnToLanguageGameMenu() {
        showLanguageGameSnapshot(
            LanguageGameReducer.gameMenu(),
            forceSpeak = true,
        )
    }

    fun exitLanguageGame() {
        languageGameDismissedForLifecycle = true
        lastLanguageGameNarrationText = null
        _uiState.update { state ->
            state.copy(
                languageGame = null,
                childTurnPhaseHint = null,
                isSending = false,
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
        if (trimmedText.isEmpty() || _uiState.value.isSending) return
        if (submitStrangeDoorShowcaseName(trimmedText)) return
        if (answerStrangeDoorRiddle(trimmedText)) return
        if (handleLanguageGameText(trimmedText)) return

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
        if (state.isSending || state.voice.isUploading || state.voice.isRecording) return

        val wasSpeaking = state.tts.isSpeaking || state.tts.isSpeakingPending
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
                activeSpeechInputController(cacheDirectory).startRecording()
                scheduleVoiceRecordingAutoStop()
            }.onFailure {
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
        if (!_uiState.value.voice.isRecording) return

        voiceRecordingAutoStopJob?.cancel()
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
                SpeechInputResult.Failed("刚才没听清。请家长帮忙看一下麦克风")
            }
            Log.d(TAG, "[LatencyTrace] stage=asr_done result=${result::class.simpleName}")
            applySpeechInputResult(result)
        }
    }

    fun onVoicePermissionDenied() {
        childInteractionStarted = true
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
            _uiState.update {
                it.copy(
                    voice = it.voice.copy(
                        errorMessage = "先写一句话，再发给小白狐",
                    ),
                )
            }
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
        if (_uiState.value.isSending) return

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
                renderAgentReply(
                    response = response,
                    replaceMessageId = streamingAgentMessageId,
                )
            }.onFailure { error ->
                Log.e(TAG, "sendTextWithAttachments: failed", error)
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
        if (_uiState.value.isSending || payload.bytes.isEmpty()) return
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
        registerStrangeDoorShowcaseCandidate(
            photoMessageId = photoMessageId,
            payload = payload,
            transform = transform,
            doorState = nextSnapshot.doorState,
        )
        _uiState.update { state ->
            state.copy(
                strangeDoorDemo = nextSnapshot,
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
        if (!transform.canSaveToShowcase || xiaozhantaiRepository == null) return
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
                if (!voiceConfirmBeforeSend) {
                    val transcript = result.text.trim()
                    if (transcript.isNotEmpty()) {
                        if (submitStrangeDoorShowcaseName(transcript)) return
                        if (answerStrangeDoorRiddle(transcript)) return
                        if (handleLanguageGameText(transcript)) return
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
                }
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
        appendMessage(
            ChatMessage(
                id = nextMessageId("agent"),
                author = MessageAuthor.Agent,
                text = text,
            ),
        )
    }

    private fun appendMessage(message: ChatMessage) {
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
            return
        }
        viewModelScope.launch(sendDispatcher) {
            val audioUrl = generateFeedbackAudioUrlWithRetry(trimmedText)
            if (audioUrl.isNullOrBlank()) {
                Log.w(TAG, "speakAgentFeedback: audioUrl missing after retry")
                return@launch
            }
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
        if (!force && lastStrangeDoorNarrationText == text) return
        lastStrangeDoorNarrationText = text
        speakAgentFeedback(text)
    }

    private fun maybeShowLanguageGameEntryPromptAfterOpening() {
        if (languageGameAutoPromptShown || languageGameDismissedForLifecycle) return
        if (_uiState.value.strangeDoorDemo != null) return
        if (_uiState.value.languageGame != null) return
        if (_uiState.value.messages.any { it.author == MessageAuthor.Child }) return
        languageGameAutoPromptShown = true
        _uiState.update { state ->
            state.copy(
                languageGame = LanguageGameReducer.entryPrompt(autoPromptShown = true),
                quickActions = emptyList(),
            )
        }
    }

    private fun handleLanguageGameText(text: String): Boolean {
        val trimmed = text.trim()
        if (trimmed.isBlank()) return false
        if (_uiState.value.strangeDoorDemo != null) return false
        val snapshot = _uiState.value.languageGame
        if (snapshot?.state == LanguageGameState.BrainTeaser) {
            val brainTeaser = snapshot.brainTeaser
            if (brainTeaser?.gameState == BrainTeaserGameState.Question ||
                brainTeaser?.gameState == BrainTeaserGameState.Hint
            ) {
                showLanguageGameSnapshot(
                    LanguageGameReducer.applyBrainTeaserAnswer(
                        snapshot = snapshot,
                        transcript = trimmed,
                    ),
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
                showLanguageGameSnapshot(
                    LanguageGameReducer.applyWordChainAnswer(
                        snapshot = snapshot,
                        transcript = trimmed,
                    ),
                    forceSpeak = true,
                )
            }
            return true
        }
        if (handleLanguageGameCommand(trimmed)) return true
        return false
    }

    private fun handleLanguageGameCommand(text: String): Boolean {
        return when {
            text.contains("脑筋急转弯") -> {
                startBrainTeaserGame()
                true
            }
            text.contains("词语接龙") ||
                text.contains("接龙") -> {
                startWordChainGame()
                true
            }
            text.contains("猜谜语") ||
                text.contains("谜语") -> {
                openLanguageGameMenu()
                true
            }
            text.contains("玩游戏") -> {
                openLanguageGameMenu()
                true
            }
            text.contains("随便聊聊") ||
                text.contains("先聊别的") -> {
                exitLanguageGame()
                true
            }
            text.contains("换个游戏") -> {
                returnToLanguageGameMenu()
                true
            }
            text.contains("下一题") -> {
                if (_uiState.value.languageGame?.state != LanguageGameState.BrainTeaser) return false
                nextBrainTeaserQuestion()
                true
            }
            text.contains("再玩一次") &&
                _uiState.value.languageGame?.state == LanguageGameState.WordChain -> {
                restartWordChainGame()
                true
            }
            text.contains("告诉我答案") -> {
                if (_uiState.value.languageGame?.state != LanguageGameState.BrainTeaser) return false
                revealBrainTeaserAnswer()
                true
            }
            text.contains("给我提示") -> {
                if (_uiState.value.languageGame?.state != LanguageGameState.BrainTeaser) return false
                requestBrainTeaserHint()
                true
            }
            else -> false
        }
    }

    private fun showLanguageGameSnapshot(
        snapshot: LanguageGameSnapshot,
        forceSpeak: Boolean = false,
    ) {
        if (_uiState.value.strangeDoorDemo != null) return
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
        if (!force && lastLanguageGameNarrationText == text) return
        lastLanguageGameNarrationText = text
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
            return
        }

        val token = nextTtsToken()
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
            return
        }
        if (openingRequested) return
        openingRequested = true
        Log.d(TAG, "[LatencyTrace] stage=opening_start")
        // 0-1 秒：立即显示本地确定性状态 "我在这儿"
        _uiState.update { state ->
            state.copy(
                childTurnPhaseHint = null,
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
                // 只有孩子尚未输入、仍处于 opening 状态时才展示个性化 opening
                if (childInteractionStarted || _uiState.value.messages.any { it.author == MessageAuthor.Child }) {
                    Log.d(TAG, "[LatencyTrace] stage=opening_discarded reason=child_already_interacted")
                    return@onSuccess
                }
                renderAgentReply(
                    response = response,
                    replaceMessageId = "agent-welcome",
                )
                maybeShowLanguageGameEntryPromptAfterOpening()
            }.onFailure {
                openingFallbackJob.cancel()
                Log.d(TAG, "[LatencyTrace] stage=opening_failed")
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
