# Codex 进度看板 v0.1

用途：手动跟踪第一版开发进度。每次 Codex 完成任务或 PR 合并后更新。  
状态值建议：`todo` / `planned` / `in_progress` / `review` / `done` / `blocked` / `deferred`

---

## 0. 总体状态

```text
当前版本：v0.1-dev
当前阶段：阶段 0 / 项目准备
当前目标：创建仓库、放入文档、建立 AGENTS.md、会话协作流程和后端骨架
下一步：完成本地初始提交后，进入 M1 后端 FastAPI 骨架
```

---

## 1. Milestone 总览

| ID | 阶段 | 目标 | 状态 | 依赖 | 验收摘要 |
|---|---|---|---|---|---|
| C0 | 项目准备 | 仓库、文档、AGENTS、README | done | 无 | 本地仓库规则和结构清晰，GitHub 远程后置 |
| M1 | 后端骨架 | FastAPI + health + conversation mock | todo | C0 | pytest 通过，mock 会话可用 |
| M2 | 时间与父亲策略 | TimeContext + ParentPolicy | todo | M1 | time_period 和父亲目标注入会话 |
| M3 | 模型抽象 | ModelRegistry + MockProvider | todo | M1 | 业务不绑定具体模型 |
| M4 | Prompt 管理 | PromptManager + 分层模板 | todo | M3 | 场景 prompt 可组合 |
| M5 | 安全与意图 | SafetyEngine + IntentClassifier | todo | M2 | 高风险优先，意图识别可测 |
| M6 | 场景编排 | SceneOrchestrator + 四类场景 | todo | M5 | 动态场景切换可用 |
| M7 | 记忆系统 | MemoryService + MemoryExtractor mock | todo | M6 | 结构化记忆可写可查 |
| M8 | 父亲日报 | ParentReportService | todo | M7 | 今日摘要可生成 |
| M9 | 附件/OCR | Attachment + Mock OCR | todo | M6 | 拍题流程可演示 |
| Q1 | 后端硬化 | scenario tests + CI + demo scripts | todo | M1-M9 | 后端 MVP 稳定 |
| A1 | Android 壳 | Compose 静态聊天 UI | todo | C0 | Android 可编译 |
| A2 | Android API | 接入 conversation API | todo | Q1/A1 | 能收发消息 |
| A3 | Android 拍题 | Mock 拍题流程 | todo | A2/M9 | 学习求助可跑通 |
| A4 | 父亲设置 | 设置目标和作息 | todo | A2/M2 | policy 可修改 |
| E2E | 联调 | 后端 + Android 家庭内测流程 | todo | Q1/A1-A4 | 核心场景可手动跑通 |
| H1 | 安全加固 | 真实模型接入前检查 | todo | E2E | 可切换 Mock/真实模型 |

---

## 2. 详细任务看板

### C0：项目准备

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| C0-01 创建 GitHub 仓库 | deferred |  | 当前仅使用本地 Git，远程仓库后置 |
| C0-02 复制 docs 文档包 | done |  | docs 文件完整 |
| C0-03 复制 AGENTS_TEMPLATE 为 AGENTS.md | done |  | Codex 可读取规则 |
| C0-04 创建 README.md | done |  | 指向核心文档 |
| C0-05 创建 .gitignore | done |  | 忽略 env/build/cache |
| C0-06 创建 .env.example | done |  | 无真实 secret |
| C0-07 创建 scripts 目录 | done |  | dev/test 脚本占位 |
| C0-08 创建 PR 模板 | done |  | 包含 Tests/Safety/Docs |
| C0-09 创建多会话协作流程 | done |  | docs/session_process 可指导子会话协作 |

### M1：后端骨架

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| M1-01 初始化 backend pyproject | todo |  | 依赖可安装 |
| M1-02 创建 app/main.py | todo |  | FastAPI 可启动 |
| M1-03 实现 /api/v1/health | todo |  | 返回 ok |
| M1-04 定义 conversation schema | todo |  | request/response 可校验 |
| M1-05 实现 conversation mock service | todo |  | 返回小狐狸回复 |
| M1-06 添加 pytest | todo |  | health/conversation 测试通过 |
| M1-07 添加 backend README | todo |  | 本地启动说明可用 |

