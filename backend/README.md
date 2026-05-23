# Backend

FastAPI backend for the v0.1 child AI growth agent MVP.

The current backend is intentionally local-first and mock-first:

- Uses `MockModelProvider` by default.
- Does not call real model, OCR, vision, or external network services in tests.
- Keeps all child-facing AI decisions behind backend services such as `SafetyEngine`, `IntentClassifier`, `SceneOrchestrator`, `PromptManager`, and `ModelRegistry`.
- Routes child-facing replies through `ChildAgentRuntime`: `SceneOrchestrator`
  decides the scene strategy and safe fallback reply, `PromptManager` composes
  the prompt, `ModelRegistry` generates the child chat response, and
  `SafetyEngine.classify_output()` checks the output before return.
- Retrieves non-safety structured memory before `ChildAgentRuntime`, and writes
  rule-based conversation memory after routing. Memory evidence uses summary
  sources only; raw chat, full transcripts, raw audio, and raw photos are not
  stored as long-term evidence.
- E1 relationship memory is rule-first and local: low-sensitivity
  `interest_seed`, `topic_boundary`, and `proud_moment` summaries can be
  created from child conversation turns, while operation asides, bystander
  prompts, privacy details, high-risk safety content, and raw/full transcripts
  are filtered out before storage. The E1.1 hardening keeps memory writes
  best-effort, dedupes active interest seeds by child/topic across sessions,
  and only lets opening lightly revisit the latest low-sensitivity seed.
- Treats child chat as open-ended conversation. Time periods and scenes provide
  context, safety boundaries, and fallback replies; they should not force every
  ordinary message into a fixed script.
- Current direction is freedom-first: `conversation.open` is the default base.
  Time context, parent free-form guidance, memory, recent turns, and images are
  prompt/context inputs; safety, privacy, explicit learning help, explicit
  bedtime closeout, and confirmed parent hard rules are guardrails.
- Attachment is moving from homework-only to universal image sharing. The
  existing homework flow remains available, but generic image attachments can
  represent toys, drawings, books, plants, handmade work, or homework and are
  routed by image intent.
- Uses `ConversationHistoryService` for short-term, in-memory recent turns so
  ordinary chat can keep context within one running backend process. This is not
  a durable chat database; service restart clears it, and full chat transcripts
  are not written to long-term memory or parent reports.
- Normalizes child-facing model replies for voice-first use: short natural
  sentences, no Markdown/list formatting, and usually one main question.
- Returns child-facing reply metadata for future voice and 小白狐 animation
  work: `voice_enabled`, optional `audio_url`, `emotion`, and `agent_motion`.
- Speech recognition v1 is backend MiMo ASR: Android records only after an
  explicit tap and uploads short audio to the backend ASR endpoint. Child mode
  auto-sends a non-empty transcript to conversation; the pending transcript
  panel remains only for DevSettings / father debugging.
  Raw child audio is never stored long-term and MiMo ASR remains disabled until
  father authorization and ASR policy flags allow it.
- Opening greeting is available at `POST /api/v1/conversation/opening`.
  It uses time context, parent policy names, and parent guidance to return one
  short child-facing greeting, with optional `reply.audio_url`. When a recent
  low-sensitivity relationship `interest_seed` exists, opening may lightly
  revisit one topic and still gives the child a clear choice to switch away.
  E2-A routes this through `OpeningPolicyBuilder`, so fallback text and model
  prompt share the same `opening_mode`, boundary cooldown, bedtime closure,
  age-band length, parent-goal translation, and forbidden-phrase rules.
- Parent policy supports `child_nickname` and `child_display_name`; Android
  father settings can edit them, and opening greeting uses nickname first,
  display name second, then no forced call name.
- 小白狐 voice output now has a backend TTS path: `POST /api/v1/tts/xiaobaohu`
  can generate or return a cached wav URL. The default provider is mock and
  never calls external services. MiMo VoiceClone is disabled until explicit
  local environment variables and the TTS data policy gate allow child text
  transmission. Android now prefers `reply.audio_url` playback and falls back
  to local TextToSpeech or text if remote audio fails.

If Android replies look like fixed templates such as “听起来可以聊”, the backend
is probably running with the default mock provider. For real Mimo chat, restart
the backend with the temporary environment variables in the Mimo section below;
do not put the real API key into git, Android, docs, tests, or screenshots.

## Current Voice And Presentation Contract

