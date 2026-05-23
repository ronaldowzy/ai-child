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

## 当前测试阶段最高原则

当前阶段以真实可测试、真实可用为最高执行目的。已经开发并进入当前测试范围的功能必须在本地/真机测试环境中全部开放和验证，不能因为兜底实现、未启用开关或安全默认值而实际不可用。

执行规则：

- 不要以“安全默认值”为理由关闭或跳过当前要测试的功能。
- 所有已开发但在当前测试环境不能使用的功能，都视为问题或 bug，必须修到可用，或明确标记为外部阻塞并说明缺少什么。
- 兜底实现和备用路径只能用于异常保护，不能替代真实功能验收，也不能作为完成状态。
- 测试前必须确认运行中的后端/Android 配置与本轮目标一致；例如 prompt trace、真实 ASR、真实 TTS、vision 或 DB persistence 已开发且本轮要测，就必须实际启用并验证写入/调用链路。
- 不得把“代码已存在但运行环境未开启”写成 done。
- 儿童安全护栏仍必须工作，但不能把安全护栏当成关闭功能、绕过验收或长期停留在非真实链路的理由。

## 当前状态

v0.1 第一轮后端和 Android MVP 已完成。当前项目已从基础闭环进入受控 AI 智能体运行时、完整设备 QA 和家庭内测前体验加固阶段。下一阶段产品重点已确认：优先推进语音交互和小白狐形象体验，但必须先完成现有设备侧闭环验收。

已完成的第一轮能力：

- 后端 FastAPI 骨架、health、conversation API、时间上下文、父亲策略、PromptManager、ModelRegistry、SafetyEngine、IntentClassifier、SceneOrchestrator。
- 结构化记忆、父亲日报、附件和 OCR/vision 图片理解流程。
- Android Compose MVP：统一聊天入口、conversation API 接入、ui_actions 渲染、系统相机/相册真实图片上传、父亲设置页和父亲日报页。
- ChildAgentRuntime 主回复链路、真实模型外发安全闸门、规则型自动记忆闭环、安全场景细分、父亲入口长按 + PIN 轻量保护。
- 真实模型本机 smoke 已通过；当前测试阶段不能停留在非真实链路。已开发且进入测试范围的真实 provider / 本地 provider 必须在测试环境实际启用和验证，缺 key、缺模型文件、缺权限或网络失败要标记为 BLOCKED/FAIL，而不是写成 done。
- 本地后端 test/lint/demo、Android build/test/lint、E2E API 检查和基础模拟器 smoke 记录。

当前未完成或正在加固的能力：

- 窗口模式模拟器或真实平板完整设备 QA。
- Android 语音输入真机 QA、系统相机真实图片上传/识图 QA、本地 SenseVoice ASR 准确率/延迟 QA、小白狐 opening greeting、复杂动画低配 QA 和完整设备 QA。
- 普通聊天正在升级为 freedom-first：`conversation.open` 是默认底座，时段、父母寄语、记忆和图片能力作为上下文或工具；安全、隐私、学习、睡前边界按需介入。
- 通用图片分享：拍照入口从“拍题目”升级为“拍给小白狐看”，作业题只是其中一个分支。
- 账号系统、CameraX 自定义相机、长期图片存储和生产级父亲身份认证。

已完成但仍需持续验证的加固能力：

- 真实模型外发前的数据安全闸门：Mimo 等外部 provider 必须通过 child data、图片/音频和 retention policy 开关校验；但进入当前测试范围后，应使用临时测试环境显式开启并验证真实链路，不能用未启用配置作为完成状态。
- Android 父亲设置/日报入口轻量保护：长按父亲入口后输入开发 PIN 才进入；这不是账号系统或强安全机制。
- 后端回复输出安全检查：模型回复会做语音化规整，并拦截秘密关系、隔离可信成人、直接给作业最终答案等风险输出。
- 小白狐 TTS 后端主路径：已新增 `/api/v1/tts/xiaobaohu`、本地 wav 缓存和 TTS 数据策略闸门；测试阶段应启用 MiMo VoiceClone 或明确记录缺少的外部条件，Android 优先播放 `reply.audio_url`，系统 TTS 仅作异常兜底和诊断。
- Open Conversation Mode 小步实现：普通兴趣话题进入 `conversation.open`，ChildAgentRuntime 传入最近几轮短期 history；安全、隐私、学习、睡前边界仍由后端强约束。

已确认的下一阶段产品方向：

