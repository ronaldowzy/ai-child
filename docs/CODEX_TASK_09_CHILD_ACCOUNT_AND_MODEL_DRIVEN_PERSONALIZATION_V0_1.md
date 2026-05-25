# Codex Task 09: Child Account and Model-driven Personalization v0.1

Project: `ai-child` / `ronaldowzy/ai-child`  
Target branch: `main`  
Task type: architecture foundation + product personalization  
Recommended mode: five lanes on separate branches/worktrees; if only one Codex session is available, execute A -> B -> C -> D -> E.

---

## 0. Why this task

Recent Redmi K60 device QA showed the main family-beta loop now works: parent settings, voice-first conversation, TTS stop/mute, image sharing, topic shift chips, and parent report can be exercised on device.

The next issues are structural:

```text
1. The app still behaves like a single test child_id demo. Personalized opening, topic suggestions, parent report ownership, and history need a stable account identity.
2. Current topic shift is partly rule-driven. It can give a switch choice, but it does not yet let the model semantically judge whether the child wants to continue, stop, or switch.
3. Topic chips are safer than before, but still feel like a static menu. They should be generated from child profile, interests, recent history, and curated safe seeds.
4. Opening greeting is slow and repetitive. It should be personalized, history-aware, and non-blocking.
5. UI/product copy should move from “父亲” to “家长”.
```

This task starts the next architecture stage while staying MVP-simple.

---

## 1. Product direction: one child account, parent-operated

For current family-beta MVP, do **not** implement full family organization / multi-child / multi-parent account complexity.

Use this simpler model:

```text
1. One child account represents one child's app space.
2. All registration, login, settings, logout, and account management are performed by the parent/guardian.
3. The child is not expected to create or manage credentials.
4. The app stays logged in after login unless the parent manually logs out or the token expires/invalidates.
5. Parent settings and parent report use the current logged-in account; PIN is deprecated for the default family-beta path.
6. Dev/test fallback can still provide a default child id for local development, but it must not be the default product path after login is implemented.
```

Future migration path can still become:

```text
family_account -> guardian_accounts -> child_accounts
```

but Task 09 should not build that future model now.

---

## 2. Shared required reading

Before coding, read:

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/PRODUCT_AND_EXPERIENCE_ROADMAP_AFTER_TASK09_V0_1.md
docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md
docs/CODEX_TASK_08_REAL_DEVICE_QA_ROUND2_AND_FIX_TRIAGE_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
backend/README.md
android/README.md
```

If the roadmap doc does not exist yet, continue with this task and note the missing doc in the final response.

---

## 3. Coordination model

Suggested branches:

```text
codex/task09-a-child-account-auth-foundation
codex/task09-b-parent-to-guardian-copy
codex/task09-c-model-driven-conversation-control
codex/task09-d-personalized-opening-v2
codex/task09-e-interest-aware-topic-suggestions
```

Suggested merge order:

```text
1. Lane A first: account identity affects settings/history/report ownership.
2. Lane B second: copy/naming should align with account and parent surface.
3. Lane C third: conversation control can use profile/history context.
4. Lane D fourth: opening v2 can use child account and profile data.
5. Lane E fifth: topic suggestions can use account/profile + model control.
```

If only one Codex session is available, execute A -> B -> C -> D -> E sequentially.

Avoid broad codebase renames unless required. Keep compatibility with existing DB/dev flows.

---

# Lane A — Child Account / Auth Foundation Thin Slice

## A1. Goal

Create a minimal, local-family-beta account system:

```text
parent-operated child account registration/login
persistent Android login session
conversation/settings/report tied to current account child_id
PIN no longer required for the default parent surface once logged in
```

This is a thin slice, not production auth compliance.

## A2. Suggested backend model

Prefer minimal tables/models such as:

```text
child_accounts
  id
  username
  password_hash
  child_nickname
  child_display_name
  child_age
  child_grade
  child_call_preference
  child_interests
  topic_boundaries
  created_by_guardian boolean default true
  created_at
  updated_at
  last_login_at

login_sessions or auth_sessions
  id
  child_account_id
  token_hash
  created_at
  expires_at
  revoked_at nullable
