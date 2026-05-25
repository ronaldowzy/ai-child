# Voice Interaction Design v0.1

用途：定义儿童端语音输入、TTS 朗读、opening greeting、音频数据边界和 QA 验收清单。本文档区分已实现能力和待设备验收项；Android 语音输入 v1 已实现点击录音、上传后端 ASR、儿童默认自动发送 transcript，确认面板仅保留为 DevSettings / 父亲调试模式，仍待 Redmi K60 / Honor Pad 5 真机 QA。ASR 真实识别主路径已修订为后端本地 sherpa-onnx + SenseVoice-Small int8，MiMo ASR 仅作为本地异常后的云端 fallback。小白狐语音输出主路径已从 Android 系统 TTS 调整为后端 MiMo VoiceClone 音频生成；当前儿童端自动朗读不使用系统 TTS fallback，系统 TTS 仅保留为开发诊断/未来评估背景。

关联决策：

```text
docs/PRODUCT_DECISIONS_V0_1.md
PD-002 / PD-034：语音输入曾修订为后端接 MiMo audio input / ASR；现由 PD-048 进一步修订为本地 ASR 优先，MiMo 作为 fallback。
PD-003：儿童端默认改为 voice-first 自动发送，confirm-before-send 仅保留为 DevSettings / 父亲调试模式。
PD-005：后端继续通过 reply.voice_enabled、reply.audio_url、reply.emotion、reply.agent_motion 暴露表现层信号。
PD-010：语音输入 v1 儿童默认流程是点击语音 -> 录音 -> 后端 ASR -> 自动发送 transcript -> conversation stream；不做常开麦克风或自动连续监听。
PD-011：TTS v1 默认自动朗读小白狐回复，必须有停止/静音和 DevSettings 或父亲设置开关。
PD-014：SpeechRecognizer / TextToSpeech 必须通过 VoiceEngine / SpeechInputController / TtsController 抽象。
PD-017：小白狐音色方向是小孩子般干净、清脆、中性、活泼可爱，但不能过度尖锐或幼稚。
PD-018：采用双设备测试策略，高配 Android 手机先做功能主验证，Honor Pad 5 Android 9 / 4GB 做低配兼容性验证。
PD-021：Redmi K60 真机反馈显示 TTS 链路不可观测且无声，下一步优先修 TTS 诊断、UI 状态和 fallback。
PD-022：Android 系统 TTS 只是 v1 验证方案，不作为最终儿童产品音色承诺。
PD-027：小白狐正式品牌音色方案改为后端 MiMo VoiceClone；VoiceDesign 只用于音色筛选，普通 MiMo TTS 只做测试/兜底。
PD-034：ASR v1 方案确定接 MiMo audio input / ASR；真实儿童音频外发必须由父亲授权和 ASR data policy flags 控制。
PD-048：ASR v1 第一选择改为 sherpa-onnx + SenseVoice-Small int8 本地识别，本地异常后再走原有 MiMo ASR fallback。
PD-036：儿童默认隐藏文字输入框、发送按钮和可编辑 ASR 文本确认面板；语音是主输入。
PD-037：儿童聊天页打开后，小白狐请求 opening greeting；称呼优先 child_nickname，其次 child_display_name，都没有则不强行称呼。
```

---

## 1. Scope

### 1.1 v0.1 Current Scope

```text
1. 后端已返回 reply.voice_enabled、reply.audio_url、reply.emotion、reply.agent_motion。
2. Android DTO 已解析这些字段，并已做小白狐轻量状态映射。
3. Android 语音输入 v1 已接入：点击后请求麦克风权限，录制短 WAV，上传后端 `/api/v1/asr/transcribe`；后端优先本地 SenseVoice ASR，异常后按配置 fallback；儿童默认自动发送非空 transcript，DevSettings / 父亲调试模式可恢复可编辑待确认文本。
4. 后端已提供 `POST /api/v1/tts/xiaobaohu`；当前测试阶段应启用目标 TTS provider，并通过环境变量和 TTS 数据策略闸门验证真实音频链路。
5. Android 已实现 remote `reply.audio_url` 优先播放、默认自动朗读、停止/静音控制、VoiceProfile 诊断和小白狐 speaking 状态联动；儿童端自动朗读不再 fallback 到系统 TextToSpeech。
6. Android unified interaction state thin slice 已新增 `ChildTurnUiPhase` / `ChildInteractionPresentation`，统一派生 ASR listening/recognizing、stream thinking、TTS pending/speaking、image processing、needs retry、permission needed 和 service error 的儿童可见状态。
7. mock 拍题和学习求助仍以文字和 mock OCR 为主。
```

### 1.2 v0.2 Voice Scope