### M2：时间与父亲策略

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| M2-01 TimePeriod 枚举 | todo |  | 枚举可导入 |
| M2-02 TimeContextService | todo |  | 16:30 -> after_school |
| M2-03 ParentPolicy schema | todo |  | goals/preferences/schedule |
| M2-04 ParentPolicyService | todo |  | 可读写默认策略 |
| M2-05 /api/v1/parent/policy | todo |  | GET/POST 可用 |
| M2-06 conversation 注入 context | todo |  | debug 含 time_context |

### M3：模型抽象

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| M3-01 ModelTaskType | todo |  | 类型完整 |
| M3-02 BaseModelProvider | todo |  | 抽象接口清晰 |
| M3-03 MockModelProvider | todo |  | 不调外网 |
| M3-04 OpenAICompatibleProvider skeleton | todo |  | 默认 disabled |
| M3-05 ModelRegistry | todo |  | task_type 选择 provider |
| M3-06 fallback 测试 | todo |  | provider 异常可降级 |

### M4：Prompt Manager

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| M4-01 PromptTemplate schema | todo |  | 有版本/scene_id |
| M4-02 global_system prompt | todo |  | 儿童安全规则完整 |
| M4-03 persona_fox prompt | todo |  | 温和不依赖 |
| M4-04 scene prompts | todo |  | 三大场景可用 |
| M4-05 PromptManager.compose | todo |  | 可组合上下文 |
| M4-06 prompt tests | todo |  | 缺失模板有错误 |

### M5：安全与意图

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| M5-01 Risk enums | todo |  | risk 类型完整 |
| M5-02 Intent enums | todo |  | intent 类型完整 |
| M5-03 SafetyEngine | todo |  | 高风险规则可测 |
| M5-04 IntentClassifier | todo |  | 学习/放学/睡前可测 |
| M5-05 conversation debug | todo |  | 返回 risk/intent |

### M6：场景编排

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| M6-01 SceneId / SceneState | todo |  | 场景类型清晰 |
| M6-02 SceneOrchestrator.route | todo |  | 根据 context 路由 |
| M6-03 after_school scene | todo |  | 低压力选择题 |
| M6-04 learning_help scene | todo |  | 拍照/口述 action |
| M6-05 bedtime scene | todo |  | 三问复盘 |
| M6-06 safety scene | todo |  | 父亲提醒 |
| M6-07 routing_decision | todo |  | 可记录或 debug |

### M7-M9：记忆、日报、多模态占位

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| M7-01 MemoryItem | todo |  | 字段完整 |
| M7-02 MemoryRepository | todo |  | 可写可查 |
| M7-03 MemoryService | todo |  | 过滤过期/敏感 |
| M7-04 MemoryExtractor mock | todo |  | 输出结构化记忆 |
| M8-01 ParentReport schema | todo |  | 字段完整 |
| M8-02 ParentReportService | todo |  | 今日摘要可生成 |
| M8-03 report API | todo |  | /today 可用 |
| M9-01 Attachment schema | todo |  | image/text 可表达 |
| M9-02 MockOCRProvider | todo |  | mock 识别题目 |
| M9-03 attachment API | todo |  | 上传 mock 题目 |

### Android 与联调

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| A1-01 Android 初始化 | todo |  | 可编译 |
| A1-02 ChildChatScreen | todo |  | 静态 UI |
| A2-01 ConversationApiClient | todo |  | 可请求后端 |
| A2-02 ui_actions 渲染 | todo |  | 按钮显示 |
| A3-01 Mock 拍题 | todo |  | 题目流程跑通 |
| A4-01 ParentSettingsScreen | todo |  | policy 可修改 |
| E2E-01 手动 QA | todo |  | MANUAL_QA_V0_1.md |

---

## 3. 当天记录

### 日期：YYYY-MM-DD

```text
今日目标：
完成任务：
阻塞问题：
Codex 偏差：
需要补充到 AGENTS.md 的规则：
明日第一任务：
```
