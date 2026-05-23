# Android 平板端

本目录是儿童 AI 成长智能体的 Android 平板端。当前阶段已在 S11 / A1 静态壳和 S12 / A2 Conversation API 基础上接入 S13 / A3-A4 演示闭环。

当前 Android MVP 已完成儿童统一聊天、系统相机/相册真实图片上传、父亲设置/日报和父亲入口轻量保护。TTS 已接入远程 `reply.audio_url` 优先播放：后端 MiMo VoiceClone 音频可作为小白狐正式音色，Android 系统 TextToSpeech 保留为 fallback/诊断能力。Streaming v1 首版已接入 `/api/v1/conversation/stream`；语音输入 ASR v1 已接入录音、上传后端 ASR 和儿童默认自动发送，确认面板仅保留为 DevSettings / 父亲调试模式，仍待真机 QA。

## 当前范围

- 单一儿童聊天入口。
- 小白狐智能体形象占位，会根据后端 `reply.emotion` 和
  `reply.agent_motion` 做轻量状态变化。
- 儿童默认 voice-first 输入：主按钮用于开始说话 / 说完了 / 正在听懂；文字输入框和发送按钮默认隐藏，可通过 DevSettings 打开。
- 默认优先调用后端 `POST /api/v1/conversation/stream`；失败时 fallback 到 `POST /api/v1/conversation/message`。
- 渲染后端返回的 `reply.text` 和 `ui_actions` 快捷按钮；`session_state` 只保存在 UI state 中供续会话和开发排查使用，默认不展示给儿童。
- DTO 已解析 `reply.voice_enabled`、`reply.audio_url`、`reply.emotion` 和
  `reply.agent_motion`；当前 UI 已接入小白狐 `animation_v1` WebP 序列帧、旧静态 WebP 和 Canvas 三层 fallback。TTS v1 会默认自动朗读小白狐回复，优先播放后端远程音频，并在朗读时切到 speaking 状态。Stream audio segment 会进入队列顺序播放；语音输入 ASR 使用后端 `/api/v1/asr/transcribe`，儿童默认自动发送 transcript，调试模式才展示确认面板。
- “拍给小白狐看”默认调用 Android 系统相机或系统相册，压缩为 JPEG 后通过 multipart 上传后端 `/api/v1/attachments/images`；Android 不保存 MiMo key，不直接调用 MiMo。CameraX 自定义相机不是当前目标。
- 普通图片分享成功后，Android 会暂存图片摘要和 `attachment_id`。孩子点击“聊聊它 / 编个故事 / 问这是什么”时，会把图片上下文和 `attachment_id` 一起发送给后端，让小白狐围绕刚才那张图继续聊。
- 父亲设置页可读取和保存孩子小名 / 显示名、父母寄语、目标、沟通偏好、放学后/作业/睡前时间段。小白狐 opening greeting 优先使用小名，没有小名时使用显示名，都没有时不强行称呼。
- 父亲日报页读取后端 `GET /api/v1/parent/reports/{child_id}` 只读摘要。
- 儿童聊天页中的父亲设置和父亲日报入口使用轻量误触保护：点击只提示，长按后输入开发 PIN 才进入。
- 使用内存保存当前 `session_id` 和最新 `session_state`。
- 当前产品方向是 freedom-first：儿童端默认让孩子自由说；时段、父母寄语、记忆和图片能力作为上下文或工具，安全、隐私、学习和睡前边界由后端按需介入。

## Freedom-first 第二轮收口

当前 Android 行为：

```text
1. 父母寄语可在父亲设置页编辑；后端会在 PostgreSQL 可用时持久化，数据库不可用时 dev fallback 到内存。
2. 孩子小名 / 显示名可在父亲设置页编辑；不要强制填写真实全名。
3. 父母寄语不会出现在儿童聊天 UI 或 session_state debug 中。
4. 普通图片上传失败文案使用“图片”，作业图片失败文案才使用“题目”。
5. 普通图片后续快捷动作会带上 pendingImageContext；后端缺失时不崩溃。
6. “拍给小白狐看”是默认图片入口；旧 mock attachment 不作为儿童端默认路径。
```

待 Redmi K60 手动 QA：

