# Product Decisions v0.1

用途：记录父亲 / 产品负责人已经确认的产品决策、边界原则和阶段调整。子会话实现前必须先检查本文件，避免新想法只留在聊天记录里。

状态值：

```text
proposed：已提出但尚未确认，不能作为实现依据。
confirmed：父亲 / 产品负责人已确认，代码和文档不得冲突。
revised：已被父亲 / 产品负责人修订，后续以修订后的内容为准。
deprecated：已废弃，不再作为实现依据。
```

---

## 1. Product Decision Sync

```text
1. 父亲 / 产品负责人确认的新想法、方案调整、边界原则，必须写入本文件。
2. 涉及语音、小白狐形象、儿童安全、模型外发、记忆、父亲治理的决策，不允许只存在对话中。
3. 子会话开始前必须检查本文件是否有影响本任务的新决策。
4. 子会话完成后如果发现新的产品事实或限制，必须建议主会话更新本文件或对应设计文档。
5. 代码实现不得与 confirmed decision 冲突；如冲突，先报告，不要擅自改产品方向。
6. 每次父亲确认的新产品想法，必须先写入本文件，再进入子会话实现。
```

---

## 2. Confirmed Decisions

| ID | 状态 | 决策 | 影响范围 |
|---|---|---|---|
| PD-001 | confirmed | 下一阶段优先解决语音交互和小白狐形象体验。 | Android、后端 reply metadata、QA、视觉设计 |
| PD-002 | revised | 语音输入 ASR v1 目标修订为后端接 MiMo audio input / ASR；Android 不直接调用 MiMo，只负责点击录音、上传后端和展示儿童端语音状态；儿童默认自动发送 transcript，确认面板仅保留为 DevSettings / 父亲调试模式。TTS 正式音色路径已由 PD-027 修订为后端 MiMo VoiceClone。 | Android 权限、语音设计、后端 API 边界、ASR、TTS |
| PD-003 | revised | 儿童端默认改为 voice-first 自动发送：ASR 成功且 transcript 非空时自动进入 conversation；confirm-before-send 仅保留为 DevSettings / 父亲调试模式。 | Android UX、儿童安全、QA |
| PD-004 | confirmed | 小白狐形象应温和、好奇、慢热友好，避免强刺激、排行榜、连击奖励或上瘾式动画。 | 视觉 brief、动画状态、Android UI |
| PD-005 | confirmed | 后端继续通过 `reply.voice_enabled`、`reply.audio_url`、`reply.emotion`、`reply.agent_motion` 向 Android 暴露表现层信号。 | 后端 API、Android DTO、TTS/动画 |
| PD-006 | confirmed | 小白狐表现层不得制造“唯一朋友”“只有我懂你”等依赖感。 | Prompt、安全检查、视觉与动效文案 |
| PD-007 | confirmed | 所有新体验仍必须遵守：不直接给作业最终答案，不要求保密，不鼓励隐瞒父母，不保存原始音频/照片到长期记忆。 | 全端、安全、记忆、QA |
| PD-008 | confirmed | 每次父亲确认的新产品想法，必须先写入 `docs/PRODUCT_DECISIONS_V0_1.md`，再进入子会话实现。 | 协作流程、AGENTS、README |
| PD-009 | confirmed | 正式名称为“小白狐”；UI、产品、设计和测试说明优先统一。代码 class 名 `FoxAgent` 暂可保留，后续如要改代码命名单独 refactor。 | Android UI、README、设计文档、QA 文案、后续代码重命名计划 |
| PD-010 | revised | 语音输入 v1 儿童默认流程是点击语音 -> 录音 -> 后端 ASR -> 自动发送 transcript -> conversation stream；不做常开麦克风、不做自动连续监听，确认面板只作为开发/父亲模式。 | Android 语音输入、后端 ASR、QA、后端 API 边界 |
| PD-011 | revised | TTS 默认自动朗读小白狐回复；必须有停止/静音、DevSettings 或父亲设置开关。系统 `VoiceProfile` 保留为 fallback，正式品牌音色由 PD-027 的 MiMo VoiceClone 承担。 | Android TTS、父亲治理、DevSettings、后端 TTS、QA |
| PD-012 | confirmed | `VoiceProfile` v1 包含 `preferredVoiceName`、`zh-CN`、稍慢 `speechRate`、偏高但不过度的 `pitch`、fallback 系统默认中文 voice。 | Android TTS 配置、测试 |
| PD-013 | confirmed | 小白狐视觉目标是 3D / soft 3D / 毛绒感 / 立体绘本感；Compose Canvas / 2D 只是 fallback，不阻塞语音开发。 | 视觉 brief、Android 资源、下一阶段计划 |
| PD-014 | confirmed | 允许 Android `SpeechRecognizer` / `TextToSpeech`，但必须通过可替换抽象：`VoiceEngine` / `SpeechInputController` / `TtsController`。 | Android 架构、测试、后续替换能力 |
| PD-015 | confirmed | 语音 QA 必须记录识别准确率、延迟、中文效果、儿童声音识别、TTS 自然度和孩子接受度。 | QA 计划、家庭内测准备 |
| PD-016 | confirmed | 小白狐应是 3D 卡通、柔和立体、有毛绒感、儿童动画质感的卡通形象，整体活泼开朗，支持说话、倾听、蹦蹦跳跳等状态。 | 视觉 brief、Android 资源、动效、QA |
| PD-017 | confirmed | 小白狐音色方向是小孩子般干净、清脆、中性、活泼可爱，但不能过度尖锐或幼稚。 | Android TTS、VoiceProfile、QA |
| PD-018 | confirmed | 采用双设备测试策略：高配 Android 手机作为功能主验证设备，Honor Pad 5 Android 9 / 4GB 作为低配兼容性和大屏目标设备。 | QA、Android 性能、语音、TTS、小白狐资源 |
| PD-019 | confirmed | 小白狐 Android 第一版运行方式优先预渲染 3D PNG/WebP 状态图 + 轻量 Compose 动画；不把实时 3D 引擎或重型动画依赖作为第一版必需能力。 | Android presentation、资源、性能降级 |
| PD-020 | revised | 小白狐 v1 初始候选形象资产包含 neutral_idle、listening、speaking、jumping_happy、thinking 五个基础状态；现已由 PD-023 扩展为 11 个状态。 | Android drawable、视觉设计、QA |
| PD-021 | revised | Redmi K60 / Android 14 真机反馈显示系统 TTS 链路不可观测且无声；已先修诊断和 fallback，正式音色路径由 PD-027 改为后端 MiMo VoiceClone。 | Android TTS、VoiceProfile、QA、下一阶段计划 |
| PD-022 | confirmed | Android 系统 TTS 只是 v1 验证方案，不作为最终儿童产品音色承诺；后续需评估小白狐专属或替代音色方案。 | Android TTS、数据策略、供应商评估、QA |
| PD-023 | confirmed | 新增 6 张小白狐状态图 calm、sleepy、safety_concern、privacy_boundary、homework_focus、network_error 已提交，需接入 Android 资源映射并保留 Canvas fallback。 | Android drawable、FoxAgentAssetMapper、视觉 QA |
| PD-024 | revised | 普通聊天进入 Open Conversation Mode / Freer Context Mode：普通兴趣和日常话题更自由，模型接收最近多轮短期上下文，SceneOrchestrator 保留安全、隐私、学习和睡前约束。 | 后端 conversation、Prompt/Runtime、QA |
| PD-025 | confirmed | Redmi K60 截图中的 TTS 失败先按代码链路不可用处理，而不是按“系统音色不好”处理。 | Android TTS、Manifest、InputBar、QA |
| PD-026 | confirmed | 当前阶段不读取或保存完整逐字聊天数据库；普通聊天只使用进程内短期 history 给模型补上下文。 | ConversationHistoryService、Memory、Parent report |
| PD-027 | confirmed | 小白狐正式品牌音色方案改为后端 MiMo VoiceClone：VoiceDesign 只用于音色筛选且已完成，VoiceClone 用已下载 wav 样本生成 App 语音，普通 MiMo TTS 只做测试/兜底。 | 后端 TTS、Android remote audio、数据策略、QA |
| PD-028 | confirmed | 产品底座修订为 freedom-first：默认自由对话，时间、父母寄语、记忆和图片作为上下文或能力，安全/隐私/学习/睡前强边界作为护栏。 | 后端路由、Prompt、Android 入口、QA |
| PD-029 | confirmed | 拍照从“拍作业”升级为“拍给小白狐看”的通用图片分享能力；作业题只是图片能力的一个分支。 | Attachment API、Android mock 图片、Prompt、QA |
| PD-030 | confirmed | 父母寄语需要支持自由文本，作为 Prompt 重要上下文；不能机械复述给孩子，不能覆盖儿童安全底线。 | ParentPolicy、PromptManager、Android 父亲设置、QA |
| PD-034 | revised | ASR v1 方案确定接 MiMo audio input / ASR：Android 不直接调用 MiMo，不常开麦克风；儿童默认自动发送非空 transcript，confirm-before-send 只作为 DevSettings / 父亲调试模式。真实儿童音频外发必须由父亲授权和 ASR data policy flags 控制，开发阶段只用 fake/smoke audio。 | Android voice、backend ASR、MiMo provider、ASR policy guard、QA |
| PD-035 | confirmed | MiMo ASR 复用当前 MiMo key：优先 `CHILD_AI_MIMO_ASR_API_KEY`，为空时使用 `CHILD_AI_MIMO_API_KEY`，再 fallback 到 `CHILD_AI_MIMO_TTS_API_KEY`；ASR 默认模型是 `mimo-v2.5`，不是文本对话的 `mimo-v2.5-pro`。 | backend config、ASR provider、QA artifact gate、docs、smoke script |
| PD-036 | confirmed | 儿童主界面默认隐藏文字输入框、发送按钮和可编辑 ASR 文本确认面板；语音是主输入，保留重说、取消、停止朗读、静音等大按钮。 | Android child UI、InputBar、DevSettings、QA |
| PD-037 | confirmed | App 打开儿童聊天页后，小白狐应主动请求 opening greeting，基于时间、父母寄语和孩子称呼生成一句短开场白；称呼优先 child_nickname，其次 child_display_name，都没有则不强行称呼。 | backend opening API、Android ChatViewModel、ParentPolicy、TTS、QA |
| PD-038 | confirmed | 普通文字对话调用 MiMo `mimo-v2.5-pro`；带图片的 conversation attachment / vision / OCR 链路调用 MiMo `mimo-v2.5`。 | ModelRegistry、OpenAICompatibleProvider、AttachmentService vision path、vision smoke script |
| PD-039 | confirmed | “拍给小白狐看”默认是普通图片分享；不要用图片描述里的地址、电话、学校名等关键词自动路由到 `privacy.boundary`，隐私边界只由明确隐私意图或后续安全策略触发。 | AttachmentService、OCR/vision provider、PromptManager、Android pending image context、QA |
| PD-040 | revised | 父亲日报在父亲点开时应结合当天已落库会话消息、路由摘要和结构化 memory，由 `ModelTaskType.PARENT_REPORT` 大模型总结生成；当天有新会话素材时刷新已有日报，但仍不展示逐字聊天记录。 | ParentReportService、ModelRegistry、ConversationPersistenceRepository、parent_reports、Android ParentReportScreen |
| PD-047 | confirmed | 当前本地测试阶段允许通过临时表 `model_debug_traces` 记录完整模型 prompt 和回复，用于 prompt/体验分析；做相关功能测试时必须显式开启并验证写入，不保存 secrets/raw media/base64，不代表生产儿童数据策略。 | ModelRegistry、model_debug_traces、backend docs、prompt QA |
| PD-048 | confirmed | ASR v1 真实识别第一选择改为 sherpa-onnx + SenseVoice-Small int8 本地推理；本地异常后再走原有 MiMo ASR fallback。当前测试阶段应启用 local_sensevoice 验证真实本地识别，MiMo fallback 仍需父亲授权和 ASR data policy flags。 | backend ASR provider、AsrService fallback、ASR docs、QA |
| PD-049 | revised | 家庭 MVP 前 opening greeting 默认走 deterministic policy/template 主路径；父亲日报已由 PD-052 修订为 model-first。 | OpeningService、OpeningPolicyBuilder、QA |
| PD-052 | confirmed | 父亲日报 v2 必须 model-first：程序只构造当天受控 evidence packet 并调用 `ModelTaskType.PARENT_REPORT`，模型结构化 JSON 才是正式日报；失败时返回明确可重试状态，不用规则日报冒充成功。 | ParentReportService、ModelRegistry、ParentReportScreen、parent_reports |
| PD-053 | confirmed | 真机 QA 发现有图片上下文时模型仍可能说“看不到图片”，stream TTS 失败时 Android 系统音色混播，opening 首屏被同步 TTS 拉慢；当前修正为：图片上下文优先且禁止拒看话术，stream TTS 失败不再混用系统 TTS 朗读同段，opening 默认先返回文本不等待远程 TTS。 | PromptManager、ChildAgentRuntime、TextSegmenter、OpeningService、Android ChatViewModel、QA |

