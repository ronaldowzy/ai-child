# Codex Task 10: Task 09 Closeout, Account/Opening/Control QA v0.1

Project: `ai-child` / `ronaldowzy/ai-child`  
Target branch: `main`  
Task type: closeout + device QA package + narrow hardening after Task 09  
Recommended mode: four lanes on separate branches/worktrees; if only one Codex session is available, execute A -> B -> C -> D.

---

## 0. Why this task

Task 09 landed the correct next architecture foundation:

```text
1. parent-operated one-child account registration/login;
2. persistent Android login token for family-beta;
3. authenticated child_id overriding dev child_id;
4. user-facing copy moved from 父亲 to 家长;
5. model-driven conversation_control parser/guardrails;
6. personalized opening v2 with model generation and late-opening suppression;
7. backend-generated topic choices based on profile interests + curated seeds.
```

Master review accepts Task 09 direction, but it is a large architecture change and needs closeout before the next real device QA.

Known closeout concerns:

```text
1. Opening v2 is Android-non-blocking, but backend `create_opening()` still waits for model opening and TTS audio generation before returning. This may still feel slow if the child waits for Xiaobaihu to speak.
2. Auth endpoints are optional on many existing APIs for dev compatibility. This is acceptable for dev fallback, but the default logged-in Android path must be verified end-to-end.
3. Android stores the family-beta token in SharedPreferences. This is acceptable for v0.1 family-beta but must be documented as not production security hardening.
4. QuickActionService now uses backend topic choices, but still has some old keyword fallback actions. These must not override account/profile-based suggestions when model control indicates soft_shift.
5. Model-driven conversation_control has unit tests, but needs synthetic real-provider trace and device QA before it can be considered natural.
```

Do not add broad new features in this task. Prepare a stable Task 09 QA build and fix only narrow closeout gaps.

---

## 1. Shared required reading

```text
docs/CODEX_TASK_09_CHILD_ACCOUNT_AND_MODEL_DRIVEN_PERSONALIZATION_V0_1.md
docs/PRODUCT_AND_EXPERIENCE_ROADMAP_AFTER_TASK09_V0_1.md
docs/PRODUCT_DECISIONS_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
backend/README.md
android/README.md
```

---

## 2. Coordination model

Suggested branches:

```text
codex/task10-a-auth-account-qa-closeout
codex/task10-b-opening-v2-latency-closeout
codex/task10-c-conversation-control-topic-choice-trace
codex/task10-d-device-qa-package-docs
```

Suggested merge order:

```text
1. Lane A first: auth/session stability affects all QA.
2. Lane B second: opening latency is a key device observation.
3. Lane C third: model control/topic choices can use account/profile context.
4. Lane D last: QA docs/APK package should reflect final Task 10 state.
```

---

# Lane A — Auth/account closeout and regression tests

## A1. Goal

Verify and harden the one-child account thin slice without expanding scope into production auth.

## A2. Requirements

Backend:

```text
1. Confirm password hashes and token hashes are never logged or returned except raw token only in login/register response.
2. Confirm session expiration and revoked sessions return 401.
3. Confirm authenticated account child_id overrides any client-supplied dev child_id for conversation, stream, opening, parent policy, parent report, and attachment upload paths.
4. Keep unauthenticated explicit child_id only as local/dev compatibility where already intended; document it.
5. Ensure migration creates child_accounts/auth_sessions and DB smoke covers it.
```

Android:

```text
1. Login/register persists session and relaunch stays logged in.
2. Logout clears token and returns to login screen.
3. Invalid/expired token clears session after `/auth/me` failure.
4. Parent settings/report default route uses logged-in account, no PIN in logged-in path.
5. Child does not see token/debug credentials.
```

## A3. Allowed files

```text
backend/app/api/v1/auth.py
backend/app/api/v1/conversation*.py
backend/app/api/v1/parent_*.py
backend/app/api/v1/attachments*.py
backend/app/services/auth_service.py
backend/app/repositories/auth_repository.py
backend/app/tests/**/*auth*
backend/app/tests/**/*conversation*
backend/app/tests/**/*attachment*
backend/app/tests/**/*parent_policy*
backend/app/tests/**/*parent_report*
android/app/src/main/java/com/childai/companion/data/auth/*
android/app/src/main/java/com/childai/companion/ui/auth/*
android/app/src/main/java/com/childai/companion/ui/AppNavHost.kt
android/app/src/test/java/com/childai/companion/**/*Auth*
android/app/src/test/java/com/childai/companion/ui/parent/*
```

Docs:

