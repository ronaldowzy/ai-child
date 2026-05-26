# CODE_AGENT_TASK_14_PRODUCT_ADVANCEMENT_MEMORY_ARC_SHOWTELL_UI_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: product advancement batch, not QA-only  
Goal: continue building the product vision after Task 11/12 instead of waiting for nightly device QA.

---

## 0. Why this task

The master session explicitly corrected the workflow: do not spend the whole day circling around tonight's APK test. Real-device QA is important, but it should validate batches of product work, not block every next step.

Task 11 reset the child conversation prompt and parent report prompt. Task 12 contained the authorized local TTS experiment. Task 13 can remain as a future QA build package, but the main daytime work now continues with product advancement.

This Task 14 starts the next planned product layer from the roadmap:

```text
1. relationship memory v2;
2. conversation arc materialization;
3. show-and-tell image/object sharing v2;
4. child companion surface UI v2 thin slice;
5. synthetic scenario harness to protect the above from regressions.
```

Do not add broad new features outside these lanes.

---

## 1. Required reading

Before coding, read:

```text
docs/CODE_AGENT_PROJECT_CONTEXT_AND_WORKFLOW_V0_1.md
docs/PRODUCT_AND_EXPERIENCE_ROADMAP_AFTER_TASK09_V0_1.md
docs/CODE_AGENT_TASK_11_PROMPT_AND_REPORT_DESIGN_RESET_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md
docs/CHILD_UI_POLISH_DESIGN_V0_1.md
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
```

Important: Task 14 must not overwrite Task 11 prompt reset unless this document provides exact new text. It should build systems around the new prompt quality.

---

## 2. Coordination model

If using multiple agents, split into branches:

```text
codeagent/task14-a-relationship-memory-v2
codeagent/task14-b-conversation-arc-materials
codeagent/task14-c-show-and-tell-v2
codeagent/task14-d-child-ui-surface-v2
codeagent/task14-e-synthetic-scenario-harness
```

If using one agent, execute A -> B -> C -> D -> E.

Suggested merge order:

```text
1. Lane A first: memory/profile material is foundation.
2. Lane B second: conversation arc uses memory material.
3. Lane C third: show-and-tell writes better material.
4. Lane D fourth: UI consumes backend quick suggestions/status without inventing content.
5. Lane E last: scenario harness covers the final integrated behavior.
```

---

# Lane A — Relationship Memory v2: structured, non-raw, parent-operated child account memory

## A1. Goal

Create a small relationship memory layer that helps Xiaobaihu remember useful, safe, non-raw facts about the child.

This memory should support:

```text
1. more personalized opening;
2. better topic choices;
3. better parent report summaries;
4. less repetitive conversation;
5. respecting things the child does not want to talk about.
```

Do **not** create a surveillance diary.

## A2. Memory object design

Add or refine a structured memory object with fields like:

```json
{
  "child_id": "...",
  "interests": [
    {"label": "画画", "source": "parent_setting|child_conversation|image_share", "confidence": "low|medium|high", "last_seen_at": "..."}
  ],
  "topic_boundaries": [
    {"label": "不要追问输赢", "source": "parent_setting|child_signal", "last_seen_at": "..."}
  ],
  "recent_positive_moments": [
    {"summary": "孩子分享了一个让他有点紧张的比赛", "last_seen_at": "..."}
  ],
  "recent_unfinished_threads": [
    {"summary": "孩子说要去英语打卡，一会再聊", "suggested_next_step": "下次开场不要强追问，只可轻轻提一句"}
  ],
  "communication_style": {
    "prefers_short_choices": true,
    "often_short_answers": true,
    "best_prompt_style": "二选一或很短的选择"
  },
  "last_updated_at": "..."
}
```

Exact schema can vary, but it must be:

```text
1. non-raw;
2. short;
3. auditable;
4. safe to use in prompts;
5. not a full transcript;
6. tied to the logged-in child account.
```

## A3. Update policy

Memory should update only from safe signals:

```text
1. parent settings: interests and topic boundaries;
2. child repeatedly mentions an interest;
3. child explicitly says they do not want to talk about something;
4. child shares a creation/object/image;
5. end-of-session synthetic summary.
```

Do not infer sensitive traits, mental health labels, ability labels, or personality labels.

Do not store raw child sentences. Store short summaries only.

## A4. Allowed files

