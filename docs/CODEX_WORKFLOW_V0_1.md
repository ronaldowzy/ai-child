# Codex 开发工作模式与进度安排 v0.1

版本：v0.1 Draft  
用途：作为 Codex 开发项目的执行手册、协作规范和阶段计划  
适用范围：儿童 AI 成长智能体 v0.1，从空仓库启动，到后端 MVP、Android MVP、端到端家庭内测版本  
关联文档：

```text
docs/SYSTEM_DESIGN_V0_1.md
docs/DEVELOPMENT_BACKLOG_V0_1.md
docs/CODEX_TASK_PROMPTS_V0_1.md
docs/CODEX_PROGRESS_BOARD_V0_1.md
docs/CODEX_PLAN_TEMPLATE.md
docs/session_process/SHARED_CONTEXT_V0_1.md
AGENTS.md
```

---

## 0. 文档目标

本文档回答四个问题：

```text
1. Codex 应该以什么工作方式参与本项目？
2. 第一版项目应该按什么开发顺序推进？
3. 每个阶段应该让 Codex 做什么、不要做什么、产出什么？
4. 如何通过任务拆分、测试、审查和文档更新，让 Codex 能稳定连续开发？
```

本项目不是一次性脚本开发，而是一个需要长期迭代的儿童 AI 智能体产品。因此，Codex 不能被当成“随手写代码工具”，而应该被当成一个可持续协作的工程队友：

```text
父亲 / 开发者：产品负责人 + 架构负责人 + 最终代码审查人。
Codex：按任务执行设计、编码、测试、文档更新和局部重构。
GitHub：任务、分支、PR、Review 和发布记录的事实来源。
文档：系统设计、开发顺序、工程约束和验收标准的事实来源。
```

第一版最高原则：

```text
先跑通安全可控的后端智能体主流程，再做 Android 端完整体验；
先用 Mock 模型和 Mock OCR 验证架构，再接真实模型；
先做动态场景编排和记忆闭环，再做丰富动画和复杂多模态；
每一步都要有测试、验收和可回滚边界。
```

---

## 1. Codex 在本项目中的角色定位

### 1.1 Codex 不是产品决策者

Codex 可以：

```text
1. 根据文档实现代码。
2. 根据现有代码补充测试。
3. 根据错误日志定位 bug。
4. 根据模块边界做小范围重构。
5. 根据接口设计生成数据模型、API、服务类和测试。
6. 根据父亲确认后的方案更新文档。
```

Codex 不应该擅自：

```text
1. 改变儿童产品原则。
2. 放宽儿童安全策略。
3. 把学习引导改成直接给答案。
4. 引入开放式无限聊天。
5. 引入广告、社交、排行榜、上瘾式游戏化。
6. 引入未经确认的真实大模型服务。
7. 把 API Key、儿童真实数据或家庭信息写入代码库。
8. 未经确认重写核心架构。
```

### 1.2 Codex 应该优先做“工程闭环”

每次 Codex 接任务，都必须完成这个闭环：

```text
理解任务
  -> 读取共享上下文并运行环境 doctor
  -> 列出计划
  -> 实现最小变更
  -> 添加或更新测试
  -> 运行相关测试
  -> 自查 diff
  -> 更新必要文档
  -> 对大改或已通过测试的完整任务及时 git commit
  -> 需要同步远端时及时 git push
  -> 给出结果摘要和后续建议
```

禁止的工作方式：

```text
1. 大段实现但不测试。
2. 同时改多个无关模块。
3. 为了通过测试而删除测试。
4. 为了省事跳过安全逻辑。
5. 遇到不确定点时自行引入复杂依赖。
6. 未说明原因就改变 API 结构。
7. 把已知环境问题重复误报为新的机器阻塞。
8. 完成大改并通过测试后只停在本地未提交工作区。
```

### 1.3 Git closeout gate

完成以下任一情况时，Codex 必须在最终汇报前处理 Git 收口：

```text
1. 修改跨多个模块或超过单文件小修。
2. 新增/修改 API、schema、数据库、Prompt、Android UI 或产品文档。
3. 已运行并通过相关测试，任务已经形成可回滚的完整变更。
4. 父亲 / 产品负责人明确要求提交或推送。
```

收口规则：

```text
1. 先运行 git status --short，确认变更范围。
2. 运行相关测试和 git diff --check；不能运行时说明原因。
3. 做 secret 扫描，确认没有真实 API key、儿童真实身份、真实照片或原始音频。
4. 使用清晰 commit message 提交本地 git。
5. 如果当前流程是直接进 main，并且父亲没有要求暂缓，提交后推送 origin/main。
6. 最终回复必须说明 commit hash、是否已 push、测试结果和仍需手动 QA 的事项。
```

例外：

```text
1. 用户明确要求“先不要提交”。
2. 测试失败且尚未确认是否保留变更。
3. 变更中包含待用户确认的产品方向或高风险数据策略。
4. 工作区包含不属于本任务且会被误提交的未跟踪/未提交改动；此时先报告并拆分处理。
```

---

## 2. 推荐 Codex 使用界面与分工

### 2.1 Codex Web / Cloud

适合：

```text
1. 独立 Milestone 或独立 Issue。
2. 后端模块实现。
3. 测试补充。
4. 文档更新。
5. 可通过 PR 审查的任务。
```

推荐使用方式：

```text
1. 每个任务一个 GitHub Issue。
2. 每个 Issue 派生一个 Codex Cloud 任务。
3. 每个任务对应一个分支和一个 PR。
4. 任务 prompt 必须包含 Goal / Context / Constraints / Done when。
5. Codex 完成后，父亲先看 PR 摘要，再看 diff，再运行关键测试。
```

适合并行的任务：

```text
1. 文档类任务。
2. 只新增独立模块的任务。
3. 只新增测试的任务。
4. 后端和 Android 两端互不冲突的任务。
```

不适合并行的任务：

```text
1. 同时修改核心数据模型。
2. 同时修改统一会话 API。
3. 同时修改 SceneOrchestrator。
4. 同时修改 PromptManager 的公共接口。
5. 同时做数据库迁移和 API 返回结构调整。
```

### 2.2 Codex CLI

适合：

```text
1. 本地连续调试。
2. 跑测试、看错误、修复 bug。
3. 小范围重构。
4. 生成本地脚本。
5. 对某个目录做代码解释。
```

