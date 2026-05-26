# Code Agent Project Context and Workflow v0.1

Project: `ai-child` / `ronaldowzy/ai-child`  
Audience: code implementation agents working on this repository  
Purpose: prevent local, context-poor code changes and make execution align with the product/design direction.

---

## 0. Read this before modifying code

This repository is not a generic chat app. It is a child-facing AI growth companion app with strict product, child-safety, parent-governance, and healthy-engagement constraints.

Before any non-trivial change, a code agent must read:

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/PRODUCT_AND_EXPERIENCE_ROADMAP_AFTER_TASK09_V0_1.md
docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md
docs/EXPERIENCE_REVIEW_AND_NEXT_OPTIMIZATION_GUIDE_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md
```

For prompt/report/design tasks, also read the exact task doc provided by the master session, for example:

```text
docs/CODE_AGENT_TASK_11_PROMPT_AND_REPORT_DESIGN_RESET_V0_1.md
```

---

## 1. Product identity

`ai-child` is a voice-first child AI companion app for 5-10 year-old children, currently focused on Android landscape family-beta testing in mainland China.

The AI character is `小白狐`.

The app should feel like:

```text
1. a warm child companion;
2. a safe expression partner;
3. a bridge back to parents/guardians and real life;
4. a gentle learning scaffold when needed;
5. a healthy, stoppable experience.
```

The app should **not** feel like:

```text
1. a teacher interviewing the child;
2. an adult customer-service chatbot;
3. a homework answer machine;
4. a game retention system;
5. a surveillance dashboard for parents;
6. a secret friend replacing real relationships.
```

---

## 2. Current architecture status

As of Task 11 planning, the project has these major systems:

```text
1. Android voice-first child chat.
2. Xiaobaihu animation/state panel.
3. Local ASR / MiMo ASR fallback paths.
4. MiMo VoiceClone remote audio playback; no Android system TTS auto-mixing.
5. Child-facing interaction phase state.
6. Image sharing with local preview and safe specific first response.
7. Parent-operated one-child account thin slice.
8. Persistent Android login session for family beta.
9. Parent settings and parent report tied to logged-in child account.
10. Model-driven conversation_control with program guardrails.
11. Curated topic seed system; no live web/trending lookup in child chat.
12. Parent report with topic summary and bridge fields.
13. Healthy Engagement non-content metrics.
14. Family beta QA checklist and timing logs.
```

Do not assume any of these systems are production-ready. Many are family-beta thin slices.

---

## 3. Absolute prohibitions

Do not add or reintroduce:

```text
1. points, coins, badges, streaks, rankings, leaderboards;
2. gacha, card collection, limited-time rewards;
3. pet hunger, emotional punishment, “小白狐会难过/想你了”;
4. FOMO or daily engagement pressure;
5. secret relationship language;
6. “只有我懂你” or AI-as-only-friend language;
7. child-managed social sharing;
8. raw transcript display/export without explicit separate design;
9. Android system TTS as Xiaobaihu automatic child-facing fallback;
10. live web/trending search inside child chat;
11. plaintext passwords or raw tokens in backend storage/logs;
12. logging raw child audio, raw images, full child text, full assistant replies, API keys, or parent_message_raw.
```

---

## 4. Design ownership rule

For product/design-sensitive areas, the code agent must not invent the design.

Design-sensitive areas include:

```text
1. global Xiaobaihu persona;
2. child conversation prompts;
3. opening greeting strategy;
4. conversation_control semantics;
5. parent report prompt and wording;
6. child-facing UI copy;
7. parent-facing UI copy;
8. safety/healthy-engagement rules;
9. learning help behavior;
10. image sharing response style.
```

If the task document gives exact prompt/copy, use it exactly. Do not paraphrase, compress, or “improve” it unless asked.

If the task document is unclear, stop and ask for clarification rather than inventing new product behavior.

---

## 5. Engineering execution rule

A code agent should usually do the smallest change that satisfies the current task.

Before coding, identify:

```text
1. allowed files;
2. forbidden files;
3. tests required;
4. expected behavior examples;
5. product decisions affected;
6. real-device QA items that remain NOT_RUN.
```

Do not perform broad refactors in the same commit as prompt/copy work.

Do not modify account/auth/TTS/ASR/image/upload/navigation unless the task explicitly allows it.

---

## 6. Parent/guardian terminology

The product term is now `家长`, not `父亲`, for user-facing UI and docs.

Preferred terms:

```text
家长设置
家长日报
家长寄语
家长入口 / 大人入口
今晚可以这样聊
今天聊了什么
家长可以怎么做
今晚尽量别这样问
```

Technical class names like `ParentReport` can remain if renaming would be risky. Do not do destructive API/DTO renames unless explicitly instructed.

---

## 7. Child account model

Current MVP direction:

```text
1. one child account represents one child app space;
2. parent/guardian creates and manages the account;
3. child does not manage credentials;
4. app remains logged in unless parent logs out or session expires;
5. parent settings/report use logged-in account context;
6. dev fallback may still support explicit child_id for local testing.
```

This is a family-beta thin slice, not production compliance completion.

Do not add multi-child, multi-guardian, family organization, password reset, SMS, email verification, OAuth, or payment unless a future task explicitly requests it.

---

## 8. Prompt and report reset task rule

For Task 11, the code agent must follow:

```text
docs/CODE_AGENT_TASK_11_PROMPT_AND_REPORT_DESIGN_RESET_V0_1.md
```

Task 11 is intentionally narrow:

```text
1. replace prompt files with exact supplied text;
2. replace parent report system prompt with exact supplied text;
3. change parent report section titles;
4. improve parent report payload with short_content_hint;
5. add tests;
6. avoid account/auth/TTS/ASR/image/navigation changes.
```

The code agent must report whether exact prompt text was used.

---

## 9. Testing expectations

For each task, report exact commands and results. Do not say “tests pass” without commands.

Common commands:

```bash
cd backend && pytest
cd backend && ruff check .
cd android && ./gradlew test
cd android && ./gradlew assembleDebug
```

If full tests are too slow, run targeted tests and say what was skipped and why.

Never claim real-device QA passed unless a real device was actually tested.

---

## 10. Final response format for code agents

Every implementation report should include:

```text
1. commit sha;
2. task doc used;
3. files changed;
4. files intentionally not touched;
5. tests run and exact results;
6. whether any prohibited area was touched;
7. whether product decisions changed;
8. remaining QA items;
9. any deviations from task instructions.
```

For prompt/report tasks, additionally include:

```text
1. whether exact prompt text was used;
2. UI copy before/after;
3. sample expected report output;
4. sample expected child reply behavior.
```

---

## 11. If you are uncertain

If uncertain, do not improvise.

Ask the master session for clarification when:

```text
1. a prompt or UI copy seems contradictory;
2. a task requires changing forbidden files;
3. a test failure suggests broad architecture change;
4. product behavior is not specified;
5. a change might affect child safety, parent trust, or data privacy.
```

The safest useful code agent is not the one that changes the most code. It is the one that changes the right small amount and preserves the product direction.
