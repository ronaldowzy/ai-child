# Experience Optimization Master Plan v0.1

Status: execution plan for family-beta experience optimization  
Target path: `docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md`  
Project: `ai-child` / `ronaldowzy/ai-child`  
Primary owner: project master session  
Implementer loop: Codex task sessions  
Initial date: 2026-05-24  
Scope: 5–10 岁儿童，首发中国大陆，Android 横屏，voice-first，小白狐成长陪伴，家庭内测前体验优化

---

## 0. Purpose

本文件是 `ai-child` 下一阶段体验优化的主执行计划。它不是新的产品设想集合，而是把已确认的产品方向、体验审计结论和工程任务拆成可持续执行的 Codex 循环。

后续每一轮修改都应以本文件为主计划，结合以下文档同步执行：

```text
docs/PRODUCT_DECISIONS_V0_1.md
docs/EXPERIENCE_REVIEW_AND_NEXT_OPTIMIZATION_GUIDE_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/NEXT_PHASE_PLAN_V0_2.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md
docs/LOCAL_ASR_SENSEVOICE_DESIGN_V0_1.md
docs/OPS_FOUNDATION_GAP_ANALYSIS_V0_1.md
```

本计划的目标是把当前“功能能跑通的 voice-first AI 聊天 App”升级为“儿童能理解、能掌控、能安全离开、能帮助亲子现实连接的小白狐成长陪伴系统”。

---

## 1. Current Baseline

### 1.1 当前已具备的主能力

截至本计划生成时，main 已具备以下基础能力：

```text
1. Android 横屏双栏：左侧小白狐，右侧聊天和输入。
2. 儿童默认 voice-first：隐藏文字输入框和发送按钮，录音后走后端 ASR，成功后自动发送。
3. 后端 ASR provider：local_sensevoice 主路径，MiMo ASR fallback，mock 保留。
4. Conversation stream：Android 默认优先走 /api/v1/conversation/stream，后端做安全回复后的 pseudo streaming。
5. TTS：后端 MiMo VoiceClone 生成小白狐 audio_url，Android 播放远程音频，不再用系统 TTS 混播儿童端自动朗读。
6. 小白狐 animation_v1：manifest-driven WebP 序列帧 + static WebP + Canvas fallback。
7. Universal image sharing：系统相机 / 相册真实图片上传，后端 vision / attachment，pending image context。
8. Freedom-first：默认 conversation.open，自由话题优先，安全/隐私/学习/睡前作为护栏。
9. Healthy Engagement 初版：禁止签到、FOMO、排行榜、抽卡、唯一朋友、秘密关系、排他依恋。
10. 父亲设置、父母寄语、孩子小名 / 显示名、父亲日报、ParentReport v2 model-first、本地 PostgreSQL thin slice。
11. Ops P0：request_id、JSON 日志、provider timing、health detail 等基础能力。
```

### 1.2 当前最关键体验差距

```text
1. Android 状态分散：ASR、stream、TTS、动画、按钮、图片处理没有统一 child-facing phase。
2. voice-first 模式下，儿童看不到足够明确的停止朗读/静音/打断能力。
3. 普通对话回复对 5–6 岁儿童偏长，且连续追问容易把自由表达变成访谈。
4. 小白狐视觉已接入，但还没有成为主要交互反馈主体。
5. 图片分享可以跑通，但第一句反馈模板化，缺少“被具体看见”的体验。
6. 父亲入口和父亲日报失败态仍有成人治理/开发工具感。
7. Healthy Engagement 主要是 prompt 和安全禁令，还没有足够可观测、可测试。
8. QA 仍偏工程 smoke，缺少儿童体验和亲子桥接验收。
```

---

## 2. Execution Model

### 2.1 主会话职责

主会话负责：

```text
1. 同步 GitHub main 最新状态。
2. 判断下一步优先级。
3. 生成给 Codex 的单轮任务提示语。
4. Codex 推送后，重新同步 main，审查 diff、文档、测试和产品一致性。
5. 判断是否接受该轮修改。
6. 更新本计划、progress board 或提出下一轮任务。
7. 保持儿童心理、教育目标、健康使用边界与软件实现一致。
```