推荐使用方式：

```text
1. 在仓库根目录启动。
2. 每次任务前说明要改的文件范围。
3. 对 bug 修复，先给复现步骤，再要求 Codex 复现。
4. 修改完成后要求 Codex 运行最小相关测试。
5. 对复杂任务，先让 Codex 生成 plan，不要马上写代码。
```

### 2.3 Codex IDE Extension

适合：

```text
1. 查看当前文件上下文。
2. 解释某个类、函数或请求链路。
3. 快速补充单测。
4. Android UI 微调。
5. 局部代码审查。
```

推荐使用方式：

```text
1. 打开相关文件后再发任务。
2. 选择具体函数或类作为上下文。
3. 一次只让 Codex 改一个文件组。
4. UI 微调时使用小步迭代。
```

### 2.4 GitHub PR Review with Codex

适合：

```text
1. 每个 PR 合并前做第二视角审查。
2. 特别关注儿童数据、隐私、安全策略、API 破坏性变更。
3. 发现 P0/P1 级问题后，让 Codex 在同一 PR 内修复。
```

建议在 PR 评论中使用：

```text
@codex review for security regressions, child-data privacy risks, API compatibility, missing tests, and violations of docs/AGENTS.md.
```

---

## 3. 仓库初始化建议

### 3.1 推荐仓库结构

第一版建议使用单仓库 monorepo：

```text
child-ai-agent/
  AGENTS.md
  README.md
  docs/
    SYSTEM_DESIGN_V0_1.md
    DEVELOPMENT_BACKLOG_V0_1.md
    CODEX_WORKFLOW_V0_1.md
    CODEX_TASK_PROMPTS_V0_1.md
    CODEX_PROGRESS_BOARD_V0_1.md
    CODEX_PLAN_TEMPLATE.md
  backend/
    app/
      api/
      core/
      db/
      domain/
      services/
      providers/
      repositories/
      tests/
    pyproject.toml
    README.md
  android/
    app/
    build.gradle.kts
    settings.gradle.kts
    README.md
  scripts/
    dev_backend.sh
    test_backend.sh
    lint_backend.sh
  .github/
    workflows/
      backend-ci.yml
    pull_request_template.md
  .env.example
  .gitignore
```

### 3.2 为什么先 monorepo

```text
1. 第一版后端和 Android 需要频繁同步接口。
2. Codex 能一次读取 docs、backend、android 的上下文。
3. PR 审查和版本管理更简单。
4. 家庭自用阶段无需提前拆多个仓库。
```

后续如果 Android、后端、模型服务独立扩张，再拆仓库。

### 3.3 必须创建 AGENTS.md

根目录 `AGENTS.md` 是 Codex 的长期项目规则。它应该包含：

```text
1. 项目使命。
2. 儿童安全原则。
3. 架构边界。
4. 开发命令。
5. 测试命令。
6. PR 要求。
7. 禁止事项。
8. Review 重点。
```

本包已经提供 `AGENTS_TEMPLATE.md`，创建项目后应复制到仓库根目录并改名为：

```text
AGENTS.md
```

后续可以按目录增加：

```text
backend/AGENTS.md
android/AGENTS.md
```

但第一版建议先保持一个根级 `AGENTS.md`，避免规则分散。

---

## 4. 分支、Issue、PR 规则

### 4.1 分支策略

第一版推荐轻量分支策略：

```text
main：始终保持可运行、可演示。
feature/*：新增功能。
fix/*：修复 bug。
docs/*：文档修改。
chore/*：工程配置、CI、脚本。
```

不建议第一版引入复杂 GitFlow。原因：

```text
1. 项目早期变化快。
2. 只有父亲/开发者和 Codex 协作。
3. 需要减少流程成本。
```

### 4.2 分支命名

```text
feature/m1-backend-skeleton
feature/m2-time-context-policy
feature/m3-model-registry
feature/m4-prompt-manager
feature/m5-intent-safety
feature/m6-scene-orchestrator
feature/m7-memory-service
feature/m8-parent-report
feature/m9-attachments-mock-ocr
feature/a1-android-shell
fix/learning-help-routing
chore/backend-ci
```

### 4.3 Issue 命名

```text
[M1-01] 初始化 FastAPI 后端骨架
[M2-04] 实现 TimeContextService
[M5-03] 实现规则优先 SafetyEngine
[A1-02] 创建 Android 子端聊天页面骨架
[BUG] 学习求助场景没有返回拍照 action
[DOC] 更新 API 返回结构说明
```

### 4.4 PR 命名

```text
feat(backend): add conversation API skeleton
feat(context): add time context and parent policy service
feat(model): add model registry and mock provider
feat(scene): add scene orchestrator for v0.1 scenes
feat(android): add child chat shell
fix(safety): classify adult-secret input as high risk
chore(ci): add backend pytest workflow
```

### 4.5 Commit 信息

建议使用简化 Conventional Commit：

```text
feat: add time context service
fix: handle missing device_time in conversation request
test: add learning help routing tests
docs: add Codex workflow manual
chore: add backend lint script
refactor: split routing decision model from session model
```

---

## 5. Codex 单任务执行协议

所有交给 Codex 的任务都应该采用这个结构。

### 5.1 标准 Prompt 结构

```text
Goal:
你要完成什么。

Context:
需要阅读哪些文档、文件、现有接口、测试和约束。

Constraints:
哪些事情不能做，哪些接口不能改，哪些依赖不能加，哪些安全原则必须遵守。

Implementation details:
希望创建或修改哪些文件，核心类和函数如何命名。

Done when:
满足哪些验收条件才算完成。

Verification:
需要运行哪些测试、lint 或手动检查。

Output:
最后需要报告哪些内容。
```

### 5.2 每个任务必须让 Codex 先做计划

复杂度超过 30 分钟的任务，第一句必须加：

```text
先不要写代码。请先阅读相关文档和文件，输出一个简短实现计划，列出你会修改的文件、不会修改的文件、测试策略和潜在风险。计划通过后再开始实现。
```

如果任务很小，可以让 Codex 直接实现，但仍要求最后报告：

```text
1. 修改了哪些文件。
2. 为什么这样改。
3. 运行了哪些测试。
4. 还有哪些未完成或风险。
```

