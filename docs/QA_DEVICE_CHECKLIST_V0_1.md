# QA Device Checklist v0.1

用途：家庭内测前真机 QA 清单。自动测试和 APK 构建已完成不等于真机通过。

## 1. 设备

```text
Redmi K60：主功能验证设备。
Honor Pad 5 / Android 9 / 4GB：低配性能、大屏布局和 fallback 验证设备。
```

当前状态：

```text
自动测试：已完成。
debug APK 构建：已完成，当前真机 QA APK 使用 Mac LAN base URL。
真机安装和完整手动 QA：未完成。
```

## 2. 安装前检查

```text
[ ] 后端用 LAN 可访问地址启动：bash scripts/dev_backend.sh --host 0.0.0.0 --port 8000
[ ] Mac 和设备在同一网络。
[ ] curl --noproxy '*' http://<mac-lan-ip>:8000/api/v1/health 返回 ok。
[ ] 使用真机 base URL 重新构建 APK，或使用本轮已构建的 LAN APK：
    bash scripts/build_device_debug_apk.sh --base-url http://<mac-lan-ip>:8000/
[ ] 记录 APK size 和 sha256。
[ ] 确认 Android BuildConfig.CONVERSATION_API_BASE_URL 不是 http://10.0.2.2:8000/。
[ ] 当前本轮 APK metadata：
    path=android/app/build/outputs/apk/debug/app-debug.apk
    size=16049959 bytes
    sha256=3577e3c3fdb46ccf0298310fce21ac449b5dc5da7b8a20449295bbda567f4b95
    baseUrl=http://192.168.0.118:8000/
[ ] 如果 Mac LAN IP 变化，必须重新构建并重新记录 metadata。
```

## 3. Redmi K60 QA

先测 Redmi K60。Redmi K60 是主功能设备，先确认后端连接、voice-first、ASR、stream audio 和 opening greeting 主链路。

### Layout And Mascot

```text
[ ] App 强制横屏，左侧小白狐、右侧对话区域没有重叠。
[ ] animation_v1 WebP 序列帧能播放。
[ ] 切到 speaking/listening/thinking/calm 等状态时不卡顿。
[ ] 如果 animation_v1 加载失败，static WebP fallback 可见。
[ ] 如果图片资源失败，Canvas fallback 可见。
```

### Opening Greeting

```text
[ ] App 打开后小白狐主动展示短 opening greeting。
[ ] 有孩子小名时优先喊小名。
[ ] 没有小名但有显示名时使用显示名。
[ ] 都没有时不强行称呼。
[ ] opening 的 audioUrl 能自动播放。
[ ] 孩子先开始说话时，迟到 opening 不打断孩子。
```

### Parent Settings

```text
[ ] 父亲入口普通点击不直接进入。
[ ] 长按 + PIN 后进入父亲设置。
[ ] 孩子小名/显示名可保存并读回。
[ ] 父母寄语、目标、沟通偏好、作息保存后不丢失。
[ ] 小名/显示名不要求填写真实全名。
```

### ASR Voice Input

```text
[ ] 点击语音按钮时才请求麦克风权限。
[ ] 权限允许后开始录音，小白狐切 listening。
[ ] “说完了”停止录音并上传后端 ASR。
[ ] ASR ok 且 transcript 非空时儿童默认自动发送，不展示编辑确认面板。
[ ] needs_retry 显示“我刚才没听清，可以再说一次”，不自动发送。
[ ] policy blocked / provider unavailable 显示请大人检查，不自动发送。
[ ] 权限拒绝后仍可请大人处理，App 不崩溃。
[ ] 打开 DevSettings.VOICE_CONFIRM_BEFORE_SEND=true 后，可进入确认模式。
```

### Streaming And Audio

```text
[ ] 普通聊天可看到 text_delta 渐进显示。
[ ] stream 输出 done 后 loading=false。
[ ] audio_ready segment 进入队列并按顺序播放。
[ ] 播放时小白狐切 speaking。
[ ] 停止朗读能停止当前音频并清空队列。
[ ] 静音后不播放 audio_ready，也不 fallback 系统 TTS。
[ ] stream 失败时 fallback 到旧 /conversation/message 或显示温和错误，不清空已有文本。
```

### DB Persistence Smoke

```text
[ ] 本地 PostgreSQL 启动并迁移到 head。
[ ] 发送普通 conversation 后，conversation_sessions/messages/routing_decisions 有记录。
[ ] stream conversation 完成后，只落一条完整 turn，不落每个 text_delta。
[ ] ConversationMemoryHooks 生成 structured memory 并进入 memory_items。
[ ] 父亲日报生成后 parent_reports 有记录。
[ ] parent_reports 不含 evidence、quote_summary、raw transcript、prompt、debug。
```

## 4. Honor Pad 5 QA

Redmi K60 主链路通过后再测 Honor Pad 5。Honor Pad 5 重点看 Android 9 / 4GB 下的低配性能、横屏布局和 fallback。

```text
[ ] 横屏双栏在 4GB 低配设备上不重叠。
[ ] animation_v1 流畅度可接受；如不接受，记录是否需要低性能默认。
[ ] static WebP / Canvas fallback 可用。
[ ] opening greeting 不阻塞语音按钮。
[ ] 录音、上传、ASR 自动发送可完成。
[ ] audio segment 播放不卡死；停止/静音有效。
[ ] 后端断开时错误文案温和，App 不崩溃。
[ ] 长时间使用不出现明显内存压力或输入区错位。
```

## 5. 未完成实现边界

```text
1. true LLM streaming 未实现。
2. CameraX / real OCR 未实现。
3. PostgreSQL setup PASS，DB smoke PASS。
4. MiMo ASR real provider smoke PASS，provider=mimo；使用 synthetic fake wav，不验证儿童语音识别准确率。
5. MiMo vision real provider smoke PASS，provider=mimo；使用 fake/test image，不接 CameraX。
6. 本清单未执行前，Redmi K60 / Honor Pad 5 不得写成真机通过。
```

## 6. QA Result Template

记录测试结果时使用：

```text
docs/QA_RESULT_TEMPLATE_V0_1.md
```

如需收集 Android 端日志：

```bash
bash scripts/collect_android_qa_logs.sh
```