```text
1. 语音输入 v1：Android 点击录音后上传短音频到后端 ASR，后端优先调用本地 sherpa-onnx + SenseVoice-Small int8；本地异常时再走配置的原有识别方式。
2. 儿童默认不展示可编辑识别文本，ASR ok 且 transcript 非空后自动发送 conversation stream；确认面板只作为 DevSettings / 父亲调试模式。
3. TTS 朗读 v1：后端使用小白狐 VoiceClone 生成 `audio_url`，Android 优先播放 `audio_url`。
4. `audio_url` 不可用或播放失败时，Android 保留文字和温和提示，不用系统 TextToSpeech 顶替儿童端自动朗读；系统 TTS 不再作为正式小白狐音色方案。
5. 后端 ASR endpoint 可以接收一次性短音频做转写，但原始音频不入长期库、不进日志、不进入 memory；语音输入正式进入对话的仍是自动发送后的文本。
6. Hands-free conversational mode 是 future，不进入 v1。
7. 本地 ASR 方案见 `docs/LOCAL_ASR_SENSEVOICE_DESIGN_V0_1.md`；MiMo ASR / audio input 仍作为 fallback 和对照测试路径，结论见 `docs/ASR_INPUT_RESEARCH_V0_1.md` 和 `docs/MIMO_ASR_INTEGRATION_DESIGN_V0_1.md`；真实儿童音频外发必须由父亲授权和 ASR policy flags 控制。
8. 语音输出下一步转向文本流式和 TTS 分句/分段播放，不能继续依赖增加同步 read timeout。
```

---

## 2. Android Voice Architecture

Android v1 可以使用平台 `SpeechRecognizer` 和 `TextToSpeech`，但业务层不得直接绑定平台实现。先定义可替换抽象，便于未来替换本地引擎、云端能力或小白狐专属音色。

```text
VoiceEngine
  -> SpeechInputController
  -> TtsController
  -> VoiceProfile
```

职责边界：

| Component | 责任 | v1 默认实现 |
|---|---|---|
| VoiceEngine | 管理语音输入和 TTS 的总入口、权限状态、开关状态和生命周期 | Android voice engine |
| SpeechInputController | 处理点击语音、录音、上传后端 ASR、识别结果、自动发送、取消、错误和调试用 confirm-before-send 状态 | Android recorder + backend ASR upload wrapper |
| TtsController | 处理自动朗读、停止、静音、远程音频播放、错误和生命周期释放；儿童端自动朗读不混播系统 TTS fallback | Remote audio player + diagnostic fallback abstraction |
| VoiceProfile | 管理语言、voice 名称、语速、音高和 fallback | zh-CN system voice profile |

---

## 3. Android Speech Recognition Strategy

```text
1. 第一阶段 ASR provider 使用后端本地 SenseVoice ASR；MiMo audio input / ASR 作为本地异常后的云端 fallback，Android 平台 SpeechRecognizer 可保留为未来 fallback 评估，不是当前 ASR v1 主路径。
2. 语音识别是儿童默认输入方式，但不改变后端统一 conversation API 的安全边界。
3. 儿童默认识别成功后自动发送 transcript；不展示编辑框，不要求孩子点击确认。
4. 开发/父亲调试模式可打开确认面板，用于查看、编辑、重说、取消或确认发送。
5. 识别失败、噪声过大、超时或权限拒绝时，提供重说、取消或请大人检查，不自动发送。
6. 不把原始音频写入本地长期存储；上传后端 ASR 的短音频只用于本次转写，不写数据库、不进日志、不进 memory。
7. 识别能力必须封装在 SpeechInputController，UI 不直接依赖 SpeechRecognizer。
8. Hands-free conversational mode 不进入 v1；v1 不做常开麦克风或自动连续监听。
```

补充方向（2026-05-20）：

```text
1. 语音输入已从调研进入 MiMo ASR v1 后端接入阶段。
2. 未打开父亲授权和 ASR policy flags 前，不外发真实儿童音频；开发验证只用 fake/smoke audio。
3. Android 仍不得保存模型 API key，后端必须提供独立数据策略 gate。
4. 儿童默认自动发送 transcript；confirm-before-send 只作为 DevSettings / 父亲调试模式；hands-free conversational mode 仍是 future。
```

补充结论（2026-05-21）：

```text
1. 外部规格显示 MiMo chat completions audio input 可作为非流式 ASR，目标模型为 `mimo-v2.5` / `mimo-v2-omni`。
2. 云端 ASR 外发必须有父亲授权和 policy flags；缺少可验证的 retention、删除和 no-training 承诺时应标记 BLOCKED，而不是写成通过。
3. MiMo ASR 只返回 transcript；儿童默认由 Android 自动发送，调试模式才展示待确认文本。
4. 云端 MiMo ASR 是 v1 目标路线；Android 本地 SpeechRecognizer 不作为当前主路径。
5. 不做 streaming ASR、常开麦克风、唤醒词或 hands-free conversational mode。
```

补充结论（2026-05-23）：

