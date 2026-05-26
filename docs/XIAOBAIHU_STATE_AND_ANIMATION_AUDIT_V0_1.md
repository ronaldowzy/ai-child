# XIAOBAIHU_STATE_AND_ANIMATION_AUDIT_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Audit scope: Xiaobaihu state model, animation resources, Android mapping, and business trigger coverage  
Task type: design audit and next-step implementation plan, not runtime code or asset generation  
Date: 2026-05-26

---

## 1. Executive Summary

The current Xiaobaihu implementation has a usable animation foundation, but it should not yet be described as a complete product-level state experience.

Current state:

1. `animation_v1` assets exist for 11 runtime states and are declared in `android/app/src/main/assets/mascot/xiaobaohu/v1/mascot_manifest.json`.
2. Android has a matching `MascotState` enum for all 11 state IDs.
3. Android can render `animation_v1` first, then fall back to static WebP, then Compose Canvas.
4. Core interaction states are genuinely wired into business flow today: `idle`, `listening`, `thinking`, `speaking`, and `network_error`.
5. `safety_concern` is genuinely reachable through the microphone permission-needed path and can also be backend-driven.
6. `privacy_boundary` and `homework_focus` are mapped and test-covered, but are backend-signal dependent from Android's perspective.
7. `calm`, `sleepy`, and `jumping_happy` are resource-ready and mapped, but do not yet have strong product-safe business triggers in the observed Android flow.
8. Redmi K60 / Honor Pad 5 real-device QA is still not complete for per-state coverage, memory, frame smoothness, and state switching.

Primary design conclusion:

Xiaobaihu should be treated as a layered companion state system, not as a one-to-one animation mirror of every backend scene. The next task should focus on a stable v2 visual state contract: base attention state plus low-intensity emotional overlay plus safety/boundary overlay. This prevents Xiaobaihu from becoming a button animation, loading spinner, reward loop, or emotional dependency device.

Recommended immediate next implementation task:

Create Task 17 as a non-asset implementation/design-hardening task:

1. Add explicit state coverage tests for manifest completeness and business triggers.
2. Introduce a layered visual state resolver or equivalent adapter.
3. Add transition throttling / hold rules to prevent rapid switching.
4. Clarify backend `emotion` / `agent_motion` contract.
5. Run Redmi K60 and Honor Pad 5 QA against the matrix in this document.

No new art assets are recommended before this coverage and QA layer is complete.

---

## 2. Audit Method and Evidence Boundary

This audit is based on the current GitHub `main` branch files requested by the task:

```text
docs/CODE_AGENT_TASK_16_XIAOBAIHU_STATE_AND_ANIMATION_DESIGN_AUDIT_V0_1.md
docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md
docs/CHILD_UI_POLISH_DESIGN_V0_1.md
docs/PRODUCT_AND_EXPERIENCE_ROADMAP_AFTER_TASK09_V0_1.md
android/app/src/main/java/com/childai/companion/ui/chat/ChildTurnUiPhase.kt
android/app/src/main/java/com/childai/companion/ui/chat/CartoonAgentView.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/FoxAgentAssetMapper.kt
android/app/src/main/java/com/childai/companion/mascot/MascotState.kt
android/app/src/main/java/com/childai/companion/mascot/MascotController.kt
android/app/src/main/java/com/childai/companion/mascot/AssetManifestLoader.kt
android/app/src/main/java/com/childai/companion/mascot/FrameSequencePlayer.kt
android/app/src/main/java/com/childai/companion/mascot/FrameBitmapCache.kt
android/app/src/main/java/com/childai/companion/mascot/MascotManifest.kt
android/app/src/main/assets/mascot/xiaobaohu/v1/mascot_manifest.json
android/app/src/test/java/com/childai/companion/ui/chat/XiaobaohuStateCoverageTest.kt
```

Important boundary:

`resource exists`, `manifest declared`, `MascotState exists`, `Android mapping exists`, `business trigger exists`, `unit test covered`, and `real-device QA verified` are separate levels. This audit does not treat asset existence as product completion.

---

## 3. 当前小白狐动态资源清单

Runtime package root:

```text
android/app/src/main/assets/mascot/xiaobaohu/v1/
```

Runtime package format:

```text
mascot_manifest.json
state/vX.Y.Z/manifest.json
state/vX.Y.Z/frames_webp/*.webp
```

Current package facts:

| Item | Current value |
|---|---|
| Mascot | `Little White Fox` |
| Runtime package version | `0.1.1-runtime-webp` |
| Runtime format | `webp_frame_sequence_runtime` |
| Default FPS | `12` |
| Default state | `idle` |
| Declared state count | `11` |
| Runtime principle | animation_v1 -> static WebP -> Canvas fallback |

Asset inventory from manifest:

| State ID | Manifest declared | Asset exists in runtime package | Type | Frames | FPS | Size | Notes |
|---|---:|---:|---|---:|---:|---|---|
| `idle` | Yes | Yes | `loop` | 24 | 12 | 512x512 | Primary resting/ready loop. Version `v0.2.0`. |
| `listening` | Yes | Yes | `loop` | 24 | 12 | 512x341 | Voice listening and retry-like attention state. |
| `thinking` | Yes | Yes | `loop` | 24 | 12 | 512x341 | Sending, recognizing, stream thinking, image processing currently collapse here. |
| `speaking` | Yes | Yes | `loop` | 24 | 12 | 512x341 | TTS pending / active speaking path. |
| `homework_focus` | Yes | Yes | `loop` | 24 | 12 | 512x341 | Backend-dependent learning overlay. Not a direct Android phase today. |
| `calm` | Yes | Yes | `loop` | 24 | 12 | 512x341 | Resting/calm overlay exists. Business trigger incomplete. |
| `sleepy` | Yes | Yes | `loop` | 24 | 12 | 512x341 | Should be reserved for bedtime/low-stimulation closing. |
| `privacy_boundary` | Yes | Yes | `oneshot_hold` | 24 | 12 | 512x341 | Backend-dependent privacy boundary overlay. Must stay warm, not scary. |
| `safety_concern` | Yes | Yes | `oneshot_hold` | 24 | 12 | 512x341 | Permission-needed and backend safety paths. Must stay calm and adult-bridging. |
| `network_error` | Yes | Yes | `oneshot_hold` | 24 | 12 | 512x341 | Local failures and stream/upload/network errors. |
| `jumping_happy` | Yes | Yes | `short_loop` | 24 | 12 | 512x512 | Resource exists, but should not be used as rewards/check-ins/achievements. |

Manifest priority order:

```text
safety_concern > privacy_boundary > network_error > speaking > thinking > listening > homework_focus > calm > sleepy > jumping_happy > idle
```

Audit note:

The priority order is reasonable for safety and boundary states, but product behavior should still avoid excessive override churn. Safety/boundary visuals should be stable and warm, not alarming.

---

## 4. 当前代码状态映射清单

### 4.1 Render mode and fallback

`DevSettings` currently sets:

```text
FOX_RENDER_MODE = animation_v1
FOX_ANIMATION_ENABLED = true
FOX_ANIMATION_PRELOAD_ENABLED = true
FOX_ANIMATION_LOW_PERFORMANCE_MODE = false
FOX_ASSET_MODE = auto
```

`CartoonAgentView` behavior:

1. Reads `DevSettings.FOX_RENDER_MODE`.
2. Loads `mascot_manifest.json` through `AssetManifestLoader`.
3. Resolves current `FoxAgentUiState` into `MascotState` through `MascotController.stateFor(agent)`.
4. Loads the matching frame sequence if `animation_v1` is enabled and the manifest exists.
5. Falls back to `StaticFoxAgentView` if frame sequence loading fails.
6. Static fallback uses `FoxAgentAssetMapper` and then Canvas fallback if needed.

Current rendering hierarchy:

```text
FoxAgentUiState
  -> MascotController.stateFor(agent)
  -> MascotState
  -> AssetManifestLoader.loadFrameSequenceOrNull(state)
  -> FrameSequencePlayer
  -> StaticFoxAgentView fallback
  -> drawable WebP fallback
  -> Canvas fallback
```

### 4.2 MascotState enum coverage

`MascotState` contains all 11 manifest state IDs:

```text
Idle -> idle
Listening -> listening
Thinking -> thinking
Speaking -> speaking
HomeworkFocus -> homework_focus
Calm -> calm
Sleepy -> sleepy
PrivacyBoundary -> privacy_boundary
SafetyConcern -> safety_concern
NetworkError -> network_error
JumpingHappy -> jumping_happy
```

### 4.3 FoxMood / FoxMotion -> MascotState mapping

Current `MascotState.fromAgent(agent)` mapping:

| MascotState | FoxMood / FoxMotion inputs |
|---|---|
| `SafetyConcern` | `FoxMotion.ConcernedStill` or `FoxMood.SafetyConcern` |
| `PrivacyBoundary` | `FoxMotion.SteadyBoundary` or `FoxMood.PrivacyBoundary` |
| `NetworkError` | `FoxMotion.NetworkError` or `FoxMood.NetworkError` |
| `Speaking` | `FoxMotion.Speaking` |
| `HomeworkFocus` | `FoxMotion.HomeworkFocus` or `FoxMood.HomeworkFocus` |
| `Sleepy` | `FoxMotion.SleepyBlink` or `FoxMood.Sleepy` |
| `Thinking` | `FoxMotion.ThinkingBlink` or `FoxMood.Thinking` |
| `Listening` | `FoxMotion.ListeningTail` or `FoxMood.Listening` |
| `JumpingHappy` | `FoxMotion.CelebrateSmall` or `FoxMood.Encouraging` |
| `Calm` | `FoxMotion.CalmStill` or `FoxMood.Calm` |
| `Idle` | default fallback |