新增执行依据：

```text
PD-028 / PD-029 / PD-030 / PD-039 是 freedom-first 与图片/父母寄语方向的最高优先级产品修正；PD-048 是当前 ASR 第一选择，PD-034 / PD-035 保留为 MiMo fallback 的约束，PD-036 / PD-037 是 voice-first 和开场白体验的最高优先级语音输入修正；PD-049 是家庭 MVP 前 opening/parent report 的默认生成路径。
不要继续把 after_school、homework、bedtime、photo 做成默认硬模式。
```

### 2.1 Structured Decision Records

#### PD-001

Decision ID: PD-001
Date: 2026-05-19
Status: confirmed
Source: father / product planning
Decision: 下一阶段优先解决语音交互和小白狐形象体验。
Rationale: v0.1 后端和 Android MVP 已完成，家庭内测前的主要体验缺口在自然输入、朗读反馈和智能体形象。
Affected modules: Android chat UI、voice、TTS、FoxAgent presentation、QA、docs。
Implementation notes: 先完成设备 QA，再分阶段实现语音输入、TTS、小白狐视觉资源和状态机。
Docs updated: `README.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`。
Tests or QA needed: 完整设备 QA、语音 QA、小白狐状态和资源 QA。

#### PD-002

Decision ID: PD-002
Date: 2026-05-19
Status: revised
Source: father / product planning; revised by PD-027 for TTS
Decision: 语音输入 ASR v1 目标修订为后端接 MiMo audio input / ASR；Android 不直接调用 MiMo，只负责点击录音、上传到后端、展示儿童端语音状态，并在儿童默认模式自动发送非空 transcript；确认面板只保留为 DevSettings / 父亲调试模式。TTS 正式音色路径已由 PD-027 修订为后端 MiMo VoiceClone。
Rationale: 父亲已完成 MiMo ASR 调研并确认 ASR 方案接 MiMo；为了避免 Android 持有 API key 和供应商逻辑，真实 ASR 统一由后端 provider 和 data policy guard 控制。系统 TTS 在 Redmi K60 上不可用或体验不理想，因此不再作为正式小白狐音色方案。
Affected modules: Android voice、Android permissions、backend ASR API、MiMo ASR provider、privacy policy、QA。
Implementation notes: 儿童默认 `VOICE_CONFIRM_BEFORE_SEND=false`，ASR ok 且 transcript 非空后自动进入 conversation；开发/父亲调试可打开 `VOICE_CONFIRM_BEFORE_SEND=true` 查看待确认文本。不做常开麦克风；后端 ASR 真实链路测试必须显式选择目标 provider；真实儿童音频外发必须满足父亲授权和 `CHILD_AI_MIMO_ASR_*` policy flags；开发阶段只用 fake/smoke audio。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`android/README.md`、`backend/README.md`。
Tests or QA needed: 权限、识别、失败 fallback、无音频文件保存检查。

#### PD-003

Decision ID: PD-003
Date: 2026-05-19
Status: revised
Source: father / product planning; revised by father voice-first feedback on 2026-05-21
Decision: 儿童端默认改为 voice-first 自动发送：ASR 成功且 transcript 非空时自动进入 conversation；confirm-before-send 仅保留为 DevSettings / 父亲调试模式。
Rationale: 真机反馈显示孩子不会稳定编辑文字或点击确认按钮；儿童端应以自然说话为主，失败时提供重说/取消，而不是把文字编辑作为主流程。
Affected modules: Android InputBar、ChatViewModel、voice UI state、QA。
Implementation notes: `VOICE_CONFIRM_BEFORE_SEND=false` 为儿童默认；`VOICE_CONFIRM_BEFORE_SEND=true` 时保留旧确认面板供开发/父亲排查。自动发送后的 transcript 才作为正常 child text 进入 conversation。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`android/README.md`。
Tests or QA needed: ASR ok 自动发送、needs_retry 不发送、permission denied 不发送、开发确认模式仍可用。

#### PD-004

