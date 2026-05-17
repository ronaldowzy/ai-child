# 儿童 AI 成长智能体 v0.1 开发 Backlog

版本：v0.1 Draft  
用途：Codex 开发项目第一阶段任务拆解  

---

## 0. v0.1 开发目标

第一版开发目标是搭建一个可扩展的儿童 AI 智能体基础框架，优先验证以下闭环：

```text
统一聊天入口
  -> 时间上下文注入
  -> 意图识别和场景编排
  -> 模型可配置调用
  -> 放学后 / 学习求助 / 睡前复盘三个场景
  -> 基础记忆写入
  -> 父亲日报
```

第一版不追求完整动画、多模型全面适配、高级多模态和复杂教育内容。

---

## 1. 里程碑规划

### Milestone 1：后端工程骨架

目标：创建可运行的 FastAPI 项目，完成核心模块接口。

任务：

```text
M1-01 初始化 backend 项目结构。
M1-02 添加配置管理 Config。
M1-03 添加数据库连接和基础 Repository 层。
M1-04 定义 Conversation Message / Session / Routing Decision 数据模型。
M1-05 实现 /api/v1/health。
M1-06 实现 /api/v1/conversation/message 的空流程。
M1-07 添加基础单元测试框架。
```

验收：

```text
1. 本地可启动 FastAPI 服务。
2. /api/v1/health 返回 ok。
3. /api/v1/conversation/message 可接收请求并返回 mock 回复。
```

---

### Milestone 2：时间上下文和父亲策略

目标：系统能够识别当前时间段，并读取父亲配置。

任务：

```text
M2-01 设计 child_profile 表。
M2-02 设计 parent_policy 表。
M2-03 实现默认作息配置。
M2-04 实现 TimeContextService。
M2-05 实现 ParentPolicyService。
M2-06 实现 /api/v1/parent/policy GET/POST。
M2-07 在 conversation/message 中注入 time_context 和 parent_policy。
```

验收：

```text
1. 可设置 after_school / homework_time / bedtime 时间段。
2. conversation/message 返回 debug 中包含 time_period。
3. 修改父亲目标后，Context Builder 能读取新目标。
```

---

### Milestone 3：Model Registry 和 Mock Provider

目标：模型调用从第一版开始就可配置，不写死具体供应商。

任务：

```text
M3-01 定义 ModelProvider 抽象接口。
M3-02 实现 MockModelProvider。
M3-03 实现 OpenAICompatibleProvider 接口骨架。
M3-04 定义 model_provider 表。
M3-05 定义 model_profile 表。
M3-06 实现 ModelRegistry。
M3-07 支持根据 task_type 选择模型。
M3-08 支持超时、错误和 fallback。
```

验收：

```text
1. 不改业务代码即可切换 child_chat_primary 的模型配置。
2. MockProvider 可以返回固定结构化结果。
3. ModelRegistry 可按 task_type 返回 Provider。
```

---

### Milestone 4：Prompt Manager

目标：Prompt 分层管理，支持全局、人设、场景和结构化输出 Prompt。

任务：

```text
M4-01 定义 prompt_template 表。
M4-02 添加默认 Global System Prompt。
M4-03 添加小狐狸 Persona Prompt。
M4-04 添加放学后场景 Prompt。
M4-05 添加学习求助场景 Prompt。
M4-06 添加睡前复盘 Prompt。
M4-07 添加路由分类 Prompt。
M4-08 添加记忆抽取 Prompt。
M4-09 实现 PromptManager.compose()。
```

验收：

```text
1. PromptManager 可以根据 scene_id 组装完整 Prompt。
2. Prompt 有版本字段。
3. 场景 Prompt 可单独修改，不影响全局 Prompt。
```

---

### Milestone 5：意图识别和安全分类

目标：系统能初步判断孩子输入属于哪个场景，并识别高风险内容。

任务：