```text
1. 实测每轮音频发到大模型端识别耗时影响儿童端体验，ASR 真实识别主路径改为本地优先。
2. 当前第一选择是 sherpa-onnx + SenseVoice-Small int8，本机 Apple M2 / 8GB 可运行，公开中文样例速度明显优于 MiMo 云端识别链路。
3. 后端保留 MiMo ASR provider 作为本地异常后的 fallback；fallback 仍必须通过父亲授权和 ASR data policy flags。
4. 当前测试阶段应安装本地 runtime 和模型文件并启用 `CHILD_AI_ASR_PROVIDER=local_sensevoice` 验证真实本地识别链路。
5. 本地 ASR 不改变数据边界：原始音频只在一次请求中存在，不入库、不进日志、不进 memory。
```

v1 流程：

```text
点击语音
  -> 孩子说话
  -> Android 上传短音频到后端 ASR
  -> 后端优先本地 SenseVoice ASR
  -> 本地异常时按配置 fallback，MiMo fallback 必须通过 policy gate
  -> 儿童默认自动发送 transcript
  -> needs_retry / policy blocked / permission denied 时提供重说、取消或请大人检查
  -> text 走 conversation stream，失败时 fallback /api/v1/conversation/message
```

推荐状态：

| State | 说明 | 下一步 |
|---|---|---|
| idle | 默认语音待命 | 可点击语音大按钮 |
| listening | 正在听 | 可取消 |
| recognizing | 后端 ASR 识别中 | 等待结果 |
| auto_sending | 已听到并准备发送 | 自动进入 conversation stream |
| confirm_text_debug | 调试模式展示识别文字 | 编辑、重说、确认发送 |
| failed | 识别失败 | 重说、取消或请大人检查 |
| permission_needed | 需要麦克风权限 | 请求权限或请大人打开 |

---

## 4. Opening Greeting Strategy

App 打开儿童聊天页后，小白狐应主动发起一次短 opening greeting，让孩子看到小白狐已经准备好，而不是空白等待。

```text
ChildChatScreen 首次可见
  -> Android 每个 session 请求一次 POST /api/v1/conversation/opening
  -> 后端基于 child_id、session_id、deviceTime、timezone、父母寄语和称呼生成短句
  -> 可选生成 reply.audio_url
  -> Android 作为第一条 agent message 展示，并按现有 audioUrl 规则播放
```

称呼策略：

```text
1. 优先 `ParentPolicy.child_nickname`。
2. 其次 `ParentPolicy.child_display_name`。
3. 两者都没有时不强行称呼。
4. 不从父母寄语里猜真实姓名，不把父母寄语原文暴露给儿童。
```

交互原则：

```text
1. opening 只是一句或两句短、低刺激、适合朗读的话。
2. 不像老师点名，不查岗，不固定问“今天在学校怎么样”。
3. 晚上使用更轻的语气；刚放学可以欢迎回来，但不强迫汇报。
4. 同一个 ChatViewModel session 只请求一次。
5. 如果孩子在 opening 返回前已经开始说话，Android 丢弃 opening，孩子主动输入优先。
6. opening TTS 失败不影响文本展示，也不阻塞语音按钮。
```

---

## 5. Backend And Android TTS Strategy

```text
1. 正式小白狐音色主路径改为后端 MiMo VoiceClone 生成音频。
2. Android 收到 `reply.audio_url` 时优先播放远程音频。
3. 必须提供停止当前朗读的控制。
4. 必须提供静音或关闭自动朗读的开关。
5. 自动朗读开关必须可放在 DevSettings 或父亲设置中；进入家庭内测前优先收敛到父亲可治理。
6. 如果 reply.voice_enabled=false，则不自动朗读。
7. 如果 reply.audio_url 为空或播放失败，Android 只保留文字和温和提示，不使用本地系统 TTS 混播儿童端自动朗读；系统 TTS 只作诊断和未来评估背景，不作为正式品牌音色。
8. TTS 文本必须使用后端已规整、经过输出安全检查的 voice-first 短句回复。
9. 高风险安全回复可以生成语音，但 emotion 使用 safety，语气稳定、温和，不做戏剧化刺激表现。
10. TTS 能力必须封装在 TtsController / AudioUrlPlayer，UI 不直接依赖 TextToSpeech 或 MediaPlayer。
11. Android 不直接调用 MiMo，不存 MiMo API key。
```

实现状态（2026-05-20）：

