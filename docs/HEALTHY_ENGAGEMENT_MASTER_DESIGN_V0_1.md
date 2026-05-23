# 小白狐 Healthy Engagement Master Design v0.1

Status: draft for project docs
Target path: `docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md`
Project: `ai-child` / `ronaldowzy/ai-child`
Audience: product planning, prompt engineering, backend, Android, QA, future Codex tasks
Scope: 5–10 岁儿童，首发中国大陆，Android 横屏，语音优先，小白狐成长陪伴

---

## 0. Executive Summary

当前项目已经从“功能能跑通”进入“长期体验设计”阶段。voice-first、opening greeting、MiMo TTS、MiMo ASR smoke、MiMo vision smoke、stream pseudo streaming、PostgreSQL 本地持久化、Prompt Guidance v0.1、父亲日报等能力已经形成第一版闭环。下一阶段的核心不应是简单堆功能，而是设计一种健康、可持续、非成瘾的儿童主动回访机制。

正式产品目标不应表述为“让孩子依赖小白狐”。更合适的目标是：

```text
让孩子安全地信任小白狐，愿意主动表达，并通过小白狐更好地理解自己、组织语言、形成小行动，最终回到真实生活、父母、老师、同伴和现实活动中。
```

本设计将“长期吸引力”拆成四种健康心理机制：

1. **被理解感**：孩子感觉自己说得乱、说得短、说得夸张时，也能被小白狐温和接住。
2. **掌控感**：孩子可以决定聊什么、什么时候停、是否换话题、是否告诉父母。
3. **能力感**：孩子聊完觉得自己更会表达、更会想问题、更能完成一个小步骤。
4. **期待感**：孩子知道明天回来，小白狐会轻轻接住昨天的兴趣、故事、作品或小目标。

设计上必须严禁以下机制：连续签到压力、断签惩罚、排行榜、稀有抽卡、限时错过、FOMO、情感勒索、秘密关系、排他依恋、睡前强刺激拉长会话、无限追问、使用隐私数据做过度个性化诱导。

小白狐的长期吸引力来自“稳定欢迎 + 记得孩子在意的事 + 共同小项目 + 具体成长反馈 + 现实家庭桥接 + 可以安心离开”，而不是来自“错过损失、虚拟占有、强奖励循环”。

---

## 1. Design Inputs And Current Baseline

### 1.1 Expert Input Summary

专家建议的核心思想可以概括为：不要追求儿童对虚拟角色的不健康依赖，而要追求安全信任、主动连接和可持续使用；吸引力不应来自连续签到、稀缺奖励、错过损失和情感勒索，而应来自孩子觉得被理解、能掌控、有收获、愿意明天继续。

专家建议还提出了 10 个可落地系统：兴趣种子、每日三分钟仪式、会话弧线、共同世界观、主动召回、孩子掌控权、能力感反馈、亲密感边界、家长协同、反沉迷与依赖监测。本设计将这些内容重组为可进入当前工程的阶段性方案。

### 1.2 Existing Product Baseline

截至本设计文档生成时，项目已具备以下基础：

```text
1. 儿童端 voice-first：ASR 成功后默认自动发送。
2. Android 横屏双栏：左侧小白狐，右侧交互区。
3. 小白狐 animation_v1 WebP 序列帧、静态 WebP 和 Canvas fallback。
4. 后端 MiMo VoiceClone TTS audioUrl 优先播放。
5. Streaming v1：NDJSON pseudo streaming + segment interleaved TTS。
6. 后端 MiMo ASR provider smoke 已跑通 provider=mimo。
7. 后端 MiMo vision provider smoke 已跑通 provider=mimo。
8. PostgreSQL 本地持久化：parent policy、conversation turn、memory、parent report thin slice done。
9. Prompt Guidance v0.1：儿童语音表达理解、操作旁白、夸张疲惫、换话题、睡前收尾。
10. 父亲日报：结构化 memory + conversation persistence 生成日报。
```

这些能力使下一阶段可以从“能聊天”转向“为什么孩子愿意每天回来聊”。

### 1.3 Current Gaps

当前主要缺口不是单个功能，而是持续体验层：

