# MiMo ASR Integration Design v0.1

用途：定义 MiMo audio input 作为 ASR v1 云端 fallback provider 时的后端接入方式、数据策略和 Coordinator 集成事项。PD-048 已将真实识别第一选择修订为 sherpa-onnx + SenseVoice-Small int8 本地推理；本文档保留 MiMo fallback 约束。默认仍 policy-blocked，不表示已经允许真实儿童音频外发。

状态：

```text
implementation_target
default_provider=mock
preferred_real_provider=local_sensevoice
fallback_provider=mimo
cloud_asr_enabled=false
android_child_mode_auto_send=true
confirm_before_send_debug_mode=true
```

---

## 1. Decision Summary

```text
1. ASR v1 原云端方案是 MiMo audio input / ASR；PD-048 后，MiMo 降级为本地 SenseVoice 异常后的 fallback。
2. Android 不直接调用 MiMo，只负责录音、上传后端和儿童端语音状态。
3. 后端 ASR endpoint 即使存在，也只能返回 transcript，不能直接调用 conversation/message 或 conversation/stream。
4. Android 仍不得持有 MiMo API key。
5. MiMo fallback 受 policy gate 控制，必须同时满足 enabled、API key、child audio allowed、retention checked 和 no-training confirmed。
6. 开发阶段先用 fake audio / smoke audio；未取得父亲授权和 policy flags 前，不允许真实儿童音频外发。
7. Android 儿童默认 voice-first：ASR ok 且 transcript 非空后自动发送到 conversation stream；确认面板仅保留为 DevSettings / 父亲调试模式。
8. 不做常开麦克风，不做 streaming ASR，不做后端 ASR 自动调用 conversation。
```

---

## 2. Provider Contract

| Field | Value |
|---|---|
| Provider role | Cloud fallback after local SenseVoice ASR error |
| Provider | MiMo OpenAI-compatible chat completions |
| Target models | `mimo-v2.5` first, `mimo-v2-omni` fallback |
| Unsupported model names | `MiMo-V2.5-ASR`, `mimo-v2.5-asr` |
| Endpoint | `POST https://token-plan-cn.xiaomimimo.com/v1/chat/completions` |
| Mode | Non-streaming audio input only; streaming not confirmed |
| Auth | `Authorization: Bearer <env-provided-key>`; default key order is `CHILD_AI_MIMO_ASR_API_KEY`, then shared `CHILD_AI_MIMO_API_KEY`, then `CHILD_AI_MIMO_TTS_API_KEY` |
| Audio input field | user content item with `type=input_audio` and audio data URI |
| Transcript output | assistant message text content |
| Timeout | Project should start lower than the external spec's generous timeout, then tune by QA |

Model naming caution:

```text
The existing project has a separate MiMo text-provider note that `mimo-v2.5-pro`
is the valid text model for that path. ASR is a separate audio-input path and
must use `mimo-v2.5` by default, not the text `-pro` model. The local
policy-gated smoke on 2026-05-21 confirmed `provider=mimo` and
`model=mimo-v2.5`.
```

---

## 3. Backend Flow

```text
POST /api/v1/asr/transcribe
  -> ASR request schema validation
  -> size / duration / format guard
  -> AsrDataPolicyGuard
  -> AsrService
  -> AsrProvider
       - MockAsrProvider by default
       - LocalSenseVoiceAsrProvider when explicitly enabled
       - MiMoAsrProvider only as fallback and only when explicitly enabled
  -> transcript response with requiresConfirmation=true as backend safety metadata
  -> Android child mode auto-sends non-empty transcript by default
  -> DevSettings / father debug mode can show editable confirmation text
  -> text goes to /api/v1/conversation/stream, with /message fallback
```

Important boundary:

```text
ASR service must not call SafetyEngine, SceneOrchestrator or ModelRegistry as a replacement for conversation.
Those remain in the confirmed-text conversation path.
```

ASR may run lightweight input validation before provider call:

```text
1. supported format.
2. duration limit.
3. decoded audio size limit.
4. base64/data URI shape.
5. policy gate.
```

Safety classification happens after confirmed text enters the existing conversation API.

---

## 4. Proposed Public API

This API is the v1 backend ASR contract. It may be mounted while local SenseVoice is the preferred ASR path; MiMo network calls still require all policy flags.