```text
1. Android 已新增 TtsController / RemoteAudioTtsController / AudioUrlPlayer / AndroidTtsController / TtsUiState / VoiceProfile。
2. ChatViewModel 在 agent reply 到达后，根据 reply.voice_enabled、AUTO_TTS_ENABLED 和静音状态决定是否自动朗读。
3. TTS 请求被接受后先进入 speaking pending / speaking 视觉反馈，不再完全依赖系统 onStart 回调。
4. 朗读结束或停止后恢复后端 reply 对应的 base mood / motion。
5. UI 提供停止、静音和短状态提示；开发构建可显示 TTS 诊断文本。本轮 Android TTS/phase closeout 已保证 voice-first 下 TTS pending/speaking 时显示“停一下”和“静音/打开朗读”；停止走现有 stop path 并清空当前播放/segment queue，静音阻止后续自动朗读。
6. TtsUiState / VoiceDiagnostics 记录 isInitializing、isInitialized、enginePackageName、selectedLocale、selectedVoiceName、setLanguageResult、setVoiceResult、lastSpeakResult 和 lastFailureReason。
7. 系统 TTS 不可用时显示“我现在不能朗读，但文字还在这里。”并降级为文字。
8. 后端已新增 `POST /api/v1/tts/xiaobaohu`，可返回本地缓存 wav 的 `/media/tts/...` URL；当前测试阶段应验证目标 TTS provider。
9. 后端 MiMo VoiceClone provider 已隔离在 provider 层，必须通过 TtsDataPolicyGuard 才允许外发儿童相关文本；进入测试范围后应显式启用验证。
10. Android Manifest 已声明 TTS service 查询，避免 Android 11+ package visibility 影响引擎发现。
11. AndroidTtsController 已修复 TextToSpeech 初始化回调早于字段赋值时的误判风险。
12. TTS 不可用时 UI 提供“检查朗读设置”和“安装语音数据”入口，便于 Redmi K60 复测。
13. 真实 MiMo VoiceClone smoke 已通过：`/api/v1/tts/xiaobaohu` 返回 `/media/tts/...wav`，conversation 在 `CHILD_AI_CONVERSATION_TTS_ENABLED=true` 时可自动返回 `reply.audio_url`。
14. Android 已实现 remote audioUrl 优先播放：`reply.audio_url` 非空时先播放后端 WAV，失败时保留文字和温和错误提示，不再 fallback 到系统 TextToSpeech。
15. 真实设备听感、远程音频播放、停止/静音按钮可发现性、延迟和 Honor Pad 5 低配表现仍需 QA；不应把本轮写成语音体验全部完成。
16. Redmi K60 真机已听到 MiMo 小白狐音频，但同步等待时间仍长；下一阶段不能继续靠提高 read timeout，需进入文本流式和 TTS 分句/分段播放设计。
17. Task 07 已增加 TTS latency observability：非 stream `/conversation/message` 日志记录 `conversation_turn_latency`，包含 `request_id`、`request_start`、`model_ms`、`tts_ms`、`audio_url_present`、`turn_total_ms`；stream 日志记录 `conversation_stream_finished`，包含 `request_start`、`first_text_ms`、`tts_started_ms`、`first_audio_ms`、`turn_total_ms`。Android logcat 使用 `XiaobaohuTtsTiming` 记录 remote audio URL received / playback started / done / error，包含 request_id、turn_id、segment_index、elapsed_ms，不显示给儿童。
```

### 5.3 Streaming Voice Direction

当前同步语音链路：

```text
child input -> wait full LLM reply -> wait full MiMo TTS audio -> return audioUrl -> Android play
```

下一阶段目标：

```text
child input
  -> stream text_delta
  -> sentence/chunk ready
  -> TTS segment generation
  -> audio_ready event
  -> Android audio segment queue playback
```

原则：

```text
1. 先确认 MiMo VoiceClone 是否支持 true streaming；不要假设一定支持。
2. 如果不支持 true streaming，先做 sentence-level pseudo streaming。
3. TTS 失败不能中断文本流。
4. 高风险、安全、隐私、学习和睡前边界仍由后端安全链路控制。
5. QA 必须记录 first_text_ms、first_audio_ms、total_turn_ms 和 audio segment gap。
```

### 5.0 Redmi K60 Real Device Feedback

父亲 / 产品负责人已在 Redmi K60 / Android 14 / 中国大陆环境测试当前版本，反馈如下：

```text
1. 语音输入当时不可用：旧 APK 反馈已归档；当前 Android ASR v1 已接录音上传、后端 `/api/v1/asr/transcribe` 和儿童默认自动发送，确认面板仅保留为调试模式，仍需新 APK 真机复验。
2. TTS 播报不可用：没有声音、没有停止/静音提示、小白狐没有切 speaking。
3. 手机系统里有 TTS / 文字转语音相关服务，但声音不好，不适合孩子作为最终产品音色。
4. 截图中诊断为 `speak=SKIPPED_UNAVAILABLE`、`failure=TextToSpeech is unavailable`，说明上一版在调用 speak 前已经判定平台 TTS 不可用。
```

判断：

```text
1. 这不是单纯“系统音色不好”，而是 TTS 链路不可观测。
2. 必须先确认 AndroidTtsController 是否 attach、reply.voice_enabled 是否为 true、AUTO_TTS 是否开启、speak() 是否被调用、onInit / setLanguage / setVoice / speak 返回什么。
3. 小白狐 speaking 状态必须在请求被接受时先有反馈，不能只依赖系统 onStart。
4. 修通可观测链路后，再决定是否继续依赖系统 TTS。
5. 新 APK 复测时优先观察是否出现 engine、locale、lang、setVoice、speak 的具体值；如果仍是 SKIPPED_UNAVAILABLE，先进入系统朗读设置或安装语音数据。
```

