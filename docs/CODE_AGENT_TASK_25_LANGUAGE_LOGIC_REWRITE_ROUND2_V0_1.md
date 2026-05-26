# CODE_AGENT_TASK_25_LANGUAGE_LOGIC_REWRITE_ROUND2_V0_2

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: language / prompt / parent-report output correction  
Goal: finish the project-wide Chinese wording and logic cleanup started by the master session, and fully incorporate the parent-report prompt/output audit.

---

## 0. Current status

The previous `CODE_AGENT_TASK_25_VOICE_FIRST_CONVERSATION_POLISH_V0_1.md` is paused. Do not implement voice-first behavior now.

The master session has already directly updated these prompt files in round 1:

```text
backend/app/prompts/persona_little_fox_v0_1.txt
backend/app/prompts/scenes/daily_after_school_checkin_v0_1.txt
backend/app/prompts/scenes/daily_bedtime_reflection_v0_1.txt
backend/app/prompts/scenes/learning_homework_help_v0_1.txt
```

This task is round 2. It combines:

```text
1. mechanical code-backed wording replacements from the first language audit;
2. deeper parent-report prompt/output corrections from PARENT_REPORT_PROMPT_AND_COPY_AUDIT_V0_1.
```

The code agent must not invent new product wording. Use the replacements and rules below.

---

## 1. Required reading

```text
docs/MASTER_COLLABORATION_AND_FORWARD_MOTION_RULES_V0_1.md
docs/PARENT_REPORT_PROMPT_AND_COPY_AUDIT_V0_1.md
backend/app/prompts/persona_little_fox_v0_1.txt
backend/app/prompts/scenes/daily_after_school_checkin_v0_1.txt
backend/app/prompts/scenes/daily_bedtime_reflection_v0_1.txt
backend/app/prompts/scenes/learning_homework_help_v0_1.txt
backend/app/services/prompt_manager.py
backend/app/services/parent_report_service.py
backend/app/services/child_agent_runtime.py
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildTurnUiPhase.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/InputBar.kt
```

---

## 2. Scope

Allowed files:

```text
backend/app/services/prompt_manager.py
backend/app/services/parent_report_service.py
backend/app/services/child_agent_runtime.py
backend/app/tests/test_parent_report_visible_quality.py
backend/app/tests/test_show_and_tell_visible_quality.py
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildTurnUiPhase.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/InputBar.kt
android/app/src/test/java/com/childai/companion/ui/chat/*
docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
```

Forbidden:

```text
1. Do not implement the old voice-first Task 25.
2. Do not change ASR/TTS provider architecture.
3. Do not change image upload transport or storage.
4. Do not change auth/account/navigation.
5. Do not change mascot assets or animation manifest.
6. Do not add gamification, rewards, score, missions, streaks, badges, or retention hooks.
7. Do not add raw transcript/image/audio export.
8. Do not invent product copy beyond the wording and rules below.
```

---

## 3. Core product rule for this task

Parent reports are not a monitoring log of the child's conversation with Xiaobaihu.

They should help parents understand:

```text
1. the broad themes or states the child expressed today;
2. one low-pressure way to connect tonight;
3. which questions or reactions to avoid.
```

They must not expose or prompt interrogation about:

```text
1. exact child-Xiaobaihu interaction details;
2. exact images shown to Xiaobaihu;
3. quasi-quotes reconstructed from snippets;
4. message counts or usage statistics;
5. teacher-style expression/ability assessment.
```

---

## 4. Required backend wording changes

### 4.1 `PromptManager._render_image_context()`

Current wording includes engineering terms such as “后端图片理解”. Replace the image-context system wording with a softer internal instruction.

Required content intent:

```text
孩子刚刚分享了一张图片。以下内容是系统提供的安全图片摘要，不是原始图片本身。
你可以基于这段摘要自然回应；不要说你看不到图片、不能看图片或没有看图功能。
图片意图：{purpose}。
识别类型：{recognized_type}。
图片描述：{text}
孩子说明：{child_caption}
这段图片描述只用于帮助你回应，不要逐字复述给孩子，也不要写成识别报告。
最多提及一个具体、安全、被摘要支持的细节。不要编造摘要里没有的内容。
```

Keep the existing per-type rules but avoid engineering wording.

For privacy, use:

```text
如果图片可能包含隐私内容，不要描述私密细节。可以建议孩子请家长一起看一下。
```

For no image context, keep the meaning but prefer:

```text
当前没有图片上下文。不要假装看到了图片。如果孩子只是说想拍照给你看，请告诉孩子可以点“拍给小白狐看”上传。
```

Do not mention backend/provider/debug in the prompt text.

### 4.2 `ParentReportService._parent_report_system_prompt()` reader intent

Replace the reader intent from:

```text
家长想知道：今天孩子大概和小白狐聊了什么，孩子表达了什么状态...
```