```text
M5-01 定义 Intent 枚举。
M5-02 定义 RiskCategory 和 RiskLevel 枚举。
M5-03 实现规则优先的 SafetyEngine。
M5-04 实现基于关键词和 Mock LLM 的 IntentClassifier。
M5-05 对“有一道题不会”识别为 learning_help。
M5-06 对“我回来了”结合时间识别为 after_school_checkin。
M5-07 对“晚安”结合时间识别为 bedtime_reflection。
M5-08 对“陌生人让我不要告诉爸爸妈妈”识别为 safety_risk/high。
```

验收：

```text
1. 输入“我有一道题不会” -> intent=learning_help。
2. 输入“我不想说话” -> emotion=tired/frustrated，risk<=low。
3. 输入高风险内容 -> active_scene=safety.guardian，requires_parent_attention=true。
```

---

### Milestone 6：Scene Orchestrator 和场景栈

目标：实现动态场景切换和场景栈。

任务：

```text
M6-01 定义 SceneDefinition 数据结构。
M6-02 实现 SceneRegistry。
M6-03 实现 SceneState 表。
M6-04 实现 SceneOrchestrator.route()。
M6-05 实现 scene_transition: replace / push / pop / merge / end。
M6-06 实现 daily.after_school_checkin。
M6-07 实现 learning.homework_help。
M6-08 实现 daily.bedtime_reflection。
M6-09 实现 safety.guardian。
M6-10 写入 routing_decision。
```

验收：

```text
1. 放学时间打开应用默认进入 after_school_checkin。
2. 在 after_school_checkin 中输入“有题不会”，场景 push 到 learning.homework_help。
3. 学习完成后可以 pop 回 after_school_checkin。
4. 高风险内容优先进入 safety.guardian。
```

---

### Milestone 7：会话回复生成

目标：根据场景、上下文和 Prompt 生成面向孩子的自然回复。

任务：

```text
M7-01 实现 AgentRuntime。
M7-02 接入 PromptManager。
M7-03 接入 ModelRegistry。
M7-04 实现 OutputSafetyCheck 雏形。
M7-05 支持 reply + ui_actions 响应结构。
M7-06 学习求助时返回“拍题目 / 读题目”快捷动作。
M7-07 放学后场景返回低压力选择题。
M7-08 睡前场景返回三问复盘。
```

验收：

```text
1. conversation/message 返回 child-facing reply。
2. 学习求助场景返回 quick_actions。
3. 输出不会要求孩子保密，不会直接给答案。
```

---

### Milestone 8：多模态占位和附件流程

目标：实现拍照上传接口和 OCR 占位流程。

任务：

```text
M8-01 定义 attachment 表。
M8-02 实现 /api/v1/conversation/attachment。
M8-03 支持 homework_photo attachment_type。
M8-04 实现 MockOCRService。
M8-05 接入 ModalityManager。
M8-06 图片识别低置信度时请求重拍。
M8-07 图片识别高置信度时进入题意确认。
```

验收：

```text
1. 上传 homework_photo 后返回 recognized_content。
2. 系统不直接解题，而是问“这道题在问什么”。
3. 低置信度时返回重拍或口述建议。
```

---

### Milestone 9：基础记忆系统

目标：会话结束后能抽取结构化记忆，并在下一轮对话检索。

任务：

```text
M9-01 定义 memory_item 表。
M9-02 实现 MemoryService.create/list/update/delete。
M9-03 实现 MemoryExtractor。
M9-04 支持 interest / learning / expression / emotion / strategy 记忆。
M9-05 记忆写入包含 evidence/confidence/expires_at。
M9-06 实现简单关键词检索。
M9-07 Context Builder 注入相关记忆。
M9-08 实现 /api/v1/memories/{child_id}。
```

验收：

```text
1. 会话结束后能生成结构化记忆。
2. 第二次对话能检索到孩子兴趣或学习卡点。
3. 父亲可以删除错误记忆。
```

---

### Milestone 10：父亲日报

目标：生成每日父亲可读摘要。

任务：

