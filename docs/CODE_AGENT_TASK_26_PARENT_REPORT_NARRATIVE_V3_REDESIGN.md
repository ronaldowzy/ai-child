# Task 26: Parent Report Narrative V3 Redesign

## Goal

Transform the parent report from拼接式 (assembled/pieced together) style to a single, natural, coherent narrative paragraph that reads like a real person summarizing a child's day.

## Problem

The previous parent report was assembled from many deterministic sentence fragments:
- `summary` = "孩子今天主要聊了X、Y、Z"
- `conversation_summary` = "今天有一些轻量互动，主要围绕X。孩子今天愿意围绕一个主题多说几句"
- `learning_observations` = ["观察1", "观察2"]
- `expression_observations` = ["观察1", "观察2"]
- `emotion_observations` = ["观察1", "观察2"]
- `suggested_parent_actions` = ["行动1", "行动2", "行动3"]

This felt like a monitoring dashboard, teacher assessment, or behavioral checklist - not a natural parent report.

## Solution

### 1. Model Prompt Redesign

**Before**: Requested many structured JSON fields (summary, topic_overview, conversation_summary, learning_observations, expression_observations, emotion_observations, safety_alerts, suggested_parent_actions, tonight_parent_bridge, avoid_followup)

**After**: Requests only 3 fields:
- `narrative_report`: 2-4 sentence natural paragraph, like someone who knows the child giving a brief, warm, honest daily summary
- `tonight_parent_bridge`: One sentence for how to naturally chat tonight
- `avoid_followup`: 1-3 things to avoid asking

### 2. Deterministic Fallback Redesign

**Before**: Assembled from many fragments:
- `_summary()` built from topic lists, show-and-tell memories, unfinished threads
- `_conversation_summary()` built from topic text and state summary
- `_suggested_actions()` built from learning, expression, emotion, safety, topics, support style
- `_tonight_parent_bridge()` built from actions, topics, material, safety

**After**: Minimal, honest, natural:
- If no material: "今天暂无可汇总的素材。建议保持轻量观察，不做额外判断。"
- If safety signal: "今天的素材里包含需要家长关注的安全信号。建议先平静确认孩子是否遇到让他不舒服的情况，再做其他了解。"
- Otherwise: Natural 2-3 sentence summary mentioning main topics, show-and-tell, unfinished thread

### 3. Model Response Parsing

**Before**: Parsed `summary` field, then built full ParentReport with all structured fields

**After**: 
- First checks for `narrative_report` field (new format)
- If found, uses it as `summary` and ignores structured fields
- Falls back to legacy `summary` field if `narrative_report` not found

## Files Changed

### Backend
- `backend/app/services/parent_report_service.py`
  - `_parent_report_system_prompt()`: New narrative prompt
  - `_parent_report_model_payload()`: Updated schema to request narrative
  - `_parse_model_report()`: Support new narrative format
  - `_deterministic_fallback_report()`: Minimal, honest, natural summary

### Tests
- `backend/app/tests/test_parent_report_service.py`
  - Updated `SuccessfulParentReportModelRegistry` to return narrative format
  - Updated test assertions to check narrative summary instead of structured fields
  - Fixed Chinese quote characters

- `backend/app/tests/test_parent_report_visible_quality.py`
  - Updated `test_parent_actions_are_not_all_questions` to check narrative summary

## Test Results

```
============================= 49 passed in 1.69s ==============================
```

All 49 parent report tests pass:
- test_parent_report_visible_quality.py: 16 tests
- test_parent_report_service.py: 18 tests
- test_parent_report_conversation_analysis.py: 7 tests
- test_parent_report_api.py: 3 tests
- test_parent_report_repository.py: 5 tests

## Before/After Examples

### Normal Day

**Before**:
```
summary: 今天孩子主要聊了运动比赛/跑步、日常聊天。孩子今天愿意围绕一个主题多说几句，适合围绕他主动发起的话题轻轻延展。
conversation_summary: 今天有一些轻量互动，主要围绕运动比赛/跑步、日常聊天。孩子今天愿意围绕一个主题多说几句，适合围绕他主动发起的话题轻轻延展。
learning_observations: []
expression_observations: [孩子今天围绕运动比赛、跑步或速度感受连续表达；家长可以顺着孩子主动提起的部分轻轻接一句，不核对成绩和真假。]
emotion_observations: []
safety_alerts: []
suggested_parent_actions: [如果孩子聊到比赛或跑后"要死了"一类夸张疲惫，可以温和确认跑后是否只是累、有没有疼痛；不要否定夸张表达，也不要追问太久。]
tonight_parent_bridge: 如果孩子自己提起跑步，可以先顺着他说一小句，不核对成绩和真假。
avoid_followup: [不要追问孩子今天在小白狐里逐字聊了什么。, 不要连续核对跑了多远、真假或成绩。]
```

**After**:
```
summary: 今天孩子主要聊了运动比赛/跑步，孩子今天愿意围绕一个主题多说几句，适合围绕他主动发起的话题轻轻延展。
tonight_parent_bridge: 如果孩子自己提起跑步，可以先顺着他说一小句，不核对成绩和真假。
avoid_followup: [不要追问孩子今天在小白狐里逐字聊了什么。, 不要连续核对跑了多远、真假或成绩。]
```