The backend remains the decision and safety boundary. Android may record and
upload short audio to backend ASR later, and now uses remote audio playback plus
TextToSpeech fallback for voice output, but child-facing content still flows through:

```text
SafetyEngine -> IntentClassifier -> SceneOrchestrator -> PromptManager -> ModelRegistry -> output safety check
```

Current backend contract:

- Accept child text through `POST /api/v1/conversation/message` and NDJSON
  stream text through `POST /api/v1/conversation/stream`.
- Treat v1 speech input as voice-first in child mode: ASR ok with non-empty
  transcript is sent automatically by Android. Confirm-before-send remains a
  debug/father mode only; hands-free conversational mode is still a future
  product phase and should not change the v1 backend contract.
- ASR v1 target is backend MiMo audio input / ASR. Android must not call MiMo
  directly or store provider API keys.
- Raw audio uploaded for ASR must be short-lived request data only: no database
  persistence, no logs, no memory, no test fixtures with real child recordings.
- Keep external audio and child text transmission disabled unless a confirmed
  product decision and provider gate review explicitly allow it.
- Return `reply.voice_enabled`, optional `reply.audio_url`, `reply.emotion`, and
  `reply.agent_motion` for Android TTS and 小白狐 presentation.
- Use `POST /api/v1/tts/xiaobaohu` for backend-generated 小白狐 speech audio.
- Use `POST /api/v1/conversation/opening` when the child chat screen first
  becomes visible. Call-name priority is `child_nickname`,
  `child_display_name`, then no forced call name.
- Never use voice or presentation metadata to weaken learning-answer, secrecy,
  trusted-adult, or long-term raw-data storage safety rules.

## Setup

Project convention uses the local conda environment from `docs/session_process/README.md`:

```bash
eval "$(/opt/homebrew/bin/conda shell.zsh hook)"
conda activate child-ai
cd backend
python -m pip install -e ".[dev]"
```

If the environment is not activated, root scripts will try `/opt/homebrew/bin/conda run --no-capture-output -n child-ai python` before falling back to system Python. You can override this explicitly:

```bash
PYTHON_BIN="/opt/homebrew/bin/conda run --no-capture-output -n child-ai python" bash scripts/test_backend.sh
PYTHON_BIN=python3 bash scripts/lint_backend.sh
```

For local environment diagnosis:

```bash
bash scripts/doctor_local_env.sh
```

## Run

From the repository root:

```bash
bash scripts/dev_backend.sh
```

Or from `backend/` after activating the environment:

```bash
python -m uvicorn app.main:app --reload
```

For Android device or tablet LAN testing, listen on all interfaces:

```bash
bash scripts/dev_backend.sh --host 0.0.0.0 --port 8000
```

Then use the Mac mini LAN address from the Android build, for example:

```bash
bash scripts/android_gradle.sh assembleDebug -PconversationApiBaseUrl=http://MAC_MINI_LAN_IP:8000/
```

Default local API docs:

- `GET http://127.0.0.1:8000/docs`
- `GET http://127.0.0.1:8000/api/v1/health`

## Test And Lint

From the repository root:

```bash
bash scripts/test_backend.sh
bash scripts/lint_backend.sh
```

From `backend/`:

```bash
python -m pytest
python -m ruff check .
```

Q1 scenario tests live in:

```text
app/tests/test_scenarios_v0_1.py
```

They cover:

- after-school check-in
- learning help
- direct-answer request handling
- child does not want to talk
- watch-level peer trouble routing to `safety.gentle_checkin`
- low privacy boundary routing to `privacy.boundary`
- high-risk safety guardian routing with parent attention
- bedtime reflection
- parent goal influencing reply wording
- model fallback
- automatic conversation memory hooks in
  `app/tests/test_conversation_memory_hooks.py`, including learning patterns,
  low-energy emotion observations, high-risk safety memory, watch observations,
  privacy-boundary summaries, relationship interest seeds, topic boundaries,
  proud moments, parent report visibility, and safety-memory retrieval
  isolation

## Demo Scenarios

Run a local demo from the repository root:

```bash
bash scripts/demo_backend_scenarios.sh
```

By default the script starts a temporary backend server on `127.0.0.1:18080`, runs safe mock scenarios, prints the active scene, intent, risk level, quick actions, and reply, then stops the server.

To point the demo at an already running server:

```bash
DEMO_BASE_URL=http://127.0.0.1:8000 bash scripts/demo_backend_scenarios.sh
```

The demo uses only fictional IDs such as `child_demo_001` and mock homework text. It does not use real child data, real photos, real OCR, or real model calls.