to:

```text
家长想知道：孩子今天大概表达了哪些主题或状态，家长今晚可以怎样自然接住，以及哪些问法最好避免。
```

Add or strengthen this principle:

```text
家长日报不是孩子和小白狐的聊天监控。不要让家长像是在追问孩子与小白狐的私密互动细节。
```

Also add:

```text
不要把日报写成使用统计、老师评语、心理诊断、行为评分或家长盘问清单。
```

### 4.3 `ParentReportService._parent_report_system_prompt()` output examples

Add good/bad examples so the model has a clear target style.

Good example style:

```text
summary: 今天孩子有一些轻量交流，主要围绕图片分享和一个想换题的信号。
conversation_summary: 孩子今天有用图片表达的倾向，也出现过想换题的信号。整体适合轻轻给一个分享入口，不需要追问具体聊了什么。
tonight_parent_bridge: 今晚可以自然留个入口：“今天有没有什么想给我看看，或者想讲给我听的小东西？”如果孩子不想说，就不用追问。
avoid_followup: 不要追问孩子具体给小白狐看了哪张图；不要要求孩子复述和小白狐的聊天内容。
```

Bad example style to forbid:

```text
今天孩子和小白狐聊了三件事...
你今天给小白狐看的是什么？
小白狐发现孩子表达能力较好...
孩子今天共有 5 条消息...
```

### 4.4 `short_content_hint` and `conversation_snippets` guard

If these payload fields remain, the prompt must explicitly say:

```text
short_content_hint / conversation_snippets 只用于判断大概主题，不得改写成“孩子说了……”或作为准原话输出。
```

Preferred implementation if low risk:

```text
1. Keep topic_overview_hints, state_hints, avoid_followup_hints.
2. Reduce parent-report reliance on short child text snippets.
3. If snippets are still sent, keep them as signals only and do not let model output reconstructed child utterances.
```

Tests must verify prompt contains this rule.

### 4.5 Remove message counts from parent-facing summaries

Current `_conversation_summary()` writes:

```text
今天共有 N 条孩子消息和 M 条小白狐回复。
```

Remove exact message counts from parent-facing summaries.

Use:

```text
今天有一些轻量互动，主要围绕{topic_text}。
```

If material is sparse:

```text
今天素材不多，只能做轻量总结。
```

Do not include exact child/agent message counts in `summary`, `conversation_summary`, or fallback report text.

### 4.6 Parent report image sharing fallback

Replace all wording like:

```text
你今天那张图，最想让我看哪里？
一起看一眼图片
今天给小白狐看的是什么呀
孩子今天拿了一个{topic}给小白狐看
把看到的东西给小白狐一起看
```

with parent-safe open invitations.

Use these exact styles:

For expression observation:

```text
孩子今天有通过图片表达或展示的倾向；家长可以顺着孩子愿意分享的部分看一眼，不需要追问具体是哪张图。
```

For topic overview image summary / intent:

```text
child_intent: 通过图片表达或展示自己看到、做出的东西
summary: 今天图片更像是孩子表达或展示的入口。家长可以给一个开放分享机会，不需要追问具体是哪张图。
parent_bridge: 今晚可以自然留个入口：“今天有没有什么想给我看看，或者想讲给我听的小东西？”如果孩子不想说，就不用追问。
```

For `tonight_parent_bridge` when topics include 图片分享 / 看图交流:

```text
今晚可以自然留个入口：“今天有没有什么想给我看看，或者想讲给我听的小东西？”如果孩子不想说，就不用追问。
```

For `SHOW_AND_TELL_EVENT` parent action:

```text
孩子今天有展示或分享的表达；家长可以轻轻问：“今天有没有什么想让我也看看？”不需要追问是不是给小白狐看过。
```

For `avoid_followup` image item:

```text
不要追问孩子具体给小白狐看了哪张图，也不要把所有图片都默认当成作业或隐私问题。
```

### 4.7 Parent actions should not become a question list

Current report often generates many items starting with:

```text
今晚可以问...
今晚可以轻轻问...
你最喜欢...
最有意思的是哪一段...
```

Required direction:

```text
1. Prefer one low-pressure opening sentence, not a question for every topic.
2. Use “如果孩子自己提起...” for sports/game/image topics.
3. Avoid turning every topic into something parents must ask tonight.
```

Recommended replacements:

For sports:

```text
如果孩子自己提起跑步，可以先顺着他说一小句，不核对成绩和真假。
```

For games:

```text
如果孩子自己提起游戏，可以先把它当作普通兴趣听一句，不急着谈时长或输赢。
```

For general expression:

```text
今晚可以留一个轻入口：“今天有没有一件还不错的小事？”孩子不想说就不追问。
```

### 4.8 Avoid teacher-style expression assessment

Replace teacher/report-card wording like:

```text
孩子今天整体能连续表达
孩子能把一个主动话题延展开
表达能力较好
```