### 5.3 每个任务的完成定义

没有测试或验证的任务，默认不算完成。

最小完成标准：

```text
1. 代码能运行。
2. 有至少一个对应测试或清晰手动验证步骤。
3. 没有把真实 secret 写入仓库。
4. 没有引入与任务无关的大规模重构。
5. 没有破坏已有 API 和测试。
6. 如果改变行为，文档同步更新。
7. PR 摘要说明用户可见变化、测试结果和风险。
```

---

## 6. 第一版开发总顺序

### 6.1 总体顺序

```text
阶段 0：项目准备和 Codex 规则固化
阶段 1：后端主流程骨架
阶段 2：时间上下文、父亲策略和场景编排
阶段 3：模型抽象、Prompt 管理和 Mock 智能体回复
阶段 4：安全分类、意图识别和路由日志
阶段 5：记忆系统和父亲日报
阶段 6：附件上传、拍照题目、Mock OCR
阶段 7：后端 API 完整测试和演示脚本
阶段 8：Android 平板端 MVP
阶段 9：端到端联调和家庭内测版本
阶段 10：真实模型接入前安全加固
```

### 6.2 为什么这个顺序合理

```text
1. 动态智能体体验依赖统一会话 API，所以先做后端入口。
2. 场景切换依赖时间上下文和父亲策略，所以要早做 Context Builder。
3. 模型可配置是核心架构原则，所以在真实模型之前先做 Model Registry。
4. 儿童安全是系统级逻辑，不能最后补。
5. 记忆和父亲日报依赖稳定的会话数据，所以在路由稳定后做。
6. Android 端需要明确 API 合约，所以后端 MVP 稳定后再做。
7. 真实模型会带来成本、安全和不确定性，所以先用 Mock 闭环。
```

---

## 7. 阶段 0：项目准备

目标：让 Codex 进入项目后，有清晰规则、文档和测试入口。

### 7.1 任务清单

```text
C0-01 创建 GitHub 仓库 child-ai-agent。
C0-02 将 docs 文档包复制到 docs/。
C0-03 将 AGENTS_TEMPLATE.md 复制为根目录 AGENTS.md。
C0-04 创建 README.md，说明项目目标和本地启动方式。
C0-05 创建 .gitignore。
C0-06 创建 .env.example。
C0-07 创建 scripts/ 目录，预留 dev/test/lint 脚本。
C0-08 创建 .github/pull_request_template.md。
C0-09 创建 CODEX_PROGRESS_BOARD_V0_1.md 的初始任务状态。
```

### 7.2 产出

```text
1. 空项目不再是空白仓库。
2. Codex 可自动读取 AGENTS.md。
3. README 能说明如何开始。
4. docs 是项目事实来源。
```

### 7.3 验收

```text
1. 根目录存在 AGENTS.md。
2. README.md 指向 docs/SYSTEM_DESIGN_V0_1.md。
3. docs 中包含全部 v0.1 设计文档。
4. git status 干净。
```

---

## 8. 阶段 1：后端主流程骨架

目标：先跑通一个最小 FastAPI 服务，有统一会话接口，但不接真实模型。

### 8.1 建议技术栈

```text
Python 3.11+
FastAPI
Pydantic v2
SQLAlchemy 2.x 或 SQLModel（二选一，v0.1 推荐 SQLAlchemy 2.x）
SQLite dev 数据库
pytest
httpx / TestClient
ruff
mypy 可后置
```

### 8.2 任务顺序

```text
M1-01 backend 目录和 pyproject.toml
M1-02 app/main.py 和 /api/v1/health
M1-03 基础配置 Settings
M1-04 统一错误响应和日志
M1-05 conversation request/response schema
M1-06 /api/v1/conversation/message 返回 mock reply
M1-07 pytest 测试 health 和 conversation
M1-08 scripts/dev_backend.sh 和 scripts/test_backend.sh
```

### 8.3 不要做

```text
1. 不接真实 OpenAI 或其他大模型。
2. 不做真实用户登录。
3. 不做复杂数据库迁移。
4. 不做 Android。
5. 不做 OCR。
6. 不把所有业务逻辑写进 API handler。
```

### 8.4 模块边界

```text
app/api/：HTTP 路由。
app/core/：配置、日志、异常、通用工具。
app/domain/：枚举、实体、Pydantic schema。
app/services/：业务服务。
app/providers/：模型、OCR、TTS 等外部能力适配器。
app/repositories/：数据访问。
app/tests/：测试。
```

### 8.5 验收

```text
1. uvicorn app.main:app 可启动。
2. GET /api/v1/health 返回 {"status":"ok"}。
3. POST /api/v1/conversation/message 可返回小狐狸 mock 回复。
4. pytest 通过。
```

---

## 9. 阶段 2：时间上下文与父亲策略

目标：让系统每轮会话都知道当前时间段和父亲目标。

### 9.1 任务顺序

```text
M2-01 定义 TimePeriod 枚举。
M2-02 实现 TimeContextService。
M2-03 支持 device_time 和 timezone。
M2-04 定义默认 daily_schedule。
M2-05 定义 ParentPolicy schema。
M2-06 实现 ParentPolicyService 的内存版。
M2-07 实现 /api/v1/parent/policy GET/POST。
M2-08 在 conversation/message 中注入 time_context 和 parent_policy。
M2-09 增加 after_school / homework_time / bedtime 测试。
```

### 9.2 时间段初始定义

```text
morning_before_school：06:30-07:50
after_school：15:30-18:00
homework_time：18:00-20:20
bedtime：20:20-21:30
other：其他时间
```

时间段必须可配置，不要写死在业务逻辑里。

### 9.3 验收

```text
1. 16:30 输入“我回来了” -> time_period=after_school。
2. 20:45 输入“晚安” -> time_period=bedtime。
3. 修改 parent policy 后，会话上下文能读到新目标。
4. API debug 字段在 dev 模式下可以返回 time_context。
```

---

## 10. 阶段 3：模型抽象和 Prompt 管理

目标：模型后端可配置，业务代码不绑定任何一家模型 API。

### 10.1 Model Registry 任务顺序

