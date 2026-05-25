# Codex 进度看板 v0.1

用途：手动跟踪第一版开发进度。每次 Codex 完成任务或 PR 合并后更新。
状态值建议：`todo` / `planned` / `in_progress` / `review` / `done` / `blocked` / `deferred`

---

## 0. 总体状态

```text
当前版本：v0.1-dev
当前阶段：第一轮后端和 Android MVP 已完成，MiMo VoiceClone、动态小白狐和横屏双栏初步跑通；Freedom-first 第二轮与 Ops P0 已完成，Streaming v1 后端和 Android 首版 client 已接入，并完成 segment-level interleaved TTS quick win；Android ASR 已改为儿童默认 voice-first 自动发送；ASR 真实识别主路径已修订为后端本地 SenseVoice 优先、MiMo fallback，local_sensevoice 已用非儿童合成中文 WAV smoke 跑通；“拍给小白狐看”已从儿童端默认 mock attachment 改为系统相机/相册真实图片 multipart 上传 + 后端 MiMo vision 路径，普通 child_chat 仍用 `mimo-v2.5-pro`，vision/OCR/multimodal 用 `mimo-v2.5`；opening greeting 首版和家长设置孩子称呼 UI 已接入；家庭内测前 smoke 脚本、QA checklist、debug APK metadata、本地 PostgreSQL 自动 setup、ASR 状态核对和 MiMo vision opt-in smoke 已补齐；child_chat prompt 已新增儿童语音表达理解和 turn_guidance runtime section；Healthy Engagement 总体设计已进入 docs，并完成 output contract / quick actions / output safety 快速落地；E1 Relationship Memory / Interest Seed thin slice、E1.1 hardening、E2-A Opening Policy Foundation、DEV-TRACE-1 本地模型调用 trace、DEV-TRACE-2 synthetic trace scenario review、DEV-TRACE-3 real MiMo synthetic trace review 和 MVP-CLOSEOUT-1 historical opening deterministic default 已接入后端；家长日报已按 PD-052 从 deterministic v1 修订为 model-first v2，正式成功只接受 `ModelTaskType.PARENT_REPORT` 结构化模型输出；PD-053 已加固真机 QA 暴露的 opening 冷启动等待、图片拒看和 stream TTS 混播问题；Experience Optimization E1-01 Android unified interaction state thin slice 已接入，儿童可见 Ready/Listening/Recognizing/Thinking/Speaking/ImageProcessing/NeedsRetry/PermissionNeeded/ServiceError 状态由 reducer 统一派生；Parallel Experience Foundation Lane A 已补 voice-first 下 TTS pending/speaking 的“停一下”和“静音/打开朗读”，Lane B 已补 backend age-banded replies 与连续追问 throttle thin slice；Task 03 Lane A 已补普通图片具体安全细节回复和 Android 本地图片确认卡，Lane B 已补儿童端家长入口降噪与家长日报“今晚可以怎么接一句”；Task 04 已补 Healthy Engagement 非原文观测、家庭内测 QA runbook 和小白狐 phase/scene 状态覆盖矩阵；Task 09 已完成一个孩子一个账号的家长代创建/登录薄片、父亲->家长产品文案迁移、model-driven conversation_control、personalized opening v2 和后端生成 interest-aware topic choices；Task 10 已完成 Task 09 closeout：auth/session 覆盖高影响路由、opening timing + TTS soft timeout、conversation_control/topic choices trace hardening 和新 QA APK 包
当前目标：默认 conversation.open 自由交流；时间、家长寄语、记忆和图片作为上下文/能力；安全、隐私、学习和睡前边界作为护栏；儿童默认用语音发起对话，小白狐启动时主动短开场；流式链路用后端 NDJSON pseudo streaming + segment interleaved TTS + Android 渐进气泡/audio segment queue 降低同步等待感
下一步：安装 Task 10 QA APK，在 Redmi K60 / Honor Pad 5 复验注册、登录、保持登录、退出登录、失效 token 回登录、家长设置/日报默认登录态进入、opening v2 首屏 Ready 不阻塞、opening timing request_id 采集、孩子先开口时迟到 opening 不插入、CS/game 短答 conversation_control soft_shift、high-engagement 继续当前话题、后端生成 topic choices 可读且不挤压 voice-first/TTS 控件、ASR 权限/录音/自动发送/重说取消、系统相机真实拍照/相册上传、本地图片确认卡、MiMo vision 识图与后续图片续聊、stream 渐进文字、MiMo 分段音频、voice-first 下“停一下”和“静音/打开朗读”可见并生效、TTS latency logcat/backend timing 对齐、TTS 失败不混播系统音色、小白狐状态覆盖，以及低配横屏输入栏是否挤占消息区；没有同一慢 turn 的 backend `request_id` + Android `XiaobaohuTtsTiming` logcat + 视频时间点前，不做猜测式 latency 修复；后端仍需用真实模型继续观察 age-banded replies、model-driven conversation_control、opening v2、Healthy Engagement boundary metrics 和家长日报 bridge 文案自然度；ParentReport v2 为 model-first，模型失败时不展示规则日报冒充成功；未接 CameraX，不做完整 family/multi-child/multi-guardian 账号体系
```

第一轮已完成能力快照：

```text
后端骨架：done
Android 壳：done
Conversation API：done
真实图片上传：in_progress
家长设置/日报：review
```

---

## 1. Milestone 总览

