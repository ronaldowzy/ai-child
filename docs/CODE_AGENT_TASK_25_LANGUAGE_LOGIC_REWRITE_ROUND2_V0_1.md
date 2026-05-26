# CODE_AGENT_TASK_25_LANGUAGE_LOGIC_REWRITE_ROUND2_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: language/copy logic correction, mechanical implementation round 2  
Goal: finish the project-wide Chinese wording and logic cleanup started by the master session, without letting the code agent design product copy.

---

## 0. Current status

The previous `CODE_AGENT_TASK_25_VOICE_FIRST_CONVERSATION_POLISH_V0_1.md` is paused. Do not implement it now.

The master session has already directly updated these prompt files in round 1:

```text
backend/app/prompts/persona_little_fox_v0_1.txt
backend/app/prompts/scenes/daily_after_school_checkin_v0_1.txt
backend/app/prompts/scenes/daily_bedtime_reflection_v0_1.txt
backend/app/prompts/scenes/learning_homework_help_v0_1.txt
```

Round 2 is for the code agent to apply exact wording corrections in code-backed strings and tests.

The code agent must not invent new product wording. Use the replacements below.

---

## 1. Required reading

```text
docs/MASTER_COLLABORATION_AND_FORWARD_MOTION_RULES_V0_1.md
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
1. Do not change ASR/TTS provider architecture.
2. Do not change image upload transport or storage.
3. Do not change auth/account/navigation.
4. Do not change mascot assets or animation manifest.
5. Do not add gamification, rewards, score, missions, streaks, badges, or retention hooks.
6. Do not add raw transcript/image/audio export.
7. Do not invent product copy beyond exact replacements below.
```

---

## 3. Required backend wording changes

### 3.1 `PromptManager._render_image_context()`

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

Keep the existing per-type rules but avoid engineering wording. For privacy, use:

```text
如果图片可能包含隐私内容，不要描述私密细节。可以建议孩子请家长一起看一下。
```

For no image context, keep the meaning but prefer:

```text
当前没有图片上下文。不要假装看到了图片。如果孩子只是说想拍照给你看，请告诉孩子可以点“拍给小白狐看”上传。
```

Do not mention backend/provider/debug in the prompt text.

### 3.2 `ParentReportService._parent_report_system_prompt()`

Replace the reader intent from:

```text
家长想知道：今天孩子大概和小白狐聊了什么...
```

to:

```text
家长想知道：孩子今天大概表达了哪些主题或状态，家长今晚可以怎样自然接住，以及哪些问法最好避免。
```

Keep the no-raw-transcript/no-monitoring rules.

Add or strengthen this principle:

```text
家长日报不是孩子和小白狐的聊天监控。不要让家长像是在追问孩子与小白狐的私密互动细节。
```

For image topics, avoid wording that suggests the parent saw or should ask about the exact image sent to Xiaobaihu.

### 3.3 Parent report image sharing fallback

Replace all wording like:

```text
你今天那张图，最想让我看哪里？
一起看一眼图片
今天给小白狐看的是什么呀
孩子今天拿了一个{topic}给小白狐看
```

with parent-safe open invitations.

Use these exact styles:

```text
孩子今天有用图片来表达或展示的倾向。家长可以留一个开放入口：“今天有没有什么想给我看看，或者想讲给我听的小东西？”如果孩子不想说，就不用追问。
```

For `tonight_parent_bridge` when topics include 图片分享 / 看图交流:

```text
今晚可以自然留个入口：“今天有没有什么想给我看看，或者想讲给我听的小东西？”如果孩子不想说，就不用追问。
```

For `SHOW_AND_TELL_EVENT` parent action:

```text
孩子今天有展示或分享的表达；家长可以轻轻问：“今天有没有什么想让我也看看？”不需要追问是不是给小白狐看过。
```

For `expression_observations` image text:

```text
孩子今天有通过图片表达或展示的倾向；家长可以顺着孩子愿意分享的部分看一眼，不需要追问具体是哪张图。
```

For `avoid_followup` image item:

```text
不要追问孩子具体给小白狐看了哪张图，也不要把所有图片都默认当成作业或隐私问题。
```

### 3.4 Parent report internal word guard

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
```

Be careful: `小白狐` itself is allowed in general, but avoid wording that asks parent to interrogate what was shown to Xiaobaihu.

---

## 4. Required Android child-facing wording changes

### 4.1 `ChatViewModel.followupFailureMessage()`

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

### 4.2 `ChildTurnUiPhase.statusText()`

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

### 4.3 `ChildTurnUiPhase.primaryButtonText()`

Replace:

```text
请大人检查后再说
```

with:

```text
请大人帮忙看看
```

Optional if nearby tests exist: keep “按一下开始说” unless there is a clear reason to change.

### 4.4 Parent entry hints in `ChildChatScreen.kt`

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

### 4.5 Dev/debug transcript panel

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

## 5. Tests required

Backend tests:

```text
cd backend && pytest app/tests/test_parent_report_visible_quality.py app/tests/test_show_and_tell_visible_quality.py
cd backend && ruff check .
```

Add/adjust tests to verify:

```text
1. Parent report image bridge does not contain “那张图”.
2. Parent report image bridge does not ask what was shown to Xiaobaihu.
3. Parent report image observations use open family invitation wording.
4. PromptManager image context no longer contains “后端图片理解”.
5. Parent-facing report fields do not contain internal words listed above.
```

Android tests:

```text
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

## 6. Final report required

Report:

```text
1. commit sha;
2. files changed;
3. exact wording replacements applied;
4. tests run and exact results;
5. confirmation old voice-first Task 25 was not implemented;
6. confirmation no forbidden areas were touched;
7. remaining device QA items marked NOT_RUN.
```

---

## 7. Master review guidance

Reject if:

```text
1. The patch implements the old voice-first Task 25 instead of this language rewrite.
2. The patch changes ASR/TTS/image/upload/auth/navigation/mascot assets.
3. Parent report still asks parents about “那张图” or “给小白狐看的是什么”.
4. Child-facing strings contain “后端”, “provider”, “ASR”, “error”, “policy”, or similar engineering terms.
5. The code agent invents new copy instead of applying the provided replacements.
```
