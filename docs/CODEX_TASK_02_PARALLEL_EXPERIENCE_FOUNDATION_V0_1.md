# Codex Task 02: Parallel Experience Foundation v0.1

Project: `ai-child` / `ronaldowzy/ai-child`  
Target branch: `main`  
Task type: coordinated implementation batch  
Recommended mode: two Codex sessions on separate branches/worktrees, then merge in order; if only one Codex session is available, execute Lane A first, then Lane B.

---

## 0. Why this batch

Task 01 has landed the Android `ChildTurnUiPhase` / `ChildInteractionPresentation` thin slice. This is accepted as the foundation, but it intentionally left two closeout items:

```text
1. voice-first mode has visible “停一下”, but mute visibility is still not fully surfaced.
2. starting a new child action should explicitly stop any current/queued TTS before entering Listening/Sending/ImageProcessing, otherwise speaking state can visually dominate the new action.
```

The next product-critical backend issue is reply length and question density. The current child population is 5–10, but ordinary conversation still tends to behave like an 8-year-old baseline and can keep asking one question per turn. This batch therefore has two lanes:

```text
Lane A: Android E1 closeout — TTS control visibility + new-child-action stops old speaking.
Lane B: Backend E2 thin slice — age-banded reply guidance + continuous-question throttle.
```

These lanes are intentionally separated by file ownership so Codex can work efficiently.

---

## 1. Coordination rules

### If using two Codex sessions

Use two branches:

```text
codex/e1-02-android-tts-phase-closeout
codex/e2-01-backend-age-band-question-throttle
```

Merge order:

```text
1. Merge Lane A first.
2. Rebase Lane B on latest main.
3. Merge Lane B second.
```

Avoid both lanes editing the same docs in parallel. Lane A may update Android/voice docs. Lane B may update backend/freedom/healthy docs and progress board. If conflict appears in `docs/CODEX_PROGRESS_BOARD_V0_1.md`, resolve after both implementation branches are done.

### If using one Codex session

Do this sequence:

```text
1. Implement Lane A.
2. Run Android tests.
3. Commit Lane A.
4. Implement Lane B.
5. Run backend tests and any affected Android tests.
6. Commit Lane B or one combined commit if repo policy prefers.
```

Do not mix Lane A and Lane B files casually.

---

## 2. Shared required reading

Before coding, read:

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md
docs/EXPERIENCE_REVIEW_AND_NEXT_OPTIMIZATION_GUIDE_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

Lane A additionally reads:

```text
android/README.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md
```

Lane B additionally reads:

```text
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
backend/app/prompts/global_system_v0_1.txt
backend/app/prompts/output_contracts/child_chat_v0_1.txt
backend/app/prompts/scenes/conversation_open_v0_1.txt
```

---

# Lane A — Android TTS / phase closeout

## A1. Goal

Finish the E1 Android interaction-state closeout without large UI redesign.

The child should be able to:

```text
1. stop Xiaobaihu speaking in voice-first mode,
2. see a low-pressure mute/unmute control when speaking or speaking pending,
3. start a new voice/text/image action without the previous TTS visually dominating the new state,
4. keep existing voice-first auto-send behavior.
```