```http
POST /api/v1/asr/transcribe
Content-Type: application/json
```

Request:

```json
{
  "childId": "<fictional-or-dev-child-id>",
  "sessionId": "<session-id>",
  "audio": {
    "data": "data:audio/wav;base64,<redacted>",
    "format": "wav",
    "sampleRateHz": 16000,
    "channelCount": 1,
    "durationMs": 8000
  },
  "language": "zh-CN",
  "mode": "confirm_before_send",
  "clientContext": {
    "timezone": "Asia/Shanghai",
    "deviceTime": "2026-05-21T20:00:00+08:00"
  }
}
```

Response:

```json
{
  "status": "ok",
  "transcript": "我想问一道数学题。",
  "requiresConfirmation": true,
  "provider": "mock",
  "model": "mock-asr-v0",
  "language": "zh-CN",
  "durationMs": 8000,
  "confidence": null,
  "errorCode": null,
  "fallbackAction": null
}
```

Rules:

```text
1. `requiresConfirmation` remains true as backend metadata because ASR itself is transcribe-only; Android child mode may still auto-send per product decision.
2. `audio.data` must never be logged.
3. `transcript` must be short enough for direct child conversation or the optional confirmation UI; long audio should be rejected before provider call.
4. ASR response is not a child message inside the backend until Android explicitly sends it to conversation.
```

---

## 5. MiMo Provider Request Shape

Provider adapter builds a chat completions request with:

```json
{
  "model": "mimo-v2.5",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "input_audio",
          "input_audio": {
            "data": "data:audio/wav;base64,<redacted>"
          }
        },
        {
          "type": "text",
          "text": "<transcribe-only prompt>"
        }
      ]
    }
  ],
  "max_completion_tokens": 1024
}
```

Prompt contract:

```text
1. Transcribe the spoken Chinese content as text.
2. Output only the transcript.
3. Do not summarize, explain, embellish or add content not heard.
4. If unclear, return a fixed unable-to-hear marker that the service maps to retry UI.
```

Response extraction:

```text
choices[0].message.content -> transcript
```

Provider adapter must treat missing, non-string or empty content as `empty_transcript`.

---

## 6. Audio Requirements

| Requirement | Initial Policy |
|---|---|
| Formats | `wav` and `m4a` for smoke/backend v1; `mp3` still disabled |
| Data URI | `data:audio/<format>;base64,` prefix must match `audio.format` |
| Sample rate | 16 kHz or higher |
| Channels | mono preferred |
| Bit depth | 16 bit preferred |
| Duration | max 30 seconds |
| Size | max 25 MB by external spec; project may choose a lower first limit |
| Recording trigger | explicit tap only |
| Background recording | not allowed |
| Long-term audio storage | not allowed |

Suggested first project limit:

```text
duration <= 30s
decoded_audio_bytes <= 10MB for first implementation unless QA proves need for more
```

The external provider's 25 MB number should not be treated as a product target.

---

## 7. Auth And Configuration

MiMo fallback config example:

```bash
CHILD_AI_ASR_PROVIDER=local_sensevoice
CHILD_AI_ASR_FALLBACK_PROVIDER=mimo
CHILD_AI_MIMO_ASR_ENABLED=true
CHILD_AI_MIMO_ASR_API_KEY=
CHILD_AI_MIMO_ASR_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
CHILD_AI_MIMO_ASR_MODEL=mimo-v2.5
CHILD_AI_MIMO_ASR_TIMEOUT_MS=30000
CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO=true
CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED=true
CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED=true
```

Rules:

```text
1. No real key in `.env.example`, docs, tests, Android or git.
2. ASR does not require a separate key by default. Reuse `CHILD_AI_MIMO_API_KEY` when `CHILD_AI_MIMO_ASR_API_KEY` is empty; fall back to `CHILD_AI_MIMO_TTS_API_KEY` only for local operational compatibility.
3. Android never reads these values.
4. A missing or false policy flag must block external ASR calls.
5. ASR model default is `mimo-v2.5`; do not use `mimo-v2.5-pro` for ASR.
```

---

## 8. Data Policy Guard

External ASR provider call is allowed only when all are true:

```text
1. provider == mimo
2. enabled == true
3. api key present
4. child_audio_allowed == true
5. retention_policy_checked == true
6. no_training_confirmed == true
```

Blocking reasons should be explicit and non-sensitive:

```text
mimo_asr_disabled
missing_mimo_asr_api_key
child_audio_not_allowed
retention_policy_not_checked
no_training_not_confirmed
```

Logging policy:

```text
1. Log event=asr_call_finished with request_id, provider, model, duration_ms, audio_bytes, elapsed_ms, status and error_type.
2. Do not log audio data URI, base64, raw transcript, API key or child real identity.
3. If transcript preview is needed for debugging, keep it behind DevSettings or father-mode controls and never use real child speech.
```

---

## 9. Error Mapping

| Internal error | HTTP | Response status | Fallback |
|---|---:|---|---|
| `asr_policy_blocked` | 403 | `blocked` | use local ASR or text |
| `unsupported_audio_format` | 400 | `failed` | re-record or convert to WAV |
| `audio_too_long` | 400 | `failed` | ask for shorter recording |
| `audio_too_large` | 413 | `failed` | ask for shorter recording |
| `invalid_audio_data` | 400 | `failed` | retry recording |
| `provider_timeout` | 504 | `failed` | retry later or type |
| `provider_http_error` | 502 | `failed` | type fallback |
| `empty_transcript` | 200 | `needs_retry` | re-record or type |

Child-facing copy remains in `VOICE_INTERACTION_DESIGN_V0_1.md`; backend should return stable codes, not verbose provider bodies.

---

## 10. Coordinator Integration Notes

Current safe integration status:

```text
1. ASR settings now exist in `backend/app/core/config.py` with mock/disabled defaults.
2. ASR env defaults are documented in `.env.example` and `backend/README.md`.
3. Backend tests cover mock transcript, unsupported format, default MiMo policy block and router smoke in isolation.
4. Product decision PD-048 now makes local SenseVoice the v1 first choice; MiMo remains fallback while real child-audio external transmission remains gated.
```

Current implementation tasks:

```text
1. Mount ASR router in `backend/app/main.py` while preserving mock/disabled defaults. [done]
2. Wire real MiMo ASR network call behind `AsrDataPolicyGuard`. [done]
3. Confirm MiMo fallback model id through a policy-gated smoke using fake/smoke audio only. [manual smoke only]
4. Build Android recording upload, child-mode auto-send, and optional DevSettings confirm UI. [code_ready_device_qa]
5. Add local SenseVoice provider and fallback orchestration. [done]
```

Smoke script contract:

```bash
CHILD_AI_ASR_PROVIDER=mimo
CHILD_AI_MIMO_ASR_ENABLED=true
# Optional override only; ASR otherwise reuses CHILD_AI_MIMO_API_KEY.
CHILD_AI_MIMO_ASR_API_KEY=<shell-only-override>
CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO=true
CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED=true
CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED=true
CHILD_AI_ASR_SMOKE_WAV=/path/to/fake-or-smoke.wav-or.m4a
bash scripts/smoke_mimo_asr.sh
```

Status check contract:

```bash
bash scripts/check_asr_real_status.sh
```

The status check must print one of:

```text
ASR_STATUS=mock_only
ASR_STATUS=policy_blocked
ASR_STATUS=mimo_ready
ASR_STATUS=mimo_smoke_pass
ASR_STATUS=mimo_smoke_fail
```

`mock_only` means Android can only test recording/upload/fallback UI, not real
speech recognition. `policy_blocked` means MiMo ASR is selected but missing one
or more required policy/key env values. Only `mimo_smoke_pass` with
`provider=mimo` and `model=mimo-v2.5` can be called a real MiMo ASR smoke.

For `.m4a` smoke files, the script converts to 16 kHz mono WAV before calling
the backend so the smoke artifact matches the Android recording path and the
MiMo spec's `data:audio/wav;base64,...` requirement.

Script output is intentionally limited to:

```text
status
provider
model
duration
confidence
errorCode
```

It must not print the audio path, base64, transcript text, API key, request body or response body.

Blocked until father authorization and policy flags:

```text
Cloud ASR with real child audio.
Streaming ASR.
Hands-free conversational mode.
Direct Android-to-MiMo ASR calls.
Saving raw audio or long transcripts.
```
