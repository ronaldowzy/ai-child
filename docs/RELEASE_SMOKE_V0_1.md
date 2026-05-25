# Release Smoke v0.1

用途：记录家庭内测前 smoke、构建和 QA 交付状态。本文档不是正式上架 release note。

## 1. 当前阶段

```text
阶段：family-test-prep smoke
日期：2026-05-22
目标：用 本地 smoke、real provider smoke、自动测试和真机 LAN debug APK 构建确认既有主链路可交付给真机 QA。
```

已完成范围：

```text
1. DB1-B2/B3/B4/B5 thin-slice done：
   - parent_policies
   - conversation message / stream turn
   - memory_items
   - parent_reports
2. Android child mode 默认 voice-first，ASR ok 后自动发送 transcript。
3. Streaming v1 当前是 NDJSON pseudo streaming + segment interleaved TTS。
4. 小白狐 animation_v1 使用 512px WebP runtime assets，未把美术验收全量包整体放入 APK。
```

仍未完成：

```text
1. true LLM streaming 未实现。
2. CameraX / real OCR 未实现。
3. MiMo ASR real provider smoke 已用临时 env overlay + synthetic fake wav 执行并 PASS；这只验证 provider 请求链路，不验证中文识别准确率。
4. MiMo vision/OCR real provider smoke 已用临时 env overlay + fake/test image 执行并 PASS；这只验证 provider 请求链路和图片理解返回，不接 CameraX。
5. Redmi K60 / Honor Pad 5 真机 QA 仍待用户或开发者执行。
```

## 2. APK Metadata

### Device QA Debug APK

```text
APK path: android/app/build/outputs/apk/debug/app-debug.apk
build variant: debug
build time UTC: 2026-05-22T12:06:31Z
size: 16190741 bytes / 15M
sha256: 798a87a6256c9b2523b519aeb337385eec2fe7b9cecc43e25f1feb79bf51f850
base URL in this build: http://192.168.0.118:8000/
BuildConfig.CONVERSATION_API_BASE_URL: http://192.168.0.118:8000/
```

构建命令：

```bash
bash scripts/build_device_debug_apk.sh --base-url http://192.168.0.118:8000/
```

注意：

```text
1. 这个 APK 是本轮给 Redmi K60 / Honor Pad 5 的真机 QA debug APK。
2. Mac LAN IP 变化后必须重新构建，不能继续使用旧 APK。
3. 真机 QA 仍未完成；APK 构建成功不等于 Redmi K60 / Honor Pad 5 通过。
4. 安装前先启动后端：
   bash scripts/start_backend_services.sh --agent main --host 0.0.0.0 --port 8000
5. 设备和 Mac 必须在同一网络，并在设备侧能访问：
   http://192.168.0.118:8000/api/v1/health
```

### Deprecated Non-Device APK Path

旧非真机 APK 路径已废弃。当前阶段只交付 Mac LAN base URL 的 Redmi K60 / Honor Pad 5 真机 APK。

## 3. Automated Test Results

```text
bash scripts/test_backend.sh
result: PASS
summary: 286 passed in 1.90s

bash scripts/lint_backend.sh
result: PASS
summary: All checks passed

bash scripts/android_gradle.sh test
result: PASS
summary: BUILD SUCCESSFUL; testDebugUnitTest and testReleaseUnitTest up-to-date.

bash scripts/android_gradle.sh assembleDebug
result: PASS
summary: BUILD SUCCESSFUL; final device APK uses Mac LAN base URL.

bash scripts/build_device_debug_apk.sh --base-url http://192.168.0.118:8000/
result: PASS
summary: generated device debug APK with BuildConfig.CONVERSATION_API_BASE_URL=http://192.168.0.118:8000/.
apk_path: android/app/build/outputs/apk/debug/app-debug.apk
apk_size_bytes: 16471142
apk_sha256: 2afe25e5d62484edf4657e51f96dd12bfdce132daa373e8474b314490103b5db
```

## 4. Smoke Results

