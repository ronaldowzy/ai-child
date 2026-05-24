# Codex Task 04: Healthy Engagement, QA, and State Coverage v0.1

Project: `ai-child` / `ronaldowzy/ai-child`  
Target branch: `main`  
Task type: coordinated hardening batch after Task 03  
Recommended mode: three Codex sessions on separate branches/worktrees; if only one Codex session is available, execute Lane A, then Lane B, then Lane C.

---

## 0. Position in the roadmap

Run this task after `docs/CODEX_TASK_03_IMAGE_AND_PARENT_BRIDGE_V0_1.md` has been implemented and merged.

Task 01 completed Android child-facing interaction phase.
Task 02 completed Android TTS/phase closeout and backend age-band/question-throttle thin slice.
Task 03 should complete image sharing “具体看见” and parent bridge/father report UX.

Task 04 hardens the experience system so it can be evaluated in family beta:

```text
Lane A: Healthy Engagement observability, using non-content metrics.
Lane B: Family beta QA checklist and smoke/runbook consolidation.
Lane C: Xiaobaihu visual/state coverage matrix and tests.
```

This task intentionally does not add new child-facing features. It turns the existing product principles into measurable, reviewable engineering artifacts.

---

## 1. Shared required reading

Before coding, read:

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md
docs/EXPERIENCE_REVIEW_AND_NEXT_OPTIMIZATION_GUIDE_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md
```

Also inspect the latest implementation from Task 01–03 before choosing exact files.

---

## 2. Coordination rules

Use separate branches if multiple Codex agents are available:

```text
codex/e5-01-healthy-engagement-observability
codex/e6-01-family-beta-qa-checklist
codex/fox-state-coverage-matrix
```

Suggested merge order:

```text
1. Lane C first if it only adds docs/tests and does not affect runtime behavior.
2. Lane A second because it may touch backend runtime/logging.
3. Lane B last so QA docs reflect the latest state after Lane A/C.
```

Avoid multiple lanes editing the same file in parallel unless unavoidable. If conflicts occur, resolve `docs/CODEX_PROGRESS_BOARD_V0_1.md` after all implementation lanes are ready.

If only one Codex agent is available:

```text
1. Lane C: state coverage matrix first.
2. Lane A: Healthy Engagement observability.
3. Lane B: final QA checklist/runbook.
```

---

# Lane A — Healthy Engagement Observability

## A1. Goal

Make Healthy Engagement testable and observable without storing raw child content.

The system should be able to answer, in logs/tests, questions like:

```text
1. Did Xiaobaihu continue asking after the child said “不聊了/睡觉了/换话题”？
2. How many consecutive question turns happened in an ordinary conversation?
3. Was the reply age-band limited?
4. Was a bedtime boundary respected?
5. Did a turn include TTS/stream first text/first audio timing?
```

This is not analytics for growth/retention. It is safety and experience QA telemetry.

## A2. Allowed files

Backend:

```text
backend/app/services/conversation_service.py
backend/app/services/conversation_stream_service.py
backend/app/services/child_agent_runtime.py
backend/app/services/turn_guidance_builder.py
backend/app/core/logging.py
backend/app/domain/schemas/conversation.py
backend/app/tests/**/*healthy* or relevant runtime/logging tests
```

Docs:

```text
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/OPS_FOUNDATION_GAP_ANALYSIS_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## A3. Do not do

```text
1. Do not record full child text in logs.
2. Do not record full assistant text in logs.
3. Do not record raw audio, raw image, parent_message_raw, Authorization, API keys, DB URLs, or provider secrets.
4. Do not add retention/growth metrics such as streaks, daily active child score, reward hooks, or engagement targets.
5. Do not block the child response path if telemetry logging fails.
```

## A4. Required metrics

Add a lightweight per-turn Healthy Engagement metric object or structured log fields. Names can vary, but must cover:

```text
turn_index or recent_history_turns
active_scene
age_band
reply_char_count
question_count
turn_guidance_hints
boundary_signal: none/topic_change/no_chat/bedtime_close/correction
boundary_respected: true/false/unknown
same_topic_score
consecutive_recent_questions
reply_normalized: true/false
first_text_ms if available in stream path
first_audio_ms if available in stream/TTS path
turn_total_ms if available
```

If some timings are unavailable in the non-stream path, use `null` or omit with documentation. Do not fake timings.

## A5. Boundary detection

Reuse or extend `TurnGuidanceBuilder` so the metric can classify:

```text
child_requests_topic_change
bedtime_close_requested
child_correction
too_many_recent_questions
same_topic_too_long
```

For `boundary_respected`, a thin slice is enough:

```text
true if boundary hint exists and normalized reply contains no question mark and does not revive the old topic.
false if boundary hint exists and reply contains a new open hook/question.
unknown if no boundary hint.
```

## A6. Tests

Add tests for:

```text
1. “不聊了/换个话题” emits boundary_signal and boundary_respected=true when reply has no new hook.
2. “睡觉了/晚安” emits bedtime_close and boundary_respected=true.
3. Consecutive question throttle emits too_many_recent_questions.
4. Log/metric payload does not contain raw child_text or raw reply_text.
5. Telemetry failure does not break conversation response.
```

Run:

```bash
cd backend
pytest
ruff check .
```

If full pytest is too slow, run targeted tests plus document what was not run.

## A7. Acceptance criteria