| ID | 阶段 | 目标 | 状态 | 依赖 | 验收摘要 |
|---|---|---|---|---|---|
| C0 | 项目准备 | 仓库、文档、AGENTS、README | done | 无 | 本地仓库规则和结构清晰，GitHub 远程已配置 |
| M1 | 后端骨架 | FastAPI + health + conversation mock | done | C0 | pytest 通过，mock 会话可用 |
| M2 | 时间与家长策略 | TimeContext + ParentPolicy | done | M1 | time_period 和家长目标注入会话 |
| M3 | 模型抽象 | ModelRegistry + provider abstraction | done | M1 | 业务不绑定具体模型 |
| M4 | Prompt 管理 | PromptManager + 分层模板 | done | M3 | 场景 prompt 可组合 |
| M5 | 安全与意图 | SafetyEngine + IntentClassifier | done | M2 | 高风险优先，意图识别可测 |
| M6 | 场景编排 | SceneOrchestrator + 四类场景 | done | M5 | 动态场景切换可用 |
| M7 | 记忆系统 | MemoryService + MemoryExtractor mock | done | M6 | 结构化记忆可写可查，pytest/ruff 通过 |
| M8 | 家长日报 | ParentReportService | review | M7 | deterministic v1 已完成；model-first v2 已接入，等待真实 provider/家长端 QA |
| M9 | 附件/OCR/Vision | Attachment + OCR/Vision foundation | done | M6 | 附件上下文可接入学习/图片分享，pytest/ruff 通过 |
| Q1 | 后端硬化 | scenario tests + 本地质量脚本 + demo scripts | done | M1-M9 | pytest/ruff/demo 通过，后端 MVP 可稳定验收 |
| A1 | Android 壳 | Compose 静态聊天 UI | done | C0 | Android 可编译，单元测试通过 |
| A2 | Android API | 接入 conversation API | done | Q1/A1 | 可请求后端并渲染 reply/ui_actions；session_state 内部保存，默认不展示给儿童 |
| A3 | Android 图片输入 | 系统相机/相册真实上传 + attachment 续聊 | in_progress | A2/M9 | 儿童默认入口已改为真实图片 multipart 上传；mock attachment 仅保留为测试/异常替身；真机相机和 MiMo vision 仍待设备 QA |
| A4 | 家长设置/日报 | 设置目标、作息并查看日报 | review | A2/M2/M8 | policy 可修改；ParentReportScreen 已识别 model-first 成功/失败状态，真机 QA 待验 |
| E2E | 联调 | 后端 + Android 家庭内测流程 | in_progress | Q1/A1-A4 | 本机/LAN API 已通过；QA1 历史设备 smoke 曾覆盖基础聊天、放学后、学习入口、家长入口点击保护和后端断开温和错误；家长正确 PIN、系统相机真实拍照上传、MiMo vision 识图和真实平板仍待复验 |
| R1 | AgentRuntime | 统一智能体执行链路和输出安全检查 | done | Q1/E2E/R2 | conversation 编排收敛到 runtime，模型调用、输出检查和安全 fallback 边界已落地 |
| R2 | 模型外发安全闸门 | 真实模型接入前 child data gate | done | Q1 | 外发开关、数据最小化、审计和 fallback gate 可测 |
| R3 | 自动记忆闭环 | conversation 后自动抽取结构化记忆并进入日报素材 | done | M7/M8/R1 | 规则型摘要记忆写入、日报可见和 safety 检索隔离已测 |
| R4 | 安全场景细分 | 细分高风险类别和家长提醒策略 | done | M5/M6/R1 | 高风险优先，WATCH/PRIVACY 分流可测，固定安全回复不完全依赖模型 |
| R5 | 家长入口保护 | Android 家长页访问保护 | done | A4/E2E | 长按家长入口 + dev PIN 轻量保护，避免儿童轻易进入家长设置和日报 |
| R6 | 对话体验加固 | 真实模型自由聊天质量、语音化输出和小白狐状态预留 | done | R1/A2 | 后端输出更适合语音；Android 轻量映射 emotion/motion；真实语音和复杂动画仍后置 |
| R7 | 完整设备 QA | 家庭内测前完整平板手动验收 | in_progress | E2E/R1-R6 | QA1 已记录当前 v0.1+ 基础闭环事实；Task 04 新增 `QA_FAMILY_BETA_CHECKLIST_V0_1.md` 统一 Redmi K60 / Honor Pad 5 runbook；真机状态仍为 NOT_RUN |
| R8 | 产品决策同步 | confirmed decision 进入文档事实源 | done | R7 | 新想法先写入 PRODUCT_DECISIONS，再进入子会话实现 |
| V1 | 语音交互 v1 | 后端本地 SenseVoice ASR voice-first 自动发送 + 后端小白狐 VoiceClone 输出 | in_progress | R7/R8 | 后端 TTS endpoint、cache/policy guard 已接入；真实 MiMo VoiceClone smoke 和 conversation audioUrl 注入已通过；ASR v1 目标已修订为本地 SenseVoice 优先、MiMo fallback，provider 和 endpoint 已接入；local_sensevoice 本机非儿童 synthetic WAV smoke PASS；Android ASR 录音上传和儿童默认自动发送已接入，调试确认模式保留，待真机 QA |
| F1 | 小白狐体验 v1 | 3D/soft 3D 视觉资源和轻量动画状态机 | in_progress | R7/R8 | animation_v1 runtime 已优化为 512px WebP 序列帧，Android assets 约 4.9MB；静态 fallback 已压缩为 WebP，保留 Canvas fallback；待 Redmi K60 / Honor Pad 5 设备 QA |
| DB1 | PostgreSQL 本地持久化 | 本地 PostgreSQL、迁移和核心表；逐步替换内存服务 | done | Q1/R3/R8 | DB1-A 基础设施 done；B2 ParentPolicy thin slice done；B3 conversation message/stream turn thin slice done；B4 MemoryService thin slice done；B5 ParentReportService thin slice done；当前是本地家庭库，不是云端多租户 |
| S-Stream | 流式交互 | 文本 delta + 分句/分段 TTS + Android 渐进显示/播放 | in_progress | V1/F1/R1 | 后端 NDJSON skeleton 已接入；segment-level interleaved TTS 已完成；Android 首版 stream client、渐进 agent bubble 和 audio segment queue 已接入；旧 `/conversation/message` 保留为 fallback |
| EXP-E1 | Android 统一交互状态 | child-facing phase reducer 统一 ASR、stream、TTS、图片、错误态和小白狐反馈 | done | V1/F1/S-Stream | 新增 `ChildTurnUiPhase` / `ChildInteractionPresentation` thin slice；InputBar 主按钮、状态短语、小白狐 agent、TTS “停一下”、静音 toggle 和图片按钮可见性从统一 presentation 派生；真机布局仍待 Redmi K60 / Honor Pad 5 QA |
| EXP-E2 | 分龄回复与追问节制 | Backend age-banded replies and question throttle thin slice | done | R1/Freedom-First/HE-01 | PromptManager 注入 `age_band` / `reply_char_budget` / `question_policy`；ChildAgentRuntime 按 age band 做长度规整并在连续问句、边界、纠错时移除新追问钩子；不改 DB schema 或 Android |
| EXP-E3 | 图片分享具体看见 | Image sharing specific response + local thumbnail thin slice | done | M9/A3/Freedom-First | 后端普通图片在安全且高置信时从 recognized_content 提取一个短具体细节；低置信不假装看见；Android 拍照/相册发送后显示本地临时图片确认卡；不接 CameraX，不保存 raw photo 到长期记忆；Redmi K60 / Honor Pad 5 真机 QA 待验 |
| EXP-E4 | 家长入口与现实接话桥 | Parent entry deemphasis + father report bridge thin slice | done | A4/M8/Healthy Engagement | 儿童端家长入口默认收敛为小“大人”按钮，点击只提示、长按 + PIN 后仍可进日报/设置；家长日报支持 `tonight_parent_bridge` 并顶部显示“今晚可以怎么接一句”；失败态不暴露后端/model/provider/config；不做生产级 auth；真机 QA 待验 |
| UI-Landscape | 横屏双栏 | 左侧动态小白狐，右侧对话交互，手机也横屏 | planned | F1/V1 | 不做完整美术重设计，不破坏 audioUrl 和 animation_v1 |
| Fox-Coverage | 小白狐状态覆盖 | 检查 11/12 状态资源、manifest、MascotState、业务触发和 QA | done | F1 | Task 04 已在 `FOX_AGENT_VISUAL_DESIGN_V0_1.md` 补 phase/scene 覆盖矩阵，并新增 `XiaobaohuStateCoverageTest` 固定 phase -> Fox/Mascot 映射；真机动画表现仍待 QA |
| ASR-Research | 语音输入调研 | 调研本地 SenseVoice、MiMo ASR fallback 和儿童语音数据边界 | done | V1 | 家长已确认 ASR v1 本地 SenseVoice 优先、MiMo fallback；已生成本地 ASR 设计和 MiMo 脱敏设计；真实儿童音频外发仍受 policy gate 控制 |
| Ops-Foundation | 运行基础 | request_id、结构化日志、provider timing、health 扩展和 QA 记录 | in_progress | DB1/V1 | P0 thin slice 已完成：后端 request_id、JSON 日志、request/model/TTS timing、health/detail 和日志脱敏测试；Task 04 已补 `app.healthy_engagement` 非原文结构化观测；Android 诊断和清理脚本后续 |
| Freedom-First | 自由对话底座 | 时段/家长寄语/图片/记忆作为上下文，安全/隐私/学习作为护栏 | done | R1/O1 | 学习触发已收窄；after_school/bedtime 不再强锁自由话题；家长寄语进入 prompt 并可 DB 持久化；普通图片后续快捷动作可带 image context 进入 LLM 上下文 |

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

