# Android 平板端

本目录是儿童 AI 成长智能体的 Android 平板端。当前阶段已在 S11 / A1 静态壳和 S12 / A2 Conversation API 基础上接入 S13 / A3-A4 演示闭环。

当前 Android MVP 已完成文字聊天、mock 拍题、父亲设置/日报和父亲入口轻量保护。TTS 已接入远程 `reply.audio_url` 优先播放：后端 MiMo VoiceClone 音频可作为小白狐正式音色，Android 系统 TextToSpeech 保留为 fallback/诊断能力。语音输入 ASR 仍是后续任务。

## 当前范围

- 单一儿童聊天入口。
- 小白狐智能体形象占位，会根据后端 `reply.emotion` 和
  `reply.agent_motion` 做轻量状态变化。
- 文本输入框和发送按钮。
- 调用后端 `POST /api/v1/conversation/message`。
- 渲染后端返回的 `reply.text` 和 `ui_actions` 快捷按钮；`session_state` 只保存在 UI state 中供续会话和开发排查使用，默认不展示给儿童。
- DTO 已解析 `reply.voice_enabled`、`reply.audio_url`、`reply.emotion` 和
  `reply.agent_motion`；当前 UI 已接入小白狐 `animation_v1` PNG 序列帧、旧静态 PNG 和 Canvas 三层 fallback。TTS v1 会默认自动朗读小白狐回复，优先播放后端远程音频，并在朗读时切到 speaking 状态。语音输入 ASR 仍是后续能力。
- 点击“拍题目”走 mock attachment 流程，不接真实 CameraX，不保存真实图片。
- 父亲设置页可读取和保存目标、沟通偏好、放学后/作业/睡前时间段。
- 父亲日报页读取后端 `GET /api/v1/parent/reports/{child_id}` 只读摘要。
- 儿童聊天页中的父亲设置和父亲日报入口使用轻量误触保护：点击只提示，长按后输入开发 PIN 才进入。
- 使用内存保存当前 `session_id` 和最新 `session_state`。

## 下一阶段语音和小白狐方向

已确认方向：

