# CODE_AGENT_TASK_18_PROFILE_CONTEXT_INTEGRATION_CLOSEOUT_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: focused integration closeout after Task 15  
Goal: ensure the unified child profile actually affects opening, topic suggestions, memory, parent report, and QA traces.

---

## 0. Why this task

Task 15 created a canonical child profile and unified registration/parent settings fields.

Now ensure the profile is not only stored/rendered, but used consistently by the product:

```text
1. opening greeting should use age/interests/temperament/support style carefully;
2. topic suggestions should use interests, boundaries, support preferences;
3. relationship memory should merge parent-set profile context with conversation-derived memory;
4. parent report should know profile context but not expose labels mechanically;
5. synthetic scenario tests should prove the effect.
```

This is a closeout/integration task, not a new profile schema task.

---

## 1. Required reading

```text
docs/CODE_AGENT_TASK_15_CHILD_PROFILE_UNIFICATION_AND_PROMPT_CONTEXT_V0_1.md
docs/PRODUCT_AND_EXPERIENCE_ROADMAP_AFTER_TASK09_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
backend/app/domain/schemas/child_profile.py
```

---

## 2. Required behavior

### 2.1 Opening

Opening should use child profile, but gently:

```text
- nickname/display name for greeting;
- age for length/complexity;
- interests for optional light topic;
- topic boundaries to avoid unwanted topics;
- temperament/support style for rhythm, not labels.
```

Do not say:

```text
“你是一个慢热的孩子”
“家长说你说话短”
“因为你是男孩/女孩，所以……”
```

### 2.2 Topic suggestions

Topic suggestions should prioritize:

```text
1. explicit current child interest;
2. recent show-and-tell / unfinished thread;
3. curated seed by age;
4. never topic_boundaries;
5. never gender-derived interests.
```

If support style includes `offer_two_choices`, prefer 1-2 choices over 3.  
If support style includes `ask_fewer_questions`, avoid turning chips into question-heavy prompts.

### 2.3 Relationship memory

Relationship memory should combine:

```text
parent-set interests / boundaries / support style
+ conversation-derived interests / boundaries / unfinished threads
```

Parent-set data should be labeled as `source=parent_setting`. Conversation-derived data should remain non-raw summary.

### 2.4 Parent report

Parent report may use profile context to tailor suggestions, but must not show labels as judgments.

Good:

```text
“如果孩子平时不喜欢被连续追问，今晚可以只问一个很小的问题。”
```

Bad:

```text
“孩子性格慢热，所以……”
“孩子属于容易受挫类型。”
```

---

## 3. Allowed files

```text
backend/app/services/opening_service.py
backend/app/services/topic_seed_service.py
backend/app/services/quick_action_service.py
backend/app/services/relationship_memory.py
backend/app/services/conversation_memory_hooks.py
backend/app/services/parent_report_service.py
backend/app/tests/**/*opening*
backend/app/tests/**/*topic_seed*
backend/app/tests/**/*quick_action*
backend/app/tests/**/*memory*
backend/app/tests/**/*parent_report*
scripts/run_model_trace_scenarios.py
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

Do not modify:

```text
auth schema
parent settings UI
TTS/ASR
mascot animation
image upload transport
DB migrations
```

unless a test proves a minor integration bug.

---

## 4. Tests

Add/verify tests:

```text
1. opening uses nickname + interests but does not expose temperament labels;
2. topic choices prefer interests and filter boundaries;
3. support_style_preferences=offer_two_choices limits choices;
4. support_style_preferences=ask_fewer_questions avoids question-heavy labels;
5. relationship memory source labels parent_setting vs child_conversation;
6. parent report uses support style without labeling child.
```

Minimum commands:

```bash
cd backend && pytest backend/app/tests/test_child_profile.py backend/app/tests/test_topic_seed_service.py backend/app/tests/test_parent_report_conversation_analysis.py
cd backend && ruff check .
```

---

## 5. Final response required

Report:

```text
1. commit sha;
2. files changed;
3. profile integration behavior by service;
4. opening example;
5. topic suggestion example;
6. relationship memory example;
7. parent report example;
8. tests run and results;
9. confirmation no auth UI/TTS/ASR/mascot work was added.
```