### M2：时间与家长策略

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
| M3-04 OpenAICompatibleProvider skeleton | done |  | 需显式配置验证 |
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
| M6-06 safety scene | done |  | 家长提醒 |
| M6-07 routing_decision | done |  | 可记录或 debug |

### M7-M9：记忆、日报、多模态占位

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| M7-01 MemoryItem | done |  | 字段完整，含 evidence/confidence/expires_at/sensitivity |
| M7-02 MemoryRepository | done |  | 内存版可写可查 |
| M7-03 MemoryService | done |  | 过滤过期记忆，普通检索默认隔离 safety |
| M7-04 MemoryExtractor mock | done |  | 输出结构化记忆 |
| M8-01 ParentReport schema | done |  | 字段完整 |
| M8-02 ParentReportService deterministic v1 | done |  | 今日摘要可生成，不返回逐字聊天记录 |
| M8-03 ParentReportService model-first v2 | review |  | 正式日报主路径调用 `ModelTaskType.PARENT_REPORT`；模型失败返回可重试状态，不用规则日报冒充成功；`mimo_parent_report` 已使用独立 completion budget，避免短 token 限制导致真实模型空输出 |
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
| A3-01 系统相机真实图片上传 | in_progress |  | Android 调系统相机/相册并 multipart 上传；后端返回真实 attachment_id；发送后显示本地临时图片确认卡；CameraX 不在本轮范围；真机 QA 待验 |
| A4-01 ParentSettingsScreen | done |  | policy 可修改 |
| A4-02 ParentReportScreen | review |  | report 可读取；顶部显示“今晚可以怎么接一句”；model_failed/model_blocked 时展示“今天的小结还没准备好，请稍后再试”，不展示 fallback 正文或工程诊断；家长日报 client read timeout 已调到 70s 覆盖 model-first 首次生成耗时；真机 QA 待验 |
| E2E-01 本机/LAN API QA | done |  | MANUAL_QA_V0_1.md 记录 S14_E2E_API: PASS |
| E2E-02 Android 历史基础 smoke | done |  | 历史 App 安装、聊天 API、家长日报读取通过 |
| E2E-03 Android 完整手动 QA | in_progress |  | QA1 通过历史设备 smoke 验证基础聊天、放学后、学习入口动作、家长入口普通点击不进入、错误 PIN 不进入和后端不可达温和错误；正确 PIN、家长设置修改、设备侧完整 mock 拍题和真实平板仍待复验 |
| E2E-04 Android 表达层 smoke | in_progress |  | 儿童端主要可见文案已改为“小白狐”；PNG 候选资源、TTS speaking 联动、后端 ASR voice-first 自动发送和 opening greeting 已接入；仍需设备侧验证默认自动朗读、停止/静音、VoiceProfile 听感、录音上传、3D 资源/fallback 和低配降级 |