## Local E2E API Check

With a backend server already running, validate the Android-facing API contract:

```bash
bash scripts/e2e_local_api_check.sh
```

To target a LAN server:

```bash
E2E_BASE_URL=http://MAC_MINI_LAN_IP:8000 bash scripts/e2e_local_api_check.sh
```

The check covers health, after-school, learning help, mock homework attachment, bedtime, high-risk safety, parent policy update, and parent report read. It uses fictional IDs and mock homework text only.

With automatic memory enabled, the parent report step may include structured
conversation summaries generated during the same process. It still does not
return evidence fields, quote summaries, or full chat transcripts.

## Family Test Smoke

Family-test smoke scripts live under `scripts/` and are designed to catch
configuration drift before handing an APK to device QA.

```bash
bash scripts/setup_local_postgres.sh
bash scripts/smoke_backend_local.sh
bash scripts/smoke_voice_stack.sh
bash scripts/smoke_db_persistence.sh
bash scripts/check_asr_real_status.sh
bash scripts/smoke_vision_model_opt_in.sh
```

Coverage:

- `smoke_backend_local.sh` starts a temporary mock backend by default and checks
  `/api/v1/health/detail`, `/conversation/message`, `/conversation/stream`,
  parent policy save/read, and parent report read.
- `smoke_voice_stack.sh` starts a temporary mock backend and checks mock ASR,
  mock TTS, and stream `include_tts=true` through `audio_ready`.
- `smoke_db_persistence.sh` requires local PostgreSQL and migrations. If the
  database is unavailable, it prints a clear `SKIP` with
  `bash scripts/setup_local_postgres.sh` and must not be counted as pass.
- `setup_local_postgres.sh` first tries Docker Compose, waits for the local
  PostgreSQL healthcheck, runs migrations, then runs DB persistence smoke. If
  Docker is unavailable on macOS, it tries Homebrew `postgresql@16` and creates
  the `child_ai` role and `child_ai_dev` database idempotently. If Docker,
  Homebrew, or permissions are unavailable, it reports `POSTGRES_SETUP: BLOCKED`
  with a concrete reason.
- `check_asr_real_status.sh` sources `.env`, applies a temporary MiMo ASR
  smoke overlay, starts a temporary backend, and generates a synthetic
  non-child fake WAV when no safe smoke audio path was provided. This validates
  the real provider request chain without permanently changing `.env`.
- `smoke_vision_model_opt_in.sh` verifies the OpenAI-compatible MiMo vision path
  by sourcing `.env`, applying a temporary MiMo image smoke overlay, starting a
  temporary backend, and generating a fake/test PNG when no safe image path was
  provided. It never prints image base64, the full image description, API keys,
  or provider raw response.

MiMo ASR real smoke:

```bash
bash scripts/check_asr_real_status.sh
```

The ASR smoke must not print API keys, audio base64, transcript text, or
provider raw response, and it must not be run with real child recordings during
development smoke.

MiMo vision/OCR smoke:

```bash
bash scripts/smoke_vision_model_opt_in.sh
```

The vision smoke path posts a data URI to `/api/v1/conversation/attachment`.
The backend does not store the raw image data URI and still defaults to
MockOCR unless the provider and policy env explicitly opt in to MiMo.
Normal text chat uses `CHILD_AI_MIMO_MODEL=mimo-v2.5-pro`; image/vision/OCR
uses `CHILD_AI_MIMO_VISION_MODEL=mimo-v2.5` because MiMo image understanding is
served by the native multimodal model, not the pro text model. The MiMo provider
uses `max_completion_tokens` for MiMo chat completions.

## Local PostgreSQL Persistence

The v0.1-dev persistence target is local PostgreSQL for family testing. DB1-A
adds the database foundation. DB1-B2/B3/B4/B5 now cover the local persistence
thin slice:
`ParentPolicyService` reads/writes `parent_policies` through a SQLAlchemy
repository when PostgreSQL is available, including `parent_message_raw`,
`parent_message_updated_at`, `child_nickname`, and `child_display_name`.
DB1-B3 records ordinary `/api/v1/conversation/message` turns and
completed `/api/v1/conversation/stream` turns with a best-effort repository. It
upserts `conversation_sessions`, stores the child message, stores one final
agent message, and stores a non-sensitive routing decision summary. Stream turns
are recorded once after completion; text deltas, full stream event lists, and
per-segment TTS text are not stored. If the local database is unavailable in
dev/test, persistence failures are logged with hashed identifiers and the
conversation response or stream output is not blocked.

