# Next Phase Plan v0.2

用途：把 v0.1 MVP 之后的家庭内测前计划拆成可执行阶段。本文档不替代 `docs/CODEX_PROGRESS_BOARD_V0_1.md`，进度状态仍以看板和 QA 记录为准。

当前前提：

```text
1. v0.1 第一轮后端和 Android MVP 已完成。
2. 当前仍需完成完整设备 QA，不能跳过现有文字和安全闭环验收。
3. 下一阶段优先解决语音交互和小白狐形象体验。
4. 默认 Mock 优先，真实模型和儿童数据外发仍受后端 gate 约束。
5. 语音输入第一阶段优先 Android 本地 SpeechRecognizer，不默认上传原始音频到后端。
6. 小白狐语音输出主路径改为后端 MiMo VoiceClone 生成 `audio_url`，Android 优先播放远程音频；系统 TextToSpeech 保留为 fallback 和诊断能力。
7. 小白狐视觉优先 3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感；Compose Canvas / 2D 只是 fallback。
8. 小白狐 v1 候选形象资产已生成，当前静态资源包含 11 个状态；动态 animation_v1 资源包以 `mascot_manifest.json` 为准，当前实际状态也是 11 个：idle、listening、speaking、jumping_happy、thinking、calm、sleepy、safety_concern、privacy_boundary、homework_focus、network_error。
9. Android 第一版优先预渲染 3D PNG/WebP 状态图 + 本地 PNG 序列帧轻量播放，不引入实时 3D 引擎或大型动画依赖作为必需能力。
10. 采用双设备测试策略：高配 Android 手机先做功能主验证，Honor Pad 5 Android 9 / 4GB 做低配兼容性、大屏和降级验证。
11. Redmi K60 / Android 14 截图显示上一版系统 TTS 为 `SKIPPED_UNAVAILABLE`，系统 TTS 不再作为正式小白狐音色方案。
12. 小白狐 animation_v1 PNG 序列帧资源已导入 Android assets，当前运行时体积约 117MB，fallback 链为 animation_v1 -> png_static -> canvas。
13. 普通聊天已进入 Open Conversation Mode 小步实现：兴趣和日常话题走 `conversation.open`，模型接收进程内短期 history；安全、隐私、学习和睡前边界不放松。
14. 后端已新增 `POST /api/v1/tts/xiaobaohu`，默认 mock provider，不外发；MiMo VoiceClone 必须显式通过 TTS 数据策略闸门。
15. 本地持久化数据库已确认选用 PostgreSQL；DB1-A 基础设施已进入代码，业务服务仍按 B2-B5 串行迁移，不能阻塞 Android 语音 QA。
16. Redmi K60 真机反馈显示 MiMo VoiceClone 音频初步跑通、动态小白狐形象已经可见，但同步链路等待时间仍长，下一阶段不能继续依赖增加 read timeout。
17. 儿童端主界面下一版改为横屏双栏：左侧动态小白狐，右侧聊天交互；手机也进入横屏。
18. 语音输入开始进入方案准备阶段，优先调研 MiMo ASR / audio input 能力；在接口和儿童语音数据边界确认前，不实现云端 ASR。
19. 下一阶段必须补齐 request_id、结构化日志、provider timing、health 扩展、环境检查和 QA 记录等运行基础组件。
20. 最新产品方向修订为 freedom-first：默认自由对话，时间、父母寄语、记忆、最近聊天和图片能力作为上下文或工具；高风险安全、隐私边界、明确学习求助、明确睡前收尾和父母强规则作为护栏。
21. 拍照能力从“拍题目”升级为“拍给小白狐看”的通用图片分享；玩具、画、书、植物、手工和作业都应先理解孩子意图，再分流。
22. 父母寄语需要支持自由文本，作为 Prompt 背景上下文注入；不能机械复述给孩子，不能覆盖儿童安全底线。
23. Ops P0 已完成 request_id、JSON 日志、request/model/TTS timing 和 `/api/v1/health/detail`。
24. Streaming v1 后端 skeleton 已新增 `/api/v1/conversation/stream`，采用 NDJSON 和 sentence-level pseudo streaming；Android stream client 尚未实现。
25. MiMo ASR spec intake 已完成脱敏归档；云 ASR 默认 disabled，ASR skeleton 不挂载到生产主 app，Android 本地 SpeechRecognizer 仍是 v1 默认路线。
```