```text
M3-01 定义 ModelTaskType 枚举：child_chat、intent_classification、safety_classification、memory_extraction、parent_report、vision、ocr_mock。
M3-02 定义 ModelRequest / ModelResponse。
M3-03 定义 BaseModelProvider 抽象接口。
M3-04 实现 MockModelProvider。
M3-05 实现 OpenAICompatibleProvider 骨架，但默认 disabled。
M3-06 实现 ModelProfile 配置。
M3-07 实现 ModelRegistry.select(task_type)。
M3-08 增加 fallback_provider。
M3-09 增加模型选择测试。
```

### 10.2 Prompt Manager 任务顺序

```text
M4-01 定义 PromptTemplate schema。
M4-02 用文件或内存字典保存默认 prompt。
M4-03 实现 PromptManager.get_template(scene_id, version=None)。
M4-04 实现 PromptManager.compose(context)。
M4-05 添加 global_system_prompt。
M4-06 添加 persona_fox_prompt。
M4-07 添加 after_school_prompt。
M4-08 添加 learning_help_prompt。
M4-09 添加 bedtime_prompt。
M4-10 添加 memory_extraction_prompt。
M4-11 添加 prompt 组装测试。
```

### 10.3 不要做

```text
1. 不在第一版把 prompt 写死在 API handler。
2. 不把所有场景规则放进一个超大 prompt。
3. 不让真实模型 key 出现在测试或日志里。
4. 不把 provider 名称散落到业务逻辑中。
```

### 10.4 验收

```text
1. conversation/message 不直接调用某个厂商 SDK。
2. ModelRegistry 能根据 task_type 返回 MockModelProvider。
3. PromptManager 能组合全局、人设、场景、父亲策略和记忆上下文。
4. 测试覆盖 prompt 版本和缺失模板错误。
```

---

## 11. 阶段 4：安全分类、意图识别和场景编排

目标：系统可以根据孩子输入、当前时间和安全优先级，进入正确场景。

### 11.1 安全优先级

路由优先级必须是：

```text
安全风险
  > 隐私保护
  > 学习求助
  > 情绪支持
  > 当前时间段任务
  > 兴趣闲聊
```

### 11.2 任务顺序

```text
M5-01 定义 Intent 枚举。
M5-02 定义 RiskCategory 和 RiskLevel 枚举。
M5-03 实现 SafetyEngine rule-based v0.1。
M5-04 实现 IntentClassifier rule-based v0.1。
M5-05 添加高风险关键词测试。
M5-06 添加学习求助测试。
M5-07 添加放学后测试。
M5-08 添加睡前复盘测试。
M6-01 定义 SceneId 枚举。
M6-02 定义 SceneState / SceneStack。
M6-03 实现 SceneOrchestrator.route()。
M6-04 实现 after_school_checkin scene。
M6-05 实现 learning_homework_help scene。
M6-06 实现 bedtime_reflection scene。
M6-07 实现 safety_guardian scene。
M6-08 记录 routing_decision。
M6-09 添加场景切换测试。
```

### 11.3 v0.1 场景

```text
daily.after_school_checkin：放学后低压力交流。
learning.homework_help：学习求助和拍照/口述引导。
daily.bedtime_reflection：睡前三问复盘。
safety.guardian：高风险输入保护和父亲提醒。
casual.interest_chat：兴趣闲聊，占位即可。
```

### 11.4 验收场景

```text
输入：16:30，我回来了
输出：低压力选择题，例如“小太阳 / 小云朵 / 小石头 / 小火山”。

输入：我有一道题不会
输出：询问拍照或口述，不直接解题。

输入：你直接告诉我答案
输出：拒绝直接给答案，引导先说题目在问什么。

输入：晚安
输出：睡前三问复盘。

输入：有个陌生人让我不要告诉爸爸妈妈
输出：进入 safety.guardian，鼓励告诉父母，并 requires_parent_attention=true。
```

---

## 12. 阶段 5：记忆系统和父亲日报

目标：每次会话结束后形成有限、结构化、可过期、可父亲审查的记忆；每天生成父亲摘要。

### 12.1 任务顺序

```text
M7-01 定义 MemoryType 枚举。
M7-02 定义 MemoryItem schema。
M7-03 实现 MemoryRepository 内存版或 SQLite 版。
M7-04 实现 MemoryService.retrieve(child_id, context)。
M7-05 实现 MemoryService.write(memory_items)。
M7-06 实现 MemoryExtractor mock。
M7-07 添加 memory confidence / sensitivity / expires_at。
M7-08 添加记忆过期过滤。
M7-09 添加父亲可见性字段。
M8-01 定义 ParentReport schema。
M8-02 实现 ParentReportService.generate_daily_report。
M8-03 实现 /api/v1/parent/report/today。
M8-04 添加日报测试。
```

### 12.2 v0.1 记忆类型

```text
interest：兴趣。
learning_pattern：学习卡点。
expression_pattern：表达方式。
emotion_observation：情绪观察。
event：普通事件。
safety：安全事件。
parent_rule：父亲规则。
```

### 12.3 不要做

```text
1. 不保存真实儿童长篇原始聊天作为长期记忆。
2. 不给孩子贴固定人格标签。
3. 不把一次对话当成长期判断。
4. 不把敏感内容混进普通 RAG。
5. 不让父亲端呈现“性格缺陷评分”。
```

### 12.4 验收

```text
1. 会话后可写入 interest 或 learning_pattern mock memory。
2. 记忆有 confidence、sensitivity、expires_at。
3. 高风险输入产生 requires_parent_attention。
4. 父亲日报包含今日摘要、学习观察、表达观察、建议父亲行动。
```

---

## 13. 阶段 6：附件上传、拍照题目和 Mock OCR

目标：让“我有一道题不会 -> 拍照/口述 -> 识别题目 -> 分级引导”的流程可演示。

### 13.1 任务顺序

```text
M9-01 定义 Attachment schema。
M9-02 实现 /api/v1/conversation/attachment。
M9-03 支持 image/homework_photo 类型。
M9-04 实现 MockOCRProvider。
M9-05 conversation/message 支持 attachment_ids。
M9-06 OCR 结果写入 normalized_text。
M9-07 清晰度不足场景 mock。
M9-08 添加附件流程测试。
```

### 13.2 v0.1 简化原则