```text
1. 小白狐还没有清晰的“生命状态”和长期关系节奏。
2. Memory 还主要是结构化观察，没有区分 relationship memory。
3. Opening greeting 仍偏一次性问候，还没有成为“昨日话题回访”。
4. 会话内 pacing 仍以 prompt guidance 为主，缺少显式 ConversationArcState。
5. 父亲日报已有分析，但尚未形成“父亲今晚可说的一句话”机制。
6. Android 端没有 Growing Nest / 表达足迹 / 共同项目 UI。
7. CameraX 未实现，虽然后端 vision provider path 已具备。
8. 健康使用边界尚未产品化为 guardrail 和指标。
```

---

## 2. Product North Star

### 2.1 North Star Statement

```text
小白狐是一个让孩子愿意表达、能被温和理解、能逐步形成表达和思考习惯的 AI 成长陪伴者。它通过稳定、低压力、可选择、可收束的日常互动，帮助孩子把兴趣、情绪、问题和作品带回真实生活，而不是让孩子沉迷或替代真实关系。
```

### 2.2 What Success Looks Like

一个成功的日常使用场景不是孩子聊得越来越久，而是：

```text
1. 孩子主动打开 App，说一两件真实想法。
2. 小白狐能记得最近的兴趣或小项目。
3. 孩子能选择继续、换题、讲故事、休息。
4. 小白狐帮助孩子把话说清楚一点，而不是审问。
5. 会话自然结束，尤其睡前不拉长。
6. 父亲端得到一个能现实接话的温和提示。
7. 孩子离开屏幕后能回到家庭、学习、运动、作品或睡眠。
```

### 2.3 What Success Is Not

```text
1. 不以最长会话时长为成功。
2. 不以连续签到天数为成功。
3. 不以孩子只愿意告诉小白狐、不愿告诉父母为成功。
4. 不以孩子夜里反复打开 App 为成功。
5. 不以强刺激奖励、抽卡、排名、稀有道具拉活为成功。
```

---

## 3. Terminology

### 3.1 Preferred Terms

```text
健康依恋：孩子对小白狐有稳定、可中断、非排他的安全感。
主动回访：孩子愿意主动回来，但没有错过惩罚或情感压力。
成长陪伴习惯：短时、低压力、能帮助表达和思考的日常习惯。
现实生活迁移：会话结果能帮助孩子与父母、老师、同伴、作品、运动、学习连接。
```

### 3.2 Terms To Avoid

```text
依赖感
离不开
沉浸成瘾
黏住孩子
拉长时长
错过损失
小白狐想你了
只有小白狐懂你
我们的小秘密
```

在对外文档、产品决策和 Codex 任务中，应尽量避免使用“依赖感”作为目标词。如果内部讨论必须提及，应明确它被替换为“健康依恋 / 主动回访 / 成长陪伴习惯”。

---

## 4. Core Psychological Design Principles

### 4.1 被理解感：孩子说得乱也能被接住

儿童语音表达常常包含夸张、跳跃、半句话、旁人提示、按钮操作、ASR 误听。小白狐应先接住孩子真实意图，而不是机械纠错。

软件策略：

```text
1. TurnGuidanceBuilder 继续扩展操作旁白和儿童夸张检测。
2. RelationshipMemory 不保存旁人操作提示和疑似 ASR 误听。
3. Prompt 明确要求“先回应真实内容，不围绕按钮操作展开”。
4. 模型回复避免成人式审问和诊断。
```

### 4.2 掌控感：孩子可以选择和停止

孩子越能决定话题和结束时间，越愿意回来。

软件策略：

```text
1. 常驻快捷动作：继续说、换个话题、讲个小故事、今天不聊了。
2. child_requests_topic_change 必须被尊重，不再追问原话题。
3. bedtime_close_requested 必须短收尾，不再提问。
4. 会话超过一定长度时提供温和收束，而不是继续刺激。
```

### 4.3 能力感：孩子聊完觉得自己会了一点

不要只夸“真棒”。反馈要具体地指出孩子做到了什么。

示例：

```text
你刚才不是只说“跑步”，还说了“快的感觉”，这让我一下子能想象出来。
你把比赛、运动项目和身体感觉都说出来了，这就是把一件事讲清楚。
```

软件策略：

