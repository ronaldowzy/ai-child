# CODE_AGENT_TASK_20_TOPIC_BOUNDARY_AND_QUICK_ACTION_V2_CLOSEOUT_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: product runtime hardening after Task 19  
Goal: convert the personalized session loop tests into better runtime behavior by fixing boundary semantics and quick action/menu fallback.

---

## 0. Why this task

Task 19 added a synthetic personalized child session loop test. It is useful as a guardrail, but it also exposed two product issues:

```text
1. Topic boundary semantics are too coarse.
   Example: parent boundary “不要追问比赛输赢” currently filters out “跑步比赛” entirely because both share the marker “比赛”.
   Product intent should be: Xiaobaihu may still talk about比赛准备、感受、努力、画面 or轻松换题, but must not追问输赢、排名、结果、谁赢谁输.

2. QuickActionService still has old keyword fallback actions such as “继续说 / 讲个小故事 / 今天不聊了”.
   These sometimes make the UI feel like a fixed menu rather than profile-aware, child-led suggestions.
```

Task 20 is a narrow runtime hardening task. It must not add new major features.

---

## 1. Required reading

```text
docs/CODE_AGENT_TASK_19_PERSONALIZED_CHILD_SESSION_LOOP_CLOSEOUT_V0_1.md
docs/CODE_AGENT_TASK_15_CHILD_PROFILE_UNIFICATION_AND_PROMPT_CONTEXT_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
backend/app/tests/test_personalized_session_loop.py
backend/app/services/topic_seed_service.py
backend/app/services/quick_action_service.py
```

---

## 2. Required product behavior

### 2.1 Boundary semantics v2

A parent-set boundary is not always a hard topic ban.

Support at least these internal boundary categories:

```text
avoid_topic: do not suggest this topic at all.
avoid_followup: the topic can be mentioned, but do not追问/深挖 the specified angle.
avoid_framing: avoid a frame such as输赢/排名/比较/表现好坏.
unknown: safe fallback; avoid offering it if uncertain.
```

Heuristic v0.1 is acceptable:

```text
If boundary contains “不要追问/少追问/别问/不要问” => avoid_followup.
If boundary contains “输赢/赢/输/排名/第几/成绩/分数/表现” => avoid_framing.
If boundary contains “不要聊/不想聊/别聊/不聊” => avoid_topic.
Otherwise unknown.
```

For example:

```text
Boundary: 不要追问比赛输赢
Interest: 跑步比赛
Allowed topic choice: 聊跑步比赛前的感觉 / 聊跑步比赛里的准备
Disallowed labels: 聊比赛输赢 / 问问谁赢了 / 排名怎么样
```

### 2.2 Topic choices should be boundary-aware, not over-filtered

Topic choices should:

```text
1. Keep safe interests when boundary is avoid_followup/avoid_framing.
2. Rewrite labels to avoid the forbidden angle.
3. Filter hard only for avoid_topic.
4. Still respect offer_two_choices limit.
5. Never derive topics from gender.
6. Keep labels short and child-friendly.
```

### 2.3 Quick action v2: remove old fixed menu feel

`QuickActionService` should prefer:

```text
1. model conversation_control suggested moves if safe;
2. profile-aware topic choices;
3. show-and-tell action when child intent is image/object sharing;
4. a minimal stop/continue choice only when no better context exists.
```

Reduce or remove keyword fallback branches that return generic fixed menus:

```text
继续说 / 换个话题 / 今天不聊了
继续说 / 讲个小故事 / 今天不聊了
```

If such labels remain, they should be last-resort and not appear when profile interests or model control exist.

### 2.4 Support style preferences

If profile has:

```text
offer_two_choices
```

then max visible quick actions should be 2 unless a hard scene requires fixed actions.

If profile has:

```text
ask_fewer_questions
```

then quick action labels should avoid question wording and should not all be questions.

If profile has:

```text
use_shorter_sentences
```

then quick action labels should stay concise.

---

## 3. Allowed files

```text
backend/app/services/topic_seed_service.py
backend/app/services/quick_action_service.py
backend/app/tests/test_topic_seed_service.py
backend/app/tests/test_quick_action_service.py
backend/app/tests/test_personalized_session_loop.py
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

Avoid changing Prompt files in this task.

Do not modify:

```text
auth/account schema
parent settings UI
TTS/ASR
image upload transport
Android navigation
mascot animation
DB migrations
parent report prompt
```

---

## 4. Specific tests to add/update

### 4.1 Boundary nuance

Add tests:

```text
Boundary: 不要追问比赛输赢
Interests: 跑步比赛, 画画
Expected: topic labels may include a safe比赛-related label, but must not include输赢/排名/谁赢/结果.
```

### 4.2 Hard topic ban

```text
Boundary: 不要聊游戏
Interests: 游戏, 画画
Expected: no 游戏-related topic label.
```

### 4.3 Quick action profile priority

```text
Given profile interests and soft_shift control,
Expected: profile-aware labels appear; old fixed menu does not override them.
```

### 4.4 Show-and-tell action

```text
Child text: 你看这个/拍给你看/我画了一个...
Expected: share_photo appears, plus at most one safe follow-up action.
```

### 4.5 Personalized session loop trace update

Update Task 19 scenario expectation:

```text
For boundary “不要追问比赛输赢”, do not require 跑步比赛 to be fully filtered.
Instead require that any比赛 label avoids输赢/排名/结果 framing.
```

---

## 5. Test commands

Run:

```bash
cd backend && pytest backend/app/tests/test_topic_seed_service.py backend/app/tests/test_quick_action_service.py backend/app/tests/test_personalized_session_loop.py
cd backend && ruff check .
```

If relevant Android tests are unaffected, say so.

---

## 6. Final response required

Report:

```text
1. commit sha;
2. files changed;
3. boundary semantics implemented;
4. examples:
   - 不要追问比赛输赢 + 跑步比赛 -> safe label;
   - 不要聊游戏 + 游戏 -> filtered;
5. quick action before/after examples;
6. tests run and exact results;
7. confirmation no auth/TTS/ASR/navigation/prompt/parent report prompt changes were made.
```