DB1-B4 records structured `MemoryService` items in `memory_items` when
PostgreSQL is available. The service keeps the same validation boundary as the
in-memory repository: memory content must be structured summary material,
evidence must be short `quote_summary` style evidence, safety memories remain
parent-visible, and forbidden raw evidence sources are rejected before storage.
Relationship memory E1 uses the same table and schema: `interest_seed`,
`topic_boundary`, and `proud_moment` are stored as low-sensitivity structured
summaries with metadata, not as child verbatim text.
If PostgreSQL is unavailable, MemoryService falls back to the process-local
repository without blocking conversation or Android QA.

DB1-B5 records generated `ParentReportService` reports in `parent_reports`.
`get_daily_report()` first reads an existing report for `child_id + date`; if
none exists, it generates a report from parent-visible structured memory and
best-effort saves it. Repository failure does not block the parent report API:
the service returns the generated report and logs only hashed identifiers,
date, operation, and error type.
Parent reports can use relationship memories to suggest low-pressure real-world
conversation starters with an avoid note, for example gently asking about a
running competition without interrogating distance or body symptoms.

Local dev database:

```bash
bash scripts/setup_local_postgres.sh
```

Manual Docker-only equivalent:

```bash
docker compose -f docker-compose.local.yml up -d postgres
bash scripts/db_migrate.sh
bash scripts/smoke_db_persistence.sh
```

To reset the local schema during development:

```bash
bash scripts/db_reset_local.sh --yes
```

Default local database URL:

```text
CHILD_AI_DATABASE_URL=postgresql+psycopg://child_ai:child_ai@localhost:5432/child_ai_dev
```

Initial tables:

```text
children
parent_policies
conversation_sessions
conversation_messages
routing_decisions
memory_items
parent_reports
tts_cache_records
```

After pulling DB1 changes, run migrations:

```bash
bash scripts/db_migrate.sh
```

Data boundary:

- This is local family-use storage, not a cloud multi-tenant production design.
- Ordinary `/api/v1/conversation/message` and completed
  `/api/v1/conversation/stream` final text may be stored locally for context,
  review, and future parent report material.
- Stream persistence stores one turn only. It may store the first audio segment
  URL and non-sensitive counts such as `audio_segment_count`, `has_audio`, and
  `tts_error_count`; it must not store every `text_delta` or the full stream
  event list.
- Raw audio files, raw photos, API keys, model keys, and debug internals must
  not be written to PostgreSQL.
- Prompt text, `parent_message_raw`, provider raw responses, audio base64, and
  raw image/OCR debug data must not be written to conversation persistence.
- `memory_items` stores structured summaries, tags, short evidence summaries,
  sensitivity, visibility flags, parent-attention flags, expiry, and optional
  embedding ids. It must not store raw media, full chat transcripts, prompts,
  debug internals, provider raw responses, or API keys.
- `parent_reports` stores parent-facing daily summary text, observations,
  structured safety alerts, and suggested parent actions. It must not store
  memory evidence, quote summaries, raw chat transcripts, prompts, debug
  internals, provider raw responses, or API keys.
- `tts_cache_records` stores hashes and cache metadata, not full sensitive TTS
  input text.
- Parent free-text notes are stored in `parent_policies.parent_message_raw` for
  local family testing. They are prompt background only and must not be exposed
  in child-facing debug/UI.
- Any future cloud deployment or app-store release requires a separate child
  data compliance review before enabling remote persistence.

## Freedom-first Conversation Notes

The default child conversation mode is `conversation.open`. Time context,
parent notes, memory, and image context are prompt context, not hard modes.
Safety, privacy, explicit homework help, and explicit bedtime closeout remain
guardrails.

Second-round routing fixes:

- Standalone “不会” or generic “题/问题” no longer triggers homework help.
- “我不会画这个小怪兽”, “游戏里有一道谜题”, and “我想出一个问题考你” stay in
  open conversation.
- Explicit homework phrases such as “我有一道题不会”, “这道题怎么做”, “帮我看看作业”,
  “数学题不会”, “练习册” enter `learning.homework_help`.
- Generic image sharing can continue into conversation through attachment
  context. The prompt receives the image summary and child caption, but no raw
  photo.
- Parent reports are generated when the parent opens the report screen. The
  service combines structured memory with same-day persisted conversation
  message/routing summaries, refreshes stale same-day reports when new chat
  material exists, and still avoids raw transcripts, evidence quotes, prompts,
  debug internals, provider raw responses, and raw media.