Decision ID: PD-004
Date: 2026-05-19
Status: confirmed
Source: father / design direction
Decision: 小白狐形象应温和、好奇、慢热友好，避免强刺激、排行榜、连击奖励或上瘾式动画。
Rationale: 智能体应支持陪伴和引导，不应诱导孩子延长使用或形成刺激性依赖。
Affected modules: visual design、Android presentation、animation state、QA。
Implementation notes: 所有视觉资源和动效必须低刺激、可收尾，不做游戏化奖励机制。
Docs updated: `docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`AGENTS.md`。
Tests or QA needed: 动效 QA、儿童安全视觉 review。

#### PD-005

Decision ID: PD-005
Date: 2026-05-19
Status: confirmed
Source: implementation review
Decision: 后端继续通过 `reply.voice_enabled`、`reply.audio_url`、`reply.emotion`、`reply.agent_motion` 向 Android 暴露表现层信号。
Rationale: 后端负责安全和语义状态，Android 负责展示和本地表现，避免客户端复制 AI 决策逻辑。
Affected modules: backend conversation schema、ChildAgentRuntime、Android DTO、FoxAgent presentation、TTS。
Implementation notes: Android 可用这些字段做朗读和状态映射，但不得绕过后端安全判断。
Docs updated: `README.md`、`backend/README.md`、`android/README.md`、`docs/VOICE_INTERACTION_DESIGN_V0_1.md`。
Tests or QA needed: API DTO mapping、reply.voice_enabled=false 时不朗读。

#### PD-006

Decision ID: PD-006
Date: 2026-05-19
Status: confirmed
Source: father / safety boundary
Decision: 小白狐表现层不得制造“唯一朋友”“只有我懂你”等依赖感。
Rationale: 儿童智能体必须避免替代父母、老师或可信成人，也不能形成秘密关系。
Affected modules: PromptManager、SafetyEngine、ChildAgentRuntime、Android copy、visual design、TTS。
Implementation notes: 文案、语音、视觉和动画都不得表达排他关系或让孩子疏远可信成人。
Docs updated: `AGENTS.md`、`docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md`、`docs/VOICE_INTERACTION_DESIGN_V0_1.md`。
Tests or QA needed: 输出安全测试、文案扫描、视觉 review。

#### PD-007

Decision ID: PD-007
Date: 2026-05-19
Status: confirmed
Source: father / safety boundary
Decision: 所有新体验仍必须遵守：不直接给作业最终答案，不要求保密，不鼓励隐瞒父母，不保存原始音频/照片到长期记忆。
Rationale: 语音、TTS 和形象体验不能削弱既有儿童安全底线。
Affected modules: backend safety、learning scenes、memory hooks、Android voice、TTS、QA。
Implementation notes: 语音最终仍走后端文本链路；长期 memory 只保存结构化摘要，不保存 raw audio/raw photo/full transcript。
Docs updated: `AGENTS.md`、`docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`。
Tests or QA needed: 学习拒答、高风险、memory evidence、raw data scan。

#### PD-008

Decision ID: PD-008
Date: 2026-05-19
Status: confirmed
Source: father / workflow requirement
Decision: 每次父亲确认的新产品想法，必须先写入 `docs/PRODUCT_DECISIONS_V0_1.md`，再进入子会话实现。
Rationale: 多会话并行时，如果产品决策只留在聊天记录中，子会话会按旧假设开发。
Affected modules: Codex workflow、AGENTS、session process、docs。
Implementation notes: 子会话开始前检查本文件；冲突时先报告，不擅自改产品方向。
Docs updated: `AGENTS.md`、`README.md`、`docs/PRODUCT_DECISIONS_V0_1.md`。
Tests or QA needed: 文档一致性检查。

#### PD-009

Decision ID: PD-009
Date: 2026-05-19
Status: confirmed
Source: father / naming decision
Decision: 正式名称为“小白狐”；UI、产品、设计和测试说明优先统一。代码 class 名 `FoxAgent` 暂可保留，后续如要改代码命名单独 refactor。
Rationale: 先统一面向儿童和设计端的产品称呼，同时避免在语音/动画任务中混入大规模命名 diff。
Affected modules: Android UI copy、README、design docs、QA、future refactor。
Implementation notes: 新文档和新 UI 文案使用“小白狐”；历史旧称“小狐狸”只作为旧文档和旧代码背景跟踪。
Docs updated: `README.md`、`android/README.md`、`docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md`、`docs/MANUAL_QA_V0_1.md`。
Tests or QA needed: UI 文案 QA、后续命名替换 smoke test。

#### PD-010

Decision ID: PD-010
Date: 2026-05-19
Status: revised
Source: father / voice interaction decision; revised by MiMo ASR v1 confirmation and voice-first feedback on 2026-05-21
Decision: 语音输入 v1 儿童默认流程是点击语音 -> 孩子说话 -> Android 上传短音频到后端 ASR -> ASR ok 自动发送 transcript -> text 走 conversation stream；future hands-free conversational mode 不进入 v1。
Rationale: 儿童默认体验需要减少文字编辑和确认按钮；但仍保持主动点击录音、非连续监听、可取消/重说和后端统一安全链路。
Affected modules: Android voice、InputBar、ChatViewModel、ASR API、conversation API usage、QA。
Implementation notes: v1 不做常开麦克风或唤醒词；Android 不保存 MiMo API key；自动发送后的 transcript 是正式 child message，未成功识别或未发送前不入库、不进 memory。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`android/README.md`。
Tests or QA needed: 自动发送、取消/重说、权限拒绝、policy blocked、开发确认模式。

#### PD-011

Decision ID: PD-011
Date: 2026-05-19
Status: revised
Source: father / TTS decision; revised by PD-027 for voice source
Decision: TTS 默认自动朗读小白狐回复；必须有停止/静音、DevSettings 或父亲设置开关。系统 `VoiceProfile` 保留为 fallback，正式品牌音色由 PD-027 的 MiMo VoiceClone 承担。
Rationale: 语音体验应默认可听见，但必须给父亲和孩子保留控制权；系统 TTS 无法保证固定音色且 Redmi K60 体验不理想，因此正式声音来源改为后端生成音频。
Affected modules: Android TTS、DevSettings、parent settings、VoiceProfile、backend TTS、QA。
Implementation notes: 只朗读 agent reply，不朗读孩子输入、debug 或 session_state；优先播放 `reply.audio_url`，失败时 fallback 系统 TTS 或文字；高风险和睡前场景低刺激。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`android/README.md`。
Tests or QA needed: 自动朗读、停止/静音、开关、reply.voice_enabled=false。

#### PD-012

Decision ID: PD-012
Date: 2026-05-19
Status: confirmed
Source: father / TTS decision
Decision: `VoiceProfile` v1 包含 `preferredVoiceName`、`zh-CN`、稍慢 `speechRate`、偏高但不过度的 `pitch`、fallback 系统默认中文 voice。
Rationale: Android 系统 TTS 的 voice 依赖设备和引擎，必须通过可调配置形成可评估、可替换的第一版音色策略。
Affected modules: Android TtsController、VoiceProfile、DevSettings、QA。
Implementation notes: 找不到中文 voice 时温和降级为文字显示，不生成或保存音频文件。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`android/README.md`。
Tests or QA needed: zh-CN voice selection、fallback、TTS 不可用路径。

#### PD-013

Decision ID: PD-013
Date: 2026-05-19
Status: confirmed
Source: father / visual direction decision
Decision: 小白狐视觉目标是 3D / soft 3D / 毛绒感 / 立体绘本感；Compose Canvas / 2D 只是 fallback，不阻塞语音开发。
Rationale: 产品正式方向需要更有质感和亲和力的三维小白狐，但当前体验闭环不能被素材交付阻塞。
Affected modules: visual design、Android drawable resources、CartoonAgentView、QA。
Implementation notes: 没有真实 3D 资源时继续使用 Canvas fallback，不硬塞低质量临时图。
Docs updated: `docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`android/README.md`。
Tests or QA needed: 资源规格、fallback、视觉安全 review。

#### PD-014

Decision ID: PD-014
Date: 2026-05-19
Status: confirmed
Source: father / architecture decision
Decision: 允许 Android `SpeechRecognizer` / `TextToSpeech`，但必须通过可替换抽象：`VoiceEngine` / `SpeechInputController` / `TtsController`。
Rationale: Android 系统能力可快速落地，但不同设备效果不稳定，后续可能替换为其他 ASR/TTS 方案。
Affected modules: Android voice package、InputBar、ChatViewModel、tests、docs。
Implementation notes: UI 不直接散落平台调用；抽象层负责权限、生命周期、失败和替换边界。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`android/README.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`。
Tests or QA needed: controller 单元测试、生命周期释放、平台不可用 fallback。

#### PD-015

Decision ID: PD-015
Date: 2026-05-19
Status: confirmed
Source: father / QA decision
Decision: 语音 QA 必须记录识别准确率、延迟、中文效果、儿童声音识别、TTS 自然度和孩子接受度。
Rationale: 语音体验质量高度依赖设备、系统引擎、环境噪声和儿童声音，不能只用编译通过代表可用。
Affected modules: manual QA、device QA、voice implementation planning。
Implementation notes: 如果 ASR/TTS 效果不好，不继续堆功能，应先回到体验评估。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`docs/MANUAL_QA_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`。
Tests or QA needed: 设备侧语音体验记录、家庭内测反馈。

#### PD-016

Decision ID: PD-016
Date: 2026-05-19
Status: confirmed
Source: father / visual direction decision
Decision: 小白狐应是 3D 卡通、柔和立体、有毛绒感、儿童动画质感的卡通形象，整体活泼开朗，支持说话、倾听、蹦蹦跳跳等状态。
Rationale: 新候选形象已经从更安静的占位方向推进到儿童动画质感，角色需要更清晰地承担语音交流和状态反馈。
Affected modules: visual design、Android drawable resources、CartoonAgentView、animation state、QA。
Implementation notes: 活泼状态必须受控，不能变成连击奖励、排行榜、强刺激弹跳或诱导长时间使用。
Docs updated: `docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`android/README.md`。
Tests or QA needed: 视觉状态 QA、动画低刺激 review、低配设备流畅度记录。

#### PD-017

Decision ID: PD-017
Date: 2026-05-19
Status: confirmed
Source: father / voice direction decision
Decision: 小白狐音色方向是小孩子般干净、清脆、中性、活泼可爱，但不能过度尖锐或幼稚。
Rationale: 默认自动朗读需要更贴近角色气质；Android 系统 TTS 无法稳定提供满意音色，父亲已通过 MiMo Studio 筛选出 v01 小白狐样本。
Affected modules: backend TTS、Android remote audio playback、VoiceProfile fallback、DevSettings、QA。
Implementation notes: 正式声音由 MiMo VoiceClone v01 承担；系统 VoiceProfile 只作为 fallback 和诊断能力，效果不好时降级为远程音频或文字。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`android/README.md`、`docs/MANUAL_QA_V0_1.md`。
Tests or QA needed: TTS 自然度、音高、语速、是否尖锐、儿童接受度。

#### PD-018

Decision ID: PD-018
Date: 2026-05-19
Status: confirmed
Source: father / QA strategy decision
Decision: 采用双设备测试策略：高配 Android 手机作为功能主验证设备，Honor Pad 5 Android 9 / 4GB 作为低配兼容性和大屏目标设备。
Rationale: Honor Pad 5 配置较低，不应阻塞早期语音和小白狐体验开发；但它仍代表低配平板兼容性、性能和儿童真实尺寸验证。
Affected modules: manual QA、Android runtime、voice、TTS、FoxAgent presentation、performance mode。
Implementation notes: 先在高配手机跑通功能闭环，再在 Honor Pad 5 验证 Android 9、4GB RAM、横屏/大屏、ASR/TTS、图片内存、动画流畅度、发热和降级策略。
Docs updated: `docs/MANUAL_QA_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`android/README.md`。
Tests or QA needed: 每个语音和小白狐 QA 结果记录设备型号、Android 版本、是否通过、延迟、卡顿、ASR 准确率、TTS 自然度、动画流畅度和是否需要降级。

#### PD-019

Decision ID: PD-019
Date: 2026-05-19
Status: confirmed
Source: father / Android runtime decision
Decision: 小白狐 Android 第一版运行方式优先预渲染 3D PNG/WebP 状态图 + 轻量 Compose 动画；不把实时 3D 引擎或重型动画依赖作为第一版必需能力。
Rationale: 预渲染资源更利于 Android 9 / 4GB 低配兼容和快速迭代，避免早期把风险集中到实时 3D、动画依赖和性能问题上。
Affected modules: Android drawable resources、CartoonAgentView、DevSettings、QA。
Implementation notes: 必须保留低性能模式：减少动画、降低图片尺寸、关闭自动动画或仅保留静态状态图。
Docs updated: `docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`android/README.md`。
Tests or QA needed: 高配手机显示、Honor Pad 5 流畅度、低性能模式、资源缺失 fallback。

#### PD-020

Decision ID: PD-020
Date: 2026-05-19
Status: revised
Source: father / asset delivery
Decision: 小白狐 v1 初始候选形象资产包含 `neutral_idle`、`listening`、`speaking`、`jumping_happy`、`thinking` 五个基础状态；现已由 PD-023 扩展为 11 个状态。
Rationale: 先用 5 个基础状态验证角色识别度、资源切换、TTS speaking 联动和低配性能；随后补全安全、隐私、睡前、网络错误等专门状态。
Affected modules: docs assets、Android drawable-nodpi、FoxAgentAssetMapper、CartoonAgentView、QA。
Implementation notes: 资源归档到 `docs/assets/fox/v1/`，Android 运行时资源放在 `android/app/src/main/res/drawable-nodpi/`；Canvas fallback 继续保留。
Docs updated: `docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`docs/MANUAL_QA_V0_1.md`、`android/README.md`。
Tests or QA needed: 缺失状态不崩溃、网络错误 fallback、TTS speaking 后续联动、Honor Pad 5 图片内存和切换流畅度。

