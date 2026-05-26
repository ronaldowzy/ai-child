# CODE_AGENT_TASK_23_SHOW_AND_TELL_VISIBLE_QUALITY_V3

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: focused backend visible-quality improvement after Task 22  
Goal: make “拍给小白狐看” feel more natural and child-friendly for drawings, toys, objects, schoolwork, and unclear images, while preserving privacy/homework safety boundaries.

---

## 0. Why this task

The product has already moved from “拍题目” to the more general child expression action: “拍给小白狐看”.

Existing design says children may share:

```text
玩具、画、书、昆虫、植物、作业、手工、生活中看到的东西。
```

The current backend already passes `image_context` into prompt composition and has a repair path when the model incorrectly says it cannot see images.

But the visible experience still needs to feel less like a generic image classifier and more like Xiaobaihu is gently looking with the child.

Task 23 should improve the first child-facing response and parent-report summary for show-and-tell, without adding new image storage, new image model architecture, or Android camera scope.

---

## 1. Product principles

Show-and-tell should feel like:

```text
1. “小白狐真的在和我一起看”；
2. warm, specific, and short;
3. child-led rather than adult evaluation;
4. safe when the image is unclear, private, or homework-like;
5. connected to parents through parent report without exposing raw image/text.
```

It must not become:

```text
1. an OCR/classifier report;
2. art grading or correction;
3. a homework answer machine;
4. privacy overexposure;
5. a fake hallucinated visual description;
6. a reward loop or sticker/score system.
```

---

## 2. Required reading

```text
docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/CODE_AGENT_PROJECT_CONTEXT_AND_WORKFLOW_V0_1.md
docs/MASTER_COLLABORATION_AND_FORWARD_MOTION_RULES_V0_1.md
backend/app/services/prompt_manager.py
backend/app/services/child_agent_runtime.py
backend/app/services/parent_report_service.py
backend/app/tests/test_personalized_session_loop.py
```

Current facts to preserve:

```text
1. PromptManager renders image_context and tells the model not to claim missing image capability.
2. ChildAgentRuntime has _image_context_repair_reply() for model image-refusal repair.
3. ParentReportService already recognizes attachments / image_or_photo signals in deterministic fallback.
4. Android local preview is a temporary child UI confirmation and must not leak local file paths into prompts.
```

---

## 3. Scope

Allowed files:

```text
backend/app/services/prompt_manager.py
backend/app/services/child_agent_runtime.py
backend/app/services/parent_report_service.py
backend/app/tests/test_show_and_tell_visible_quality.py
backend/app/tests/test_personalized_session_loop.py
backend/app/tests/test_parent_report_visible_quality.py
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

Only touch Android if a tiny test fixture or string mismatch blocks backend tests. Do not change Android camera/upload/runtime behavior in this task.

Forbidden:

```text
1. no new image upload transport;
2. no CameraX work;
3. no new image storage or raw image persistence;
4. no new vision provider architecture;
5. no TTS/ASR/auth/account changes;
6. no mascot assets or animation changes;
7. no raw transcript/image export;
8. no gamification/reward/sticker/score system;
9. no broad prompt rewrite beyond the specific image-context/show-and-tell wording in this task.
```

---

## 4. Required behavior

### 4.1 Child-facing first response for non-homework sharing

When `image_context` is present and the image is not homework/privacy/unsafe, Xiaobaihu should respond with a short natural line.

Use this style:

```text
我看到这里有一个{具体但安全的细节}。你最想让我看哪里？
```

or, for drawings/child-created art:

```text
我看到你画了{一个具体细节}。这个地方很有意思。你想给它起个名字吗？
```

Rules:

```text
1. Mention at most one safe visible detail from recognized_text / recognized_type.
2. Do not score, grade, criticize, or overpraise the child’s work.
3. Do not say “画得真棒” as generic filler unless the child clearly wants encouragement; prefer noticing a concrete detail.
4. Do not invent details absent from image_context.
5. Keep it short; usually 1-2 sentences.
6. Ask at most one gentle question.
```

### 4.2 Different handling by image intent/type

If available, use `image_purpose`, `recognized_type`, `recognized_text`, and `child_caption`.

Target visible behavior:

```text
art_feedback / child_drawing:
  Notice one concrete detail; invite child to tell the story/name/part they like.
  Do not grade, compare, or correct.

toy / object / handmade / daily_life:
  Mention one safe concrete detail; ask what the child wants Xiaobaihu to notice.

ask_what_is_this:
  If context supports a safe identification, answer cautiously: “看起来像……”。
  If unsure, say not fully sure and ask for one clue.

tell_story:
  Start a tiny imaginative bridge, but avoid long overstimulating story unless child asks.

learning_homework / homework_problem:
  Enter learning help mode. First ask what the question is asking or where the child is stuck.
  Do not give final answer directly.

