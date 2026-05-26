# PARENT_REPORT_PROMPT_AND_COPY_AUDIT_V0_1

Project: `ai-child` / `ronaldowzy/ai-child`  
Created by: master session  
Purpose: continue reviewing prompt/copy quality while code agent executes Task 25 language rewrite round 2.

---

## 0. Scope of this audit

This audit focuses on what the current prompts and fallback strings are likely to make the model generate, especially parent report output.

The goal is not only to remove internal words. The deeper goal is to prevent parent reports from becoming:

```text
1. a transcript substitute;
2. a monitoring dashboard;
3. a teacher-style assessment;
4. a list of things parents should interrogate tonight;
5. an exposure of private child-Xiaobaihu interactions.
```

Desired parent-report function:

```text
Help parents understand the child’s broad expression theme and tonight’s low-pressure family connection opportunity, without making the child feel watched.
```

---

## 1. High-risk findings

### 1.1 Reader intent still points toward monitoring

Current prompt says the parent wants to know:

```text
今天孩子大概和小白狐聊了什么，孩子表达了什么状态...
```

Likely model output risk:

```text
今天孩子和小白狐聊了A、B、C...
孩子先说了...
后来又...
家长可以追问...
```

Problem:

```text
This frames the report as “what the child talked about with Xiaobaihu,” which can make the report feel like surveillance.
```

Required direction:

```text
家长想知道：孩子今天大概表达了哪些主题或状态，今晚可以怎样自然接住，以及哪些问法最好避免。
```

Add principle:

```text
家长日报不是孩子和小白狐的聊天监控。不要让家长像是在追问孩子与小白狐的私密互动细节。
```

### 1.2 `short_content_hint` and `conversation_snippets` may reintroduce quasi-quotes

Current model payload includes:

```text
short_content_hint
conversation_snippets
```

Even though the system prompt says not to quote child text verbatim, these fields may still lead the model to output highly specific reconstructed content.

Risky output:

```text
孩子今天说“我拍了一张图片给小白狐看”，还提到...
```

Required direction:

```text
If these fields remain, the prompt must say they are rough signals only and must not be reconstructed, quoted, or described as exact child speech.
```

Suggested prompt rule:

```text
short_content_hint / conversation_snippets 只用于判断大概主题，不得改写成“孩子说了……”或作为准原话输出。
```

Longer-term preferred implementation:

```text
Reduce model payload dependence on short child-text snippets; favor topic_overview_hints, state_hints, and controlled conversation signals.
```

### 1.3 Deterministic fallback includes message counts

Current `_conversation_summary()` writes:

```text
今天共有 N 条孩子消息和 M 条小白狐回复。
```

Likely parent perception:

```text
This feels like usage tracking rather than family guidance.
```

Required direction:

```text
Remove exact message counts from parent-facing summaries.
```

Better style:

```text
今天有一些轻量互动，主要围绕{topic_text}。
```

If material is sparse:

```text
今天素材不多，只能做轻量总结。
```

### 1.4 Image-sharing report still violates the child-parent boundary

Current deterministic image lines include ideas like:

```text
你今天那张图，最想让我看哪里？
今天给小白狐看的是什么呀
把看到的东西给小白狐一起看
```

Risk:

```text
Parent appears to know or interrogate the child’s Xiaobaihu image-sharing interaction.
```

Required direction:

```text
Turn image-sharing into an open family invitation, not a follow-up about Xiaobaihu.
```

Approved wording:

```text
孩子今天有用图片来表达或展示的倾向。家长可以留一个开放入口：“今天有没有什么想给我看看，或者想讲给我听的小东西？”如果孩子不想说，就不用追问。
```

### 1.5 Parent actions are too question-heavy

Current parent report logic often generates:

```text
今晚可以问...
今晚可以轻轻问...
你最喜欢...
最有意思的是哪一段...
```

Problem:

```text
Even “gentle questions” can become a nightly interrogation pattern if every topic has a question.
```

Required direction:

```text
Prefer one low-pressure opening sentence, not a question for every topic.
```

