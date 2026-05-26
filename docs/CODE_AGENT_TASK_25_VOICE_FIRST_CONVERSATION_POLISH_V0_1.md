# CODE_AGENT_TASK_25_VOICE_FIRST_CONVERSATION_POLISH_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: product polish / Android voice-first UX thin slice  
Goal: improve the child-facing voice-first conversation loop without waiting for nightly APK/device QA, and without changing ASR/TTS provider architecture.

---

## 0. Why this task

Task 24 / family-beta APK testing will happen when device testing conditions are available. Do not block product progress while waiting for night-time testing.

After Tasks 21-23, the visible experience has improved in:

```text
1. opening greeting;
2. parent report readability;
3. Xiaobaihu visual state stability;
4. show-and-tell image response quality.
```

The next highest-value product line is the core child loop:

```text
Child taps voice -> speaks -> app listens -> ASR recognizes -> transcript auto-sends -> Xiaobaihu thinks/speaks -> child can stop/retry/cancel/mute naturally.
```

This task should make that loop feel less like a dev demo and more like a child-friendly voice companion.

---

## 1. Product principles

Voice-first should feel like:

```text
1. clear: child always knows whether Xiaobaihu is listening, thinking, or speaking;
2. forgiving: child can retry, cancel, or stop without feeling they failed;
3. low-pressure: no adult-like error messages or technical wording;
4. safe: no always-on microphone, no wake word, no continuous listening;
5. controllable: stop speaking / mute / retry remain discoverable;
6. non-blocking: text stays visible even if audio fails.
```

It must not become:

```text
1. hands-free always-listening mode;
2. a hidden audio recorder;
3. a speech scoring system;
4. a gamified streak/mission loop;
5. a broad ASR/TTS provider refactor;
6. an excuse to change backend data policy or raw audio storage.
```

---

## 2. Required reading

```text
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/LOCAL_ASR_SENSEVOICE_DESIGN_V0_1.md
docs/MIMO_ASR_INTEGRATION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
docs/MASTER_COLLABORATION_AND_FORWARD_MOTION_RULES_V0_1.md
docs/CODE_AGENT_PROJECT_CONTEXT_AND_WORKFLOW_V0_1.md
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuVisualStateResolver.kt
android/app/src/main/java/com/childai/companion/voice/BackendSpeechInputController.kt
android/app/src/main/java/com/childai/companion/voice/AndroidWavAudioRecorder.kt
android/app/src/main/java/com/childai/companion/voice/RemoteAudioTtsController.kt
```

Current facts to preserve:

```text
1. Android voice input v1 already records short audio and uploads to backend `/api/v1/asr/transcribe`.
2. ASR success auto-sends transcript by default; confirm-before-send is only DevSettings / parent debug mode.
3. Hands-free conversational mode is future, not this task.
4. TTS uses backend audio_url / remote audio; child-facing auto-read must not silently fall back to Android system TTS.
5. Original audio is not long-term stored or written to memory.
6. Xiaobaihu visual phases already include listening, recognizing, sending, thinking, speaking pending, speaking, needs retry, permission needed, service error.
```

---

## 3. Scope