## Optional Xiaomi Mimo Provider

v0.1 remains mock-first. A Xiaomi Mimo OpenAI-compatible provider can be configured for controlled local testing, but it is disabled by default and falls back to mock on provider/configuration failure.

Use environment variables only; never commit real API keys:

```bash
export CHILD_AI_MODEL_PROVIDER=mimo
export CHILD_AI_MIMO_ENABLED=true
export CHILD_AI_MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
export CHILD_AI_MIMO_MODEL=mimo-v2.5-pro
export CHILD_AI_MIMO_API_KEY="..."
```

For child-facing traffic, do not enable real external transmission until the safety/data-retention review is complete:

```bash
export CHILD_AI_MIMO_ALLOW_CHILD_DATA=false
export CHILD_AI_MIMO_ALLOW_IMAGE=false
export CHILD_AI_MIMO_ALLOW_AUDIO=false
export CHILD_AI_MIMO_RETENTION_POLICY_CHECKED=false
```

For a local developer-only Mimo smoke test, use temporary shell environment
variables or an ignored local root `.env`. Never write the real key to
committed files, docs, tests, Android, screenshots, or git:

```bash
export CHILD_AI_MODEL_PROVIDER=mimo
export CHILD_AI_MIMO_ENABLED=true
export CHILD_AI_MIMO_API_KEY="<temporary key>"
export CHILD_AI_MIMO_ALLOW_CHILD_DATA=true
export CHILD_AI_MIMO_RETENTION_POLICY_CHECKED=true
export CHILD_AI_MIMO_MAX_TOKENS=800
export CHILD_AI_MIMO_TIMEOUT_MS=30000
bash scripts/dev_backend.sh --host 0.0.0.0 --port 8000
```

`scripts/dev_backend.sh` loads the root `.env` when it exists, then starts
uvicorn. This is only for local development; `.env` must stay ignored and must
not be shared.

Only use fictional child IDs and test text in this mode. Keep
`CHILD_AI_MIMO_ALLOW_IMAGE=false` and `CHILD_AI_MIMO_ALLOW_AUDIO=false` unless a
separate review explicitly allows those data types.

`ModelRegistry.generate()` enforces this as a code-level gate before any
OpenAI-compatible provider call. When request metadata marks
`contains_child_data=true`, an external profile must have both
`allow_child_data=true` and `retention_policy_checked=true`; otherwise it falls
back to the mock profile without calling the external provider. Metadata
`contains_image=true` and `contains_audio=true` also require `allow_image=true`
and `allow_audio=true`. Mock providers are not blocked by this external
transmission gate.

The child-facing runtime always marks child chat model requests with
`contains_child_data=true`. If prompt composition fails, the model registry
blocks or falls back from an external provider, the model call fails, the model
returns empty text, output safety is `high`/`critical`, or a learning-scene
model output appears to give a direct final answer, the runtime returns the
existing `SceneRouteDecision.reply_text` fallback instead of model text. This
keeps the default path mock-first and preserves a deterministic safe reply for
each routed scene.

Output safety also blocks model replies that create secret relationships,
isolate the child from trusted adults, or imply the AI is the child's only or
best friend. These checks run after model generation and before the response is
returned to Android.

The Android app never stores model API keys. All model configuration belongs on the backend host.

## Current API Scope

- `GET /api/v1/health`
- `POST /api/v1/conversation/message`
- `POST /api/v1/conversation/stream`
- `POST /api/v1/conversation/attachment`
- `POST /api/v1/asr/transcribe`
- `GET /api/v1/parent/policy`
- `POST /api/v1/parent/policy`
- `GET /api/v1/parent/reports/{child_id}`
- `GET /api/v1/parent/report/today`
- `GET /api/v1/memories/{child_id}`
- `POST /api/v1/tts/xiaobaohu`
- `GET /media/tts/{voice_version}/{cache_key}.wav`

## XiaoBaiHu TTS Endpoint

The backend now owns the official 小白狐 voice path. Android should not call
MiMo directly and must not store any TTS API key.

Default behavior is local and mock-only:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/tts/xiaobaohu \
  -H 'content-type: application/json' \
  -d '{"text":"我们先看这道题在问什么。","emotion":"hint","voiceVersion":"xiaobaohu_v01"}'