```text
1. 使用系统相机拍摄非儿童测试图片 -> 上传成功后返回真实 `attachment_id`。
2. 分享积木/玩具图片 -> 点击“聊聊它”后，小白狐继续围绕图片聊，不进入作业。
3. 分享图片 -> 点击“编个故事”后，小白狐基于后端 MiMo vision 摘要编故事。
4. 后端缺 key、`allow_image` 未开或 provider 失败时，儿童端显示失败，不假装看到了。
5. 断开后端时，普通图片和作业图片分别显示正确失败文案。
```

## 下一阶段语音和小白狐方向

已确认方向：

- 语音输入 ASR v1 目标已修订为后端本地 SenseVoice ASR 优先，MiMo audio input / ASR 作为本地异常后的云端 fallback。
- Android 不直接调用 MiMo，不保存 MiMo API key，也不持有本地 ASR 模型；Android 只负责点击录音、上传后端 ASR 和儿童端语音状态。
- 语音输入 v1 儿童默认流程：点击语音 -> 孩子说话 -> Android 上传短音频到后端 ASR -> ASR ok 自动发送 transcript -> text 走 conversation stream；confirm-before-send 仅保留为 DevSettings / 父亲调试模式。
- Future hands-free conversational mode 不进入 v1。
- 自动发送后的文本继续调用 conversation API；如果 streaming enabled，优先走 `/api/v1/conversation/stream`。
- 原始音频只作为一次性 ASR 请求数据，不长期保存、不写日志、不入库；开发阶段只用 fake/smoke audio 或非儿童测试音频做 ASR smoke，不用真实儿童录音。
- 当前 Android 已实现 `RECORD_AUDIO` 点击触发、短 WAV 录音、最长 30 秒自动停止、上传后端 ASR、默认自动发送、重说/取消；pending transcript 编辑面板仅在 `VOICE_CONFIRM_BEFORE_SEND=true` 时展示。
- App 打开儿童聊天页后会请求 `POST /api/v1/conversation/opening`，把 opening greeting 作为第一条小白狐消息展示；后端默认不为了 opening 冷启动远程 TTS 而阻塞首屏，如果返回 `audio_url` 才自动播放。孩子先开口时，迟到的 opening 不插入。
- opening greeting 的称呼来自父亲设置页的孩子小名 / 显示名：小名优先，其次显示名；都为空时不强行称呼。
- TTS 朗读优先播放后端返回的 `reply.audio_url`，朗读后端已安全处理的 `reply.text` 对应音频；普通完整回复远程播放失败时可 fallback 到系统 TextToSpeech 或文字，但 stream 分段 TTS 失败不再混用系统音色朗读同一段。
- TTS 已有停止/静音控制，并受 `DevSettings.AUTO_TTS_ENABLED` / `DevSettings.TTS_MUTED` 初始配置治理；`DevSettings.SHOW_TTS_DIAGNOSTICS` 用于开发构建显示 engine、locale、voice、speak 返回值和失败原因。
- TTS 不可用时 UI 会显示温和文字提示，并提供“检查朗读设置”和“安装语音数据”入口；文字聊天不受影响。
- TTS fallback 已实现 `VoiceProfile`：`preferredVoiceName`、`zh-CN`、稍慢 `speechRate`、偏高但不过度的 `pitch`、fallback 系统默认中文 voice。
- Redmi K60 / Android 14 反馈说明系统 TTS 即使可用，声音也可能不适合孩子；Android system TTS 只作为 fallback 和诊断能力，不作为最终音色承诺。
- Android 不直接调用 MiMo，不保存 MiMo API key；正式音频由后端 `/api/v1/tts/xiaobaohu` 生成并通过 `/media/tts/...wav` 返回。后端真实 MiMo VoiceClone smoke 已通过，Android 已接入 `reply.audio_url` 远程播放优先级。
- Redmi K60 当前复测重点：确认 Android 是否请求 `/media/tts/...wav`、是否能听到 MiMo 小白狐音色、停止/静音是否生效；如果远程播放失败，再检查系统 TTS fallback 的 `lang` / `setVoice` / `speak` 诊断。
- Android 可以使用平台录音 / `TextToSpeech`，但必须通过可替换抽象：`VoiceEngine` / `SpeechInputController` / `TtsController`。
- 小白狐形象应温和、好奇、活泼开朗，视觉目标优先 3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感；Compose Canvas / 2D 只是 fallback，不阻塞语音开发。
- 小白狐 v1 候选资源已导入，当前包含 11 个状态：`neutral_idle`、`listening`、`speaking`、`jumping_happy`、`thinking`、`calm`、`sleepy`、`safety_concern`、`privacy_boundary`、`homework_focus`、`network_error`。
- Android 第一版优先预渲染 3D PNG/WebP 状态图 + 本地 WebP 序列帧轻量播放，不引入实时 3D 引擎或大型动画依赖作为必需能力。
- 小白狐动态序列帧放在 `android/app/src/main/assets/mascot/xiaobaohu/v1/`，由 manifest-driven loader 读取；旧静态 fallback 已压缩为 WebP 并保留在 `android/app/src/main/res/drawable-nodpi/`。
- `FoxAgentAssetMapper` 负责把 `FoxAgentUiState` / `FoxMood` / `FoxMotion` 映射到 drawable 或 Canvas fallback。
- `DevSettings.FOX_RENDER_MODE` 当前支持 `animation_v1` / `png_static` / `canvas` / `auto` 语义；`png_static` 是兼容旧模式名，实际静态资源已压缩为 WebP；低配设备可强制 Canvas 或静态状态。
- TTS speaking 会优先映射到 animation_v1 的 `speaking` 序列帧；朗读结束或停止后恢复后端 reply 对应的基础状态。
- UI、产品、设计和测试说明统一称为“小白狐”；代码 class 名 `FoxAgent` 暂可保留，后续如要改代码命名单独 refactor。
- 小白狐表现层不得制造“唯一朋友”“只有我懂你”等依赖感，不做排行榜、连击奖励或上瘾式动画。
- 小白狐音色方向是小孩子般干净、清脆、中性、活泼可爱，但不能过度尖锐或幼稚；当前正式方向是后端 MiMo VoiceClone v01，系统 TTS 只做 fallback。
- QA 需要记录识别准确率、延迟、中文效果、儿童声音识别、TTS 自然度、孩子接受度、小白狐动画流畅度和是否需要降级。