privacy_sensitive:
  Do not describe private details. Ask child to find a家长 together or keep it general.

unsafe_unknown / unclear / low confidence:
  Do not pretend to see. Ask child to tell Xiaobaihu what they want to show.
```

### 4.3 PromptManager image context wording

Improve only `_render_image_context()` if needed.

It should tell the model:

```text
1. image_context is a safe summary, not raw image;
2. use at most one concrete detail;
3. do not write an image recognition report;
4. do not hallucinate details;
5. for child art, notice rather than judge;
6. for homework, scaffold not answer;
7. for privacy/unsafe/unclear, stay safe and ask child/parent for help.
```

Do not rewrite the global persona or entire prompt system.

### 4.4 Deterministic repair fallback

Improve `_image_context_repair_reply()` in `ChildAgentRuntime` so if the model says it cannot see images, the repair response follows the visible-quality rules above.

Minimum cases:

```text
1. child drawing / art_feedback -> concrete detail + gentle invitation;
2. toy/object/share -> concrete detail + “你最想让我看哪里？”;
3. homework_problem -> learning scaffold, no final answer;
4. privacy_sensitive -> privacy-safe bridge to家长;
5. unclear/empty -> do not pretend; ask child what to look at.
```

### 4.5 Parent report visible quality

Parent report should summarize image sharing as a child expression event, not raw content extraction.

Good examples:

```text
孩子今天把图片作为表达入口，更像是在分享自己看到或做出来的东西。
今晚可以问：“那张图你最想让我看哪里？”孩子不想说就换轻松话题。
```

For child art / handmade / toy/object, parent report may say:

```text
孩子今天用图片分享了自己的作品或感兴趣的东西；家长可以先顺着孩子想展示的部分看一眼，不急着评价好坏。
```

Do not include raw transcript, raw image text, local file names, or internal labels such as `image_context`, `recognized_type`, `prompt`, `provider`.

---

## 5. Tests required

Add `backend/app/tests/test_show_and_tell_visible_quality.py` or equivalent.

Required tests:

```text
1. drawing/art image refusal repair produces concrete-detail + child-led invitation, not “我看不到图片”.
2. toy/object image refusal repair does not become homework help.
3. homework image repair asks about题意/卡点 and does not give final answer.
4. privacy image repair does not expose details and asks for家长 help.
5. unclear image repair does not pretend to see.
6. PromptManager image_context section includes “one concrete detail / do not hallucinate / not raw image / child art notice not judge” rules.
7. Parent report fallback for image sharing avoids internal words and raw transcript/image text.
8. Existing personalized session loop still passes.
```

Also strengthen existing parent-report visible-quality tests if needed.

---

## 6. Example expected outputs

These are product examples. Do not have to match character-for-character unless a test is explicitly checking an exact fallback.

```text
Drawing:
我看到你画里有一只小狐狸。这个地方很有意思，你想给它起个名字吗？

Toy/object:
我看到图里像是一个积木城堡。你最想让我看哪里？

Unclear:
图片已经传上来了，但这次我看不太清。你可以告诉我最想让我看哪里。

Homework:
我看到这张图像是一道题。我们先看看题目在问什么，你可以读一小句给我听。

Privacy:
这张图可能有隐私内容，我们先不展开细节。可以请家长一起看一下。
```

Avoid:

```text
1. “我无法看到图片。” when image_context exists.
2. “这幅画画得非常棒，满分！”
3. “答案是……”
4. “我看到你家地址/学校名/电话……”
5. “这是一个 image_context / recognized_type=...”
```

---

## 7. Test commands

Run:

```bash
cd backend && pytest app/tests/test_show_and_tell_visible_quality.py app/tests/test_parent_report_visible_quality.py app/tests/test_personalized_session_loop.py
cd backend && ruff check .
```

If full backend tests are run, report that too. Do not claim Android/device QA passed unless tested on device.

---

## 8. Final report required

Report:

```text
1. commit sha;
2. files changed;
3. child-facing show-and-tell examples for drawing, object, homework, privacy, unclear;
4. prompt/image_context wording changes;
5. parent report visible-quality changes;
6. tests run and exact results;
7. confirmation no forbidden areas were touched;
8. remaining Redmi K60 / Honor Pad 5 image QA items as NOT_RUN unless actually tested.
```

---

## 9. Review guidance for master session

When reviewing Task 23:

```text
1. compare from this task-doc commit to main;
2. check file scope first;
3. inspect PromptManager image_context wording;
4. inspect ChildAgentRuntime image repair fallback;
5. inspect ParentReportService image summary wording if changed;
6. inspect tests for drawing/object/homework/privacy/unclear paths;
7. reject if the patch adds image storage, raw image export, Android camera scope, or broad prompt rewrites.
```