### 家庭内测前加固

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| R1-01 AgentRuntime 统一执行链路 | done |  | conversation 编排收敛到 ChildAgentRuntime；PromptManager、ModelRegistry、SafetyEngine 均在回复链路中执行 |
| R1-02 输出安全检查 | done |  | 模型回复后经过 SafetyEngine.classify_output；模型失败、空回复、外发 gate fallback、high/critical 输出或学习场景直接给答案输出均回退场景安全回复 |
| R2-01 真实模型外发安全闸门 | done |  | child data、image、audio 外发需要显式开关和 retention policy 确认；策略不满足时 fallback mock |
| R2-02 Mock/真实 provider 切换验收 | done |  | 当前测试阶段真实 provider smoke 必须使用临时 env 和 policy gate 验证；单元测试仍使用 test double |
| R3-01 自动记忆写入闭环 | done |  | conversation 后按规则写入 learning/emotion/watch/privacy/safety 摘要记忆；不保存长篇逐字原文 |
| R3-02 记忆到家长日报素材闭环 | done |  | 当天结构化记忆可进入日报，不暴露 evidence、quote_summary 或逐字记录 |
| R4-01 安全场景细分 | done |  | HIGH/CRITICAL -> safety.guardian；WATCH -> safety.gentle_checkin；LOW privacy -> privacy.boundary；低能量表达保留普通 check-in |
| R4-02 家长提醒策略加固 | done |  | 高风险 requires_parent_attention 可测，WATCH/LOW 默认不制造过度告警 |
| R5-01 家长入口保护 | done |  | Android 家长设置/日报入口需长按并输入 dev PIN，不做账号系统但避免儿童误入 |
| R6-01 真实模型输出质量加固 | done |  | Prompt 和 ChildAgentRuntime 输出规整改为 voice-first、短句、少 Markdown/列表、通常只保留一个主问题 |
| R6-02 输出依赖/秘密关系拦截 | done |  | SafetyEngine.classify_output 会拦截“唯一朋友”“只有我懂你”“不要告诉可信成人”等风险话术并 fallback |
| R6-03 Android 小白狐状态预留 | done |  | Android 将 `reply.emotion` / `reply.agent_motion` 映射为轻量状态；语音入口已推进到后端 ASR 录音上传和儿童默认自动发送，仍需真机 QA |
| R6-04 儿童语音 prompt guidance | done |  | global/scene prompt 新增儿童表达理解、话题换轨和睡前收尾；ChildAgentRuntime 注入 `turn_guidance`；Safety/Intent 对运动语境夸张疲惫按 watch-lite 处理；家长日报不把运动比赛误报学习求助 |
| HE-01 Healthy Engagement 总体设计 | done |  | `HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md` 已作为下一阶段产品优化指导进入 docs；产品目标改为健康依恋、主动回访和成长陪伴习惯，禁止签到压力、FOMO、排行榜、抽卡、情感勒索和排他依恋 |
| HE-02 Healthy Engagement 快速落地 | done |  | child_chat output contract 增加健康使用边界和现实连接；Open conversation quick actions 默认提供继续说、换个话题、讲个小故事、今天不聊了；SafetyEngine 拦截留存压力输出 |
| HE-03 Relationship Memory / Interest Seed | done |  | E1/E1.1 thin slice：ConversationMemoryHooks 从儿童自然对话中规则提取低敏 `interest_seed`、`topic_boundary`、`proud_moment`，并加固比赛/创作误伤、跨 session 去重、best-effort 写入；Opening 只回访最新低敏兴趣种子并加强回访安全约束；ParentReportService 生成低压力现实接话建议。不触碰 Android runtime/assets、DB schema/migration；Opening v2 完整产品化和真机 QA 仍未完成 |
| HE-04 Opening Greeting v2 Policy Foundation | done |  | E2-A done：新增 `OpeningPolicyBuilder` / `OpeningPolicy`，集中判断 `opening_mode`、兴趣回访资格、topic boundary 冷却、睡前收束、分龄长度、家长目标低压力转译和 forbidden phrases；MVP-CLOSEOUT-1 后 `OpeningService` 默认使用 deterministic policy template，model opening 仅保留为 dev/test 实验 helper，不作为家庭内测主路径。未触碰 Android runtime/assets、DB schema/migration；Opening v2 完整产品化、Redmi K60 / Honor Pad 5 真机 QA 和 CameraX 仍未完成 |
| HE-05 Healthy Engagement observability | done |  | Task 04 thin slice：后端在 runtime/conversation/stream 链路生成 `healthy_engagement_turn` / `healthy_engagement_stream` 非原文结构化日志，覆盖 boundary_signal、boundary_respected、previous_topic_revived、question_count、consecutive_recent_questions、age_band、scene、reply_char_count 和 first_text/first_audio/turn_total timing；Task 05 已把 `boundary_respected` 从“边界 + 无问句”增强为会标记明显旧话题复活的 v0.1 heuristic；测试确认边界/睡前/连续追问、payload 不含儿童原文或回复全文、telemetry 失败不阻断响应；不把 Healthy Engagement 写成最终完成 |
| R7-01 完整设备 QA | in_progress |  | QA1 已补充 MANUAL_QA_V0_1.md 当前结果；后续采用双设备策略：高配 Android 手机先做功能主验证，Honor Pad 5 Android 9 / 4GB 做低配兼容和大屏验证 |
| R7-02 Family beta QA checklist/runbook | done |  | Task 04 新增 `docs/QA_FAMILY_BETA_CHECKLIST_V0_1.md`，覆盖 14 类家庭内测场景并要求每行记录 ID、Scenario、Steps、Expected、Actual、Status、Evidence、Notes；所有真机项初始为 NOT_RUN，证据不得包含儿童原文、完整回复、原始音频、原图或家长寄语原文 |
| R7-03 Mimo 真实 provider smoke 记录 | done |  | 临时 env 使用 `mimo-v2.5-pro` 已跑通；真实 key 不进仓库；当前测试阶段不能用未启用配置替代真实 smoke |
| R7-04 Task 05 family beta closeout package | done |  | 2026-05-24 完成 Task 05 closeout：`pytest` 417 passed、`ruff check .` passed、`./gradlew test` passed、`./gradlew assembleDebug` passed、`build_device_debug_apk.sh --base-url http://192.168.0.118:8000/` PASS，APK `android/app/build/outputs/apk/debug/app-debug.apk` size=16471142 sha256=`a666007b69be16efc1651b7246362d9b3a8755ee2c39856ffa0c02b45ec4c074`；`smoke_db_persistence.sh` PASS；`adb devices` 无连接设备，Redmi K60 / Honor Pad 5 仍为 NOT_RUN |
| R7-05 Task 06 post-device QA refinement | done |  | 2026-05-24 完成 Task 06 thin slice：Lane A 家长设置改为孩子画像/年龄/可选年级/称呼偏好/兴趣/话题边界，显性作息配置降级；Lane B 后端增加 same-topic low-engagement topic shift 和静态 curated seed packs；Lane C 家长日报增加 topic_overview、conversation_summary、avoid_followup 与 Android “今日聊了什么”；Lane D 儿童聊天页小白狐区域增加 phase chip 和轻背景，并新增 `CHILD_UI_POLISH_DESIGN_V0_1.md`。`bash scripts/test_backend.sh` 424 passed、`bash scripts/lint_backend.sh` passed、`bash scripts/android_gradle.sh test` BUILD SUCCESSFUL；Redmi K60 / Honor Pad 5 真机 QA 仍为 NOT_RUN |
| R7-06 Task 07 closeout and latency hardening | done |  | 2026-05-24 完成 Task 07：Lane A 家长设置保存不再校验隐藏 schedule，也不重写隐藏默认时间，仍保留后端 schedule 兼容；Lane B topic seed pack 升级为 reviewed/age-aware/expiring objects，并在儿童端 Ready/Resting idle 状态增加轻量换题 chips；Lane C 后端增加 non-stream/stream TTS latency timing 字段，Android remote audio logcat 增加 URL received/start/done/error timing；Lane D CS/game 家长日报 synthetic 摘要加强为地图、队友/朋友配合和输赢感受级别摘要，不展示 raw transcript。`bash scripts/test_backend.sh` 428 passed、`bash scripts/lint_backend.sh` passed、`bash scripts/android_gradle.sh test` BUILD SUCCESSFUL、`bash scripts/android_gradle.sh assembleDebug` BUILD SUCCESSFUL；Redmi K60 / Honor Pad 5 真机 QA 仍为 NOT_RUN |
| R7-07 Task 08 real-device QA round 2 package | done |  | 2026-05-24 按 Task 08 仅执行 Lane A：未发现新一轮 Redmi K60 / Honor Pad 5 视频、backend `request_id` 或 Android `XiaobaohuTtsTiming` logcat，`adb devices` 也无连接设备，因此跳过 Lane B/C/D 窄修复，不做猜测式代码修改。已构建真机 QA APK `android/app/build/outputs/apk/debug/app-debug.apk`，base URL `http://192.168.0.118:8000/`，size 16471142，sha256 `811a87abd220e1c102619e827beedb505f0771658b533871e44af02a134d0c86`；`pytest` 428 passed、`ruff check .` passed、`bash scripts/android_gradle.sh test` BUILD SUCCESSFUL、`bash scripts/android_gradle.sh assembleDebug` BUILD SUCCESSFUL。慢 turn 分类仍为 NOT_RUN，等待同一 turn 的 request_id + backend timing + logcat + 视频时间点。 |
| R7-08 Task 09 child account and model-driven personalization | done |  | 2026-05-25 完成 Task 09：Lane A 新增家长代创建/登录一个孩子账号、PBKDF2 password hash、auth session token hash、Android 持久登录态和退出；Lane B 儿童/家长可见文案从父亲迁移为家长，代码 `Parent*` 名称暂保留；Lane C child_chat output contract 增加 `conversation_control`，模型语义判断继续/换题/停止，program guardrails 覆盖安全/边界/fallback/metrics；Lane D opening v2 使用账号画像/兴趣/低敏历史生成短开场，provider failure 走确定性 fallback，Android Ready 不等待 opening/TTS；Lane E 后端基于兴趣、topic boundaries、curated seeds 和 control 生成 topic choices，Android 不再硬编码 fallback chips。Redmi K60 / Honor Pad 5 注册登录、opening v2、topic choices 和家长页默认路径仍为 NOT_RUN。 |
| R7-09 Task 10 Task09 closeout and QA package | done |  | 2026-05-25 完成 Task 10：Lane A 补 auth/session closeout，expired/revoked token 401，conversation/message、stream、opening、家长策略、家长日报和 attachment JSON/multipart 路径在 bearer token 存在时统一使用账号 child_id；Android auth state 单测覆盖保存会话刷新、失效清空和退出。Lane B 为 opening 增加 `app.opening_timing` 非敏感结构化日志和 TTS soft timeout，TTS 慢/失败仍返回文字且不触发系统 TTS fallback。Lane C 增强 `conversation_control_trace`、topic choice boundary filtering 和 trace runner synthetic cases。Lane D 构建 QA APK：base URL `http://192.168.0.118:8000/`，path `android/app/build/outputs/apk/debug/app-debug.apk`，size 16471142，sha256 `28fdd63f6cd6e9ef71c27d0dde2c8ce274d7980ea06d0a9e50e2d2248fa0ddaa`；`bash scripts/test_backend.sh` 453 passed、`bash scripts/lint_backend.sh` passed、`bash scripts/android_gradle.sh test` BUILD SUCCESSFUL、`bash scripts/android_gradle.sh assembleDebug` BUILD SUCCESSFUL、`run_model_trace_scenarios.py` PASS 26 scenarios / 26 traces。Redmi K60 / Honor Pad 5 真机 QA 仍为 NOT_RUN。 |