### 4.4 ChildTurnUiPhase -> FoxAgentUiState mapping

Current `ChildTurnUiPhase.agentFor(fallbackAgent)` mapping:

| ChildTurnUiPhase | FoxMood | FoxMotion | MascotState outcome | Notes |
|---|---|---|---|---|
| `Ready` | fallback | fallback | usually `Idle`, but backend fallback can influence | Ready does not force idle; it preserves fallback mood/motion. |
| `Listening` | `Listening` | `ListeningTail` | `Listening` | True voice path. |
| `Recognizing` | `Thinking` | `ThinkingBlink` | `Thinking` | ASR upload / understanding. |
| `Sending` | `Thinking` | `ThinkingBlink` | `Thinking` | Text send. |
| `Thinking` | `Thinking` | `ThinkingBlink` | `Thinking` | Stream/session wait. |
| `SpeakingPending` | fallback mood | `Speaking` | `Speaking` | TTS accepted but not yet started. |
| `Speaking` | fallback mood | `Speaking` | `Speaking` | Audio playback active. |
| `ImageProcessing` | `Thinking` | `ThinkingBlink` | `Thinking` | Currently no separate `looking_at_image` state. |
| `NeedsRetry` | `Listening` | `ListeningTail` | `Listening` | Re-record/retry path. |
| `PermissionNeeded` | `SafetyConcern` | `ConcernedStill` | `SafetyConcern` | Local permission boundary. |
| `Resting` | `Calm` | `CalmStill` | `Calm` | State exists, but product trigger is weak/incomplete. |
| `ServiceError` | `NetworkError` | `NetworkError` | `NetworkError` | Failure path. |

### 4.5 Static fallback asset mapping

`FoxAgentAssetMapper` covers static drawable fallback for the same major state families:

```text
speaking -> fox_3d_speaking
homework_focus -> fox_3d_homework_focus
sleepy -> fox_3d_sleepy
safety_concern -> fox_3d_safety_concern
privacy_boundary -> fox_3d_privacy_boundary
network_error -> fox_3d_network_error
listening -> fox_3d_listening
encouraging / celebrate -> fox_3d_jumping_happy
thinking -> fox_3d_thinking
calm -> fox_3d_calm
fallback -> fox_3d_neutral_idle
```

### 4.6 Animation completion behavior risk

`FrameSequencePlayer` supports:

```text
Loop
OneShotHold
ShortLoop
```

But `CartoonAgentView` currently stores `completedShortState` for any finished animation callback. If the completed state equals the still-requested base state, the requested visual state becomes `Idle`.

Risk:

1. This is appropriate for `jumping_happy` as a short loop.
2. It may be less appropriate for `privacy_boundary`, `safety_concern`, and `network_error`, because their manifest type is `oneshot_hold`, but the view can still switch back to idle after the callback.
3. Product-wise, boundary/error/safety states should usually hold long enough for the child to understand the message, without feeling like a flashing alert.

Recommendation:

In Task 17, split completion handling by animation type:

```text
short_loop -> return to base/idle after completion
oneshot_hold -> hold until business state changes or a safe minimum display time expires
loop -> continue while state remains active
```

---

## 5. 当前业务触发路径清单