```

Expected response shape:

```json
{
  "audioUrl": "/media/tts/xiaobaohu_v01/<cache_key>.wav",
  "duration": 0.25,
  "text": "我们先看这道题在问什么。",
  "emotion": "hint",
  "voiceVersion": "xiaobaohu_v01",
  "provider": "mock",
  "model": "mock-tts-v0",
  "cacheHit": false
}
```

Important paths:

```text
backend/assets/voices/xiaobaohu_voice_v01.wav
backend/storage/tts_cache/
```

`backend/assets/voices/xiaobaohu_voice_v01.wav` is the server-side voice clone
reference sample. It is not an Android asset and is not served through
`/media/tts`.

`backend/storage/tts_cache/` stores generated wav files and metadata. Generated
cache files are ignored by git. The media route serves only `.wav` files and
does not serve metadata JSON or the voice sample.

Default TTS environment:

```bash
export CHILD_AI_TTS_PROVIDER=mock
export CHILD_AI_CONVERSATION_TTS_ENABLED=false
export CHILD_AI_MIMO_TTS_ENABLED=false
export CHILD_AI_MIMO_TTS_API_KEY=""
export CHILD_AI_MIMO_TTS_BASE_URL="https://token-plan-cn.xiaomimimo.com/v1"
export CHILD_AI_MIMO_TTS_MODEL=mimo-v2.5-tts-voiceclone
export CHILD_AI_MIMO_TTS_ALLOW_CHILD_TEXT=false
export CHILD_AI_MIMO_TTS_RETENTION_POLICY_CHECKED=false
```

Only enable MiMo VoiceClone in a local ignored `.env` or temporary shell after
explicitly accepting child-text transmission and retention policy checks:

```bash
export CHILD_AI_TTS_PROVIDER=mimo
export CHILD_AI_MIMO_TTS_ENABLED=true
export CHILD_AI_MIMO_TTS_API_KEY="<temporary key>"
export CHILD_AI_MIMO_TTS_ALLOW_CHILD_TEXT=true
export CHILD_AI_MIMO_TTS_RETENTION_POLICY_CHECKED=true
```

For a real local MiMo VoiceClone smoke test, keep the API key in `.env` or the
shell only, start the backend with the same TTS env, then run:

```bash
TTS_SMOKE_BASE_URL=http://127.0.0.1:8000 bash scripts/smoke_mimo_tts.sh
```

The script checks the server-side voice sample, prints only the API-key length,
calls `POST /api/v1/tts/xiaobaohu`, downloads the generated `/media/tts/...wav`,
and then verifies that `/api/v1/conversation/message` can return a non-empty
`reply.audio_url`. It uses fake smoke text only.

Current real MiMo VoiceClone adapter notes from 2026-05-20 smoke:

```text
endpoint: /chat/completions
request audio: top-level audio.format=wav and audio.voice=data:audio/wav;base64,...
response audio: choices[0].message.audio.data
voice sample sha256: 8eec0f98629350a1dd09bd98a31c2bee80132128bf214d4c0a009331c9a66c40
```

`TtsDataPolicyGuard` runs before any external TTS provider call. If the guard
blocks, the endpoint returns a clear error and conversation can still return
text with `audio_url=null`. The conversation integration is also gated by
`CHILD_AI_CONVERSATION_TTS_ENABLED=false` by default.

## Streaming And Ops Roadmap

The legacy conversation path is intentionally still synchronous:

```text
child input -> full LLM reply -> full TTS audio -> response text + audio_url
```

This remains the Android fallback. The backend now also exposes a separate
Streaming v1 skeleton without breaking the existing API:

```text
POST /api/v1/conversation/stream
```

Current stream behavior:

```text
1. Keep `/api/v1/conversation/message` for fallback and regression safety.
2. Continue routing through SafetyEngine, IntentClassifier, SceneOrchestrator,
   ChildAgentRuntime, ModelRegistry, and TtsDataPolicyGuard.
3. Return `application/x-ndjson` events with session_started, route_decision,
   text_delta, sentence_ready, tts_started, audio_ready, text_final, done/error.
4. Split text into sentence/chunk events and interleave TTS per segment:
   `text_delta`, `sentence_ready`, `tts_started`, `audio_ready/error`.
5. Emit `text_final` after all segment TTS attempts, then `done`.
6. Use sentence-level pseudo streaming first; true MiMo streaming is not assumed.
7. TTS failure must not fail the text stream.
8. `app.stream_timing` logs request_id, session_id_hash, active_scene,
   first_text_ms, first_tts_start_ms, first_audio_ms, stream_total_ms,
   text_segment_count, tts_segment_count, audio_segment_count,
   tts_error_count, and error_type.
