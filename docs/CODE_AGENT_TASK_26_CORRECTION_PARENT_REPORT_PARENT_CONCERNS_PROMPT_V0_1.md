# CODE_AGENT_TASK_26_CORRECTION_PARENT_REPORT_PARENT_CONCERNS_PROMPT_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Task type: correction for Task 26 parent report narrative v3  
Goal: fix one implementation bug and strengthen the parent-report prompt around what real parents care about, without returning to stitched reports.

---

## 0. Review finding

Task 26 correctly moves the parent report toward a narrative format, but two issues remain.

### 0.1 Staleness bug

Current implementation parses model `narrative_report` into:

```text
summary = narrative_report
topic_overview = []
conversation_summary = None
```

But `_is_stale()` still treats any persisted report without `topic_overview` or `conversation_summary` as stale. This means a valid new narrative report may be regenerated every time.

Required fix:

```text
A MODEL_GENERATED report in the new narrative format should not require topic_overview or conversation_summary to be considered fresh.
Use material_fingerprint and latest material time as the freshness source of truth.
A report with non-empty summary and matching material_fingerprint is acceptable.
```

### 0.2 Prompt is too thin

The current system prompt says parents want to know:

```text
孩子今天大概怎么样，有没有什么值得留意的信号，今晚可以怎么自然地和孩子聊几句。
```

This is directionally right, but too generic. The model may output a short, bland note that still does not feel useful.

We need to tell the model what parents actually care about, while still preventing surveillance, diagnosis, and transcript-like summaries.

---

## 1. Product principle

A parent report should answer the parent’s real questions in a calm, practical way:

```text
1. 今天孩子整体状态怎么样？
2. 孩子今天主要在表达什么兴趣、困惑、情绪或需要？
3. 有没有需要家长今晚留意的风险、边界或不舒服信号？
4. 有没有学习/作业上的卡点，家长应该怎样帮，而不是直接替孩子做？
5. 有没有作品、图片、运动、游戏、故事等孩子想展示或分享的东西？
6. 家长今晚怎么自然打开一个话题？
7. 哪些问法可能让孩子有压力，最好避免？
```

But the report must not answer these by exposing private details.

It should not say:

```text
1. 孩子和小白狐逐句聊了什么；
2. 孩子具体给小白狐看了哪张图；
3. 孩子具体说了哪句话；
4. 孩子今天表现好不好；
5. 孩子是不是有心理问题；
6. 孩子用了 App 多少条消息。
```

---

## 2. Required files

Allowed:

```text
backend/app/services/parent_report_service.py
backend/app/tests/test_parent_report_visible_quality.py
backend/app/tests/test_parent_report_service.py
```

Optional if existing tests require it:

```text
backend/app/tests/test_show_and_tell_visible_quality.py
```

Forbidden:

```text
1. Do not change Android in this correction.
2. Do not change ASR/TTS/image upload/auth/navigation/mascot assets.
3. Do not restore stitched topic_overview / learning_observations / suggested_parent_actions as the main user-visible report.
4. Do not expose raw transcript, raw image text, message counts, or exact child quotes.
```

---

## 3. Required prompt redesign

Update `_parent_report_system_prompt()` so it contains a stronger parent-concern framework.

Use this intent. Exact formatting may vary, but keep the content.

```text
你是“小白狐”项目的家长日报撰写器。

你在帮家长读一份很短的“今晚小结”。
家长真正关心的不是孩子和小白狐逐句聊了什么，而是：
- 今天孩子整体状态大概怎么样；
- 孩子主要在表达什么兴趣、困惑、情绪或需要；
- 有没有需要家长留意的安全、隐私、情绪、学习或边界信号；
- 如果孩子今天展示了图片、作品、玩具、运动、游戏或故事，家长可以怎样顺着孩子愿意分享的部分连接现实生活；
- 今晚家长可以用一句怎样的低压力话打开交流；
- 哪些问法最好避免。

请先把今天的材料理解成一个整体，再写给家长。
不要像聊天记录，不要像老师评语，不要像心理诊断，不要像使用统计，不要像家长盘问清单。

重要边界：
- 不要说孩子和小白狐逐句聊了什么；
- 不要引用或改写孩子原话；
- 不要重构 short_content_hint / conversation_snippets；
- 不要说具体“那张图”或“给小白狐看的是什么”；
- 不要写消息数量；
- 不要给孩子贴固定标签；
- 没有证据时不要编造。

写作方式：
- narrative_report 是主要内容，2-4句自然中文；
- 先说整体状态，再说一两个有证据的主题或信号，最后自然落到家长今晚怎么接；
- 只写今天材料支持的内容，不需要覆盖所有维度；
- 如果素材很少，就诚实说明素材不多，并给一个轻量入口；
- 如果有安全/隐私信号，先写安全与家长平静介入；
- 如果有学习/作业线索，写“陪孩子看题意/第一步”，不要写答案；
- 如果有图片/作品/玩具分享，写“孩子有展示或分享的倾向”，不要让家长追问具体哪张图；
- 如果有运动/游戏话题，写成兴趣或体验表达，不要引导家长追问输赢、时长或真假。

返回严格 JSON object，只包含：
{
  "narrative_report": "2-4句自然小结",
  "tonight_parent_bridge": "今晚家长可以自然说的一句话",
  "avoid_followup": ["1-3条今晚尽量避免的问法"]
}
```