| Trigger source | Code path | Phase / signal | Mascot result | Real trigger status |
|---|---|---|---|---|
| App initial/opening | `initialChatMessages()` and `requestOpeningGreeting()` | Warm + GentleIdle / Ready | `idle` | Real path exists. |
| Voice recording start | `startVoiceRecording()` | `ChildTurnUiPhase.Listening` | `listening` | Real path exists. |
| Voice upload / ASR recognize | `stopVoiceRecordingAndUpload()` | `ChildTurnUiPhase.Recognizing` | `thinking` | Real path exists. |
| Voice retry | `SpeechInputResult.NeedsRetry` | `ChildTurnUiPhase.NeedsRetry` | `listening` | Real path exists. |
| Mic permission denied | `onVoicePermissionDenied()` | `ChildTurnUiPhase.PermissionNeeded` | `safety_concern` | Real rare path exists. |
| Text send | `sendTextWithAttachments()` | `ChildTurnUiPhase.Sending` | `thinking` | Real path exists. |
| Stream session started | `applyStreamEvent(session_started)` | `ChildTurnUiPhase.Thinking` | `thinking` | Real path exists when streaming is enabled. |
| Stream route decision | `applyStreamRoute()` | backend `emotion` / `agentMotion` | depends on backend signal | Backend-dependent path exists. |
| Non-stream reply | `renderAgentReply()` | `reply.toFoxAgentUiState()` | depends on backend `emotion` / `agent_motion` | Backend-dependent path exists. |
| TTS accepted/pending | `maybeAutoReadReply()` | `asSpeakingPending()` | `speaking` | Real path exists if auto-read enabled and not muted. |
| TTS playback start | `TtsCallbacks.onStart` / audio queue `onStart` | `asSpeaking()` | `speaking` | Real path exists. |
| Image capture submit | `submitCapturedPhoto()` | `ChildTurnUiPhase.ImageProcessing` | `thinking` | Real path exists, but should become `looking_at_image` in v2. |
| Attachment upload failure | `submitCapturedPhoto().onFailure` | `ChildTurnUiPhase.ServiceError` + NetworkError | `network_error` | Real path exists. |
| Conversation send failure | `sendTextWithAttachments().onFailure` | `ChildTurnUiPhase.ServiceError` + NetworkError | `network_error` | Real path exists. |
| Stream error without partial text | `applyStreamError()` | `ChildTurnUiPhase.ServiceError` + NetworkError | `network_error` | Real path exists. |
| Homework image follow-up | `handleAttachmentResponse()` -> backend conversation | backend-dependent | expected `homework_focus` if backend emits it | Partial path exists; Android local phase is still `thinking`. |
| Resting / calm | `ChildTurnUiPhase.Resting` | CalmStill | `calm` | Phase exists; direct business trigger not observed in current code path. |
| Sleepy / bedtime | backend `sleepy` mood/motion only | backend-dependent | `sleepy` | No strong Android business trigger observed. |
| Jumping happy / encouragement | backend `encouraging` or `CelebrateSmall` only | backend-dependent | `jumping_happy` | No safe current business trigger recommended. |

---

## 6. 状态覆盖矩阵

Format required by task:

`State ID | Asset exists | MascotState exists | FoxMood/FoxMotion | Trigger path | Frequency | Current status | Recommendation`

| State ID | Asset exists | MascotState exists | FoxMood/FoxMotion | Trigger path | Frequency | Current status | Recommendation |
|---|---|---|---|---|---|---|---|
| `idle` | Yes: manifest + runtime WebP | Yes: `MascotState.Idle` | fallback / Warm + GentleIdle | App initial state, opening greeting, default fallback | Very high | `implemented_and_triggered` | Keep as base attention state. Ensure idle feels alive but not attention-grabbing. |
| `listening` | Yes | Yes: `MascotState.Listening` | `FoxMood.Listening` / `FoxMotion.ListeningTail` | Voice recording start; ASR retry | High in voice-first UX | `implemented_and_triggered` | Keep. Avoid making it look like a recording button; it should feel like attentive listening. |
| `thinking` | Yes | Yes: `MascotState.Thinking` | `FoxMood.Thinking` / `FoxMotion.ThinkingBlink` | Text send, ASR upload, stream wait, image processing | High | `implemented_and_triggered` | Keep, but split `looking_at_image` from generic thinking in v2. Do not use animation to hide latency addictively. |
| `speaking` | Yes | Yes: `MascotState.Speaking` | `FoxMotion.Speaking` plus fallback mood | TTS pending and active playback | High when auto-read enabled | `implemented_and_triggered` | Keep. Ensure no flicker between pending, playing, and stream sentence audio. |
| `network_error` | Yes | Yes: `MascotState.NetworkError` | `FoxMood.NetworkError` / `FoxMotion.NetworkError` | Conversation failure, stream error, attachment upload failure, voice failure | Medium/rare, but important | `implemented_and_triggered` | Keep calm and non-blaming. Do not make Xiaobaihu look guilty or ask child to retry repeatedly. |
| `safety_concern` | Yes | Yes: `MascotState.SafetyConcern` | `FoxMood.SafetyConcern` / `FoxMotion.ConcernedStill` | Mic permission needed; backend safety signal | Rare | `implemented_rare_scene` | Keep warm and steady. Use to bridge to trusted adult, not to scare child. |
| `privacy_boundary` | Yes | Yes: `MascotState.PrivacyBoundary` | `FoxMood.PrivacyBoundary` / `FoxMotion.SteadyBoundary` | Backend `reply.emotion` / `reply.agent_motion` route only from Android perspective | Rare | `implemented_rare_scene` | Keep, but add explicit backend contract and tests. Should feel clear but gentle. |
| `homework_focus` | Yes | Yes: `MascotState.HomeworkFocus` | `FoxMood.HomeworkFocus` / `FoxMotion.HomeworkFocus` | Backend learning/homework signal; image homework flow can lead to backend conversation | Medium once learning support matures | `implemented_rare_scene` | Keep as boundary/safety overlay for learning focus. Do not turn into answer-machine mode. |
| `calm` | Yes | Yes: `MascotState.Calm` | `FoxMood.Calm` / `FoxMotion.CalmStill` | `ChildTurnUiPhase.Resting`; backend calm signal possible | Low today | `resource_ready_but_not_triggered` | Keep as v2 emotional overlay. Add explicit low-energy / resting / closeout trigger only after UX copy is stable. |
| `sleepy` | Yes | Yes: `MascotState.Sleepy` | `FoxMood.Sleepy` / `FoxMotion.SleepyBlink` | Backend sleepy signal possible; no direct Android phase | Very low | `resource_ready_but_not_triggered` | Delay product use until bedtime/reflection flow exists. Never use to invite more chatting. |
| `jumping_happy` | Yes | Yes: `MascotState.JumpingHappy` | `FoxMood.Encouraging` / `FoxMotion.CelebrateSmall` | Backend encouraging/celebrate signal possible; short-loop asset exists | Should be very low | `resource_ready_but_not_triggered` | Do not use for check-ins, achievements, streaks, correct answers, or retention. If ever used, limit to rare gentle encouragement with strict cooldown. |