主会话不直接把大任务一次性全部交给 Codex。每轮 Codex 只做一个可测试、可回滚、边界明确的任务。

### 2.2 Codex 单轮任务职责

每轮 Codex 必须：

```text
1. 先同步 main。
2. 阅读本计划、体验审计文档、PRODUCT_DECISIONS 和相关设计文档。
3. 检查相关代码，不得只改文档或只按猜测修改。
4. 严格区分：
   - 已实现代码
   - 文档规划
   - 真机 QA 待验
   - 本轮没有触碰的范围
5. 做最小可验证修改。
6. 增加或更新自动化测试。
7. 更新必要文档和 CODEX_PROGRESS_BOARD。
8. 提供测试命令和结果。
9. 不提交真实 key、真实儿童音频、真实儿童照片、DB dump、模型文件。
```

### 2.3 每轮验收门槛

每轮主会话验收时至少检查：

```text
1. 是否与 PRODUCT_DECISIONS confirmed/revised 冲突。
2. 是否破坏 voice-first、freedom-first、Healthy Engagement、数据最小化。
3. 是否增加了不适合儿童的留存/奖励/依赖机制。
4. 是否把文档规划误写成已实现事实。
5. 是否有自动化测试覆盖本轮核心逻辑。
6. 是否有真机 QA 待验标记。
7. 是否更新了 docs/CODEX_PROGRESS_BOARD_V0_1.md。
8. Android UI 修改是否仍适配横屏和低配设备。
9. 后端修改是否不绕过 SafetyEngine / ChildAgentRuntime / policy gate。
```

---

## 3. Priority Strategy

### 3.1 P0/P1 优先原则

下一阶段先做“体验地基”，不先做新功能。

优先顺序：

```text
P0-A Android 小白狐统一交互状态机。
P0-B voice-first 下儿童可见停止朗读/静音/打断能力。
P1-A 普通对话年龄分层与连续追问节制。
P1-B 图片分享具体反馈与临时缩略图。
P1-C 父亲入口视觉降噪与父亲日报家庭化失败态。
P1-D Healthy Engagement 可观测指标与 QA 回归。
```

### 3.2 暂缓方向

以下方向在 P0/P1 完成前暂缓：

```text
1. CameraX 自定义相机。
2. Growing Nest / 作品足迹 UI。
3. 复杂 3D 实时引擎。
4. hands-free 连续监听模式。
5. 账号系统和生产级鉴权。
6. 大规模新增场景。
```

### 3.3 禁止方向

任何阶段都不做：

```text
1. 排行榜、积分、抽卡、签到、断签惩罚、限时奖励、宠物饥饿值。
2. “小白狐想你了”“你不来我会难过”“只有小白狐懂你”。
3. 秘密关系、排他依恋、鼓励隐瞒父母。
4. 父亲日报展示逐字聊天记录。
5. 儿童端暴露 API key、provider、模型配置等工程细节。
6. 把普通图片分享默认路由成作业或隐私教育。
```

---

## 4. Phase Roadmap

## Phase 0：计划对齐与协同规则固化

### 目标

建立后续 Codex 循环的统一计划和验收方式。

### 任务

```text
0.1 新增本主计划文档。
0.2 在 CODEX_PROGRESS_BOARD 中加入 Experience Optimization 执行区。
0.3 如需要，在 PRODUCT_DECISIONS 中记录新的执行规则，而不是新的产品功能。
```

### 验收

```text
1. 文档进入 docs/。
2. 后续 Codex 任务均能引用本计划。
3. 主会话能够基于本计划逐轮验收。
```

---

## Phase 1：Android 小白狐统一交互状态机

### 产品目标

孩子不需要理解“ASR / stream / TTS / backend / audio segment”，只需要知道：

```text
小白狐准备好了。
小白狐在听。
小白狐在听懂。
小白狐在想。
小白狐在说。
小白狐在看图片。
小白狐没听清，可以再说。
可以停一下。
需要大人检查。
```

### 工程目标

新增或收敛一个 Android child-facing phase reducer，例如：

