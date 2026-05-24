# Codex Task 08: Real Device QA Round 2 and Fix Triage v0.1

Project: `ai-child` / `ronaldowzy/ai-child`  
Target branch: `main`  
Task type: post-Task-07 real-device QA support and narrow fix triage  
Run after: `docs/CODEX_TASK_07_TASK06_CLOSEOUT_AND_LATENCY_UI_HARDENING_V0_1.md`

---

## 0. Purpose

Task 07 closes the main post-device QA refinement gaps:

```text
1. hidden parent schedule no longer blocks save or rewrites defaults;
2. topic seeds are reviewed/static/expiring objects;
3. child chat has a small topic-shift chip thin slice;
4. backend and Android have TTS latency timing fields/logs;
5. father report has stronger CS/game summary tests.
```

Task 08 is not a feature-building task. It coordinates the next real-device QA round and turns observed issues into narrow fixes only.

If no new Redmi K60 / Honor Pad 5 QA video or logs are available, Codex should only prepare/verify the QA build package and update docs. Do not invent fixes for unobserved problems.

---

## 1. Required inputs

Before doing code fixes, collect as many of these as available:

```text
1. latest main commit sha;
2. Android debug APK build result and path;
3. Redmi K60 screen recording or timestamp notes;
4. Honor Pad 5 recording or timestamp notes if available;
5. backend request_id for at least one slow TTS turn;
6. Android logcat lines tagged `XiaobaohuTtsTiming` for the same slow turn;
7. father report date and whether generated_by=model/model_failed;
8. whether local_sensevoice ASR or MiMo fallback was used.
```

Do not request raw child audio, raw photos, full private family transcripts, API keys, DB dumps, or production secrets.

---

## 2. Shared reading

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/CODEX_TASK_07_TASK06_CLOSEOUT_AND_LATENCY_UI_HARDENING_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
docs/CHILD_UI_POLISH_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
android/README.md
backend/README.md
```

---

## 3. Coordination model

If real-device evidence is available, split into lanes:

```text
Lane A: build/package and QA evidence indexing.
Lane B: voice/TTS latency and playback fixes.
Lane C: conversation rhythm/topic-shift/father-report fixes.
Lane D: Android layout/UI polish regressions.
```

Suggested merge order:

```text
1. Lane A first if it updates docs/build notes.
2. Lane B/C/D only for observed issues.
3. Final docs update after all fixes.
```

If no real-device evidence is available, only execute Lane A.

---

# Lane A — QA Build Package and Evidence Index

## A1. Goal

Prepare the exact build/test package for human QA and index evidence cleanly.

## A2. Allowed files

```text
android/README.md
backend/README.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/NEXT_PHASE_PLAN_V0_2.md
scripts/*qa*
scripts/*smoke*
```

## A3. Required checks

Run or document:

```bash
cd backend && pytest
cd backend && ruff check .
cd android && ./gradlew test
cd android && ./gradlew assembleDebug
```

If unavailable/too slow, record exact reason.

## A4. QA package notes

Document:

```text
1. APK path and SHA256.
2. backend base URL used for LAN testing.
3. current commit sha.
4. request_id/log collection instructions.
5. `adb logcat | grep XiaobaohuTtsTiming` or platform equivalent.
6. which scenarios are NOT_RUN vs PASS/FAIL/BLOCKED.
```

---

# Lane B — Voice/TTS Latency Triage

Run only if slow-turn request_id/logcat evidence is available.

## B1. Goal

Use logs to classify delay:

```text
1. model_ms high;
2. tts_ms / first_audio_ms high;
3. Android remote_audio_url_received -> playback_started high;
4. network/download/prepare failure;
5. segment queue blockage.
```

## B2. Allowed files

```text
backend/app/services/conversation_service.py
backend/app/services/conversation_stream_service.py
backend/app/services/tts_service.py
backend/app/tests/**/*tts* or stream tests
android/app/src/main/java/com/childai/companion/voice/*
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/test/java/com/childai/companion/voice/*
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
```

## B3. Do not do

```text
1. Do not switch providers without a product decision.
2. Do not reintroduce Android system TTS fallback.
3. Do not expose latency debug text in child UI.
4. Do not log raw child text or full reply text in timing logs.
```

## B4. Acceptance criteria

```text
1. Each observed slow turn is classified by source.
2. Fixes are narrow and test-backed.
3. Remaining provider latency is documented rather than hidden.
```

---

# Lane C — Conversation Rhythm / Topic Shift / Father Report Triage

Run only if QA evidence shows poor topic rhythm, awkward topic chips, or father report readability issues.

## C1. Goal

Tune the child conversation and parent report based on observed QA, not guesses.

## C2. Allowed files

```text
backend/app/services/turn_guidance_builder.py
backend/app/services/child_agent_runtime.py
backend/app/services/topic_seed_service.py
backend/app/services/parent_report_service.py
backend/app/tests/**/*turn_guidance* or parent_report tests
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
```

## C3. Do not do

```text
1. Do not add live web trend lookup.
2. Do not make topic chips into tasks/rewards/streaks.
3. Do not show raw transcript in parent report.
4. Do not overfit to one adult tester phrase if it harms child generality.
```

## C4. Acceptance criteria

```text
1. If topic shift still comes too late, tests capture the observed sequence.
2. If topic shift comes too early, tests distinguish high-engagement continuation.
3. Father report changes preserve summary-not-transcript boundary.
```

---

# Lane D — Android Layout/UI Polish Regression Triage

Run only if real-device QA shows layout or child-facing UI issues.

## D1. Goal

Fix observed layout/readability regressions on Redmi K60 or Honor Pad 5.

## D2. Allowed files

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/InputBar.kt
android/app/src/main/java/com/childai/companion/ui/parent/*
android/app/src/test/java/com/childai/companion/ui/chat/*
docs/CHILD_UI_POLISH_DESIGN_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
```

## D3. Do not do

```text
1. Do not add heavy new art/3D engine.
2. Do not hide stop/mute/retry controls.
3. Do not add points, badges, pet hunger, streaks, or ranking.
```

## D4. Acceptance criteria

```text
1. Fix maps to a concrete timestamp/device symptom.
2. Low-end Honor Pad remains prioritized for layout simplicity.
3. Tests/docs record NOT_RUN if device was unavailable.
```

---

## 4. Final Codex response requirements

Codex must report:

```text
1. commit sha(s),
2. whether real-device evidence was available,
3. lanes executed or skipped,
4. files changed by lane,
5. test commands and exact results,
6. APK path/SHA256 if built,
7. slow-turn latency classification if evidence existed,
8. issue list by P0/P1/P2/P3,
9. remaining NOT_RUN QA rows,
10. whether any product decision needs master review.
```