---

## 7. 哪些状态已经真实触发

The following states are genuinely reachable from current Android business paths:

| State | Evidence summary | Notes |
|---|---|---|
| `idle` | Initial/welcome/opening/default fallback path | Primary base state. |
| `listening` | Voice recording start and retry flow | Strong voice-first path. |
| `thinking` | Sending, recognizing, stream waiting, image processing | Overloaded today; should split image attention later. |
| `speaking` | TTS pending and playback callbacks | Strong path if auto-read is enabled and not muted. |
| `network_error` | Conversation, stream, upload, and voice failure flows | Important non-happy failure state. |
| `safety_concern` | Local permission-needed path; backend safety signal can also map here | Real rare path, but visual tone needs careful QA. |

---

## 8. 哪些状态只是 resource_ready_but_not_triggered

These states have assets, manifest declarations, `MascotState` entries, and mapping support, but should not yet be treated as completed product experiences:

| State | Why it is not complete yet | Recommendation |
|---|---|---|
| `calm` | `Resting` phase exists, but a clear product trigger such as low-energy closeout/rest is not observed as a normal flow. | Keep resource. Add v2 closeout/resting rule only after UX copy and engagement boundary are defined. |
| `sleepy` | No direct Android phase. Suitable only for bedtime/reflection/low-stimulation close. | Delay until bedtime flow exists. Do not use to prolong chat. |
| `jumping_happy` | Mapped via `Encouraging` / `CelebrateSmall`, but using it as reward is a product risk. | Keep resource dormant. Do not wire to rewards, check-ins, achievements, correct answers, or streak-like feedback. |

Backend-dependent but not local-phase-triggered states:

| State | Current status | Recommendation |
|---|---|---|
| `privacy_boundary` | Android can display it if backend emits the right mood/motion. No local ChildTurnUiPhase directly maps to it. | Add backend contract tests and QA scenarios. |
| `homework_focus` | Android can display it if backend emits the right mood/motion. Homework image flow currently shows `thinking` locally until backend reply. | Add explicit learning/homework visual contract; avoid answer-machine framing. |

---

## 9. 哪些状态缺业务触发

Strictly missing or insufficient direct product triggers today:

1. `sleepy`: missing a dedicated bedtime/reflection/closeout product flow.
2. `jumping_happy`: intentionally should not be broadly triggered; current safe trigger policy is missing.
3. `calm`: has `Resting` phase but lacks a clear normal business path and UX policy.
4. `privacy_boundary`: lacks local Android phase; depends on backend signal.
5. `homework_focus`: lacks local visual phase; depends on backend signal after attachment/conversation routing.

Not missing, but overloaded:

1. `thinking` currently covers thinking, sending, recognizing, and image processing.
2. `safety_concern` covers both permission-needed and safety concern. These are not the same emotional situation and may need separate copy/tone rules even if they share the same visual asset.

---

## 10. 哪些状态不建议现在使用或应延后

### 10.1 `jumping_happy`

Do not use now as a general product feedback animation.

Do not connect it to:

```text
1. rewards;
2. check-ins;
3. achievements;
4. streaks;
5. correct answers;
6. daily task completion;
7. returning to the app;
8. repeated usage loops.
```

Allowed future use, if any:

```text
rare gentle encouragement
strict cooldown
short loop only
no reward copy
no fireworks / score / badge / streak pairing
```

### 10.2 `sleepy`

Delay until bedtime/reflection or low-stimulation closeout exists.

Do not use it to say or imply:

```text
1. keep chatting with me;
2. I am lonely;
3. I miss you;
4. come back tomorrow for me;
5. you should continue because I am sleepy/cute.
```

### 10.3 `privacy_boundary` and `safety_concern`

Use carefully and warmly. These should never become alarming states.

Tone requirement:

```text
privacy_boundary: clear, calm, protective, not suspicious
safety_concern: concerned, steady, adult-bridging, not frightening
```

### 10.4 Backend scene over-mapping

Do not create a new animation for every backend scene. Scenes such as `daily.after_school_checkin`, `conversation.open`, `learning.homework_help`, `privacy.boundary`, and `safety.guardian` should resolve into a small set of layered visual states.

---

## 11. 小白狐状态模型 v2 设计建议

Recommended v2 model:

```text
VisualStateV2 = BaseAttentionState + EmotionalOverlay + BoundarySafetyOverlay
```

### 11.1 Base attention state

| Base state | Current source | Intended meaning | Recommended visual |
|---|---|---|---|
| `idle` | Ready/opening/default | Xiaobaihu is present and available | Gentle breathing/blink, no urgency. |
| `listening` | Voice recording / retry | Xiaobaihu is paying attention to the child | Forward attention, stable, not a button pulse. |
| `thinking` | Sending / model wait / ASR understanding | Xiaobaihu is processing | Small thinking motion, no addictive waiting animation. |
| `speaking` | TTS pending/playback | Xiaobaihu is speaking | Mouth/gesture loop, stable across audio segments. |
| `looking_at_image` | ImageProcessing | Xiaobaihu is looking at the shared picture | New logical state; can reuse `thinking` asset initially. |
| `resting` | Resting / closeout | Low stimulation pause | Can use `calm` asset once product trigger exists. |

### 11.2 Emotional overlay

| Overlay | Use | Asset/mapping today | Notes |
|---|---|---|---|
| `warm` | Normal companion tone | `idle` / `Warm` | Default. |
| `curious` | Child shares object/story/image | Not explicit today | Could be copy/state only first; no new asset required. |
| `encouraging` | Child expresses effort or reasoning | Currently maps toward `jumping_happy` risk | Should not automatically jump. Consider warm/calm microcopy first. |
| `calm` | Low-energy child, pause, regulation | `calm` | Add trigger later. |
| `concerned` | Safety/privacy/error concern | `safety_concern` / `privacy_boundary` / `network_error` | Must be steady and not scary. |
| `sleepy` | Bedtime closeout only | `sleepy` | Delay. |

### 11.3 Boundary/safety overlay

| Overlay | Use | Priority | Notes |
|---|---|---|---|
| `privacy_boundary` | Personal information, strangers, privacy rule | High | Warm boundary, not alarm. |
| `safety_concern` | High-risk or trusted adult needed | Highest | Adult bridge, no panic. |
| `network_error` | Backend/audio/upload issue | High | Non-blaming. |
| `homework_focus` | Learning help without answer-giving | Medium-high | Focused helper, not answer machine. |

### 11.4 Resolver behavior

Recommended resolver order:

```text
1. If safety_concern active: show safety_concern.
2. Else if privacy_boundary active: show privacy_boundary.
3. Else if network_error active: show network_error.
4. Else if speaking active and no higher-priority overlay: show speaking.
5. Else select base attention state: listening / thinking / looking_at_image / resting / idle.
6. Apply emotional overlay only if it does not create noisy or reward-like behavior.
```

### 11.5 Transition rules

Recommended transition rules:

```text
1. Minimum display duration for base states: about 600-900ms.
2. Minimum display duration for boundary/error/safety: about 1200-1800ms or until copy changes.
3. No more than one non-safety visual switch per child turn unless speaking starts.
4. Speaking may override thinking, but safety/privacy/network may override speaking.
5. Short-loop states return to the previous stable base state.
6. One-shot-hold states hold until business state changes; they should not immediately snap to idle.
7. Repeated backend route_decision events should not cause visual jitter.
```

### 11.6 Product copy alignment

State copy should remain child-readable and non-technical:

```text
idle: 小白狐在这里
listening: 在听你说
thinking: 在想一想
speaking: 在说给你听
looking_at_image: 在看这张图
resting: 先歇一小会儿
privacy_boundary: 这件事要保护好
safety_concern: 这件事请大人一起看看
network_error: 先请大人看看网络
homework_focus: 我们一步一步看题目
```

Avoid exposing:

```text
backend scene IDs
provider names
stream status
model state
risk labels
debug values
```

---

## 12. 下一步实现任务拆分建议

### Task 17 — Xiaobaihu visual state v2 resolver and coverage hardening

Scope: code + tests + QA hooks only. No new assets.

Recommended implementation items:

1. Add a `XiaobaohuVisualStateV2` or equivalent resolver layer.
2. Represent state as:

```text
baseAttention: Idle | Listening | Thinking | Speaking | LookingAtImage | Resting
emotionalOverlay: Warm | Curious | Encouraging | Calm | Concerned | Sleepy | None
boundaryOverlay: PrivacyBoundary | SafetyConcern | NetworkError | HomeworkFocus | None
```