```

If existing `ParentPolicy` already carries profile fields, do not duplicate unnecessarily. Either:

```text
1. child_account stores auth identity and basic display/profile fields, while ParentPolicy remains preference store; or
2. child_account stores identity only and ParentPolicy stores profile/preferences.
```

Pick the least disruptive approach and document it.

Password requirements:

```text
1. never store plaintext password;
2. use a standard password hash available in project dependencies, or add a small dependency only if appropriate;
3. token stored server-side as hash, returned to Android as bearer token;
4. no production-grade reset/email/SMS required.
```

## A3. Backend API thin slice

Add endpoints similar to:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

Request/response names may vary, but must support:

```text
register: username, password, child profile basics
login: username, password
logout: current token
me: current account/profile
```

For existing APIs:

```text
1. parent settings should read/write current account's profile/policy by default;
2. parent report should use current account child_id by default;
3. child conversation should use current account child_id when Android is logged in;
4. dev fallback may still pass explicit child_id in local/debug mode.
```

Do not break existing tests that rely on a fixed dev child id; adapt with compatibility helpers.

## A4. Android thin slice

Add minimal UI flow:

```text
1. If no valid saved token: show parent-operated login/register screen.
2. Register creates one child account and logs in.
3. Login stores token securely enough for family-beta; use DataStore/SharedPreferences according to existing project patterns.
4. Relaunch keeps the user logged in.
5. Manual logout clears token and returns to login.
6. Parent settings/report no longer require PIN in the logged-in path; if a re-auth screen is needed, ask account password, not PIN.
```

Keep UI simple. Do not build password recovery, email verification, SMS, OAuth, or multi-account switcher in this task.

## A5. Allowed files

Backend:

```text
backend/app/api/**/*auth* or backend/app/routers/*auth*
backend/app/domain/schemas/*auth* or parent policy/profile schemas
backend/app/services/*auth*
backend/app/repositories/*auth*
backend/app/db/models.py
backend/app/db/migrations/* or alembic versions if used
backend/app/main.py
backend/app/tests/**/*auth*
backend/app/tests/**/*parent_policy*
backend/app/tests/**/*conversation*
```

Android:

```text
android/app/src/main/java/com/childai/companion/data/auth/*
android/app/src/main/java/com/childai/companion/ui/auth/*
android/app/src/main/java/com/childai/companion/MainActivity.kt
android/app/src/main/java/com/childai/companion/ui/parent/*
android/app/src/main/java/com/childai/companion/ui/chat/*
android/app/src/test/java/com/childai/companion/**/*Auth* or auth tests
```

Docs:

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/NEXT_PHASE_PLAN_V0_2.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
backend/README.md
android/README.md
```

## A6. Do not do

```text
1. Do not implement full production account compliance.
2. Do not implement family org, multi-child, multiple guardians, role matrix, or password reset.
3. Do not let child-facing UI ask the child to manage credentials.
4. Do not store plaintext password or raw tokens.
5. Do not expose account/token/debug details in child UI.
6. Do not add raw transcript export.
```

## A7. Acceptance criteria

```text
1. Parent can register one child account from Android.
2. Parent can log in and app remains logged in after restart unless logout is used.
3. Conversation/settings/report use the logged-in account's child_id/profile by default.
4. PIN is deprecated/removed from default parent settings/report entry; dev fallback can remain documented.
5. Password is hashed; token is not stored server-side as plaintext.
6. Tests cover register/login/logout/me and invalid credentials.
```

---

# Lane B — “父亲” to “家长” copy and parent surface rename

## B1. Goal

Update user-facing product copy from father-specific wording to guardian/parent wording.

Use:

```text
父亲日报 -> 家长日报
父亲设置 -> 家长设置
父母寄语 / 家长寄语 depending on context; prefer 家长寄语 for UI
父亲入口 -> 家长入口 / 大人入口
```

Code class names can remain temporarily for compatibility if renaming them would be risky. UI/docs/tests should reflect the new product language.

## B2. Allowed files