### 产品决策、语音和小白狐下一阶段

| Task | 状态 | PR | 验收 |
|---|---|---|---|
| R8-01 Product Decision Sync 机制 | done |  | 家长确认的新产品想法先写入 PRODUCT_DECISIONS；子会话实现前检查 confirmed decision |
| R8-02 语音交互设计文档 | done |  | 明确儿童默认 voice-first 自动发送、调试用 confirm-before-send、后端 MiMo ASR、默认自动 TTS、VoiceProfile、opening greeting、可替换抽象、原始音频策略、权限、错误文案、安全边界和 QA 指标 |
| R8-03 下一阶段计划文档 | done |  | 拆分完整设备 QA、语音输入、TTS、小白狐视觉资源、小白狐动画状态机、真实平板家庭内测准备 |
| V1-01 Android 语音上传 voice-first v1 | done |  | Android 录音上传后端 ASR 后儿童默认自动发送 transcript；DevSettings 确认模式保留；不直接调用 MiMo；future hands-free conversational mode 不进 v1；待真机权限和录音 QA |
| V1-02 Android TTS 朗读 v1 | in_progress |  | Android 播放 `reply.audio_url`；远程音频失败或缺失时只保留文字和错误提示，不再 fallback 系统 TTS，避免小白狐音色与系统音色混播；待 Redmi K60 听感和网络播放 QA |
| V1-03 Android 语音抽象和 VoiceProfile | in_progress |  | TtsController / AndroidTtsController / VoiceProfile 已完成；SpeechInputController / backend ASR upload 抽象已接入；VoiceProfile 使用 zh-CN、稍慢语速、偏高不过度音高和系统中文 fallback |
| V1-04 语音 QA 指标记录 | todo |  | 记录识别准确率、延迟、中文效果、儿童声音识别、TTS 自然度和孩子接受度 |
| V1-05 TTS-D1 可观测性与故障修复 | done |  | 新增 TtsUiState / VoiceDiagnostics 诊断，记录 engine、locale、voice、setLanguage、setVoice、speak 返回值和 failure reason；speaking 状态前移到请求接受阶段；新增 TTS 设置/语音数据入口 |
| V1-06 后端小白狐 TTS endpoint | done |  | 新增 `/api/v1/tts/xiaobaohu`、TTS schema、mock/MiMo VoiceClone provider 抽象、TtsDataPolicyGuard、本地 wav 缓存和 `/media/tts/...wav` 受控服务；默认不外发；真实 smoke 已确认 `/chat/completions` + `choices[0].message.audio.data` 可生成 RIFF/WAV |
| V1-07 Android remote audioUrl 播放 | done |  | Android 收到 `reply.audio_url` 时播放远程音频；失败时只保留文字和错误提示，不再 fallback 系统 TTS；朗读时小白狐切 speaking；Android conversation read timeout 已从 12s 调整为 45s，避免 MiMo TTS 同步生成接近 10s 时误报断网 |
| F1-01 小白狐视觉资源 v1 | in_progress |  | v1 候选资源已扩展：neutral_idle、listening、speaking、jumping_happy、thinking、calm、sleepy、safety_concern、privacy_boundary、homework_focus、network_error；目标是 3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感 |
| F1-02 小白狐静态资源接入 | in_progress |  | 已新增 drawable-nodpi 候选资源、FoxAgentAssetMapper 和 DevSettings.FOX_ASSET_MODE；静态资源已压缩为 WebP 并保留 Canvas fallback；6 张新增状态图已接入资源目录和映射，后续需设备侧验证图片显示和低配降级 |
| F1-03 小白狐动画状态机 v1 | in_progress |  | 已接入 manifest-driven animation_v1、MascotController、FrameSequencePlayer 和三层 fallback；覆盖 11 个状态、12 FPS、24 帧 WebP 序列；Android runtime assets 约 4.9MB，静态 fallback 约 1.5MB，clean assemble debug APK 约 15MB；待真机验证画质、流畅度和低配降级 |
| O1-01 Open Conversation Mode 小步实现 | done |  | 普通兴趣和日常话题进入 `conversation.open`；ChildAgentRuntime 接收进程内短期 history；普通聊天 quick actions 随上下文轻量变化；安全、隐私、学习、睡前边界保留 |
| DB1-A PostgreSQL 基础设施 | done |  | 新增 SQLAlchemy sync、psycopg、Alembic、PostgreSQL 16 local compose、初始 8 张表、migration/reset 脚本和基础测试；B2-B5 业务 thin slice 已接入 |
| DB1-B ParentPolicy 持久化 | done |  | ParentPolicyService 已支持 PostgreSQL repository 优先读写；数据库不可用时 dev fallback 到内存；`parent_message_raw` 和 `parent_message_updated_at` 已有迁移 |
| DB1-C Conversation message 持久化 | done |  | thin slice done：普通 `/api/v1/conversation/message` 和 `/api/v1/conversation/stream` 成功 turn 均已 best-effort 保存 session、child message、agent message、routing decision、audio_url/stream audio summary、emotion、agent_motion；持久化失败不阻断回复；不保存 delta 列表、debug、prompt、parent_message_raw、原始音频或照片 |
| DB1-D MemoryService 持久化 | done |  | thin slice done：MemoryService 优先使用 PostgreSQL `memory_items`，数据库不可用时回退进程内 repository；只保存结构化 summary、tags、evidence summary、visibility/safety flags，不保存 raw media、full transcript、prompt 或 debug internals |
| DB1-E ParentReport 持久化 | done |  | thin slice done：ParentReportService 优先从 PostgreSQL `parent_reports` 读取已生成日报；model-first v2 新增 `generation_status` / `generated_by` / `generation_error_code` / `material_fingerprint`；缺失或当天有更新会话素材时刷新模型日报；模型失败不保存为正式报告；不保存 evidence、quote_summary、raw transcript、prompt、debug 或 provider raw response |
| DEV-TRACE-1 模型调用 trace | done |  | 新增 `model_debug_traces` 本地 trace 表；当前测试阶段作为默认系统组件随后端启用，不再需要显式 trace 开关；`ModelRegistry.generate()` 统一记录完整 request messages/input/context/metadata 和 response text/structured output/metadata、fallback/policy/error/latency；记录失败不阻断模型调用，过滤 API key/Authorization/raw media/base64；不改 Android 或现有业务表 |
| DEV-TRACE-2 trace scenario review | done |  | `scripts/run_model_trace_scenarios.py` 强制 mock provider，清空并回放 21 个 synthetic opening/child_chat/image-context/parent_report 场景，覆盖 Task 05 要求的 age_5_6、age_9_10、连续追问、换题、睡前、纠错、普通图片、低置信图片、家长日报 bridge 和 self-harm fallback；确认写入默认 `model_debug_traces`，报告明确不代表真实 MiMo、Android 真机或真实儿童 QA |
| DEV-TRACE-3 real provider trace review | done |  | `run_model_trace_scenarios.py --provider mimo` 已支持显式 opt-in real MiMo synthetic 文本场景并记录 request_id；临时 env overlay 不写 `.env`，缺 key 时输出 `REAL_PROVIDER_BLOCKED`；2026-05-24 Task 05 复跑到 `REAL_PROVIDER_SMOKE: REVIEW_NEEDED`，19 scenarios / 14 traces，child_chat 均为 `mimo/mimo-v2.5-pro` 且 self-harm 保持确定性可信成人兜底；一个 parent_report 场景超时 fallback 到 mock，creative-share synthetic checker 标记 P2，需人工 review；报告不代表真机 QA |
| S-Stream-0 流式架构设计 | done |  | 新增 `STREAMING_INTERACTION_DESIGN_V0_1.md`；确认 NDJSON、事件结构、pseudo streaming、fallback 和 QA 指标 |
| S-Stream-1 后端 stream endpoint | done |  | 新增 `/api/v1/conversation/stream` NDJSON skeleton；保留旧接口；复用 ConversationService/Runtime 安全链路；按句子 pseudo streaming 和可恢复 TTS segment error |
| S-Stream-2 Android stream client | done |  | 新增 NDJSON stream client、progressive agent bubble、audio segment queue、stop/mute 处理；stream 失败 fallback 旧接口；待 Redmi K60/Honor Pad 5 手动 QA |
| S-Stream-3 interleaved TTS quick win | done |  | 后端 stream 现在按 segment 输出 text_delta/sentence_ready 后立即 tts_started/audio_ready；text_final 在所有 segment 处理后输出；新增 first_tts_start_ms、text_segment_count、tts_error_count timing |
| EXP-E1-01 Android unified interaction state | done |  | 新增 `ChildTurnUiPhase` / `ChildInteractionPresentation` reducer，集中派生 Ready、Listening、Recognizing、Sending、Thinking、SpeakingPending、Speaking、ImageProcessing、NeedsRetry、PermissionNeeded、Resting、ServiceError 的儿童可见状态；InputBar 主按钮文案、按钮可用性、图片按钮可见性、TTS “停一下”、小白狐状态短语和 agent 状态已接入；Parallel Lane A 补齐 voice-first 下 TTS pending/speaking 的“静音/打开朗读”和新动作前 stop TTS；未改后端协议、图片具体反馈、家长日报或 Healthy Engagement 指标；Redmi K60 / Honor Pad 5 真机 QA 仍待验 |
| EXP-E2-01 Backend age-banded replies and question throttle | done |  | 新增 `AgeBandReplyPolicy`，从 ParentPolicy communication_preferences 的 `age_band`、`child_age` 或 `age` 派生 age_5_6 / age_7_8 / age_9_10 / unknown，默认 age_7_8；global/output/open conversation prompt 不再写死 8 岁或 150-450 字；ChildAgentRuntime 按预算裁剪普通回复，并在连续问句、换题/不聊/睡觉、孩子纠错时不新增追问钩子；未改 DB schema、后端 API 协议、Android 或家长日报 |
| EXP-E2-02 Topic shift curated seeds | done |  | Task 06 thin slice：`TurnGuidanceBuilder` 新增 same_topic_turn_count、child_engagement_signal、topic_shift_recommended、topic_shift_reason 和 suggested_topic_seeds；静态 seed pack 位于 `backend/app/data/topic_seed_packs_v0_1.json`；ChildAgentRuntime 会修复低能量同题下继续深挖旧话题的模型回复；不抓实时热点、不引入上瘾式机制，真机自然度 QA 待验 |
| UI-Landscape-1 横屏双栏布局 | done |  | Android 主界面已改为 sensorLandscape 横屏：左侧约 41% 小白狐，右侧约 59% 消息和输入；Android test/assemble/lint 通过，待真机视觉 QA |
| Fox-Coverage-1 动态小白狐覆盖矩阵 | done |  | 历史 `FOX_AGENT_STATE_COVERAGE_V0_1.md` 记录 manifest/资源基线；Task 04 已在 `FOX_AGENT_VISUAL_DESIGN_V0_1.md` 更新 phase/scene 覆盖矩阵，覆盖 Ready、Listening、Recognizing、Thinking、SpeakingPending、Speaking、ImageProcessing、NeedsRetry、PermissionNeeded、Resting、ServiceError、OpeningGreeting、PrivacyBoundary、SafetyConcern、HomeworkFocus、NetworkError，并新增 `XiaobaohuStateCoverageTest`；Resting 业务触发和全量真机动画切换仍待 QA |
| ASR-Research-0 MiMo ASR 调研 | done |  | 新增 `ASR_INPUT_RESEARCH_V0_1.md` 和 `MIMO_ASR_INTEGRATION_DESIGN_V0_1.md`；确认 v1 目标 provider、目标模型、非流式 audio input、格式、30s 上限和数据留存缺口 |
| ASR-Skeleton-0 后端 mock skeleton | done |  | 新增 ASR schema/service/provider/policy guard；真实 ASR 测试需显式选择目标 provider，真实儿童音频外发仍被 policy guard 控制 |
| ASR-Provider-1 MiMo ASR provider | done |  | `/api/v1/asr/transcribe` 已挂载；MiMo `/chat/completions` provider 已实现；默认 policy-blocked；新增 fake-audio smoke 脚本，不使用真实儿童录音 |
| ASR-Provider-2 Local SenseVoice provider | done |  | 新增 `local_sensevoice` provider、sherpa-onnx optional dependency、模型路径配置、本地 policy allow 和本地异常 fallback；模型文件不进 git；2026-05-23 本机非儿童 synthetic WAV smoke PASS：provider=local_sensevoice、model=model.int8.onnx、status=ok |
| ASR-Android-1 录音上传 voice-first UI | done |  | Android 已接入 RECORD_AUDIO 点击触发、短 WAV 录音、上传后端 ASR、儿童默认自动发送、重说/取消；DevSettings 确认面板保留；不常开麦克风、不自动连续监听 |
| Opening-1 小白狐启动开场白 | done |  | 后端新增 `/api/v1/conversation/opening`；支持 child_nickname / child_display_name 称呼优先级、时段和家长寄语约束、TTS 失败降级；Android 每 session 请求一次，孩子先说话时不插入 |
| ParentProfile-1 家长设置孩子称呼 | done |  | Android 家长设置页已接入 child_nickname / child_display_name 读取、编辑和保存；opening 使用小名优先、显示名 fallback；待 Redmi K60 / Honor Pad 5 真机 QA |
| ASR-Smoke-1 provider smoke QA | done |  | MiMo fallback smoke 已确认 `provider=mimo`、`model=mimo-v2.5`；新增 `scripts/check_local_sensevoice_asr_status.py`，本地 primary smoke 已确认 `provider=local_sensevoice`、`model=model.int8.onnx`；两类 smoke 均不输出 transcript/base64/API key，真实儿童语音准确率和 Android QA 仍待验 |
| Ops-Foundation-1 运行基础缺口分析 | done |  | 新增 `OPS_FOUNDATION_GAP_ANALYSIS_V0_1.md`；首批聚焦 request_id、结构化日志、provider timing、health 扩展和脚本统一 |
| Ops-Foundation-2 P0 后端可观测性骨架 | done |  | 新增 request_id middleware、结构化 JSON 日志、request/model/TTS timing、`/api/v1/health/detail` 和日志脱敏测试；不接第三方 APM |
| QA-Gate-1 测试品目标一致性门槛 | done |  | 固化 2026-05-21 复盘：给家长 APK/后端测试品前必须核对 APK base URL、运行后端 env、provider/mock 状态和目标接口 smoke；mock ASR 不能声明为真实 MiMo ASR 测试 |
| QA-Gate-2 ASR key/model 对齐 | done |  | 固化 2026-05-21 复盘：MiMo ASR 默认复用当前 MiMo key，effective key 顺序为 ASR key -> shared MiMo key -> TTS key；ASR 模型必须是 `mimo-v2.5`，不是文本对话 `mimo-v2.5-pro` |
| QA-Smoke-1 家庭内测前 smoke 打包 | done |  | 新增 backend local、voice stack、DB persistence 和 MiMo ASR opt-in smoke 脚本；新增 release smoke 记录和 Redmi K60 / Honor Pad 5 QA checklist；旧非真机 APK 已废弃；当前只交付 Mac LAN base URL 真机 APK |
| QA-Smoke-2 本地 DB/ASR/Vision smoke 收口 | done |  | `setup_local_postgres.sh` 在本机无 Docker CLI 时自动使用 Homebrew postgresql@16，并完成 migration + DB persistence smoke PASS；`check_asr_real_status.sh` 已改为读取 `.env` 后施加临时 MiMo ASR overlay，自动生成 synthetic fake wav，真实 smoke PASS：provider=mimo、model=mimo-v2.5、status=needs_retry；`smoke_vision_model_opt_in.sh` 已改为临时 MiMo image overlay 并自动生成 fake/test PNG，真实 smoke PASS：provider=mimo、model=mimo-v2.5；latest observed recognized_type=privacy_sensitive/text_length=176，分类值随 fake image 可变，smoke 只验证真实 provider 路由与脱敏输出 |