3. Keep the current `MascotState` enum as the runtime asset target.
4. Add resolver tests from v2 layered states to `MascotState`.
5. Add business trigger tests in `ChatViewModel` for:

```text
voice start -> listening
voice uploading -> thinking
send text -> thinking
stream session_started -> thinking
stream route privacy -> privacy_boundary
stream route safety -> safety_concern
stream route homework -> homework_focus
TTS pending/start -> speaking
image submit -> looking_at_image logical state, initially mapped to thinking asset
upload/network failure -> network_error
permission denied -> safety_concern
```

6. Add manifest completeness test:

```text
every MascotState used by resolver exists in mascot_manifest.json
manifest state IDs do not silently collapse unknown states to Idle in tests
statePriority contains all declared states once
```

7. Add animation completion tests or QA-only checks for:

```text
short_loop returns to base
oneshot_hold holds visibly
loop remains active while state remains active
```

8. Add transition throttling / debounce in the visual resolver or view state layer.
9. Keep `SHOW_MASCOT_DEBUG_SWITCHER` gated behind dev settings.
10. Do not touch assets, TTS, ASR, auth, parent report, or backend routing logic except for contract tests/stubs.

### Task 18 — Real-device QA and evidence package

Scope: manual QA + evidence capture + targeted P0/P1/P2 fixes only.

Recommended implementation items:

1. Build APK from main after Task 17.
2. Run Redmi K60 QA scenarios below.
3. Run Honor Pad 5 QA scenarios below.
4. Capture short screen recordings for each state family.
5. Record FPS/perceived jank, memory pressure symptoms, audio sync behavior, and fallback behavior.
6. Fix only evidence-backed issues.

### Task 19 — Optional backend contract cleanup

Scope: backend/frontend visual signal contract.

Recommended implementation items:

1. Define allowed `reply.emotion` values.
2. Define allowed `reply.agent_motion` values.
3. Map backend scenes into v2 visual layers, not one animation per scene.
4. Add server-side or contract tests for privacy, safety, homework, comfort, bedtime, and network-like fallback cases.
5. Make `jumping_happy` opt-in only, with strict product review.

---

## 13. Redmi K60 / Honor Pad 5 真机 QA 场景

### 13.1 Shared QA setup

Before each QA run:

```text
1. Use Android landscape mode.
2. Confirm FOX_RENDER_MODE=animation_v1.
3. Confirm FOX_ANIMATION_ENABLED=true.
4. Confirm SHOW_MASCOT_DEBUG_SWITCHER=false for normal child-facing QA.
5. Confirm auto-read/TTS state: test both enabled and muted.
6. Clear app state only when a scenario explicitly requires first-run/opening behavior.
```

Record for each scenario:

```text
device
OS version
build commit
render mode
state expected
state observed
fallback observed: animation_v1 / static WebP / Canvas
state switch delay
visual flicker: yes/no
layout clipping: yes/no
audio sync issue: yes/no
child-facing copy issue: yes/no
```

### 13.2 Redmi K60 QA

| QA ID | Scenario | Steps | Expected state | Pass criteria |
|---|---|---|---|---|
| `RK60-FOX-001` | Opening idle | Launch child chat fresh. Wait for opening greeting. | `idle`, then possibly `speaking` if TTS starts | Xiaobaihu visible; no debug text; idle does not look like a loading spinner. |
| `RK60-FOX-002` | Voice listening | Tap voice button and start speaking. | `listening` | State changes smoothly; chip says listening; no jumpy reward motion. |
| `RK60-FOX-003` | ASR recognizing | Stop recording and upload. | `thinking` | Recognizing does not flicker with ready/listening. |
| `RK60-FOX-004` | Text/model thinking | Send a text message. | `thinking` | Thinking appears while waiting; no addictive waiting loop or excessive bouncing. |
| `RK60-FOX-005` | TTS speaking | Receive reply with audioUrl or generated audio; auto-read on. | `speaking` | Speaking starts when audio is pending/playing; no rapid toggling between thinking and speaking. |
| `RK60-FOX-006` | Stop speaking | Tap stop while speaking. | previous base or `idle` | Stops without visual residue or crash. |
| `RK60-FOX-007` | Image sharing | Share/capture a picture. | currently `thinking`; v2 should be `looking_at_image` logical state | Image preview and Xiaobaihu area both fit landscape layout. |
| `RK60-FOX-008` | Attachment upload failure | Simulate failed upload/network. | `network_error` | Warm error visual; copy asks adult to check, not child to repeatedly retry. |
| `RK60-FOX-009` | Stream error before text | Simulate stream error before partial response. | `network_error` | Error state holds long enough to be noticed; no scary expression. |
| `RK60-FOX-010` | Permission denied | Deny microphone permission. | `safety_concern` | Child-facing copy says adult help; visual is calm, not panic. |
| `RK60-FOX-011` | Backend privacy signal | Stub/backend returns privacy mood/motion. | `privacy_boundary` | Clear boundary state, no alarm visuals. |
| `RK60-FOX-012` | Backend homework signal | Stub/backend returns homework mood/motion. | `homework_focus` | Focused helper tone, no answer-machine or reward feel. |
| `RK60-FOX-013` | Backend calm signal | Stub/backend returns calm mood/motion. | `calm` | Low-stimulation; does not induce continued use. |
| `RK60-FOX-014` | Backend sleepy signal | Stub/backend returns sleepy mood/motion. | `sleepy` | Only acceptable in bedtime/closeout test copy. Should not invite more chat. |
| `RK60-FOX-015` | Jumping happy gated | Stub/backend returns encouraging/celebrate. | ideally not shown unless explicitly enabled | Confirm it is not wired to generic rewards/check-ins. |