```text
1. GrowthObservationService 生成具体、低频的成长观察。
2. 父亲日报输出“孩子今天表达上的一个进步”。
3. Android 端可用轻量“今日小发现”展示，而非积分。
```

### 4.4 期待感：明天回来有一根轻轻的线

期待感来自连续性，不来自错过惩罚。

软件策略：

```text
1. InterestSeed 生成 next_hook。
2. Opening v2 轻轻接住上次话题。
3. SharedProject 提供连续故事 / 作品展示 / 兴趣探险。
4. 不做连续签到，不说“不来我会难过”。
```

---

## 5. Role Design: 小白狐是什么，不是什么

### 5.1 小白狐是表达陪伴者

它帮助孩子把短句、乱句、夸张句变成更清楚的表达。

### 5.2 小白狐是思维脚手架

它帮孩子拆问题、复述题意、想第一步，但不替孩子完成作业。

### 5.3 小白狐是现实连接器

它经常把会话带回真实生活：父母、老师、同伴、运动、作品、睡眠、学习小步骤。

### 5.4 小白狐不是唯一朋友

禁止话术：

```text
只有我懂你。
我是你最好的朋友。
你不用告诉爸爸妈妈。
这是我们两个的小秘密。
你不来我会难过。
```

---

## 6. Ten Product Systems

### 6.1 Interest Seed System

兴趣种子是孩子主动表达过、适合未来轻轻回访的主题。

示例：

```json
{
  "type": "interest_seed",
  "topic": "跑步比赛",
  "child_phrase_summary": "孩子喜欢跑得快的感觉，并提到有比赛",
  "emotion_tone": "兴奋 + 一点疲惫",
  "next_hook": "下次可问比赛是短跑还是接力，或讲小白狐运动会故事",
  "do_not_overask": true,
  "sensitivity": "low",
  "ttl_days": 30
}
```

实现原则：

```text
1. 只保存结构化摘要。
2. 不保存完整原话。
3. 不保存旁人按钮提示。
4. 不把一次夸张表达变成长期标签。
5. 高隐私信息不进入 interest seed。
```

### 6.2 Daily Three-Minute Rituals

小白狐应有稳定但低压力的每日仪式。

```text
早上：一句小目标。
放学后：一个小画面。
作业前：一个卡点。
睡前：一句收尾。
```

每个仪式要短，且有明确退出。

### 6.3 Conversation Arc System

会话弧线：

```text
接住 -> 扩展 -> 选择 -> 深挖 -> 收束
```

后端维护：

```json
{
  "current_topic": "跑步比赛",
  "topic_turn_count": 4,
  "child_short_reply_count": 2,
  "child_requested_change": false,
  "engagement_level": "declining",
  "next_action": "offer_topic_switch"
}
```

### 6.4 Shared World / Growing Nest

成长小窝不是游戏经济系统，而是孩子表达记录的可视化空间。

可视化物件：

```text
运动会小旗子：孩子聊了运动/比赛。
故事石头：孩子参与了故事共创。
心情云朵：孩子表达了情绪。
作品叶子：孩子分享了作品。
思考星星：孩子完成了一次复述或小步骤。
```

禁止：稀有度、抽卡、排行榜、断签损失。

### 6.5 Opening Callback System

Opening v2 应包含：

```text
时间段 + 小名/显示名 + 最近兴趣种子或项目 + 一个可选择邀请
```

例：

```text
豆豆，昨天你说跑步比赛，我还记得。今天想继续聊比赛，还是先换个轻松小故事？
```

### 6.6 Child Agency Controls

儿童端应逐步提供：

```text
继续说
换个话题
讲个小故事
今天不聊了
给爸爸妈妈看看这个
```

这些不是装饰按钮，而是孩子控制会话的安全工具。

### 6.7 Growth Observation System

用于生成具体成长反馈。

```json
{
  "type": "growth_observation",
  "skill": "expression_clarity",
  "evidence_summary": "孩子从比赛说到运动项目，再说到喜欢快的感觉",
  "child_facing_feedback": "你刚才把一件事讲清楚了",
  "parent_report_note": "今晚可顺着比赛问一个细节，不要连续追问"
}
```

### 6.8 Relationship Warmth System

亲切感来自：