---

## 3. 当天记录

### 日期：2026-05-24

```text
今日目标：执行 Task 06 post-device QA product refinement，按单智能体 A -> B -> C -> D 完成家长设置、话题切换、家长日报和儿童 UI polish thin slice。
完成任务：家长设置页显性重点改为孩子画像：小名/显示名、年龄、可选年级、称呼偏好、兴趣和近期不想被追问的话题；作息时间仍兼容后端但不再作为 v0.1 家庭内测主配置。后端 turn guidance 增加 same-topic low-engagement 检测和静态 curated seed pack，ChildAgentRuntime 对继续深挖旧话题的低能量回复做换题修复。家长日报 domain/service/Android DTO/UI 增加 topic_overview、conversation_summary、avoid_followup 和“今日聊了什么”。儿童聊天页小白狐区域增加 phase-derived 短状态 chip 和轻背景；新增 CHILD_UI_POLISH_DESIGN_V0_1.md。更新 Product Decisions、README、Freedom/Healthy/QA/Next Phase/Progress docs。
阻塞问题：未连接 Redmi K60 / Honor Pad 5，家长设置可读性、话题切换自然度、家长日报层级、小白狐 phase chip 横屏布局和低配表现仍需真机 QA。
Codex 偏差：无；本轮未做 prompt 年龄体系大重写、实时热点抓取、CameraX、后端协议变更、排行榜/积分/签到/宠物机制，也未记录儿童原文、原始音频、原图或家长寄语原文。
需要补充到 AGENTS.md 的规则：暂无。
明日第一任务：在 Redmi K60 / Honor Pad 5 按 QA_FAMILY_BETA_CHECKLIST_V0_1.md 复验 Task 06 设置页、话题切换、家长日报和儿童 UI polish，并记录非敏感证据。
```

