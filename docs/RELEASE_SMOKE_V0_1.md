# Release Smoke v0.1

用途：记录家庭内测前 smoke、构建和 QA 交付状态。本文档不是正式上架 release note。

## 1. 当前阶段

```text
阶段：family-test-prep smoke
日期：2026-05-22
目标：用 mock-first 本地 smoke、自动测试和 debug APK 构建确认既有主链路可交付给真机 QA。
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
3. MiMo ASR real provider smoke 只在 opt-in env 和非儿童测试音频满足时执行。
4. Redmi K60 / Honor Pad 5 真机 QA 仍待用户或开发者执行。
```

## 2. APK Metadata

```text
APK path: android/app/build/outputs/apk/debug/app-debug.apk
build variant: debug
build time UTC: 2026-05-22T04:00:54Z
size: 16047291 bytes / 15M
sha256: 7468ac8c605bb92f5244e38a39d022b1bb388d79d142bbd3444eb95b620f3e10
base URL in this build: http://10.0.2.2:8000/
```

注意：

```text
1. 这个 APK 使用默认 emulator base URL，只适合模拟器本机后端。
2. 交给 Redmi K60 / Honor Pad 5 前必须重新构建：
   bash scripts/android_gradle.sh assembleDebug -PconversationApiBaseUrl=http://<mac-lan-ip>:8000/
3. 真机 APK 必须重新记录 path、size、sha256 和 BuildConfig.CONVERSATION_API_BASE_URL。
```

## 3. Automated Test Results

```text
bash scripts/test_backend.sh
result: PASS
summary: 278 passed in 1.27s

bash scripts/lint_backend.sh
result: PASS
summary: All checks passed

bash scripts/android_gradle.sh test
result: PASS
summary: BUILD SUCCESSFUL

bash scripts/android_gradle.sh assembleDebug
result: PASS
summary: BUILD SUCCESSFUL
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
  - health/detail returned degraded because local PostgreSQL was unavailable.
  - DB-backed persistence warnings were expected in this no-DB smoke; response fallback still worked.

bash scripts/smoke_voice_stack.sh
result: PASS
coverage:
  - mock ASR with tiny fake WAV data URI and mock transcript metadata
  - mock TTS endpoint
  - stream include_tts=true with tts_started/audio_ready/done
notes:
  - no real child audio, API key, base64, transcript text, or provider raw response was printed.

bash scripts/smoke_db_persistence.sh
result: SKIP
reason:
  - local PostgreSQL was unavailable on 127.0.0.1:5432.
  - script output clearly prompted: docker compose -f docker-compose.local.yml up -d
  - this is not counted as PASS.

scripts/smoke_mimo_asr_opt_in.sh
result: NOT RUN
reason:
  - real MiMo ASR smoke requires explicit opt-in env flags, MiMo key, and developer-provided non-child smoke audio path.
  - this round did not execute external MiMo ASR to avoid unintended child-audio or secret exposure.
```

## 5. Smoke Commands

```bash
bash scripts/smoke_backend_local.sh
bash scripts/smoke_voice_stack.sh
bash scripts/smoke_db_persistence.sh
```

MiMo ASR opt-in smoke:

```bash
ASR_PROVIDER=mimo \
MIMO_ASR_ENABLED=true \
MIMO_ASR_ALLOW_CHILD_AUDIO=true \
MIMO_ASR_RETENTION_POLICY_CHECKED=true \
MIMO_ASR_NO_TRAINING_CONFIRMED=true \
CHILD_AI_MIMO_KEY="$CHILD_AI_MIMO_KEY" \
MIMO_ASR_SMOKE_AUDIO=/path/to/non-child-smoke-audio.wav \
bash scripts/smoke_mimo_asr_opt_in.sh
```

The opt-in script must not be used with real child recordings during development smoke.