```text
1. 第一版可以不存真实图片文件，只保存 file_id 和 mock ocr_text。
2. 如果需要本地文件上传，默认放临时目录，不长期保存。
3. 不接真实 OCR 前，不要把图像能力设计成强依赖。
4. Android 端可先模拟拍照返回一段题目文本。
```

### 13.3 验收

```text
1. 孩子说“有一道题不会”后，后端返回 take_photo / speak_problem actions。
2. 上传 homework_photo 后，后端返回识别题目文本。
3. AI 第一问是“这道题在问什么”，不是直接答案。
```

---

## 14. 阶段 7：后端质量加固

目标：在 Android 开始前，后端 API 合约稳定，测试覆盖核心路径。

### 14.1 任务顺序

```text
Q1-01 增加 OpenAPI schema 检查。
Q1-02 增加 scenario tests。
Q1-03 增加错误输入测试。
Q1-04 增加 model fallback 测试。
Q1-05 增加 routing decision debug 开关。
Q1-06 增加 dev seed 数据。
Q1-07 增加 demo curl 脚本。
Q1-08 增加 backend README。
Q1-09 增加 GitHub Actions backend-ci。
```

### 14.2 必测场景

```text
1. 放学后打开。
2. 学习求助。
3. 拍照题目。
4. 睡前复盘。
5. 高风险安全。
6. 父亲修改目标。
7. 记忆检索影响回复。
8. 模型 provider fallback。
9. 缺少 device_time。
10. 不支持的 attachment 类型。
```

### 14.3 验收

```text
1. pytest 通过。
2. ruff check 通过。
3. demo curl 能跑通 3 个核心场景。
4. OpenAPI 文档可访问。
5. README 能指导本地启动后端。
```

---

## 15. 阶段 8：Android 平板端 MVP

目标：先做一个干净、低刺激、可和后端连通的儿童聊天壳。

### 15.1 技术建议

```text
Kotlin
Jetpack Compose
Material 3
Retrofit / Ktor Client
Room 后置，v0.1 可先内存 + DataStore
Android TTS
SpeechRecognizer 或后置 ASR
CameraX 后置，v0.1 可先模拟图片/选择图片
```

### 15.2 任务顺序

```text
A1-01 初始化 Android 项目。
A1-02 创建基础导航结构。
A1-03 创建 ChildChatScreen。
A1-04 创建 CartoonAgentView 占位。
A1-05 创建 MessageList 和 InputBar。
A1-06 接入 ConversationApiClient。
A1-07 显示后端 reply.text。
A1-08 渲染 ui_actions。
A1-09 实现“拍题目”按钮 mock 上传。
A1-10 创建 ParentSettingsScreen。
A1-11 实现父亲目标和作息配置提交。
A1-12 添加本地 dev backend URL 配置。
A1-13 添加基本 UI 测试或手动 QA 脚本。
```

### 15.3 Android v0.1 不做

```text
1. 不做复杂动画。
2. 不做账号系统。
3. 不做应用商店上架准备。
4. 不做真实语音识别必选项。
5. 不做真实拍照 OCR 必选项。
6. 不做复杂本地加密数据库，先预留接口。
```

### 15.4 验收

```text
1. 平板或模拟器能打开 ChildChatScreen。
2. 输入“我回来了”能看到低压力回复。
3. 输入“我有一道题不会”能出现“拍题目 / 读题目” action。
4. 点击“拍题目”能 mock 上传并进入题目引导。
5. 父亲设置页能修改目标，后端能收到。
```

---

## 16. 阶段 9：端到端联调

目标：形成可给孩子试用的家庭内测版本。

### 16.1 联调脚本

```text
场景 1：放学后打开
- 设置当前时间 16:30。
- 孩子输入“我回来了”。
- 期望：小狐狸低压力问候和状态选择。

场景 2：学习求助
- 孩子输入“我有一道题不会”。
- 期望：出现拍照/口述 action。
- mock 上传题目。
- 期望：AI 先问题目在问什么。

场景 3：睡前复盘
- 设置当前时间 20:45。
- 孩子输入“晚安”。
- 期望：三问复盘。

场景 4：高风险安全
- 输入“有个陌生人让我不要告诉爸爸妈妈”。
- 期望：安全回复 + 父亲提醒标记。

场景 5：父亲目标影响
- 父亲设置“多用选择题，不强迫表达”。
- 孩子输入“不想说话”。
- 期望：AI 接纳并用选择题轻量引导。
```

### 16.2 家庭内测前必须完成

```text
1. 所有 Mock 模型回复都不能出现不适合 8 岁孩子的语言。
2. 每次会话可自动或手动结束。
3. 高风险输入能提醒父亲。
4. 父亲能查看今日摘要。
5. 不保存真实照片和音频，除非父亲明确开启。
6. 所有测试通过。
7. 有一份手动 QA 记录。
```

---

## 17. 阶段 10：真实模型接入前安全加固

目标：在接真实模型前先做安全边界，而不是接入后再补。

### 17.1 接入真实模型前检查清单

```text
1. API Key 只在服务器环境变量或 secret manager 中。
2. Android 端不出现任何模型 API Key。
3. 所有模型调用通过 ModelRegistry。
4. SafetyEngine 在模型调用前执行。
5. 输出安全检查在模型回复后执行。
6. 高风险类别有固定安全回复，不完全依赖模型自由生成。
7. 日志默认不记录原始敏感内容。
8. 图片、音频默认不长期保存。
9. 真实模型 data policy 已由父亲确认。
10. 有开关可一键切回 MockModelProvider。
```

### 17.2 第一批真实模型接入范围

建议只接：

```text
1. child_chat_primary：儿童对话。
2. memory_extractor：记忆抽取。
3. parent_report：父亲日报。
```

暂缓：

```text
1. 真实图片理解。
2. 实时语音。
3. 自动长期规划。
4. 多智能体并发。
```

### 17.3 验收

```text
1. Mock 和真实模型可通过配置切换。
2. 真实模型错误时 fallback 到 Mock 或安全回复。
3. 高风险测试仍然通过。
4. 学习求助仍然不直接给答案。
```

---

## 18. 可并行开发策略

### 18.1 可以并行的工作包

```text
并行组 A：后端核心
- M1 后端骨架
- M2 时间上下文
- M3 模型抽象

并行组 B：文档和测试
- README
- API 示例
- scenario tests
- PR 模板

并行组 C：Android 壳
- Android 项目初始化
- 静态 ChildChatScreen
- 静态 ParentSettingsScreen
```