---

## Phase 1：完整设备 QA

目标：在窗口模式模拟器或真实安卓平板上完整验收现有 v0.1 MVP。

设备策略：

```text
Device A：高配 Android 手机，功能主验证。
Device B：Honor Pad 5，Android 9，RAM 4GB，低配兼容性和大屏目标设备。
```

范围：

```text
1. 自由聊天。
2. 学习求助。
3. 直接要答案。
4. mock 拍题。
5. 父亲设置。
6. 父亲入口保护。
7. 睡前复盘。
8. 高风险安全。
9. 隐私边界。
10. 后端断开提示。
11. 自动记忆日报素材。
12. 小白狐轻量状态和语音占位边界。
```

验收：

```text
1. MANUAL_QA_V0_1.md 的核心设备侧场景有明确结果。
2. 不使用真实儿童身份、真实家庭信息、真实照片或真实音频。
3. 发现环境共性坑时由主控更新 SHARED_CONTEXT。
4. 不把未验证能力写成 done。
```

---

## Phase 2：语音输入 v1

目标：让孩子可以用语音辅助输入，但仍由确认后的文字进入后端。v1 是 confirm-before-send，不做 hands-free conversational mode。

设备顺序：

```text
1. 先在高配 Android 手机上跑通：点击语音 -> 本地识别 -> 展示文字 -> 确认/编辑 -> 发送。
2. 再在 Honor Pad 5 上验证权限申请、中文识别、儿童声音识别、延迟、失败提示和是否可接受。
3. Honor Pad 5 不作为第一阶段语音功能开发阻塞设备；如效果不好，允许降级为文字优先并记录 QA。
```

范围：

```text
1. Android 本地 SpeechRecognizer。
2. 主动点击后请求 RECORD_AUDIO 权限。
3. 识别结果先展示为待确认文本。
4. 支持编辑、重说、取消和确认发送。
5. 确认后复用现有 /api/v1/conversation/message。
6. 不上传原始音频，不长期保存原始音频。
7. 通过可替换的 VoiceEngine / SpeechInputController 抽象接入 SpeechRecognizer。
```

非目标：

```text
1. 不做常开麦克风。
2. 不做唤醒词。
3. 不做云端 ASR。
4. 不新增后端音频上传接口。
5. 不做 hands-free conversational mode。
```

验收：

```text
1. 误识别不会自动触发 AI 回复。
2. 学习求助和高风险输入仍走后端安全链路。
3. 权限拒绝、识别失败、无网络都有温和文案和文字输入 fallback。
4. QA 记录识别准确率、延迟、中文效果和儿童声音识别效果。
```

---

## Phase 3：TTS 朗读 v1

目标：用后端 MiMo VoiceClone 生成小白狐回复音频，Android 优先播放 `reply.audio_url`。Android 系统 TTS 只作为 fallback 和诊断能力，朗读内容必须来自后端已安全处理的 reply。

设备顺序：

```text
1. 先在高配 Android 手机上跑通 `reply.audio_url` 远程音频播放、停止、关闭、speaking 状态和系统 TTS fallback。
2. 再在 Honor Pad 5 上验证远程 wav 播放、延迟、卡顿、缓存音频体积、系统 TTS fallback 是否可用，以及是否需要关闭自动朗读作为低配默认。
```

## Phase 7：PostgreSQL Local Persistence

目标：把当前内存态服务逐步迁移到本地 PostgreSQL，先支撑家庭内测的数据连续性，不做云端多租户。