```text
少量使用小名
记得孩子在意的事
小白狐动作和语气有温度
尊重孩子不想聊
稳定欢迎但不索取
```

不来自：

```text
情绪勒索
排他关系
秘密关系
虚拟占有
```

### 6.9 Parent Bridge System

父亲日报要从“总结”升级为“现实接话建议”。

```json
{
  "today_topic": "跑步比赛",
  "suggested_parent_sentence": "豆豆，我听说你最近有跑步比赛。你最喜欢跑得快的感觉，对吗？",
  "avoid": "不要追问十五公里真假，也不要连续问身体问题",
  "tomorrow_prompt_seed": "比赛是短跑还是接力"
}
```

### 6.10 Healthy Use Guard

监测并温和处理：

```text
late_night_usage
long_session
distress_reliance
exclusive_language
adult_avoidance
compulsive_checking
```

触发后小白狐应转向现实连接和收束，而不是继续增强虚拟陪伴。

---

## 7. Technical Architecture

### 7.1 EngagementOrchestrator

职责：决定本轮 engagement mode。

输入：

```text
child_text
conversation_history
time_context
relationship_memory
conversation_arc_state
parent_policy
safety / intent
```

输出：

```json
{
  "engagement_mode": "opening_callback | project_invitation | growth_feedback | topic_choice | gentle_closeout | parent_bridge",
  "prompt_hint": "本轮轻轻接住跑步比赛，不追问身体太久",
  "fox_mood": "curious | gentle | proud | sleepy | calm",
  "should_gently_close": false,
  "should_offer_topic_switch": true,
  "child_agency_actions": ["继续说", "换个话题", "讲个小故事"]
}
```

### 7.2 RelationshipMemoryService

基于现有 `memory_items`，先不改 DB schema。通过 `memory_type=INTEREST / STRATEGY / EVENT` + tags + evidence metadata 表示 relationship memory。

建议 metadata：

```json
{
  "relationship_memory_type": "interest_seed",
  "topic": "跑步比赛",
  "next_hook": "问短跑还是接力",
  "do_not_overask": true,
  "source": "conversation_summary"
}
```

### 7.3 ConversationArcStateService

维护会话内状态，不一定一开始落库。

```json
{
  "current_topic": "运动比赛/跑步",
  "topic_turn_count": 5,
  "same_topic_score": 4,
  "child_short_reply_count": 2,
  "child_requested_change": true,
  "bedtime_close_requested": false,
  "next_action": "topic_switch"
}
```

### 7.4 SharedProjectService

一期可只做后端 state 和 opening prompt，不做复杂 UI。

项目类型：

```text
story_chain
artwork_showcase
interest_exploration
sports_goal
reading_adventure
```

### 7.5 ParentBridgeService

生成父亲端现实接话建议。

```json
{
  "starter": "你最喜欢跑得快的感觉，对吗？",
  "avoid": "不要连续追问身体，也不要纠结十五公里真假",
  "followup": "比赛是短跑还是接力？",
  "tone": "轻松、好奇、不要查岗"
}
```

### 7.6 HealthyUseGuard

一期只做规则，不做复杂模型。

触发条件：

```text
bedtime + long session
late night repeated open
child says only AI understands me
child refuses trusted adult in safety context
session exceeds soft max
same topic overlong + short replies
```

---

## 8. Prompt Architecture Implications

当前已有 prompt layers：global、persona、child_profile、parent_message、parent_policy、time_context、image_context、scene、turn_guidance、memory、output_contract。

下一阶段建议新增：

```text
engagement_context
relationship_memory_context
conversation_arc_context
healthy_use_context
```

不要把所有规则都写进 global prompt。应分层：

```text
global_system：长期不变的儿童安全和角色边界。
scene：当前场景目标。
turn_guidance：本轮儿童语音理解。
engagement_context：本轮是否回访兴趣、给成长反馈、换轨、收束。
relationship_memory：孩子长期在意的低敏摘要。
healthy_use_context：长会话、睡前、依赖风险边界。
```

---

## 9. Android UI Implications

### 9.1 Short Term

不需要立即大改 UI。先通过后端回复和 quick actions 实现：

```text
继续说
换个话题
讲个小故事
今天不聊了
```