#### PD-021

Decision ID: PD-021
Date: 2026-05-19
Status: revised
Source: father / real device QA; revised by PD-027 for voice source
Decision: Redmi K60 / Android 14 真机反馈显示系统 TTS 链路不可观测且无声；已先修诊断和 fallback，正式音色路径由 PD-027 改为后端 MiMo VoiceClone。
Rationale: 真机上同时出现无声音、无停止/静音提示、小白狐不切 speaking，说明问题不能只归因于系统音色不好，必须先判断是否触发、初始化、选 voice 和 speak 返回值。
Affected modules: Android TtsController、AndroidTtsController、ChatViewModel、InputBar、FoxAgent state、Manual QA。
Implementation notes: 增加 TtsUiState / VoiceDiagnostics，记录初始化、locale、voice、setLanguage、setVoice、speak 返回值和失败原因；speaking 状态不再完全依赖系统 onStart。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`docs/MANUAL_QA_V0_1.md`、`android/README.md`。
Tests or QA needed: Redmi K60 复验 TTS 状态、诊断文本、speaking pending、真实声音和失败原因。

#### PD-022

Decision ID: PD-022
Date: 2026-05-19
Status: confirmed
Source: father / real device QA
Decision: Android 系统 TTS 只是 v1 验证方案，不作为最终儿童产品音色承诺；后续需评估小白狐专属或替代音色方案。
Rationale: Redmi K60 上系统文字转语音相关服务即使可用，声音也不适合孩子；目标音色仍是小孩子般干净、清脆、中性、活泼可爱，但不能尖锐或幼稚。
Affected modules: Android TTS、VoiceProfile、future TTS provider selection、data policy、QA。
Implementation notes: 当前不接第三方 TTS；如使用云 TTS，必须新增 TTS data policy guard，并由父亲确认供应商、留存、训练、删除、费用和稳定性。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`。
Tests or QA needed: 记录系统 TTS 自然度和孩子接受度，输出替代方案预研。

#### PD-023

Decision ID: PD-023
Date: 2026-05-19
Status: confirmed
Source: father / asset delivery
Decision: 新增 6 张小白狐状态图 calm、sleepy、safety_concern、privacy_boundary、homework_focus、network_error 已提交，需接入 Android 资源映射并保留 Canvas fallback。
Rationale: 这些状态覆盖睡前、安全、隐私、学习和网络错误等关键体验，可以减少用 neutral 复用导致的状态不准确。
Affected modules: docs assets、Android drawable-nodpi、FoxAgentAssetMapper、AgentPresentation、Manual QA。
Implementation notes: Android 静态资源名仍使用 `fox_3d_<state>`，当前文件格式已压缩为 WebP；低配设备仍可强制 Canvas 或静态降级。
Docs updated: `android/README.md`、`docs/MANUAL_QA_V0_1.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`。
Tests or QA needed: 高配手机和 Honor Pad 5 验证资源显示、切换流畅度、缺失状态 fallback 和内存压力。

#### PD-024

Decision ID: PD-024
Date: 2026-05-19
Status: revised
Source: father / product feedback
Decision: 普通聊天进入 Open Conversation Mode / Freer Context Mode：普通兴趣和日常话题更自由，模型接收最近多轮短期上下文，SceneOrchestrator 保留安全、隐私、学习和睡前约束。
Rationale: 当前普通对话仍显得程序控制较重，快捷选项和上下文不够自然；自由聊天需要更完整的实时多轮上下文。
Affected modules: backend conversation runtime、ChildAgentRuntime、PromptManager、ConversationHistoryService、quick actions、QA。
Implementation notes: 已先实现小步后端版本：普通话题进入 `conversation.open`，PromptManager 使用开放对话 prompt，ChildAgentRuntime 传入进程内短期 history；不把完整聊天写入长期 memory 或父亲日报。
Docs updated: `docs/NEXT_PHASE_PLAN_V0_2.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`backend/README.md`。
Tests or QA needed: 普通兴趣话题多轮上下文、学习不直接给答案、高风险/隐私/睡前约束不回退。

#### PD-025

Decision ID: PD-025
Date: 2026-05-19
Status: confirmed
Source: father / real device screenshot
Decision: Redmi K60 截图中的 TTS 失败先按代码链路不可用处理，而不是按“系统音色不好”处理。
Rationale: 截图显示 `speak=SKIPPED_UNAVAILABLE`、`failure=TextToSpeech is unavailable`，说明上一版 Android 端在调用 `speak()` 前已经判定 TextToSpeech 不可用。
Affected modules: AndroidTtsController、AndroidManifest、InputBar、TTS QA、android/README。
Implementation notes: 修复 TextToSpeech 初始化竞态风险，声明 TTS service package visibility，TTS 不可用时显示“检查朗读设置”和“安装语音数据”入口；复测时继续记录 engine、locale、voice、lang、setVoice、speak 和 failure。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`docs/MANUAL_QA_V0_1.md`、`android/README.md`。
Tests or QA needed: Redmi K60 安装新 APK 后复验是否仍为 SKIPPED_UNAVAILABLE，或是否进入更具体的 lang / speak / voice 失败。

#### PD-026

Decision ID: PD-026
Date: 2026-05-19
Status: confirmed
Source: father / product feedback
Decision: 当前阶段不读取或保存完整逐字聊天数据库；普通聊天只使用进程内短期 history 给模型补上下文。
Rationale: 项目当前没有持久化完整聊天数据库，长期保存完整儿童聊天原文不符合数据最小化原则；但模型需要最近几轮上下文来避免每轮像第一次聊天。
Affected modules: ConversationHistoryService、ChildAgentRuntime、ConversationService、MemoryService、ParentReportService。
Implementation notes: `ConversationHistoryService` 只保留每个 session 的短窗口 user/assistant 消息，服务重启丢失；长期 memory 仍只写结构化摘要，不写 raw chat/full transcript。
Docs updated: `backend/README.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`。
Tests or QA needed: 同 session 连续普通聊天能利用上下文；父亲日报不展示逐字聊天记录。

#### PD-027

Decision ID: PD-027
Date: 2026-05-20
Status: confirmed
Source: father / MiMo Studio voice design
Decision: 小白狐正式品牌音色方案改为后端 MiMo VoiceClone：`MiMo-V2.5-TTS-VoiceDesign` 只用于前期设计和筛选角色音色且已完成；`MiMo-V2.5-TTS-VoiceClone` 使用已下载的 wav 样本作为正式 App 主音色；`MiMo-V2.5-TTS` 只作为临时测试、内置音色对照或兜底。
Rationale: Redmi K60 系统 TTS 不可用或体验不理想，且父亲已通过 MiMo Studio 得到满意的小白狐音色样本，后端生成音频可提供更稳定一致的品牌声音。
Affected modules: backend TTS service、TTS data policy guard、TTS cache、MiMo VoiceClone provider、conversation reply audio_url、Android remote audio playback、QA。
Implementation notes: 音色样本归档为 `backend/assets/voices/xiaobaohu_voice_v01.wav`，sha256=`8eec0f98629350a1dd09bd98a31c2bee80132128bf214d4c0a009331c9a66c40`；当前测试阶段应启用目标 TTS provider 验证小白狐音频链路；MiMo VoiceClone 必须通过独立 TTS env 和 policy guard；真实 VoiceClone smoke 已确认当前 provider 走 `/chat/completions`，返回音频从 `choices[0].message.audio.data` 读取；Android 不直接调用 MiMo，不存 API key；生成音频缓存不提交 git。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`backend/README.md`、`android/README.md`。
Tests or QA needed: `/api/v1/tts/xiaobaohu` mock、policy block、cache hit、voice sample missing 和真实 MiMo smoke 已通过；后续 Android audioUrl playback、fallback 和真机听感。

#### PD-028

Decision ID: PD-028
Date: 2026-05-20
Status: confirmed
Source: father / product direction
Decision: 本地持久化数据库选择 PostgreSQL。v0.1-dev 先作为家庭自用本地库，允许交互文本进入本地 PostgreSQL，用于上下文、复盘、父亲日报和后续体验优化；原始音频、原始照片、API key 和生产 secret 仍不得入库。
Rationale: 当前内存态服务重启会丢失父亲设置、会话、记忆和日报素材；家庭内测前需要本地可追溯数据基础，同时仍保持本地优先和数据最小化。
Affected modules: backend DB layer、SQLAlchemy/Alembic、ParentPolicyService、ConversationService、MemoryService、ParentReportService、TTS cache metadata、QA。
Implementation notes: DB1-A 已新增 SQLAlchemy sync、Alembic、psycopg、PostgreSQL 16 local docker compose、初始表结构和 DB 基础设施测试；业务服务仍未迁移，后续按 B2-B5 串行接入。
Docs updated: `backend/README.md`、`docs/SYSTEM_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`docs/MANUAL_QA_V0_1.md`。
Tests or QA needed: Alembic migration、ParentPolicy 持久化、conversation message 落库、memory/report 落库、确认 debug/key/raw audio/raw photo 不入库；未来云端化或上架前必须重新做儿童数据合规评审。

#### PD-029

Decision ID: PD-029
Date: 2026-05-20
Status: confirmed
Source: father / animation asset delivery
Decision: 小白狐动态形象第一版采用父亲提供的 3D 风格序列帧资源包，Android 运行时使用 manifest-driven `animation_v1` 播放；运行时包只保留一套 512px WebP sequence；旧静态 drawable 资源和 Compose Canvas 必须继续作为 fallback。
Rationale: 父亲已提供完整序列帧资源包，比单张静态状态图更接近“小白狐会说话、会倾听、会思考”的体验目标；同时 Honor Pad 5 是 Android 9 / 4GB 低配目标设备，必须保留可降级路径。
Affected modules: Android mascot assets、MascotController、AssetManifestLoader、FrameSequencePlayer、CartoonAgentView、DevSettings、Manual QA、visual design docs。
Implementation notes: Android 运行时资源放在 `android/app/src/main/assets/mascot/xiaobaohu/v1/`，当前 manifest 声明 11 个状态、每状态 24 帧、12 FPS，runtime assets 约 4.9MB；静态 drawable fallback 也压缩为 WebP，约 1.5MB；渲染 fallback 链为 `animation_v1 -> png_static -> canvas`，其中 `png_static` 保留旧模式名；不接 Rive、不接实时 3D；不把验收全量包、PNG frames、preview html/gif/webp/spritesheet 作为运行时依赖。
Docs updated: `docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`docs/MANUAL_QA_V0_1.md`、`android/README.md`。
Tests or QA needed: Android 单测覆盖 manifest 解析、状态优先级、short_loop 和 unknown fallback；Redmi K60 验证 idle/listening/thinking/speaking/network_error；Honor Pad 5 验证卡顿、发热、APK 体积和低性能降级。

