# Next Phase Plan v0.2

用途：把 v0.1 MVP 之后的家庭内测前计划拆成可执行阶段。本文档不替代 `docs/CODEX_PROGRESS_BOARD_V0_1.md`，进度状态仍以看板和 QA 记录为准。

当前前提：

```text
1. v0.1 第一轮后端和 Android MVP 已完成。
2. 当前仍需完成完整设备 QA，不能跳过现有文字和安全闭环验收。
3. 下一阶段优先解决语音交互和小白狐形象体验。
4. 默认 Mock 优先，真实模型和儿童数据外发仍受后端 gate 约束。
5. 语音第一阶段优先 Android 本地 SpeechRecognizer + Android TTS，不默认上传原始音频到后端。
6. TTS v1 默认自动朗读小白狐回复，但必须可停止、可静音，并有 DevSettings 或父亲设置开关。
7. 小白狐视觉优先 3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感；Compose Canvas / 2D 只是 fallback。
8. 小白狐 v1 候选形象资产已生成，当前包含 11 个状态：neutral_idle、listening、speaking、jumping_happy、thinking、calm、sleepy、safety_concern、privacy_boundary、homework_focus、network_error。
9. Android 第一版优先预渲染 3D PNG/WebP 状态图 + 轻量 Compose 动画，不引入实时 3D 引擎或大型动画依赖作为必需能力。
10. 采用双设备测试策略：高配 Android 手机先做功能主验证，Honor Pad 5 Android 9 / 4GB 做低配兼容性、大屏和降级验证。
11. Redmi K60 / Android 14 截图显示上一版 TTS 为 `SKIPPED_UNAVAILABLE`，新 APK 已补 TTS service 查询、初始化竞态修复和系统朗读设置入口，仍需真机复测。
12. 小白狐 v1 资源已扩展到 11 个状态，新增 calm、sleepy、safety_concern、privacy_boundary、homework_focus、network_error。
13. 普通聊天已进入 Open Conversation Mode 小步实现：兴趣和日常话题走 `conversation.open`，模型接收进程内短期 history；安全、隐私、学习和睡前边界不放松。
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

目标：用 Android 系统 TTS 默认自动朗读小白狐回复，朗读内容必须来自后端已安全处理的 reply。

设备顺序：

```text
1. 先在高配 Android 手机上跑通默认自动朗读、停止、关闭、VoiceProfile 调整。
2. 再在 Honor Pad 5 上验证中文 TTS 是否存在、音色是否可接受、是否卡顿、是否延迟明显、是否需要关闭自动朗读作为低配默认。
```

范围：

```text
1. Android TextToSpeech 初始化、播放、停止。
2. 只朗读 reply.text，不朗读 debug、session_state 或内部字段。
3. 遵守 reply.voice_enabled。
4. reply.audio_url 为空时使用本地 TTS。
5. 朗读状态和小白狐轻量状态联动。
6. 提供停止当前朗读和静音 / 关闭自动朗读入口。
7. 提供 DevSettings 或父亲设置开关。
8. 通过 TtsController 抽象接入 TextToSpeech。
9. 实现 VoiceProfile：preferredVoiceName、zh-CN、speechRate 稍慢、pitch 偏高不过度、fallback 系统默认中文 voice。
10. 音色方向是小孩子般干净、清脆、中性、活泼可爱，但不能过度尖锐或幼稚。
```

非目标：

```text
1. 不生成真实后端音频文件。
2. 不上传孩子音频给真实模型 provider。
3. 不做夸张音效或刺激型反馈。
4. v1 不做小白狐专属音色，v2 再评估。
```

验收：

```text
1. TTS 不绕过 SafetyEngine / ChildAgentRuntime。
2. 高风险安全回复朗读稳定、低刺激。
3. TTS 失败时文字仍可读，UI 显示温和提示。
4. Redmi K60 等真机上能看到 engine、locale、voice、setLanguage、setVoice、speak 返回值和 failure reason。
5. TTS 请求被接受后小白狐进入 speaking pending；失败、停止或结束后恢复 base state。
6. QA 记录 TTS 自然度和孩子接受度。
```

### Phase 3.1：TTS-D1 可观测性与故障修复

目标：先判断 TTS 链路是否触发、初始化、选中中文 voice、调用 speak()，再决定是否继续依赖系统 TTS。

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
2. 不接第三方 TTS。
3. 不新增后端音频接口。
4. 不承诺 Android 系统 TTS 是最终产品音色。
```

后续判断：

```text
1. 如果 Redmi K60 能朗读但音色差，记录为音色方案问题。
2. 如果 Redmi K60 仍无声但诊断显示 speak SUCCESS，需要继续查系统 TTS 引擎 / 音量 / onStart/onDone 回调。
3. 如果 speak ERROR、语言不支持或 voice 选择失败，则评估替代 TTS。
```

---

## Phase 4：小白狐视觉资源 v1

目标：替换占位形象，形成温和、好奇、活泼开朗的小白狐基础视觉。优先方向是 3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感。

范围：

```text
1. 基础静态形象资源。
2. 优先探索 3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感资源。
3. 当前 v1 候选资产：neutral_idle、listening、speaking、jumping_happy、thinking、calm、sleepy、safety_concern、privacy_boundary、homework_focus、network_error。
4. 后续若继续补充，优先完善同一角色的一致光照、姿态比例和低配尺寸优化。
5. 与 reply.emotion / reply.agent_motion 的映射表。
6. Android 资源命名、drawable-nodpi 和尺寸规范。
7. Compose Canvas / 2D 仅作为 fallback，不阻塞语音开发。
8. 优先预渲染 3D PNG/WebP 状态图 + 轻量 Compose 动画。
9. 低配设备静态降级：减少动画、降低图片尺寸、关闭自动动画或只保留静态状态图。
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
4. 高配手机上 PNG 状态图显示正常。
5. Honor Pad 5 Android 9 / 4GB 上记录图片内存占用、切换流畅度、发热、卡顿和是否需要降级。
```

---

## Phase 5：小白狐动画状态机 v1

目标：让小白狐随会话状态轻量变化，增强陪伴感但不拉长使用时间。

范围：

```text
1. Android 本地状态机。
2. 输入中、识别中、待确认、后端请求中、回复中、TTS 播放中、错误状态。
3. 后端 reply.emotion / reply.agent_motion 映射到温和表现。
4. 动画时长和循环次数受控。
5. 低性能设备上可降级为静态状态。
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
