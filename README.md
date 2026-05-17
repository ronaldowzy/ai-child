# 儿童 AI 成长智能体

面向 8 岁儿童的 AI 成长智能体项目，目标是在安卓平板上提供一个由父亲配置和治理的统一智能体入口。v0.1 优先搭建安全、可控、可扩展的基础框架，而不是开放式儿童聊天机器人。

核心闭环：

```text
孩子统一聊天入口
  -> 时间上下文注入
  -> 安全和意图识别
  -> 动态场景编排
  -> 模型可配置调用
  -> 结构化记忆
  -> 父亲日报
```

## 当前状态

当前处于 `C0 / 项目准备` 阶段。仓库已放入项目规则和 v0.1 设计文档，后续将按会话顺序进入后端骨架和 Android 壳开发。

当前尚未创建后端或 Android 实现文件。后端命令、Android 命令和 demo 脚本会在对应会话补齐后可运行。

## 文档入口

优先阅读：

- [AGENTS.md](AGENTS.md)
- [docs/SYSTEM_DESIGN_V0_1.md](docs/SYSTEM_DESIGN_V0_1.md)
- [docs/DEVELOPMENT_BACKLOG_V0_1.md](docs/DEVELOPMENT_BACKLOG_V0_1.md)
- [docs/CODEX_WORKFLOW_V0_1.md](docs/CODEX_WORKFLOW_V0_1.md)
- [docs/session_process/README.md](docs/session_process/README.md)
- [docs/CODEX_PROGRESS_BOARD_V0_1.md](docs/CODEX_PROGRESS_BOARD_V0_1.md)

## 安全原则摘要

- 不把 AI 设计成孩子唯一的朋友或最懂孩子的人。
- 不要求孩子保密，不鼓励隐瞒父母、老师或可信成人。
- 学习求助默认引导思路，不直接给最终答案。
- 高风险输入要鼓励孩子告诉父母或可信成人，并触发父亲提醒。
- 不保存不必要的儿童原始音频、照片和长篇聊天原文。
- 第一版默认使用 Mock 能力，不在 Android 端放模型 API key。

完整规则以 [AGENTS.md](AGENTS.md) 为准。

## 计划中的仓库结构

```text
backend/
  app/
    api/
    core/
    db/
    domain/
    providers/
    repositories/
    services/
    tests/
android/
  app/
docs/
scripts/
.github/
```

`backend/` 和 `android/` 将由后续专项会话创建，本次仓库初始化不写业务代码。

## 本地命令入口

项目脚本位于 `scripts/`：

```bash
bash scripts/test_backend.sh
bash scripts/dev_backend.sh
bash scripts/demo_backend_scenarios.sh
```

在 `backend/` 尚未初始化前，这些脚本会明确失败并提示进入 S01 后端骨架会话。

后端创建后，以 `backend/README.md` 为准。Android 创建后，以 `android/README.md` 为准。