当前状态：

```text
1. DB1-A 基础设施已完成：SQLAlchemy sync、psycopg、Alembic、PostgreSQL 16 local docker compose、migration/reset 脚本和基础测试。
2. 初始表包含 children、parent_policies、conversation_sessions、conversation_messages、routing_decisions、memory_items、parent_reports、tts_cache_records。
3. 业务服务仍未迁移，当前 parent policy、memory、report 等运行时行为仍以原有内存实现为主。
```

迁移顺序：

```text
1. B2：ParentPolicyService 持久化。
2. B3：Conversation session/message 落库，保存 child/agent message、audio_url、emotion、agent_motion，不保存 debug。
3. B4：MemoryService 落库。
4. B5：ParentReportService 落库。
```

数据边界：

```text
1. 原始音频、原始照片、API key 和 debug internals 不入库。
2. TTS cache metadata 优先保存 hash，不保存完整敏感文本。
3. 当前是本地家庭自用库；如果未来云端化或上架，必须重新做儿童数据合规评审。
```

---

## Phase 8：Streaming Interaction And Landscape UX

目标：把当前“同步等待完整回复 + 完整 TTS 音频”的体验改造成可渐进反馈的儿童对话体验，同时把 Android 主界面调整为横屏双栏。

当前同步链路：

```text
child input
  -> 后端等待 LLM 完整回复
  -> 后端等待 MiMo TTS 完整音频
  -> conversation 返回 text + audioUrl
  -> Android 播放
```

下一阶段目标链路：

```text
child input
  -> 后端立即返回 stream
  -> text_delta 持续输出
  -> sentence/chunk ready 后触发 TTS
  -> audio segment ready 后 Android 排队播放
  -> 文本和语音都能渐进反馈
```

阶段拆分：

```text
1. S-Stream-0：先写 `STREAMING_INTERACTION_DESIGN_V0_1.md`，确认 SSE/NDJSON、事件结构、pseudo streaming 和 QA 指标。
2. S-Stream-1：已新增 `/api/v1/conversation/stream`，保留旧 `/conversation/message`，不绕过安全、场景、runtime 和 TTS gate。
3. S-Stream-2：Android 增加 stream client、progressive bubble 和 audio segment queue；stream 失败 fallback 到旧接口。
4. UI-Landscape-1：Android 横屏双栏，左侧小白狐，右侧对话；不做完整美术重设计。
5. Fox-Coverage-1：输出小白狐 11/12 状态资源和业务触发覆盖矩阵，不假装未触发状态已完成。
```

S-Stream-1 当前实现边界（2026-05-21）：

```text
1. 事件协议为 `application/x-ndjson`，事件包含 session_started、route_decision、text_delta、sentence_ready、tts_started、audio_ready、text_final、done 和 error。
2. 后端先生成经过安全输出检查的完整 reply，再按句子/短片段 pseudo streaming；当前不假设 MiMo 支持 true streaming。
3. TTS 按 segment 生成；TTS 失败会发送 recoverable error，不中断 text_final 和 done。
4. stream timing 日志记录 request_id、session_id_hash、active_scene、first_text_ms、first_audio_ms、stream_total_ms、tts_segment_count 和 error_type。
5. Android 尚未接入 stream client；旧 `/api/v1/conversation/message` 继续作为正式 fallback。
```

约束：

```text
1. 45 秒 read timeout 只是临时稳定性修复，不作为最终体验方案。
2. 如果 MiMo VoiceClone 不支持 true streaming，先做 sentence-level pseudo streaming。
3. TTS 失败不能中断文本流。
4. 高风险、隐私、学习“不直接给答案”、睡前低刺激边界不得因流式而绕过。
5. 横屏改造不得破坏 MiMo audioUrl 播放、animation_v1 和现有父亲入口保护。
```

QA 指标：