TTS-D1 诊断字段：

| 字段 | 用途 |
|---|---|
| `isAutoReadEnabled` | 判断自动朗读开关 |
| `isMuted` | 判断 UI 静音状态 |
| `isAvailable` | 判断当前 TTS 是否可用 |
| `isInitializing` / `isInitialized` | 判断 TextToSpeech 初始化状态 |
| `isSpeaking` / `isSpeakingPending` | 区分系统开始朗读与已接受请求但等待回调 |
| `lastRequestedTextPreview` | 确认是否有文本进入 TTS，不保存完整长文本 |
| `lastFailureReason` | 记录失败原因 |
| `selectedLocale` / `selectedVoiceName` | 记录语言和 voice 选择 |
| `setLanguageResult` / `setVoiceResult` | 记录平台 API 返回 |
| `lastSpeakResult` | 记录 `TextToSpeech.speak()` 返回 `SUCCESS` / `ERROR` |
| `enginePackageName` | 记录系统 TTS 引擎 |

### 5.1 VoiceProfile v1

`VoiceProfile` 保留为 Android 平台 TTS 诊断和未来评估配置，不再作为儿童端自动朗读 fallback 的产品路径。正式主路径由后端 MiMo VoiceClone 生成音频。

| 字段 | v1 默认 |
|---|---|
| `preferredVoiceName` | 优先选择可用的中文系统 voice；找不到时为空并只记录诊断 |
| `locale` | `zh-CN` |
| `speechRate` | 稍慢，便于 8 岁儿童听清 |
| `pitch` | 略高但不过度，目标是干净、清脆、中性、活泼可爱，不做尖锐或过度幼稚音色 |
| `fallbackVoice` | 系统默认中文 voice 诊断字段；儿童端自动朗读不可用时只显示文字 |

音色方向：

```text
1. 小孩子般干净、清脆、中性、活泼可爱。
2. 不过度尖锐、不婴儿化、不做夸张动画配音腔。
3. 睡前场景可降低语速和刺激感。
4. 高风险安全回复保持稳定、温和，不使用戏剧化情绪音色。
5. 系统 TTS 不承诺固定专属音色；如果平台 TTS 效果不好，只记录诊断，不顶替小白狐自动朗读。
```

### 4.2 MiMo VoiceClone Little White Fox Voice

父亲 / 产品负责人已通过 MiMo Studio 生成并下载一段满意的小白狐音色样本：

```text
backend/assets/voices/xiaobaohu_voice_v01.wav
```

模型分工：

```text
1. MiMo-V2.5-TTS-VoiceDesign：
   只用于前期设计和筛选“小白狐”角色音色；当前已完成，不作为 App runtime。

2. MiMo-V2.5-TTS-VoiceClone：
   作为正式 App 接入时的小白狐主音色方案；后端使用 v01 wav 样本和安全规整后的回复文本生成音频。

3. MiMo-V2.5-TTS：
   只作为临时测试、内置音色对照或兜底方案，不作为正式品牌音色。
```

后端接口：

```http
POST /api/v1/tts/xiaobaohu
```

当前 MiMo VoiceClone provider 适配（2026-05-20 smoke 验证）：

```text
1. Endpoint：`/chat/completions`，不是 `/audio/speech`。
2. 鉴权仍使用 OpenAI-compatible `Authorization: Bearer <key>`，key 只来自本地 `.env` 或 shell env。
3. 请求体包含 `messages` 和 top-level `audio`；`audio.voice` 使用 `data:audio/wav;base64,...` voice sample。
4. 返回音频优先读取 `choices[0].message.audio.data`。
5. 已用 `scripts/smoke_mimo_tts.sh` 验证真实 `/api/v1/tts/xiaobaohu` 和 conversation 自动 `reply.audio_url`。
6. voice sample sha256：`8eec0f98629350a1dd09bd98a31c2bee80132128bf214d4c0a009331c9a66c40`。
```

核心约束：

```text
1. 显式设置 `CHILD_AI_TTS_PROVIDER` 以验证目标 TTS provider；测试 double 不能作为真实音频验收。
2. MiMo VoiceClone 必须显式设置 enabled、API key、allow child text 和 retention policy checked。
3. TTS text 可能包含儿童上下文、学习内容或个性化对话，因此按儿童相关文本处理。
4. Android 不直接调用 MiMo，不存 MiMo API key。
5. 生成音频缓存到 backend/storage/tts_cache，缓存文件不进 git。
6. `/media/tts/...wav` 只暴露生成音频，不暴露 voice sample 或 metadata json。
7. 缓存 metadata 不保存完整儿童文本，只保存 text hash、provider、model、voice sample hash 和生成信息。
8. conversation 自动生成 audioUrl 默认为关闭；TTS 失败时 conversation 仍返回文字。
```

固定声音风格提示词：

