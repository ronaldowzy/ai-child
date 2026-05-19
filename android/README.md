# Android 平板端

本目录是儿童 AI 成长智能体的 Android 平板端。当前阶段已在 S11 / A1 静态壳和 S12 / A2 Conversation API 基础上接入 S13 / A3-A4 演示闭环。

当前 Android MVP 已完成文字聊天、mock 拍题、父亲设置/日报和父亲入口轻量保护。下一阶段产品重点是语音交互和小白狐形象体验，但必须先完成完整设备 QA。

## 当前范围

- 单一儿童聊天入口。
- 小白狐智能体形象占位，会根据后端 `reply.emotion` 和
  `reply.agent_motion` 做轻量状态变化。
- 文本输入框和发送按钮。
- 调用后端 `POST /api/v1/conversation/message`。
- 渲染后端返回的 `reply.text` 和 `ui_actions` 快捷按钮；`session_state` 只保存在 UI state 中供续会话和开发排查使用，默认不展示给儿童。
- DTO 已解析 `reply.voice_enabled`、`reply.audio_url`、`reply.emotion` 和
  `reply.agent_motion`；当前 UI 已做轻量状态映射，但语音输入、TTS 播放和复杂动画仍是后续能力。
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
- TTS 朗读 v1 优先使用 Android 系统 TextToSpeech，默认自动朗读小白狐回复，朗读后端已安全处理的 `reply.text`。
- TTS 必须有停止/静音和 DevSettings 或父亲设置开关。
- TTS v1 需要 `VoiceProfile`：`preferredVoiceName`、`zh-CN`、稍慢 `speechRate`、偏高但不过度的 `pitch`、fallback 系统默认中文 voice；v2 再评估小白狐专属音色。
- Android 可以使用 `SpeechRecognizer` / `TextToSpeech`，但必须通过可替换抽象：`VoiceEngine` / `SpeechInputController` / `TtsController`。
- 小白狐形象应温和、好奇、慢热友好，视觉目标优先 3D / soft 3D / 毛绒感 / 立体绘本感；Compose Canvas / 2D 只是 fallback，不阻塞语音开发。
- UI、产品、设计和测试说明统一称为“小白狐”；代码 class 名 `FoxAgent` 暂可保留，后续如要改代码命名单独 refactor。
- 小白狐表现层不得制造“唯一朋友”“只有我懂你”等依赖感，不做排行榜、连击奖励或上瘾式动画。
- QA 需要记录识别准确率、延迟、中文效果、儿童声音识别、TTS 自然度和孩子接受度。

详细设计见：

- `docs/PRODUCT_DECISIONS_V0_1.md`
- `docs/VOICE_INTERACTION_DESIGN_V0_1.md`
- `docs/FOX_AGENT_VISUAL_DESIGN_V0_1.md`
- `docs/NEXT_PHASE_PLAN_V0_2.md`

## 当前不做

- 当前 v0.1 不接真实相机、语音或 TTS；下一阶段语音 v1 才会接 Android 本地 SpeechRecognizer 和系统 TTS。
- 不在当前版本录制、生成或播放真实语音；语音入口和字段只作为后续接口预留。
- 不默认上传原始音频到后端，不把原始音频保存到长期记忆。
- 不长期保存真实图片；拍题流程只发送 mock OCR 文本和 mock metadata。
- 不做账号系统。
- 不把父亲入口 PIN 当作强安全机制；它只是 v0.1 开发期的轻量误触保护。
- 不在 Android 端放任何模型 API key。
- 不在客户端实现 AI 决策。
- 不在客户端做安全分类、意图识别或场景路由。
- 不展示孩子完整逐字聊天记录。

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
11. 小白狐状态应随后端 `emotion` / `agent_motion` 轻量变化；底部语音入口仍是占位，不应录音或播放音频。
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
