# CODE_AGENT_TASK_19_PERSONALIZED_CHILD_SESSION_LOOP_CLOSEOUT_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: integration closeout after Tasks 15/17/18  
Goal: turn profile + memory + conversation arc + show-and-tell + visual state into one observable personalized child session loop.

---

## 0. Why this task

Tasks 15, 17, and 18 added important pieces:

```text
Task 15: canonical child profile.
Task 17: Xiaobaihu visual state v2 resolver and trigger tests.
Task 18: profile context integration into opening/topic/memory/report.
```

Now the product needs one complete, testable loop:

```text
parent sets child profile -> child opens app -> Xiaobaihu greets naturally -> child talks / shares image -> Xiaobaihu follows arc and respects stop -> memory updates non-raw -> parent report summarizes -> next opening uses safe context lightly -> Xiaobaihu visual state reflects interaction without reward/flicker.
```

This task is not a new feature expansion. It is an integration closeout and synthetic scenario harness upgrade.

---

## 1. Required reading

```text
docs/CODE_AGENT_TASK_15_CHILD_PROFILE_UNIFICATION_AND_PROMPT_CONTEXT_V0_1.md
docs/CODE_AGENT_TASK_17_XIAOBAIHU_VISUAL_STATE_V2_RESOLVER_V0_1.md
docs/CODE_AGENT_TASK_18_PROFILE_CONTEXT_INTEGRATION_CLOSEOUT_V0_1.md
docs/XIAOBAIHU_STATE_AND_ANIMATION_AUDIT_V0_1.md
docs/CODE_AGENT_PROJECT_CONTEXT_AND_WORKFLOW_V0_1.md
```

---

## 2. Required integrated scenario

Create or extend a synthetic scenario harness/test that simulates:

```text
1. Parent registers/has a child profile:
   - nickname: 航航
   - age: 7
   - gender: boy
   - interests: 跑步比赛, 画画
   - topic_boundaries: 不要追问比赛输赢
   - child_temperament: concise, sensitive_to_pressure
   - support_style_preferences: offer_two_choices, ask_fewer_questions, use_shorter_sentences
   - learning_support_preferences: hint_first, keep_homework_short

2. Opening:
   - uses nickname or light interest;
   - short;
   - does not say “你是说话短/不喜欢压力的孩子”;
   - does not mention gender stereotypes.

3. Conversation:
   - child says比赛前有点紧张;
   - child gives a short answer after 2-3 turns;
   - Xiaobaihu soft-shifts or gives choice, not endless interview;
   - visual state path should be idle -> listening -> thinking -> speaking.

4. Show-and-tell:
   - child shares/describes an object or photo;
   - Xiaobaihu mentions one safe detail and asks at most one small question;
   - relationship memory stores a non-raw show_and_tell_event.

5. Closing/handoff:
   - child says要去英语打卡，一会再聊;
   - arc becomes closing/handoff;
   - Xiaobaihu respects stop and does not pull back into old topic.

6. Parent report:
   - summary mentions match/nervousness, image/object, English check-in at high level;
   - no raw transcript;
   - no internal words: 接一句, 桥接, 结构化摘要, 表达入口;
   - parent action respects support style, e.g. only one small question.

7. Next opening:
   - may lightly remember unfinished thread;
   - does not force continuation;
   - respects boundary about not追问输赢.
```

---

## 3. Implementation requirements

### 3.1 Scenario harness

Prefer adding/extending:

```text
scripts/run_model_trace_scenarios.py
backend/app/tests/test_personalized_session_loop.py
```

Use synthetic data only. Do not require real child data.

The test may use deterministic/fake model outputs where necessary, but it must check the real services' integration points.

### 3.2 Observable trace output

Add a compact trace format for this scenario, for example:

```json
{
  "profile_context_used": true,
  "opening": {"text": "...", "contains_forbidden_label": false},
  "topic_choices": ["聊跑步比赛", "聊画画"],
  "arc_phases": ["opening", "exploring", "soft_shift", "handoff"],
  "memory_updates": ["show_and_tell_event", "unfinished_thread"],
  "visual_states": ["idle", "listening", "thinking", "speaking"],
  "parent_report_checks": {
    "mentions_match": true,
    "mentions_image": true,
    "mentions_english_checkin": true,
    "no_internal_words": true,
    "no_raw_transcript": true
  }
}
```

Do not log raw child text in production logs. Synthetic test traces can include synthetic snippets if needed.

### 3.3 Small fixes allowed

If the scenario exposes a small integration gap, fix it within allowed files.

Allowed:

```text
backend/app/services/opening_service.py
backend/app/services/quick_action_service.py
backend/app/services/topic_seed_service.py
backend/app/services/relationship_memory.py
backend/app/services/conversation_memory_hooks.py
backend/app/services/parent_report_service.py
backend/app/tests/test_personalized_session_loop.py
scripts/run_model_trace_scenarios.py
android/app/src/test/java/com/childai/companion/ui/chat/*State*Test.kt
```

Do not modify:

```text
auth/account schema
parent settings UI
TTS provider/fallback
ASR
image upload transport
Android navigation
animation assets
DB migrations
```

---

## 4. Specific checks

The scenario must fail if:

```text
1. opening says labels like “你是慢热/说话短/容易受挫”.
2. opening uses gender to infer interests or behavior.
3. topic suggestions include a topic boundary such as追问比赛输赢.
4. support_style_preferences=offer_two_choices still returns 3+ choices.
5. support_style_preferences=ask_fewer_questions returns labels that are all questions.
6. parent report includes internal words: 接一句, 桥接, 结构化摘要, 表达入口.
7. parent report exposes raw transcript-like content.
8. closing/handoff still deepens old topic.
9. visual resolver maps generic encouragement to jumping_happy by default.
```

---

## 5. Tests

Run at minimum:

```bash
cd backend && pytest backend/app/tests/test_personalized_session_loop.py backend/app/tests/test_child_profile.py backend/app/tests/test_parent_report_conversation_analysis.py backend/app/tests/test_topic_seed_service.py backend/app/tests/test_quick_action_service.py
cd backend && ruff check .
cd android && ./gradlew test
```

If Android full tests are too slow, run targeted state resolver tests and report skipped parts.

---

## 6. Final response required

Report:

```text
1. commit sha;
2. files changed;
3. integrated scenario trace summary;
4. opening example and checks;
5. topic choices example and checks;
6. arc phase sequence;
7. memory update summary;
8. parent report summary checks;
9. visual state sequence checks;
10. tests run and exact results;
11. confirmation no auth/TTS/ASR/navigation/assets changes were made.
```