```text
小白狐 AI 伙伴的角色声音。语气清亮、轻快、灵动、亲近，像一只聪明的小白狐在陪孩子学习。说话有微笑感，尾音轻轻上扬，节奏自然活泼，不要沉闷，不要成人化，不要像老师讲课，不要播音腔，不要客服感。遇到孩子答错时轻轻安慰，答对时开心表扬，提示时像发现了一个小线索。
```

emotion 映射：

| Emotion | 语气 |
|---|---|
| encourage | 轻快、温暖、鼓励，像看到孩子刚刚完成了一小步 |
| comfort | 轻声、耐心、安慰，语速稍慢，像陪孩子慢慢平静下来 |
| hint | 俏皮、聪明、像发现了一个小线索，但不要吊胃口 |
| explain | 清楚、自然、轻快，不像老师讲课，不要播音腔 |
| happy | 开心、有微笑感，尾音轻轻上扬，但不要尖叫或过度兴奋 |
| calm | 安静、柔和、低刺激，适合睡前或孩子不想说话时 |
| safety | 稳定、认真、温和，不恐吓孩子，不戏剧化 |
| privacy | 温和但清晰，像提醒孩子先停一下，不责备 |

### 4.3 Future Dedicated Little White Fox Voice

Android system TextToSpeech 只是 fallback 和诊断能力，不作为最终儿童产品音色承诺。Redmi K60 反馈已经说明系统 TTS 即使可用，也可能声音不适合孩子。当前正式方向已调整为 MiMo VoiceClone；仍保留以下候选方向用于后续评估。

后续候选方向：

```text
1. 更换设备系统 TTS 引擎。
2. 使用可离线的中文 TTS 引擎。
3. 使用本地轻量 TTS 模型。
4. 使用后端 TTS 服务。
5. 使用第三方云 TTS 定制小白狐音色。
```

约束：

```text
1. 不得在未确认前把儿童相关文本发送给第三方 TTS。
2. 如果使用云 TTS，必须新增 TTS data policy guard。
3. TTS 文本可能包含儿童上下文或学习内容，仍需按儿童数据处理。
4. 需要父亲确认供应商、留存策略、是否用于训练、是否可删除、费用和稳定性。
5. v1 先保证后端 VoiceClone 可受控生成、Android 可播放 audioUrl，并保留系统 TTS/文字降级。
```

---

## 5. 小白狐 Presentation Coordination

语音和小白狐表现需要一致，但不互相阻塞：

```text
1. 正式名称统一为“小白狐”。
2. 代码 class 名 FoxAgent 暂可保留；如要重命名，后续单独 refactor。
3. 视觉目标优先 3D / soft 3D / 毛绒感 / 立体绘本感。
4. Compose Canvas / 2D 形象只是 fallback，不阻塞语音输入和 TTS 开发。
5. TTS 播放时，小白狐进入 speaking 状态；停止、结束或静音后恢复后端 reply 对应的基础状态。
6. 小白狐表现层不得制造“唯一朋友”“只有我懂你”等依赖感。
```

---

## 6. Backend Audio Interface Policy

当前已经新增后端 TTS 输出接口和受控 ASR 上传接口；ASR 上传只处理一次性短音频，不长期保存原始儿童音频。

后端当前继续负责：

```text
1. 接收儿童端发送的文本消息；语音默认由 Android 自动发送 ASR transcript，调试模式可先确认。
2. 通过 SafetyEngine、IntentClassifier、SceneOrchestrator、PromptManager、ModelRegistry 和 ChildAgentRuntime 生成安全回复。
3. 返回 reply.voice_enabled、reply.audio_url、reply.emotion、reply.agent_motion。
4. 通过 `POST /api/v1/tts/xiaobaohu` 按需生成小白狐语音音频。
5. 保持音频和儿童相关文本外发 gate；真实 provider 只有在本轮测试目标和 policy 条件满足时才接收 child text 或 child audio。
```

ASR 研究后的后端边界：

```text
1. `/api/v1/asr/transcribe` 已挂载；本地 SenseVoice 是当前 ASR 主路径，真实 MiMo ASR 外发必须满足父亲授权和 ASR policy flags。
2. `/api/v1/asr/transcribe` 只返回 transcript / status / provider metadata；是否自动发送由 Android DevSettings 控制，ASR endpoint 本身不直接调用 conversation runtime。
3. 自动发送后的 transcript 必须走 conversation message/stream，不得绕过 SafetyEngine、IntentClassifier、SceneOrchestrator、PromptManager 或 ModelRegistry。
4. 原始音频 base64 不写日志、不写数据库、不进入 memory、不写测试 fixture。
5. 真实 provider 需要独立 AsrDataPolicyGuard；MiMo TTS 的 child text 许可不能自动等同于 child audio 许可。
```

只有满足以下条件时，才考虑后端音频上传或云端 ASR：

```text
1. 父亲 / 产品负责人明确确认。
2. 更新 PRODUCT_DECISIONS。
3. 完成儿童音频数据、外发模型、retention policy 和删除策略 review。
4. 新增 API schema、测试和 QA 验收。
5. 默认仍不得长期保存原始音频。
```

