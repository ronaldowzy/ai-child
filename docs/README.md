# 儿童 AI 成长智能体 v0.1 文档包

这个文档包用于启动 Codex 开发项目。

建议目录：

```text
child-ai-agent/
  AGENTS.md
  docs/
    SYSTEM_DESIGN_V0_1.md
    DEVELOPMENT_BACKLOG_V0_1.md
    CODEX_WORKFLOW_V0_1.md
    CODEX_TASK_PROMPTS_V0_1.md
    CODEX_PROGRESS_BOARD_V0_1.md
    CODEX_PLAN_TEMPLATE.md
    AGENTS_TEMPLATE.md
```

## 文档说明

```text
SYSTEM_DESIGN_V0_1.md
  第一版系统设计主文档，说明产品定位、架构、模块、数据库、API、Prompt、安全隐私和验收标准。

DEVELOPMENT_BACKLOG_V0_1.md
  第一版开发任务拆解，按 Milestone 描述后端、Android、记忆、日报、多模态占位等任务。

CODEX_WORKFLOW_V0_1.md
  Codex 开发工作手册，说明工作模式、阶段顺序、PR 规则、测试策略、审查清单和每日节奏。

CODEX_TASK_PROMPTS_V0_1.md
  可直接复制给 Codex 的任务 Prompt 清单，覆盖 M1-M9、Android、E2E、Bug、Review、文档更新。

CODEX_PROGRESS_BOARD_V0_1.md
  手动进度看板，用于跟踪任务状态、PR、验收和阻塞问题。

CODEX_PLAN_TEMPLATE.md
  复杂任务开始前让 Codex 填写的执行计划模板。

AGENTS_TEMPLATE.md
  建议复制到仓库根目录并改名为 AGENTS.md，作为 Codex 的长期项目规则。
```

## 推荐使用方式

1. 创建 GitHub 仓库，例如 `child-ai-agent`。
2. 将本目录复制到项目的 `docs/` 目录。
3. 将 `docs/AGENTS_TEMPLATE.md` 复制到项目根目录，并改名为 `AGENTS.md`。
4. 将 `docs/CODEX_PROGRESS_BOARD_V0_1.md` 保留在 docs 中，每次任务完成后更新。
5. 先让 Codex 阅读 `AGENTS.md` 和 `docs/` 中的核心文档。
6. 再让 Codex 按 `CODEX_TASK_PROMPTS_V0_1.md` 中的任务顺序开始开发。

## 第一条 Codex 指令

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

## 第一阶段开发顺序

```text
C0 项目准备
M1 后端 FastAPI 骨架
M2 时间上下文与父亲策略
M3 Model Registry 与 MockModelProvider
M4 Prompt Manager
M5 SafetyEngine 与 IntentClassifier
M6 SceneOrchestrator
M7 MemoryService
M8 ParentReportService
M9 Attachment 与 Mock OCR
Q1 后端 scenario tests、CI、demo scripts
A1 Android 静态聊天壳
A2 Android 接入 conversation API
A3 Android Mock 拍题流程
A4 Android 父亲设置页
E2E 端到端联调
H1 真实模型接入前安全加固
```

## 重要原则

第一版先跑通：

```text
统一聊天入口
  -> 时间上下文
  -> 意图和安全识别
  -> 动态场景编排
  -> Mock 模型回复
  -> 结构化记忆
  -> 父亲日报
  -> Android 展示
```

第一版先不要做：

```text
真实模型强依赖
复杂动画
开放式无限聊天
真实 OCR 强依赖
账号系统
应用商店上架
复杂多智能体并发
```
