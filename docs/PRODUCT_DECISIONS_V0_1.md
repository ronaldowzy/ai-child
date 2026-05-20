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
| PD-002 | revised | 语音输入第一阶段仍优先 Android 本地 `SpeechRecognizer`，不默认上传原始音频到后端；TTS 正式音色路径已由 PD-027 修订为后端 MiMo VoiceClone。 | Android 权限、语音设计、后端 API 边界、TTS |
| PD-003 | confirmed | 语音输入应先转文字确认，再发送给后端；不要误识别后自动直接进入 AI 回复。 | Android UX、儿童安全、QA |
| PD-004 | confirmed | 小白狐形象应温和、好奇、慢热友好，避免强刺激、排行榜、连击奖励或上瘾式动画。 | 视觉 brief、动画状态、Android UI |
| PD-005 | confirmed | 后端继续通过 `reply.voice_enabled`、`reply.audio_url`、`reply.emotion`、`reply.agent_motion` 向 Android 暴露表现层信号。 | 后端 API、Android DTO、TTS/动画 |
| PD-006 | confirmed | 小白狐表现层不得制造“唯一朋友”“只有我懂你”等依赖感。 | Prompt、安全检查、视觉与动效文案 |
| PD-007 | confirmed | 所有新体验仍必须遵守：不直接给作业最终答案，不要求保密，不鼓励隐瞒父母，不保存原始音频/照片到长期记忆。 | 全端、安全、记忆、QA |
| PD-008 | confirmed | 每次父亲确认的新产品想法，必须先写入 `docs/PRODUCT_DECISIONS_V0_1.md`，再进入子会话实现。 | 协作流程、AGENTS、README |
| PD-009 | confirmed | 正式名称为“小白狐”；UI、产品、设计和测试说明优先统一。代码 class 名 `FoxAgent` 暂可保留，后续如要改代码命名单独 refactor。 | Android UI、README、设计文档、QA 文案、后续代码重命名计划 |
| PD-010 | confirmed | 语音输入 v1 是 confirm-before-send：点击语音 -> 孩子说话 -> Android 本地 ASR -> 展示识别文本 -> 孩子确认/可编辑 -> 点击发送 -> text 走 `/conversation/message`。future hands-free conversational mode 不进入 v1。 | Android 语音输入、QA、后端 API 边界 |
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
Decision: 语音输入第一阶段仍优先 Android 本地 `SpeechRecognizer`，不默认上传原始音频到后端；TTS 正式音色路径已由 PD-027 修订为后端 MiMo VoiceClone。
Rationale: 本地 ASR 能更快形成可控输入闭环，同时降低儿童原始音频外发和留存风险；系统 TTS 在 Redmi K60 上不可用或体验不理想，因此不再作为正式小白狐音色方案。
Affected modules: Android voice、Android permissions、backend API boundary、privacy policy、QA。
Implementation notes: Android 只把确认后的文本发给 `/api/v1/conversation/message`；后端不新增孩子原始音频上传接口；语音输出通过后端 TTS endpoint 和 Android remote audio playback 迭代。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`android/README.md`、`backend/README.md`。
Tests or QA needed: 权限、识别、失败 fallback、无音频文件保存检查。

#### PD-003

Decision ID: PD-003
Date: 2026-05-19
Status: confirmed
Source: father / product planning
Decision: 语音输入应先转文字确认，再发送给后端；不要误识别后自动直接进入 AI 回复。
Rationale: 儿童语音容易误识别，确认/编辑步骤能避免错误内容直接触发模型回复或安全流程。
Affected modules: Android InputBar、ChatViewModel、voice UI state、QA。
Implementation notes: 语音识别结果进入待确认状态，孩子可编辑、重说、取消或发送。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`android/README.md`。
Tests or QA needed: confirm-before-send、编辑后发送、取消不调用后端。

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
Status: confirmed
Source: father / voice interaction decision
Decision: 语音输入 v1 是 confirm-before-send：点击语音 -> 孩子说话 -> Android 本地 ASR -> 展示识别文本 -> 孩子确认/可编辑 -> 点击发送 -> text 走 `/conversation/message`。future hands-free conversational mode 不进入 v1。
Rationale: 第一版优先可控和可纠错；连续自动对话需要更完整的误识别、安全、打断和收尾设计。
Affected modules: Android voice、InputBar、ChatViewModel、conversation API usage、QA。
Implementation notes: v1 不做自动发送、常开麦克风或唤醒词。
Docs updated: `docs/VOICE_INTERACTION_DESIGN_V0_1.md`、`docs/NEXT_PHASE_PLAN_V0_2.md`、`android/README.md`。
Tests or QA needed: 识别后不自动调用后端、编辑确认、取消路径。

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
Implementation notes: Android 资源命名使用 `fox_3d_<state>.png`；低配设备仍可强制 Canvas 或静态降级。
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
Implementation notes: 音色样本归档为 `backend/assets/voices/xiaobaohu_voice_v01.wav`，sha256=`8eec0f98629350a1dd09bd98a31c2bee80132128bf214d4c0a009331c9a66c40`；默认 TTS provider 仍为 mock，MiMo VoiceClone 必须通过独立 TTS env 和 policy guard；真实 VoiceClone smoke 已确认当前 provider 走 `/chat/completions`，返回音频从 `choices[0].message.audio.data` 读取；Android 不直接调用 MiMo，不存 API key；生成音频缓存不提交 git。
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