当前 TTS 输出接口约束：

```text
1. 只处理后端已生成并经过安全规整的小白狐回复文本。
2. text 默认不超过 300 个汉字或配置的最大长度。
3. emotion 和 voiceVersion 使用白名单。
4. 测试阶段应验证目标 TTS provider；MiMo VoiceClone 必须显式通过 TtsDataPolicyGuard。
5. TTS endpoint 失败不应导致 conversation API 失败；最多返回 audio_url=null。
6. 生成音频缓存可本地保存，但缓存目录忽略 git，metadata 不保存完整儿童文本。
```

---

## 7. Raw Audio Storage Policy

```text
1. Android 不长期保存原始音频。
2. 后端默认不接收原始音频。
3. 日志、测试、fixture 不写入真实儿童语音内容或真实身份信息。
4. 结构化记忆只能保存必要的摘要型观察，不保存原始音频、长篇逐字转写或可识别家庭隐私。
5. 临时识别文本只有在用户确认发送后，才作为普通 conversation text 进入后端。
```

---

## 8. Permission Strategy

```text
1. 只有用户主动点击语音输入时才请求 RECORD_AUDIO。
2. 权限说明使用中性、可理解文案，不制造焦虑。
3. 权限拒绝后提示请大人打开麦克风；开发/父亲模式仍可打开文字输入。
4. 不在后台录音。
5. 不做常开麦克风或唤醒词监听。
```

推荐权限文案：

```text
需要麦克风权限，才能听懂你说的话。我们只在你按下语音按钮后听。
```

---

## 9. Child-Facing Error Copy

| 场景 | 文案 |
|---|---|
| 识别失败 | 我刚才没听清，可以再说一次。 |
| 环境太吵 | 周围有点吵，我可能听不准。我们可以短一点再说一遍。 |
| 无网络或后端 ASR 不可用 | 我现在还不能听懂声音，我们先请大人检查一下。 |
| 麦克风权限拒绝 | 没有麦克风权限，我们可以请大人打开。 |
| 调试模式识别文本待确认 | 我先把听到的话写出来，你看一看对不对，再决定要不要发送。 |
| TTS 不可用 | 我现在不能朗读，但文字还在这里。 |
| 自动朗读已静音 | 好的，我先不出声，文字还在这里。 |

文案禁区：

```text
1. 不说“你必须开麦克风”。
2. 不要求孩子偷偷授权或避开父母。
3. 不暗示 AI 会一直听着孩子。
4. 不用失败、笨、你说错了等责备表达。
```

---

## 10. Child Safety Boundaries

```text
1. 语音体验不得制造“唯一朋友”“只有我懂你”等依赖感。
2. 学习求助仍不直接给最终答案，要先引导读题、拆题和说思路。
3. 高风险输入要鼓励告诉父母、老师或可信成人，并触发父亲提醒。
4. 不要求孩子保密，不鼓励隐瞒父母。
5. 不保存原始音频、真实照片或长篇逐字聊天原文到长期记忆。
6. 不做常开麦克风、后台录音、陌生人社交、排行榜、连击奖励或上瘾式语音反馈。
```

---

## 11. QA Checklist

全部 QA 使用虚构 child_id、虚构输入，不使用真实儿童身份、真实家庭信息、真实照片或真实音频。

### 11.1 双设备测试策略

| 设备 | 定位 | 用途 |
|---|---|---|
| Device A：Redmi K60，Android 14 | 功能主验证 | 快速验证后端 ASR 录音上传、默认自动发送、opening greeting、远程 audioUrl 播放、小白狐状态切换、图片资源和轻量动画、真实模型对话体验和异常兜底路径，以及自由聊天、学习求助、直接要答案、安全场景、隐私边界和父亲入口保护等核心流程 |
| Device B：Honor Pad 5，Android 9，RAM 4GB | 低配兼容性目标设备 | 验证 Android 9 兼容性、4GB 内存性能、平板横屏/大屏 UI、儿童真实使用尺寸、后端 ASR 自动发送、opening greeting、远程 TTS 播放、小白狐资源大小、动画流畅度、发热和卡顿 |

执行顺序：

```text
1. V1 语音输入先在 Device A 跑通点击语音 -> 录音 -> 上传后端 ASR -> 自动发送 transcript -> conversation stream；DevSettings 确认模式单独验证。
2. 再在 Honor Pad 5 验证权限申请、录音格式、中文识别、儿童声音识别、延迟、失败提示和是否可接受。
3. V2 TTS 先在 Device A 跑通 `reply.audio_url` 远程音频播放、默认自动朗读、停止、关闭和失败时保留文字提示。
4. 再在 Honor Pad 5 验证远程 wav 播放、缓存音频体积、播放延迟、是否卡顿，以及是否需要关闭自动朗读作为低配默认。
5. 如果 Honor Pad 5 语音效果不好，允许降级为文字优先，但必须记录结果和降级原因。
```