## Streaming v1 Client

当前实现：

```text
1. `DevSettings.USE_STREAMING_CONVERSATION=true` 时，ChatViewModel 优先走 `/api/v1/conversation/stream`。
2. Android 逐行解析 NDJSON event。
3. `text_delta` 追加到当前小白狐消息气泡。
4. `text_final` 修正最终文本。
5. `audio_ready` 进入 AudioSegmentQueuePlayer，顺序播放远程音频 segment。
6. 静音时不播放 audio segment，也不 fallback 系统 TTS。
7. 单个 stream TTS segment 失败时，只保留文字并继续后续 segment，不用系统 TTS 混播失败段。
8. 停止朗读会停止当前 segment 并清空队列。
9. stream 失败时 fallback 到旧 `/conversation/message`。
```

待手动 QA：

```text
1. Redmi K60：普通聊天能看到渐进文字，不出现重复 agent bubble。
2. Redmi K60：MiMo TTS segment 能按顺序播放，小白狐切 speaking，停止/静音生效。
3. 后端断开或 stream 中断：已显示文本不被清空，旧接口 fallback 或温和错误可见。
4. Honor Pad 5：横屏双栏、animation_v1 和 stream 更新同时运行不卡顿；必要时记录低性能降级。
```

详细设计见：

- `docs/PRODUCT_DECISIONS_V0_1.md`
- `docs/VOICE_INTERACTION_DESIGN_V0_1.md`
- `docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md`
- `docs/NEXT_PHASE_PLAN_V0_2.md`

## 小白狐 animation_v1 序列帧资源

父亲 / 产品负责人已提供完整小白狐动态资源包。当前 Android 运行时必要文件已经导入：

```text
android/app/src/main/assets/mascot/xiaobaohu/v1/
```

导入内容：

```text
mascot_manifest.json
每个状态目录下的 manifest.json
每个状态目录下的 frames_webp/*.webp
```

当前没有把验收全量包、PNG frames、preview html、gif/webp 预览和 spritesheet 调试资料作为运行时依赖。完整资源记录见：

```text
docs/assets/fox/animation_v1/README.md
```

manifest 当前声明 11 个状态，均为 24 帧、12 FPS：

```text
safety_concern
privacy_boundary
network_error
speaking
thinking
listening
homework_focus
calm
sleepy
jumping_happy
idle
```