---

## 3. Current Product Direction

v0.1 第一轮后端和 Android MVP 已完成，当前重点不是扩展开放式聊天，而是进入家庭内测前加固和下一阶段体验设计：

```text
1. 先完成完整设备 QA，确认现有文字聊天、学习引导、mock 拍题、父亲治理和安全场景在平板上可用。
2. 再进入语音输入 v1：Android 本地 ASR，先给孩子和父亲可见的文字确认，不自动发送误识别内容；hands-free conversational mode 留到未来阶段。
3. 小白狐正式语音输出改为后端 MiMo VoiceClone 生成 `audio_url`，Android 优先播放远端音频；系统 TextToSpeech 保留为 fallback 和诊断能力。
4. 语音实现必须先抽象为 VoiceEngine / SpeechInputController / TtsController，并让 remote audio、系统 TTS 和文字 fallback 都走统一生命周期。
5. 小白狐音色方向是小孩子般干净、清脆、中性、活泼可爱，但不能过度尖锐或幼稚；已通过 MiMo Studio VoiceDesign 筛选出 v01 样本。
6. 小白狐视觉目标进一步确认是 3D 卡通、柔和立体、有毛绒感、儿童动画质感，角色可以活泼开朗并有说话、倾听、蹦跳等状态，但不做上瘾式奖励反馈。
7. Android 第一版优先接预渲染 3D PNG/WebP 状态图 + 轻量 Compose 动画，不引入实时 3D 引擎作为必需能力。
8. 采用双设备测试策略：高配 Android 手机先跑通功能闭环，Honor Pad 5 Android 9 / 4GB 做低配兼容、大屏、性能和降级验证。
9. 当前小白狐 v1 候选资产已扩展到 11 个状态：neutral_idle、listening、speaking、jumping_happy、thinking、calm、sleepy、safety_concern、privacy_boundary、homework_focus、network_error。
10. Redmi K60 / Android 14 真机反馈表明系统 TTS 不适合作为正式音色方案；后端 VoiceClone 成为主路径，系统 TTS 仅作为 fallback。
11. 下一版普通聊天方向是 Open Conversation Mode：更自由地使用最近多轮上下文，但不放松安全、隐私、学习和睡前边界。
12. 本地持久化方向改为 PostgreSQL：先做家庭自用本地库和最小可用表，再逐步迁移父亲策略、会话消息、结构化记忆和日报；如果未来云端化或上架，必须重新做儿童数据合规评审。
13. 所有新增体验继续遵守儿童安全底线和数据最小化原则。
```

---

## 4. Open Items For Later Confirmation

| ID | 状态 | 待确认问题 | 当前默认 |
|---|---|---|---|
| PO-001 | confirmed | 真实平板家庭内测前是否需要持久化父亲 policy、日报素材和结构化记忆。 | 已确认进入 PostgreSQL 本地库分阶段落地；DB1-A 基础设施已完成，业务迁移按 B2-B5 串行。 |
| PO-002 | proposed | 是否需要后端音频上传或云端 ASR。 | v0.2 之前默认不需要；如启用必须单独做儿童数据和 retention review。 |
| PO-003 | proposed | 小白狐视觉资源数量、文件格式、制作方式和版权来源。 | 视觉方向已确认优先 3D / soft 3D / 毛绒感 / 立体绘本感；具体资源由视觉 brief / F1 会话继续设计。 |
| PO-004 | confirmed | 小白狐专属音色是否需要采购、训练或接入第三方音色。 | 已确认使用 MiMo VoiceClone v01；真实 VoiceClone API schema 已通过 smoke 验证，下一步确认 Android remote audio 播放和设备侧听感。 |
| PO-005 | proposed | Open Conversation Mode 的 history 窗口大小、摘要策略和 quick action 生成方式。 | 下一轮先做设计和小步后端实现，安全、隐私、学习、睡前边界不可放松。 |