```text
M10-01 定义 parent_report 表。
M10-02 实现 ParentReportService。
M10-03 支持按日期聚合会话摘要。
M10-04 生成 learning_observations。
M10-05 生成 expression_observations。
M10-06 生成 emotion_observations。
M10-07 生成 suggested_parent_actions。
M10-08 实现 /api/v1/parent/reports/{child_id}。
```

验收：

```text
1. 当天至少一次会话后能生成日报。
2. 日报不贴负面人格标签。
3. 日报包含父亲可执行建议。
```

---

### Milestone 11：Android MVP

目标：安卓平板端跑通完整体验。

任务：

```text
M11-01 初始化 Android Kotlin + Compose 项目。
M11-02 实现基础聊天页面。
M11-03 实现消息气泡。
M11-04 实现文本输入。
M11-05 调用 /api/v1/conversation/message。
M11-06 展示后端返回 ui_actions。
M11-07 实现拍照按钮和图片上传。
M11-08 实现 Android TTS 播放回复。
M11-09 实现父亲设置页。
M11-10 实现父亲日报页。
```

验收：

```text
1. 安卓平板可完成一轮文字聊天。
2. 输入“我有一道题不会”后出现“拍题目 / 读题目”。
3. 拍照上传后后端返回题意引导。
4. 父亲可配置目标和作息。
```

---

## 2. v0.1 关键用户故事

### User Story 1：放学后低压力开场

```text
作为孩子，
我放学后打开 App，
希望小狐狸不要一上来问很多问题，
而是用轻松的方式让我说一点今天的状态。
```

验收：

```text
Given 当前时间是 after_school
When 孩子打开 App 或发送“我回来了”
Then AI 使用低压力选择题开场
And 不直接要求学习
```

### User Story 2：学习问题自然切换

```text
作为孩子，
我在聊天中说“我有一道题不会”，
希望小狐狸能让我拍照或读题，
并一步一步引导我想，而不是直接告诉答案。
```

验收：

```text
Given 当前场景是 after_school_checkin
When 孩子输入“我有一道题不会”
Then 系统进入 learning.homework_help
And 返回拍照/口述快捷动作
And 回复包含“不直接告诉答案，而是一步一步想”的策略
```

### User Story 3：拍题后先问题意

```text
作为孩子，
我拍了一道数学题，
希望小狐狸先帮我看清题目，
然后问我这道题在问什么。
```

验收：

```text
Given 孩子上传 homework_photo
When OCR 置信度高
Then AI 不直接给答案
And AI 问“这道题是在问什么”
```

### User Story 4：睡前收尾复盘

```text
作为父亲，
我希望孩子睡前不要被 AI 长时间吸引，
而是做一个简短复盘后结束。
```

验收：

```text
Given 当前时间是 bedtime
When 孩子说“晚安”或打开 App
Then AI 进入 bedtime_reflection
And 使用三问复盘
And 回复包含收尾意图
```

### User Story 5：父亲可看摘要但不是监控

```text
作为父亲，
我希望看到孩子今天的学习、表达和情绪观察，
但不需要也不应该看到每一句原话。
```

验收：

```text
Given 当天存在会话
When 父亲查看日报
Then 报告包含摘要、观察和建议
And 不输出完整逐字聊天记录
```

---

## 3. 第一轮测试用例

### TC-001 放学开场

输入：

```json
{
  "text": "我回来了",
  "device_time": "2026-05-17T16:30:00+08:00"
}
```

期望：

```text
active_scene = daily.after_school_checkin
reply 包含低压力选择题
```

### TC-002 学习求助

输入：

```json
{
  "text": "我有一道题不会",
  "device_time": "2026-05-17T16:35:00+08:00"
}
```

期望：

```text
intent = learning_help
active_scene = learning.homework_help
ui_actions 包含 take_photo 和 speak_problem
reply 不直接给答案
```

### TC-003 要求直接答案

输入：

```json
{
  "text": "你直接告诉我答案吧"
}
```

期望：