渲染策略：

```text
1. `animation_v1`：优先使用 manifest + WebP frames 播放。
2. `png_static`：animation manifest 或 frames 失败时使用旧静态 WebP fallback。
3. `canvas`：静态资源也不可用或低性能模式时使用 Compose Canvas fallback。
```

相关开关：

```kotlin
DevSettings.FOX_RENDER_MODE = "animation_v1"
DevSettings.FOX_ANIMATION_ENABLED = true
DevSettings.FOX_ANIMATION_LOW_PERFORMANCE_MODE = false
DevSettings.SHOW_MASCOT_DEBUG_SWITCHER = false
```

当前 animation_v1 runtime assets 约 4.9MB，采用 512px WebP sequence；静态 drawable fallback 约 1.5MB，也已压缩为 WebP。验收全量包只作为美术源包、QA 留档和重新导出母包，不应整体放入 App。Redmi K60 作为功能主验证设备，Honor Pad 5 Android 9 / 4GB 作为低配性能和降级验证设备。

最新真机 debug APK：

```text
路径：android/app/build/outputs/apk/debug/app-debug.apk
base URL：http://192.168.0.118:8000/
大小：16471142 bytes
SHA256：81bf25c27316261d5b3e0e749ea55cfb80a970c04641d880c477e37431e8e9ce
```

交给 Redmi K60 / Honor Pad 5 前必须使用 Mac LAN IP 构建并重新记录 sha256：

```bash
bash scripts/build_device_debug_apk.sh --base-url http://<mac-lan-ip>:8000/
shasum -a 256 android/app/build/outputs/apk/debug/app-debug.apk
```

MiMo VoiceClone 开启后，`/api/v1/conversation/message` 会同步等待“对话模型 + TTS 音频生成”。Redmi K60 真机测试中出现过旧版 App 误报“没有连上后端”的情况；后端日志显示一轮请求耗时约 10.5 秒，接近旧版 12 秒 read timeout。当前 Android conversation read timeout 已调为 45 秒，后端也增加了 `app.request_timing` 请求耗时日志。

## 小白狐 v1 静态候选资源

当前候选资源来自父亲 / 产品负责人提供的小白狐角色设定，已经归档到：

```text
docs/assets/fox/v1/little_white_fox_character_sheet_v1.png
docs/assets/fox/v1/fox_3d_neutral_idle.png
docs/assets/fox/v1/fox_3d_listening.png
docs/assets/fox/v1/fox_3d_speaking.png
docs/assets/fox/v1/fox_3d_jumping_happy.png
docs/assets/fox/v1/fox_3d_thinking.png
docs/assets/fox/v1/calm.png
docs/assets/fox/v1/sleepy.png
docs/assets/fox/v1/safety_concern.png
docs/assets/fox/v1/privacy_boundary.png
docs/assets/fox/v1/homework_focus.png
docs/assets/fox/v1/network_error.png
```

Android 运行时资源位于：

```text
android/app/src/main/res/drawable-nodpi/fox_3d_character_sheet_v1.webp
android/app/src/main/res/drawable-nodpi/fox_3d_neutral_idle.webp
android/app/src/main/res/drawable-nodpi/fox_3d_listening.webp
android/app/src/main/res/drawable-nodpi/fox_3d_speaking.webp
android/app/src/main/res/drawable-nodpi/fox_3d_jumping_happy.webp
android/app/src/main/res/drawable-nodpi/fox_3d_thinking.webp
android/app/src/main/res/drawable-nodpi/fox_3d_calm.webp
android/app/src/main/res/drawable-nodpi/fox_3d_sleepy.webp
android/app/src/main/res/drawable-nodpi/fox_3d_safety_concern.webp
android/app/src/main/res/drawable-nodpi/fox_3d_privacy_boundary.webp
android/app/src/main/res/drawable-nodpi/fox_3d_homework_focus.webp
android/app/src/main/res/drawable-nodpi/fox_3d_network_error.webp
```

当前状态映射：