```text
backend/app/services/conversation_memory_hooks.py
backend/app/services/conversation_history_service.py
backend/app/services/parent_policy_service.py
backend/app/services/topic_seed_service.py
backend/app/services/opening_service.py
backend/app/repositories/*memory* or existing repository files
backend/app/domain/schemas/*memory* or existing schema files
backend/app/tests/**/*memory*
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

Do not add a large migration unless necessary. Prefer existing JSON persistence if available.

## A5. Acceptance criteria

```text
1. Parent settings interests flow into relationship memory or memory context.
2. Child boundary signals can create/update a non-raw topic boundary.
3. Recent unfinished thread, e.g. “要去英语打卡，一会再聊”, can be stored as a short summary.
4. Opening/topic suggestion services can read memory context.
5. Tests prove raw child text is not stored in memory fields intended for prompt use.
```

---

# Lane B — Conversation Arc Materialization v2

## B1. Goal

Make each conversation feel like a coherent arc, not isolated turns.

Conversation arc:

```text
opening -> child-led topic -> brief deepen -> shift/close detection -> real-life bridge -> memory/report material
```

## B2. Runtime material

Add a lightweight `ConversationArcState` or equivalent material object per session/turn:

```json
{
  "session_topic": "比赛和紧张感",
  "turn_count_on_topic": 3,
  "child_engagement": "low|medium|high|unclear",
  "current_arc_phase": "opening|exploring|deepening|soft_shift|closing|handoff",
  "last_boundary_signal": "none|topic_change|no_chat|bedtime|leave_for_task",
  "real_life_bridge_hint": "可以等会儿跟家长说一句比赛前有点紧张",
  "memory_update_hint": "孩子今天提到比赛紧张和英语打卡"
}
```

Exact shape can vary, but it should be non-content and usable for:

```text
1. next prompt context;
2. parent report material;
3. memory updates;
4. QA/debug metrics.
```

## B3. Behavior rules

```text
1. If child gives short answers for 2-3 turns, arc phase should move toward soft_shift.
2. If child says they need to go do something, arc phase should become closing/handoff.
3. If child adds vivid detail, arc can remain exploring/deepening.
4. Parent report should receive arc summaries, not raw transcript.
5. Opening should use prior unfinished thread carefully, not force a continuation.
```

## B4. Allowed files

```text
backend/app/services/turn_guidance_builder.py
backend/app/services/child_agent_runtime.py
backend/app/services/conversation_service.py
backend/app/services/conversation_stream_service.py
backend/app/services/parent_report_service.py
backend/app/services/conversation_memory_hooks.py
backend/app/tests/**/*turn_guidance*
backend/app/tests/**/*child_agent_runtime*
backend/app/tests/**/*parent_report*
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## B5. Acceptance criteria

```text
1. A match/competition conversation with short answers reaches soft_shift instead of deepening endlessly.
2. “我要去英语打卡，一会再聊” becomes closing/handoff, not another topic hook.
3. Parent report material includes match/image/leave-for-task at summary level.
4. No raw transcript is added to arc state logs.
```

---

# Lane C — Show-and-tell Image/Object Sharing v2

## C1. Goal

Improve “拍给小白狐看” from image upload working to a natural child expression loop.

A child should feel:

```text
小白狐真的看到了一个具体东西，愿意听我讲一点，而不是把图片当作作业检查或隐私警告。
```

## C2. Show-and-tell response policy

When image/object sharing is ordinary and safe:

```text
1. Mention exactly one concrete safe visible detail.
2. Use a warm short sentence.
3. Invite child to tell one small thing only if appropriate.
4. Do not ask multiple questions.
5. Do not classify everything as homework.
6. Do not over-describe the image.
7. If uncertain, say “我看得还不太清楚”。
```

Exact child-facing examples:

```text
“我看到像是一个小摆件，颜色挺亮。你是想让我看看它哪里有趣吗？”
“这个看起来像你手边的一个小东西。你可以只告诉我它叫什么。”
“我看得还不太清楚，但我知道你是想拿给我看。”
```

Do not use these exact examples mechanically every time.

## C3. Structured material

Add a `show_and_tell_event` or equivalent summary for parent report/memory:

```json
{
  "type": "show_and_tell",
  "safe_visible_detail": "一个小物品/图画/搭建作品",
  "child_intent": "想让小白狐看看这个东西",
  "followup_style": "one_small_question|max_one_choice|no_question",
  "parent_report_hint": "孩子今天拿了一个东西给小白狐看，可能是在分享身边物品。"
}
```

No raw image. No full caption. No private details.

## C4. Allowed files