```text
1. first_text_ms：孩子发送后到首个文本 delta 的时间。
2. first_audio_ms：孩子发送后到首段音频可播放的时间。
3. total_turn_ms：整轮文本和音频完成时间。
4. stream_interrupt_recovery：stream 中断时是否保留已有文本并温和提示。
5. audio_segment_gap：分段音频之间是否有明显断裂。
```

---

## Phase 9：ASR Research And Ops Foundation

目标：语音输入先进入调研和边界确认，同时补齐本地家庭内测需要的运行基础组件。

ASR 调研：

```text
1. 已新增 `docs/ASR_INPUT_RESEARCH_V0_1.md`。
2. 已新增 `docs/MIMO_ASR_INTEGRATION_DESIGN_V0_1.md`。
3. 父亲本机 spec 显示 MiMo chat completions audio input 可作为非流式 ASR 候选，候选模型为 `mimo-v2.5` / `mimo-v2-omni`。
4. 流式 ASR 未确认；儿童音频 retention、删除和 no-training 承诺未确认。
5. 未确认前不启用云端 ASR，不上传真实儿童原始音频。
6. Android v1 仍遵守 confirm-before-send，不做 hands-free conversational mode。
7. 后端已新增 mock-first ASR skeleton 和 AsrDataPolicyGuard；ASR router 当前不挂载到主 app。
```

---

## Phase 10：Freedom-First Conversation And Universal Image Sharing

目标：把系统从固定场景驱动调整为“自由对话为底座，护栏按需介入，多模态能力按需调用”。

实施顺序：

```text
1. 新增 `FREEDOM_FIRST_INTERACTION_DESIGN_V0_1.md`。
2. 新增 `UNIVERSAL_IMAGE_SHARING_DESIGN_V0_1.md`。
3. ParentPolicy 增加 `parent_message_raw` 和更新时间。
4. PromptManager 增加 Child Profile、Parent Message、Time Context 层。
5. SceneOrchestrator 默认回到 `conversation.open`，时段只做语气上下文。
6. Attachment API 支持通用 image sharing，作业题和隐私敏感图片按意图分流。
7. Android 父亲设置增加父母寄语，图片入口改为“拍给小白狐看”。
8. 第二轮收窄学习意图，不再用单独“题 / 不会”触发 homework。
9. 普通图片后续快捷动作携带 attachment_id 和图片摘要，进入 LLM 上下文。
10. ParentPolicyService 优先使用 PostgreSQL 持久化父母寄语，dev/test 数据库不可用时回退内存。
```

验收：

```text
after_school + “我想聊恐龙” -> conversation.open。
bedtime + “我想给你看积木” -> conversation.open + 低刺激上下文。
“晚安” / “我困了” -> daily.bedtime_reflection。
普通图片分享不进入 homework_help。
普通图片后续“聊聊它 / 编个故事 / 问这是什么”能围绕刚才图片继续。
作业图片仍进入 learning.homework_help。
父母寄语进入 Prompt，但不出现在儿童 UI debug。
```

运行基础组件：

```text
1. 新增 `docs/OPS_FOUNDATION_GAP_ANALYSIS_V0_1.md`。
2. P0 thin slice 已完成：request_id middleware、结构化 JSON 日志、request timing、LLM/TTS provider timing、health/detail 和日志脱敏测试。
3. health 应逐步区分 app、postgres、tts_cache、mimo_config。
4. 日志不得包含 API key、完整儿童原文、完整回复文本、原始音频或照片路径。
5. 本地脚本和 QA 报告需要统一记录 request_id、设备、网络、后端 commit、APK build。
```

Ops P0 当前能力（2026-05-21）：

```text
1. 每个 HTTP 请求都有 `X-Request-ID`，客户端安全值会沿用，非法或超长值会替换。
2. 后端 stdout 为 JSON line 日志，request timing、model timing、TTS timing 可通过 request_id 串联。
3. `GET /api/v1/health/detail` 返回 postgres、tts_cache、小白狐 voice sample 和 MiMo TTS config 状态；组件失败返回 degraded。
4. 日志只允许记录 hash、长度、耗时、provider/model、cache 命中和 error_type；禁止完整 child text、prompt、parent_message_raw、TTS text、API key、原始音频和照片。
5. Streaming v1 后端将复用这些字段，并补充 `first_text_ms`、`first_audio_ms` 和 `stream_total_ms`。
```