```text
android/app/src/main/java/com/childai/companion/ui/parent/*
android/app/src/main/java/com/childai/companion/ui/chat/*
android/app/src/test/java/com/childai/companion/ui/parent/*
backend/app/domain/parent_report.py
backend/app/services/parent_report_service.py
backend/app/tests/**/*parent_report*
docs/**/*.md
```

## B3. Do not do

```text
1. Do not do large class/package renames unless necessary.
2. Do not change API fields destructively; keep backward-compatible aliases if needed.
3. Do not make the child-facing UI more adult-governance heavy.
```

## B4. Acceptance criteria

```text
1. Child-facing and parent-facing UI no longer says “父亲日报/父亲设置”.
2. Docs use 家长 as the default product term, except historical notes if needed.
3. Tests updated for new copy.
4. API/DTO remains compatible.
```

---

# Lane C — Model-driven Conversation Control

## C1. Goal

Move ordinary topic continuation/shift from rule-primary to model semantic judgment + program guardrails.

The model should judge, in the same child_chat call, whether the child likely wants to continue the current topic, softly shift, stop, or is unclear. Program rules remain responsible for safety, privacy, bedtime, explicit boundaries, fallback, and metrics.

## C2. Output contract extension

Extend child chat structured output with a control object. Suggested shape:

```json
{
  "reply": "...",
  "conversation_control": {
    "child_engagement": "high|medium|low|unclear",
    "topic_continuity": "continue|soft_shift|stop|unclear",
    "topic_shift_intent": "likely|possible|unlikely|explicit",
    "reason": "short_answer_after_repeated_topic",
    "suggested_next_moves": [
      {"id": "continue_current", "label": "接着说这个"},
      {"id": "shift_topic", "label": "换个轻松话题"},
      {"id": "show_something", "label": "拍给小白狐看"}
    ]
  }
}
```

Exact fields can vary, but must capture:

```text
child engagement
whether to continue/shift/stop
model reason
suggested next moves
```

## C3. Runtime behavior

```text
1. If model control says soft_shift, reply should naturally offer a change without sounding like a menu.
2. If child is highly engaged, do not force topic shift just because same_topic_turn_count is high.
3. If child explicitly says 不聊了/睡觉了/换话题, program guardrail wins even if model control says continue.
4. If model control is missing/invalid, use existing TurnGuidanceBuilder fallback.
5. Store model_control and final_control in non-content metrics/debug for QA.
```

Do not add a second model call; do this in the existing child_chat call if possible.

## C4. Allowed files