### 13.3 Honor Pad 5 QA

Honor Pad 5 is the low-performance compatibility target. Prioritize layout, memory, and fallback behavior over animation richness.

| QA ID | Scenario | Steps | Expected state | Pass criteria |
|---|---|---|---|---|
| `HP5-FOX-001` | Landscape layout baseline | Launch child chat in landscape. | `idle` | Agent panel, chat panel, input bar all visible; no clipping. |
| `HP5-FOX-002` | Animation smoothness | Cycle idle -> listening -> thinking -> speaking. | multiple | No obvious freeze, crash, or severe jank. |
| `HP5-FOX-003` | Low-performance mode | Enable low-performance mode if available/build supports it. | same logical state | Lower image sample size/fallback still readable. |
| `HP5-FOX-004` | Long voice turn | Record near max voice duration, then upload. | listening -> thinking | No memory spike symptoms; UI remains responsive. |
| `HP5-FOX-005` | Stream + TTS | Receive streaming reply with sentence audio. | thinking -> speaking | Chip and mascot do not flicker rapidly. |
| `HP5-FOX-006` | Image upload | Share picture and continue. | thinking / future looking_at_image | Preview does not squeeze input bar or hide Xiaobaihu. |
| `HP5-FOX-007` | Network failure | Disable backend/network and send. | `network_error` | Fallback and error copy are readable. |
| `HP5-FOX-008` | Manifest fallback | Test missing/invalid manifest build or dev variant if available. | static WebP or Canvas fallback | App does not crash; Xiaobaihu remains visible. |
| `HP5-FOX-009` | Static fallback | Force static mode. | expected mapped static state | Static assets are clear at landscape size. |
| `HP5-FOX-010` | Canvas fallback | Force canvas mode. | canvas fox | Canvas fallback remains acceptable and does not expose debug UI. |
| `HP5-FOX-011` | Safety/privacy visual | Trigger safety and privacy test states. | safety/privacy | Warm, stable, no frightening motion. |
| `HP5-FOX-012` | Sleepy/calm closeout test | QA-only backend signal. | calm/sleepy | Low stimulation; no dependency-inducing copy. |

---

## 14. Acceptance Criteria for the Next Task

Task 17 should be accepted only when:

1. No runtime assets are changed.
2. No TTS / ASR / auth / backend conversation behavior is changed beyond optional stubs/tests.
3. Every current `MascotState` is classified as one of:

```text
implemented_and_triggered
implemented_rare_scene
resource_ready_but_not_triggered
missing_mapping
missing_asset
needs_design
```

4. Unit tests distinguish:

```text
asset exists
manifest declared
MascotState exists
mapping exists
business trigger exists
```

5. QA checklist explicitly marks Redmi K60 and Honor Pad 5 as:

```text
NOT_RUN
PASS
FAIL
BLOCKED
```

6. `jumping_happy` is not wired into rewards/check-ins/streaks/achievements.
7. `sleepy` is not wired into general engagement or reactivation.
8. Safety/privacy visuals remain warm, not alarming.
9. Image-processing has a v2 logical state plan even if it initially reuses `thinking` asset.

---

## 15. Final Audit Conclusion

The current Xiaobaihu system has a solid runtime foundation: 11 animation resources, manifest-driven loading, fallback rendering, enum coverage, and unit-tested state mapping. The product experience is not yet complete because several states are still backend-dependent, resource-ready-only, or missing real QA evidence.

The right next move is not to add more animations. The right next move is to stabilize the state model, prove trigger coverage, prevent rapid switching, and run real-device QA on Redmi K60 and Honor Pad 5.

Recommended next task title:

```text
Task 17 — Xiaobaihu Visual State V2 Resolver, Trigger Coverage Tests, and Device QA Preparation
```

Recommended task type:

```text
implementation + tests + QA plan
no new assets
no runtime mascot engine rewrite
no backend scene explosion
```
