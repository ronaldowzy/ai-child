# CODE_AGENT_TASK_22_CORRECTION_COMPOSE_RUNTIME_HOLD_TIMER_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: correction patch for Task 22  
Goal: fix runtime integration so Xiaobaihu visual min-hold works reliably in Compose without mutating state during composition or requiring incidental recomposition.

---

## 0. Review finding

Task 22 implementation added a good pure reducer:

```text
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuVisualStateRuntime.kt
```

and tests:

```text
android/app/src/test/java/com/childai/companion/ui/chat/XiaobaohuVisualStateRuntimeTest.kt
```

But runtime wiring in `CartoonAgentView.kt` currently does this during composition:

```kotlin
val nowMs = System.currentTimeMillis()
val next = XiaobaohuVisualStateRuntime.reduce(...)
displayedState = next
next.mascotState
```

This has two product/engineering problems:

```text
1. It mutates Compose state during composition.
2. It does not schedule a timer for minHoldMs expiry, so a pending state may not be applied when the hold expires unless another unrelated recomposition happens.
```

The pure reducer is useful and should be kept, but the Compose integration needs a small correction.

---

## 1. Allowed files

```text
android/app/src/main/java/com/childai/companion/ui/chat/CartoonAgentView.kt
android/app/src/main/java/com/childai/companion/ui/chat/XiaobaohuVisualStateRuntime.kt
android/app/src/test/java/com/childai/companion/ui/chat/XiaobaohuVisualStateRuntimeTest.kt
android/app/src/test/java/com/childai/companion/ui/chat/*Cartoon*State*Test.kt  # optional if useful
```

Forbidden:

```text
backend/*
TTS/ASR/image upload/auth/account/parent report/opening/prompt files
mascot image/frame assets
manifest state IDs
animation engine rewrite
new reward/retention behavior
```

---

## 2. Required correction

### 2.1 Do not mutate state during composition

Move runtime state updates into a Compose side-effect, most likely `LaunchedEffect` keyed by requested visual state / debug override.

The render path should read a stable `displayedState` value, not assign to it inline while composing.

### 2.2 Schedule min-hold expiry

When the reducer keeps the current state because `current.minHoldMs` has not expired and stores a pending state, the Compose integration must schedule a delayed reduction at the correct expiry time.

Expected behavior:

```text
1. requested Thinking displays immediately;
2. requested Idle arrives after 100ms, but Thinking minHoldMs is 500ms;
3. UI keeps Thinking;
4. after the remaining 400ms, UI switches to Idle without needing another external state change.
```

Use coroutine `delay(remainingMs)` inside `LaunchedEffect` or an equivalent Compose-safe approach.

### 2.3 Keep urgent interrupts responsive

Speaking should still interrupt Thinking promptly when playback starts.

Safety/privacy/network should still not flicker away.

Debug mascot switcher should remain deterministic and may bypass the throttle.

### 2.4 Keep the reducer deterministic

If needed, extend `XiaobaohuDisplayedVisualState` to keep enough information for pending state expiry. Avoid wall-clock dependency in unit tests.

Recommended additions if useful:

```kotlin
val pendingMinHoldMs: Long? = null
```

or a small pending data class.

Do not over-engineer.

---

## 3. Required tests

Keep the existing reducer tests and add at least one test proving the reducer carries enough pending metadata for scheduled expiry if you change the data model.

Because Compose timer behavior is harder to unit-test without UI test setup, minimum acceptable test coverage is:

```text
1. pure reducer keeps current state and records pending requested state before hold expiry;
2. pure reducer switches after hold expiry when requested/pending state is applied;
3. speaking still interrupts thinking immediately;
4. safety/privacy/network states do not switch to idle before minHoldMs;
5. no jumping_happy or sleepy auto-wiring.
```

If a lightweight Compose test is practical, add it. If not, explain why runtime timer wiring is manually reviewed and covered through reducer tests.

---

## 4. Test commands

Run:

```bash
cd android && ./gradlew test --tests '*XiaobaohuVisualStateRuntimeTest'
cd android && ./gradlew test
```

Report exact command output summary.

Do not claim real-device QA passed unless a real device was used.

---

## 5. Final report required

Report:

```text
1. commit sha;
2. files changed;
3. exact Compose-side runtime update approach;
4. how minHoldMs expiry is scheduled;
5. why state is no longer mutated during composition;
6. tests run and exact results;
7. confirmation no forbidden files/areas were touched;
8. remaining device QA items as NOT_RUN if not tested.
```
