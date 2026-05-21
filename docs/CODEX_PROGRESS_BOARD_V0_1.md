# Codex 进度看板 v0.1

用途：手动跟踪第一版开发进度。每次 Codex 完成任务或 PR 合并后更新。
状态值建议：`todo` / `planned` / `in_progress` / `review` / `done` / `blocked` / `deferred`

---

## 0. 总体状态

```text
当前版本：v0.1-dev
当前阶段：第一轮后端和 Android MVP 已完成，MiMo VoiceClone、动态小白狐和横屏双栏初步跑通；Freedom-first 第二轮与 Ops P0 已完成，Streaming v1 后端骨架已接入
当前目标：默认 conversation.open 自由交流；时间、父母寄语、记忆和图片作为上下文/能力；安全、隐私、学习和睡前边界作为护栏；流式链路先以后端 NDJSON skeleton 降低首字/首音频等待
下一步：真机复验自由对话、通用图片连续追问、父母寄语持久化和 MiMo audioUrl 播放；Android stream client、ASR 本地语音输入和 DB conversation message 持久化继续排队，不能按旧固定场景假设开发
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
| C0 | 项目准备 | 仓库、文档、AGENTS、README | done | 无 | 本地仓库规则和结构清晰，GitHub 远程已配置 |
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
| A2 | Android API | 接入 conversation API | done | Q1/A1 | 可请求后端并渲染 reply/ui_actions；session_state 内部保存，默认不展示给儿童 |
| A3 | Android 拍题 | Mock 拍题流程 | done | A2/M9 | mock attachment + conversation 连续调用可用 |
| A4 | 父亲设置/日报 | 设置目标、作息并查看日报 | done | A2/M2/M8 | policy 可修改，report 可读取 |
| E2E | 联调 | 后端 + Android 家庭内测流程 | in_progress | Q1/A1-A4 | 本机/LAN API 已通过；QA1 窗口模式模拟器复验覆盖基础聊天、放学后、学习入口、父亲入口点击保护和后端断开温和错误；父亲正确 PIN、设备侧完整 mock 拍题和真实平板仍待复验 |
| R1 | AgentRuntime | 统一智能体执行链路和输出安全检查 | done | Q1/E2E/R2 | conversation 编排收敛到 runtime，模型调用、输出检查和安全 fallback 边界已落地 |
| R2 | 模型外发安全闸门 | 真实模型接入前 child data gate | done | Q1 | 外发开关、数据最小化、审计和 fallback gate 可测 |
| R3 | 自动记忆闭环 | conversation 后自动抽取结构化记忆并进入日报素材 | done | M7/M8/R1 | 规则型摘要记忆写入、日报可见和 safety 检索隔离已测 |
| R4 | 安全场景细分 | 细分高风险类别和父亲提醒策略 | done | M5/M6/R1 | 高风险优先，WATCH/PRIVACY 分流可测，固定安全回复不完全依赖模型 |
| R5 | 父亲入口保护 | Android 父亲页访问保护 | done | A4/E2E | 长按父亲入口 + dev PIN 轻量保护，避免儿童轻易进入父亲设置和日报 |
| R6 | 对话体验加固 | 真实模型自由聊天质量、语音化输出和小白狐状态预留 | done | R1/A2 | 后端输出更适合语音；Android 轻量映射 emotion/motion；真实语音和复杂动画仍后置 |
| R7 | 完整设备 QA | 家庭内测前完整平板/模拟器手动验收 | in_progress | E2E/R1-R6 | QA1 已记录当前 v0.1+ 基础闭环事实；新增小白狐命名、语音输入确认、TTS 自动朗读、停止/静音、VoiceProfile、系统 ASR/TTS 评估和 3D/fallback 待验收项 |
| R8 | 产品决策同步 | confirmed decision 进入文档事实源 | done | R7 | 新想法先写入 PRODUCT_DECISIONS，再进入子会话实现 |
| V1 | 语音交互 v1 | Android 本地语音输入确认 + 后端小白狐 VoiceClone 输出 | in_progress | R7/R8 | 后端 TTS endpoint、mock/cache/policy guard 已接入；真实 MiMo VoiceClone smoke 和 conversation audioUrl 注入已通过；Android remote audioUrl 播放代码已完成，待 Redmi K60 真机 QA；系统 TTS 仅 fallback；SpeechRecognizer ASR 仍 todo |
| F1 | 小白狐体验 v1 | 3D/soft 3D 视觉资源和轻量动画状态机 | in_progress | R7/R8 | animation_v1 PNG 序列帧已接入 Android assets；保留静态 PNG 和 Canvas fallback；待 Redmi K60 / Honor Pad 5 设备 QA |
| DB1 | PostgreSQL 本地持久化 | 本地 PostgreSQL、迁移和核心表；逐步替换内存服务 | in_progress | Q1/R3/R8 | DB1-A 基础设施 done；B2-B5 业务持久化仍 todo |
| S-Stream | 流式交互 | 文本 delta + 分句/分段 TTS + Android 渐进显示/播放 | in_progress | V1/F1/R1 | 后端 NDJSON skeleton 已接入；旧 `/conversation/message` 保留；Android stream client 仍 todo |
| UI-Landscape | 横屏双栏 | 左侧动态小白狐，右侧对话交互，手机也横屏 | planned | F1/V1 | 不做完整美术重设计，不破坏 audioUrl 和 animation_v1 |
| Fox-Coverage | 小白狐状态覆盖 | 检查 11/12 状态资源、manifest、MascotState、业务触发和 QA | planned | F1 | 输出覆盖矩阵，未触发状态标记 resource_ready_but_not_triggered |
| ASR-Research | 语音输入调研 | 调研 MiMo ASR / audio input 能力和儿童语音数据边界 | done | V1 | 已读取父亲 MiMo ASR spec 并生成脱敏设计；云 ASR 默认 disabled，不上传真实儿童音频 |
| Ops-Foundation | 运行基础 | request_id、结构化日志、provider timing、health 扩展和 QA 记录 | in_progress | DB1/V1 | P0 thin slice 已完成：后端 request_id、JSON 日志、request/model/TTS timing、health/detail 和日志脱敏测试；Android 诊断和清理脚本后续 |
| Freedom-First | 自由对话底座 | 时段/父母寄语/图片/记忆作为上下文，安全/隐私/学习作为护栏 | done | R1/O1 | 学习触发已收窄；after_school/bedtime 不再强锁自由话题；父母寄语进入 prompt 并可 DB 持久化；普通图片后续快捷动作可带 image context 进入 LLM 上下文 |

---

## 2. 详细任务看板

### C0：项目准备

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| C0-01 创建 GitHub 仓库 | done |  | origin 已配置到 ronaldowzy/ai-child，可推送 main |
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
| M1-05 实现 conversation mock service | done |  | 返回小白狐回复 |
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
| A2-02 ui_actions 渲染 | done |  | 快捷按钮可显示；session_state 用于续会话和开发排查，默认不在儿童界面展示 |
| A3-01 Mock 拍题 | done |  | 题目流程跑通，不接真实 CameraX |
| A4-01 ParentSettingsScreen | done |  | policy 可修改 |
| A4-02 ParentReportScreen | done |  | report 可读取，不展示逐字聊天记录 |
| E2E-01 本机/LAN API QA | done |  | MANUAL_QA_V0_1.md 记录 S14_E2E_API: PASS |
| E2E-02 Android 模拟器基础 smoke | done |  | AVD 启动、App 安装、聊天 API、父亲日报读取通过 |
| E2E-03 Android 完整手动 QA | in_progress |  | QA1 通过窗口模式模拟器验证基础聊天、放学后、学习入口动作、父亲入口普通点击不进入、错误 PIN 不进入和后端不可达温和错误；正确 PIN、父亲设置修改、设备侧完整 mock 拍题和真实平板仍待复验 |
| E2E-04 Android 表达层 smoke | in_progress |  | 儿童端主要可见文案已改为“小白狐”；PNG 候选资源和 TTS speaking 联动已接入；仍需设备侧验证默认自动朗读、停止/静音、VoiceProfile 听感、系统 ASR、3D 资源/fallback 和低配降级 |

### 家庭内测前加固

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| R1-01 AgentRuntime 统一执行链路 | done |  | conversation 编排收敛到 ChildAgentRuntime；PromptManager、ModelRegistry、SafetyEngine 均在回复链路中执行 |
| R1-02 输出安全检查 | done |  | 模型回复后经过 SafetyEngine.classify_output；模型失败、空回复、外发 gate fallback、high/critical 输出或学习场景直接给答案输出均回退场景安全回复 |
| R2-01 真实模型外发安全闸门 | done |  | child data、image、audio 外发需要显式开关和 retention policy 确认；策略不满足时 fallback mock |
| R2-02 Mock/真实 provider 切换验收 | done |  | 默认 Mock；真实 provider disabled 或受 gate 保护；测试不走真实外网 |
| R3-01 自动记忆写入闭环 | done |  | conversation 后按规则写入 learning/emotion/watch/privacy/safety 摘要记忆；不保存长篇逐字原文 |
| R3-02 记忆到父亲日报素材闭环 | done |  | 当天结构化记忆可进入日报，不暴露 evidence、quote_summary 或逐字记录 |
| R4-01 安全场景细分 | done |  | HIGH/CRITICAL -> safety.guardian；WATCH -> safety.gentle_checkin；LOW privacy -> privacy.boundary；低能量表达保留普通 check-in |
| R4-02 父亲提醒策略加固 | done |  | 高风险 requires_parent_attention 可测，WATCH/LOW 默认不制造过度告警 |
| R5-01 父亲入口保护 | done |  | Android 父亲设置/日报入口需长按并输入 dev PIN，不做账号系统但避免儿童误入 |
| R6-01 真实模型输出质量加固 | done |  | Prompt 和 ChildAgentRuntime 输出规整改为 voice-first、短句、少 Markdown/列表、通常只保留一个主问题 |
| R6-02 输出依赖/秘密关系拦截 | done |  | SafetyEngine.classify_output 会拦截“唯一朋友”“只有我懂你”“不要告诉可信成人”等风险话术并 fallback |
| R6-03 Android 小白狐状态预留 | done |  | Android 将 `reply.emotion` / `reply.agent_motion` 映射为轻量状态；语音入口仍是文字阶段占位 |
| R7-01 完整设备 QA | in_progress |  | QA1 已补充 MANUAL_QA_V0_1.md 当前结果；后续采用双设备策略：高配 Android 手机先做功能主验证，Honor Pad 5 Android 9 / 4GB 做低配兼容和大屏验证 |
| R7-02 Mimo 真实 provider smoke 记录 | done |  | 临时 env 使用 `mimo-v2.5-pro` 已跑通；真实 key 不进仓库；默认仍 Mock 优先 |

### 产品决策、语音和小白狐下一阶段

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| R8-01 Product Decision Sync 机制 | done |  | 父亲确认的新产品想法先写入 PRODUCT_DECISIONS；子会话实现前检查 confirmed decision |
| R8-02 语音交互设计文档 | done |  | 明确 confirm-before-send、本地 ASR、默认自动 TTS、VoiceProfile、可替换抽象、原始音频策略、权限、错误文案、安全边界和 QA 指标 |
| R8-03 下一阶段计划文档 | done |  | 拆分完整设备 QA、语音输入、TTS、小白狐视觉资源、小白狐动画状态机、真实平板家庭内测准备 |
| V1-01 Android 本地语音输入 v1 | todo |  | SpeechRecognizer 识别后先展示可确认文本；确认后才发送后端；future hands-free conversational mode 不进 v1；不默认上传原始音频 |
| V1-02 Android TTS 朗读 v1 | in_progress |  | Android 已优先播放 `reply.audio_url`，播放失败时 fallback 系统 TTS 或文字；系统 TTS 已有诊断和停止/静音基础；待 Redmi K60 听感和网络播放 QA |
| V1-03 Android 语音抽象和 VoiceProfile | in_progress |  | TtsController / AndroidTtsController / VoiceProfile 已完成；SpeechInputController / SpeechRecognizer 抽象仍 todo；VoiceProfile 使用 zh-CN、稍慢语速、偏高不过度音高和系统中文 fallback |
| V1-04 语音 QA 指标记录 | todo |  | 记录识别准确率、延迟、中文效果、儿童声音识别、TTS 自然度和孩子接受度 |
| V1-05 TTS-D1 可观测性与故障修复 | done |  | 新增 TtsUiState / VoiceDiagnostics 诊断，记录 engine、locale、voice、setLanguage、setVoice、speak 返回值和 failure reason；speaking 状态前移到请求接受阶段；新增 TTS 设置/语音数据入口 |
| V1-06 后端小白狐 TTS endpoint | done |  | 新增 `/api/v1/tts/xiaobaohu`、TTS schema、mock/MiMo VoiceClone provider 抽象、TtsDataPolicyGuard、本地 wav 缓存和 `/media/tts/...wav` 受控服务；默认不外发；真实 smoke 已确认 `/chat/completions` + `choices[0].message.audio.data` 可生成 RIFF/WAV |
| V1-07 Android remote audioUrl 播放 | done |  | Android 收到 `reply.audio_url` 时优先播放远程音频；失败时 fallback 系统 TTS 或文字；朗读时小白狐切 speaking；Android conversation read timeout 已从 12s 调整为 45s，避免 MiMo TTS 同步生成接近 10s 时误报断网 |
| F1-01 小白狐视觉资源 v1 | in_progress |  | v1 候选资源已扩展：neutral_idle、listening、speaking、jumping_happy、thinking、calm、sleepy、safety_concern、privacy_boundary、homework_focus、network_error；目标是 3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感 |
| F1-02 小白狐 PNG 资源接入 | in_progress |  | 已新增 drawable-nodpi 候选资源、FoxAgentAssetMapper 和 DevSettings.FOX_ASSET_MODE；保留 Canvas fallback；6 张新增状态图已接入资源目录和映射，后续需设备侧验证图片显示和低配降级 |
| F1-03 小白狐动画状态机 v1 | in_progress |  | 已接入 manifest-driven animation_v1、MascotController、FrameSequencePlayer 和三层 fallback；覆盖 11 个状态、12 FPS、24 帧序列；Android test/assemble/lint 通过；debug APK 约 147MB，待真机验证流畅度和低配降级 |
| O1-01 Open Conversation Mode 小步实现 | done |  | 普通兴趣和日常话题进入 `conversation.open`；ChildAgentRuntime 接收进程内短期 history；普通聊天 quick actions 随上下文轻量变化；安全、隐私、学习、睡前边界保留 |
| DB1-A PostgreSQL 基础设施 | done |  | 新增 SQLAlchemy sync、psycopg、Alembic、PostgreSQL 16 local compose、初始 8 张表、migration/reset 脚本和基础测试；业务服务仍未迁移 |
| DB1-B ParentPolicy 持久化 | done |  | ParentPolicyService 已支持 PostgreSQL repository 优先读写；数据库不可用时 dev fallback 到内存；`parent_message_raw` 和 `parent_message_updated_at` 已有迁移 |
| DB1-C Conversation message 持久化 | todo |  | 保存 child/agent message、audio_url、emotion、agent_motion；不保存 debug、原始音频或照片 |
| DB1-D MemoryService 持久化 | todo |  | 结构化 memory_items 落库，evidence 继续使用 summary，不保存 full transcript |
| DB1-E ParentReport 持久化 | todo |  | 日报生成结果可持久化，仍不展示逐字聊天记录 |
| S-Stream-0 流式架构设计 | done |  | 新增 `STREAMING_INTERACTION_DESIGN_V0_1.md`；确认 NDJSON、事件结构、pseudo streaming、fallback 和 QA 指标 |
| S-Stream-1 后端 stream endpoint | done |  | 新增 `/api/v1/conversation/stream` NDJSON skeleton；保留旧接口；复用 ConversationService/Runtime 安全链路；按句子 pseudo streaming 和可恢复 TTS segment error |
| S-Stream-2 Android stream client | todo |  | 渐进文本气泡 + audio segment queue；stream 失败 fallback 旧接口 |
| UI-Landscape-1 横屏双栏布局 | done |  | Android 主界面已改为 sensorLandscape 横屏：左侧约 41% 小白狐，右侧约 59% 消息和输入；Android test/assemble/lint 通过，待真机视觉 QA |
| Fox-Coverage-1 动态小白狐覆盖矩阵 | done |  | 新增 `FOX_AGENT_STATE_COVERAGE_V0_1.md`；manifest 确认 11 个状态，每状态 24 帧；记录 oneshot_hold 后续 QA 风险 |
| ASR-Research-0 MiMo ASR 调研 | done |  | 新增 `ASR_INPUT_RESEARCH_V0_1.md` 和 `MIMO_ASR_INTEGRATION_DESIGN_V0_1.md`；确认候选模型、非流式 audio input、格式、30s 上限和数据留存缺口 |
| ASR-Skeleton-0 后端 mock skeleton | done |  | 新增 ASR schema/service/provider/policy guard 和未挂载 router；默认 mock，MiMo ASR disabled，真实儿童音频外发仍被 policy guard 阻断 |
| Ops-Foundation-1 运行基础缺口分析 | done |  | 新增 `OPS_FOUNDATION_GAP_ANALYSIS_V0_1.md`；首批聚焦 request_id、结构化日志、provider timing、health 扩展和脚本统一 |
| Ops-Foundation-2 P0 后端可观测性骨架 | done |  | 新增 request_id middleware、结构化 JSON 日志、request/model/TTS timing、`/api/v1/health/detail` 和日志脱敏测试；不接第三方 APM |

---

## 3. 当天记录

### 日期：2026-05-21

```text
今日目标：先完成 Ops v1 P0 thin slice，为 Streaming v1 后端实现提供 request_id、provider timing 和 health/detail 诊断骨架；随后启动 Streaming v1 后端 skeleton，并完成 ASR spec intake/design lock。
完成任务：后端新增 request_id middleware，支持安全 `X-Request-ID` 透传和非法/超长值替换；日志改为单行 JSON structured log；request timing 记录 `request_finished` / `request_failed`；ModelRegistry 记录 `model_call_finished`；TtsService 记录 `tts_call_finished`；新增 `/api/v1/health/detail`，覆盖 postgres、tts_cache、小白狐 voice sample 和 MiMo TTS 配置状态；新增测试覆盖 request_id、日志脱敏、model/TTS timing、health/detail API key 不泄露、postgres degraded 和 tts_cache degraded。后续新增 `/api/v1/conversation/stream` NDJSON skeleton，事件覆盖 session_started、route_decision、text_delta、sentence_ready、tts_started、audio_ready、text_final、done/error；stream 复用现有 ConversationService/Runtime 安全链路，保留旧 `/conversation/message`。已读取父亲本机 MiMo ASR spec，未发现真实 API key、真实儿童信息或敏感音频路径；生成脱敏 ASR 研究和集成设计文档；新增 ASR schema/service/provider/policy guard skeleton，但 ASR router 尚未挂载到 main，云 ASR 默认 disabled。
阻塞问题：无代码阻塞；Android 端尚未生成 `X-Request-ID`，后续 Android 诊断任务再接；Android stream client 和 Android ASR 录音链路仍未实现。
Codex 偏差：无；本轮未做 Android stream client、未做 Android ASR 录音 UI、未改 UI 美术、未做 DB 全量迁移。
需要补充到 AGENTS.md 的规则：暂无。
明日第一任务：启动 S-Stream-2 Android stream client 设计/实现前先做手动 curl QA 和 Android 接入计划；ASR 下一步只做本地 SpeechRecognizer confirm-before-send 或 dev-only ASR endpoint 审批，不直接外发真实儿童音频。
```

### 日期：2026-05-19

```text
今日目标：完成 S13 Android 拍题与父亲页验收，推进 S14 本机/API 联调和 S20a 文档同步，进入 AgentRuntime、模型外发安全闸门、自动记忆闭环、安全场景细分、父亲入口保护和家庭内测前加固阶段。
完成任务：Android mock 拍题流程已接入 attachment API 和 conversation API；父亲设置页可读取/保存 goals、沟通偏好和作息时间；父亲日报页可读取后端日报摘要；S14 本机 health、LAN health、E2E API 合约检查通过；新增共享上下文、环境 doctor 和 Android Gradle 包装脚本；已安装 Android Emulator，创建 child_ai_tablet_api35 AVD，并完成 App 安装、聊天 API、父亲日报基础 smoke；Android test、assembleDebug、lintDebug 通过；S20a 修正文档中过期的 C0/未初始化描述，并补齐多会话协同规则和后续子会话提示词；S16 已完成模型外发安全闸门；S19 已完成 Android 父亲入口长按 + dev PIN 轻量保护；S15 已完成 ChildAgentRuntime 主回复链路，默认 mock-first，模型失败/空回复/高风险输出回退 SceneRouteDecision.reply_text；S18 已完成安全场景细分，HIGH/CRITICAL 进入 safety.guardian，WATCH 进入 safety.gentle_checkin，LOW privacy 进入 privacy.boundary，低能量表达不进 guardian；S17 已完成规则型自动记忆闭环，conversation 会在 runtime 前检索非 safety 记忆，并在路由后写入结构化摘要记忆，父亲日报可读取当天自动记忆素材；S24 已完成真实模型输出质量加固，回复更适合语音播报并拦截秘密关系/唯一朋友/隔离可信成人风险话术；S25 已完成 Android 小白狐轻量状态映射和语音占位 UI；本轮补充小白狐 v1 候选资源、双设备测试策略、预渲染 PNG/WebP + 轻量 Compose 动画原则、FoxAgentAssetMapper 和低配 fallback 规则；V2 已完成 Android 本地 TTS v1 代码接入，支持默认自动朗读、停止/静音、VoiceProfile 和小白狐 speaking 状态联动；Redmi K60 截图显示上一版 TTS 为 SKIPPED_UNAVAILABLE，TTS-D1 已补 TTS service 查询、初始化竞态修复、系统朗读设置入口和诊断；6 张新增小白狐状态图已进入资源接入流程；Open Conversation Mode 已完成小步后端实现，普通话题进入 conversation.open 并传入短期 history；当前 8000 后端已改为加载本地忽略 `.env` 的 Mimo 配置，Mimo 超时调为 30000ms，普通恐龙话题 smoke 已返回真实模型回复。
阻塞问题：无硬阻塞；完整设备侧手动 QA 仍需继续执行；Mimo 真实 provider 已用临时 env smoke 通过，后续不得重复使用错误模型 id `mimo-v2.5pro`。
Codex 偏差：S14 子会话把裸 Gradle 的 Java Runtime 报错误判为本机缺少 JDK；主控会话已修正为共享环境未加载问题，并固化标准入口。
需要补充到 AGENTS.md 的规则：暂无。
今日补充：voice sample 已确认在 `backend/assets/voices/xiaobaohu_voice_v01.wav`，sha256=`8eec0f98629350a1dd09bd98a31c2bee80132128bf214d4c0a009331c9a66c40`；`scripts/smoke_mimo_tts.sh` 已通过真实 MiMo VoiceClone 验证，`/api/v1/tts/xiaobaohu` 和 conversation 自动 `reply.audio_url` 均能返回可下载 RIFF/WAV。
真机反馈：Redmi K60 已听到 MiMo 小白狐音频，动态小白狐形象已出现；但整体等待时间长，不能继续靠提高 read timeout 解决体验。下一阶段转向流式交互、横屏双栏、动态状态覆盖矩阵、MiMo ASR 调研和运行基础组件补齐。
明日第一任务：启动 S-Stream-1 后端 stream endpoint 与 S-Stream-2 Android stream client；并并行开展 ASR-Research-0 和 Ops P0 小步实现。
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