```text
1. Healthy Engagement metrics exist in structured, testable form.
2. Metrics are non-content and privacy-safe.
3. Boundary respect is measurable for no-chat/topic-change/bedtime/correction thin slice.
4. Existing child safety, parent report, stream, and prompt tests continue to pass.
5. Docs clearly say this is observability, not retention optimization.
```

---

# Lane B — Family Beta QA Checklist and Runbook

## B1. Goal

Create one actionable family-beta QA checklist that testers can use on Redmi K60 and Honor Pad 5 without reading all design docs.

This lane is mostly docs/scripts. It should not implement new product features.

## B2. Allowed files

```text
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/MANUAL_QA_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/NEXT_PHASE_PLAN_V0_2.md
scripts/*qa* or scripts/*smoke* if useful
android/README.md
backend/README.md
```

## B3. Do not do

```text
1. Do not claim real-device QA passed unless a device was actually tested.
2. Do not include real child audio, real child photos, or private family data as test fixtures.
3. Do not make QA depend on production secrets.
4. Do not create a massive unreadable checklist; prefer tables with pass/fail/evidence.
```

## B4. Required checklist sections

Create/update `docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md` with these sections:

```text
1. Build and environment
2. Backend health and PostgreSQL
3. Android install and horizontal layout
4. Opening greeting
5. Voice-first ASR: permission, recording, auto-send, retry, cancel
6. TTS: remote audio, segment queue, stop, mute/unmute, failure without system voice mixing
7. Xiaobaihu state: Ready/Listening/Recognizing/Thinking/Speaking/ImageProcessing/NeedsRetry/PermissionNeeded/ServiceError
8. Age-banded reply and question throttle scenarios
9. Image sharing: ordinary image, dark/unclear image, homework-like image, privacy-like image, upload failure
10. Parent entry: normal tap, long press, wrong PIN, correct PIN, report/settings access
11. Father report: success, model_failed/model_blocked, empty material, tonight bridge
12. Healthy Engagement boundaries: 换话题/不聊了/睡觉了/你说错了
13. Weak network/backend down
14. Device-specific notes: Redmi K60 and Honor Pad 5
```

Each row should include:

```text
ID
Scenario
Steps
Expected result
Actual result
Status: PASS/FAIL/BLOCKED/NOT_RUN
Evidence: video timestamp/request_id/log path
Notes
```

## B5. Optional helper scripts

If useful, add a tiny script to print local QA environment status, but avoid overengineering. Existing smoke scripts may already be enough.

## B6. Acceptance criteria

```text
1. Checklist is detailed enough to run without asking the master session.
2. It distinguishes automated smoke from real-device QA.
3. It includes the new Task 01–03 experience changes.
4. It does not mark unrun scenarios as passed.
5. CODEX_PROGRESS_BOARD points testers to the checklist.
```

---

# Lane C — Xiaobaihu State Coverage Matrix

## C1. Goal

Ensure the visual/animation state system is not just implemented but covered: every meaningful child-facing phase has a mapped Xiaobaihu visual state, asset fallback, and QA trigger.

## C2. Allowed files

Android:

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChildTurnUiPhase.kt
android/app/src/main/java/com/childai/companion/ui/chat/CartoonAgentView.kt
android/app/src/main/java/com/childai/companion/mascot/*
android/app/src/test/java/com/childai/companion/ui/chat/*
android/app/src/test/java/com/childai/companion/mascot/*
```

Docs:

```text
docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## C3. Do not do

```text
1. Do not regenerate art assets.
2. Do not add heavy 3D engine work.
3. Do not break animation_v1 manifest fallback.
4. Do not increase APK asset size significantly.
```

## C4. Required state matrix

Add a matrix covering at least:

```text
Ready
Listening
Recognizing
Thinking
SpeakingPending
Speaking
ImageProcessing
NeedsRetry
PermissionNeeded
Resting
ServiceError
OpeningGreeting
PrivacyBoundary
SafetyConcern
HomeworkFocus
NetworkError
```

Columns:

```text
Child-facing phase or scene
FoxMood
FoxMotion
MascotState / animation asset if any
Fallback behavior
Triggered by which code path
QA scenario ID
Status: implemented / resource_ready_but_not_triggered / missing_asset / pending_QA
```

## C5. Tests

Add tests where possible:

```text
1. ChildTurnUiPhase maps to expected FoxMood/FoxMotion.
2. MascotController has a defined state/fallback for every phase-derived agent state.
3. Missing manifest/asset fallback does not crash.
```

## C6. Acceptance criteria

```text
1. FOX_AGENT_VISUAL_DESIGN contains a current state coverage matrix.
2. At least one test verifies phase-to-agent mapping.
3. Missing or untriggered states are honestly marked, not hidden.
4. QA checklist references the state coverage scenarios.
```

---

## 3. Documentation update rules

Each lane should update only what it owns. Final merge should update:

```text
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

Rules:

```text
1. Mark code-complete separately from real-device QA.
2. Do not claim Healthy Engagement is fully solved; mark thin slice.
3. Do not say family beta ready until real device QA rows are PASS.
4. If Task 03 has not been implemented yet, do not execute this task; keep it pending.
```

---

## 4. Final response required from Codex

Codex must report:

```text
1. branch/commit sha(s),
2. which lanes were completed,
3. modified files by lane,
4. test commands and exact results,
5. any skipped tests or unavailable devices,
6. remaining QA items,
7. whether implementation stayed within allowed files and scope,
8. any product decisions that need master-session review.
```