范围：

```text
1. 后端 `/api/v1/tts/xiaobaohu` 生成或返回缓存音频 URL。
2. 只朗读 reply.text，不朗读 debug、session_state 或内部字段。
3. 遵守 reply.voice_enabled。
4. reply.audio_url 非空时 Android 优先播放远程音频。
5. 朗读状态和小白狐轻量状态联动。
6. 提供停止当前朗读和静音 / 关闭自动朗读入口。
7. 提供 DevSettings 或父亲设置开关。
8. 通过 TtsController / AudioUrlPlayer 抽象接入远程音频播放；系统 TextToSpeech 作为 fallback。
9. 系统 fallback 保留 VoiceProfile：preferredVoiceName、zh-CN、speechRate 稍慢、pitch 偏高不过度、fallback 系统默认中文 voice。
10. 正式音色方向由 MiMo VoiceClone v01 承担：小孩子般干净、清脆、中性、活泼可爱，但不能过度尖锐或幼稚。
```

非目标：

```text
1. 不上传孩子原始音频给真实模型 provider。
2. 不让 Android 直接调用 MiMo 或保存 MiMo API key。
3. 不做夸张音效或刺激型反馈。
4. 不做复杂音频流式播放或实时 3D。
```

验收：

```text
1. TTS 不绕过 SafetyEngine / ChildAgentRuntime。
2. 高风险安全回复朗读稳定、低刺激。
3. TTS 失败时文字仍可读，UI 显示温和提示。
4. 后端 TTS 默认 mock 时不外发；MiMo policy 不满足时不调用外部 provider。
5. TTS 请求被接受后小白狐进入 speaking pending；失败、停止或结束后恢复 base state。
6. QA 记录远程音频播放延迟、自然度、孩子接受度和系统 fallback 结果。
```

### Phase 3.1：TTS-D1 可观测性与故障修复

目标：先判断 Android 系统 TTS fallback 链路是否触发、初始化、选中中文 voice、调用 speak()，并作为 remote audioUrl 失败时的诊断和降级能力。

范围：

```text
1. 扩展 TtsUiState / VoiceDiagnostics。
2. 记录 enginePackageName、selectedLocale、selectedVoiceName、setLanguageResult、setVoiceResult、lastSpeakResult、lastFailureReason。
3. InputBar 显示朗读已开启、正在准备朗读、不可用等短状态。
4. 开发构建显示紧凑诊断文本，便于 Redmi K60 复验。
5. speaking 状态前移到请求被接受阶段，不完全依赖系统 onStart。
6. 系统 TTS 不可用或 speak 返回 ERROR 时恢复 baseAgentState，不影响文字聊天。
```

非目标：

```text
1. 不做 ASR / SpeechRecognizer。
2. 不让 Android 直接接第三方 TTS。
3. 不新增后端音频上传接口。
4. 不承诺 Android 系统 TTS 是最终产品音色。
```

后续判断：

```text
1. 如果 Redmi K60 能用系统 TTS 朗读但音色差，记录为 fallback 体验问题，不再作为正式音色方向。
2. 如果 Redmi K60 仍无声但诊断显示 speak SUCCESS，需要继续查系统 TTS 引擎 / 音量 / onStart/onDone 回调。
3. 如果 speak ERROR、语言不支持或 voice 选择失败，则保留文字 fallback，并优先推进后端 VoiceClone audioUrl 播放。
```

### Phase 3.2：Backend VoiceClone TTS endpoint

目标：提供受控的小白狐语音生成后端能力，为 Android remote audio playback 做准备。

当前实现：