```

Local stream smoke:

```bash
curl -sS --no-buffer -X POST http://127.0.0.1:8000/api/v1/conversation/stream \
  -H 'content-type: application/json' \
  -H 'X-Request-ID: stream-readme-smoke-001' \
  -d '{"child_id":"stream_demo_child","session_id":"stream_demo_session","input":{"type":"text","text":"我想聊恐龙","attachments":[]},"client_context":{"device_time":"2026-05-21T16:35:00+08:00","timezone":"Asia/Shanghai","app_mode":"child"},"stream_options":{"include_tts":false,"client_turn_id":"readme_smoke_001"}}'
```

Android stream client, progressive bubble rendering, and audio segment queue are
not implemented in this backend slice.

The first backend Ops P0 slice is now in place. It is intentionally local-first
and does not use a third-party APM or external log platform:

```text
1. Every HTTP response includes `X-Request-ID`.
2. Safe incoming `X-Request-ID` values are reused; illegal or overlong values
   are replaced.
3. Backend logs are JSON lines and carry request_id context.
4. `app.request_timing` logs request_finished/request_failed with method, path,
   status_code, elapsed_ms, and error_type.
5. `app.model_timing` logs model_call_finished with task_type, provider, model,
   elapsed_ms, fallback_used, policy_blocked, error_type, child_id_hash, and
   session_id_hash.
6. `app.tts_timing` logs tts_call_finished with provider, model, voice_version,
   emotion, cache_hit, elapsed_ms, audio_bytes, text_chars, cache_key_prefix,
   and error_type.
7. `GET /api/v1/health/detail` reports postgres, tts_cache, 小白狐 voice sample,
   and MiMo TTS config status.
```

Allowed log content:

```text
request_id, method, path, status_code, elapsed_ms
provider, model, task_type, fallback_used, policy_blocked, cache_hit
voice_version, emotion, audio_bytes, text_chars, cache_key_prefix
child_id_hash, session_id_hash, error_type
```

Forbidden log content:

```text
API keys, Authorization headers, full child text, full prompt,
full parent_message_raw, full image descriptions, raw audio/photo paths,
full TTS text, full reply text, and signed audioUrl query parameters.
```

Local health detail:

```bash
curl -sS http://127.0.0.1:8000/api/v1/health/detail
```

`/api/v1/health` remains a lightweight process-alive check. `/health/detail`
may return `"status":"degraded"` when PostgreSQL is unavailable, the TTS cache
is not writable, the 小白狐 voice sample is missing, or MiMo TTS is enabled but
missing key/policy configuration. It never returns the API key, database URL, or
voice sample contents.

Streaming v1 will reuse the same request_id and provider timing fields, then add
stream-specific `first_text_ms`, `first_tts_start_ms`, `first_audio_ms`, and
`stream_total_ms`.

## MiMo ASR v1

MiMo ASR / audio-input research and integration design are documented in:

```text
docs/ASR_INPUT_RESEARCH_V0_1.md
docs/MIMO_ASR_INTEGRATION_DESIGN_V0_1.md
```

Current backend status:

```text
1. ASR v1 target is backend MiMo audio input / ASR.
2. Android records/uploads to the backend and child mode auto-sends a non-empty transcript; `requiresConfirmation=true` pending transcript UI is kept only for DevSettings / father debugging.
3. Android must not call MiMo directly and must not store MiMo API keys.
4. `POST /api/v1/asr/transcribe` is mounted, but default provider is mock; MiMo ASR is disabled and policy-blocked by default.
5. Real MiMo `/chat/completions` ASR provider is implemented behind `AsrDataPolicyGuard`.
6. No real child audio should be used in development smoke; use fake/smoke audio only.
7. Raw audio must not be stored in the database, logs, long-term memory, docs, tests, or git.
```

ASR environment defaults:

```bash
export CHILD_AI_ASR_PROVIDER=mock
export CHILD_AI_MIMO_ASR_ENABLED=false
export CHILD_AI_MIMO_ASR_API_KEY=""
export CHILD_AI_MIMO_ASR_BASE_URL="https://token-plan-cn.xiaomimimo.com/v1"
export CHILD_AI_MIMO_ASR_MODEL=mimo-v2.5
export CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO=false
export CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED=false
export CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED=false
```

ASR uses `mimo-v2.5` by default. Do not use the text conversation model
`mimo-v2.5-pro` for ASR.

Fake-audio smoke script:

```bash
set -a
source .env
set +a
CHILD_AI_ASR_PROVIDER=mimo \
CHILD_AI_MIMO_ASR_ENABLED=true \
CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO=true \
CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED=true \
CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED=true \
CHILD_AI_ASR_SMOKE_WAV=/path/to/fake_or_smoke_audio.wav-or.m4a \
ASR_SMOKE_BASE_URL=http://127.0.0.1:8000 \
bash scripts/smoke_mimo_asr.sh
```

The smoke script accepts `.wav` or `.m4a` smoke audio. `.m4a` is converted to
16 kHz mono WAV before upload so the smoke path matches the Android recorder
and the MiMo spec's `data:audio/wav;base64,...` input requirement. The script
prints only status/provider/model/duration/confidence/errorCode. It does not
print the API key, base64 audio, full transcript, request body, response body,
or audio path.

Do not enable MiMo ASR with real child audio until father authorization,
retention/deletion/no-training terms, and all ASR policy flags are confirmed.

### ASR QA artifact rule

Android ASR UI code does not mean real ASR is enabled. Before asking for real
speech-recognition QA, verify the running backend is not using mock ASR:

```bash
set -a
source .env
set +a
python3 - <<'PY'
import os
for key in [
    "CHILD_AI_ASR_PROVIDER",
    "CHILD_AI_MIMO_ASR_ENABLED",
    "CHILD_AI_MIMO_ASR_API_KEY",
    "CHILD_AI_MIMO_API_KEY",
    "CHILD_AI_MIMO_TTS_API_KEY",
    "CHILD_AI_MIMO_ASR_MODEL",
    "CHILD_AI_MIMO_ASR_ALLOW_CHILD_AUDIO",
    "CHILD_AI_MIMO_ASR_RETENTION_POLICY_CHECKED",
    "CHILD_AI_MIMO_ASR_NO_TRAINING_CONFIRMED",
]:
    value = os.getenv(key, "")
    print(f"{key}={'present' if 'KEY' in key and value else value or 'missing'}")