```text
backend/app/prompts/output_contracts/child_chat_v0_1.txt
backend/app/services/prompt_manager.py
backend/app/services/child_agent_runtime.py
backend/app/services/turn_guidance_builder.py
backend/app/domain/agent_runtime.py
backend/app/domain/schemas/conversation.py
backend/app/tests/**/*child_agent_runtime*
backend/app/tests/**/*turn_guidance*
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## C5. Acceptance criteria

```text
1. CS/game short-answer scenario returns/uses model control soft_shift.
2. High-engagement child adding vivid details can continue current topic.
3. Explicit no-chat/bedtime/topic-change still program-overrides model control.
4. Invalid/missing control falls back to existing safe rules.
5. Metrics expose model_control vs final_control without raw child text.
```

---

# Lane D — Personalized Opening v2

## D1. Goal

Make opening greeting personalized, less repetitive, and non-blocking.

Current issue: opening is slow on first Xiaobaihu speech and often sounds like a repeated deterministic template.

## D2. Product behavior

```text
1. Android should enter Ready quickly; do not block the child from speaking while opening TTS is being generated.
2. Opening text should use account/profile context: nickname, age band, interests, topic boundaries, parent message, recent relationship memory, recent conversation summary, and local time period.
3. Opening should be short: 1-2 sentences, no long interview.
4. Opening should not repeat the same sentence pattern every session.
5. If the child starts speaking before opening arrives, late opening should be discarded or downgraded; do not insert it awkwardly after the child already started a topic.
6. TTS should be optional/non-blocking. If audio is slow/unavailable, keep text and Ready state.
7. Deterministic fallback must remain for provider failure.
```

## D3. Suggested implementation

Backend:

```text
1. OpeningService builds richer context from child account/profile + memory/history summaries.
2. Add model-generated opening v2 if safe and available, with deterministic fallback.
3. Add cache: child_id/account_id + local_date + context_hash -> opening text/audio_url metadata, if low-risk.
4. Avoid storing raw child turns solely for opening; use existing memory/history summaries.
```

Android:

```text
1. App shows Ready immediately.
2. Opening request runs async.
3. If user starts recording/sending before opening returns, suppress insertion.
4. If opening audio_url arrives late, do not auto-play over the child's active turn.
```

## D4. Allowed files

```text
backend/app/services/opening_service.py
backend/app/services/opening_policy.py
backend/app/services/prompt_manager.py
backend/app/services/parent_policy_service.py
backend/app/services/conversation_history_service.py
backend/app/services/conversation_memory_hooks.py
backend/app/tests/**/*opening*
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/test/java/com/childai/companion/ui/chat/*Opening*
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## D5. Acceptance criteria

```text
1. Opening no longer blocks Ready state.
2. Opening uses profile/interests/history context when available.
3. Same session does not repeat opening.
4. If child starts speaking first, late opening is not inserted into the active conversation.
5. Provider failure falls back to deterministic short greeting.
6. Tests cover non-blocking and late-opening suppression.
```

---

# Lane E — Interest-aware Topic Suggestions

## E1. Goal

Replace static Android fallback chips with backend-generated, child-safe, interest-aware topic choices.

## E2. Behavior

```text
1. Backend produces 0-3 topic choices using: child account/profile interests, topic boundaries, age-band curated seeds, recent conversation topic, and model conversation_control.
2. Android displays choices returned by backend quick actions/control payload; it should not hard-code fixed labels like 恐龙或太空 unless backend provided them.
3. If no profile interests exist, use curated seeds as fallback.
4. If profile interests exist, prefer them, but avoid pressure, ranking, purchases, or game-time encouragement.
5. Choices should appear only when idle/Ready, topic shift is recommended, or backend returns safe quick actions.
```

## E3. Allowed files

```text
backend/app/services/topic_seed_service.py
backend/app/services/quick_action_service.py
backend/app/services/child_agent_runtime.py
backend/app/services/prompt_manager.py
backend/app/domain/schemas/conversation.py
backend/app/tests/**/*topic* or quick_action tests
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/test/java/com/childai/companion/ui/chat/*
docs/CHILD_UI_POLISH_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## E4. Do not do

```text
1. Do not call live web/search/trending APIs in child chat.
2. Do not make chips look like tasks, rewards, streaks, or missions.
3. Do not encourage additional game playing or purchases.
4. Do not ignore topic_boundaries set by parent/guardian.
```

## E5. Acceptance criteria

```text
1. With interests “恐龙、画画、跑步”, backend topic choices prefer those interests when appropriate.
2. With no interests, backend uses curated seeds.
3. Android no longer shows hard-coded seed chips independent of backend context.
4. Topic boundaries filter choices.
5. Tests cover profile-interest priority and boundary filtering.
```

---

## 4. Cross-lane documentation updates

Final merge should update:

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/PRODUCT_AND_EXPERIENCE_ROADMAP_AFTER_TASK09_V0_1.md
docs/NEXT_PHASE_PLAN_V0_2.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
backend/README.md
android/README.md
```

Document clearly:

```text
1. account system is a local family-beta thin slice, not production compliance completion;
2. one child account is parent-operated;
3. “家长” is the product term going forward;
4. model-driven conversation control uses program guardrails;
5. opening v2 is personalized and non-blocking;
6. topic suggestions are curated/static/interest-aware, not live trend scraping.
```

---

## 5. Final Codex response requirements

Codex must report:

```text
1. commit sha(s),
2. lanes completed,
3. files changed by lane,
4. test commands and exact results,
5. child account data model and auth/session behavior,
6. parent/father wording scope changed,
7. CS/game short-answer conversation_control before/after example,
8. opening v2 before/after example,
9. interest-aware topic suggestion examples,
10. remaining Redmi K60 / Honor Pad 5 QA items,
11. product decisions changed.
```