### 日期：2026-05-21

```text
今日目标：解决家长反馈的两个 P0 体验问题：儿童端语音默认自动发送并隐藏文字编辑负担；App 打开时小白狐主动生成短 opening greeting。
完成任务：Android 新增 `CHILD_VOICE_FIRST_MODE=true`、`VOICE_CONFIRM_BEFORE_SEND=false`、`SHOW_TEXT_INPUT_FOR_CHILD=false` 默认配置；InputBar 儿童默认只显示语音大按钮和重说/取消/停止/静音等辅助按钮，隐藏文字输入框、发送按钮和待确认文本编辑面板。ChatViewModel 在 ASR ok 且 transcript 非空时自动发送 conversation stream；needs_retry、permission denied、policy blocked 和 ASR failure 不自动发送，调试确认模式仍可打开。后端新增 `POST /api/v1/conversation/opening`、ParentPolicy `child_nickname` / `child_display_name` schema 和迁移；opening 按小名、display name、无称呼优先级生成短开场白，支持 TTS audioUrl，TTS 失败仍返回文本，同 session 去重。Android 儿童聊天页首次可见时请求 opening，作为第一条小白狐消息展示并自动播放 audioUrl；孩子先说话时丢弃迟到 opening。
阻塞问题：无代码阻塞；没有连接 Android 真机，录音权限、真实麦克风采集、Redmi K60 首音频延迟和 Honor Pad 5 性能仍需手动 QA；真实 MiMo ASR smoke 需家长确认 env flags 和使用非儿童 smoke 音频。
Codex 偏差：无；本轮未做常开麦克风、未保存原始音频、未做真实 LLM streaming、未做 DB 全量迁移、未破坏横屏布局或 animation_v1。
需要补充到 AGENTS.md 的规则：暂无。
明日第一任务：在 Redmi K60 上手动 QA opening greeting、语音权限、录音上传、ASR 自动发送、重说/取消、DevSettings 确认模式、stream 首音频延迟、分段 audio queue、停止/静音和 ASR policy blocked/needs_retry；Honor Pad 5 复验横屏、animation_v1、opening 和录音性能。
```

### 日期：2026-05-22

