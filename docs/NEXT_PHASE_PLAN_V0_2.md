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
8. 小白狐 v1 候选形象资产已生成，当前包含 neutral_idle、listening、speaking、jumping_happy、thinking 五个基础状态。
9. Android 第一版优先预渲染 3D PNG/WebP 状态图 + 轻量 Compose 动画，不引入实时 3D 引擎或大型动画依赖作为必需能力。
10. 采用双设备测试策略：高配 Android 手机先做功能主验证，Honor Pad 5 Android 9 / 4GB 做低配兼容性、大屏和降级验证。
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
3. TTS 失败时文字仍可读。
4. QA 记录 TTS 自然度和孩子接受度。
```

---

## Phase 4：小白狐视觉资源 v1

目标：替换占位形象，形成温和、好奇、活泼开朗的小白狐基础视觉。优先方向是 3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感。

范围：

```text
1. 基础静态形象资源。
2. 优先探索 3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感资源。
3. 当前 v1 候选资产：neutral_idle、listening、speaking、jumping_happy、thinking。
4. 后续补充：calm、sleepy、safety_concern、privacy_boundary、homework_focus、network_error。
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