```text
1. 新增 `POST /api/v1/tts/xiaobaohu`。
2. 默认 `CHILD_AI_TTS_PROVIDER=mock`，返回本地 mock wav audioUrl，不调用外部服务。
3. 新增 `TtsDataPolicyGuard`，MiMo VoiceClone 必须显式 enabled、API key、allow child text 和 retention policy checked。
4. 新增本地缓存目录 `backend/storage/tts_cache`，生成缓存不进 git。
5. `/media/tts/...wav` 只暴露生成音频，不暴露 voice sample 或 metadata。
6. conversation 自动生成 audioUrl 默认为关闭；TTS 失败不影响文字回复。
7. 真实 MiMo VoiceClone smoke 已通过，当前 provider 使用 `/chat/completions`，从 `choices[0].message.audio.data` 读取音频。
8. `scripts/smoke_mimo_tts.sh` 已验证 `/api/v1/tts/xiaobaohu` 和 conversation 自动 `reply.audio_url` 都能返回可下载 RIFF/WAV。
```

下一步：

```text
1. Redmi K60 验证 remote audioUrl 是否真正播放 MiMo 小白狐音色。
2. 如果 `reply.audio_url` 播放失败，fallback 到系统 TTS 或文字。
3. 在 Redmi K60 和 Honor Pad 5 上记录播放延迟、卡顿、speaking 状态和 fallback。
```

---

## Phase 4：小白狐视觉资源 v1

目标：替换占位形象，形成温和、好奇、活泼开朗的小白狐基础视觉。优先方向是 3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感。

范围：

```text
1. 基础静态形象资源。
2. 优先探索 3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感资源。
3. 当前 v1 候选资产：neutral_idle、listening、speaking、jumping_happy、thinking、calm、sleepy、safety_concern、privacy_boundary、homework_focus、network_error。
4. 当前 animation_v1 动态资源：manifest-driven PNG frames，11 个状态，每状态 24 帧，12 FPS。
5. 与 reply.emotion / reply.agent_motion 的映射表。
6. Android 静态资源命名、drawable-nodpi 和尺寸规范。
7. Android 动态资源放在 `android/app/src/main/assets/mascot/xiaobaohu/v1/`，保留 manifest 包结构。
8. Compose Canvas / 2D 仅作为 fallback，不阻塞语音开发。
9. 优先预渲染 3D PNG/WebP 状态图 + 本地序列帧轻量播放。
10. 低配设备静态降级：减少动画、降低图片尺寸、关闭自动动画或只保留静态状态图。
```

原则：

```text
1. 不做强刺激视觉。
2. 不做排行榜、连击奖励或上瘾式动画。
3. 不制造“唯一朋友”“只有我懂你”的依赖表达。
4. 视觉资源来源和版权必须清晰。
5. UI、产品、设计和测试说明统一称为“小白狐”；代码 class 名 FoxAgent 暂可保留。
6. 不引入实时 3D 引擎或重型动画依赖作为第一版必需能力。
```

验收：

```text
1. 资源能在平板横竖屏或目标布局中稳定显示。
2. 不遮挡聊天、确认文本、父亲入口或错误提示。
3. 与 F1 视觉 brief 保持一致。
4. 高配手机上 PNG 静态图和 animation_v1 序列帧显示正常。
5. Honor Pad 5 Android 9 / 4GB 上记录图片内存占用、切换流畅度、发热、卡顿和是否需要降级。
```

---

## Phase 5：小白狐动画状态机 v1

目标：让小白狐随会话状态轻量变化，增强陪伴感但不拉长使用时间。

范围：

```text
1. Android 本地 `MascotController`。
2. `AssetManifestLoader` 从 assets 读取 `mascot_manifest.json` 和状态 manifest。
3. `FrameSequencePlayer` 按 fps 播放 PNG frames，支持 loop、oneshot_hold、short_loop。
4. 输入中、识别中、待确认、后端请求中、回复中、TTS 播放中、错误状态。
5. 后端 reply.emotion / reply.agent_motion 映射到温和表现。
6. 动画时长和循环次数受控，`jumping_happy` 等正反馈不做上瘾式循环。
7. 低性能设备上可降级为静态 PNG 或 Canvas。
```

