# Codex 进度看板 v0.1

用途：手动跟踪第一版开发进度。每次 Codex 完成任务或 PR 合并后更新。  
状态值建议：`todo` / `planned` / `in_progress` / `review` / `done` / `blocked` / `deferred`

---

## 0. 总体状态

```text
当前版本：v0.1-dev
当前阶段：第一轮后端和 Android MVP 已完成，进入家庭内测前加固
当前目标：补齐 AgentRuntime、自动记忆闭环、安全场景细分和完整设备 QA；模型外发安全闸门和父亲入口保护已完成代码级加固
下一步：启动 S15 ChildAgentRuntime；窗口模式模拟器复跑 mock 拍题、父亲设置、父亲入口保护、睡前和高风险场景
```

第一轮已完成能力快照：

```text
后端骨架：done
Android 壳：done
Conversation API：done
Mock 拍题：done
父亲设置/日报：done
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
| M9 | 附件/OCR | Attachment + Mock OCR | done | M6 | 拍题流程可演示，pytest/ruff 通过 |
| Q1 | 后端硬化 | scenario tests + 本地质量脚本 + demo scripts | done | M1-M9 | pytest/ruff/demo 通过，后端 MVP 可稳定验收 |
| A1 | Android 壳 | Compose 静态聊天 UI | done | C0 | Android 可编译，单元测试通过 |
| A2 | Android API | 接入 conversation API | done | Q1/A1 | 可请求后端并渲染 reply/ui_actions/session_state |
| A3 | Android 拍题 | Mock 拍题流程 | done | A2/M9 | mock attachment + conversation 连续调用可用 |
| A4 | 父亲设置/日报 | 设置目标、作息并查看日报 | done | A2/M2/M8 | policy 可修改，report 可读取 |
| E2E | 联调 | 后端 + Android 家庭内测流程 | in_progress | Q1/A1-A4 | 本机/LAN API 已通过；模拟器基础 UI smoke 已通过，完整手动 QA 待跑 |
| R1 | AgentRuntime | 统一智能体执行链路和输出安全检查 | planned | Q1/E2E/R2 | AgentRuntime、输出安全检查、模型调用边界待落地 |
| R2 | 模型外发安全闸门 | 真实模型接入前 child data gate | done | Q1 | 外发开关、数据最小化、审计和 fallback gate 可测 |
| R3 | 自动记忆闭环 | conversation 后自动抽取结构化记忆并进入日报素材 | todo | M7/M8/R1 | 不保存长篇原文，记忆写入链路可测 |
| R4 | 安全场景细分 | 细分高风险类别和父亲提醒策略 | todo | M5/M6/R1 | 高风险优先，固定安全回复不完全依赖模型 |
| R5 | 父亲入口保护 | Android 父亲页访问保护 | done | A4/E2E | 长按父亲入口 + dev PIN 轻量保护，避免儿童轻易进入父亲设置和日报 |
| R6 | 完整设备 QA | 家庭内测前完整平板/模拟器手动验收 | in_progress | E2E/R1-R5 | mock 拍题、父亲设置、睡前、高风险和断网状态待窗口模式复验 |

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
| C0-10 共享上下文与环境 doctor | done |  | 子会话先读共享上下文并使用标准入口，避免重复踩环境坑 |

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
| M9-01 Attachment schema | done |  | homework_photo 和 recognized_content 可表达 |
| M9-02 MockOCRProvider | done |  | mock 识别题目，支持低置信度 |
| M9-03 attachment API | done |  | 上传 mock 题目并接入学习求助 |

### Android 与联调

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| A1-01 Android 初始化 | done |  | 项目已创建，assembleDebug 通过 |
| A1-02 ChildChatScreen | done |  | 静态 UI 已创建，test 通过 |
| A2-01 ConversationApiClient | done |  | 可请求后端 conversation API |
| A2-02 ui_actions 渲染 | done |  | 快捷按钮和 session_state 可显示 |
| A3-01 Mock 拍题 | done |  | 题目流程跑通，不接真实 CameraX |
| A4-01 ParentSettingsScreen | done |  | policy 可修改 |
| A4-02 ParentReportScreen | done |  | report 可读取，不展示逐字聊天记录 |
| E2E-01 本机/LAN API QA | done |  | MANUAL_QA_V0_1.md 记录 S14_E2E_API: PASS |
| E2E-02 Android 模拟器基础 smoke | done |  | AVD 启动、App 安装、聊天 API、父亲日报读取通过 |
| E2E-03 Android 完整手动 QA | in_progress |  | mock 拍题、父亲设置、睡前、高风险、断网和父亲入口保护场景待窗口模式复验 |

### 家庭内测前加固

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| R1-01 AgentRuntime 统一执行链路 | planned |  | conversation 编排收敛到 runtime，模型调用、输出检查、记忆抽取有明确顺序 |
| R1-02 输出安全检查 | todo |  | 模型回复后仍经过安全审查；高风险和学习直接给答案有兜底 |
| R2-01 真实模型外发安全闸门 | done |  | child data、image、audio 外发需要显式开关和 retention policy 确认；策略不满足时 fallback mock |
| R2-02 Mock/真实 provider 切换验收 | done |  | 默认 Mock；真实 provider disabled 或受 gate 保护；测试不走真实外网 |
| R3-01 自动记忆写入闭环 | todo |  | conversation 后自动抽取结构化记忆；不保存长篇逐字原文 |
| R3-02 记忆到父亲日报素材闭环 | todo |  | 当天结构化记忆可稳定进入日报，不暴露 evidence 原文 |
| R4-01 安全场景细分 | todo |  | adult_secret、stranger、privacy、self_harm 等风险类别有不同回复/提醒策略 |
| R4-02 父亲提醒策略加固 | todo |  | 高风险 requires_parent_attention 可测，普通低风险不制造过度告警 |
| R5-01 父亲入口保护 | done |  | Android 父亲设置/日报入口需长按并输入 dev PIN，不做账号系统但避免儿童误入 |
| R6-01 完整设备 QA | in_progress |  | 窗口模式模拟器或真实平板跑完 MANUAL_QA_V0_1.md 全部核心场景 |

---

## 3. 当天记录

### 日期：2026-05-19

```text
今日目标：完成 S13 Android 拍题与父亲页验收，推进 S14 本机/API 联调和 S20a 文档同步，进入 AgentRuntime、模型外发安全闸门、自动记忆闭环、安全场景细分、父亲入口保护和家庭内测前加固阶段。
完成任务：Android mock 拍题流程已接入 attachment API 和 conversation API；父亲设置页可读取/保存 goals、沟通偏好和作息时间；父亲日报页可读取后端日报摘要；S14 本机 health、LAN health、E2E API 合约检查通过；新增共享上下文、环境 doctor 和 Android Gradle 包装脚本；已安装 Android Emulator，创建 child_ai_tablet_api35 AVD，并完成 App 安装、聊天 API、父亲日报基础 smoke；Android test、assembleDebug、lintDebug 通过；S20a 修正文档中过期的 C0/未初始化描述，并补齐多会话协同规则和后续子会话提示词；S16 已完成模型外发安全闸门；S19 已完成 Android 父亲入口长按 + dev PIN 轻量保护。
阻塞问题：无硬阻塞；完整设备侧手动 QA、AgentRuntime、自动记忆闭环和安全场景细分仍需继续执行；Mimo 真实网络 smoke 尚未执行。
Codex 偏差：S14 子会话把裸 Gradle 的 Java Runtime 报错误判为本机缺少 JDK；主控会话已修正为共享环境未加载问题，并固化标准入口。
需要补充到 AGENTS.md 的规则：暂无。
明日第一任务：启动 S15 ChildAgentRuntime，并用窗口模式模拟器复跑 S14/R6 完整设备侧手动 QA。
```

### 日期：2026-05-18

```text
今日目标：完成 S10 后端质量与演示验收，完成 S11 Android 壳项目复验，并完成 S12 Android API 接入验收。
完成任务：补齐 Q1 场景测试，覆盖放学后、学习求助、直接要答案、不想说话、高风险安全、睡前复盘、父亲目标影响回复、模型 fallback；更新 test/lint/dev/demo 后端脚本；更新 backend README；本地 pytest、ruff、demo 通过；Android 壳项目已创建并通过 assembleDebug / test；Android 已接入 conversation API 并渲染 reply、ui_actions、session_state。
阻塞问题：无。
Codex 偏差：未新增 GitHub Actions，因为当前任务约束要求没有远端 GitHub 时优先保证本地脚本和 README。
需要补充到 AGENTS.md 的规则：暂无。
明日第一任务：启动 S13 Android 拍题与父亲页会话。
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