```text
bash scripts/smoke_backend_local.sh
result: PASS
coverage:
  - GET /api/v1/health/detail
  - POST /api/v1/conversation/message
  - POST /api/v1/conversation/stream to done
  - POST/GET /api/v1/parent/policy
  - GET /api/v1/parent/reports/{child_id}
notes:
  - after local PostgreSQL setup, health/detail returned ok.
  - DB-backed persistence path was available during this smoke.

bash scripts/smoke_voice_stack.sh
result: PASS
coverage:
  - mock ASR with tiny fake WAV data URI and mock transcript metadata
  - mock TTS endpoint
  - stream include_tts=true with tts_started/audio_ready/done
notes:
  - no real child audio, API key, base64, transcript text, or provider raw response was printed.

bash scripts/smoke_db_persistence.sh
result: PASS
reason:
  - local PostgreSQL is now available through scripts/setup_local_postgres.sh.
  - migration completed and parent policy -> conversation -> memory -> parent report persistence path passed.

bash scripts/setup_local_postgres.sh
result: PASS
coverage:
  - Docker Compose postgres:16 startup when Docker is available
  - Homebrew postgresql@16 fallback on macOS when Docker is unavailable
  - Alembic migration
  - DB persistence smoke
notes:
  - current Codex environment had no Docker CLI.
  - script installed/started Homebrew postgresql@16, created/updated child_ai role and child_ai_dev DB, ran migrations, then smoke.
  - final output: POSTGRES_SETUP: PASS.

bash scripts/check_asr_real_status.sh
result: PASS
observed:
  - dotenv_loaded=true
  - mimo_key_present=true
  - mimo_key_source=CHILD_AI_MIMO_API_KEY
  - initial_asr_provider=mock
  - smoke_env_overlay=applied
  - smoke_audio=synthetic_fake_wav
  - ASR_STATUS=mimo_ready
  - status=needs_retry
  - provider=mimo
  - model=mimo-v2.5
  - duration=1000
  - errorCode=empty_transcript
  - ASR_STATUS=mimo_smoke_pass
notes:
  - The synthetic tone audio is intentionally non-child fake input.
  - needs_retry / empty_transcript is acceptable for this smoke because it validates real provider request wiring, not recognition accuracy.
  - No API key, audio base64, transcript text, or raw provider response was printed.

bash scripts/smoke_vision_model_opt_in.sh
result: PASS
coverage:
  - OpenAI-compatible multimodal vision path
  - AttachmentService vision recognition with image_data_uri
  - output redaction: no key, no base64, no full provider raw response
observed:
  - dotenv_loaded=true
  - vision_model_path_implemented=yes
  - mimo_key_present=true
  - smoke_env_overlay=applied
  - smoke_image=generated_fake_test_image
  - VISION_STATUS=mimo_ready
  - model_call_finished logged fallback_used=false, provider=mimo, model=mimo-v2.5
  - VISION_STATUS=mimo_smoke_pass
  - provider=mimo
  - model=mimo-v2.5
  - latest observed recognized_type=privacy_sensitive
  - latest observed text_length=176
notes:
  - This is not blocked by missing image or missing image policy; the script generated a fake/test PNG and applied temporary opt-in image policy.
  - The generated fake image can produce different recognized_type values; this smoke validates real MiMo provider routing and output redaction, not classification quality.
  - Root cause fixed: vision profile must use MiMo multimodal model `mimo-v2.5`; global text model `mimo-v2.5-pro` is not an image endpoint.
  - MiMo provider payload uses `max_completion_tokens`, matching official MiMo chat completions docs.
  - No API key, image base64, full image description, or provider raw response was printed.
```

## 5. Smoke Commands

```bash
bash scripts/smoke_backend_local.sh
bash scripts/setup_local_postgres.sh
bash scripts/smoke_voice_stack.sh
bash scripts/smoke_db_persistence.sh
bash scripts/check_asr_real_status.sh
bash scripts/smoke_vision_model_opt_in.sh
```

MiMo ASR opt-in smoke:

```bash
bash scripts/check_asr_real_status.sh
```

The status script sources `.env`, applies a temporary MiMo ASR smoke overlay,
generates a synthetic fake wav if no safe smoke audio is provided, starts a
temporary backend, and then runs the opt-in script. It must not be used with
real child recordings during development smoke.

MiMo vision opt-in smoke:

```bash
bash scripts/smoke_vision_model_opt_in.sh
```

The vision script sources `.env`, applies a temporary MiMo image smoke overlay,
generates a fake/test PNG if no safe smoke image is provided, and starts a
temporary backend. It must not be used with real child photos or real family
photos during development smoke.

## 6. Device QA Handoff

```text
Current status:
  PostgreSQL setup: PASS
  DB smoke: PASS
  real MiMo ASR smoke: PASS, provider=mimo
  real MiMo vision smoke: PASS, provider=mimo
  device debug APK build: PASS
  Redmi K60 QA: pending
  Honor Pad 5 QA: pending

Still not implemented:
  true LLM streaming
  CameraX / real camera OCR
```

交付真机 QA 前：

```bash
bash scripts/start_backend_services.sh --agent main --host 0.0.0.0 --port 8000
curl --noproxy '*' http://192.168.0.118:8000/api/v1/health
```

真机测试记录使用：

```text
docs/QA_DEVICE_CHECKLIST_V0_1.md
docs/QA_RESULT_TEMPLATE_V0_1.md
```

如果需要收集 Android 日志：

```bash
bash scripts/collect_android_qa_logs.sh
```