| 状态 | 资源 |
|---|---|
| 普通 / warm / idle | `fox_3d_neutral_idle` |
| 倾听 / listening | `fox_3d_listening` |
| 鼓励 / encouraging / celebrate small | `fox_3d_jumping_happy` |
| 思考 / thinking | `fox_3d_thinking` |
| 学习 / homework focus | `fox_3d_homework_focus` |
| 平静 / calm | `fox_3d_calm` |
| 睡前 / sleepy | `fox_3d_sleepy` |
| 安全关注 / safety concern | `fox_3d_safety_concern` |
| 隐私边界 / privacy boundary | `fox_3d_privacy_boundary` |
| TTS speaking / future speaking state | `fox_3d_speaking` |
| 网络错误 | `fox_3d_network_error` |
| 缺失资源 / 低性能模式 | neutral 或 Canvas fallback |

不要删除 Compose Canvas fallback；缺失状态、低性能设备或资源加载失败时必须能降级。

## TTS-D1 真机诊断

Redmi K60 / Android 14 真机反馈：

```text
1. 语音输入不可用：符合当前状态，Android ASR 录音确认 UI 尚未实现。
2. TTS 完全没有声音。
3. 截图显示朗读诊断：speak=SKIPPED_UNAVAILABLE，failure=TextToSpeech is unavailable。
4. 小白狐没有切到 speaking，说明上一版没有进入可见的 speaking pending / onStart 路径。
5. 系统 TTS 声音不好，不适合作为最终儿童产品音色。
```

当前修复内容：

```text
1. TTS 请求被接受后先进入 speaking pending / speaking，不再只依赖系统 onStart。
2. UI 显示朗读已开启、正在准备朗读、不可用等短状态。
3. 开发构建显示诊断：engine、locale、voice、setLanguage、setVoice、speak、failure。
4. speak() 返回 ERROR 或系统 TTS 不可用时恢复小白狐基础状态，并保留文字聊天。
5. AndroidManifest 声明 TTS service 查询，AndroidTtsController 修复初始化回调早于字段赋值时的误判风险。
6. TTS 不可用时显示“检查朗读设置”和“安装语音数据”入口。
7. 当前 Android 不接第三方 TTS、不直接调用 MiMo；后端受控 TTS endpoint 已通过真实 MiMo VoiceClone smoke，Android 已优先播放 `reply.audio_url`，失败时 fallback 到系统 TTS 或文字。
```

历史真机 APK记录（非本轮 family smoke build）：

```text
路径：android/app/build/outputs/apk/debug/app-debug.apk
大小：31M
SHA256：c70f804c06621905c9cc4a8ca0d8357f6b8647df42013ff9dd2cd0de389fa503
base URL：http://192.168.0.118:8000/
```

## 双设备测试策略

父亲 / 产品负责人已确认双设备策略：

| 设备 | 定位 | 重点 |
|---|---|---|
| Device A：Redmi K60，Android 14 | 功能主验证 | 先跑通后端 ASR 录音上传确认、自动朗读、小白狐状态切换、图片资源、轻量动画、真实模型/Mock 模型对话体验和核心安全流程 |
| Device B：Honor Pad 5，Android 9，RAM 4GB | 低配兼容性目标设备 | 验证 Android 9、4GB 内存、平板横屏/大屏 UI、后端 ASR 上传确认、TTS fallback、小白狐资源大小、动画流畅度、发热、卡顿和降级策略 |

开发原则：

```text
1. Honor Pad 5 不阻塞第一阶段语音和小白狐功能开发。
2. 高配手机先跑通功能闭环。
3. Honor Pad 5 用于最低兼容目标和性能降级验证。
4. Android 9 兼容性不能被破坏。
5. Honor Pad 5 上语音效果不好时，允许降级为文字优先，但必须记录 QA 结果。
```

## 当前不做

- 当前不做 CameraX 或自定义相机 UI；图片输入使用系统相机 / 系统相册。
- 当前 Android 不直接调用 MiMo，也不保存模型、TTS 或 ASR API key。小白狐正式语音由后端生成 `audio_url`，后端 smoke 已确认可返回可下载 WAV；Android 优先播放远程音频，失败时 fallback 系统 TextToSpeech 或文字。
- 不默认上传原始音频到后端，不把原始音频保存到长期记忆。
- 不长期保存真实图片；当前图片路径上传真实图片给后端临时处理，后端只把受控 image context 带入 conversation。
- 不做账号系统。
- 不把父亲入口 PIN 当作强安全机制；它只是 v0.1 开发期的轻量误触保护。
- 不在 Android 端放任何模型 API key。
- 不在客户端实现 AI 决策。
- 不在客户端做安全分类、意图识别或场景路由。
- 不展示孩子完整逐字聊天记录。
- 不引入实时 3D 引擎或大型动画依赖作为第一版小白狐资源必需能力。

