# Task 26 Correction: Parent Report Parent-Concerns Prompt v0.1

## Goal

Fix two issues discovered during Task 26 review:
1. `_is_stale()` bug causing narrative reports to be regenerated every time
2. Prompt too generic; needs to focus on real parent concerns

## Changes

### 1. Fix `_is_stale()` Bug

**Problem**: After narrative v3, `topic_overview=[]` and `conversation_summary=None`, but `_is_stale()` still required these fields to be non-empty (line 977):
```python
if not report.topic_overview or not report.conversation_summary:
    return True
```
This meant every narrative report was considered stale and regenerated on every request.

**Fix**: Change staleness check to use `summary` (which holds the narrative text) instead of `topic_overview`/`conversation_summary`:
```python
if not report.summary:
    return True
```

**Location**: `backend/app/services/parent_report_service.py` line 977

### 2. Strengthen Parent Report Prompt

**Problem**: Previous prompt was too generic — "孩子今天大概怎么样". Did not address specific parent concerns.

**New prompt framework** explicitly lists 7 parent concerns:
1. Child's overall state (happy, flat, tired, irritable, down)
2. Interests / confusions / emotions / needs expressed
3. Safety / privacy / boundary signals
4. Learning / homework blockers
5. Expression through images, works, toys, sports, games, stories
6. How to naturally open conversation tonight
7. What questioning styles to avoid

**Boundary additions**:
- Explicit: "不要暴露孩子和小白狐逐句聊了什么、具体给小白狐看了哪张图、孩子原话、消息数量"
- Explicit: "如果孩子通过图片、作品、玩具、运动、游戏或故事表达了什么，请提及这个表达倾向，但不要说具体是哪张图或哪个作品"

### 3. Fix Fallback Wording

**Problem**: Fallback still had monitoring-style phrases:
- "今天孩子主要聊了X" → monitoring feel
- "展示了一样自己画或拿给小白狐看的东西" → references specific interaction with 小白狐

**New wording**:
- "今天孩子在交流中提到了X" (more natural)
- "有通过图片或作品来表达的倾向" (expression tendency, not specific item)
- "最后有想去做别的事的信号" (signal, not action)
- Added disclaimer: "这些只适合作为家长理解孩子状态的线索，不需要追问具体聊了什么。"

## Before/After

### Prompt Before

```
你的读者是孩子的家长。家长想知道：孩子今天大概怎么样，有没有什么值得留意的信号，今晚可以怎么自然地和孩子聊几句。

家长日报不是孩子和小白狐的聊天监控。不要让家长像是在追问孩子与小白狐的私密互动细节。
不要把日报写成使用统计、老师评语、心理诊断、行为评分或家长盘问清单。
```

### Prompt After

```
你的读者是孩子的家长。家长真正关心的是：
  1. 孩子今天整体状态怎么样——开心、平淡、疲惫、烦躁、低落？
  2. 孩子今天有没有表现出什么兴趣、困惑、情绪或需要？
  3. 有没有安全/隐私/边界信号需要家长留意？
  4. 有没有学习/作业卡点，孩子是想求助还是只是随口提？
  5. 孩子今天有没有通过图片、作品、玩具、运动、游戏、故事等方式表达或展示什么？
  6. 今晚可以怎么自然地和孩子打开话题？
  7. 哪些问法今晚应该避免？

你的日报要围绕这些问题来写，但要用自然的段落，不要分点列举。

边界：
- 不要把日报写成聊天监控、使用统计、老师评语、心理诊断、行为评分或家长盘问清单。
- 不要暴露孩子和小白狐逐句聊了什么、具体给小白狐看了哪张图、孩子原话、消息数量。
```

### Fallback Before (normal day)

```
今天孩子主要聊了运动比赛/跑步，展示了一样自己画或拿给小白狐看的东西，最后说要去打卡或做别的事。
```

### Fallback After (normal day)

```
今天孩子在交流中提到了运动比赛/跑步，有通过图片或作品来表达的倾向，最后有想去做别的事的信号。这些只适合作为家长理解孩子状态的线索，不需要追问具体聊了什么。
```

## Files Changed

- `backend/app/services/parent_report_service.py`
  - `_is_stale()`: Changed from `topic_overview`/`conversation_summary` check to `summary` check
  - `_parent_report_system_prompt()`: Rewritten around 7 parent concerns
  - `_deterministic_fallback_report()`: Rewritten to remove monitoring-style phrases

## Forbidden Areas Not Touched

- Android app
- ASR/TTS
- Image upload
- Auth
- Navigation
- Mascot assets

## Commit

SHA: [to be added after commit]