#### PD-030

Decision ID: PD-030
Date: 2026-05-20
Status: confirmed
Source: father / real device QA
Decision: 当前体验不能继续依赖提高 read timeout；下一阶段必须进入流式交互设计与分阶段实现，优先降低首字延迟和首音频延迟。
Rationale: Redmi K60 真机已确认 MiMo VoiceClone 音频初步可听、动态小白狐已接入，但同步链路仍需等待 LLM 完整文本和 TTS 完整音频，整体等待时间长。
Affected modules: backend conversation stream endpoint、ChildAgentRuntime、TtsService、Android stream client、AudioSegmentQueuePlayer、Manual QA。
Implementation notes: 先写 `STREAMING_INTERACTION_DESIGN_V0_1.md`；保留现有 `/api/v1/conversation/message`；新增 stream path 必须继续走 SafetyEngine、SceneOrchestrator、ChildAgentRuntime 和 TtsDataPolicyGuard。若 MiMo 不支持 true streaming，先做 sentence-level pseudo streaming。
Docs updated: `docs/NEXT_PHASE_PLAN_V0_2.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`docs/MANUAL_QA_V0_1.md`、`docs/VOICE_INTERACTION_DESIGN_V0_1.md`。
Tests or QA needed: 记录 first_text_ms、first_audio_ms、total_turn_ms、stream 中断 fallback、TTS 失败不影响文本。

#### PD-031

Decision ID: PD-031
Date: 2026-05-20
Status: confirmed
Source: father / product direction
Decision: 儿童端主界面下一版改为横屏双栏布局，手机也自动横屏：左侧动态小白狐，右侧聊天交互。
Rationale: 小白狐已经成为核心体验元素，横屏能让小白狐和对话区同时可见，更适合平板和家庭内测场景。
Affected modules: Android Manifest、ChildChatScreen、CartoonAgentView、Manual QA、android README。
Implementation notes: 首版先做结构可用性：Row 双栏，左侧约 38%-45% 小白狐，右侧约 55%-62% 消息、快捷动作、输入和停止/静音；不做完整 UI 美术重设计，不破坏 remote audioUrl 播放和 animation_v1 fallback。
Docs updated: `docs/NEXT_PHASE_PLAN_V0_2.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`docs/MANUAL_QA_V0_1.md`、`android/README.md`。
Tests or QA needed: Redmi K60 横屏可点击、字体可读、键盘不遮挡主要交互；Honor Pad 5 横屏大屏比例和低配动画流畅度。

#### PD-032

Decision ID: PD-032
Date: 2026-05-20
Status: revised
Source: father / product direction; revised by MiMo ASR v1 confirmation on 2026-05-21
Decision: MiMo ASR / audio input 调研已完成，ASR v1 方案确定接 MiMo；实现顺序是后端 provider 和 policy gate 先行，Android 负责录音上传和儿童端语音状态，儿童默认自动发送 transcript，确认 UI 仅保留为开发/父亲模式。
Rationale: 家庭真实使用大多数时间会是语音交互；父亲已经确认 MiMo ASR 方案，因此下一阶段应进入受控后端接入和 fake audio smoke，而不是继续停留在候选调研。
Affected modules: ASR research docs、MiMo ASR provider、ASR data policy guard、Android voice abstraction、future SpeechInputController、TTS/stream UX、QA。
Implementation notes: 儿童默认自动发送，调试时可恢复 confirm-before-send；真实儿童音频外发必须通过父亲授权和 ASR policy flags；Android 不保存模型 API key；开发 smoke 只允许 fake/smoke audio。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`。
Tests or QA needed: 确认 MiMo ASR 是否支持中文儿童语音、流式/非流式、音频格式、留存策略、是否训练、延迟和费用。

#### PD-033

Decision ID: PD-033
Date: 2026-05-20
Status: confirmed
Source: father / engineering review
Decision: 下一阶段必须补齐基础运行组件，至少包括 request_id、结构化日志、provider timing、health 扩展、环境检查和 QA 记录，而不是只继续堆体验功能。
Rationale: 真机联调已经暴露“健康检查正常但 conversation 慢或失败”“日志看不到足够原因”“设备侧无法判断 TTS/后端/网络哪一段失败”等问题，需要可观测性支持后续流式和语音开发。
Affected modules: backend logging middleware、health endpoint、provider wrappers、scripts、Manual QA、ops docs。
Implementation notes: 先做 `OPS_FOUNDATION_GAP_ANALYSIS_V0_1.md`；首批实现建议限于本地开发可用的 request_id、timing 和健康检查，不接第三方 APM 或外部日志平台。
Docs updated: `docs/NEXT_PHASE_PLAN_V0_2.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`backend/README.md`。
Tests or QA needed: 日志不含 API key 或完整儿童文本；health 能区分 postgres、tts_cache、mimo_config；QA 能记录 request_id。

#### PD-034

Decision ID: PD-034
Date: 2026-05-21
Status: revised
Source: father / MiMo ASR integration decision
Decision: ASR v1 方案确定接 MiMo audio input / ASR。Android 不直接调用 MiMo，只负责点击录音、上传到后端和展示儿童端语音状态；儿童默认自动发送非空 transcript，confirm-before-send 仅作为 DevSettings / 父亲调试模式；不做常开麦克风。
Rationale: 父亲已完成 MiMo ASR 接入方案调研并明确确认后续仍接 MiMo。后端统一持有 provider 配置和 API key，能集中做授权、日志脱敏、超时、错误映射和儿童音频外发策略。
Affected modules: backend ASR provider、ASR API、AsrDataPolicyGuard、Android voice upload/confirm UI、QA、docs。
Implementation notes: 真实儿童音频外发必须同时满足 `CHILD_AI_ASR_PROVIDER=mimo`、`CHILD_AI_MIMO_ASR_ENABLED=true`、API key 存在、`CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO=true`、`CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED=true`、`CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED=true`。开发阶段只用 fake audio / smoke audio；原始音频不入长期库、不进日志、不提交仓库。
Docs updated: `docs/ASR_INPUT_RESEARCH_V0_1.md`、`docs/MIMO_ASR_INTEGRATION_DESIGN_V0_1.md`、`docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`backend/README.md`。
Tests or QA needed: ASR policy-blocked 默认路径、fake audio MiMo smoke、Redmi K60 / Honor Pad 5 录音上传、默认自动发送、DevSettings 确认模式、secret/base64 scan。

#### PD-036

Decision ID: PD-036
Date: 2026-05-21
Status: confirmed
Source: father / voice-first child UI feedback
Decision: 儿童主界面默认隐藏文字输入框、发送按钮和可编辑 ASR 文本确认面板；语音是主输入，保留重说、取消、停止朗读、静音等大按钮。
Rationale: 真机反馈显示孩子不会稳定编辑识别文本或点击确认按钮；儿童默认界面应减少文字编辑负担，突出可理解的大按钮。
Affected modules: Android InputBar、ChatViewModel、DevSettings、Manual QA。
Implementation notes: `CHILD_VOICE_FIRST_MODE=true`、`VOICE_CONFIRM_BEFORE_SEND=false`、`SHOW_TEXT_INPUT_FOR_CHILD=false` 是儿童默认；开发/父亲模式可打开文字输入或确认面板排查问题。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`android/README.md`、`docs/MANUAL_QA_V0_1.md`。
Tests or QA needed: 默认界面无文字输入框/发送按钮；ASR ok 自动发送；needs_retry、permission denied、policy blocked 不自动发送。

#### PD-037

Decision ID: PD-037
Date: 2026-05-21
Status: confirmed
Source: father / opening greeting feedback
Decision: App 打开儿童聊天页后，小白狐应主动请求 opening greeting，基于时间、父母寄语和孩子称呼生成一句短开场白；称呼优先 `child_nickname`，其次 `child_display_name`，都没有则不强行称呼。
Rationale: 孩子打开 App 时需要小白狐自然进入状态，至少在已配置称呼时喊一下孩子，而不是空白等待或固定模板。
Affected modules: backend opening API、ParentPolicy schema、Prompt/opening service、Android ChatViewModel、Android father settings、remote audio playback、QA。
Implementation notes: 后端新增 `POST /api/v1/conversation/opening`；同一 session 做短期去重；TTS 失败不影响文本 opening。Android 每个 chat session 只请求一次，如果孩子先开始说话，opening 不应打断或覆盖孩子输入。父亲设置页已支持配置 `child_nickname` 和 `child_display_name`，文案不诱导填写真实全名。
Docs updated: `backend/README.md`、`android/README.md`、`docs/MANUAL_QA_V0_1.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`。
Tests or QA needed: 小名优先、display name fallback、无名称不强称呼、晚上低刺激、父母寄语不查岗、opening 音频播放、用户先说话时不插入；Redmi K60 / Honor Pad 5 真机复验父亲设置保存后的 opening 称呼。

#### PD-035

Decision ID: PD-035
Date: 2026-05-21
Status: confirmed
Source: father / MiMo ASR key and model correction
Decision: MiMo ASR 复用当前 MiMo key：优先 `CHILD_AI_MIMO_ASR_API_KEY`，为空时使用 `CHILD_AI_MIMO_API_KEY`，再 fallback 到 `CHILD_AI_MIMO_TTS_API_KEY`；ASR 默认模型是 `mimo-v2.5`，不是文本对话的 `mimo-v2.5-pro`。
Rationale: ASR 是 MiMo chat completions 的 audio input 能力，不需要因单独 ASR key 为空而阻塞真实语音识别测试；但 ASR 与文本对话模型名不同，必须防止把 `mimo-v2.5-pro` 套到 ASR。
Affected modules: backend config、AsrService、MiMo ASR provider、smoke script、QA artifact readiness gate、docs。
Implementation notes: 交付语音输入测试包前必须用真实 smoke 或日志确认 `provider=mimo`、`model=mimo-v2.5`；如果仍是 `provider=mock`，不得让父亲按真实 ASR 测试。
Docs updated: `docs/PRODUCT_DECISIONS_V0_1.md`、`docs/CODEX_WORKFLOW_V0_1.md`、`docs/MIMO_ASR_INTEGRATION_DESIGN_V0_1.md`、`backend/README.md`。
Tests or QA needed: 单元测试覆盖 ASR key fallback 和默认模型；smoke 脚本输出 provider/model，不输出 key、base64 或 transcript。

#### PD-038

Decision ID: PD-038
Date: 2026-05-22
Status: confirmed
Source: father / MiMo vision smoke correction
Decision: 普通文字对话调用 MiMo `mimo-v2.5-pro`；带图片的 conversation attachment / vision / OCR 链路调用 MiMo `mimo-v2.5`，不使用 `mimo-v2.5-pro` 做图片理解。
Rationale: MiMo 官方图像理解文档只列出 `mimo-v2.5` / `mimo-v2-omni` 支持 image understanding。实测 `mimo-v2.5-pro` 会返回 `No endpoints found that support image input`；切到 `mimo-v2.5` 并使用 `max_completion_tokens` 后，fake/test image smoke 返回 `provider=mimo`、`model=mimo-v2.5`。
Affected modules: ModelRegistry、OpenAICompatibleProvider、AttachmentService vision path、vision smoke script、backend docs、QA gate。
Implementation notes: `mimo_child_chat` 继续使用 `CHILD_AI_MIMO_MODEL=mimo-v2.5-pro`；`mimo_vision` / `mimo_ocr` 使用 `CHILD_AI_MIMO_VISION_MODEL=mimo-v2.5`。Provider 必须优先使用 selected profile 的 model，不能让全局文本模型覆盖 vision profile。真实 smoke 仍只使用 fake/test image，不使用真实儿童或家庭图片。
Docs updated: `docs/PRODUCT_DECISIONS_V0_1.md`、`docs/VISION_MODEL_SMOKE_V0_1.md`、`docs/RELEASE_SMOKE_V0_1.md`、`backend/README.md`。
Tests or QA needed: smoke 脚本输出 `provider=mimo` / `model=mimo-v2.5`，不输出 API key、image base64 或完整图片描述；后续 CameraX 仍需单独设计。

#### PD-039

Decision ID: PD-039
Date: 2026-05-22
Status: confirmed
Source: father / image sharing QA feedback
Decision: “拍给小白狐看”默认是普通图片分享；不要用图片描述里的地址、电话、学校名等关键词自动路由到 `privacy.boundary`。隐私边界只由明确隐私意图或后续安全策略触发。
Rationale: 真机图片 QA 发现 MiMo vision 会输出“可能有隐私”或包含否定式隐私描述，关键词二次判定会把普通图片误路由到隐私边界，并导致模板化回复。
Affected modules: AttachmentService、MockOCRProvider、ModalityManager、PromptManager、Android pending image context、QA。
Implementation notes: 后端不再根据 image description 关键词二次标记 `privacy_sensitive`；普通图片即使描述像作业题，也保留 image context 并继续 `conversation.open`，只有孩子明确把它当作作业题时才进入学习引导。图片上下文必须传入 prompt，避免模型回复“看不到图片”。
Docs updated: `docs/PRODUCT_DECISIONS_V0_1.md`。
Tests or QA needed: 普通照片不误进 privacy.boundary；普通照片不强行问“这道题”；后续对话能围绕刚才那张图回答；明确隐私图片仍可由显式 purpose 进入 privacy.boundary。

#### PD-040

Decision ID: PD-040
Date: 2026-05-22
Status: revised
Source: father / parent report QA feedback
Decision: 父亲日报在父亲点开时应结合当天已落库会话消息、路由摘要和结构化 memory，由 `ModelTaskType.PARENT_REPORT` 大模型总结生成；当天有新会话素材时刷新已有日报，但仍不展示逐字聊天记录。
Rationale: 只基于 memory 的日报会漏掉当天真实互动，父亲点开日报时需要看到有用的总结分析，而不是空摘要或过早生成的旧摘要。
Affected modules: ParentReportService、ModelRegistry、ConversationPersistenceRepository、parent_reports、Android ParentReportScreen。
Implementation notes: 程序只读取当天会话、routing/scene/risk 受控信号和 parent-visible memories，构造最小 evidence packet；模型输出必须是结构化 JSON。程序不按规则拼正式日报正文、学习观察、表达观察、情绪观察或父亲建议；provider fail / policy block / 空输出 / JSON 不可解析时返回 `generation_status=model_failed|model_blocked`，父亲端显示稍后重试，不用 deterministic fallback 冒充成功。
Docs updated: `docs/PRODUCT_DECISIONS_V0_1.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`backend/README.md`。
Tests or QA needed: 当天 conversation message 可进入日报摘要；新会话晚于已生成 report 时重新生成；report JSON 不含逐字聊天、evidence、quote_summary、prompt 或 debug。

