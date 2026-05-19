# Voice Interaction Design v0.1

用途：定义儿童端语音输入、TTS 朗读、音频数据边界和 QA 验收清单。本文档区分已实现能力和待设备验收项；语音输入 ASR 仍未实现，TTS v1 已进入 Android 本地实现阶段。

关联决策：

```text
docs/PRODUCT_DECISIONS_V0_1.md
PD-002：语音第一阶段优先 Android 本地 SpeechRecognizer + Android TTS，不默认上传原始音频到后端。
PD-003：语音输入应先转文字确认，再发送给后端；不要误识别后自动直接进入 AI 回复。
PD-005：后端继续通过 reply.voice_enabled、reply.audio_url、reply.emotion、reply.agent_motion 暴露表现层信号。
PD-010：语音输入 v1 是 confirm-before-send，future hands-free conversational mode 不进入 v1。
PD-011：TTS v1 默认自动朗读小白狐回复，必须有停止/静音和 DevSettings 或父亲设置开关。
PD-014：SpeechRecognizer / TextToSpeech 必须通过 VoiceEngine / SpeechInputController / TtsController 抽象。
PD-017：小白狐音色方向是小孩子般干净、清脆、中性、活泼可爱，但不能过度尖锐或幼稚。
PD-018：采用双设备测试策略，高配 Android 手机先做功能主验证，Honor Pad 5 Android 9 / 4GB 做低配兼容性验证。
PD-021：Redmi K60 真机反馈显示 TTS 链路不可观测且无声，下一步优先修 TTS 诊断、UI 状态和 fallback。
PD-022：Android 系统 TTS 只是 v1 验证方案，不作为最终儿童产品音色承诺。
```

---

## 1. Scope

### 1.1 v0.1 Current Scope

```text
1. 后端已返回 reply.voice_enabled、reply.audio_url、reply.emotion、reply.agent_motion。
2. Android DTO 已解析这些字段，并已做小白狐轻量状态映射。
3. Android 语音输入入口仍是占位或后续入口，不录音、不调用真实 SpeechRecognizer。
4. Android TTS v1 已实现本地 TextToSpeech 抽象、默认自动朗读、停止/静音控制、VoiceProfile 和小白狐 speaking 状态联动；Redmi K60 真机反馈显示上一版无声且不可观测，因此 TTS-D1 优先补充诊断、UI 状态和降级。
5. mock 拍题和学习求助仍以文字和 mock OCR 为主。
```

### 1.2 v0.2 Voice Scope

```text
1. 语音输入 v1：Android 本地 SpeechRecognizer 把孩子语音转成文字。
2. 识别结果必须先展示为可确认文本，由孩子或父亲确认后再发送后端。
3. TTS 朗读 v1：Android 使用系统 TextToSpeech 默认自动朗读小白狐回复。
4. 后端暂不需要音频上传接口，不生成真实音频文件。
5. 后端继续只接收确认后的文本消息和必要的轻量 metadata。
6. Hands-free conversational mode 是 future，不进入 v1。
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
| SpeechInputController | 处理点击语音、监听、识别结果、取消、错误和 confirm-before-send 状态 | Android SpeechRecognizer wrapper |
| TtsController | 处理自动朗读、停止、静音、队列、错误和生命周期释放 | Android TextToSpeech wrapper |
| VoiceProfile | 管理语言、voice 名称、语速、音高和 fallback | zh-CN system voice profile |

---

## 3. Android Local Speech Recognition Strategy

```text
1. 第一阶段使用 Android 平台 SpeechRecognizer。
2. 语音识别只作为文字输入辅助，不改变后端统一 conversation API。
3. 识别结束后进入“待确认文本”状态，不自动调用 /conversation/message。
4. 用户可以编辑识别文本、重新说一遍、取消或确认发送。
5. 识别失败、噪声过大、超时或权限拒绝时，回到文字输入，不阻断主流程。
6. 不把原始音频写入本地长期存储，不上传原始音频到后端。
7. 识别能力必须封装在 SpeechInputController，UI 不直接依赖 SpeechRecognizer。
8. Hands-free conversational mode 不进入 v1；v1 必须保留确认按钮。
```

v1 流程：

```text
点击语音
  -> 孩子说话
  -> Android 本地 ASR
  -> 展示识别文本
  -> 孩子确认 / 可编辑 / 可重说 / 可取消
  -> 点击发送
  -> text 走 /api/v1/conversation/message