- 语音输入 v1 优先使用 Android 本地 `SpeechRecognizer`。
- 语音输入 v1 是 confirm-before-send：点击语音 -> 孩子说话 -> Android 本地 ASR -> 展示识别文本 -> 孩子确认/可编辑 -> 点击发送 -> text 走 `/conversation/message`。
- Future hands-free conversational mode 不进入 v1。
- 确认后的文本继续调用现有 `POST /api/v1/conversation/message`。
- 第一阶段默认不上传原始音频到后端，不长期保存原始音频。
- TTS 朗读优先播放后端返回的 `reply.audio_url`，朗读后端已安全处理的 `reply.text` 对应音频；远程播放失败时 fallback 到系统 TextToSpeech 或文字。
- TTS 已有停止/静音控制，并受 `DevSettings.AUTO_TTS_ENABLED` / `DevSettings.TTS_MUTED` 初始配置治理；`DevSettings.SHOW_TTS_DIAGNOSTICS` 用于开发构建显示 engine、locale、voice、speak 返回值和失败原因。
- TTS 不可用时 UI 会显示温和文字提示，并提供“检查朗读设置”和“安装语音数据”入口；文字聊天不受影响。
- TTS fallback 已实现 `VoiceProfile`：`preferredVoiceName`、`zh-CN`、稍慢 `speechRate`、偏高但不过度的 `pitch`、fallback 系统默认中文 voice。
- Redmi K60 / Android 14 反馈说明系统 TTS 即使可用，声音也可能不适合孩子；Android system TTS 只作为 fallback 和诊断能力，不作为最终音色承诺。
- Android 不直接调用 MiMo，不保存 MiMo API key；正式音频由后端 `/api/v1/tts/xiaobaohu` 生成并通过 `/media/tts/...wav` 返回。后端真实 MiMo VoiceClone smoke 已通过，Android 已接入 `reply.audio_url` 远程播放优先级。
- Redmi K60 当前复测重点：确认 Android 是否请求 `/media/tts/...wav`、是否能听到 MiMo 小白狐音色、停止/静音是否生效；如果远程播放失败，再检查系统 TTS fallback 的 `lang` / `setVoice` / `speak` 诊断。
- Android 可以使用 `SpeechRecognizer` / `TextToSpeech`，但必须通过可替换抽象：`VoiceEngine` / `SpeechInputController` / `TtsController`。
- 小白狐形象应温和、好奇、活泼开朗，视觉目标优先 3D 卡通 / soft 3D / 毛绒感 / 儿童动画质感；Compose Canvas / 2D 只是 fallback，不阻塞语音开发。
- 小白狐 v1 候选资源已导入，当前包含 11 个状态：`neutral_idle`、`listening`、`speaking`、`jumping_happy`、`thinking`、`calm`、`sleepy`、`safety_concern`、`privacy_boundary`、`homework_focus`、`network_error`。
- Android 第一版优先预渲染 3D PNG/WebP 状态图 + 本地 PNG 序列帧轻量播放，不引入实时 3D 引擎或大型动画依赖作为必需能力。
- 小白狐动态序列帧放在 `android/app/src/main/assets/mascot/xiaobaohu/v1/`，由 manifest-driven loader 读取；旧静态 PNG fallback 保留在 `android/app/src/main/res/drawable-nodpi/`。
- `FoxAgentAssetMapper` 负责把 `FoxAgentUiState` / `FoxMood` / `FoxMotion` 映射到 drawable 或 Canvas fallback。
- `DevSettings.FOX_RENDER_MODE` 当前支持 `animation_v1` / `png_static` / `canvas` / `auto` 语义；`DevSettings.FOX_ASSET_MODE` 继续控制旧静态 PNG fallback；低配设备可强制 Canvas 或静态状态。
- TTS speaking 会优先映射到 animation_v1 的 `speaking` 序列帧；朗读结束或停止后恢复后端 reply 对应的基础状态。
- UI、产品、设计和测试说明统一称为“小白狐”；代码 class 名 `FoxAgent` 暂可保留，后续如要改代码命名单独 refactor。
- 小白狐表现层不得制造“唯一朋友”“只有我懂你”等依赖感，不做排行榜、连击奖励或上瘾式动画。
- 小白狐音色方向是小孩子般干净、清脆、中性、活泼可爱，但不能过度尖锐或幼稚；当前正式方向是后端 MiMo VoiceClone v01，系统 TTS 只做 fallback。
- QA 需要记录识别准确率、延迟、中文效果、儿童声音识别、TTS 自然度、孩子接受度、小白狐动画流畅度和是否需要降级。

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
每个状态目录下的 frames/*.png
```

当前没有把 preview html、gif/webp 预览和 spritesheet 调试资料作为运行时依赖。完整资源记录见：

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
1. `animation_v1`：优先使用 manifest + PNG frames 播放。
2. `png_static`：animation manifest 或 frames 失败时使用旧静态 PNG。
3. `canvas`：静态资源也不可用或低性能模式时使用 Compose Canvas fallback。
```

相关开关：

```kotlin
DevSettings.FOX_RENDER_MODE = "animation_v1"
DevSettings.FOX_ANIMATION_ENABLED = true
DevSettings.FOX_ANIMATION_LOW_PERFORMANCE_MODE = false
DevSettings.SHOW_MASCOT_DEBUG_SWITCHER = false
```

当前 animation_v1 assets 约 117MB，会显著增加 APK 体积。Redmi K60 作为功能主验证设备，Honor Pad 5 Android 9 / 4GB 作为低配性能和降级验证设备。

最新 animation_v1 debug APK：

```text
路径：android/app/build/outputs/apk/debug/app-debug.apk
大小：147M
SHA256：25cbd4a8522987fc0551df9e162b8c1fa6b7b44e5aaace53e437beb4c90d4cd5
base URL：http://192.168.0.118:8000/
```

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
android/app/src/main/res/drawable-nodpi/fox_3d_character_sheet_v1.png
android/app/src/main/res/drawable-nodpi/fox_3d_neutral_idle.png
android/app/src/main/res/drawable-nodpi/fox_3d_listening.png
android/app/src/main/res/drawable-nodpi/fox_3d_speaking.png
android/app/src/main/res/drawable-nodpi/fox_3d_jumping_happy.png
android/app/src/main/res/drawable-nodpi/fox_3d_thinking.png
android/app/src/main/res/drawable-nodpi/fox_3d_calm.png
android/app/src/main/res/drawable-nodpi/fox_3d_sleepy.png
android/app/src/main/res/drawable-nodpi/fox_3d_safety_concern.png
android/app/src/main/res/drawable-nodpi/fox_3d_privacy_boundary.png
android/app/src/main/res/drawable-nodpi/fox_3d_homework_focus.png
android/app/src/main/res/drawable-nodpi/fox_3d_network_error.png
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
1. 语音输入不可用：符合当前状态，ASR 尚未实现。
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

最新真机 APK：

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
| Device A：Redmi K60，Android 14 | 功能主验证 | 先跑通 TextToSpeech 诊断、SpeechRecognizer、自动朗读、小白狐状态切换、图片资源、轻量动画、真实模型/Mock 模型对话体验和核心安全流程 |
| Device B：Honor Pad 5，Android 9，RAM 4GB | 低配兼容性目标设备 | 验证 Android 9、4GB 内存、平板横屏/大屏 UI、系统 ASR/TTS 可用性、小白狐资源大小、动画流畅度、发热、卡顿和降级策略 |

开发原则：

```text
1. Honor Pad 5 不阻塞第一阶段语音和小白狐功能开发。
2. 高配手机先跑通功能闭环。
3. Honor Pad 5 用于最低兼容目标和性能降级验证。
4. Android 9 兼容性不能被破坏。
5. Honor Pad 5 上语音效果不好时，允许降级为文字优先，但必须记录 QA 结果。
```

## 当前不做

- 当前不接真实相机或 SpeechRecognizer ASR；语音输入 v1 后续才会接 Android 本地 SpeechRecognizer。
- 当前 Android 不直接调用 MiMo，也不保存模型或 TTS API key。小白狐正式语音由后端生成 `audio_url`，后端 smoke 已确认可返回可下载 WAV；Android 优先播放远程音频，失败时 fallback 系统 TextToSpeech 或文字。
- 不默认上传原始音频到后端，不把原始音频保存到长期记忆。
- 不长期保存真实图片；拍题流程只发送 mock OCR 文本和 mock metadata。
- 不做账号系统。
- 不把父亲入口 PIN 当作强安全机制；它只是 v0.1 开发期的轻量误触保护。
- 不在 Android 端放任何模型 API key。
- 不在客户端实现 AI 决策。
- 不在客户端做安全分类、意图识别或场景路由。
- 不展示孩子完整逐字聊天记录。
- 不引入实时 3D 引擎或大型动画依赖作为第一版小白狐资源必需能力。

## 后端配置

默认开发 base URL 是 Android Emulator 访问宿主机的地址：

```text
http://10.0.2.2:8000/
```

如需改成真机或其他地址，可以在 Gradle 命令中传入：

```bash
bash scripts/android_gradle.sh assembleDebug -PconversationApiBaseUrl=http://192.168.1.10:8000/
```

联调前先确认后端可从 Mac 本机和局域网地址访问：

```bash
curl --noproxy '*' http://127.0.0.1:8000/api/v1/health
curl --noproxy '*' http://192.168.1.10:8000/api/v1/health
```

模拟器继续使用默认 `http://10.0.2.2:8000/`；真机或平板必须使用 Mac mini 的局域网 IP，并确保设备和 Mac 在同一网络。

本地开发使用 HTTP 明文访问后端；不要在 Android 端写入任何模型 API key 或真实 secret。

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

## 本机模拟器

本机已按项目共享上下文准备 tablet AVD：

```text
child_ai_tablet_api35
```

启动窗口模式模拟器：

```bash
bash scripts/start_android_emulator.sh
```

启动无窗口模式用于命令行 smoke test：

```bash
bash scripts/start_android_emulator.sh --headless
```

构建、安装并打开 debug 包：

```bash
bash scripts/install_android_debug.sh
```

模拟器访问宿主机后端使用默认 `http://10.0.2.2:8000/`。启动后端：

```bash
bash scripts/dev_backend.sh --host 0.0.0.0 --port 8000
```

如果模拟器里 App 提示无法连接后端，先确认模拟器网络和宿主机 health：

```bash
bash scripts/android_env.sh adb shell cmd wifi connect-network AndroidWifi open
bash scripts/android_env.sh adb shell 'curl -fsS http://10.0.2.2:8000/api/v1/health'
```

窗口模式手动输入中文时，可切到系统 Gboard 中文拼音：

```bash
bash scripts/android_env.sh adb shell settings put secure selected_input_method_subtype 617035939
bash scripts/android_env.sh adb shell ime set com.google.android.inputmethod.latin/com.android.inputmethod.latin.LatinIME
```

自动化 UI QA 需要直接注入中文时，本机 emulator 可临时使用 ADBKeyBoard 调试输入法；它只安装到模拟器，不属于产品 APK：

```bash
curl -fL -o /tmp/child-ai-qa/adbkeyboard.apk \
  https://github.com/senzhk/ADBKeyBoard/releases/download/v2.5-dev/keyboardservice-debug.apk
bash scripts/android_env.sh adb install -r /tmp/child-ai-qa/adbkeyboard.apk
bash scripts/android_env.sh adb shell ime enable com.android.adbkeyboard/.AdbIME
bash scripts/android_env.sh adb shell ime set com.android.adbkeyboard/.AdbIME
bash scripts/android_env.sh adb shell am broadcast -a ADB_INPUT_TEXT --es msg '我有一道题不会'
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
3. 点击“拍题目”，保留默认 mock 题目或编辑题目文字，然后点击“发送题目”。
4. 页面应通过 /conversation/attachment 创建 attachment，再通过 /conversation/message 携带 attachment_id。
5. 页面应显示后端返回的题意引导，例如先问“这道题是在问什么”，不显示最终答案。
6. 点击“父亲设置”不应直接进入；长按“父亲设置”后输入开发 PIN `0000`，读取当前 policy，修改目标、沟通偏好或时间段，保存后应显示成功提示。
7. 回到聊天页再发送消息，后端应使用更新后的 parent policy。
8. 点击“父亲日报”不应直接进入；长按“父亲日报”后输入开发 PIN `0000`，读取当天 summary；如果当天没有结构化记忆，后端会返回“暂无可汇总的结构化会话素材”类摘要。
9. 页面不应默认显示 `base=... | active=...` 这类内部 session_state 调试文本。
10. 断开后端时，页面应显示温和错误，提示请大人检查网络。
11. 小白狐状态应随后端 `emotion` / `agent_motion` 轻量变化；小白狐回复默认自动朗读，朗读时切到 speaking，可停止或静音。
12. 底部语音输入按钮仍是占位，不应录音或请求麦克风权限。
```

如果需要先排除后端 API 合约问题，可以在仓库根目录运行：

```bash
bash scripts/e2e_local_api_check.sh
```

## 父亲日报说明

后端当前已提供父亲日报 API：

```text
GET /api/v1/parent/reports/{child_id}?date=YYYY-MM-DD
```

Android 端按只读页展示后端 summary、学习观察、表达观察、情绪/社交观察、建议父亲动作和需要关注事项。该页不展示 evidence、quote_summary 或孩子完整逐字聊天记录。当前后端日报素材来自内存态结构化 memory；如果重启后端或当天没有 memory，日报会显示空摘要，这不是 Android stub。
