# MASTER_SESSION_HANDOFF_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Purpose: hand off the current master planning/review session to a new ChatGPT session without losing product context, design direction, or coordination rules.

---

## 0. Current situation

The current ChatGPT page has become slow due to long context. Future master work should continue in a new ChatGPT session.

This document is the handoff anchor. The new master session should first sync GitHub `main`, then read this file and the referenced task/design docs.

Current repository baseline when this file is created:

```text
Latest known main includes Task 20 runtime hardening and Task 21 task doc.
Task 21 has been sent to the development agent and is in progress.
Task 21 implementation has not yet been reviewed by the master session at the time of this handoff.
```

---

## 1. Product identity

`ai-child` is a voice-first child AI growth companion app for 5-10 year-old children, Android landscape first, initially for mainland China family-beta testing.

The companion character is `小白狐`.

The product should feel like:

```text
1. a warm child companion;
2. a safe expression partner;
3. a bridge back to parents/guardians and real life;
4. a gentle learning scaffold when needed;
5. a healthy, stoppable experience.
```

It must not become:

```text
1. a teacher interviewing the child every turn;
2. an adult customer-service chatbot;
3. a homework answer machine;
4. a game retention system;
5. a surveillance dashboard for parents;
6. a secret friend replacing real relationships.
```

Forbidden product mechanisms:

```text
points, coins, badges, streaks, rankings, leaderboards,
gacha/cards, limited-time rewards, pet hunger, FOMO,
“Xiaobaihu misses you” emotional hooks,
“only Xiaobaihu understands you” secret-dependency language,
raw transcript display/export without separate design.
```

---

## 2. Current work mode

The master ChatGPT session is responsible for:

```text
1. product direction;
2. child psychology / education / healthy engagement design;
3. prompt and parent-report design;
4. task documents for code agents;
5. GitHub main synchronization and code review;
6. deciding next tasks;
7. preventing scope drift.
```

Code agents are responsible for:

```text
1. implementing the exact task documents;
2. small scoped code changes;
3. tests;
4. reporting commit sha, files changed, test results, and deviations.
```

For design-sensitive areas, code agents must not invent design. They must follow master-provided wording and behavior.

Design-sensitive areas include:

```text
Xiaobaihu persona,
child conversation prompts,
opening strategy,
parent report prompt and wording,
child-facing / parent-facing UI copy,
healthy engagement rules,
learning help behavior,
image/show-and-tell response style,
mascot visual state usage.
```

---

## 3. Essential docs for new master session

Read first:

```text
docs/MASTER_SESSION_HANDOFF_V0_1.md
docs/CODE_AGENT_PROJECT_CONTEXT_AND_WORKFLOW_V0_1.md
docs/PRODUCT_AND_EXPERIENCE_ROADMAP_AFTER_TASK09_V0_1.md
docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md
docs/EXPERIENCE_REVIEW_AND_NEXT_OPTIMIZATION_GUIDE_V0_1.md
docs/PRODUCT_DECISIONS_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
```

Core design docs:

```text
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md
docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md
docs/XIAOBAIHU_STATE_AND_ANIMATION_AUDIT_V0_1.md
```

Recent task docs:

```text
docs/CODE_AGENT_TASK_11_PROMPT_AND_REPORT_DESIGN_RESET_V0_1.md
docs/CODE_AGENT_TASK_15_CHILD_PROFILE_UNIFICATION_AND_PROMPT_CONTEXT_V0_1.md
docs/CODE_AGENT_TASK_17_XIAOBAIHU_VISUAL_STATE_V2_RESOLVER_V0_1.md
docs/CODE_AGENT_TASK_18_PROFILE_CONTEXT_INTEGRATION_CLOSEOUT_V0_1.md
docs/CODE_AGENT_TASK_19_PERSONALIZED_CHILD_SESSION_LOOP_CLOSEOUT_V0_1.md
docs/CODE_AGENT_TASK_20_TOPIC_BOUNDARY_AND_QUICK_ACTION_V2_CLOSEOUT_V0_1.md
docs/CODE_AGENT_TASK_21_OPENING_AND_PARENT_REPORT_VISIBLE_QUALITY_V2.md
```

---

## 4. Recent completed tasks and conclusions

### Task 11 — Prompt and parent report design reset

Purpose: stop letting code agents “optimize prompt” freely. Master session supplied exact prompt/report wording.

Result:

```text
1. Xiaobaihu role shifted from AI growth coach to warm child companion.
2. Conversation prompt emphasizes short replies, fewer questions, respect for stop/change-topic/sleep.
3. Parent report prompt was rewritten to avoid internal words such as 接一句, 桥接, 结构化摘要, 表达入口.
4. Parent report UI titles changed to 家长-readable wording.
```

Important rule: future prompt/report changes should be designed by master session, not improvised by code agent.

