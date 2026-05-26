# CODE_AGENT_TASK_22_XIAOBAIHU_RUNTIME_VISUAL_TRANSITION_THROTTLE_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: focused Android runtime quality improvement after Task 21  
Goal: make Xiaobaihu visual state changes feel stable and calm by enforcing lightweight runtime transition hold rules, without changing assets or product content.

---

## 0. Why this task

Task 17 implemented the Xiaobaihu visual state v2 resolver. The resolver now exposes:

```text
baseAttention,
emotionalOverlay,
boundaryOverlay,
mascotState,
minHoldMs,
reason.
```

But runtime display still changes mainly through the existing `CartoonAgentView` / `MascotController.stateFor(agent)` path. `minHoldMs` is metadata today; it is not yet a runtime anti-flicker rule.

Task 22 should turn this metadata into safe runtime behavior.

The goal is not to make Xiaobaihu more animated. The goal is to make Xiaobaihu less jumpy.

---

## 1. Product rules

Xiaobaihu should feel like a warm companion, not:

```text
1. a loading spinner;
2. a reward animation;
3. a gamified pet;
4. a scary alert;
5. a constantly flickering UI indicator.
```

Runtime transition rules must preserve these decisions:

```text
1. safety_concern and privacy_boundary should hold calmly and not flash;
2. network_error should be visible long enough to understand, but not feel alarming;
3. thinking should not flicker if ASR/stream phases change quickly;
4. listening and speaking should remain responsive to actual recording/playback state;
5. jumping_happy must not be wired to rewards, streaks, correct answers, check-ins, or retention;
6. sleepy must not be used to keep the child chatting;
7. do not add new mascot assets;
8. do not rewrite the animation engine.
```

---

## 2. Required reading

```text
docs/CODE_AGENT_PROJECT_CONTEXT_AND_WORKFLOW_V0_1.md
docs/CODE_AGENT_TASK_17_XIAOBAIHU_VISUAL_STATE_V2_RESOLVER_V0_1.md
docs/XIAOBAIHU_STATE_AND_ANIMATION_AUDIT_V0_1.md
docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuVisualStateResolver.kt
android/app/src/main/java/com/childai/companion/ui/chat/CartoonAgentView.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/mascot/MascotController.kt
android/app/src/main/java/com/childai/companion/mascot/FrameSequencePlayer.kt
```

Current important facts:

```text
1. `AgentPanel` passes `presentation.agent` to `CartoonAgentView`.
2. `CartoonAgentView` currently computes `baseMascotState = debugMascotState ?: mascotController.stateFor(agent)`.
3. `XiaobaohuVisualStateResolver` already computes `mascotState`, `minHoldMs`, and `reason`.
4. Runtime min-hold enforcement is not yet wired into the displayed state.
```

---

## 3. Scope

Allowed:

```text
1. Add a small runtime state holder / transition throttle for Xiaobaihu visual state.
2. Wire `XiaobaohuVisualStateResolver` into the displayed mascot state path.
3. Enforce `minHoldMs` for non-emergency visual transitions.
4. Add JVM unit tests for transition timing logic.
5. Add or adjust small Compose-adjacent helper code if needed, but avoid broad UI layout changes.
6. Update QA checklist / progress board only if needed for Task 22 status.
```

Forbidden:

```text
1. Do not add or replace mascot image/frame assets.
2. Do not change animation manifest state IDs.
3. Do not rewrite `FrameSequencePlayer` broadly.
4. Do not change TTS provider, ASR, image upload, backend conversation, auth/account, parent report, opening, prompt files, or parent settings UI.
5. Do not introduce gamification, reward states, streaks, tasks, badges, or retention hooks.
6. Do not wire `jumping_happy` to correctness, task completion, return visits, or check-ins.
7. Do not add raw child transcript/audio/image logging.
```

---

## 4. Required implementation

### 4.1 Runtime transition holder

Add a small deterministic class, for example:

```text
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuVisualStateRuntime.kt
```

Suggested model:

```kotlin
data class XiaobaohuDisplayedVisualState(
    val visualState: XiaobaohuVisualState,
    val displaySinceMs: Long,
    val pendingState: XiaobaohuVisualState? = null,
)
```

or a simpler equivalent. Exact names can vary.

It should expose a pure function that is easy to test, for example:

```kotlin
fun reduce(
    current: XiaobaohuDisplayedVisualState?,
    requested: XiaobaohuVisualState,
    nowMs: Long,
): XiaobaohuDisplayedVisualState
```

The reducer should be framework-independent where possible, so it can be tested without Compose timing flakiness.

### 4.2 Min-hold rules