```

推荐状态：

| State | 说明 | 下一步 |
|---|---|---|
| idle | 默认文字输入 | 可点击语音按钮 |
| listening | 正在听 | 可取消 |
| recognizing | 系统识别中 | 等待结果 |
| confirm_text | 展示识别文字 | 编辑、重说、确认发送 |
| failed | 识别失败 | 重试或改用文字 |
| permission_needed | 需要麦克风权限 | 请求权限或回到文字 |

---

## 4. Android TTS Strategy

```text
1. 第一阶段使用 Android 系统 TextToSpeech。
2. v1 默认自动朗读小白狐回复，不绕过后端安全和场景编排。
3. 必须提供停止当前朗读的控制。
4. 必须提供静音或关闭自动朗读的开关。
5. 自动朗读开关必须可放在 DevSettings 或父亲设置中；进入家庭内测前优先收敛到父亲可治理。
6. 如果 reply.voice_enabled=false，则不自动朗读。
7. 如果 reply.audio_url 为空，Android 使用本地 TTS；如果未来有安全审核后的 audio_url，再单独确认播放策略。
8. TTS 文本应使用后端已规整的 voice-first 短句回复。
9. 高风险安全回复可以朗读，但语速和语气应稳定，不做戏剧化刺激表现。
10. TTS 能力必须封装在 TtsController，UI 不直接依赖 TextToSpeech。
```

实现状态（2026-05-19）：

```text
1. Android 已新增 TtsController / AndroidTtsController / TtsUiState / VoiceProfile。
2. ChatViewModel 在 agent reply 到达后，根据 reply.voice_enabled、AUTO_TTS_ENABLED 和静音状态决定是否自动朗读。
3. TTS 请求被接受后先进入 speaking pending / speaking 视觉反馈，不再完全依赖系统 onStart 回调。
4. 朗读结束或停止后恢复后端 reply 对应的 base mood / motion。
5. UI 提供停止、静音和短状态提示；开发构建可显示 TTS 诊断文本。
6. TtsUiState / VoiceDiagnostics 记录 isInitializing、isInitialized、enginePackageName、selectedLocale、selectedVoiceName、setLanguageResult、setVoiceResult、lastSpeakResult 和 lastFailureReason。
7. 系统 TTS 不可用时显示“我现在不能朗读，但文字还在这里。”并降级为文字。
8. 当前不生成、不保存任何音频文件，不接外部 TTS 服务。
9. 真实设备听感、中文 voice 可用性、延迟和 Honor Pad 5 低配表现仍需 QA。
10. Android Manifest 已声明 TTS service 查询，避免 Android 11+ package visibility 影响引擎发现。
11. AndroidTtsController 已修复 TextToSpeech 初始化回调早于字段赋值时的误判风险。
12. TTS 不可用时 UI 提供“检查朗读设置”和“安装语音数据”入口，便于 Redmi K60 复测。
```

### 4.0 Redmi K60 Real Device Feedback

父亲 / 产品负责人已在 Redmi K60 / Android 14 / 中国大陆环境测试当前版本，反馈如下：

```text
1. 语音输入不可用：符合当前状态，ASR / SpeechRecognizer 尚未实现。
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

### 4.1 VoiceProfile v1

`VoiceProfile` 用于集中管理小白狐 v1 的系统 TTS 调优。v1 不做小白狐专属音色；v2 再评估专属音色。

| 字段 | v1 默认 |
|---|---|
| `preferredVoiceName` | 优先选择可用的中文系统 voice；找不到时为空并走 fallback |
| `locale` | `zh-CN` |
| `speechRate` | 稍慢，便于 8 岁儿童听清 |
| `pitch` | 略高但不过度，目标是干净、清脆、中性、活泼可爱，不做尖锐或过度幼稚音色 |
| `fallbackVoice` | 系统默认中文 voice；仍不可用时只显示文字 |

音色方向：

```text
1. 小孩子般干净、清脆、中性、活泼可爱。
2. 不过度尖锐、不婴儿化、不做夸张动画配音腔。
3. 睡前场景可降低语速和刺激感。
4. 高风险安全回复保持稳定、温和，不使用戏剧化情绪音色。
5. v1 不承诺固定专属音色；如果系统 TTS 效果不好，记录 QA 并评估替换方案。
```

### 4.2 Future Dedicated Little White Fox Voice

Android system TextToSpeech 只是 v1 验证方案，不作为最终儿童产品音色承诺。Redmi K60 反馈已经说明系统 TTS 即使可用，也可能声音不适合孩子。

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
5. v1 仍先保证本地 TTS 链路可观测和可降级。
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

v0.2 前默认不新增后端音频接口。

后端当前继续负责：

```text
1. 接收确认后的文本消息。
2. 通过 SafetyEngine、IntentClassifier、SceneOrchestrator、PromptManager、ModelRegistry 和 ChildAgentRuntime 生成安全回复。
3. 返回 reply.voice_enabled、reply.audio_url、reply.emotion、reply.agent_motion。
4. 保持音频外发 gate 默认关闭，真实 provider 不默认接收 child audio。
```