## A2. Allowed files

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChildTurnUiPhase.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/InputBar.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/test/java/com/childai/companion/ui/chat/*
android/app/src/test/java/com/childai/companion/ui/*
android/README.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
```

## A3. Do not do

```text
1. Do not restore system TTS as automatic child-facing fallback.
2. Do not add new parent UI changes in this lane.
3. Do not do CameraX or image thumbnail work.
4. Do not change backend APIs.
5. Do not remove DevSettings debug paths.
```

## A4. Implementation requirements

### A4.1 Voice-first mute visibility

`ChildInteractionPresentation.showMuteToggle` already exists. Wire it into voice-first `InputBar`.

Minimum acceptable UX:

```text
TTS SpeakingPending/Speaking:
  primary button: 小白狐在说, disabled
  visible buttons: 停一下, 静音

Muted while not speaking:
  keep voice-first simple; do not require a permanent large toggle unless already easy.
```

Button text:

```text
if muted: 打开朗读
else: 静音
```

Do not let mute button crowd out the primary voice button on compact landscape. If needed, show mute only while speaking/pending in this thin slice.

### A4.2 Stop TTS before new child action

Ensure these actions call the existing stop path before entering their new phase:

```text
1. sendText / sendTextWithAttachments
2. startVoiceRecording
3. submitCapturedPhoto
4. submitMockPhotoCapture
5. continuePendingImageConversation / quick action that sends text
```

The goal is: when the child acts, Xiaobaihu stops talking and visually switches to Listening/Sending/ImageProcessing.

Use existing `stopCurrentTts(restoreBaseAgent = true/false)` carefully. Do not accidentally reset child input state.

### A4.3 Phase precedence sanity

Check `childTurnUiPhase(...)` precedence. Speaking can stay high priority for passive playback, but once a child action starts, TTS should already be stopped. Add tests for the action-start behavior rather than overcomplicating precedence.

## A5. Acceptance criteria

```text
1. voice-first mode displays “停一下” and “静音” while TTS is speaking/pending.
2. tapping “静音” stops current speaking and sets muted state.
3. starting voice recording stops current TTS and phase becomes Listening.
4. sending text / quick action stops current TTS and phase becomes Sending/Thinking.
5. uploading/capturing image stops current TTS and phase becomes ImageProcessing.
6. no system TTS fallback is reintroduced.
```

## A6. Tests

Add or update tests for:

```text
1. presentation.showMuteToggle true for Speaking/SpeakingPending.
2. InputBar voice-first exposes mute toggle logic through pure function or testable presentation helper.
3. startVoiceRecording stops TTS and phase becomes Listening.
4. submitCapturedPhoto stops TTS and phase becomes ImageProcessing.
5. sendText/quick action stops TTS before sending.
```

Run:

```bash
cd android
./gradlew test
```

If tests cannot run, document the exact failure and why.

---

# Lane B — Backend age-banded replies and question throttle

## B1. Goal

Make ordinary Xiaobaihu conversation respect the actual target age range and reduce interview-like repeated questioning.

This is a backend/prompt/runtime thin slice. It should not attempt a full memory or analytics system yet.

## B2. Allowed files

```text
backend/app/prompts/global_system_v0_1.txt
backend/app/prompts/output_contracts/child_chat_v0_1.txt
backend/app/prompts/scenes/conversation_open_v0_1.txt
backend/app/prompts/scenes/*
backend/app/services/prompt_manager.py
backend/app/services/child_agent_runtime.py
backend/app/services/conversation_service.py
backend/app/domain/schemas/parent_policy.py
backend/tests/**/*
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

If a tiny shared age-band utility is cleaner, add it under:

```text
backend/app/services/age_band_policy.py
```

## B3. Do not do

```text
1. Do not replace freedom-first with fixed menus.
2. Do not add a new database table for this thin slice.
3. Do not store full child text in new logs.
4. Do not weaken safety, privacy, learning, or bedtime guardrails.
5. Do not make model output longer for “older kids” than needed for TTS.
6. Do not use gamification, rewards, streaks, FOMO, or dependency language.
```

## B4. Implementation requirements

### B4.1 Replace hard-coded 8-year-old baseline

`global_system_v0_1.txt` currently frames Xiaobaihu as serving an 8-year-old child. Revise it to the project target:

```text
5–10 岁儿童，默认以 7–8 岁低压力语气处理；若 runtime child profile provides age_band, follow it.
```

Do not erase child-safety principles.

### B4.2 Add age-band policy

Derive age band from parent policy communication preferences:

```text
explicit age_band in {age_5_6, age_7_8, age_9_10, unknown}
else numeric child_age/age
else age_7_8
```