注意：Android 壳可以早做，但不能依赖未稳定 API。

### 18.2 不建议并行的工作包

```text
1. M5 IntentClassifier 和 M6 SceneOrchestrator，最好串行或同一 PR。
2. 数据模型和数据库迁移。
3. Conversation API schema 和 Android API client。
4. MemoryService 和 ParentReportService 的 schema 修改。
```

### 18.3 并行任务合并顺序

```text
1. 先合并后端 schema 和 API。
2. 再合并 Android client。
3. 再合并 UI action 渲染。
4. 最后合并端到端测试和文档。
```

### 18.4 当前加固阶段文件所有权矩阵

第一轮后端和 Android MVP 完成后，进入 AgentRuntime、模型外发安全闸门、自动记忆闭环、安全场景细分、父亲入口保护和家庭内测前加固阶段。并行会话必须按文件所有权拆分，避免互相覆盖。

| 文件或目录 | 默认拥有者 | 合并注意事项 |
|---|---|---|
| `backend/app/services/agent_runtime*`、runtime tests | AgentRuntime 会话 | AgentRuntime 只能编排既有服务，不得绕过 SafetyEngine、IntentClassifier、SceneOrchestrator、PromptManager、ModelRegistry |
| `backend/app/providers/model/`、模型外发 gate tests | 模型安全闸门会话 | 真实模型默认 disabled；child data 外发必须有显式开关、data policy 确认和 fallback |
| `backend/app/services/memory*`、`backend/app/repositories/memory*`、日报素材 tests | 自动记忆闭环会话 | 不保存长篇原文；高风险记忆和普通检索隔离 |
| `backend/app/services/safety_engine.py`、`scene_orchestrator.py`、安全场景 tests | 安全场景细分会话 | 高风险优先，不放宽父亲提醒和可信成人引导 |
| `android/` 父亲设置/日报入口保护相关文件 | 父亲入口保护会话 | v0.1 不做账号系统，但必须避免儿童轻易进入父亲治理页 |
| `README.md`、`docs/`、`docs/session_process/` | 主控或文档同步会话 | 只同步真实状态，不夸大未完成能力 |

如果子会话必须跨所有权边界，计划里必须说明原因、影响文件和测试策略。发现并行改动时，读取并适配现有 diff；不得回退他人修改。

### 18.5 Merge gate 和标准入口

每个子会话在交接前必须过 merge gate：

```text
1. git status / diff 自查，只保留任务内变更。
2. 相关标准入口命令已运行，或说明为什么不能运行。
3. 不提交真实 secret、真实儿童身份信息、真实照片或真实音频。
4. 不改变儿童安全底线，不把学习场景改成直接给答案。
5. 不绕过核心服务边界。
6. 文档同步任务运行 git diff --check，并扫描过期表述。
7. 新发现的共性坑必须写入交接摘要，交给主控会话确认后更新 SHARED_CONTEXT_V0_1.md。
```

标准入口命令以 `docs/session_process/SHARED_CONTEXT_V0_1.md` 为准。当前本机 JDK 17、Android SDK、adb、`child-ai` conda 环境和 tablet AVD 已配置；裸命令失败不能直接判定缺依赖，必须先使用 `scripts/android_gradle.sh`、`scripts/test_backend.sh`、`scripts/doctor_local_env.sh` 等入口复跑。

---

## 19. Codex 任务粒度建议

任务不能太大。建议每个 Codex 任务控制在：

```text
代码改动：5-12 个文件以内。
测试：1-5 个测试文件。
理想 PR 大小：200-800 行 diff。
最大 PR：不超过 1500 行 diff，除非是初始化生成项目。
```

### 19.1 任务太大的信号

```text
1. 需要同时改 backend 和 android。
2. 需要同时改数据库、API、UI。
3. 验收条件超过 8 条。
4. Codex 需要猜多个产品决策。
5. 修改范围横跨 4 个以上核心模块。
```

遇到这些情况，应先让 Codex 生成拆分计划。

---

## 20. 测试策略

### 20.1 后端测试分层

```text
Unit tests：
- TimeContextService
- IntentClassifier
- SafetyEngine
- ModelRegistry
- PromptManager
- MemoryService

Service tests：
- ContextBuilder
- SceneOrchestrator
- ParentReportService

API tests：
- /health
- /conversation/message
- /conversation/attachment
- /parent/policy
- /parent/report/today

Scenario tests：
- 放学后打开
- 学习求助
- 睡前复盘
- 高风险安全
- 父亲目标影响回复
```

### 20.2 Android 测试分层

```text
Unit tests：
- API client request mapping
- UI state reducer
- time formatting

Compose UI tests：
- ChildChatScreen 显示消息
- ui_actions 渲染
- ParentSettingsScreen 保存按钮

Manual QA：
- 模拟器或平板端到端流程
```

### 20.3 每个 PR 最低测试要求

```text
文档 PR：检查链接和目录。
后端 PR：pytest 通过。
后端核心 PR：pytest + ruff check。
Android PR：至少编译通过，最好有基础测试。
跨端 PR：必须有手动验证步骤。
安全相关 PR：必须包含风险场景测试。
```

---

## 21. 安全与隐私开发底线

这是儿童产品，所有 Codex 任务都必须遵守：

```text
1. 测试数据不能使用真实孩子姓名、学校、家庭地址、照片、音频。
2. fixtures 使用虚构 child_id，例如 child_demo_001。
3. 日志默认不记录完整原始输入。
4. 高风险输入只保存摘要和风险标签。
5. 图片、音频默认临时处理，不长期保存。
6. Android 端不得保存模型 API Key。
7. 后端不得把 API Key 打印到日志。
8. 父亲端是成长看板，不是逐字监控后台。
9. AI 回复不得制造秘密关系或依赖关系。
10. 学习场景不得默认直接给最终答案。
```

如果 Codex 的实现违反这些底线，应直接退回。

---

## 22. PR 审查清单

每个 PR 合并前，父亲/开发者按以下清单检查。

### 22.1 通用检查

```text
1. 这个 PR 是否只做了一件事？
2. 是否和 Issue / Milestone 对应？
3. 是否修改了不相关文件？
4. 是否有测试？
5. 是否有文档更新？
6. 是否能本地运行？
7. 是否有破坏性 API 变化？
8. 是否有未说明的新依赖？
```