```text
backend/README.md
android/README.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## A4. Do not do

```text
1. Do not add SMS/email/OAuth/password reset.
2. Do not add family/multi-child/multi-guardian org.
3. Do not claim production auth compliance.
4. Do not store plaintext password or raw token in backend DB/logs.
```

## A5. Acceptance criteria

```text
1. Auth tests cover register/login/me/logout/expired or revoked session.
2. Authenticated child_id override is tested for all high-impact routes.
3. Android auth state tests cover saved session, logout, invalid refresh.
4. Docs clearly mark SharedPreferences token as family-beta thin slice, not production security hardening.
```

---

# Lane B — Opening v2 latency closeout

## B1. Goal

Make opening v2 feel non-blocking in practice, not only in Android UI state.

Task 09 already suppresses late opening if the child starts interacting. Task 10 should reduce perceived first-opening delay and make timing diagnosable.

## B2. Requirements

Backend:

```text
1. Add timing logs for opening: model_ms, tts_ms, total_ms, audio_url_present, fallback_used.
2. Do not log parent_message_raw, full child history, or full opening text.
3. If TTS generation is slow/fails, return text without blocking longer than a short soft timeout if feasible.
4. Keep deterministic fallback.
5. Add tests for provider failure and TTS timeout/failure.
```

Android:

```text
1. Ready state remains available immediately after chat screen appears.
2. If opening response arrives after child interaction started, it is suppressed and no audio plays.
3. If opening text arrives without audio, text may show but no system TTS fallback is used.
4. Collect timing evidence for first opening request in QA docs.
```

Implementation options:

```text
Preferred thin slice: backend opening TTS soft timeout, returning text if audio is unavailable.
Future option only: async opening audio pre-generation/cache. Do not build a complex job system now.
```

## B3. Allowed files

```text
backend/app/services/opening_service.py
backend/app/api/v1/conversation_opening.py
backend/app/tests/**/*opening*
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/test/java/com/childai/companion/ui/chat/*Opening*
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
```

## B4. Do not do

```text
1. Do not block child input while opening audio is generated.
2. Do not reintroduce system TTS fallback.
3. Do not create a broad background job system.
4. Do not store raw conversation history just for opening.
```

## B5. Acceptance criteria

```text
1. Opening timing logs exist and are non-sensitive.
2. TTS failure/timeout does not prevent text opening from returning.
3. Android test proves late opening is suppressed after child starts speaking/sending.
4. QA checklist explains how to capture a slow opening trace.
```

---

# Lane C — Model control and topic choices trace hardening

## C1. Goal

Validate model-driven conversation_control and interest-aware topic suggestions beyond unit tests.

## C2. Requirements

```text
1. Extend synthetic trace runner with model-control cases:
   - CS/game short answers -> soft_shift;
   - high-detail child continuation -> continue;
   - explicit no-chat/bedtime -> program guardrail;
   - profile interests -> topic choices prefer interests;
   - topic boundaries -> filtered choices.
2. Ensure final_control and model_control are recorded in non-content metrics/debug without raw child text in logs.
3. Confirm QuickActionService does not let old keyword fallbacks override model soft_shift or profile-interest topic choices.
4. If old keyword fallbacks are still needed, clearly order them after model/profile choices and document as fallback only.
```

## C3. Allowed files

```text
backend/app/services/child_agent_runtime.py
backend/app/services/quick_action_service.py
backend/app/services/topic_seed_service.py
backend/app/services/turn_guidance_builder.py
backend/app/tests/**/*quick_action*
backend/app/tests/**/*child_agent_runtime*
backend/app/tests/**/*topic_seed*
scripts/run_model_trace_scenarios.py
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
```

## C4. Do not do

```text
1. Do not add a second model call for conversation_control.
2. Do not add live web/trending search.
3. Do not turn topic choices into tasks, rewards, or missions.
4. Do not encourage more gameplay or purchases.
```

## C5. Acceptance criteria

```text
1. Trace runner includes control-focused scenarios.
2. Tests prove model soft_shift beats old keyword deepening.
3. Tests prove high engagement can continue.
4. Tests prove interest choices and topic boundaries work.
```

---

# Lane D — Task 09 QA package and documentation closeout

## D1. Goal

Prepare the exact device QA package after Task 09/10, and update docs so the next Redmi K60 test focuses on the right things.

## D2. Required checks

Run or document exact failures:

```bash
cd backend && pytest
cd backend && ruff check .
cd android && ./gradlew test
cd android && ./gradlew assembleDebug
```

If the project uses helper scripts, use them and report exact command.

## D3. QA checklist additions

Add or verify QA rows for:

```text
1. Register one child account.
2. Login persists after app restart.
3. Logout returns to login.
4. Invalid token returns to login.
5. 家长设置/家长日报 no longer use PIN in logged-in path.
6. Opening v2 first screen Ready immediately.
7. Opening text varies based on profile/interests/history/time.
8. Slow opening trace collection: backend request_id + opening timing + Android video timestamp.
9. CS short-answer soft_shift vs high-detail continue.
10. Topic choices come from backend/profile interests, not fixed Android menu.
```

## D4. Docs to update

```text
android/README.md
backend/README.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/NEXT_PHASE_PLAN_V0_2.md
docs/PRODUCT_AND_EXPERIENCE_ROADMAP_AFTER_TASK09_V0_1.md
```

## D5. Acceptance criteria

```text
1. APK path/SHA256/base URL recorded.
2. Tests and build status recorded honestly.
3. Real device QA remains NOT_RUN unless actually run.
4. Task 10 docs distinguish code-complete from device-validated.
```

---

## 3. Final Codex response requirements

Codex must report:

```text
1. commit sha(s),
2. lanes completed,
3. files changed by lane,
4. test commands and exact results,
5. auth/session closeout summary,
6. opening latency closeout summary,
7. model-control/topic-choice trace examples,
8. APK path/SHA256/base URL if built,
9. remaining Redmi K60 / Honor Pad 5 QA items,
10. any product decisions changed.
```