Recommended reply budgets for ordinary conversation:

```text
age_5_6: 30–80 Chinese chars, usually 1–2 short sentences, question optional.
age_7_8: 60–140 Chinese chars, at most one small question.
age_9_10: 90–220 Chinese chars, may lightly compare/plan/reflect, still TTS-friendly.
unknown: 60–120 Chinese chars.
```

Learning/safety/privacy/bedtime can be shorter or use existing scene-specific constraints.

### B4.3 Inject age guidance into prompt

Add a runtime prompt section or extend existing child profile/turn guidance so the composed prompt includes:

```text
age_band
reply_char_budget
question_policy
```

This guidance must be internal; Xiaobaihu must not say “你的 age_band 是 age_7_8”.

### B4.4 Add continuous-question throttle thin slice

Implement a lightweight rule using available in-memory/session context. It does not need a new DB table.

Minimum acceptable behavior:

```text
1. Track or infer same-topic / consecutive-question tendency within a session.
2. If Xiaobaihu has asked questions in 2–3 consecutive ordinary open-conversation turns, the next ordinary open-conversation turn should prefer:
   - reflect without asking, or
   - give choice to continue/stop, or
   - bridge to real life/parent, not another deeper interview question.
3. If child says “换个话题 / 不聊了 / 今天不聊了 / 睡觉了”, the reply must not continue the old topic or ask a new engaging hook.
4. Correction turn, e.g. child says “不是 / 你说错了 / 我还没跑”, should prioritize acknowledging correction and not stack another large follow-up.
```

You can implement this with runtime guidance hints and/or post-processing in `ChildAgentRuntime`, but keep it testable.

### B4.5 Runtime safety normalization

If the model still outputs too many questions or an overlong ordinary reply:

```text
1. keep existing safety/learning/privacy logic first,
2. for ordinary conversation, trim or rewrite to fit age budget,
3. preserve one main idea,
4. allow zero questions.
```

Do not truncate in the middle of a sentence if avoidable.

## B5. Acceptance criteria

```text
1. Prompt no longer hard-codes only “8 岁二年级儿童” as the global identity.
2. Composed prompt includes age-band guidance when parent policy has age/age_band.
3. age_5_6 ordinary open conversation produces shorter, simpler guidance than age_9_10.
4. Consecutive-question throttle has tests.
5. “换个话题 / 不聊了 / 睡觉了” tests pass and do not produce new hooks.
6. Direct homework answer refusal and safety trusted-adult behavior still pass existing tests.
```

## B6. Tests

Add/update backend tests for:

```text
1. age_band derivation from explicit age_band.
2. age_band derivation from numeric child_age.
3. default age_band when missing.
4. composed prompt contains age guidance and char budget.
5. ordinary open reply for age_5_6 is normalized shorter than age_9_10 if model returns long text.
6. consecutive question throttle inserts “no more interview” guidance or post-processes output.
7. child boundary phrases: 换个话题 / 不聊了 / 睡觉了.
8. correction phrase: 你说错了 / 不是.
```

Run relevant backend tests:

```bash
cd backend
pytest
ruff check .
```

If full pytest is too slow, run targeted tests first, but final report must say what was and was not run.

---

## 3. Documentation updates

Lane A updates:

```text
android/README.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
```

Lane B updates:

```text
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

Rules:

```text
1. Do not mark true device QA as passed unless a real device was tested.
2. Mark Redmi K60 / Honor Pad 5 as pending if not tested.
3. Do not claim final Healthy Engagement is complete; this is a thin slice.
4. Do not write planned features as shipped.
```

---

## 4. Final response required from Codex

Codex must report:

```text
1. branch/commit sha(s),
2. which lane(s) were completed,
3. modified files,
4. test commands and exact results,
5. any conflicts or skipped tests,
6. remaining QA items,
7. whether implementation stayed within scope.
```

If running in parallel, each lane reports separately, then a final merged summary reports the combined main state.
