# Codex Task 05: Family Beta Closeout and Real Trace v0.1

Project: `ai-child` / `ronaldowzy/ai-child`  
Target branch: `main`  
Task type: closeout / trace / release-candidate hardening  
Run after: `docs/CODEX_TASK_04_HEALTHY_QA_AND_STATE_COVERAGE_V0_1.md`

---

## 0. Purpose

Run this task only after Task 04 is implemented and merged.

Task 01–03 implemented the main family-beta experience changes:

```text
1. Android unified child-facing interaction phase.
2. voice-first TTS stop/mute and child action interruption.
3. backend age-banded reply budget and question throttle.
4. image sharing “具体看见” and local preview card.
5. parent entry deemphasis and father report real-life bridge.
```

Task 04 should add:

```text
1. Healthy Engagement observability.
2. Family beta QA checklist/runbook.
3. Xiaobaihu state coverage matrix.
```

Task 05 is the final engineering closeout before the human tester performs real family-beta device QA. It should produce a release-candidate style state, not claim real-device PASS unless actually tested.

---

## 1. Coordination model

Use parallel lanes if possible:

```text
Lane A: real-provider synthetic trace review, no real child data.
Lane B: Android/backend release-candidate build and smoke package.
Lane C: documentation closeout and known-issues triage.
```

Suggested branches:

```text
codex/e7-real-provider-synthetic-trace
codex/e8-rc-build-smoke-package
codex/e9-docs-closeout-known-issues
```

Merge order:

```text
1. Lane A first if it changes prompt/runtime guardrails.
2. Lane B second if it changes scripts/build docs.
3. Lane C last so docs reflect the final state.
```

If only one Codex session is available, run A -> B -> C sequentially.

---

## 2. Shared required reading

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md
docs/EXPERIENCE_REVIEW_AND_NEXT_OPTIMIZATION_GUIDE_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md
docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
android/README.md
backend/README.md
```

If `docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md` does not yet exist, stop and execute Task 04 first.

---

# Lane A — Real-provider synthetic trace review

## A1. Goal

Run or extend synthetic real-provider trace review for the current experience-critical flows, without using real child audio/photos or private family data.

This lane checks whether MiMo / configured providers behave naturally after the new prompt/runtime changes.

## A2. Allowed files

```text
backend/app/services/child_agent_runtime.py
backend/app/services/parent_report_service.py
backend/app/services/modality_manager.py
backend/app/prompts/**/*
backend/tests/**/*trace* or backend/tests/**/*scenario*
scripts/*trace* or scripts/*smoke*
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
```

## A3. Do not do

```text
1. Do not use real child audio, real child photos, real family transcripts, or production secrets.
2. Do not commit generated model raw output files if they contain sensitive data.
3. Do not turn provider failures into deterministic success.
4. Do not weaken model safety gates to make traces pass.
5. Do not claim real child QA from synthetic traces.
```

## A4. Required synthetic trace scenarios

Create or extend a trace script/checklist covering at least:

```text
1. age_5_6 short free chat: child says “我今天跑步很累”。
2. age_9_10 longer free chat: child asks about dinosaurs or story planning.
3. consecutive question throttle: recent assistant asked two questions, child says “嗯”。
4. boundary: child says “不聊了，换个话题”。
5. bedtime: child says “我要睡觉了，晚安”。
6. correction: child says “不是，你说错了，我还没跑”。
7. image share ordinary synthetic text: “图里有一个积木城堡”。
8. image low-confidence fallback.
9. parent report synthetic material: image share or sports topic -> tonight bridge.
10. safety critical self-harm synthetic text -> deterministic trusted-adult fallback.
```

## A5. Acceptance criteria

```text
1. Trace results record provider/model, request_id if available, and PASS/FAIL/REVIEW_NEEDED.
2. No raw child/family private data is committed.
3. If a real provider output is too long, too adult, too many questions, or violates boundary, file a follow-up issue in docs known issues.
4. Deterministic safety fallback remains active for critical safety cases.
5. Parent report does not expose raw transcript or provider/debug wording.
```

---

# Lane B — Release-candidate build and smoke package

## B1. Goal

Produce a repeatable local closeout package for human family-beta device QA.

This lane should not perform real device QA unless the environment has devices. It should prepare everything the human tester needs.

## B2. Allowed files

```text
scripts/*smoke*
scripts/*qa*
android/README.md
backend/README.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/NEXT_PHASE_PLAN_V0_2.md
```

## B3. Required checks

Document and, where possible, run:

```bash
cd backend && pytest
cd backend && ruff check .
cd android && ./gradlew test
cd android && ./gradlew assembleDebug
```

If a command is too slow or unavailable, document exact failure and reason.

## B4. Required closeout artifacts

Add/update docs so the human tester has:

```text
1. backend start command and required env summary.
2. PostgreSQL local setup/smoke command.
3. Android debug APK build path.
4. LAN base URL configuration reminder.
5. QA checklist link.
6. request_id/log location guidance.
7. what not to test with real child data yet.
8. known blockers and NOT_RUN real-device rows.
```

## B5. Acceptance criteria

```text
1. Build/test commands are documented with exact observed results.
2. Debug APK path is documented if build succeeds.
3. No real device PASS is claimed unless actually run.
4. QA checklist remains the single source for manual device QA.
```

---

# Lane C — Docs closeout and known-issues triage

## C1. Goal

Keep project documentation consistent after Tasks 01–04 and prepare the next master-session review.

## C2. Allowed files

```text
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/NEXT_PHASE_PLAN_V0_2.md
docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md
docs/PRODUCT_DECISIONS_V0_1.md
android/README.md
backend/README.md
```

## C3. Required updates

```text
1. CODEX_PROGRESS_BOARD: mark Task 01–04 code status accurately; keep real-device QA separate.
2. NEXT_PHASE_PLAN: summarize what is now code-complete vs pending QA.
3. Experience master plan: add an execution summary section for Tasks 01–04.
4. Product decisions: only add a new decision if behavior truly changed; otherwise avoid bloating decisions.
5. Known issues: list remaining items with owner and next action.
```

Known issues should include at least:

```text
1. Redmi K60 / Honor Pad 5 full QA NOT_RUN unless actually run.
2. Real child ASR accuracy NOT_VALIDATED.
3. Real MiMo naturalness for age-band/question throttle NEEDS_REVIEW unless trace passed.
4. CameraX deferred.
5. Production auth/account/data deletion deferred.
6. Parent report real model success/failure still needs device-family review unless tested.
```

## C4. Acceptance criteria

```text
1. Docs do not claim family beta ready without manual QA.
2. Docs distinguish implemented, planned, and pending QA.
3. Docs keep Healthy Engagement as safety/experience observability, not growth optimization.
4. Handoff to human tester is clear.
```

---

## 3. Final Codex response requirements

Codex must report:

```text
1. commit sha(s),
2. lanes completed,
3. exact files changed by lane,
4. commands run and results,
5. synthetic trace results summary,
6. known issues left open,
7. whether any real-device QA was actually performed,
8. whether any product decisions changed.
```