非目标：

```text
1. 不做复杂游戏化系统。
2. 不做连击、积分、排行榜或抽奖反馈。
3. 不通过动效诱导孩子延长聊天。
```

验收：

```text
1. 动画不影响文字输入、语音确认、父亲入口和错误提示。
2. 高风险场景表现稳定、克制，不戏剧化。
3. 后端断开或 TTS 失败时状态可恢复。
4. safety_concern / privacy_boundary 优先级高于 speaking。
5. manifest 或 frames 缺失时不崩溃，fallback 到静态 PNG 或 Canvas。
```

---

## Phase 6：真实平板家庭内测准备

目标：准备可控的家庭内测版本，确保父亲可治理、儿童数据最小化、失败路径清晰。

范围：

```text
1. 真机 LAN 或本地后端部署说明。
2. 完整手动 QA 记录。
3. 父亲设置、日报、PIN 轻量保护复验。
4. 数据保留和删除策略复核。
5. 真实模型 provider 是否启用的人工确认。
6. 语音权限、TTS、识别失败和后端断开路径复验。
7. 小白狐视觉和动画边界复验。
```

内测前必须确认：

```text
1. 不在 Android 放模型 API key。
2. 不默认上传原始音频或真实照片。
3. 不保存长篇逐字聊天原文到长期记忆。
4. 学习问题不直接给最终答案。
5. 高风险输入鼓励联系父母、老师或可信成人，并触发父亲提醒。
6. 小白狐不制造秘密关系或唯一朋友依赖。
```

---

## Phase 7：Open Conversation Mode 小步实现

目标：让普通聊天和兴趣话题更自由，同时保留儿童安全、隐私、学习和睡前边界。

当前反馈：

```text
1. 父亲反馈普通对话仍显得程序控制较重。
2. 快捷选项目前多由 SceneOrchestrator 固定返回，不够随上下文动态变化。
3. 模型需要接收最近多轮 conversation history，而不是只看单轮输入和场景 fallback。
```

已完成的小步实现：

```text
1. 新增 conversation.open 场景，普通兴趣和日常话题不再硬拉回 after_school 固定菜单。
2. 新增 ConversationHistoryService，只保存每个 session 的短期进程内窗口，服务重启丢失。
3. ChildAgentRuntime 输入最近 N 轮精简 user/assistant 消息，避免只传当前 text。
4. PromptManager 增加 conversation_open prompt，要求自然接住孩子话题，避免固定三选项菜单。
5. QuickActionService 先用轻量上下文规则生成普通聊天快捷选项，硬场景仍保留 scene fallback。
6. 长期 memory 仍只保存结构化摘要，不保存 full chat transcript。
```

后续设计：

```text
1. quick actions 可升级为模型建议 + 后端安全过滤 + 场景 fallback。
2. history 窗口大小、摘要策略和 token 控制需要继续评估。
3. 如果未来持久化完整对话，必须单独做儿童数据、父亲治理、删除和最小化审查。
```

非目标：

```text
1. 不删除 SafetyEngine、IntentClassifier、SceneOrchestrator。
2. 不放松学习“不直接给答案”。
3. 不让普通聊天绕过父亲策略、隐私边界或高风险提醒。
4. 不删除短期 history 的数据最小化边界，不把完整逐字聊天写入长期 memory。
```

验收：

```text
1. “我想聊恐龙”等兴趣话题能自然多轮延续。
2. 模型能引用最近一两轮上下文，但不保存长篇原文到长期记忆。
3. 高风险、隐私、学习和睡前仍按既有边界处理。
4. quick actions 不再长期固定为同一组，而是随上下文动态生成或安全 fallback。
```