```text
backend/app/services/modality_manager.py
backend/app/services/parent_report_service.py
backend/app/services/conversation_memory_hooks.py
backend/app/tests/test_attachment_api.py
backend/app/tests/**/*modality* or image tests
docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## C5. Acceptance criteria

```text
1. Ordinary image sharing response includes one safe specific detail if available.
2. Low-confidence image does not hallucinate details.
3. Homework-like image only enters learning mode if child intent is homework/help, not any image with text.
4. Parent report can mention image/object sharing at summary level.
5. Tests cover ordinary object/photo, unclear image, homework-like image, and privacy-like image.
```

---

# Lane D — Child Companion Surface UI v2 Thin Slice

## D1. Goal

Make the child chat screen feel less like an engineering chat window and more like a calm Xiaobaihu companion surface.

This is still a thin slice. No big redesign.

## D2. Required UI changes

Implement only low-risk improvements:

```text
1. Left Xiaobaihu panel: add a simple “小白狐在这里” or equivalent warm status label when idle.
2. Add a tiny memory-aware subtitle if backend provides safe context, e.g. “可以聊画画、比赛，或者拍给我看一个东西”.
3. Right chat area: improve empty-state text so first screen does not feel blank or mechanical.
4. Quick actions: only show backend-provided actions; do not reintroduce fixed hard-coded topic menu.
5. Parent/adult entry remains small and unobtrusive.
```

## D3. Copy rules

Allowed copy examples:

```text
“小白狐在这里。”
“想说什么都可以慢慢说。”
“可以聊一件小事，也可以拍给我看。”
```

Forbidden:

```text
“今天任务”
“连续打卡”
“获得奖励”
“小白狐一直等你”
“不要忘了回来”
```

## D4. Allowed files

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/InputBar.kt
android/app/src/test/java/com/childai/companion/ui/chat/*
docs/CHILD_UI_POLISH_DESIGN_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

## D5. Acceptance criteria

```text
1. Empty/idle child screen feels warm and simple.
2. No gamification or dependency language.
3. Voice-first controls remain obvious.
4. Backend-provided quick actions are not crowded.
5. Layout remains suitable for Redmi K60 landscape and Honor Pad 5 pending QA.
```

---

# Lane E — Synthetic Scenario Harness for Product Behavior

## E1. Goal

Add non-device synthetic scenario tests so product behavior does not regress while rapid development continues.

This is not a replacement for real-device QA. It is a guardrail so code agents do not break core behavior.

## E2. Scenarios

Add or extend a script/test suite covering:

```text
1. Child says they are nervous before a match.
2. Child gives short answers after 2-3 turns.
3. Child uploads or describes an object/photo.
4. Child says they need to do English check-in and will chat later.
5. Parent report is generated after that session.
6. Opening next time sees unfinished thread but does not force continuation.
```

Expected outputs:

```text
1. Xiaobaihu does not interview endlessly.
2. Closing/handoff is respected.
3. Parent report says match/image/English check-in at summary level.
4. No internal words: 接一句, 桥接, 结构化摘要, 表达入口.
5. No raw transcript in report UI payload.
```

## E3. Allowed files

```text
backend/app/tests/**/*scenario*
backend/app/tests/test_child_agent_runtime.py
backend/app/tests/test_parent_report_conversation_analysis.py
scripts/run_model_trace_scenarios.py
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
```

## E4. Acceptance criteria

```text
1. One command can run the synthetic scenario harness or targeted tests.
2. Tests use synthetic data only.
3. Tests fail if parent report contains internal forbidden words.
4. Tests fail if stop/leave signal produces another deepening question.
```

---

## 3. Do not touch in Task 14

Unless required to fix a test failure caused by this task, do not modify:

```text
auth/account flows
TTS provider/fallback logic
ASR
image upload transport
database migrations
Android navigation
new onboarding screens
raw transcript export
```

---

## 4. Testing commands

Run targeted tests for changed areas. Minimum:

```bash
cd backend && pytest backend/app/tests/test_child_agent_runtime.py backend/app/tests/test_parent_report_conversation_analysis.py backend/app/tests/test_attachment_api.py
cd backend && ruff check .
cd android && ./gradlew test
```

If full Android tests are too slow, run targeted JVM tests and report what was skipped.

---

## 5. Final response required

Report:

```text
1. commit sha;
2. lanes completed;
3. files changed by lane;
4. tests run and exact results;
5. relationship memory v2 schema/example;
6. conversation arc example for match -> short answers -> English check-in;
7. show-and-tell example output;
8. child UI before/after summary;
9. synthetic scenario harness command/result;
10. confirmation no TTS/auth/ASR/navigation work was added.
```