每条语音 QA 记录必须包含：

```text
设备型号
Android 版本
是否通过
延迟
是否卡顿
ASR 准确率主观评价
TTS 自然度主观评价
是否需要降级
```

| ID | 场景 | 期望 |
|---|---|---|
| VQA-01 | 首次点击语音输入 | 只在点击后请求麦克风权限，拒绝后请大人打开；儿童默认界面不显示文字输入框 |
| VQA-02 | 正常语音识别 | ASR ok 且 transcript 非空后自动发送 conversation stream，不展示可编辑确认面板 |
| VQA-03 | DevSettings 确认模式 | 打开 `VOICE_CONFIRM_BEFORE_SEND=true` 后，识别文本进入待确认面板，修改后的文本才发送 |
| VQA-04 | 取消或重说 | 不调用 conversation，不保存音频；可重新开始录音 |
| VQA-05 | 识别失败 | 显示温和失败文案，可重说或请大人检查，不自动发送 |
| VQA-06 | 后端断开 | ASR 或发送失败时温和提示请大人检查网络，不把失败 transcript 加入对话 |
| VQA-07 | 学习求助语音 | 回复仍不直接给答案，先引导题意和步骤 |
| VQA-08 | 高风险语音文本 | 确认发送后进入安全场景，鼓励告诉可信成人并触发父亲提醒 |
| VQA-09 | TTS 默认自动朗读 | 默认自动朗读小白狐回复，只朗读后端安全回复，不朗读内部 debug 或 session_state |
| VQA-10 | 停止和静音 | voice-first 下 TTS pending/speaking 时可见“停一下”和“静音/打开朗读”；停止当前朗读并清空 segment queue，静音阻止后续自动朗读，仍需 Redmi K60 / Honor Pad 5 真机确认 |
| VQA-11 | VoiceProfile | 使用 zh-CN、稍慢语速、略高但不过度 pitch；找不到 preferred voice 时 fallback 系统默认中文 voice |
| VQA-12 | 抽象边界 | UI 通过 VoiceEngine / SpeechInputController / TtsController 使用语音能力，不直接散落平台调用 |
| VQA-13 | 数据检查 | 日志、memory、fixture 中没有原始音频、真实身份或长篇逐字转写 |
| VQA-14 | TTS 诊断可见 | Redmi K60 等真机上能看到朗读开启、正在准备、不可用或失败原因；开发诊断含 engine、locale、voice、speak 返回值 |
| VQA-15 | speaking pending | TTS 请求被接受后小白狐先切 speaking pending / speaking；失败或停止后恢复 base state，不一直卡住 |
| VQA-16 | 后端小白狐 TTS endpoint | `POST /api/v1/tts/xiaobaohu` 返回 `/media/tts/...wav`；当前 QA 应记录实际 provider；真实 MiMo smoke 已通过并下载 RIFF/WAV，policy 不满足时不得写成真实音频通过 |
| VQA-17 | Android remote audio 优先 | `reply.audio_url` 非空时优先播放远程音频；失败时保留文字和温和提示，不 fallback 到系统 TTS；代码已实现，待 Redmi K60 真机确认听感、网络播放和停止按钮可发现性 |
| VQA-18 | TTS 数据策略 | MiMo VoiceClone 未显式开启 allow child text 和 retention checked 时不能调用外部 provider |
| VQA-19 | Opening greeting | App 打开后小白狐请求一次 opening；有小名喊小名，有 display name 用 display name，都没有不强行称呼 |
| VQA-20 | Opening 不打断孩子 | 如果孩子先点击语音或发送文本，迟到的 opening 不插入、不覆盖孩子消息 |
| VQA-21 | TTS perceived latency breakdown | 记录一次慢 turn 的后端 `request_id`，同时抓 `app.conversation` / `app.stream_timing` / `app.tts_timing` 和 Android `XiaobaohuTtsTiming` logcat；用 `model_ms`、`tts_ms`、`first_text_ms`、`tts_started_ms`、`first_audio_ms`、`elapsed_ms` 区分模型、TTS 生成、stream audio_ready 和 Android 播放启动延迟 |
| VQA-22 | Task 09 login + opening v2 | 家长登录后进入儿童端；Ready 首屏不等待 opening/TTS，opening v2 可用账号画像/兴趣生成短句，退出登录后回到家长登录页 |

语音体验 QA 记录必须包含：

```text
1. 识别准确率。
2. 从点击语音到识别文本出现的延迟。
3. 中文普通话识别效果。
4. 儿童声音识别效果。
5. 后端 VoiceClone 的自然度；系统 TTS 不作为儿童端自动朗读 fallback 评分项。
6. 孩子接受度。
7. 如果觉得小白狐开口慢，记录 request_id、turn_id、backend timing 日志和 Android logcat；证据只保留 ID、耗时和状态，不记录儿童原文、完整回复、原始音频或完整 audio URL。
```