```text
今日目标：完成家庭内测前 smoke + QA 打包轮，不继续扩展 DB 新功能。
完成任务：新增 `scripts/smoke_backend_local.sh`、`scripts/smoke_voice_stack.sh`、`scripts/smoke_db_persistence.sh` 和 `scripts/smoke_mimo_asr_opt_in.sh`；新增 smoke 契约测试，确保脚本可执行、mock ASR 不把 data URI/transcript 写日志、stream include_tts 持久化只存 audio summary 不存完整 event list。新增 `docs/RELEASE_SMOKE_V0_1.md` 和 `docs/QA_DEVICE_CHECKLIST_V0_1.md`，记录 backend/voice smoke、DB smoke skip 原因、APK path/size/sha256、Redmi K60 与 Honor Pad 5 手动 QA 清单。Android debug APK 构建成功：`android/app/build/outputs/apk/debug/app-debug.apk`，size=16047291 bytes / 15M，sha256=`7468ac8c605bb92f5244e38a39d022b1bb388d79d142bbd3444eb95b620f3e10`。
阻塞问题：本条记录描述家庭内测前打包轮的初始状态：当时本机 PostgreSQL 未启动，`smoke_db_persistence.sh` 按设计输出 SKIP，不计为通过；当时 MiMo ASR real smoke 尚未完成；真机 base URL APK 未构建，Redmi K60 / Honor Pad 5 未安装验证。后续 QA-Smoke-2 已补齐 PostgreSQL 自动 setup 和 ASR real smoke。
Codex 偏差：无；本轮未改 Android runtime、Android assets、ASR/TTS provider 主逻辑、stream 协议、DB schema/migration、true LLM streaming 或 CameraX/real OCR。
需要补充到 AGENTS.md 的规则：暂无。
明日第一任务：启动本地 PostgreSQL 后复跑 DB persistence smoke；用 Mac LAN IP 重新构建真机 APK，按 `QA_DEVICE_CHECKLIST_V0_1.md` 执行 Redmi K60 / Honor Pad 5 手动 QA。
```

```text
今日目标：不要等用户晚上手测，补齐本地 PostgreSQL 自动 setup、ASR real status 核对、MiMo vision/OCR 最小真实 smoke。
完成任务：新增本地 PostgreSQL setup 脚本，优先 Docker Compose，Docker 不可用时在 macOS 尝试 Homebrew postgresql@16，并在成功后自动运行 migration 与 DB persistence smoke；新增 ASR 状态检查脚本，真实 smoke 目标会用临时 overlay 推进到 MiMo ready / pass / fail / policy blocked；新增 OpenAI-compatible multimodal image payload 支持、AttachmentService image_data_uri 最小 vision path 和 vision opt-in smoke 脚本。当前测试阶段 vision smoke 使用临时 env overlay 推进真实链路；不接 CameraX，不保存 raw image/base64。
阻塞问题：ASR real smoke 已不再被未启用配置阻塞，脚本会使用临时 env overlay 和 synthetic fake wav；本轮真实执行结果 PASS，provider=mimo、model=mimo-v2.5。Vision real smoke 也已不再被缺 image policy 或缺图片路径阻塞，脚本会生成 fake/test PNG 并使用临时 image overlay；已修正全局文本模型覆盖 vision profile 的问题，真实执行结果 PASS，provider=mimo、model=mimo-v2.5。Redmi K60 / Honor Pad 5 仍未真机 QA。
Codex 偏差：无；本轮未修改 Android runtime、Android assets、stream 协议、TTS provider 主逻辑、DB schema/migration、true LLM streaming 或 CameraX。
需要补充到 AGENTS.md 的规则：暂无。
明日第一任务：保持 ASR/Vision real smoke 脚本使用临时 overlay，不把 policy flags 固化进 `.env`；随后进入 Redmi K60 / Honor Pad 5 真机 QA。
```

### 日期：2026-05-22

```text
今日目标：补齐 Parent Profile + Opening Greeting 闭环，让家长设置页可以结构化配置孩子小名和显示名。
完成任务：Android ParentPolicy DTO、ParentPolicyViewModel 和 ParentSettingsScreen 已支持 child_nickname / child_display_name；家长设置页新增“孩子称呼”轻量区块，小名优先用于小白狐 opening greeting，没有小名时使用显示名，都没有时不强行称呼。补充 Android DTO/ViewModel 测试和后端 parent policy API 断言。
阻塞问题：无代码阻塞；未连接 Redmi K60 / Honor Pad 5 真机，家长设置保存后的真实 opening greeting 称呼效果仍待设备 QA。
Codex 偏差：无；本轮未修改 ASR provider、TTS provider、stream service、ChatViewModel voice-first 主链路、animation_v1 或 DB conversation/message 持久化。
```

### 日期：2026-05-19

```text
今日目标：完成 S13 Android 拍题与家长页验收，推进 S14 本机/API 联调和 S20a 文档同步，进入 AgentRuntime、模型外发安全闸门、自动记忆闭环、安全场景细分、家长入口保护和家庭内测前加固阶段。
完成任务：Android mock 拍题流程已接入 attachment API 和 conversation API；家长设置页可读取/保存 goals、沟通偏好和作息时间；家长日报页可读取后端日报摘要；S14 本机 health、LAN health、E2E API 合约检查通过；新增共享上下文、环境 doctor 和 Android Gradle 包装脚本；Android test、assembleDebug、lintDebug 通过；S20a 修正文档中过期的 C0/未初始化描述，并补齐多会话协同规则和后续子会话提示词；S16 已完成模型外发安全闸门；S19 已完成 Android 家长入口长按 + dev PIN 轻量保护；S15 已完成 ChildAgentRuntime 主回复链路，模型失败/空回复/高风险输出回退 SceneRouteDecision.reply_text；S18 已完成安全场景细分，HIGH/CRITICAL 进入 safety.guardian，WATCH 进入 safety.gentle_checkin，LOW privacy 进入 privacy.boundary，低能量表达不进 guardian；S17 已完成规则型自动记忆闭环，conversation 会在 runtime 前检索非 safety 记忆，并在路由后写入结构化摘要记忆，家长日报可读取当天自动记忆素材；S24 已完成真实模型输出质量加固，回复更适合语音播报并拦截秘密关系/唯一朋友/隔离可信成人风险话术；S25 已完成 Android 小白狐轻量状态映射和语音占位 UI；本轮补充小白狐 v1 候选资源、双设备测试策略、预渲染 PNG/WebP + 轻量 Compose 动画原则、FoxAgentAssetMapper 和低配 fallback 规则；V2 已完成 Android 本地 TTS v1 代码接入，支持默认自动朗读、停止/静音、VoiceProfile 和小白狐 speaking 状态联动；Redmi K60 截图显示上一版 TTS 为 SKIPPED_UNAVAILABLE，TTS-D1 已补 TTS service 查询、初始化竞态修复、系统朗读设置入口和诊断；6 张新增小白狐状态图已进入资源接入流程；Open Conversation Mode 已完成小步后端实现，普通话题进入 conversation.open 并传入短期 history；当前 8000 后端已改为加载本地忽略 `.env` 的 Mimo 配置，Mimo 超时调为 30000ms，普通恐龙话题 smoke 已返回真实模型回复。
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
完成任务：补齐 Q1 场景测试，覆盖放学后、学习求助、直接要答案、不想说话、高风险安全、睡前复盘、家长目标影响回复、模型 fallback；更新 test/lint/dev/demo 后端脚本；更新 backend README；本地 pytest、ruff、demo 通过；Android 壳项目已创建并通过 assembleDebug / test；Android 已接入 conversation API 并渲染 reply、ui_actions、session_state。
阻塞问题：无。
Codex 偏差：未新增 GitHub Actions，因为当前任务约束要求没有远端 GitHub 时优先保证本地脚本和 README。
需要补充到 AGENTS.md 的规则：暂无。
明日第一任务：启动 S13 Android 拍题与家长页会话。
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
