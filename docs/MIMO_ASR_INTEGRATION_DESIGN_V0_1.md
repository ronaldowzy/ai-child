# MiMo ASR Integration Design v0.1

用途：定义 MiMo audio input 作为云端 ASR 候选能力时的后端接入方式、数据策略和 Coordinator 后续集成事项。本文档不启用真实外部调用。

状态：

```text
design_only
default_provider=mock
cloud_asr_enabled=false
conversation_auto_send=false
```

---

## 1. Decision Summary

```text
1. MiMo ASR 不改变 v1 默认语音输入路线：Android 本地 SpeechRecognizer + confirm-before-send。
2. MiMo audio input 可作为后续 cloud ASR provider 候选。
3. 后端 ASR endpoint 即使存在，也只能返回 pending transcript，不能直接调用 conversation/message。
4. Android 仍不得持有 MiMo API key。
5. 真实 provider 默认 disabled，必须同时满足 enabled、API key、child audio allowed、retention checked。
6. 未确认训练/留存策略前，不允许真实儿童音频外发。
```

---

## 2. Candidate Provider Contract

| Field | Value |
|---|---|
| Provider | MiMo OpenAI-compatible chat completions |
| Candidate models | `mimo-v2.5` first, `mimo-v2-omni` fallback |
| Unsupported model names | `MiMo-V2.5-ASR`, `mimo-v2.5-asr` |
| Endpoint | `POST https://token-plan-cn.xiaomimimo.com/v1/chat/completions` |
| Mode | Non-streaming audio input only; streaming not confirmed |
| Auth | `Authorization: Bearer <env-provided-key>` |
| Audio input field | user content item with `type=input_audio` and audio data URI |
| Transcript output | assistant message text content |
| Timeout | Project should start lower than the external spec's generous timeout, then tune by QA |

Model naming caution:

```text
The existing project has a separate MiMo text-provider note that `mimo-v2.5-pro`
is the valid text model for that path. This ASR source spec names `mimo-v2.5`
and `mimo-v2-omni` for audio input. Treat ASR model names as unverified until
policy-gated smoke tests are run.
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
       - MiMoAsrProvider only when explicitly enabled
  -> transcript response with requiresConfirmation=true
  -> Android shows editable text
  -> confirmed text goes to /api/v1/conversation/message
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

This API is a future integration contract. The current ASR Spec Agent does not wire it into `backend/app/main.py`.

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
1. `requiresConfirmation` must always be true for child voice input.
2. `audio.data` must never be logged.
3. `transcript` must be short enough for a confirmation UI; long audio should be rejected before provider call.
4. ASR response is not a child message until the user confirms or edits it.
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
| Formats | `wav` first; optionally `mp3`, `m4a` after QA |
| WAV data URI | `data:audio/wav;base64,` prefix required for WAV |
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

Coordinator should add shared config only after product approval:

```bash
CHILD_AI_ASR_PROVIDER=mock
CHILD_AI_MIMO_ASR_ENABLED=false
CHILD_AI_MIMO_ASR_API_KEY=
CHILD_AI_MIMO_ASR_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
CHILD_AI_MIMO_ASR_MODEL=mimo-v2.5
CHILD_AI_MIMO_ASR_TIMEOUT_MS=30000
CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO=false
CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED=false
CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED=false
```

Rules:

```text
1. No real key in `.env.example`, docs, tests, Android or git.
2. Existing MiMo TTS key may be reused operationally only if Coordinator confirms naming and policy.
3. Android never reads these values.
4. A missing or false policy flag must block external ASR calls.
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
1. Log provider, model, request_id, duration_ms, decoded_size_bytes, elapsed_ms and error_code.
2. Do not log audio data URI, base64, raw transcript before confirmation, API key or child real identity.
3. If transcript preview is needed for debugging, keep it disabled by default and never use real child speech.
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

Coordinator has completed the safe shared-config part only:

```text
1. ASR settings now exist in `backend/app/core/config.py` with mock/disabled defaults.
2. ASR env defaults are documented in `.env.example` and `backend/README.md`.
3. Backend tests cover mock transcript, unsupported format, default MiMo policy block and router smoke in isolation.
```

Still not done:

```text
1. ASR router is not included in `backend/app/main.py`.
2. No real MiMo ASR network call is wired.
3. Endpoint availability, parent gating and Android usage are not product-approved.
4. `docs/PRODUCT_DECISIONS_V0_1.md` must be updated before enabling cloud ASR with child audio.
5. Model id must be confirmed through a policy-gated smoke using fake audio only.
```

Blocked until confirmation:

```text
Cloud ASR with real child audio.
Streaming ASR.
Hands-free conversational mode.
Direct Android-to-MiMo ASR calls.
Saving raw audio or long transcripts.
```