```text
ChildTurnUiPhase.Ready
ChildTurnUiPhase.Listening
ChildTurnUiPhase.Recognizing
ChildTurnUiPhase.Sending
ChildTurnUiPhase.Thinking
ChildTurnUiPhase.SpeakingPending
ChildTurnUiPhase.Speaking
ChildTurnUiPhase.ImageProcessing
ChildTurnUiPhase.NeedsRetry
ChildTurnUiPhase.Resting
ChildTurnUiPhase.ServiceError
```

所有可见文案、主按钮、辅助按钮、小白狐 animation、TTS 状态、stream 状态都从该 phase 派生。

### 关键文件

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/InputBar.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/chat/CartoonAgentView.kt
android/app/src/main/java/com/childai/companion/voice/*
```

### 验收

```text
1. 录音时：小白狐、主按钮、状态短语一致表达“我在听”。
2. 上传识别时：表达“我在听懂刚才的话”，不让孩子误以为还在录音。
3. 等模型时：表达“我想一想”，不显示空白等待。
4. 朗读时：表达“小白狐正在说”，可见停止。
5. 图片上传/识别时：表达“我在看这张图”。
6. 失败时：不责备孩子，给“再说一次 / 先不说 / 请大人检查”。
```

---

## Phase 2：voice-first 下 TTS 可打断与静音可见

### 产品目标

孩子必须有掌控权。自动朗读可以默认开启，但孩子要能马上停下。

### 工程目标

在 voice-first 模式下也显示低刺激 TTS 控制：

```text
1. TTS pending/speaking 时显示“停一下”。
2. 可选显示“先不朗读 / 打开朗读”。
3. 点击停止后清空 audio segment queue。
4. 停止后立即允许孩子按语音说话。
```

### 验收

```text
1. stream segment 播放中点击停止，不再继续后续 segment。
2. 远程音频失败时不 fallback 系统 TTS 混播。
3. voice-first 输入栏不再因为隐藏 text input 而隐藏停止/静音控制。
```

---

## Phase 3：普通对话年龄分层与追问节制

### 产品目标

小白狐应该帮助孩子表达，而不是无限采访孩子。

### 工程目标

把 age-band 从 opening 扩展到普通 conversation：

```text
age_5_6:
  - 30–80 中文字
  - 每轮最多一个很小的问题
  - 可以只接住不提问
  - 更依赖语音和动画

age_7_8:
  - 60–140 中文字
  - 每轮最多一个问题
  - 可引导原因或顺序

age_9_10:
  - 90–220 中文字
  - 可轻度计划、比较、复盘
  - 不做成人化报告
```

引入连续追问节制：

```text
1. 同一话题连续追问 2–3 轮后，下一轮优先反映、总结、给选择权或收束。
2. 孩子说“换个话题 / 不聊了 / 睡觉了”必须被尊重。
3. 纠错 turn 不应继续强推进。
```

### 关键文件

```text
backend/app/prompts/output_contracts/child_chat_v0_1.txt
backend/app/prompts/scenes/conversation_open_v0_1.txt
backend/app/prompts/global_system_v0_1.txt
backend/app/services/child_agent_runtime.py
backend/app/services/prompt_manager.py
backend/tests/**/*
```

### 验收

```text
1. age_5_6 普通回复明显短于当前默认。
2. age_7_8 保持自然但不过长。
3. age_9_10 可稍展开但仍语音友好。
4. “不聊了 / 睡觉了”不再抛新问题。
5. 连续追问计数有测试。
```

---

## Phase 4：图片分享“被具体看见”

### 产品目标

“拍给小白狐看”要让孩子感觉作品、玩具、生活观察被具体看见，而不是只收到上传模板。

### 工程目标

```text
1. Android 上传后显示本地临时缩略图或图片卡片。
2. 普通图片第一句用 recognized_content 中的一个安全具体细节。
3. 低置信或暗图不假装看清楚。
4. 作业图仍走学习 scaffold，不直接给答案。
5. 隐私图温和边界，但不把普通图片过度隐私化。
```

### 关键文件

```text
backend/app/services/modality_manager.py
backend/app/services/attachment_service.py
backend/app/services/prompt_manager.py
android/app/src/main/java/com/childai/companion/ui/chat/ChatViewModel.kt
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/data/attachment/*
```

### 验收

```text
1. 玩具/作品/生活图片：第一句含具体细节。
2. 暗图/模糊图：承认不清楚，让孩子补一句或重拍。
3. 题目图：引导题意，不给最终答案。
4. 后续“聊聊它 / 编个故事 / 问这是什么”仍带 attachment_id。
5. 不长期保存原图到不受控位置。
```

---

## Phase 5：父亲治理降噪与现实接话桥

### 产品目标

父亲治理要清晰但不侵入儿童端体验。父亲日报要帮助父亲现实接话，不是监控报告。

### 工程目标

```text
1. 儿童端父亲入口降噪：默认不再大字显示“父亲日报 / 父亲设置 / 长按进入”。
2. 普通点击只显示“这是给大人看的”。
3. 长按 + PIN 保留。
4. 父亲日报失败态家庭化，不在默认 UI 暴露后端/模型/provider。
5. 父亲日报顶部增加“今晚可以怎么接一句”。
6. 空素材日报提示父亲不要追问孩子。
```

Task 03 thin slice 状态：

```text
1. Android 儿童端默认父亲入口已收敛为小“大人”按钮；普通点击只提示，长按后选择父亲日报 / 父亲设置，并继续走 PIN。
2. ParentReport domain/API 增加兼容字段 tonight_parent_bridge；Android 父亲日报顶部显示“今晚可以怎么接一句”。
3. 失败态默认文案已家庭化，不展示 backend/model/provider/config。
4. 父亲日报仍是 model-first；模型失败不把规则日报冒充成功。
5. 这不是生产级账号/auth；Redmi K60 / Honor Pad 5 真机 QA 仍待验。
```

### 关键文件

```text
android/app/src/main/java/com/childai/companion/ui/chat/ChildChatScreen.kt
android/app/src/main/java/com/childai/companion/ui/parent/ParentReportScreen.kt
android/app/src/main/java/com/childai/companion/ui/parent/ParentReportViewModel.kt
backend/app/services/parent_report_service.py
backend/app/domain/parent_report.py
backend/tests/**/*
```

### 验收

```text
1. 儿童聊天主界面不被父亲入口抢注意力。
2. 父亲日报失败文案家庭可理解。
3. 开发诊断仍可记录 request_id / error_code，但默认折叠或仅开发模式可见。
4. 父亲日报不展示逐字聊天记录。
5. “今晚一句话”不评判孩子，不像监控。
```

---

## Phase 6：Healthy Engagement 可观测与 QA 回归

### 产品目标

Healthy Engagement 不只是一组 prompt 禁令，而是一组能被测试、观测和持续优化的系统指标。

### 工程目标

记录非内容指标：

```text
1. turn_index
2. active_scene
3. reply_char_count
4. question_count
5. same_topic_question_depth
6. boundary_signal: topic_change / no_chat / bedtime_close
7. boundary_respected
8. tts_segment_count
9. first_text_ms
10. first_audio_ms
11. turn_total_ms
12. quick_action_count
```

禁止记录：

```text
1. 完整儿童原文。
2. 完整模型回复。
3. 原始音频。
4. 原始照片。
5. API key / Authorization。
6. 父母寄语原文。
```

### 验收

```text
1. 能测试“换话题 / 不聊了 / 睡觉了”是否被尊重。
2. 能统计连续追问。
3. QA 模板包含 Healthy Engagement 字段。
4. 日志脱敏测试通过。
```

---

## Phase 7：家庭内测前总回归

### 目标

完成一轮真实设备体验验收，不把自动构建或 smoke 误写成真机体验通过。

### 必测设备

```text
Device A：Redmi K60 / Android 14，高配功能主验证。
Device B：Honor Pad 5 / Android 9 / 4GB 或等价低配横屏平板。
```

### 必测场景

```text
1. opening greeting。
2. 语音输入：开始说、说完了、没听清、重说、取消。
3. ASR 自动发送。
4. stream 文本渐进显示。
5. TTS 分段播放、停止、静音。
6. 小白狐状态切换。
7. 普通自由聊天。
8. 连续追问节制。
9. 换话题 / 不聊了 / 睡觉了。
10. 拍给小白狐看：普通图片、暗图、作业图、失败图。
11. 父亲入口：普通点击、长按、错误 PIN、正确 PIN。
12. 父亲日报：成功、生成中、失败、空素材。
13. 后端断开。
14. 本地 ASR 缺模型 / fallback。
15. TTS provider 失败。
```

---

## 5. Task Queue

### E0-01 Master Plan Document

Status: this document.

### E1-01 Android Unified Interaction State

Priority: P0  
Depends on: none  
Scope: Android UI state, voice, TTS, stream, fox state  
Expected outcome: child-facing phase reducer + visible consistent state

### E1-02 Child-visible TTS Stop/Mute in Voice-first

Priority: P0/P1  
Depends on: E1-01 preferred, can partially run in parallel  
Scope: InputBar + TTS queue + ChatViewModel  
Expected outcome: speaking can be stopped from voice-first UI

### E2-01 Age-banded Reply Contract

Priority: P1  
Depends on: E1-01 not required  
Scope: backend prompt/runtime/tests  
Expected outcome: age-aware reply length and question throttling

### E2-02 Conversation Arc Thin Slice

Priority: P1  
Depends on: E2-01  
Scope: backend turn guidance / runtime metadata / tests  
Expected outcome: continuous topic depth, boundary respected state

### E3-01 Image Specific First Response

Priority: P1  
Depends on: none  
Scope: backend modality manager / attachment / tests  
Expected outcome: specific, safe first response from recognized content

### E3-02 Android Image Thumbnail Card

Priority: P1/P2  
Depends on: E3-01 helpful  
Scope: Android photo payload / message rendering  
Expected outcome: local temporary thumbnail in chat

### E4-01 Parent Entry Deemphasis

Priority: P1  
Depends on: none  
Scope: Android ChildChatScreen  
Expected outcome: parent entry less intrusive but protected

### E4-02 Parent Report Family Bridge

Priority: P1  
Depends on: none  
Scope: ParentReport UI/backend  
Expected outcome: “今晚一句话” + family-facing failure state

### E5-01 Healthy Engagement Observability

Priority: P1/P2  
Depends on: E2-01 preferred  
Scope: backend logs + QA docs  
Expected outcome: measurable engagement boundaries without storing raw content

### E6-01 Family Beta QA Checklist

Priority: P1  
Depends on: phases 1–5 partial completion  
Scope: docs QA checklist  
Expected outcome: repeatable device QA script

---

## 6. Documentation Update Rules

每轮 Codex 完成后，至少判断是否需要更新：

```text
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/EXPERIENCE_OPTIMIZATION_MASTER_PLAN_V0_1.md
docs/VOICE_INTERACTION_DESIGN_V0_1.md
docs/STREAMING_INTERACTION_DESIGN_V0_1.md
docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md
docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md
docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md
android/README.md
backend/README.md
```

规则：

```text
1. 只把真正进入代码并通过测试的内容写为 done。
2. 真机未测必须写“待真机 QA”，不能写通过。
3. 设计方向但未实现写为 planned / proposed / next。
4. 产品决策变化必须先进入 PRODUCT_DECISIONS。
5. 不把临时 fallback 写成正式体验主路径。
```

---

## 7. First Codex Task Recommendation

第一轮建议交给 Codex：

```text
E1-01 Android Unified Interaction State
```

原因：

```text
1. 当前体验最底层的问题是状态分散。
2. 语音、TTS、stream、动画、图片和按钮都依赖这个状态机。
3. 先做状态机可以避免后续每个任务都继续各自修 UI。
4. 该任务主要在 Android 端，不改后端安全链路，风险可控。
```

第一轮 Codex 不应一次性改父亲日报、图片、prompt 和 Healthy Engagement。先把 Android child-facing phase 打牢。

---

## 8. Main Session Review Checklist For Each Codex Push

Codex 推送后，主会话按以下清单复核：

```text
1. 最新 commit sha 和 commit message。
2. 改动文件列表。
3. 是否越权修改非允许范围。
4. 是否增加不适合儿童的机制。
5. 是否破坏 voice-first 默认。
6. 是否仍可在 DevSettings 中保留调试能力。
7. 是否通过测试。
8. 是否有文档更新。
9. 是否有真机 QA 待验标记。
10. 是否可以进入下一轮，或需要返工。
```

---

## 9. Current Known Open Questions

```text
1. docs/EXPERIENCE_REVIEW_AND_NEXT_OPTIMIZATION_GUIDE_V0_1.md 是否已在 main 的 exact path 下可读。如果路径不同，需要同步文档索引。
2. 是否要在 CODEX_PROGRESS_BOARD 新增 Experience Optimization 分区，还是复用家庭内测前加固分区。
3. 父亲日报“今晚一句话”是否需要新增 schema 字段，还是先从 suggested_parent_actions 的第一项渲染。
4. Android unified phase 是否应完全替代现有 VoiceUiState/TtsUiState，还是先做 derived phase thin slice。
5. image thumbnail 是否可以只用 Android 本地临时 URI，不进后端长期库。
```

建议默认决策：

```text
1. 新增 Experience Optimization 分区。
2. 第一轮 unified phase 先做 derived phase thin slice，不大拆 VoiceUiState/TtsUiState。
3. 父亲日报“今晚一句话”先从 suggested_parent_actions 里提取或新增 optional 字段，避免破坏兼容。
4. 图片缩略图先只在 Android 本地短期显示，不进入长期 storage。
```

---

## 10. Execution Summary For Tasks 01-04

截至 Task 05 closeout，体验优化 Tasks 01-04 的代码状态如下：

```text
1. Task 01 Android unified interaction state：已完成 thin slice。ChildTurnUiPhase / ChildInteractionPresentation 统一派生小白狐状态、短状态文案、InputBar 主按钮、图片按钮和 TTS stop/mute 可见性；未声称真机通过。
2. Task 02 Parallel Experience Foundation：Lane A 已补 voice-first 下 TTS pending/speaking 的“停一下”和“静音/打开朗读”；Lane B 已补 backend age-banded replies 与连续追问 throttle thin slice。
3. Task 03 Image and Parent Bridge：Lane A 已补普通图片具体安全细节回复和 Android 本地缩略确认卡；Lane B 已补儿童端父亲入口降噪和父亲日报“今晚可以怎么接一句”。
4. Task 04 Healthy QA and State Coverage：已补 Healthy Engagement 非原文观测、家庭内测 QA checklist/runbook 和小白狐 phase/scene 状态覆盖矩阵。
```

Task 05 自动 closeout 结果：

```text
1. 后端 pytest / ruff、Android JVM test / assembleDebug、PostgreSQL smoke、mock synthetic trace 已通过。
2. real-provider synthetic trace 为 REVIEW_NEEDED：child_chat provider 链路可跑通，但 parent_report 一个场景 fallback，creative-share synthetic checker 标记 P2。
3. Stream TTS error payload 已去掉 stale `system_tts_or_text` wording，改为 text/audio unavailable 语义。
4. Healthy Engagement `boundary_respected` 已增强为会标记明显旧话题复活的 v0.1 heuristic。
5. Redmi K60 / Honor Pad 5 真机 QA 仍为 NOT_RUN；自动化通过不能替代儿童端体验验收。
```

## 11. End State For This Optimization Cycle

本轮体验优化完成时，应达到：

```text
1. 孩子知道小白狐现在是在听、想、说、看图、没听清还是需要大人检查。
2. 孩子能随时停下朗读、换话题、不聊、睡觉。
3. 小白狐回复更短、更分龄、更少追问。
4. 图片分享有具体“被看见”的反馈。
5. 父亲入口不抢儿童注意力。
6. 父亲日报能给父亲现实接话的一句话，不像监控。
7. Healthy Engagement 有日志和 QA 可验证。
8. Redmi K60 / Honor Pad 5 有明确真机结果。
```