## 后端配置

默认开发 base URL 是当前 Mac LAN 地址，用于 Redmi K60 / Honor Pad 5 真机测试：

```text
http://192.168.0.118:8000/
```

如需改成真机或其他地址，可以在 Gradle 命令中传入：

```bash
bash scripts/android_gradle.sh assembleDebug -PconversationApiBaseUrl=http://192.168.1.10:8000/
```

推荐使用真机打包脚本，它会输出 APK metadata：

```bash
bash scripts/build_device_debug_apk.sh --base-url http://<mac-lan-ip>:8000/
```

联调前先确认后端可从 Mac 本机和局域网地址访问：

```bash
curl --noproxy '*' http://127.0.0.1:8000/api/v1/health
curl --noproxy '*' http://192.168.1.10:8000/api/v1/health
```

真机或平板必须使用 Mac mini 的局域网 IP，并确保设备和 Mac 在同一网络。

交付真机 APK 前必须复核：

```bash
bash scripts/build_device_debug_apk.sh --base-url http://<mac-lan-ip>:8000/
sed -n '1,40p' android/app/build/generated/source/buildConfig/debug/com/childai/companion/BuildConfig.java
shasum -a 256 android/app/build/outputs/apk/debug/app-debug.apk
curl --noproxy '*' http://<mac-lan-ip>:8000/api/v1/health
```

如果 `BuildConfig.CONVERSATION_API_BASE_URL` 不是当前 Mac LAN 地址，该 APK 不能交给 Redmi K60 / Honor Pad 5 做真机 QA。

本地开发使用 HTTP 明文访问后端；不要在 Android 端写入任何模型 API key 或真实 secret。

## 家庭内测前 QA

当前可运行的自动检查：

```bash
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh assembleDebug
bash scripts/build_device_debug_apk.sh --base-url http://<mac-lan-ip>:8000/
bash scripts/smoke_backend_local.sh
bash scripts/smoke_voice_stack.sh
```

真机前置检查：