### Task 12 — Authorized local TTS experiment containment

Background: sherpa-onnx local TTS was authorized separately by product owner. It must not be rolled back, but must remain experimental/config-gated.

Current stance:

```text
1. MiMo VoiceClone remains primary/default voice path.
2. sherpa-onnx local TTS is family-beta experimental.
3. local fallback must be explicitly enabled.
4. Android system TTS must not be reintroduced as automatic Xiaobaihu fallback.
```

### Task 14 — Product advancement batch

Added first-layer material for:

```text
relationship memory,
conversation arc,
show-and-tell memory,
child companion surface UI thin slice,
synthetic scenario harness.
```

Conclusion: useful foundation, still rule/heuristic-heavy.

### Task 15 — Child profile unification

Implemented canonical child profile:

```text
child_age,
child_grade,
child_gender,
child_call_preference,
child_interests,
topic_boundaries,
child_temperament,
support_style_preferences,
learning_support_preferences.
```

Key rules:

```text
1. registration and parent settings must share one child profile model;
2. gender is only for respectful address/call preference;
3. gender must never infer interest, ability, personality, or behavior;
4. temperament/support fields are internal style guidance, not child-facing labels.
```

### Task 16 — Xiaobaihu state and animation audit

Design audit conclusion:

```text
Manifest declares 11 states.
Android MascotState covers 11 states.
Clearly triggered today: idle, listening, thinking, speaking, network_error, safety_concern.
privacy_boundary and homework_focus depend on backend signals.
calm, sleepy, jumping_happy are resource-ready but not product-complete.
```

Key design rule:

```text
jumping_happy must not be wired to rewards, streaks, correct answers, check-ins, or retention.
sleepy is only for bedtime/low-stimulation close, not continuing engagement.
privacy/safety states must be calm and not scary.
```

### Task 17 — Xiaobaihu visual state v2 resolver

Implemented Android visual state resolver with:

```text
base attention state,
emotional overlay,
boundary/safety overlay,
MascotState,
minHoldMs metadata,
reason.
```

Business trigger tests added. Runtime min-hold enforcement is not yet implemented; minHoldMs currently exists as resolver metadata.

### Task 18 — Profile context integration

Integrated child profile into:

```text
opening,
topic suggestions,
relationship memory,
parent report context.
```

Conclusion: direction correct. Profile labels must remain internal and not be spoken to child or written judgmentally to parent.

### Task 19 — Personalized child session loop test

Added synthetic integration test for:

```text
profile -> opening -> conversation -> short answers -> show-and-tell -> handoff -> memory -> parent report -> visual state trace.
```

Conclusion: good regression guard, but initially exposed over-coarse boundary filtering.

### Task 20 — Boundary semantics and quick action v2

Implemented runtime fixes:

```text
Boundary categories:
- avoid_topic
- avoid_followup
- avoid_framing
- unknown

Example:
“不要追问比赛输赢” no longer filters out “跑步比赛” entirely.
Allowed: discussing preparation/feelings.
Forbidden: 输赢, 谁赢谁输, 排名, 结果 framing.
```

Quick actions now prioritize:

```text
1. stop control;
2. model conversation_control moves;
3. show-and-tell;
4. profile-aware topic choices;
5. curated seeds;
6. minimal fallback only as last resort.
```

Old keyword menu branches such as “继续说 / 讲个小故事 / 今天不聊了” were reduced.

---

## 5. Current in-progress task

### Task 21 — Opening and parent report visible quality v2

Doc:

```text
docs/CODE_AGENT_TASK_21_OPENING_AND_PARENT_REPORT_VISIBLE_QUALITY_V2.md
```

Status at handoff:

```text
Sent to development agent; implementation in progress; not yet reviewed by master session.
```

Goal:

```text
Make visible product quality better, especially opening greeting and parent report.
```

Task 21 allowed files:

```text
backend/app/services/opening_service.py
backend/app/services/parent_report_service.py
backend/app/services/relationship_memory.py
backend/app/tests/test_opening_visible_quality.py
backend/app/tests/test_parent_report_visible_quality.py
backend/app/tests/test_personalized_session_loop.py
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

Forbidden in Task 21:

```text
auth/account schema,
parent settings UI,
TTS/ASR,
image upload transport,
Android navigation,
mascot animation engine/assets,
raw transcript export,
gamification,
prompt files unless proven corrupted.
```

When development agent reports completion, new master session should:

```text
1. compare main against commit that created Task 21 doc;
2. verify file scope;
3. inspect opening_service.py and parent_report_service.py;
4. inspect new visible-quality tests;
5. check no forbidden areas changed;
6. decide whether Task 21 passes or needs correction.
```

---

## 6. Known next tasks after Task 21

Likely next tasks:

### Task 22 — Xiaobaihu runtime visual transition throttle

Purpose:

```text
Move Task 17 minHoldMs from metadata to actual runtime display behavior where safe.
Prevent flicker between listening/thinking/speaking/network_error/safety states.
Keep safety/privacy states stable and calm.
Do not add new assets.
```

### Task 23 — Show-and-tell v3 visible quality

Purpose:

```text
Make “拍给小白狐看” feel more natural for child-created drawings, toys, objects, schoolwork when intended, and unclear images.
Improve specific but safe first responses.
Improve parent report summary for show-and-tell without raw image/text.
```

### Task 24 — Family-beta QA package

Purpose:

```text
After Tasks 21-23, build APK and run device QA.
Do not make every small task depend on nightly APK testing.
Use testing as batch validation.
```

---

## 7. Important product decisions to preserve

```text
1. One child account, parent-operated. No multi-child/multi-guardian production system yet.
2. App remains logged in unless parent logs out/session invalid.
3. 家长 is the product term, not 父亲.
4. Parent report is summary/bridge, not raw transcript.
5. Child profile fields are internal context, not labels to tell child.
6. Gender never drives stereotypes.
7. Topic boundaries can be nuanced; not every boundary is a hard topic ban.
8. Quick actions should not feel like a task menu.
9. Xiaobaihu visual states should not become reward/retention animations.
10. TTS local sherpa is experimental and config-gated.
```

---

## 8. How to review future development submissions

For every completed task:

```text
1. Sync GitHub main.
2. Compare from the task-doc commit to main.
3. Check file scope first.
4. Fetch and inspect the high-risk files.
5. Check tests and commit message.
6. Decide pass / partial pass / return for correction.
7. Create the next task doc only after review.
```

Do not accept “done” based only on developer summary.

Always watch for scope drift:

```text
TTS changes inside prompt tasks,
auth changes inside UI tasks,
prompt rewrites by code agent,
raw transcript leakage,
gamification,
Android navigation churn,
new DB migrations without explicit need.
```

---

## 9. Current master priorities

Near-term priorities:

```text
1. Review Task 21 once submitted.
2. Make opening greeting visibly less repetitive/system-like.
3. Make parent report visibly understandable to a real parent.
4. Keep quick actions profile-aware and low-menu-feel.
5. Improve Xiaobaihu visual transition timing after Task 21.
6. Improve show-and-tell visible quality.
```

Avoid near-term distractions:

```text
1. large account architecture expansion;
2. production compliance buildout;
3. raw transcript export;
4. new mascot assets before state runtime is stable;
5. new TTS provider changes before current MiMo/sherpa paths are device-tested;
6. new game-like retention systems.
```

---

## 10. Recommended new ChatGPT session startup prompt

Use this prompt in the next master session:

```text
我正在开发儿童 AI 成长陪伴 App `ai-child`，GitHub 仓库是 `ronaldowzy/ai-child`。当前旧主会话网页已经很卡顿，所以请你作为新的项目主控会话接手。

请先同步 GitHub main 最新状态，然后优先阅读：

1. docs/MASTER_SESSION_HANDOFF_V0_1.md
2. docs/CODE_AGENT_PROJECT_CONTEXT_AND_WORKFLOW_V0_1.md
3. docs/PRODUCT_AND_EXPERIENCE_ROADMAP_AFTER_TASK09_V0_1.md
4. docs/CODEX_PROGRESS_BOARD_V0_1.md
5. docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
6. docs/CODE_AGENT_TASK_21_OPENING_AND_PARENT_REPORT_VISIBLE_QUALITY_V2.md

当前开发方正在执行 Task 21。你的第一件事是在开发方提交后，同步 main，核对 Task 21 是否按范围完成：opening v3、parent report v2、visible-quality tests；确认没有改 auth/account、TTS/ASR、image upload、Android navigation、mascot assets、raw transcript export 或 gamification。

你的工作方式：
- 负责产品设计、儿童心理/教育/健康使用边界、Prompt 和家长日报设计、任务拆分、GitHub 复核。
- 不要让开发 agent 自己设计 Prompt 或产品话术。
- 每轮先核对代码事实，再安排下一步。
- 后续优先推进 Task 22 小白狐状态 runtime 防闪烁、Task 23 show-and-tell visible quality、Task 24 family-beta QA package。
```

---

## 11. If the new session is unsure

If the new session lacks context, it should not guess. It should read the handoff file and recent task docs, then inspect current code.

Minimum inspection before making a next task after Task 21:

```text
backend/app/services/opening_service.py
backend/app/services/parent_report_service.py
backend/app/tests/test_opening_visible_quality.py
backend/app/tests/test_parent_report_visible_quality.py
backend/app/tests/test_personalized_session_loop.py
```

The new session should preserve the current operating philosophy:

```text
Continuous product advancement in focused batches;
real-device QA after meaningful batches;
no endless circling around nightly test packaging;
no broad unscoped implementation.
```