Use `requested.minHoldMs` and current displayed state metadata.

Expected behavior:

```text
1. If there is no current state, display requested immediately.
2. If requested mascotState equals current mascotState, keep it and update metadata safely.
3. If current state has minHoldMs > 0 and not enough time has elapsed, keep current state and store pending requested state.
4. Once hold time has elapsed, switch to pending/requested state.
5. Higher-priority urgent states may replace lower-priority states immediately where product-safe.
```

Use Task 17 precedence as the starting point:

```text
network_error > safety_concern > privacy_boundary > homework_focus > speaking > thinking/looking_at_image > listening > resting > idle
```

Important nuance:

```text
- network_error, safety_concern, privacy_boundary should not flicker away instantly.
- speaking should be responsive when playback starts.
- listening should remain responsive when recording starts/stops.
- thinking should hold briefly to avoid Recognizing -> Thinking -> Speaking flicker.
```

### 4.3 Runtime wiring

Wire the runtime holder into the mascot display path.

Preferred minimal integration:

```text
1. Resolve `XiaobaohuVisualState` from existing `presentation.phase` + `presentation.agent` or from agent if phase is not available.
2. Apply transition throttle.
3. Pass the resulting `MascotState` to the existing render path.
4. Keep debugMascotState behavior working for debug switcher; debug override may bypass throttle.
```

Possible implementation options:

```text
Option A: Add a `phase` or `visualState` parameter to `CartoonAgentView` and compute runtime displayed state inside it.
Option B: Compute displayed visual state in `AgentPanel` and pass `debugMascotState` / resolved state into `CartoonAgentView`.
```

Choose the smallest safe change. Do not refactor the entire chat UI.

### 4.4 No new visible copy unless necessary

This task is visual runtime behavior. Do not rewrite child-facing copy. If tests need names/reasons, keep them internal.

---

## 5. Acceptance criteria

```text
1. Runtime transition throttle exists and is unit-tested.
2. Current `XiaobaohuVisualStateResolver.minHoldMs` participates in displayed state decisions.
3. Thinking has a short hold that prevents fast flicker.
4. Safety/privacy/network states do not flash away immediately.
5. Speaking remains responsive enough to start when audio playback begins.
6. Debug mascot switcher still works.
7. No new assets, no manifest state changes, no animation engine rewrite.
8. No TTS/ASR/auth/backend conversation/parent report/opening changes.
9. `jumping_happy` and `sleepy` are not newly wired into runtime reward/retention paths.
```

---

## 6. Required tests

Add or strengthen JVM tests. Suggested test file:

```text
android/app/src/test/java/com/childai/companion/ui/chat/XiaobaohuVisualStateRuntimeTest.kt
```

Required test cases:

```text
1. initial requested state displays immediately;
2. thinking holds for at least `THINKING_MIN_HOLD_MS` before switching to idle/listening if no urgent replacement;
3. safety_concern holds for at least `SAFETY_CONCERN_MIN_HOLD_MS` before returning to idle;
4. privacy_boundary holds for at least `PRIVACY_BOUNDARY_MIN_HOLD_MS`;
5. network_error holds for at least `NETWORK_ERROR_MIN_HOLD_MS`;
6. speaking can replace thinking promptly when speaking starts;
7. pending requested state is applied after hold expires;
8. jumping_happy is not introduced by the runtime throttle;
9. debug override path remains deterministic if touched.
```

Keep tests deterministic. Do not depend on wall-clock time; pass `nowMs` explicitly.

---

## 7. Test commands

Run:

```bash
cd android && ./gradlew test
```

If running a narrower test first, also report the exact class command, for example:

```bash
cd android && ./gradlew test --tests '*XiaobaohuVisualStateRuntimeTest'
```

Final report must include exact commands and results. Do not claim real-device QA passed unless a device was used.

---

## 8. Final response required

Report:

```text
1. commit sha;
2. files changed;
3. runtime transition model added;
4. how `minHoldMs` is enforced;
5. which states can interrupt holds immediately and why;
6. tests run and exact results;
7. confirmation no assets/TTS/ASR/auth/backend conversation/parent report/opening changes were made;
8. remaining Redmi K60 / Honor Pad 5 QA items.
```

---

## 9. Review guidance for master session

When reviewing Task 22, first compare file scope. Reject if the patch changes unrelated backend, voice, account, image upload, parent report, prompt files, or mascot assets.

Then inspect:

```text
1. whether the runtime reducer is pure and deterministic;
2. whether hold timing is based on explicit `nowMs` in tests;
3. whether safety/privacy/network states are stable;
4. whether speaking remains responsive;
5. whether no reward/retention animation wiring was introduced.
```