Allowed files:

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/*Voice*.kt
android/app/src/main/java/com/childai/companion/voice/*.kt
android/app/src/test/java/com/childai/companion/ui/chat/*Voice*.kt
android/app/src/test/java/com/childai/companion/ui/chat/*ChatViewModel*.kt
android/app/src/test/java/com/childai/companion/voice/*.kt
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

Backend changes are not the goal. Only touch backend if an existing test fixture cannot represent the Android voice state. Do not modify ASR/TTS provider logic.

Forbidden:

```text
1. no always-on microphone;
2. no wake word;
3. no streaming ASR;
4. no ASR/TTS provider replacement;
5. no new raw audio persistence or logs;
6. no backend data-policy changes;
7. no prompt/persona rewrite;
8. no mascot asset changes;
9. no Android navigation rewrite;
10. no auth/account changes;
11. no gamification, score, streak, mission, reward, badge, or retention hook.
```

---

## 4. Required behavior improvements

### 4.1 Voice button state clarity

The child-facing voice area should clearly distinguish these moments:

```text
Idle: ready to speak.
Listening: Xiaobaihu is listening.
Recognizing: Xiaobaihu is hearing/understanding the voice.
Sending: transcript is being sent automatically.
Thinking: Xiaobaihu is thinking.
SpeakingPending: Xiaobaihu is about to speak.
Speaking: Xiaobaihu is speaking; stop button is available.
NeedsRetry: Xiaobaihu did not catch it; child can retry.
PermissionNeeded: ask an adult for microphone permission.
ServiceError: ask adult to check network/service.
```

Do not add long text blocks. Prefer short labels and existing buttons.

### 4.2 Auto-send transition polish

When ASR returns a non-empty transcript and `VOICE_CONFIRM_BEFORE_SEND=false`:

```text
1. do not leave the child in a confusing recognizing/uploading state;
2. briefly move through Sending / Thinking as appropriate;
3. clear pending transcript and voice error;
4. stop any current TTS before recording starts;
5. do not require the child to press send;
6. do not show a text edit panel in child mode.
```

### 4.3 Retry/cancel copy polish

`NeedsRetry`, `Failed`, permission, and policy-blocked copy should be warm and non-blaming.

Preferred wording style:

```text
“这次没听清，我们可以再说一次。”
“你可以再说一遍，或者先停一下。”
“麦克风需要大人帮忙打开。”
“小白狐这次没有接稳，请大人检查一下网络。”
```

Avoid:

```text
识别失败、上传失败、ASR、transcript、policy blocked、error、timeout、provider、服务异常。
```

Technical details may stay in diagnostics/logs, not child-facing copy.

### 4.4 Stop/mute behavior polish

When child starts speaking:

```text
1. current Xiaobaihu TTS should stop;
2. agent should return to listening state;
3. queued audio should clear;
4. UI should not show speaking and listening at the same time.
```

When child taps stop during speaking:

```text
1. audio stops;
2. text remains visible;
3. Xiaobaihu returns to calm/ready state;
4. no error message should appear just because child stopped playback.
```

When muted:

```text
1. future auto-read should not start;
2. text still appears;
3. mute label should not sound punitive or scary.
```

### 4.5 Opening and child interruption

Preserve existing rule:

```text
If the child starts interacting before opening returns, Android discards the late opening.
```

Make sure voice recording counts as child interaction and prevents late opening from replacing the active child flow.

### 4.6 No fake device QA claims

This task may pass code review and unit tests without device QA. Redmi K60 / Honor Pad 5 items remain `NOT_RUN` until the product owner actually tests.

---

## 5. Tests required

Add or strengthen JVM tests. Suggested test areas:

```text
1. starting voice recording stops current TTS and enters Listening.
2. successful transcript auto-sends when confirm-before-send is false.
3. empty transcript / NeedsRetry does not auto-send and shows warm retry state.
4. cancel during recording returns to Idle and cancels recorder.
5. permission denied enters PermissionNeeded without technical copy.
6. TTS stop clears speaking/speakingPending without deleting text.
7. mute prevents future auto-read but does not hide text.
8. late opening is ignored after child voice interaction has started.
9. child-facing error strings do not contain ASR/transcript/provider/policy/timeout/error.
```

If existing test harness makes full ViewModel tests difficult, add focused tests for pure helpers/state transitions and document what remains manual/device QA.

---

## 6. Test commands

Run:

```bash
cd android && ./gradlew test
```

If targeted tests are added, also run and report exact command, for example:

```bash
cd android && ./gradlew test --tests '*Voice*'
cd android && ./gradlew test --tests '*ChatViewModel*'
```

Do not claim APK/device QA passed unless a real device was used.

---

## 7. Final report required

Report:

```text
1. commit sha;
2. files changed;
3. voice-first behavior changes;
4. child-facing copy before/after for retry, permission, service error, stop/mute if changed;
5. how auto-send remains child-default and debug confirm remains dev/parent-only;
6. how stop/mute/recording interaction is handled;
7. tests run and exact results;
8. confirmation no forbidden areas were touched;
9. Redmi K60 / Honor Pad 5 voice QA items marked NOT_RUN unless actually tested.
```

---

## 8. Review guidance for master session

When reviewing Task 25:

```text
1. compare from this task-doc commit to main;
2. check file scope first;
3. inspect ChatViewModel voice transition changes;
4. inspect ChildChatScreen voice labels/buttons if changed;
5. inspect voice controller changes if any;
6. inspect tests for auto-send/retry/cancel/stop/mute/opening-interruption;
7. reject if the patch changes ASR/TTS provider architecture, adds always-on mic, logs raw audio, or introduces gamification.
```