```text
1. 后端用 `--host 0.0.0.0` 启动，设备可访问 `http://<mac-lan-ip>:8000/api/v1/health`。
2. APK 使用真机 LAN base URL 构建。
3. MiMo key 只放后端环境变量，不放 Android、docs、tests 或截图。
4. ASR 真实 provider smoke 只用非儿童测试音频和 opt-in policy env；真机儿童语音 QA 不等于 provider smoke。
5. 详细 Redmi K60 / Honor Pad 5 手动步骤见 `docs/QA_DEVICE_CHECKLIST_V0_1.md`。
6. Redmi K60 先测主功能链路，Honor Pad 5 后测低配性能和 fallback。
7. QA 结果记录模板见 `docs/QA_RESULT_TEMPLATE_V0_1.md`。
```

当前真机 QA debug APK：

```text
路径：android/app/build/outputs/apk/debug/app-debug.apk
构建时间 UTC：2026-05-22T12:06:31Z
大小：16190741 bytes / 15M
SHA256：798a87a6256c9b2523b519aeb337385eec2fe7b9cecc43e25f1feb79bf51f850
base URL：http://192.168.0.118:8000/
BuildConfig.CONVERSATION_API_BASE_URL：http://192.168.0.118:8000/
```

这个 APK 可用于 Redmi K60 / Honor Pad 5 真机 QA，但尚未真机通过。Mac LAN IP 改变后必须重新构建。

## 本地运行

需要本机安装 JDK 17 和 Android SDK，并设置 Android SDK 路径，例如：

```bash
export ANDROID_HOME="$HOME/Library/Android/sdk"
```

本项目推荐从仓库根目录使用包装脚本，它会加载本机 JDK 17 和 Android SDK 路径，避免非交互 shell 误报缺少 Java Runtime：

```bash
bash scripts/android_gradle.sh test
bash scripts/android_gradle.sh assembleDebug
bash scripts/android_gradle.sh lintDebug
```

构建：

```bash
bash scripts/android_gradle.sh assembleDebug
```

单元测试：

```bash
bash scripts/android_gradle.sh test
```

如果需要手动进入 `android/` 运行 Gradle，先从仓库根目录加载环境：

```bash
bash -lc 'source scripts/android_env.sh && cd android && ./gradlew test assembleDebug'
```

环境排查：

```bash
bash scripts/doctor_local_env.sh
```

## 手动联调

先从仓库根目录启动后端：

```bash
bash scripts/dev_backend.sh
```

再安装运行 Android debug 包。验证路径：

```text
1. 输入“我回来了”，页面应追加孩子消息和后端回复。
2. 输入“我有一道题不会”，页面应显示“拍题目”“读题目”等快捷按钮。
3. 点击“拍给小白狐看”，选择“拍照”或“从相册选”，应调用系统相机/相册并上传真实图片。
4. 页面应通过 `/api/v1/attachments/images` 创建 attachment，再通过 `/conversation/message` 携带 attachment_id。
5. 页面应显示后端基于 MiMo vision 形成的图片分享引导；如果图片像题目，也不应直接显示最终答案。
6. 点击“父亲设置”不应直接进入；长按“父亲设置”后输入开发 PIN `0000`，读取当前 policy，修改目标、沟通偏好或时间段，保存后应显示成功提示。
7. 回到聊天页再发送消息，后端应使用更新后的 parent policy。
7a. 在父亲设置页填写小名或显示名并保存后，重新进入儿童聊天页，opening greeting 应按“小名 -> 显示名 -> 不称呼”的优先级称呼孩子。
8. 点击“父亲日报”不应直接进入；长按“父亲日报”后输入开发 PIN `0000`，读取当天 summary；如果当天没有结构化记忆，后端会返回“暂无可汇总的结构化会话素材”类摘要。
9. 页面不应默认显示 `base=... | active=...` 这类内部 session_state 调试文本。
10. 断开后端时，页面应显示温和错误，提示请大人检查网络。
11. 小白狐状态应随后端 `emotion` / `agent_motion` 轻量变化；小白狐回复默认自动朗读，朗读时切到 speaking，可停止或静音。
12. 底部语音按钮只在点击后请求麦克风权限；儿童默认 ASR 成功后自动发送，不显示文字编辑确认面板；打开 `VOICE_CONFIRM_BEFORE_SEND=true` 后才进入待确认文本。
```

如果需要先排除后端 API 合约问题，可以在仓库根目录运行：

```bash
bash scripts/e2e_local_api_check.sh
```

## Next UI / Streaming Direction

最新真机反馈已经确认：MiMo VoiceClone 音频可以在 Redmi K60 上初步听到，动态小白狐形象也已经出现；但当前同步等待时间仍长。下一轮 Android 重点如下：

```text
1. 主界面已改为横屏双栏：左侧动态小白狐，右侧对话交互；手机也进入横屏。
2. 保留现有 `reply.audioUrl` 远程音频优先播放，系统 TTS 只做 fallback。
3. Stream client 已接入，下一步真机验证文本渐进显示和 audio segment 排队播放。
4. 小白狐状态需要覆盖矩阵验证：哪些状态有资源、哪些状态能被真实业务触发。
5. 语音输入已接入 Android 录音上传后端 ASR + 儿童默认自动发送；下一步在 Redmi K60 / Honor Pad 5 做权限、录音、上传、自动发送、DevSettings 确认模式和失败 fallback 手动 QA。
```

横屏第一版不做完整视觉重设计，不删除 animation_v1、静态 WebP 或 Canvas fallback。真机 QA 需要记录 Redmi K60 和 Honor Pad 5 的布局、字体、输入区、动画流畅度、MiMo 音频延迟和 stream/fallback 行为。

## 父亲日报说明

后端当前已提供父亲日报 API：

```text
GET /api/v1/parent/reports/{child_id}?date=YYYY-MM-DD
```

Android 端按只读页展示后端 `generation_status=model_generated` 的 summary、学习观察、表达观察、情绪/社交观察、建议父亲动作和需要关注事项。该页不展示 evidence、quote_summary 或孩子完整逐字聊天记录。ParentReport v2 由后端读取当天会话和 parent-visible memory 后调用 `ModelTaskType.PARENT_REPORT` 生成；如果返回 `model_failed` / `model_blocked`，父亲端只显示“日报暂时生成失败，请稍后重试”，不展示 deterministic fallback 正文。