#### PD-041

Decision ID: PD-041
Date: 2026-05-22
Status: confirmed
Source: father / image and parent-report QA feedback
Decision: 图片上传后的儿童端确认语必须短，不向孩子回显完整 vision/OCR 描述；父亲日报由大模型基于当天会话受控素材生成，规则摘要仅可作为开发 fallback 或内部 evidence hints，不能作为正式成功日报展示。
Rationale: 真机 QA 发现图片识别内容直接展示给孩子会过长、包含不适合儿童端看到的分析细节，并且可能导致单次 TTS 失败；父亲日报如果只按规则分类，会空泛，不能表达孩子当天真实状态。
Affected modules: AttachmentService、ModalityManager、PromptManager、ChatViewModel attachment TTS、ParentReportService、ModelRegistry。
Implementation notes: 普通图片确认语只说“我看到这张图啦...”并保留 attachment context 给后续 `/conversation/stream`；后续围绕图片聊天仍走分句 `text_delta` / `tts_started` / `audio_ready`。ParentReportService 将当天 memory 和 conversation snippets 作为受控素材提交 `PARENT_REPORT` 模型任务，模型输出必须是结构化 JSON；不输出逐字聊天、完整图片描述、prompt/debug/provider raw response。
Docs updated: `docs/PRODUCT_DECISIONS_V0_1.md`。
Tests or QA needed: 图片上传确认语短且可朗读；后续图片聊天不再说“看不到”；父亲日报能基于当天新对话由模型生成具体状态分析，模型失败时父亲端显示可重试状态；Redmi K60 / Honor Pad 5 仍需真机复测。

#### PD-042

Decision ID: PD-042
Date: 2026-05-22
Status: confirmed
Source: father / voice input QA feedback
Decision: 语音输入后续目标应从“录完整短音频后一次性 ASR”升级为流式语音输入体验，参考主流聊天 App 的电话/实时交流模式；长时间说话时应边录、边识别、边展示中间结果，并在停止或确认后发送最终文本。
Rationale: 儿童按下语音后可能持续说很久，单次录音上传会等待过长，也更容易在 ASR timeout / needs_retry 时丢失体验。
Affected modules: Android SpeechInputController / AudioRecorder、backend ASR router、MiMo ASR provider、voice QA docs。
Implementation notes: 本轮先记录产品方向，不在当前修复里强行实现；下一轮需要确认 MiMo 是否支持 streaming audio input。如果 MiMo 不支持 true streaming ASR，先做 chunked pseudo-streaming：Android 分片上传，后端按片段返回 partial transcript，最终 stop 时合并并走儿童端自动发送。仍不做常开麦克风，不直接把 partial transcript 发给大模型，不保存原始音频。
Docs updated: `docs/PRODUCT_DECISIONS_V0_1.md`。
Tests or QA needed: 设计并验证长语音输入、取消、停止、partial transcript、最终 transcript、needs_retry 和网络失败 fallback。

#### PD-043