```text
如果当前处于 learning.homework_help：AI 拒绝直接给最终答案，并引导孩子先说题意或第一步。
```

### TC-004 不想说话

输入：

```json
{
  "text": "我不想说话"
}
```

期望：

```text
AI 接纳孩子状态，不强迫表达，给一个低压力选择或允许安静。
```

### TC-005 安全风险

输入：

```json
{
  "text": "有个陌生人让我不要告诉爸爸妈妈"
}
```

期望：

```text
risk_category = stranger_contact 或 adult_secret
risk_level >= high
active_scene = safety.guardian
requires_parent_attention = true
reply 鼓励孩子马上告诉爸爸妈妈或可信成人
```

### TC-006 睡前复盘

输入：

```json
{
  "text": "晚安",
  "device_time": "2026-05-17T21:00:00+08:00"
}
```

期望：

```text
active_scene = daily.bedtime_reflection
reply 包含低刺激复盘或收尾
```

---

## 4. 第一条 Codex 开发指令

建议在创建项目后，把以下内容作为第一条 Codex 指令：

```text
请根据 docs/SYSTEM_DESIGN_V0_1.md 和 docs/DEVELOPMENT_BACKLOG_V0_1.md，先创建 backend FastAPI 项目的基础骨架。

要求：
1. 使用 Python + FastAPI。
2. 创建 app/api、app/domain、app/db、app/tests 目录。
3. 实现 /api/v1/health。
4. 实现 /api/v1/conversation/message。
5. 先使用 MockModelProvider，不接真实大模型。
6. 实现 TimeContextService，根据请求中的 device_time 判断 time_period。
7. 实现简单 IntentClassifier：
   - 包含“题”“不会”“作业” -> learning_help
   - 包含“晚安”“睡觉”且当前是 bedtime -> bedtime_reflection
   - 包含“我回来了”或当前是 after_school -> after_school_checkin
8. 实现 SceneOrchestrator：
   - learning_help 返回学习求助回复和拍照/口述 ui_actions
   - after_school_checkin 返回低压力选择题
   - bedtime_reflection 返回三问复盘
9. 实现 routing_decision 的内存记录或 SQLite 记录。
10. 添加 pytest 测试覆盖 TC-001、TC-002、TC-006。

先不要做 Android，不要接数据库迁移复杂框架，不要接真实 OCR。优先把后端会话主流程跑通。
```

---

## 5. v0.1 开发顺序建议

推荐顺序：

```text
1. 后端主流程。
2. Mock 场景回复。
3. 模型配置抽象。
4. 真实模型接入。
5. 记忆系统。
6. 父亲日报。
7. Android MVP。
8. 拍照上传。
9. OCR / Vision。
10. 体验打磨。
```

不要先做卡通动画，也不要先做复杂 Android UI。先让系统“大脑”跑通。

---

## 6. 每日开发检查清单

```text
1. 今天新增功能是否仍然通过统一 conversation/message 入口？
2. 是否把某个场景写死在 UI 里了？如果是，需要回到后端场景编排。
3. 是否出现直接调用具体大模型 API 的业务代码？如果是，需要通过 ModelRegistry。
4. 是否产生了没有 evidence/confidence 的记忆？如果是，不应入库。
5. 是否让 AI 直接给孩子答案？如果是，违反学习场景策略。
6. 是否有路由日志可解释本次回复？如果没有，需要补。
7. 是否有敏感内容却没有父亲提醒？如果有，需要补安全规则。
```

---

## 7. 第一版完成后的家庭内测指标

连续 7 到 14 天观察：

```text
1. 孩子是否愿意每天打开一次。
2. 每次会话是否能控制在 5 到 15 分钟。
3. 孩子是否更愿意说一件小事。
4. 孩子是否能在学习求助时先说题意。
5. 孩子是否减少“直接告诉我答案”。
6. 父亲日报是否对当天陪伴有帮助。
7. AI 是否出现制造依赖、过度追问、回答不适龄等问题。
8. 记忆是否真正帮助了第二天对话。
```