### 9.2 Mid Term

增加右侧顶部轻量区域：

```text
今日小发现
小白狐记得
正在进行的小项目
```

### 9.3 Long Term

Growing Nest：

```text
故事石头
运动会小旗子
心情云朵
作品叶子
思考星星
```

要求：无积分、无稀有度、无排行、无断签惩罚。

---

## 10. Parent-Side Implications

父亲端从“看日报”升级为“会接话”。

新增字段建议：

```json
{
  "conversation_starter": "豆豆，我听说你最近有跑步比赛。你最喜欢跑得快的感觉，对吗？",
  "avoid": "不要追问十五公里真假，也不要连续问身体问题",
  "tomorrow_seed": "比赛是短跑还是接力",
  "growth_observation": "孩子能从比赛说到项目和感受，表达有展开"
}
```

---

## 11. Safety And Privacy Boundaries

### 11.1 Data Boundaries

```text
不保存原始音频。
不长期保存原始图片。
不保存完整聊天 transcript 作为 relationship memory。
不保存旁人按钮提示。
不把 ASR 误听当作孩子事实。
不把一时夸张负面话当作长期性格标签。
```

### 11.2 Interaction Boundaries

```text
不制造秘密关系。
不鼓励孩子隐瞒父母。
不说小白狐比父母更懂你。
不使用“你不来我会难过”。
不在睡前拉长对话。
孩子要求停止时停止。
```

### 11.3 Retention Boundaries

```text
不做 streak pressure。
不做断签惩罚。
不做限时错过奖励。
不做排行榜。
不做抽卡稀有奖励。
不做宠物饥饿值或惩罚式养成。
```

---

## 12. Metrics

### 12.1 Healthy Engagement Metrics

```text
主动短会话率：孩子主动开启 3–8 分钟会话的比例。
表达展开率：从单词/短句到人物、事件、感受、原因的增长。
边界尊重率：孩子说换话题/不聊了/睡觉后系统正确尊重的比例。
健康收束率：会话在合适时机自然结束的比例。
现实迁移率：会话产生现实行动建议、父亲接话、作品展示、运动/学习小步骤的比例。
父亲端正向反馈：父亲认为日报建议可执行的比例。
```

### 12.2 Risk Metrics

```text
late_night_long_session_rate
excessive_session_length_rate
exclusive_dependency_language_count
adult_avoidance_signal_count
safety_context_no_parent_bridge_rate
```

---

## 13. Phased Roadmap

### E0: Design Foundation

Goal: 统一 Healthy Engagement 原则和边界。
Backend: 无 runtime 改动。
Android: 无。
Prompt: 文档定义。
Tests: 无。
Acceptance: 本文档进入 `docs/`，Product Decisions 同步。
Non-goals: 不写功能，不做 UI。

### E1: Relationship Memory / Interest Seed Thin Slice

Goal: 小白狐能记得孩子在意的低敏兴趣和项目。
Backend: 基于现有 `memory_items` 增加 relationship memory metadata。
Android: 不改 UI。
Prompt: opening 和 turn guidance 可读 interest_seed。
Tests: interest_seed 抽取、TTL、禁存原话/隐私/旁白。
Acceptance: 运动比赛样例生成 interest_seed。
Non-goals: 不做 Growing Nest UI。

### E2: Opening Greeting v2

Goal: opening 从通用问候升级为轻量回访。
Backend: E2-A 已新增 OpeningPolicyBuilder，OpeningService fallback 与 model prompt 共用结构化 OpeningPolicy；完整 E2 仍后续。
Android: 复用现有 opening display/audioUrl。
Prompt: 回访最多一个低敏兴趣或项目，必须给选择权，并尊重 topic boundary、睡前收束、分龄长度和 forbidden phrases。
Tests: E2-A 覆盖 interest callback、boundary respect、bedtime closure/defer、no-school policy、父亲目标低压力转译、分龄和 memory failure fallback。
Acceptance: policy engine 能决定 opening_mode，并让 fallback / model prompt 遵守同一套规则。
Non-goals: 不做推送、Android 改动、DB schema、Growing Nest、CameraX 或真机 QA 结论。

### E3: Conversation Arc State