- 语音输入 ASR v1 目标已修订为后端本地 ASR 优先：第一选择是 sherpa-onnx + SenseVoice-Small int8；本地异常后再 fallback 到原有 MiMo ASR 路径。Android 不直接调用 MiMo，只负责点击录音、上传后端和儿童端语音状态。
- 儿童端默认 voice-first：ASR 成功且 transcript 非空后自动发送到 conversation stream；confirm-before-send 仅保留为 DevSettings / 父亲调试模式。
- 儿童默认隐藏文字输入框、发送按钮和可编辑 ASR 文本确认面板；保留重说、取消、停止朗读、静音等大按钮。
- App 打开儿童聊天页后，小白狐会请求 opening greeting；称呼优先 `child_nickname`，其次 `child_display_name`，都没有则不强行称呼。
- 小白狐正式品牌音色方案改为后端 MiMo VoiceClone：VoiceDesign 只用于音色筛选，VoiceClone 使用已下载 wav 样本生成 App 语音，普通 MiMo TTS 只做测试/兜底。
- TTS 默认自动朗读小白狐回复，必须提供停止/静音和 DevSettings 或父亲设置开关。
- Android 语音实现必须通过可替换抽象：`VoiceEngine`、`SpeechInputController`、`TtsController`；远程音频优先，系统 `VoiceProfile` 只作为 fallback。
- 默认不上传原始音频到后端，不长期保存原始音频。
- 正式名称为“小白狐”；UI、产品、设计和测试说明优先统一。代码 class 名 `FoxAgent` 暂可保留，后续如要改代码命名单独 refactor。
- 小白狐形象应温和、好奇、慢热友好；视觉目标优先 3D / soft 3D / 毛绒感 / 立体绘本感，Compose Canvas / 2D 只是 fallback；不做强刺激、排行榜、连击奖励或上瘾式动画。
- 后端继续通过 `reply.voice_enabled`、`reply.audio_url`、`reply.emotion` 和 `reply.agent_motion` 暴露表现层信号。
- 语音 QA 必须记录识别准确率、延迟、中文效果、儿童声音识别、TTS 自然度和孩子接受度。
- 新产品想法必须先写入 [docs/PRODUCT_DECISIONS_V0_1.md](docs/PRODUCT_DECISIONS_V0_1.md)，再进入子会话实现。
- 最新产品方向：不要继续增加固定任务场景；优先建设自由对话底座、父母寄语上下文和通用图片分享能力；“拍给小白狐看”当前测试路径必须走系统相机/相册真实图片上传和后端 MiMo vision。
- Ops v1 P0 已完成：request_id、JSON 结构化日志、request/model/TTS timing 和 `/api/v1/health/detail`。
- Streaming v1 已完成首版后端和 Android client，并完成 P0-A 延迟优化：`/api/v1/conversation/stream` 在完整安全回复切句后按 segment interleave `text_delta` / `tts_started` / `audio_ready`，旧 `/api/v1/conversation/message` 保留为 fallback。
- 本地 SenseVoice ASR 已作为正式 provider 接入 `/api/v1/asr/transcribe`；测试阶段应优先启用 `local_sensevoice` 并验证本地识别，异常时按配置 fallback 到原 MiMo ASR 路径。MiMo ASR provider 保留并受授权/policy gate 控制；Android 已接入录音上传和儿童默认自动发送，调试模式仍可显示待确认文本。真实儿童音频外发必须由父亲授权和 ASR data policy flags 控制。
- Opening greeting 首版已接入后端 `POST /api/v1/conversation/opening` 和 Android 启动请求；同一 session 只请求一次，TTS 失败不影响文本开场白。

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
- [docs/STREAMING_INTERACTION_DESIGN_V0_1.md](docs/STREAMING_INTERACTION_DESIGN_V0_1.md)
- [docs/OPS_FOUNDATION_GAP_ANALYSIS_V0_1.md](docs/OPS_FOUNDATION_GAP_ANALYSIS_V0_1.md)
- [docs/LOCAL_ASR_SENSEVOICE_DESIGN_V0_1.md](docs/LOCAL_ASR_SENSEVOICE_DESIGN_V0_1.md)
- [docs/ASR_INPUT_RESEARCH_V0_1.md](docs/ASR_INPUT_RESEARCH_V0_1.md)
- [docs/MIMO_ASR_INTEGRATION_DESIGN_V0_1.md](docs/MIMO_ASR_INTEGRATION_DESIGN_V0_1.md)

## 安全原则摘要

- 不把 AI 设计成孩子唯一的朋友或最懂孩子的人。
- 不要求孩子保密，不鼓励隐瞒父母、老师或可信成人。
- 学习求助默认引导思路，不直接给最终答案。
- 高风险输入要鼓励孩子告诉父母或可信成人，并触发父亲提醒。
- 不保存不必要的儿童原始音频、照片和长篇聊天原文。
- 不在 Android 端放模型 API key；真实 provider 只能由后端通过受控配置调用。

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
