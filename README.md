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

v0.1 第一轮后端和 Android MVP 已完成。当前项目已从基础闭环进入受控 AI 智能体运行时、完整设备 QA 和家庭内测前体验加固阶段。下一阶段产品重点已确认：优先推进语音交互和小白狐形象体验，但必须先完成现有设备侧闭环验收。

已完成的第一轮能力：

- 后端 FastAPI 骨架、health、conversation API、时间上下文、父亲策略、PromptManager、ModelRegistry、SafetyEngine、IntentClassifier、SceneOrchestrator。
- 结构化记忆、父亲日报、mock 附件和 Mock OCR 拍题流程。
- Android Compose MVP：统一聊天入口、conversation API 接入、ui_actions 渲染、mock 拍题、父亲设置页和父亲日报页。
- ChildAgentRuntime 主回复链路、真实模型外发安全闸门、规则型自动记忆闭环、安全场景细分、父亲入口长按 + PIN 轻量保护。
- 真实模型本机 smoke 已通过；默认仍保持 Mock 优先，真实外部 provider 只允许在后端临时环境变量和数据策略开关满足时使用。
- 本地后端 test/lint/demo、Android build/test/lint、E2E API 检查和基础模拟器 smoke 记录。

当前未完成或正在加固的能力：

- 窗口模式模拟器或真实平板完整设备 QA。
- Android 真实语音输入、小白狐复杂动画低配 QA 和完整设备 QA。
- 普通聊天正在升级为 freedom-first：`conversation.open` 是默认底座，时段、父母寄语、记忆和图片能力作为上下文或工具；安全、隐私、学习、睡前边界按需介入。
- 通用图片分享：拍照入口从“拍题目”升级为“拍给小白狐看”，作业题只是其中一个分支。
- 数据库持久化、账号系统、真实相机/OCR/图片存储和生产级父亲身份认证。

已完成但仍需持续验证的加固能力：

- 真实模型外发前的数据安全闸门：默认仍保持 Mock 优先，Mimo 等外部 provider 必须通过 child data、图片/音频和 retention policy 开关校验。
- Android 父亲设置/日报入口轻量保护：长按父亲入口后输入开发 PIN 才进入；这不是账号系统或强安全机制。
- 后端回复输出安全检查：模型回复会做语音化规整，并拦截秘密关系、隔离可信成人、直接给作业最终答案等风险输出。
- 小白狐 TTS 后端主路径：已新增 `/api/v1/tts/xiaobaohu`、mock provider、本地 wav 缓存和 TTS 数据策略闸门；MiMo VoiceClone 默认关闭，Android 下一步优先播放 `reply.audio_url`，系统 TTS 仅作 fallback 和诊断。
- Open Conversation Mode 小步实现：普通兴趣话题进入 `conversation.open`，ChildAgentRuntime 传入最近几轮短期 history；安全、隐私、学习、睡前边界仍由后端强约束。

已确认的下一阶段产品方向：

- 语音输入第一阶段优先 Android 本地 `SpeechRecognizer`。
- 语音输入必须先转成可确认文本，再由用户确认发送给后端；误识别内容不得自动进入 AI 回复。
- v1 语音输入是 confirm-before-send；hands-free conversational mode 是未来阶段，不进入 v1。
- 小白狐正式品牌音色方案改为后端 MiMo VoiceClone：VoiceDesign 只用于音色筛选，VoiceClone 使用已下载 wav 样本生成 App 语音，普通 MiMo TTS 只做测试/兜底。
- TTS 默认自动朗读小白狐回复，必须提供停止/静音和 DevSettings 或父亲设置开关。
- Android 语音实现必须通过可替换抽象：`VoiceEngine`、`SpeechInputController`、`TtsController`；远程音频优先，系统 `VoiceProfile` 只作为 fallback。
- 默认不上传原始音频到后端，不长期保存原始音频。
- 正式名称为“小白狐”；UI、产品、设计和测试说明优先统一。代码 class 名 `FoxAgent` 暂可保留，后续如要改代码命名单独 refactor。
- 小白狐形象应温和、好奇、慢热友好；视觉目标优先 3D / soft 3D / 毛绒感 / 立体绘本感，Compose Canvas / 2D 只是 fallback；不做强刺激、排行榜、连击奖励或上瘾式动画。
- 后端继续通过 `reply.voice_enabled`、`reply.audio_url`、`reply.emotion` 和 `reply.agent_motion` 暴露表现层信号。
- 语音 QA 必须记录识别准确率、延迟、中文效果、儿童声音识别、TTS 自然度和孩子接受度。
- 新产品想法必须先写入 [docs/PRODUCT_DECISIONS_V0_1.md](docs/PRODUCT_DECISIONS_V0_1.md)，再进入子会话实现。
- 最新产品方向：不要继续增加固定任务场景；优先建设自由对话底座、父母寄语上下文和通用图片分享能力。

## 文档入口

优先阅读：

- [AGENTS.md](AGENTS.md)
- [docs/SYSTEM_DESIGN_V0_1.md](docs/SYSTEM_DESIGN_V0_1.md)
- [docs/DEVELOPMENT_BACKLOG_V0_1.md](docs/DEVELOPMENT_BACKLOG_V0_1.md)
- [docs/CODEX_WORKFLOW_V0_1.md](docs/CODEX_WORKFLOW_V0_1.md)
- [docs/session_process/README.md](docs/session_process/README.md)
- [docs/CODEX_PROGRESS_BOARD_V0_1.md](docs/CODEX_PROGRESS_BOARD_V0_1.md)
- [docs/PRODUCT_DECISIONS_V0_1.md](docs/PRODUCT_DECISIONS_V0_1.md)
- [docs/VOICE_INTERACTION_DESIGN_V0_1.md](docs/VOICE_INTERACTION_DESIGN_V0_1.md)
- [docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md](docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md)
- [docs/NEXT_PHASE_PLAN_V0_2.md](docs/NEXT_PHASE_PLAN_V0_2.md)
- [docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md](docs/FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md)
- [docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md](docs/UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md)

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