Decision ID: PD-043
Date: 2026-05-22
Status: confirmed
Source: father / child voice conversation QA feedback
Decision: child_chat prompt 必须显式理解儿童语音里的操作旁白、夸张表达、ASR 误听、话题换轨和睡前收尾；“跑完要死了/累死了”这类运动语境表达按 watch-lite 疲惫/身体感受处理，不直接等同自伤；父亲日报 topic 抽取不得把运动比赛误报为学习求助。
Rationale: 真机语音测试中，孩子会夹杂“按一下、说完再按一下”等旁人/按钮提示，也会说“每天跑十五公里”“跑完感觉要死了”“换个话题”“明天再聊我得睡觉了”。小白狐需要按儿童语音语境接住，而不是成人式事实化、医学化或持续追问。
Affected modules: global system prompt、conversation.open scene prompt、PromptManager runtime turn_guidance、ChildAgentRuntime、SafetyEngine、IntentClassifier、ParentReportService、prompt QA tests。
Implementation notes: 新增 `turn_guidance` runtime section，覆盖 operation aside、child exaggeration、topic change、bedtime close、body_discomfort_watch_lite 和 same_topic_too_long。SafetyEngine 保留明确 self-harm critical 规则，但对运动语境夸张疲惫降为 LOW watch-lite；IntentClassifier 将该类信号作为 emotion_expression/body_discomfort_watch_lite。父亲日报将比赛、运动、跑步、跑完和十五公里识别为运动主线，并记录换话题边界。
Docs updated: `docs/PRODUCT_DECISIONS_V0_1.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`docs/PROMPT_CHILD_SPEECH_GUIDANCE_V0_1.md`。
Tests or QA needed: 回归测试覆盖真实运动比赛语音序列、换题、睡前收尾、自伤 critical 保留、医学 watch 保留和父亲日报 topic 抽取；Redmi K60 / Honor Pad 5 仍需真机复验回复自然度。

#### PD-044

Decision ID: PD-044
Date: 2026-05-23
Status: confirmed
Source: father / `HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md`
Decision: 下一阶段产品优化以 Healthy Engagement 为总指导：目标使用“健康依恋 / 主动回访 / 成长陪伴习惯”，避免把“不健康依赖”作为产品目标；长期吸引力来自被理解感、掌控感、能力感、期待感和现实生活迁移。
Rationale: 家庭内测前已经跑通 voice-first、TTS、ASR、vision、stream、DB、prompt guidance 和父亲日报的基础闭环；下一阶段必须防止为了留存而引入成瘾式机制或排他关系。
Affected modules: global/output prompts、QuickActionService、SafetyEngine output safety、ParentReportService、future relationship memory、opening v2、Android QA。
Implementation notes: 禁止签到压力、断签惩罚、排行榜、抽卡、FOMO、限时错过、情感勒索、秘密关系和排他依恋；儿童端应持续提供继续说、换个话题、讲个小故事、今天不聊了等掌控动作；输出应尊重停止、换题和睡前收尾，并尽量连接回父母、老师、同伴、作品、运动、学习小步骤或睡眠。本轮已先落地输出契约、quick actions 和输出安全拦截的最小快改。
Docs updated: `docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md`、`docs/PRODUCT_DECISIONS_V0_1.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`。
Tests or QA needed: prompt contract、quick actions、retention-pressure output safety 已有后端测试；Redmi K60 / Honor Pad 5 仍需确认实际回复和快捷动作是否低压力、可收束。

#### PD-045

Decision ID: PD-045
Date: 2026-05-23
Status: confirmed
Source: E1 Relationship Memory / Interest Seed implementation
Decision: 小白狐可以从自然对话中提取低敏、短期可回访的关系记忆：`interest_seed`、`topic_boundary`、`proud_moment`。这些记忆只保存结构化摘要和 metadata，不保存完整儿童原话、raw chat、full transcript、原始音频或原始图片。
Rationale: Healthy Engagement 的“被理解感、掌控感、能力感和现实生活迁移”需要小白狐记得孩子在意的低敏兴趣、尊重孩子表达的边界，并把表达上的小进步转化为低压力成长反馈和父亲现实接话建议。
Affected modules: ConversationMemoryHooks、MemoryService、OpeningService、ParentReportService、memory tests、opening/report tests。
Implementation notes: E1 复用现有 `MemoryType.INTEREST` / `STRATEGY` / `EXPRESSION_PATTERN`，通过 `MemoryEvidence.metadata.relationship_memory_type` 表达具体类型；规则型 extractor 过滤操作旁白、旁人提示、疑似 ASR 碎片、隐私、高风险安全和严重医疗信息。E1.1 加固后，单独“比赛”不会生成跑步比赛 seed，创作动作优先于动物内容词，active interest_seed 按 child/topic 跨 session 去重，Opening 只回访最新 low-sensitivity interest seed，且 model opening prompt 明确禁止留存压力和排他关系话术。Memory hook 写入为 best-effort，失败不阻塞儿童回复。父亲日报把 relationship memory 转成 starter + avoid 风格的现实接话建议。
Docs updated: `docs/PRODUCT_DECISIONS_V0_1.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`backend/README.md`。
Tests or QA needed: 后端测试覆盖跑步比赛/画画/故事兴趣、换话题/睡前边界、proud_moment、过滤 raw/full transcript、Opening 有/无 seed 和睡前分支、父亲日报低压力接话建议；Redmi K60 / Honor Pad 5 仍需真机观察回复自然度和是否过度回访。

#### PD-046

Decision ID: PD-046
Date: 2026-05-23
Status: confirmed
Source: E2-A Opening Greeting v2 policy foundation
Decision: Opening Greeting v2 使用后端 policy engine，而不是只靠 prompt 或“有 seed 就回访”。Opening 必须是轻邀请、可退出、尊重边界、睡前收束，并把父亲目标转译为低压力提示。
Rationale: Healthy Engagement 要让小白狐像温柔的门口，而不是钩子。孩子可以说、可以不说、可以换话题，也可以去找爸爸妈妈；opening 不应制造留存压力、排他关系或睡前兴奋。
Affected modules: OpeningPolicyBuilder、OpeningService、relationship memory helpers、opening tests、backend docs。
Implementation notes: `OpeningPolicyBuilder` 输出 `OpeningPolicy`，包含 `opening_mode`、age band、max chars、interest recall allowed/reason、topic boundary cooldown、bedtime defer、parent bridge、parent goal hint、forbidden phrases 和 prompt rules。MVP-CLOSEOUT-1 后 `OpeningService` 默认使用 deterministic policy template；model prompt 仍共用同一 policy，但只作为 dev/test 实验路径。memory read failure 不阻塞 opening；同 session cache 与 TTS fallback 保持不变。本轮不改 Android、不改 DB schema、不做 push notification、不做 Growing Nest 或 CameraX。
Docs updated: `docs/OPENING_GREETING_V2_POLICY_V0_1.md`、`docs/PRODUCT_DECISIONS_V0_1.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`docs/HEALTHY_ENGAGEMENT_MASTER_DESIGN_V0_1.md`、`backend/README.md`。
Tests or QA needed: 后端测试覆盖 interest callback、default light、boundary respect、bedtime closure/defer、no-school policy、father learning goal translation、age limits、memory failure fallback、model prompt contract、TTS failure 和 session cache；Redmi K60 / Honor Pad 5 真机 QA 仍未完成。

#### PD-047

Decision ID: PD-047
Date: 2026-05-23
Status: confirmed
Source: DEV-TRACE-1 local prompt analysis request
Decision: 当前本地测试阶段允许通过 opt-in 临时表 `model_debug_traces` 记录完整模型 prompt、messages、input_text、context、metadata、模型回复和 structured output，用于 prompt/体验分析。
Rationale: 家庭测试和专家 prompt 优化需要看到实际 `ModelRegistry.generate()` 发送给模型的完整上下文，以及模型返回内容和 fallback/policy/error 状态。集中在 ModelRegistry 层记录能覆盖 child_chat、opening、parent_report、vision/OCR 等任务，避免各业务服务分散补日志。
Affected modules: ModelRegistry、ModelDebugTraceService、ModelDebugTraceRepository、`model_debug_traces` migration、backend docs、prompt QA。
Implementation notes: 默认 `CHILD_AI_MODEL_DEBUG_TRACE_ENABLED=false`；本地 dev/test 显式开启后记录完整文本 prompt 和 response，但过滤 API key、Authorization/Bearer、`.env`、raw image/audio、base64 media 和 provider raw HTTP headers。trace 写入失败只 warning，不阻塞模型调用；新增清空脚本；该能力不代表生产儿童数据策略。
Docs updated: `docs/MODEL_DEBUG_TRACE_V0_1.md`、`docs/PRODUCT_DECISIONS_V0_1.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`backend/README.md`。
Tests or QA needed: 后端测试覆盖 disabled/enabled、opening prompt、parent report prompt、provider fallback、policy blocked、trace failure best-effort、secret/base64 sanitization、migration 可读和 clear。

#### PD-048

Decision ID: PD-048
Date: 2026-05-23
Status: confirmed
Source: father / local ASR direction confirmation
Decision: ASR v1 真实识别第一选择改为 sherpa-onnx + SenseVoice-Small int8 本地推理；本地异常后再走原有 MiMo ASR fallback。当前测试阶段应显式启用 local_sensevoice；缺本地模型或依赖时标记 BLOCKED，不把非真实链路写成通过。
Rationale: 实际测试中每轮语音上传到当前大模型端做识别耗时较高，影响儿童端体验。本机调研显示 SenseVoice-Small int8 在 Mac mini M2 / 8GB 上可轻量运行，公开中文样例识别速度明显优于云端大模型识别链路。
Affected modules: backend ASR provider、AsrService fallback、AsrDataPolicyGuard、backend config、ASR docs、QA。
Implementation notes: 新增 `local_sensevoice` provider，依赖 `sherpa-onnx` + `numpy`，模型文件放在 `backend/models/asr/sensevoice/` 且不提交 git。`CHILD_AI_ASR_PROVIDER=local_sensevoice` 且 `CHILD_AI_LOCAL_SENSEVOICE_ENABLED=true` 时启用本地识别；`CHILD_AI_ASR_FALLBACK_PROVIDER=mimo` 时本地异常后进入 MiMo fallback，但 MiMo 仍必须满足父亲授权、API key、child audio allowed、retention checked 和 no-training confirmed。原始音频不入库、不进日志、不进长期 memory。
Docs updated: `docs/PRODUCT_DECISIONS_V0_1.md`、`docs/LOCAL_ASR_SENSEVOICE_DESIGN_V0_1.md`、`docs/ASR_INPUT_RESEARCH_V0_1.md`、`docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`backend/README.md`。
Tests or QA needed: 后端测试覆盖 provider 选择、本地 policy allow、本地异常 fallback 和旧 MiMo/mock 路径；真机 QA 需记录 SenseVoice 对儿童中文、噪声、远场平板麦克风的准确率和 tap-to-transcript 延迟。

#### PD-049

Decision ID: PD-049
Date: 2026-05-23
Status: revised
Source: MVP-CLOSEOUT-1 / real MiMo trace quality closeout
Decision: 家庭 MVP 前 `opening greeting` 默认走 deterministic policy/template 主路径；父亲日报在 PD-052 中已修订为 model-first，本决策不再约束父亲日报。
Rationale: DEV-TRACE-3 与 PROMPT-REAL-HARDEN-1 的真实 MiMo synthetic trace 显示 `child_chat` 质量可通过 prompt/output safety 加固继续观察；opening 继续使用确定性 policy/template 保证儿童端稳定。父亲日报的产品要求已变为大模型总结，因此从 deterministic-default 决策中移出。
Affected modules: OpeningService、OpeningPolicyBuilder、backend docs、opening tests。
Implementation notes: `OpeningService.create_opening()` 默认使用 `OpeningPolicyBuilder` + deterministic templates，保留 TTS 和 session cache，不再默认调用 `ModelRegistry.generate()`。父亲日报已从该 deterministic-default 规则中移除。
Docs updated: `docs/MODEL_TRACE_REAL_PROVIDER_REVIEW_V0_1.md`、`docs/OPENING_GREETING_V2_POLICY_V0_1.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`backend/README.md`。
Tests or QA needed: 后端测试覆盖 opening 默认不调用 model、deterministic templates、trace runner 不把 opening deterministic no-trace 标为 P1；Redmi K60 / Honor Pad 5 真机 QA 仍未完成。

#### PD-052

