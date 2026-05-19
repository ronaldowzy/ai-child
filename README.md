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

v0.1 第一轮后端和 Android MVP 已完成。当前项目已从基础闭环进入 AgentRuntime、模型外发安全闸门、自动记忆闭环、安全场景细分、父亲入口保护和家庭内测前加固阶段。

已完成的第一轮能力：

- 后端 FastAPI 骨架、health、conversation API、时间上下文、父亲策略、PromptManager、ModelRegistry、SafetyEngine、IntentClassifier、SceneOrchestrator。
- 结构化记忆、父亲日报、mock 附件和 Mock OCR 拍题流程。
- Android Compose MVP：统一聊天入口、conversation API 接入、ui_actions 渲染、mock 拍题、父亲设置页和父亲日报页。
- 本地后端 test/lint/demo、Android build/test/lint、E2E API 检查和基础模拟器 smoke 记录。

当前未完成或正在加固的能力：

- AgentRuntime 统一执行链路和输出安全检查。
- 自动记忆写入闭环和父亲日报素材稳定性。
- 高风险安全场景细分。
- 窗口模式模拟器或真实平板完整设备 QA。

已完成但仍需持续验证的加固能力：

- 真实模型外发前的数据安全闸门：默认仍保持 Mock 优先，Mimo 等外部 provider 必须通过 child data、图片/音频和 retention policy 开关校验。
- Android 父亲设置/日报入口轻量保护：长按父亲入口后输入开发 PIN 才进入；这不是账号系统或强安全机制。

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

## 仓库结构

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

## 本地命令入口

本机已配置 `child-ai` conda 环境、JDK 17 和 Android SDK。部分非交互 shell 可能没有继承 `PATH`、`JAVA_HOME` 或 `ANDROID_HOME`，因此裸命令失败不能直接判定机器缺少依赖；先使用根目录标准脚本复跑。

环境检查：

```bash
bash scripts/doctor_local_env.sh
```

后端：

```bash
bash scripts/test_backend.sh
bash scripts/lint_backend.sh
bash scripts/dev_backend.sh
bash scripts/demo_backend_scenarios.sh
bash scripts/e2e_local_api_check.sh
```

Android：

```bash
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh lintDebug
bash scripts/start_android_emulator.sh
bash scripts/install_android_debug.sh
```

后端细节以 [backend/README.md](backend/README.md) 为准。Android 细节以 [android/README.md](android/README.md) 为准。多会话环境事实和已知坑以 [docs/session_process/SHARED_CONTEXT_V0_1.md](docs/session_process/SHARED_CONTEXT_V0_1.md) 为准。