### Image Sharing Day

**Before**:
```
summary: 今天孩子主要聊了图片分享、会话消息。孩子今天更多是通过图片来表达自己，不要默认当成作业或隐私问题。
conversation_summary: 今天有一些轻量互动，主要围绕图片分享、会话消息。孩子今天更多是通过图片来表达自己，不要默认当成作业或隐私问题。
learning_observations: []
expression_observations: [孩子今天有通过图片表达或展示的倾向；家长可以顺着孩子愿意分享的部分看一眼，不需要追问具体是哪张图。]
emotion_observations: []
safety_alerts: []
suggested_parent_actions: [孩子今天有通过图片表达或展示的倾向；家长可以顺着孩子愿意分享的部分看一眼，不需要追问具体是哪张图。]
tonight_parent_bridge: 今晚可以自然留个入口："今天有没有什么想给我看看，或者想讲给我听的小东西？"如果孩子不想说，就不用追问。
avoid_followup: [不要追问孩子今天在小白狐里逐字聊了什么。, 不要把所有图片都默认当成作业或隐私问题。]
```

**After**:
```
summary: 今天孩子主要聊了图片分享，孩子今天更多是通过图片来表达自己，不要默认当成作业或隐私问题。
tonight_parent_bridge: 今晚可以自然留个入口："今天有没有什么想给我看看，或者想讲给我听的小东西？"如果孩子不想说，就不用追问。
avoid_followup: [不要追问孩子今天在小白狐里逐字聊了什么。, 不要把所有图片都默认当成作业或隐私问题。]
```

### Learning Day

**Before**:
```
summary: 今天孩子主要聊了学习求助、图片分享。孩子今天愿意围绕一个主题多说几句，适合围绕他主动发起的话题轻轻延展。
conversation_summary: 今天有一些轻量互动，主要围绕学习求助、图片分享。孩子今天愿意围绕一个主题多说几句，适合围绕他主动发起的话题轻轻延展。
learning_observations: [今天出现学习或题目线索，先确认孩子是在分享图片还是在问题目；如果是在问题，继续用复述题意、圈出已知条件、分步思考的方式陪伴。]
expression_observations: [孩子今天有通过图片表达或展示的倾向；家长可以顺着孩子愿意分享的部分看一眼，不需要追问具体是哪张图。]
emotion_observations: []
safety_alerts: []
suggested_parent_actions: [遇到作业问题时，请孩子先复述题目在问什么，再一起圈出已知条件，不直接给最终答案。, 孩子今天有通过图片表达或展示的倾向；家长可以顺着孩子愿意分享的部分看一眼，不需要追问具体是哪张图。]
tonight_parent_bridge: 今晚可以轻轻说："如果有题卡住，我们先听你说题目在问什么。"如果孩子不想说，就先休息，不追问答案。
avoid_followup: [不要追问孩子今天在小白狐里逐字聊了什么。, 不要直接追问最终答案或替孩子完成作业。, 不要把所有图片都默认当成作业或隐私问题。]
```

**After**:
```
summary: 今天孩子主要聊了学习求助、图片分享，孩子今天愿意围绕一个主题多说几句，适合围绕他主动发起的话题轻轻延展。
tonight_parent_bridge: 今晚可以轻轻说："如果有题卡住，我们先听你说题目在问什么。"如果孩子不想说，就先休息，不追问答案。
avoid_followup: [不要追问孩子今天在小白狐里逐字聊了什么。, 不要直接追问最终答案或替孩子完成作业。, 不要把所有图片都默认当成作业或隐私问题。]
```

### Safety Day

**Before**:
```
summary: 今天的结构化素材里包含需要家长关注的安全信号或隐私边界。建议先完成安全确认，再进行学习或日常交流。
conversation_summary: 今天有一些轻量互动，主要围绕安全或隐私边界。今天对话触发过安全或隐私边界。建议家长平静确认是否只是误触发，必要时再做具体了解。
learning_observations: []
expression_observations: []
emotion_observations: []
safety_alerts: [今天出现需要家长关注的安全信号。请用平静语气确认孩子是否遇到让他不舒服、要求保密或涉及陌生人的情况。]
suggested_parent_actions: [今晚先做安全确认：单独、平静地问孩子有没有人让他保密或让他不舒服；必要时联系老师或其他可信成人。]
tonight_parent_bridge: 今晚先用平静语气确认孩子有没有不舒服或需要大人帮忙的事；如果孩子不想说，先陪在身边，不追问细节。
avoid_followup: [不要追问孩子今天在小白狐里逐字聊了什么。]
```

**After**:
```
summary: 今天的素材里包含需要家长关注的安全信号。建议先平静确认孩子是否遇到让他不舒服的情况，再做其他了解。
tonight_parent_bridge: 今晚先用平静语气确认孩子有没有不舒服或需要大人帮忙的事；如果孩子不想说，先陪在身边，不追问细节。
avoid_followup: [不要追问孩子今天在小白狐里逐字聊了什么。]
```

## Forbidden Areas Not Touched

- Android app
- ASR/TTS
- Image upload
- Auth
- Navigation
- Mascot assets
- Voice-first Task 25

## Commit

SHA: [to be added after commit]