with observable, low-judgment wording:

```text
孩子今天愿意围绕一个主题多说几句。
孩子今天多用短句表达，适合用更轻、更具体的方式接住。
```

### 4.9 Parent report internal word guard

Tests should reject these parent-facing words where applicable:

```text
接一句
桥接
结构化摘要
表达入口
image_context
recognized_type
prompt
provider
后端
给小白狐看的是什么
那张图
孩子今天共有
条孩子消息
条小白狐回复
表达能力较好
```

Be careful: `小白狐` itself is allowed in general, but avoid wording that asks parent to interrogate what was shown or said to Xiaobaihu.

---

## 5. Required Android child-facing wording changes

### 5.1 `ChatViewModel.followupFailureMessage()`

Replace child-facing engineering wording:

```text
小白狐现在没有连上后端。我们先停一下，请大人检查网络后再试。
题目已经识别到了，但还没有连上后端继续引导。请大人检查网络后再试。
图片已经识别到了，但还没有连上后端继续聊。请大人检查网络后再试。
```

with:

```text
小白狐这边没有接稳。我们先停一下，请大人检查网络后再试。
题目已经看到了，但这次没有接稳。请大人稍后再试。
图片已经看到了，但这次没有接稳。请大人稍后再试。
```

### 5.2 `ChildTurnUiPhase.statusText()`

Replace:

```text
小白狐准备说。
小白狐正在说。
```

with:

```text
我马上说给你听。
我在说给你听。
```

### 5.3 `ChildTurnUiPhase.primaryButtonText()`

Replace:

```text
请大人检查后再说
```

with:

```text
请大人帮忙看看
```

### 5.4 Parent entry hints in `ChildChatScreen.kt`

Replace:

```text
这是给家长看的，请让家长长按进入。
长按“大人”并输入家长账号密码，才能进入家长页面。
```

with:

```text
这里给大人用。请大人长按进入。
大人长按“大人”，输入家长账号密码后进入。
```

### 5.5 Dev/debug transcript panel

If tests touch it, replace label:

```text
先确认这句话
```

with:

```text
确认识别到的话
```

This panel remains DevSettings / parent debug only. Do not show it in child default mode.

---

## 6. Tests required

Backend tests:

```bash
cd backend && pytest app/tests/test_parent_report_visible_quality.py app/tests/test_show_and_tell_visible_quality.py
cd backend && ruff check .
```

Add/adjust tests to verify:

```text
1. Parent report image bridge does not contain “那张图”.
2. Parent report image bridge does not ask what was shown to Xiaobaihu.
3. Parent report image observations use open family invitation wording.
4. PromptManager image context no longer contains “后端图片理解”.
5. Parent report system prompt says it is not a child-Xiaobaihu chat-monitoring record.
6. Parent report prompt forbids snippet reconstruction from short_content_hint / conversation_snippets.
7. Parent-facing summaries do not include exact message counts.
8. Parent actions are not all direct questions.
9. Parent report avoids teacher-style assessment language such as “表达能力较好”.
10. Parent-facing report fields do not contain internal words listed above.
11. Parent report prompt includes good/bad output examples.
```

Android tests:

```bash
cd android && ./gradlew test --tests '*ChildTurnUiPhase*'
cd android && ./gradlew test
```

Add/adjust tests to verify:

```text
1. child-facing strings do not contain “后端”.
2. speaking pending/speaking labels are “我马上说给你听” / “我在说给你听”.
3. permission primary button is “请大人帮忙看看”.
4. parent entry hints match the new wording.
5. debug transcript label is “确认识别到的话” if covered.
```

---

## 7. Final report required

Report:

```text
1. commit sha;
2. files changed;
3. exact wording replacements applied;
4. parent report prompt/output boundary changes;
5. how message counts and snippet reconstruction were prevented;
6. tests run and exact results;
7. confirmation old voice-first Task 25 was not implemented;
8. confirmation no forbidden areas were touched;
9. remaining device QA items marked NOT_RUN.
```

---

## 8. Review guidance for master session

Reject if:

```text
1. The patch implements the old voice-first Task 25 instead of this language rewrite.
2. The patch changes ASR/TTS/image/upload/auth/navigation/mascot assets.
3. Parent report still asks parents about “那张图” or “给小白狐看的是什么”.
4. Parent-facing summaries include message counts.
5. Parent report prompt allows reconstructing child utterances from snippets.
6. Child-facing strings contain “后端”, “provider”, “ASR”, “error”, “policy”, or similar engineering terms.
7. The code agent invents new copy instead of applying the provided replacements.
```

---

## 9. After this task

After this task passes, continue the previous product optimization plan:

```text
1. Voice-first conversation polish;
2. first response / text-first audio-follow experience;
3. relationship continuity v2;
4. family bridge boundary v2, if still needed after this correction.
```