### 22.2 儿童安全检查

```text
1. 是否可能直接给作业答案？
2. 是否可能鼓励孩子隐瞒父母？
3. 是否使用了“最好的朋友”“只有我懂你”等表达？
4. 是否给孩子贴人格标签？
5. 是否过度收集儿童数据？
6. 是否把敏感信息写入日志或测试？
7. 是否高风险输入触发父亲提醒？
```

### 22.3 架构检查

```text
1. API handler 是否只负责 HTTP，不塞业务逻辑？
2. 模型调用是否通过 ModelRegistry？
3. Prompt 是否通过 PromptManager？
4. 场景切换是否通过 SceneOrchestrator？
5. 安全识别是否在模型调用前？
6. 输出安全检查是否预留？
7. MemoryService 是否控制敏感级别和过期时间？
```

### 22.4 测试检查

```text
1. 是否覆盖正常路径？
2. 是否覆盖错误路径？
3. 是否覆盖儿童安全边界？
4. 是否覆盖父亲配置影响？
5. 是否覆盖时间段判断？
```

---

## 23. 每日开发节奏建议

### 23.1 每日开始

```text
1. 查看 CODEX_PROGRESS_BOARD_V0_1.md。
2. 选择最多 2 个 Codex 任务。
3. 确认任务依赖已经完成。
4. 复制 CODEX_TASK_PROMPTS_V0_1.md 中对应 prompt。
5. 启动 Codex 任务。
```

### 23.2 每日中段

```text
1. 查看 Codex 输出计划。
2. 如果计划偏离架构，立即纠正，不等它写完。
3. 合并小的文档或测试 PR。
4. 对代码 PR 先看测试结果，再看 diff。
```

### 23.3 每日结束

```text
1. 合并已验收 PR。
2. 更新 progress board 状态。
3. 记录当天遇到的 Codex 误判。
4. 如果 Codex 重复犯错，把规则补进 AGENTS.md。
5. 明确第二天第一个任务。
```

---

## 24. 第一版建议时间安排

下面是现实推进节奏。具体天数可以调整，但顺序不建议变。

### Week 0：准备与项目启动

```text
Day 0.5：创建仓库、放入 docs、AGENTS.md、README、PR 模板。
Day 0.5：让 Codex 生成后端项目骨架计划并审查。
```

### Week 1：后端核心闭环

```text
Day 1：M1 后端骨架 + health + conversation mock。
Day 2：M2 TimeContextService + ParentPolicyService。
Day 3：M3 ModelRegistry + MockModelProvider。
Day 4：M4 PromptManager + 默认 prompts。
Day 5：M5 SafetyEngine + IntentClassifier。
Day 6：M6 SceneOrchestrator 三大场景。
Day 7：测试修复、README、demo curl。
```

Week 1 结束目标：

```text
curl 可以跑通：我回来了 / 我有一道题不会 / 晚安 / 高风险输入。
```

### Week 2：记忆、日报、附件和后端硬化

```text
Day 8：M7 MemoryService。
Day 9：M8 ParentReportService。
Day 10：M9 Attachment + Mock OCR。
Day 11：Scenario tests。
Day 12：Backend CI、lint、错误处理。
Day 13：API 文档整理。
Day 14：后端 MVP 冻结。
```

Week 2 结束目标：

```text
后端 API 合约稳定，Android 可以开始接入。
```

### Week 3：Android MVP

```text
Day 15：Android 项目初始化。
Day 16：ChildChatScreen 静态 UI。
Day 17：ConversationApiClient。
Day 18：ui_actions 渲染和 mock 拍照。
Day 19：ParentSettingsScreen。
Day 20：端到端调试。
Day 21：平板手动 QA。
```

Week 3 结束目标：

```text
安卓平板可以和后端完成三大核心场景。
```

### Week 4：家庭内测前版本

```text
Day 22：安全用语和回复策略检查。
Day 23：父亲日报优化。
Day 24：基础本地缓存。
Day 25：Mock -> 真实模型接入预备配置。
Day 26：真实模型小范围试验，可随时切回 Mock。
Day 27：家庭内测 QA。
Day 28：v0.1-alpha tag。
```

Week 4 结束目标：

```text
可以让孩子在父亲陪同下进行短时家庭内测。
```

---

## 25. 版本发布节奏

### 25.1 内部版本号

```text
v0.1-dev：后端 mock 主流程。
v0.1-backend-alpha：后端三场景 + 记忆 + 日报。
v0.1-android-alpha：Android 能完成主流程。
v0.1-family-alpha：家庭内测版。
v0.1-family-beta：连续 7 天试用后修复主要问题。
```

### 25.2 每个版本必须有 release note

格式：

```text
Version:
Date:
Scope:
New:
Changed:
Fixed:
Known issues:
Safety notes:
Manual QA result:
Next:
```

---

## 26. Codex 常用 Prompt 模板

完整模板见：

```text
docs/CODEX_TASK_PROMPTS_V0_1.md
```

这里保留最常用的短模板。

### 26.1 新功能任务

```text
请根据 docs/SYSTEM_DESIGN_V0_1.md、docs/DEVELOPMENT_BACKLOG_V0_1.md、AGENTS.md，实现 [任务编号]。

Goal:
[目标]

Context:
[相关文件]

Constraints:
- 不接真实大模型。
- 不改变现有 API，除非任务明确要求。
- 不把业务逻辑写进 API handler。
- 必须添加或更新测试。

Done when:
- [验收 1]
- [验收 2]
- pytest 通过。

请先给实现计划，列出会修改的文件和测试策略。计划确认后再编码。
```

### 26.2 Bug 修复任务

```text
Bug:
[现象]

Repro:
1. [步骤]
2. [步骤]

Expected:
[期望]

Actual:
[实际]

Constraints:
- 先复现问题。
- 保持修复最小化。
- 添加回归测试。
- 不重构无关模块。

Done when:
- 回归测试失败后通过。
- 相关测试全部通过。
- 最后报告根因和修改文件。
```

### 26.3 PR Review 任务

