# CODE_AGENT_TASK_17_XIAOBAIHU_VISUAL_STATE_V2_RESOLVER_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: focused Android implementation after design audit  
Goal: implement Xiaobaihu visual state v2 resolver and coverage tests without adding new art assets.

---

## 0. Why this task

Task 16 completed the design audit in:

```text
docs/XIAOBAIHU_STATE_AND_ANIMATION_AUDIT_V0_1.md
```

Core conclusion:

```text
1. 11 animation states exist and are declared in manifest.
2. Android MascotState covers all 11 state IDs.
3. Core states idle/listening/thinking/speaking/network_error/safety_concern are genuinely triggered today.
4. privacy_boundary/homework_focus rely on backend signals.
5. calm/sleepy/jumping_happy are resource-ready but should not be treated as product-complete states.
6. Xiaobaihu should use a layered companion state model, not one animation per backend scene.
```

Task 17 implements the next safe layer: a visual state resolver, coverage tests, and transition hold rules. It must not generate new assets or redesign the character.

---

## 1. Required reading

```text
docs/XIAOBAIHU_STATE_AND_ANIMATION_AUDIT_V0_1.md
docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md
docs/CHILD_UI_POLISH_DESIGN_V0_1.md
android/app/src/main/java/com/childai/companion/ui/chat/ChildTurnUiPhase.kt
android/app/src/main/java/com/childai/companion/ui/chat/CartoonAgentView.kt
android/app/src/main/java/com/childai/companion/mascot/*
android/app/src/main/assets/mascot/xiaobaohu/v1/mascot_manifest.json
```

---

## 2. Product rules

Xiaobaihu should feel like a warm companion, not:

```text
1. a button animation;
2. a customer-service loading spinner;
3. a reward loop;
4. a gamified pet;
5. a scary safety alert.
```

Do not use `jumping_happy` for:

```text
1. check-ins;
2. streaks;
3. task completion;
4. correct answers;
5. retention hooks;
6. “come back tomorrow” moments.
```

`jumping_happy` may only be used, if at all, for rare, brief, non-addictive warm encouragement after a child shares a positive moment. If unsure, do not use it.

`sleepy` should only be used for bedtime/low-stimulation closing, not to keep the child chatting.

`privacy_boundary` and `safety_concern` should hold calmly and not flash.

---

## 3. Required implementation

### 3.1 Add a Visual State Resolver

Add a small resolver layer, e.g.:

```text
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuVisualStateResolver.kt
```

The resolver should convert existing inputs into a resolved state model:

```kotlin
data class XiaobaohuVisualState(
    val baseAttention: BaseAttentionState,
    val emotionalOverlay: EmotionalOverlay,
    val boundaryOverlay: BoundaryOverlay,
    val mascotState: MascotState,
    val minHoldMs: Long,
    val reason: String,
)
```

Exact names can vary, but the logic must express:

```text
Base attention state:
- idle / ready
- listening
- thinking
- speaking
- looking_at_image
- resting

Emotional overlay:
- warm
- curious
- encouraging
- calm
- concerned
- sleepy

Boundary/safety overlay:
- none
- privacy_boundary
- safety_concern
- network_error
- homework_focus
```

### 3.2 State precedence

Recommended precedence:

```text
network_error > safety_concern > privacy_boundary > homework_focus > speaking > thinking/looking_at_image > listening > resting > idle
```

But do not let rare overlays create fast flicker.

### 3.3 Hold/min display rules

Implement simple min-hold metadata, even if enforcement is initially in resolver/tests only:

```text
network_error: 1200ms
safety_concern: 1500ms
privacy_boundary: 1200ms
homework_focus: 800ms
speaking: while speaking
thinking: at least 500ms unless speaking begins
listening: while recording
jumping_happy: at most short loop, not auto-triggered by default
```

If full runtime enforcement in `CartoonAgentView` is too risky, expose minHoldMs and add tests; runtime enforcement can be a follow-up. Prefer a safe thin slice.

### 3.4 Looking-at-image state

There is no dedicated asset today. Use `thinking` for `ImageProcessing`, but reason should be `looking_at_image_uses_thinking_asset`. Document this, do not invent a new asset.

### 3.5 Resource/manifest completeness test

Add or strengthen tests to prove:

```text
1. every MascotState asset ID exists in manifest;
2. every manifest state has a known MascotState;
3. unknown/missing state falls back to Idle;
4. animation_v1 fallback remains safe.
```

### 3.6 Business trigger coverage test

Add tests for these paths:

```text
Ready -> idle
Listening -> listening
Recognizing -> thinking
Thinking/Sending -> thinking
SpeakingPending/Speaking -> speaking
ImageProcessing -> thinking with looking_at_image reason
PermissionNeeded -> safety_concern
ServiceError -> network_error
Resting -> calm
backend privacy signal -> privacy_boundary
backend homework signal -> homework_focus
backend safety signal -> safety_concern
```

### 3.7 Do not add new assets

No new frames, no new manifest state IDs, no animation engine rewrite.

---

## 4. Allowed files

```text
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuVisualStateResolver.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildTurnUiPhase.kt
android/app/src/main/java/com/childai/companion/ui/chat/CartoonAgentView.kt  # only if needed for minHold metadata, avoid broad changes
android/app/src/main/java/com/childai/companion/mascot/*  # tests/support only unless necessary
android/app/src/test/java/com/childai/companion/ui/chat/*State*Test.kt
android/app/src/test/java/com/childai/companion/mascot/*Manifest*Test.kt
docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
```

Do not modify:

```text
animation assets / frames
TTS
ASR
auth/account
backend conversation logic
parent report
image upload transport
```

---

## 5. Acceptance criteria

```text
1. Visual state resolver exists and is unit-tested.
2. State precedence is explicit and tested.
3. ImageProcessing is documented/tested as looking_at_image using thinking asset.
4. Manifest completeness tests exist.
5. Business trigger coverage tests exist.
6. calm/sleepy/jumping_happy are not overused or reward-wired.
7. No new assets or animation engine rewrite.
```

---

## 6. Test commands

Run:

```bash
cd android && ./gradlew test
```

If adding only JVM tests, report exact test classes and result.

---

## 7. Final response required

Report:

```text
1. commit sha;
2. files changed;
3. visual state resolver model;
4. state precedence summary;
5. manifest completeness test result;
6. business trigger coverage test result;
7. confirmation no assets/TTS/ASR/auth/backend conversation changes were made;
8. remaining Redmi K60 / Honor Pad 5 QA items.
```