只有满足以下条件时，才考虑后端音频上传或云端 ASR：

```text
1. 父亲 / 产品负责人明确确认。
2. 更新 PRODUCT_DECISIONS。
3. 完成儿童音频数据、外发模型、retention policy 和删除策略 review。
4. 新增 API schema、测试和 QA 验收。
5. 默认仍不得长期保存原始音频。
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
3. 权限拒绝后仍可继续使用文字输入。
4. 不在后台录音。
5. 不做常开麦克风或唤醒词监听。
```

推荐权限文案：

```text
需要麦克风权限，才能把你说的话先变成文字。你可以先看文字，确认后再发送。
```

---

## 9. Child-Facing Error Copy

| 场景 | 文案 |
|---|---|
| 识别失败 | 我刚才没听清。你可以再说一遍，也可以直接打字。 |
| 环境太吵 | 周围有点吵，我可能听不准。我们可以换成打字。 |
| 无网络但本地识别不可用 | 现在语音可能用不了，可以先打字，或者请大人帮忙看看网络。 |
| 麦克风权限拒绝 | 没关系，不开麦克风也可以打字聊天。 |
| 识别文本待确认 | 我先把听到的话写出来，你看一看对不对，再决定要不要发送。 |
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
| Device A：Redmi K60，Android 14 | 功能主验证 | 快速验证 SpeechRecognizer、TextToSpeech 自动朗读、小白狐状态切换、图片资源和轻量动画、真实模型/Mock 模型对话体验，以及自由聊天、学习求助、直接要答案、安全场景、隐私边界和父亲入口保护等核心流程 |
| Device B：Honor Pad 5，Android 9，RAM 4GB | 低配兼容性目标设备 | 验证 Android 9 兼容性、4GB 内存性能、平板横屏/大屏 UI、儿童真实使用尺寸、系统 ASR/TTS 可用性、小白狐资源大小、动画流畅度、发热和卡顿 |

执行顺序：

```text
1. V1 语音输入先在 Device A 跑通点击语音 -> 本地识别 -> 展示文字 -> 确认/编辑 -> 发送。
2. 再在 Honor Pad 5 验证权限申请、中文识别、儿童声音识别、延迟、失败提示和是否可接受。
3. V2 TTS 先在 Device A 跑通默认自动朗读、停止、关闭、VoiceProfile 调整。
4. 再在 Honor Pad 5 验证中文 TTS 是否存在、音色是否可接受、是否卡顿、是否延迟明显、是否需要关闭自动朗读作为低配默认。
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
| VQA-01 | 首次点击语音输入 | 只在点击后请求麦克风权限，拒绝后文字输入仍可用 |
| VQA-02 | 正常语音识别 | 先展示识别文本，不自动发送后端 |
| VQA-03 | 编辑识别文本 | 修改后的文本才发送到 `/conversation/message` |
| VQA-04 | 取消识别结果 | 不调用后端，不保存音频 |
| VQA-05 | 识别失败 | 显示温和失败文案，可重试或打字 |
| VQA-06 | 后端断开 | 语音转文字可停在待发送状态，发送失败时温和提示请大人检查网络 |
| VQA-07 | 学习求助语音 | 回复仍不直接给答案，先引导题意和步骤 |
| VQA-08 | 高风险语音文本 | 确认发送后进入安全场景，鼓励告诉可信成人并触发父亲提醒 |
| VQA-09 | TTS 默认自动朗读 | 默认自动朗读小白狐回复，只朗读后端安全回复，不朗读内部 debug 或 session_state |
| VQA-10 | 停止和静音 | 可停止当前朗读，可通过 DevSettings 或父亲设置关闭自动朗读 |
| VQA-11 | VoiceProfile | 使用 zh-CN、稍慢语速、略高但不过度 pitch；找不到 preferred voice 时 fallback 系统默认中文 voice |
| VQA-12 | 抽象边界 | UI 通过 VoiceEngine / SpeechInputController / TtsController 使用语音能力，不直接散落平台调用 |
| VQA-13 | 数据检查 | 日志、memory、fixture 中没有原始音频、真实身份或长篇逐字转写 |
| VQA-14 | TTS 诊断可见 | Redmi K60 等真机上能看到朗读开启、正在准备、不可用或失败原因；开发诊断含 engine、locale、voice、speak 返回值 |
| VQA-15 | speaking pending | TTS 请求被接受后小白狐先切 speaking pending / speaking；失败或停止后恢复 base state，不一直卡住 |

语音体验 QA 记录必须包含：

```text
1. 识别准确率。
2. 从点击语音到识别文本出现的延迟。
3. 中文普通话识别效果。
4. 儿童声音识别效果。
5. TTS 自然度。
6. 孩子接受度。
```
