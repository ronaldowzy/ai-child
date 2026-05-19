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
| PD-002 | confirmed | 语音第一阶段优先 Android 本地 `SpeechRecognizer` + Android TTS，不默认上传原始音频到后端。 | Android 权限、语音设计、后端 API 边界 |
| PD-003 | confirmed | 语音输入应先转文字确认，再发送给后端；不要误识别后自动直接进入 AI 回复。 | Android UX、儿童安全、QA |
| PD-004 | confirmed | 小白狐形象应温和、好奇、慢热友好，避免强刺激、排行榜、连击奖励或上瘾式动画。 | 视觉 brief、动画状态、Android UI |
| PD-005 | confirmed | 后端继续通过 `reply.voice_enabled`、`reply.audio_url`、`reply.emotion`、`reply.agent_motion` 向 Android 暴露表现层信号。 | 后端 API、Android DTO、TTS/动画 |
| PD-006 | confirmed | 小白狐表现层不得制造“唯一朋友”“只有我懂你”等依赖感。 | Prompt、安全检查、视觉与动效文案 |
| PD-007 | confirmed | 所有新体验仍必须遵守：不直接给作业最终答案，不要求保密，不鼓励隐瞒父母，不保存原始音频/照片到长期记忆。 | 全端、安全、记忆、QA |
| PD-008 | confirmed | 每次父亲确认的新产品想法，必须先写入 `docs/PRODUCT_DECISIONS_V0_1.md`，再进入子会话实现。 | 协作流程、AGENTS、README |
| PD-009 | confirmed | 正式名称为“小白狐”；UI、产品、设计和测试说明优先统一。代码 class 名 `FoxAgent` 暂可保留，后续如要改代码命名单独 refactor。 | Android UI、README、设计文档、QA 文案、后续代码重命名计划 |
| PD-010 | confirmed | 语音输入 v1 是 confirm-before-send：点击语音 -> 孩子说话 -> Android 本地 ASR -> 展示识别文本 -> 孩子确认/可编辑 -> 点击发送 -> text 走 `/conversation/message`。future hands-free conversational mode 不进入 v1。 | Android 语音输入、QA、后端 API 边界 |
| PD-011 | confirmed | TTS v1 默认自动朗读小白狐回复；必须有停止/静音、DevSettings 或父亲设置开关，并实现 `VoiceProfile`。v2 再评估小白狐专属音色。 | Android TTS、父亲治理、DevSettings、QA |
| PD-012 | confirmed | `VoiceProfile` v1 包含 `preferredVoiceName`、`zh-CN`、稍慢 `speechRate`、偏高但不过度的 `pitch`、fallback 系统默认中文 voice。 | Android TTS 配置、测试 |
| PD-013 | confirmed | 小白狐视觉目标是 3D / soft 3D / 毛绒感 / 立体绘本感；Compose Canvas / 2D 只是 fallback，不阻塞语音开发。 | 视觉 brief、Android 资源、下一阶段计划 |
| PD-014 | confirmed | 允许 Android `SpeechRecognizer` / `TextToSpeech`，但必须通过可替换抽象：`VoiceEngine` / `SpeechInputController` / `TtsController`。 | Android 架构、测试、后续替换能力 |
| PD-015 | confirmed | 语音 QA 必须记录识别准确率、延迟、中文效果、儿童声音识别、TTS 自然度和孩子接受度。 | QA 计划、家庭内测准备 |

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
Status: confirmed
Source: father / product planning
Decision: 语音第一阶段优先 Android 本地 `SpeechRecognizer` + Android TTS，不默认上传原始音频到后端。
Rationale: 本地系统能力能更快形成家庭内测闭环，同时降低儿童原始音频外发和留存风险。
Affected modules: Android voice、Android permissions、backend API boundary、privacy policy、QA。
Implementation notes: Android 只把确认后的文本发给 `/api/v1/conversation/message`；后端暂不新增真实音频上传接口。
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
Implementation notes: 新文档和新 UI 文案使用“小白狐”；历史“小狐狸”文案作为待替换事项跟踪。
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
Status: confirmed
Source: father / TTS decision
Decision: TTS v1 默认自动朗读小白狐回复；必须有停止/静音、DevSettings 或父亲设置开关，并实现 `VoiceProfile`。v2 再评估小白狐专属音色。
Rationale: 语音体验应默认可听见，但必须给父亲和孩子保留控制权，并避免承诺系统 TTS 无法保证的固定专属音色。
Affected modules: Android TTS、DevSettings、parent settings、VoiceProfile、QA。
Implementation notes: 只朗读 agent reply，不朗读孩子输入、debug 或 session_state；高风险和睡前场景低刺激。
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

---

## 3. Current Product Direction

v0.1 第一轮后端和 Android MVP 已完成，当前重点不是扩展开放式聊天，而是进入家庭内测前加固和下一阶段体验设计：

```text
1. 先完成完整设备 QA，确认现有文字聊天、学习引导、mock 拍题、父亲治理和安全场景在平板上可用。
2. 再进入语音输入 v1：Android 本地 ASR，先给孩子和父亲可见的文字确认，不自动发送误识别内容；hands-free conversational mode 留到未来阶段。
3. 再进入 Android TTS 朗读 v1：默认自动朗读小白狐回复，同时提供停止/静音和 DevSettings 或父亲设置开关；后端暂不生成真实音频。
4. 语音实现必须先抽象为 VoiceEngine / SpeechInputController / TtsController，并用 VoiceProfile 管理中文系统 voice、语速、音高和 fallback。
5. 再接小白狐视觉资源和轻量状态机，优先目标是 3D / soft 3D / 毛绒感 / 立体绘本感；Compose Canvas / 2D 只是 fallback，不阻塞语音开发。
6. 所有新增体验继续遵守儿童安全底线和数据最小化原则。
```

---

## 4. Open Items For Later Confirmation

| ID | 状态 | 待确认问题 | 当前默认 |
|---|---|---|---|
| PO-001 | proposed | 真实平板家庭内测前是否需要持久化父亲 policy、日报素材和结构化记忆。 | v0.1 仍可接受内存态；家庭内测准备阶段再确认。 |
| PO-002 | proposed | 是否需要后端音频上传或云端 ASR。 | v0.2 之前默认不需要；如启用必须单独做儿童数据和 retention review。 |
| PO-003 | proposed | 小白狐视觉资源数量、文件格式、制作方式和版权来源。 | 视觉方向已确认优先 3D / soft 3D / 毛绒感 / 立体绘本感；具体资源由视觉 brief / F1 会话继续设计。 |
| PO-004 | proposed | 小白狐专属音色是否需要采购、训练或接入第三方音色。 | v2 再评估；v1 使用 Android 系统 TTS + VoiceProfile tuning。 |