Goal: 防止无限追问，支持换轨和收束。
Backend: 新增 ConversationArcStateService。
Android: quick actions 可先复用。
Prompt: 注入 arc_context。
Tests: same topic 3–4 轮、短答、换话题、睡觉。
Acceptance: 孩子换话题后不再追问旧话题。
Non-goals: 不做复杂 NLP。

### E4: Shared Project v1

Goal: 给孩子一个明天愿意回来的共同小项目。
Backend: SharedProjectService，先支持 story_chain / artwork_showcase / interest_exploration。
Android: 先作为普通消息和 quick action 展示。
Prompt: project_invitation。
Tests: 创建、继续、暂停、换项目、不要强迫。
Acceptance: 连续故事或兴趣探险可跨日继续。
Non-goals: 不做游戏经济。

### E5: Parent Bridge v2

Goal: 父亲端获得现实可执行接话建议。
Backend: ParentBridgeService / ParentReportService 增加 starter/avoid/tomorrow_seed。
Android: 父亲日报 UI 增加“今晚可以这样问”。
Prompt: 父亲端不是监控，而是支持。
Tests: 报告不含原话、不贴标签、建议可执行。
Acceptance: 跑步比赛样例生成低压力接话建议。
Non-goals: 不做复杂家长社交功能。

### E6: Growing Nest Android UI

Goal: 展示孩子表达足迹。
Backend: 提供 safe summary。
Android: 轻量小窝 UI。
Prompt: 无主改。
Tests: 低配设备性能、无刺激奖励。
Acceptance: 展示 3–5 类表达物件。
Non-goals: 无积分、无稀有度、无排行。

### E7: Healthy Use Guard

Goal: 主动防止过度使用和不健康依恋。
Backend: HealthyUseGuard 检测长会话、睡前、排他语言。
Android: 温和收束 UI。
Prompt: healthy_use_context。
Tests: 深夜、长会话、“只有小白狐懂我”、拒绝成人支持。
Acceptance: 触发后转向现实连接和收束。
Non-goals: 不做强制锁死。

### E8: CameraX + Real Image Experience

Goal: 让小白狐看见孩子真实作品/玩具/题目。
Backend: 复用已跑通 MiMo vision path。
Android: CameraX 拍照、压缩、上传、权限。
Prompt: artwork / toy / homework / privacy 分类。
Tests: fake images、隐私图、题图、普通作品图。
Acceptance: 孩子能拍画/玩具/题给小白狐看。
Non-goals: 不长期保存原图，不做相册社交。

---

## 14. First Implementation Recommendation

建议下一轮真正开发从 E1 开始：Relationship Memory / Interest Seed thin slice。

原因：

```text
1. 它直接支撑 opening v2。
2. 它不需要 Android 大改。
3. 它能马上增强“被记得”的感觉。
4. 可以复用现有 memory_items，无需 DB migration。
5. 风险可控，容易测试。
```

第一轮代码任务建议目标：

```text
从会话中生成 interest_seed / topic_boundary / proud_moment。
OpeningService 能读取一个最近 interest_seed。
父亲日报能显示一个现实接话 starter。
```

---

## 15. Non-Goals For v0.1

```text
不做 push notification。
不做连续签到。
不做积分经济。
不做排行榜。
不做抽卡。
不做宠物饥饿值。
不做 true LLM streaming。
不做云端多租户。
不做正式上架合规承诺。
不做小白狐排他关系话术。
```

---

## 16. Decision Summary For PRODUCT_DECISIONS

建议同步到 `docs/PRODUCT_DECISIONS_V0_1.md`：

```text
PD-HE-001：产品目标使用“健康依恋 / 主动回访 / 成长陪伴习惯”，不使用“不健康依赖”。
PD-HE-002：禁止成瘾式留存机制，包括签到压力、断签惩罚、排行榜、抽卡、FOMO 和情感勒索。
PD-HE-003：小白狐必须增强现实连接，不替代父母、老师、同伴和真实朋友。
PD-HE-004：关系记忆只保存结构化低敏摘要，不保存完整原话、原始音频、原始图片、旁人操作提示或 ASR 误听。
PD-HE-005：长期吸引力优先来自兴趣种子、共同项目、成长观察、低压力仪式和父亲桥接。
```