PY
```

If `CHILD_AI_ASR_PROVIDER` is `mock` or the MiMo flags are incomplete, the
artifact can only test recording, upload, confirmation UI, and graceful retry or
policy-blocked messaging. It must not be described as a real MiMo ASR test.
For real ASR QA, verify the smoke output shows `provider=mimo` and
`model=mimo-v2.5`.

The standard status check is:

```bash
bash scripts/check_asr_real_status.sh
```

`ASR_STATUS=mock_only` means only the mock ASR path is active.
`ASR_STATUS=policy_blocked` means MiMo ASR is selected but required policy/key
env is incomplete. `ASR_STATUS=mimo_smoke_pass` is the only script status that
can be described as a successful real MiMo ASR smoke.

ASR does not require a separate key by default. The backend resolves MiMo ASR
credentials in this order:

```text
1. CHILD_AI_MIMO_ASR_API_KEY
2. CHILD_AI_MIMO_API_KEY
3. CHILD_AI_MIMO_TTS_API_KEY
```

Use `CHILD_AI_MIMO_ASR_API_KEY` only when ASR needs an explicit override.

## Safety Notes

- `high` / `critical` input routes to `safety.guardian` with
  `requires_parent_attention=true`.
- Automatic safety memory created from `safety.guardian` is parent-visible and
  requires parent attention, but normal runtime retrieval calls
  `MemoryService.retrieve(..., include_safety=false)` so safety memories are not
  mixed into ordinary child-facing memory context.
- `watch` input, such as fictional peer bullying test text, routes to
  `safety.gentle_checkin` by default. It uses calm wording, encourages telling
  a parent or teacher, and does not force parent attention. The automatic memory
  hook records a parent-visible observation summary, not a raw transcript.
- Low-risk privacy questions route to `privacy.boundary` and remind the child
  not to share addresses, phone numbers, school names, or photos with AI or
  strangers. The automatic memory hook stores only the generic boundary reminder,
  not the specific address, phone number, school name, or photo content.
- Low-energy emotion expressions, such as not wanting to talk, remain in normal
  check-in/emotion support instead of `safety.guardian`.
- Learning help refuses direct final answers and asks for problem understanding or first-step thinking.
- Parent goals may influence wording, but they do not override child safety rules.
- Tests and demos must use fake child IDs and safe mock content only.