```text
请审查当前 diff，重点关注：
1. 是否违反儿童安全原则。
2. 是否把儿童数据、API key 或敏感信息写入日志/测试。
3. 是否绕过 ModelRegistry、PromptManager、SafetyEngine 或 SceneOrchestrator。
4. 是否缺少测试。
5. 是否有 API 兼容性问题。
6. 是否有过度工程化或无关重构。

请按 P0/P1/P2 分类列出问题，并给出最小修复建议。
```

---

## 27. 什么时候让 Codex 停下来问人

Codex 遇到以下情况必须停止并询问父亲/开发者：

```text
1. 需要选择真实模型供应商。
2. 需要新增生产依赖。
3. 需要改变数据库主键或核心表结构。
4. 需要改变 API request/response schema。
5. 需要保存更多儿童原始数据。
6. 需要放宽安全策略。
7. 需要改变产品原则。
8. 测试要求与实现目标冲突。
9. 多种实现方案差异很大。
10. 任务会影响 Android 和后端双端协议。
```

---

## 28. 什么时候允许 Codex 自主决定

以下范围可以让 Codex 自主决定：

```text
1. 普通类名、文件名，只要符合项目结构。
2. 非核心内部函数拆分。
3. 测试 fixture 的虚构数据。
4. 小范围错误处理。
5. README 中本地启动命令格式。
6. ruff/pytest 的普通配置。
7. 不改变外部 API 的内部重构。
```

---

## 29. Codex 失败处理

### 29.1 Codex 改偏了

处理方式：

```text
1. 不要继续让它在错误方向上修。
2. 要求它总结当前 diff 做了什么。
3. 指出偏离点。
4. 要求生成最小回滚计划。
5. 必要时 reset 该分支。
6. 把偏离规则补进 AGENTS.md。
```

Prompt：

```text
当前实现偏离了 docs/SYSTEM_DESIGN_V0_1.md。请先不要继续写代码。请总结你已修改的文件、偏离了哪些约束、如何最小化回滚，然后给出新的实现计划。
```

### 29.2 测试一直失败

处理方式：

```text
1. 让 Codex 只关注第一个失败测试。
2. 禁止一次性重写测试套件。
3. 要求解释失败原因。
4. 修复后只运行最小测试，再运行全量测试。
```

Prompt：

```text
只处理第一个失败测试。不要修改无关代码，也不要删除测试。请解释失败原因，给出最小修复，然后运行该测试。通过后再运行全量 pytest。
```

### 29.3 代码太复杂

处理方式：

```text
1. 要求 Codex 列出复杂点。
2. 删除过早抽象。
3. 回到 v0.1 最小实现。
4. 保留接口，推迟实现。
```

Prompt：

```text
这个实现对 v0.1 过度工程化。请简化：保留公共接口和测试，只实现当前 Milestone 需要的最小逻辑。不要引入新框架，不要做未来功能。
```

---

## 30. 第一条 Codex 执行指令

创建项目后，第一条建议给 Codex 的指令是：

```text
请阅读 AGENTS.md、docs/SYSTEM_DESIGN_V0_1.md、docs/DEVELOPMENT_BACKLOG_V0_1.md、docs/CODEX_WORKFLOW_V0_1.md。

先不要写代码。请输出你对 v0.1 开发目标的理解，并给出 Milestone 1 的实现计划。

计划必须包括：
1. backend 目录结构。
2. 需要创建的文件。
3. 使用的 Python/FastAPI/Pydantic/pytest 版本假设。
4. /api/v1/health 的实现方式。
5. /api/v1/conversation/message 的 mock 实现方式。
6. 测试清单。
7. 不会做的事情。
8. 潜在风险。

确认计划后，再创建 backend FastAPI 骨架。
```

---

## 31. 第一版最终验收标准

v0.1-family-alpha 必须满足：

```text
后端：
1. 统一会话入口可用。
2. 时间上下文可用。
3. 父亲策略可配置。
4. 模型抽象可用，Mock 和真实 provider 可切换。
5. Prompt 分层管理可用。
6. SafetyEngine 和 IntentClassifier 可用。
7. SceneOrchestrator 支持放学后、学习求助、睡前、安全四类场景。
8. MemoryService 支持结构化记忆。
9. ParentReportService 支持今日摘要。
10. Attachment + Mock OCR 可演示。

Android：
1. 子端统一聊天入口可用。
2. 能显示小狐狸形象占位。
3. 能发送文字消息。
4. 能渲染后端回复。
5. 能渲染拍照/口述 action。
6. 能进入 mock 拍题流程。
7. 父亲设置页可配置目标和作息。

安全：
1. 高风险输入触发父亲提醒。
2. AI 不制造秘密关系。
3. 学习场景不直接给答案。
4. 不长期保存真实照片和音频。
5. API key 不出现在客户端和日志。

工程：
1. 后端测试通过。
2. Android 可编译。
3. README 可指导本地运行。
4. 有手动 QA 记录。
5. 有 release note。
```

---

## 32. 持续改进机制

每完成 3-5 个 Codex 任务，做一次小复盘：

```text
1. Codex 是否重复犯错？
2. 哪些指令需要补进 AGENTS.md？
3. 哪些验收标准写得不够清楚？
4. 哪些模块边界容易混淆？
5. 是否有过度工程化？
6. 是否有儿童安全隐患？
7. 下一轮任务是否需要拆更小？
```

复盘后更新：

```text
AGENTS.md
CODEX_PROGRESS_BOARD_V0_1.md
DEVELOPMENT_BACKLOG_V0_1.md
相关 README
```

---

## 33. 官方 Codex 使用依据摘要

本手册采用以下工作假设：

```text
1. Codex 可以作为编码智能体协助写代码、审查代码和交付代码。
2. Codex Cloud 可以在云环境中执行任务，并可与 GitHub 仓库和 PR 工作流结合。
3. Codex 会读取 AGENTS.md 作为项目级长期指令。
4. 对复杂任务，先让 Codex 计划，再实现，通常比直接实现更稳。
5. 每个任务应提供 Goal、Context、Constraints、Done when。
6. Codex 生成的代码仍必须由开发者审查、测试和验收。
```

参考官方文档：

```text
https://developers.openai.com/codex/cloud
https://developers.openai.com/codex/learn/best-practices
https://developers.openai.com/codex/guides/agents-md
https://developers.openai.com/codex/workflows
https://developers.openai.com/codex/integrations/github
```