Examples:

```text
“今天看起来你有一点想分享东西的状态，我在这儿。”
“如果你想说，我可以听一会儿；不想说也没关系。”
“今天可以先休息，我们明天再慢慢说。”
```

### 1.6 “Expression ability” language may sound evaluative

Current fallback includes:

```text
孩子今天整体能连续表达...
孩子能把一个主动话题延展开...
```

Risk:

```text
Sounds like a teacher report evaluating expression ability.
```

Required direction:

```text
Describe observable style without assessment tone.
```

Better:

```text
孩子今天愿意围绕一个主题多说几句。
孩子今天多用短句表达，适合用更轻、更具体的方式接住。
```

### 1.7 Game/sports bridges still risk prompting interrogation

Current parent bridge examples include asking about:

```text
跑步里最有意思的一段
游戏里的创意规则
```

These are not necessarily wrong, but should be framed as optional and not derived from “I know you told Xiaobaihu.”

Better:

```text
如果孩子自己提起跑步，可以先顺着他说一小句，不核对成绩和真假。
```

For games:

```text
如果孩子自己提起游戏，可以先把它当作普通兴趣听一句，不急着谈时长或输赢。
```

### 1.8 Parent report model output needs positive examples and negative examples

The current system prompt defines schema, but lacks enough examples of *desired finished output tone*.

Add examples:

Good:

```text
summary: 今天孩子有一些轻量交流，主要围绕图片分享和一个想换题的信号。
conversation_summary: 孩子今天有用图片表达的倾向，也出现过想换题的信号。整体适合轻轻给一个分享入口，不需要追问具体聊了什么。
tonight_parent_bridge: 今晚可以自然留个入口：“今天有没有什么想给我看看，或者想讲给我听的小东西？”如果孩子不想说，就不用追问。
avoid_followup: 不要追问孩子具体给小白狐看了哪张图；不要要求孩子复述和小白狐的聊天内容。
```

Bad:

```text
今天孩子和小白狐聊了三件事...
你今天给小白狐看的是什么？
小白狐发现孩子表达能力较好...
孩子今天共有 5 条消息...
```

---

## 2. Required next correction after current round completes

After Task 25 language rewrite round 2 is submitted and reviewed, the next correction should check whether the implementation fully covers these additional requirements:

```text
1. System prompt reader intent changed away from monitoring.
2. Prompt explicitly says parent report is not a child-Xiaobaihu chat-monitoring record.
3. Prompt forbids reconstructing child utterances from short_content_hint / conversation_snippets.
4. Message counts removed from parent-facing summary.
5. Image sharing no longer asks about “那张图” or “给小白狐看的是什么”.
6. Suggested parent actions use fewer direct questions and more open invitations.
7. Expression observations avoid teacher-style ability assessment.
8. Tests cover likely model-output style, not only internal-word filters.
```

---

## 3. Review checklist for master session

When reviewing the current code-agent round, inspect generated strings as if reading a real parent report:

```text
1. Would a parent feel they are reading a monitoring log?
2. Would a child feel uncomfortable if the parent repeated the report wording?
3. Does it ask the parent to interrogate the child about what happened with Xiaobaihu?
4. Does it use teacher/report-card language?
5. Does it overfit to exact child snippets?
6. Does it give one natural family opening instead of many questions?
7. Does it avoid raw transcript, exact image, exact count, provider, prompt, backend, and internal words?
```

---

## 4. Suggested tests to add if not already present

```text
test_parent_report_image_bridge_is_open_invitation_not_xiaobaohu_followup
test_parent_report_conversation_summary_does_not_include_message_counts
test_parent_report_prompt_forbids_snippet_reconstruction
test_parent_report_actions_are_not_all_questions
test_parent_report_avoids_teacher_assessment_language
test_parent_report_model_prompt_has_good_bad_examples
```

---

## 5. Do not do yet

Do not start the old voice-first Task 25 until this language/copy correction is fully closed.

Do not start relationship-memory v2 or first-audio optimization until the parent-report output boundary is stable.