Decision ID: PD-052
Date: 2026-05-24
Status: confirmed
Source: father / parent report v2 product revision
Decision: 父亲日报 v2 必须 model-first。正式日报正文、学习观察、表达观察、情绪观察、安全提醒和父亲建议来自 `ModelTaskType.PARENT_REPORT` 的结构化模型输出；程序只负责构造当天受控 evidence packet、校验 schema、持久化模型日报和刷新 stale report。
Rationale: 父亲日报需要基于当天真实对话总结孩子状态和建议，规则拼接会空泛，且会把 deterministic fallback 误当成正式成功。模型不可用时应明确失败/可重试，而不是展示一份程序拼出来的“成功日报”。
Affected modules: ParentReportService、ModelRegistry、ParentReportRepository、ParentReportScreen、docs/tests。
Implementation notes: `ParentReportService` 读取当天 `conversation_messages`、routing/active_scene/risk 受控信号和 parent-visible memories，构造不含 provider raw、debug trace、prompt、secret、base64 或原始媒体的 evidence packet。合法模型 JSON 才保存为 `generation_status=model_generated`；policy blocked、provider fail、空输出或 JSON 不可解析返回 `model_blocked/model_failed`，Android 父亲端显示“日报暂时生成失败，请稍后重试”，不展示 deterministic fallback 正文。Opening 仍保持 deterministic default。
Docs updated: `docs/PRODUCT_DECISIONS_V0_1.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`backend/README.md`、`android/README.md`。
Tests or QA needed: 后端测试覆盖 model-first 调用、模型合法 JSON 成功、失败不冒充成功、payload 脱敏和 stale refresh；Android 需确认失败状态展示。Redmi K60 / Honor Pad 5 真机 QA 仍未完成。

#### PD-053

Decision ID: PD-053
Date: 2026-05-24
Status: confirmed
Source: father / Redmi K60 device QA feedback
Decision: 图片上下文、stream TTS 和 opening 首屏响应需要以真机体验为准加固：有真实 `attachment_id` / `image_context` 时，小白狐不得说自己没有看图功能或看不到图片；stream segment 的 MiMo 远程音频失败时不再用 Android 系统 TTS 混播同一轮；opening greeting 首屏默认先返回 deterministic 文本，不同步等待远程 TTS。
Rationale: 真机 QA 显示图片已上传并进入 conversation 后，小白狐仍说看不到；一轮回复中 MiMo VoiceClone 与系统 TTS fallback 混播会破坏角色一致性；opening 等待 TTS 冷启动会让首屏开场白出现太慢。
Affected modules: PromptManager image context section、ChildAgentRuntime output repair、TextSegmenter stream chunks、OpeningService、Android ChatViewModel、docs/tests。
Implementation notes: Prompt 明确“已获得后端图片理解结果”；ChildAgentRuntime 对有图片上下文的拒看回复做安全兜底修复；TextSegmenter 按 preferred max 拆长句，减少单段 TTS 超时；Android stream `error(stage=tts)` 只提示文字错误，不把失败段交给系统 TTS 读；OpeningService 不再同步调用 TTS。
Tests or QA needed: 后端回归覆盖图片拒看修复、拍照意图引导、长句分段和 opening 不调用 TTS；Android 回归覆盖 stream TTS error 不触发系统 TTS。Redmi K60 / Honor Pad 5 需复测 opening 速度、图片续聊和音色一致性。

#### PD-054

Decision ID: PD-054
Date: 2026-05-24
Status: confirmed
Source: father / device QA packaging correction
Decision: 当前阶段不再维护模拟器包作为默认测试产物；Android 默认构建和交付 APK 必须使用 Mac LAN base URL，面向 Redmi K60 / Honor Pad 5 真机测试。非真机路径不得作为父亲验收包，也不得再用来解释或替代真实设备 QA。
Rationale: 真机测试中 opening 无响应的直接原因是 APK 使用了非真机可达的后端地址，导致请求没有到达当前后端。当前产品重点已经是真实 ASR、真实拍照、真实后端和真实 provider 路径，继续保留默认非真机包会制造混淆。
Affected modules: Android Gradle default base URL、device APK build/install scripts、README、QA docs、shared context。
Implementation notes: `android/app/build.gradle.kts` 默认 `CONVERSATION_API_BASE_URL` 改为当前 Mac LAN 地址；删除本机模拟器启动脚本；安装脚本改为真机构建脚本；文档清除旧地址和默认模拟器包路径。
Tests or QA needed: 每次交付 APK 前运行真机构建脚本并记录 base URL、APK size 和 sha256；Redmi K60 / Honor Pad 5 真机 QA 仍需执行。

#### PD-051

Decision ID: PD-051
Date: 2026-05-23
Status: confirmed
Source: father / VISION-REAL-1
Decision: 当前测试阶段，“拍给小白狐看”必须走 Android 系统相机或系统相册真实图片上传 + 后端 MiMo vision/multimodal。CameraX 自定义相机后置；mock attachment 只允许作为单元测试替身或外部条件缺失时的异常 fallback，不作为儿童端默认路径。
Rationale: 用户当前重点是验证实际产品能力，不接受默认 mock/占位路径被写成可测功能。图片分享必须让小白狐真实看到图片；失败时应明确 BLOCKED/FAIL，而不是假装看到了。
Affected modules: Android `InputBar` / system camera launcher / attachment API client, backend attachment upload API, AttachmentService, ModelRegistry vision routing, docs and QA.
Implementation notes: Android 使用 `ActivityResultContracts.TakePicture` + `FileProvider` 或系统相册选择，压缩为 JPEG bytes 后 multipart 上传 `POST /api/v1/attachments/images`；后端短期保存图片测试文件并调用 `mimo_vision`。普通纯文字 child_chat 继续使用 `mimo-v2.5-pro`；图片/识图/OCR/multimodal 使用 `mimo-v2.5`。Opening 继续 deterministic default；ParentReport 按 PD-052 改为 model-first。Android 不保存 MiMo key。
Docs updated: `docs/VISION_REAL_PATH_V0_1.md`、`docs/PRODUCT_DECISIONS_V0_1.md`、`docs/CODEX_PROGRESS_BOARD_V0_1.md`、`backend/README.md`、`android/README.md`。
Tests or QA needed: 后端测试覆盖 multipart、MIME 拒绝、mock vision 不能当 real pass、policy blocked；Android unit/compile 覆盖 quick action 不进 mock 默认路径。Redmi K60 / Honor Pad 5 仍需真机验证系统相机、相册、上传、MiMo vision 和失败提示。

---

## 3. Current Product Direction

v0.1 第一轮后端和 Android MVP 已完成，当前重点不是扩展开放式聊天，而是进入家庭内测前加固和下一阶段体验设计：

```text
1. 先完成完整设备 QA，确认现有文字聊天、学习引导、系统相机真实图片上传/识图、父亲治理和安全场景在平板上可用。
2. 语音输入 v1：后端本地 ASR 优先，第一选择是 sherpa-onnx + SenseVoice-Small int8；本地异常后 fallback 到原有 MiMo ASR。Android 负责录音上传和儿童端语音状态；儿童默认自动发送非空 transcript，确认面板仅用于 DevSettings / 父亲调试模式；仍不做常开麦克风或自动连续监听。
3. 小白狐正式语音输出改为后端 MiMo VoiceClone 生成 `audio_url`，Android 优先播放远端音频；系统 TextToSpeech 保留为 fallback 和诊断能力。
4. 语音实现必须先抽象为 VoiceEngine / SpeechInputController / TtsController，并让 remote audio、系统 TTS 和文字 fallback 都走统一生命周期。
5. 小白狐音色方向是小孩子般干净、清脆、中性、活泼可爱，但不能过度尖锐或幼稚；已通过 MiMo Studio VoiceDesign 筛选出 v01 样本。
6. 小白狐视觉目标进一步确认是 3D 卡通、柔和立体、有毛绒感、儿童动画质感，角色可以活泼开朗并有说话、倾听、蹦跳等状态，但不做上瘾式奖励反馈。
7. Android 第一版优先接预渲染 3D PNG/WebP 状态图和 animation_v1 WebP 序列帧，不引入实时 3D 引擎作为必需能力。
8. 采用双设备测试策略：高配 Android 手机先跑通功能闭环，Honor Pad 5 Android 9 / 4GB 做低配兼容、大屏、性能和降级验证。
9. 当前小白狐 v1 候选静态资产和 animation_v1 动态资源都覆盖 11 个状态：idle/neutral_idle、listening、speaking、jumping_happy、thinking、calm、sleepy、safety_concern、privacy_boundary、homework_focus、network_error；Android 保留 animation_v1 -> png_static -> canvas fallback。
10. Redmi K60 / Android 14 真机反馈表明系统 TTS 不适合作为正式音色方案；后端 VoiceClone 成为主路径，系统 TTS 仅作为 fallback。
11. 下一版普通聊天方向是 Open Conversation Mode：更自由地使用最近多轮上下文，但不放松安全、隐私、学习和睡前边界。
12. 本地持久化方向改为 PostgreSQL：先做家庭自用本地库和最小可用表，再逐步迁移父亲策略、会话消息、结构化记忆和日报；如果未来云端化或上架，必须重新做儿童数据合规评审。
13. 下一阶段体验重点转向流式交互、横屏双栏、小白狐状态覆盖验证、本地 SenseVoice ASR 真机准确率/延迟 QA、儿童端 voice-first 自动发送、opening greeting 和运行基础组件补齐。
14. 所有新增体验继续遵守儿童安全底线和数据最小化原则。
```

---

## 4. Open Items For Later Confirmation

| ID | 状态 | 待确认问题 | 当前默认 |
|---|---|---|---|
| PO-001 | confirmed | 真实平板家庭内测前是否需要持久化父亲 policy、日报素材和结构化记忆。 | 已确认进入 PostgreSQL 本地库分阶段落地；DB1-A 基础设施已完成，业务迁移按 B2-B5 串行。 |
| PO-002 | confirmed | 是否需要后端音频上传或云端 ASR。 | 已确认 ASR v1 接 MiMo；默认仍 policy-blocked，真实儿童音频外发必须由父亲授权和 ASR policy flags 控制。 |
| PO-003 | proposed | 小白狐视觉资源数量、文件格式、制作方式和版权来源。 | 视觉方向已确认优先 3D / soft 3D / 毛绒感 / 立体绘本感；具体资源由视觉 brief / F1 会话继续设计。 |
| PO-004 | confirmed | 小白狐专属音色是否需要采购、训练或接入第三方音色。 | 已确认使用 MiMo VoiceClone v01；真实 VoiceClone API schema 已通过 smoke 验证，下一步确认 Android remote audio 播放和设备侧听感。 |
| PO-005 | proposed | Open Conversation Mode 的 history 窗口大小、摘要策略和 quick action 生成方式。 | 下一轮先做设计和小步后端实现，安全、隐私、学习、睡前边界不可放松。 |