### 3.1 Better examples

Replace the current single generic example with category-aware examples.

Good normal example:

```json
{
  "narrative_report": "今天材料不多，但能看出孩子愿意用很轻的方式和小白狐互动。今晚家长不用追问具体聊了什么，可以给孩子一个轻松入口，让他说一件小事，不想说也没关系。",
  "tonight_parent_bridge": "今晚可以说：今天有没有一件想讲给我听的小事？不想说也没关系。",
  "avoid_followup": ["不要追问孩子和小白狐逐句聊了什么"]
}
```

Good image/share example:

```json
{
  "narrative_report": "今天孩子有用图片或作品来表达、展示的倾向。这更像是孩子想让别人看见自己做过或注意到的东西，家长可以给一个现实里的分享机会，但不需要追问具体是哪张图。",
  "tonight_parent_bridge": "今晚可以自然留个入口：今天有没有什么想给我看看，或者想讲给我听的小东西？",
  "avoid_followup": ["不要追问孩子具体给小白狐看了哪张图", "不要把所有图片都默认当成作业检查"]
}
```

Good learning example:

```json
{
  "narrative_report": "今天出现了一点学习或题目相关的求助线索。家长今晚可以先听孩子说题目大概在问什么，再陪他找第一步，不需要马上追问答案或替孩子完成。",
  "tonight_parent_bridge": "如果有题卡住，我们先看看题目在问什么，不急着一下做完。",
  "avoid_followup": ["不要直接追问最终答案", "不要替孩子把作业做完"]
}
```

Good safety/privacy example:

```json
{
  "narrative_report": "今天材料里出现了需要家长留意的边界信号。家长今晚适合保持平静，先确认孩子有没有需要大人帮忙的事；如果孩子不想马上说，不要逼问细节。",
  "tonight_parent_bridge": "如果今天有让你不舒服、需要大人帮忙的事，我在这里。",
  "avoid_followup": ["不要用审问语气追问细节", "不要让孩子觉得说出来会被责备"]
}
```

Bad examples to keep forbidden:

```text
今天孩子和小白狐聊了三件事……
孩子今天共有 5 条消息……
你今天给小白狐看的是什么？
小白狐发现孩子表达能力较好……
孩子表现不错……
```

---

## 4. Required fallback correction

The deterministic fallback currently still contains wording like:

```text
展示了一样自己画或拿给小白狐看的东西
今天孩子主要聊了...
```

This still has mild monitoring / child-Xiaobaihu-detail risk.

Revise fallback to be more parent-safe:

```text
If topics exist:
  narrative = "今天有一些轻量互动，主要围绕{topic_text}。这些只能作为大概线索，家长今晚不需要追问具体聊了什么。"

If show-and-tell exists:
  add: "材料里也出现了孩子想展示或分享东西的线索。"

If unfinished thread exists:
  add: "孩子最后可能转向了现实里的事情，适合尊重这个收尾。"
```

Avoid:

```text
拿给小白狐看的东西
孩子主要聊了...
```

Recommended wording:

```text
今天有一些轻量互动，主要围绕{topic_text}。这些只适合作为家长理解孩子状态的线索，不需要追问具体聊了什么。
```

---

## 5. Required `_is_stale()` correction

Update `_is_stale()` so new narrative reports are not always stale.

Current bad behavior:

```python
if not report.topic_overview or not report.conversation_summary:
    return True
```

New behavior:

```text
1. If report.generation_status != MODEL_GENERATED -> stale.
2. If report.summary is empty -> stale.
3. If material_fingerprint mismatches -> stale.
4. If latest material is newer than report.created_at -> stale.
5. Do not require topic_overview or conversation_summary for narrative v3.
```

Add a regression test.

---

## 6. Tests required

Add/adjust tests:

```text
1. test_narrative_report_with_empty_topic_overview_is_not_stale_when_fingerprint_matches
2. test_parent_report_prompt_lists_real_parent_concerns
3. test_parent_report_prompt_has_category_aware_examples
4. test_parent_report_prompt_forbids_child_quote_reconstruction
5. test_parent_report_fallback_does_not_say_taken_to_xiaobaohu
6. test_parent_report_fallback_frames_topics_as_state_clues_not_chat_log
7. test_parent_report_image_example_uses_open_family_invitation
8. test_parent_report_learning_example_scaffolds_first_step_not_answer
9. test_parent_report_safety_example_prioritizes_calm_adult_support
```

Run:

```bash
cd backend && pytest app/tests/test_parent_report_visible_quality.py app/tests/test_parent_report_service.py app/tests/test_show_and_tell_visible_quality.py
cd backend && ruff check .
```

---

## 7. Final report required

Report:

```text
1. commit sha;
2. files changed;
3. `_is_stale()` fix summary;
4. new parent-concern prompt framework;
5. before/after prompt snippets;
6. fallback wording before/after;
7. exact tests and results;
8. confirmation no Android/ASR/TTS/image upload/auth/navigation/mascot changes were made.
```
