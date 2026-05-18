# Codex 进度看板 v0.1

用途：手动跟踪第一版开发进度。每次 Codex 完成任务或 PR 合并后更新。  
状态值建议：`todo` / `planned` / `in_progress` / `review` / `done` / `blocked` / `deferred`

---

## 0. 总体状态

```text
当前版本：v0.1-dev
当前阶段：阶段 9 / 附件与 Mock OCR 准备
当前目标：实现 Attachment API、Mock OCR Provider 和拍题占位流程
下一步：启动 S09 附件与 Mock OCR 会话
```

---

## 1. Milestone 总览

| ID | 阶段 | 目标 | 状态 | 依赖 | 验收摘要 |
|---|---|---|---|---|---|
| C0 | 项目准备 | 仓库、文档、AGENTS、README | done | 无 | 本地仓库规则和结构清晰，GitHub 远程后置 |
| M1 | 后端骨架 | FastAPI + health + conversation mock | done | C0 | pytest 通过，mock 会话可用 |
| M2 | 时间与父亲策略 | TimeContext + ParentPolicy | done | M1 | time_period 和父亲目标注入会话 |
| M3 | 模型抽象 | ModelRegistry + MockProvider | done | M1 | 业务不绑定具体模型 |
| M4 | Prompt 管理 | PromptManager + 分层模板 | done | M3 | 场景 prompt 可组合 |
| M5 | 安全与意图 | SafetyEngine + IntentClassifier | done | M2 | 高风险优先，意图识别可测 |
| M6 | 场景编排 | SceneOrchestrator + 四类场景 | done | M5 | 动态场景切换可用 |
| M7 | 记忆系统 | MemoryService + MemoryExtractor mock | done | M6 | 结构化记忆可写可查，pytest/ruff 通过 |
| M8 | 父亲日报 | ParentReportService | done | M7 | 今日摘要可生成，pytest/ruff 通过 |
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
| M1-01 初始化 backend pyproject | done |  | 依赖可安装 |
| M1-02 创建 app/main.py | done |  | FastAPI 可启动 |
| M1-03 实现 /api/v1/health | done |  | 返回 ok |
| M1-04 定义 conversation schema | done |  | request/response 可校验 |
| M1-05 实现 conversation mock service | done |  | 返回小狐狸回复 |
| M1-06 添加 pytest | done |  | health/conversation 测试通过 |
| M1-07 添加 backend README | done |  | 本地启动说明可用 |

### M2：时间与父亲策略

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| M2-01 TimePeriod 枚举 | done |  | 枚举可导入 |
| M2-02 TimeContextService | done |  | 16:30 -> after_school |
| M2-03 ParentPolicy schema | done |  | goals/preferences/schedule |
| M2-04 ParentPolicyService | done |  | 可读写默认策略 |
| M2-05 /api/v1/parent/policy | done |  | GET/POST 可用 |
| M2-06 conversation 注入 context | done |  | debug 含 time_context |

### M3：模型抽象

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| M3-01 ModelTaskType | done |  | 类型完整 |
| M3-02 BaseModelProvider | done |  | 抽象接口清晰 |
| M3-03 MockModelProvider | done |  | 不调外网 |
| M3-04 OpenAICompatibleProvider skeleton | done |  | 默认 disabled |
| M3-05 ModelRegistry | done |  | task_type 选择 provider |
| M3-06 fallback 测试 | done |  | provider 异常可降级 |

### M4：Prompt Manager

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| M4-01 PromptTemplate schema | done |  | 有版本/scene_id |
| M4-02 global_system prompt | done |  | 儿童安全规则完整 |
| M4-03 persona_fox prompt | done |  | 温和不依赖 |
| M4-04 scene prompts | done |  | 三大场景可用 |
| M4-05 PromptManager.compose | done |  | 可组合上下文 |
| M4-06 prompt tests | done |  | 缺失模板有错误 |

### M5：安全与意图

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| M5-01 Risk enums | done |  | risk 类型完整 |
| M5-02 Intent enums | done |  | intent 类型完整 |
| M5-03 SafetyEngine | done |  | 高风险规则可测 |
| M5-04 IntentClassifier | done |  | 学习/放学/睡前可测 |
| M5-05 conversation debug | done |  | 返回 risk/intent |

### M6：场景编排

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| M6-01 SceneId / SceneState | done |  | 场景类型清晰 |
| M6-02 SceneOrchestrator.route | done |  | 根据 context 路由 |
| M6-03 after_school scene | done |  | 低压力选择题 |
| M6-04 learning_help scene | done |  | 拍照/口述 action |
| M6-05 bedtime scene | done |  | 三问复盘 |
| M6-06 safety scene | done |  | 父亲提醒 |
| M6-07 routing_decision | done |  | 可记录或 debug |

### M7-M9：记忆、日报、多模态占位

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| M7-01 MemoryItem | done |  | 字段完整，含 evidence/confidence/expires_at/sensitivity |
| M7-02 MemoryRepository | done |  | 内存版可写可查 |
| M7-03 MemoryService | done |  | 过滤过期记忆，普通检索默认隔离 safety |
| M7-04 MemoryExtractor mock | done |  | 输出结构化记忆 |
| M8-01 ParentReport schema | done |  | 字段完整 |
| M8-02 ParentReportService | done |  | 今日摘要可生成，不返回逐字聊天记录 |
| M8-03 report API | done |  | /reports/{child_id} 和 /report/today 可用 |
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

### 日期：2026-05-18

```text
今日目标：完成 S07 记忆系统和 S08 父亲日报交接验收。
完成任务：MemoryItem、MemoryRepository、MemoryService、MemoryExtractor mock、memories API、ParentReport schema、ParentReportService、parent report API 已实现并通过主控会话复验。
阻塞问题：无。
Codex 偏差：DEVELOPMENT_BACKLOG 的旧 Milestone 编号仍与会话表/进度板不一致，本次未修改该文档。
需要补充到 AGENTS.md 的规则：暂无。
明日第一任务：启动 S09 附件与 Mock OCR 会话。
```

### 日期：YYYY-MM-DD

```text
今日目标：
完成任务：
阻塞问题：
Codex 偏差：
需要补充到 AGENTS.md 的规则：
明日第一任务：
```
