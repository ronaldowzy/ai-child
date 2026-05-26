# CODE_AGENT_TASK_21_OPENING_AND_PARENT_REPORT_VISIBLE_QUALITY_V2

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: visible product quality improvement  
Goal: make the most visible surfaces feel meaningfully better: opening greeting and parent report.

---

## 0. Why this task

Tasks 15-20 created important foundations:

```text
1. unified child profile;
2. relationship memory;
3. conversation arc;
4. show-and-tell memory;
5. visual state resolver;
6. boundary semantics v2;
7. profile-aware quick actions.
```

Now we must convert those foundations into user-visible improvement.

The product owner has repeatedly observed two high-impact issues:

```text
1. Opening still feels repetitive or system-like.
2. Parent report can still feel mechanical unless it uses real session material well.
```

Task 21 focuses only on these visible surfaces.

---

## 1. Scope

Allowed:

```text
1. Opening v3 content strategy and deterministic fallback.
2. Parent report v2 deterministic fallback and model payload quality.
3. Session material helpers that summarize memory/arc/show-and-tell safely.
4. Tests and synthetic examples.
5. QA checklist updates.
```

Forbidden:

```text
1. Do not change auth/account schema.
2. Do not change parent settings UI.
3. Do not change TTS provider/fallback.
4. Do not change ASR.
5. Do not change image upload transport.
6. Do not change Android navigation.
7. Do not change mascot animation engine/assets.
8. Do not add raw transcript export.
9. Do not add gamification.
```

---

## 2. Required reading

```text
docs/CODE_AGENT_PROJECT_CONTEXT_AND_WORKFLOW_V0_1.md
docs/CODE_AGENT_TASK_11_PROMPT_AND_REPORT_DESIGN_RESET_V0_1.md
docs/CODE_AGENT_TASK_19_PERSONALIZED_CHILD_SESSION_LOOP_CLOSEOUT_V0_1.md
docs/CODE_AGENT_TASK_20_TOPIC_BOUNDARY_AND_QUICK_ACTION_V2_CLOSEOUT_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
backend/app/services/opening_service.py
backend/app/services/parent_report_service.py
backend/app/services/relationship_memory.py
backend/app/services/turn_guidance_builder.py
```

---

# Lane A — Opening v3 visible quality

## A1. Goal

Opening should feel like Xiaobaihu remembers the child lightly, without sounding like a script or exposing profile labels.

Opening must be:

```text
1. short, 1-2 sentences;
2. warm and non-intrusive;
3. varied across sessions;
4. profile-aware but not label-revealing;
5. memory-aware but not forceful;
6. respectful of boundaries;
7. safe if no history exists.
```

## A2. Opening source priority

Opening may use these signals in order:

```text
1. nickname/display name;
2. current time period, only lightly;
3. recent unfinished thread, if safe;
4. recent show-and-tell event;
5. parent-set interests;
6. support style preferences;
7. default gentle greeting.
```

Do not use:

```text
1. raw child transcript;
2. temperament labels in child-facing text;
3. gender-based stereotypes;
4. topic boundaries as topics;
5. guilt/retention language.
```

## A3. Opening templates for deterministic fallback

Implement or refine fallback templates. They do not need to be exact strings, but behavior must match.

Good examples:

```text
航航，小白狐在这里。今天可以先说一件小事，也可以拍给我看。
航航，我还记得你之前提到画画。今天想慢慢说一点，还是先换个轻松的？
航航，先不急。你想聊比赛前的感觉，还是换成画画这类轻松的？
航航，回来啦。上次你说要去英语打卡，今天不用接着说，想换个话题也可以。
```

Bad examples:

```text
因为你是说话短的孩子，所以我会少问。
家长设置了你不喜欢压力。
你是男孩，所以我们聊运动吧。
小白狐一直等你回来。
今天必须完成一个小任务。
```

## A4. Variation rule

Avoid returning the same opening template every time.

Acceptable thin slice:

```text
1. choose template by session_id/date/context hash;
2. avoid exact same fallback text for same child on same local date if cache/history available;
3. tests cover at least two context types producing different fallback openings.
```

## A5. Tests

Add/verify tests:

```text
1. profile-only opening uses nickname + interest, no labels.
2. unfinished-thread opening mentions previous thread lightly and explicitly allows not continuing.
3. boundary “不要追问比赛输赢” does not produce “谁赢了/输了没/排名”.
4. two context types produce different deterministic fallback openings.
5. no gender stereotypes.
```

---

# Lane B — Parent Report v2 visible quality

## B1. Goal

Parent report should be immediately understandable to a parent:

```text
1. today what child roughly talked about;
2. what the child seemed to be trying to express;
3. one natural way the parent can talk tonight;
4. what not to ask;
5. no internal product words;
6. no raw transcript.
```

## B2. Deterministic fallback upgrade

The deterministic report fallback must not be generic. It should use safe session material:

```text
1. conversation topics;
2. conversation_summary_hint;
3. show_and_tell memory summaries;
4. unfinished_thread summaries;
5. support_style_preferences;
6. topic_boundaries;
7. arc boundary signals such as leave_for_task.
```

Example expected fallback output:

```text
summary:
今天孩子主要聊了比赛前的紧张感、展示了一样自己画/拿给小白狐看的东西，最后说要去英语打卡，一会再聊。

tonight_parent_bridge:
晚上可以轻轻说：“你今天提到比赛前有点紧张，明天要不要只准备一件最重要的小事？”

avoid_followup:
- 不要连续追问比赛输赢或排名。
- 不要把孩子展示的图片立刻当作作业检查。
- 孩子说要去打卡时，不要再把话题拉回聊天。
```

Do not write:

```text
今晚可以接一句
桥接
结构化摘要
表达入口
孩子属于慢热/容易受挫/说话短类型
```

## B3. Model payload improvement

Ensure `_parent_report_model_payload()` gives the model enough safe material:

```text
1. topic_overview_hints;
2. conversation_summary_hint;
3. short_content_hint;
4. memory_summaries with relationship_memory_type where available;
5. support_style_preferences;
6. topic_boundaries;
7. material_policy warning against raw transcript.
```

Do not include raw transcript beyond safe short hints already sanitized. Do not add raw export.

## B4. Parent report UI assumptions

Do not change UI layout broadly. But if text labels appear in tests/docs, use:

```text
今晚可以这样聊
今天聊了什么
家长可以怎么做
今晚尽量别这样问
```

## B5. Tests

Add/verify tests:

```text
1. report fallback mentions match/competition, image/object/show-and-tell, English check-in when those materials exist.
2. report uses support_style ask_fewer_questions by recommending one small question or not追问.
3. report respects boundary “不要追问比赛输赢”.
4. report does not contain internal words: 接一句, 桥接, 结构化摘要, 表达入口.
5. report does not expose raw transcript.
6. model payload includes relationship_memory_type or equivalent safe memory type marker.
```

---

# Lane C — Synthetic visible examples

## C1. Goal

Add a few developer-readable examples that make review faster.

Preferred location:

```text
backend/app/tests/test_opening_visible_quality.py
backend/app/tests/test_parent_report_visible_quality.py
```

Each test should be easy to inspect and include expected visible behavior.

Do not rely on real model calls.

---

## 3. Allowed files

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

Avoid modifying prompt files unless a test proves they were accidentally corrupted.

---

## 4. Test commands

Run:

```bash
cd backend && pytest backend/app/tests/test_opening_visible_quality.py backend/app/tests/test_parent_report_visible_quality.py backend/app/tests/test_personalized_session_loop.py
cd backend && ruff check .
```

If files are named differently, report exact commands.

---

## 5. Final response required

Report:

```text
1. commit sha;
2. files changed;
3. opening v3 before/after examples;
4. parent report v2 fallback examples;
5. model payload improvements;
6. tests run and exact results;
7. confirmation no auth/TTS/ASR/image/nav/mascot assets changes were made.
```
